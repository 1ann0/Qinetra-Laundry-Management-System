"""Only authenticated expired copies may be removed after a fresh backup passes."""
from datetime import datetime, timedelta, timezone
import hashlib
import json
import os
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

from ops.backup import encrypt_export
from ops.drive_storage import DriveStorage
from tests.test_drive_storage import ACCOUNT, DriveFixture, Reply


PROJECT = "a" * 20
NOW = datetime(2026, 10, 13, 10, 0, 0, tzinfo=timezone.utc)


class RetentionFixture(DriveFixture):
    def __init__(self):
        super().__init__(b"")
        self.key = os.urandom(32)
        self.records, self.deleted = {}, []
        self.incomplete, self.pages, self.fail_delete, self.change_old = False, False, False, False
        self.old_reads = 0
        self.share_fresh_after_listing = False
        for file_id, age in [("fresh_file", 0), ("old_file", 91), ("boundary_file", 90), ("recent_file", 89)]:
            self.add(file_id, NOW - timedelta(days=age))
        self.records["unrelated_file"] = ({"id": "unrelated_file", "name": "shop-notes.txt"}, b"notes")

    def add(self, file_id, created, *, project=PROJECT, payload=b"PGDMP fictional retention archive"):
        encrypted = encrypt_export(payload, self.key, {"schema": "qlms", "source_ref": project,
            "created_at": created.isoformat(), "archive_sha256": hashlib.sha256(payload).hexdigest()})
        metadata = {**self.file, "id": file_id, "name": created.strftime("qlms-%Y%m%dT%H%M%S%fZ.qlmsbackup"),
                    "size": str(len(encrypted)), "capabilities": {"canDelete": True}}
        self.records[file_id] = (metadata, encrypted)

    def open(self, request, timeout):
        parsed = urlsplit(request.full_url)
        if parsed.path == "/drive/v3/files":
            self.requests.append(request)
            if self.share_fresh_after_listing:
                self.records["fresh_file"][0]["shared"] = True
            query = parse_qs(parsed.query)
            assert query["q"] == ["'folder_fixture' in parents and trashed=false"]
            records = list(self.records.values())
            if self.pages:
                records = records[2:] if "pageToken" in query else records[:2]
            result = {"files": [{"id": item[0]["id"], "name": item[0]["name"]} for item in records],
                      "incompleteSearch": self.incomplete}
            if self.pages and "pageToken" not in query:
                result["nextPageToken"] = "next-fixture-page"
            return Reply(result)
        file_id = parsed.path.rsplit("/", 1)[-1]
        if file_id in self.records:
            self.requests.append(request)
            metadata, ciphertext = self.records[file_id]
            if request.method == "DELETE":
                if self.fail_delete:
                    raise TimeoutError("lost deletion response private-token")
                self.deleted.append(file_id)
                return Reply(b"")
            if "alt=media" in parsed.query:
                if file_id == "old_file":
                    self.old_reads += 1
                    if self.change_old and self.old_reads == 2:
                        self.add(file_id, NOW - timedelta(days=91))
                        ciphertext = self.records[file_id][1]
                return Reply(ciphertext)
            return Reply(metadata)
        return super().open(request, timeout)


class RetentionTests(unittest.TestCase):
    def setUp(self):
        self.api = RetentionFixture()
        self.storage = DriveStorage("fictional", ACCOUNT, "folder_fixture", opener=self.api)

    def prune(self):
        with patch("ops.drive_storage.datetime", wraps=datetime) as clock:
            clock.now.return_value = NOW
            return self.storage.prune_expired(self.api.key, PROJECT, "fresh_file", 90)

    def test_exact_90_day_boundary_fresh_copy_and_unrelated_files_are_preserved(self):
        self.api.pages = True
        self.assertEqual(self.prune(), 1)
        self.assertEqual(self.api.deleted, ["old_file"])
        self.assertTrue(all(r.full_url.endswith("/old_file") for r in self.api.requests if r.method == "DELETE"))

    def test_wrong_key_or_stale_fresh_copy_wrong_policy_and_naive_time_do_not_delete(self):
        for key, project, keep, days, now in [(os.urandom(32), PROJECT, "fresh_file", 90, NOW),
                (self.api.key, PROJECT, "old_file", 90, NOW), (self.api.key, "b" * 20, "fresh_file", 90, NOW),
                (self.api.key, PROJECT, "fresh_file", 30, NOW), (self.api.key, PROJECT, "fresh_file", 90, NOW.replace(tzinfo=None))]:
            with self.subTest(keep=keep, days=days), self.assertRaises(ValueError):
                self.storage.expired_archives(key, project, keep, days, now=now)
        self.assertEqual(self.api.deleted, [])

    def test_entire_plan_must_be_safe_before_any_deletion(self):
        for mutation in ["shared", "parent", "project", "delete_permission", "corrupt"]:
            with self.subTest(mutation=mutation):
                api = RetentionFixture()
                api.add("bad_old_file", NOW - timedelta(days=92))
                metadata, ciphertext = api.records["bad_old_file"]
                if mutation == "shared":
                    metadata["shared"] = True
                elif mutation == "parent":
                    metadata["parents"] = ["other_folder"]
                elif mutation == "project":
                    api.add("bad_old_file", NOW - timedelta(days=92), project="b" * 20)
                elif mutation == "delete_permission":
                    metadata["capabilities"] = {"canDelete": False}
                else:
                    api.records["bad_old_file"] = (metadata, ciphertext[:-1] + bytes([ciphertext[-1] ^ 1]))
                storage = DriveStorage("fictional", ACCOUNT, "folder_fixture", opener=api)
                with self.assertRaises(ValueError):
                    storage.expired_archives(api.key, PROJECT, "fresh_file", 90, now=NOW)
                self.assertEqual(api.deleted, [])

    def test_changed_archive_after_plan_or_incomplete_search_is_refused(self):
        self.api.incomplete = True
        with self.assertRaises(ValueError):
            self.prune()
        self.api.incomplete, self.api.change_old = False, True
        with self.assertRaises(ValueError):
            self.prune()
        self.assertEqual(self.api.deleted, [])

    def test_unknown_delete_outcome_is_sanitized_and_never_retried(self):
        self.api.fail_delete = True
        with self.assertRaises(RuntimeError) as error:
            self.prune()
        self.assertEqual(str(error.exception), "Private Drive request failed")
        self.assertEqual(sum(r.method == "DELETE" for r in self.api.requests), 1)

    def test_fresh_backup_changed_after_plan_blocks_old_archive_deletion(self):
        self.api.share_fresh_after_listing = True
        with self.assertRaises(ValueError):
            self.prune()
        self.assertEqual(self.api.deleted, [])

    def test_backdated_name_cannot_override_authenticated_creation_time(self):
        metadata, _ = self.api.records["recent_file"]
        metadata["name"] = (NOW - timedelta(days=100)).strftime("qlms-%Y%m%dT%H%M%S%fZ.qlmsbackup")
        with self.assertRaises(ValueError):
            self.prune()
        self.assertEqual(self.api.deleted, [])
