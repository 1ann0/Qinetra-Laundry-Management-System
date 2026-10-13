"""Recovery must use remote ciphertext, separate key custody and a disposable target."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ops.backup import encrypt_export
from ops.verify_pilot_restore import IMAGE, PROJECT, data_manifest, download_archive, main, recovery_settings, restore_and_compare
from tests.test_drive_storage import ACCOUNT, DriveFixture
from ops.drive_storage import DriveStorage


DATA = b"COPY qlms.payments (id, amount, note) FROM stdin;\n1\t900.00\tfictional\\nrefund\n2\t50.00\t\\N\n\\.\nSELECT pg_catalog.setval('qlms.payments_id_seq', 2, true);\n"


class PilotRestoreTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.root = Path(self.folder.name)
        self.key = os.urandom(32)
        self.settings = {
            "QLMS_BACKUP_PROVIDER": "google_drive", "QLMS_BACKUP_PROJECT_REF": PROJECT, "QLMS_DB_SCHEMA": "qlms",
            "QLMS_BACKUP_DATABASE_URL": f"postgresql://qlms_backup.{PROJECT}:fictional@aws-1-eu.pooler.supabase.com/postgres?sslmode=require",
            "QLMS_BACKUP_LOCAL_FOLDER": str(self.root), "QLMS_BACKUP_KEY_FILE": str(self.root / "original.key"),
            "QLMS_BACKUP_PG_CLIENT_IMAGE": IMAGE, "QLMS_BACKUP_DRIVE_ACCOUNT": ACCOUNT,
            "QLMS_BACKUP_DRIVE_FOLDER_ID": "folder_fixture", "QLMS_DRIVE_CLIENT_ID": "fictional",
            "QLMS_DRIVE_CLIENT_SECRET": "fictional", "QLMS_DRIVE_REFRESH_TOKEN": "fictional",
        }
        self.dump = b"PGDMP fictional records"
        self.envelope = encrypt_export(self.dump, self.key, {"schema": "qlms", "source_ref": PROJECT,
            "archive_sha256": hashlib.sha256(self.dump).hexdigest()})
        self.api = DriveFixture(self.envelope)
        self.storage = DriveStorage("fictional", ACCOUNT, "folder_fixture", opener=self.api)
        (self.root / "last-success.json").write_text(json.dumps({"remote_upload_verified": True,
            "remote_file_id": "file_fixture", "archive_bytes": len(self.envelope)}))

    def test_fresh_remote_read_without_upload_or_original_archive(self):
        with patch("ops.verify_pilot_restore.refresh_access_token", return_value="fictional"), \
                patch("ops.verify_pilot_restore.DriveStorage", return_value=self.storage):
            self.assertEqual(download_archive(self.settings, self.key, self.root / "download.qlmsbackup"), self.dump)
        self.assertEqual((self.root / "download.qlmsbackup").read_bytes(), self.envelope)
        self.assertTrue(any("alt=media" in r.full_url for r in self.api.requests))
        self.assertTrue(all(r.method == "GET" for r in self.api.requests))

    def test_wrong_copy_tampering_wrong_source_and_shared_or_moved_archive_block_restore(self):
        variants = ["key", "tamper", "source", "schema", "shared", "parent", "size", "owner"]
        for variant in variants:
            with self.subTest(variant=variant):
                self.setUp()
                key = self.key
                if variant == "key":
                    key = os.urandom(32)
                elif variant == "tamper":
                    self.api.ciphertext = self.envelope[:-1] + bytes([self.envelope[-1] ^ 1])
                elif variant in {"source", "schema"}:
                    self.api.ciphertext = encrypt_export(self.dump, self.key, {"schema": "other" if variant == "schema" else "qlms",
                        "source_ref": "a" * 20 if variant == "source" else PROJECT,
                        "archive_sha256": hashlib.sha256(self.dump).hexdigest()})
                    self.api.file["size"] = str(len(self.api.ciphertext))
                    (self.root / "last-success.json").write_text(json.dumps({"remote_upload_verified": True,
                        "remote_file_id": "file_fixture", "archive_bytes": len(self.api.ciphertext)}))
                elif variant == "shared":
                    self.api.file["shared"] = True
                elif variant == "parent":
                    self.api.file["parents"] = ["other_folder"]
                elif variant == "size":
                    self.api.file["size"] = "1"
                elif variant == "owner":
                    self.api.file["permissions"][0]["emailAddress"] = "other@example.invalid"
                with patch("ops.verify_pilot_restore.refresh_access_token", return_value="fictional"), \
                        patch("ops.verify_pilot_restore.DriveStorage", return_value=self.storage), self.assertRaises(ValueError):
                    download_archive(self.settings, key, self.root / "refused.qlmsbackup")
                self.assertFalse((self.root / "refused.qlmsbackup").exists())

    def test_only_fixed_pilot_restricted_connection_and_pinned_image_are_accepted(self):
        recovery_settings(self.settings)
        for changes in [{"QLMS_BACKUP_PROJECT_REF": "a" * 20}, {"QLMS_DB_SCHEMA": "public"},
                        {"QLMS_BACKUP_DATABASE_URL": self.settings["QLMS_BACKUP_DATABASE_URL"].replace("qlms_backup", "postgres")},
                        {"QLMS_BACKUP_DATABASE_URL": self.settings["QLMS_BACKUP_DATABASE_URL"].replace("require", "disable")},
                        {"QLMS_BACKUP_PG_CLIENT_IMAGE": "postgres:17"}]:
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                recovery_settings({**self.settings, **changes})

    def test_manifest_preserves_money_nulls_escaped_notes_duplicates_and_sequence_state(self):
        expected = data_manifest(DATA)
        reordered = DATA.replace(b"1\t900.00\tfictional\\nrefund\n2\t50.00\t\\N", b"2\t50.00\t\\N\n1\t900.00\tfictional\\nrefund")
        self.assertEqual(expected, data_manifest(reordered))
        for different in [DATA.replace(b"900.00", b"850.00"), DATA.replace(b", 2, true", b", 3, true"),
                          DATA.replace(b"1\t900.00\tfictional\\nrefund\n", b"1\t900.00\tfictional\\nrefund\n1\t900.00\tfictional\\nrefund\n")]:
            self.assertNotEqual(expected, data_manifest(different))
        for malformed in [b"", DATA.split(b"\\.")[0], DATA.replace(b"qlms.payments (", b"public.payments ("),
                          DATA + DATA, b"INSERT INTO qlms.payments VALUES (1);\n"]:
            with self.assertRaises(ValueError):
                data_manifest(malformed)

    def test_unknown_start_outcome_still_removes_only_generated_container_and_restores_context(self):
        with patch.dict(os.environ, {"DOCKER_CONTEXT": "fixture-original"}), \
                patch("ops.verify_pilot_restore.docker", side_effect=[TimeoutError("private"), ""]) as command:
            with self.assertRaises(TimeoutError):
                restore_and_compare("source", "archive", self.key)
            self.assertEqual(os.environ["DOCKER_CONTEXT"], "fixture-original")
        run, cleanup = command.call_args_list
        name = run.args[0][run.args[0].index("--name") + 1]
        self.assertTrue(name.startswith("qlms-save-test-restore-"))
        self.assertEqual(cleanup.args[0], ["rm", "--force", "--volumes", name])
        self.assertNotIn("--volume", run.args[0])
        self.assertEqual(run.args[0][run.args[0].index("--publish") + 1], "127.0.0.1::5432")
        self.assertNotIn(run.kwargs["environment"]["POSTGRES_PASSWORD"], str(run.args))

    def test_lost_money_row_and_cleanup_failure_cannot_pass(self):
        archive = self.root / "fixture.qlmsbackup"
        archive.write_bytes(self.envelope)
        for changed, cleanup in [(DATA.replace(b"900.00", b"850.00"), ""), (DATA, RuntimeError("private cleanup details"))]:
            with self.subTest(changed=changed != DATA), patch("ops.verify_pilot_restore.create_engine"), \
                    patch("ops.verify_pilot_restore.docker", side_effect=["fictional-id", "127.0.0.1:55888", cleanup]) as command, \
                    patch("ops.verify_pilot_restore.postgres_command", side_effect=[DATA, changed]), \
                    patch("ops.verify_pilot_restore.restore_database") as restore, self.assertRaises((ValueError, RuntimeError)):
                restore_and_compare(self.settings["QLMS_BACKUP_DATABASE_URL"], archive, self.key)
            restore.assert_called_once()
            self.assertEqual(command.call_args.args[0][:3], ["rm", "--force", "--volumes"])

    def test_noninteractive_and_secret_bearing_failures_never_print_details(self):
        output = io.StringIO()
        with patch("sys.stdin.isatty", return_value=True), patch("ops.verify_pilot_restore.dotenv_values",
                side_effect=RuntimeError("secret customer password")), patch("sys.stderr", output):
            self.assertEqual(main(), 1)
        self.assertNotIn("secret customer password", output.getvalue())
        with patch("sys.stdin.isatty", return_value=False), patch("ops.verify_pilot_restore.dotenv_values") as load, patch("sys.stderr", io.StringIO()):
            self.assertEqual(main(), 1)
            load.assert_not_called()

    def test_recovery_uses_separate_copy_even_when_original_is_unavailable(self):
        vault = self.root / "separate-vault"
        vault.mkdir()
        copy = vault / "backup.key"
        copy.write_bytes(self.key)
        settings = {**self.settings, "QLMS_BACKUP_LOCAL_FOLDER": str(self.root / "archives")}
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value=str(copy)), \
                patch("ops.verify_pilot_restore.dotenv_values", return_value=settings), \
                patch("ops.verify_pilot_restore.download_archive") as download, \
                patch("ops.verify_pilot_restore.restore_and_compare", return_value=22) as restore, patch("sys.stdout", io.StringIO()) as output:
            self.assertEqual(main(), 0)
            self.assertEqual(download.call_args.args[1], self.key)
            self.assertEqual(restore.call_args.args[2], self.key)
            self.assertIn("22 tables", output.getvalue())
            self.assertNotIn(str(copy), output.getvalue())

    def test_original_key_same_file_alias_and_key_inside_archives_cannot_be_used(self):
        original = self.root / "original.key"
        original.write_bytes(self.key)
        alias = self.root / "alias.key"
        os.link(original, alias)
        archives = self.root / "archives"
        archives.mkdir()
        inside = archives / "backup.key"
        inside.write_bytes(self.key)
        settings = {**self.settings, "QLMS_BACKUP_LOCAL_FOLDER": str(archives)}
        for copy in (original, alias, inside):
            with self.subTest(copy=copy.name), patch("sys.stdin.isatty", return_value=True), \
                    patch("builtins.input", return_value=str(copy)), patch("ops.verify_pilot_restore.dotenv_values", return_value=settings), \
                    patch("ops.verify_pilot_restore.download_archive") as download, patch("sys.stderr", io.StringIO()):
                self.assertEqual(main(), 1)
                download.assert_not_called()


if __name__ == "__main__":
    unittest.main()
