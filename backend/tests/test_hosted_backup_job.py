"""An unattended job cannot report success before private remote readback."""
import base64
import hashlib
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ops.backup import encrypt_export, postgres_command
from ops.backup_job import run_job


IMAGE = "postgres:17@sha256:" + "a" * 64
PROJECT = "b" * 20


class HostedBackupJobTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.key = os.urandom(32)
        self.settings = {
            "QLMS_BACKUP_PROVIDER": "google_drive", "QLMS_BACKUP_PROJECT_REF": PROJECT,
            "QLMS_BACKUP_DATABASE_URL": f"postgresql://qlms_backup.{PROJECT}:fictional@aws-1-eu-central-1.pooler.supabase.com/postgres?sslmode=require",
            "QLMS_BACKUP_KEY_BASE64": base64.b64encode(self.key).decode(), "QLMS_DB_SCHEMA": "qlms",
            "QLMS_BACKUP_LOCAL_FOLDER": str(self.root / "archives"), "QLMS_BACKUP_RETENTION_DAYS": "90",
            "QLMS_BACKUP_DRIVE_ACCOUNT": "owner@example.invalid", "QLMS_BACKUP_DRIVE_FOLDER_ID": "folder_fixture",
            "QLMS_DRIVE_CLIENT_ID": "fictional", "QLMS_DRIVE_CLIENT_SECRET": "fictional", "QLMS_DRIVE_REFRESH_TOKEN": "fictional",
            "QLMS_BACKUP_PG_CLIENT_IMAGE": IMAGE,
        }

    def export_fixture(self, url, schema, key, destination, independent, *, client_image=None):
        self.assertEqual(key, self.key)
        self.assertEqual(schema, "qlms")
        self.assertEqual(client_image, IMAGE)
        self.assertIsNone(independent)
        folder = Path(destination)
        folder.mkdir(exist_ok=True)
        path = folder / "qlms-fixture.qlmsbackup"
        plaintext = b"PGDMP fictional cloud fixture"
        path.write_bytes(encrypt_export(plaintext, key, {"archive_sha256": hashlib.sha256(plaintext).hexdigest()}))
        return path, None

    def test_only_verified_remote_copy_writes_success_marker_and_records_size(self):
        with patch.dict(os.environ, self.settings, clear=True), patch("ops.backup_job.refresh_access_token", return_value="fictional"), \
             patch("ops.backup_job.DriveStorage") as drive, patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            drive.return_value.upload_verified.return_value = "file_fixture"
            self.assertTrue(run_job())
        marker = json.loads((self.root / "archives" / "last-success.json").read_text())
        self.assertTrue(marker["remote_upload_verified"])
        self.assertFalse(marker["second_copy_verified"])
        self.assertFalse(marker["automatic_deletion"])
        self.assertEqual(marker["retention_days"], 90)
        self.assertEqual(marker["archive_bytes"], (self.root / "archives" / marker["archive"]).stat().st_size)
        self.assertEqual(marker["projected_retained_bytes"], marker["archive_bytes"] * 90)
        self.assertEqual(marker["storage_budget_bytes"], 5000000000)

    def test_capacity_failure_does_not_upload_or_replace_success_marker(self):
        archives = self.root / "archives"
        archives.mkdir()
        marker = archives / "last-success.json"
        marker.write_text('{"completed_at":"previous"}')
        with patch.dict(os.environ, self.settings, clear=True), \
                patch("ops.backup_job.refresh_access_token", return_value="fictional"), \
                patch("ops.backup_job.DriveStorage") as drive, \
                patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            drive.return_value.check_capacity.side_effect = ValueError("capacity")
            with self.assertRaises(ValueError):
                run_job()
        drive.return_value.upload_verified.assert_not_called()
        self.assertEqual(marker.read_text(), '{"completed_at":"previous"}')

    def test_cleanup_only_follows_verified_new_copy_and_records_completion(self):
        with patch.dict(os.environ, self.settings | {"QLMS_BACKUP_CLEANUP_ENABLED": "true"}, clear=True), \
                patch("ops.backup_job.refresh_access_token", return_value="fictional"), patch("ops.backup_job.DriveStorage") as drive, \
                patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            drive.return_value.upload_verified.return_value = "file_fixture"
            drive.return_value.prune_expired.return_value = 2
            self.assertTrue(run_job())
            drive.return_value.prune_expired.assert_called_once_with(self.key, PROJECT, "file_fixture", 90)
        marker = json.loads((self.root / "archives" / "last-success.json").read_text())
        self.assertTrue(marker["retention_completed"])
        self.assertEqual(marker["expired_archives_removed"], 2)

    def test_cleanup_failure_preserves_reference_to_fresh_verified_copy(self):
        with patch.dict(os.environ, self.settings | {"QLMS_BACKUP_CLEANUP_ENABLED": "true"}, clear=True), \
                patch("ops.backup_job.refresh_access_token", return_value="fictional"), patch("ops.backup_job.DriveStorage") as drive, \
                patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            drive.return_value.upload_verified.return_value = "file_fixture"
            drive.return_value.prune_expired.side_effect = RuntimeError("unknown cleanup outcome")
            with self.assertRaises(RuntimeError):
                run_job()
        marker = json.loads((self.root / "archives" / "last-success.json").read_text())
        self.assertEqual(marker["remote_file_id"], "file_fixture")
        self.assertTrue(marker["remote_upload_verified"])
        self.assertFalse(marker["retention_completed"])

    def test_retained_projection_blocks_oversize_before_upload(self):
        with patch.dict(os.environ, self.settings | {"QLMS_BACKUP_STORAGE_BUDGET_BYTES": "1000"}, clear=True), \
                patch("ops.backup_job.refresh_access_token", return_value="fictional"), \
                patch("ops.backup_job.DriveStorage") as drive, \
                patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            with self.assertRaises(ValueError):
                run_job()
        drive.return_value.upload_verified.assert_not_called()
        self.assertFalse((self.root / "archives" / "last-success.json").exists())

    def test_remote_failure_preserves_archive_and_previous_success_marker(self):
        archives = self.root / "archives"
        archives.mkdir()
        marker = archives / "last-success.json"
        marker.write_text('{"completed_at":"previous"}')
        with patch.dict(os.environ, self.settings, clear=True), patch("ops.backup_job.refresh_access_token", return_value="fictional"), \
             patch("ops.backup_job.DriveStorage") as drive, patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            drive.return_value.upload_verified.side_effect = RuntimeError("remote failure")
            with self.assertRaises(RuntimeError):
                run_job()
        self.assertEqual(marker.read_text(), '{"completed_at":"previous"}')
        self.assertTrue((archives / "qlms-fixture.qlmsbackup").exists())

    def test_wrong_identity_is_checked_before_database_export(self):
        with patch.dict(os.environ, self.settings, clear=True), patch("ops.backup_job.refresh_access_token", return_value="fictional"), \
             patch("ops.backup_job.DriveStorage") as drive, patch("ops.backup_job.export_database") as export:
            drive.return_value.check_destination.side_effect = ValueError("wrong account")
            with self.assertRaises(ValueError):
                run_job()
            export.assert_not_called()

    def test_missing_verified_remote_reference_cannot_create_a_success_marker(self):
        with patch.dict(os.environ, self.settings, clear=True), patch("ops.backup_job.refresh_access_token", return_value="fictional"), \
             patch("ops.backup_job.DriveStorage") as drive, patch("ops.backup_job.export_database", side_effect=self.export_fixture):
            drive.return_value.upload_verified.return_value = None
            with self.assertRaises(ValueError):
                run_job()
        self.assertFalse((self.root / "archives" / "last-success.json").exists())

    def test_incomplete_auth_bad_key_public_schema_privileged_role_or_unpinned_image_never_export(self):
        for change in [{"QLMS_DRIVE_REFRESH_TOKEN": ""}, {"QLMS_BACKUP_KEY_BASE64": "bad"},
                       {"QLMS_BACKUP_KEY_BASE64": base64.b64encode(b"short").decode()},
                       {"QLMS_DB_SCHEMA": "public"}, {"QLMS_BACKUP_PG_CLIENT_IMAGE": "postgres:latest"},
                       {"QLMS_BACKUP_RETENTION_DAYS": "0"},
                       {"QLMS_BACKUP_CLEANUP_ENABLED": "yes"},
                       {"QLMS_BACKUP_CLEANUP_ENABLED": "true", "QLMS_BACKUP_RETENTION_DAYS": "30"},
                       {"QLMS_BACKUP_DATABASE_URL": self.settings["QLMS_BACKUP_DATABASE_URL"].replace("qlms_backup.", "postgres.")}]:
            with self.subTest(change=change), patch.dict(os.environ, {**self.settings, **change}, clear=True), \
                 patch("ops.backup_job.export_database") as export, patch("ops.backup_job.refresh_access_token") as refresh:
                with self.assertRaises((ValueError, base64.binascii.Error)):
                    run_job()
                export.assert_not_called()
                refresh.assert_not_called()

    def test_pinned_container_receives_password_via_environment_not_arguments(self):
        class Result:
            returncode, stdout = 0, b"PGDMP fixture"
        with patch("ops.backup.subprocess.run", return_value=Result()) as run:
            postgres_command("pg_dump", ["--format=custom"], self.settings["QLMS_BACKUP_DATABASE_URL"], client_image=IMAGE)
        arguments, kwargs = run.call_args
        self.assertNotIn("fictional", " ".join(arguments[0]))
        self.assertIn("PGPASSWORD", arguments[0])
        self.assertEqual(kwargs["env"]["PGPASSWORD"], "fictional")
        self.assertEqual(arguments[0][-3:], [IMAGE, "pg_dump", "--format=custom"])

    def test_container_client_cannot_be_used_for_restore_or_an_unpinned_image(self):
        for tool, image in [("pg_restore", IMAGE), ("pg_dump", "postgres:17"), ("pg_dump", "untrusted:17")]:
            with patch("ops.backup.subprocess.run") as run, self.assertRaises(ValueError):
                postgres_command(tool, [], self.settings["QLMS_BACKUP_DATABASE_URL"], client_image=image)
            run.assert_not_called()
