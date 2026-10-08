"""Cloud success needs the right private account and authenticated remote bytes."""
import hashlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from urllib.error import HTTPError

from ops.backup import encrypt_export
from ops.drive_storage import DriveStorage, refresh_access_token


ACCOUNT = "backup-owner@example.invalid"


class Reply(io.BytesIO):
    def __init__(self, body, headers=None):
        super().__init__(body if isinstance(body, bytes) else json.dumps(body).encode())
        self.headers = headers or {}


class DriveFixture:
    def __init__(self, ciphertext):
        self.requests = []
        self.ciphertext = ciphertext
        permission = {"type": "user", "role": "owner", "emailAddress": ACCOUNT}
        self.account = ACCOUNT
        self.folder = {"id": "folder_fixture", "mimeType": "application/vnd.google-apps.folder",
                       "shared": False, "trashed": False, "permissions": [permission],
                       "capabilities": {"canAddChildren": True}}
        self.file = {"id": "file_fixture", "mimeType": "application/octet-stream", "shared": False,
                     "trashed": False, "permissions": [dict(permission)], "parents": ["folder_fixture"],
                     "size": str(len(ciphertext))}
        self.session = "https://www.googleapis.com/upload/drive/v3/files?upload_id=fixture"
        self.fail_upload = False

    def open(self, request, timeout):
        self.requests.append(request)
        url = request.full_url
        if "/about?" in url:
            return Reply({"user": {"emailAddress": self.account}})
        if "/files/folder_fixture?" in url:
            return Reply(self.folder)
        if "uploadType=resumable" in url:
            return Reply({}, {"Location": self.session})
        if "upload_id=fixture" in url:
            if self.fail_upload:
                raise TimeoutError("lost upload reply contains private token")
            return Reply({"id": "file_fixture"})
        if "alt=media" in url:
            return Reply(self.ciphertext)
        if "/files/file_fixture?" in url:
            return Reply(self.file)
        raise AssertionError("Unexpected fixture request")


class DriveStorageTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.addCleanup(self.folder.cleanup)
        self.key = os.urandom(32)
        payload = b"PGDMP fictional backup records"
        metadata = {"schema": "qlms", "source_ref": "fictional",
                    "archive_sha256": hashlib.sha256(payload).hexdigest()}
        self.envelope = encrypt_export(payload, self.key, metadata)
        self.path = Path(self.folder.name) / "qlms-fixture.qlmsbackup"
        self.path.write_bytes(self.envelope)
        self.api = DriveFixture(self.envelope)
        self.storage = DriveStorage("fictional-access-token", ACCOUNT, "folder_fixture", opener=self.api)

    def test_success_requires_remote_readback_without_uploading_key_or_plaintext(self):
        self.assertEqual(self.storage.upload_verified(self.path, self.key), "file_fixture")
        uploads = [r for r in self.api.requests if r.method == "PUT"]
        self.assertEqual(len(uploads), 1)
        self.assertEqual(uploads[0].data, self.envelope)
        self.assertNotIn(self.key, uploads[0].data)
        self.assertNotIn(b"fictional backup records", uploads[0].data)

    def test_other_account_stops_before_any_upload(self):
        self.api.account = "other@example.invalid"
        with self.assertRaises(ValueError):
            self.storage.upload_verified(self.path, self.key)
        self.assertFalse(any(r.method in {"POST", "PUT"} for r in self.api.requests))

    def test_shared_incomplete_or_unwritable_folder_stops_before_upload(self):
        for change in [{"shared": True}, {"shared": None}, {"permissions": []}, {"trashed": True},
                       {"mimeType": "application/octet-stream"}, {"capabilities": {"canAddChildren": False}},
                       {"permissions": [{"type": "anyone", "role": "reader"}]}]:
            with self.subTest(change=change):
                api = DriveFixture(self.envelope)
                api.folder.update(change)
                storage = DriveStorage("fictional", ACCOUNT, "folder_fixture", opener=api)
                with self.assertRaises(ValueError):
                    storage.upload_verified(self.path, self.key)
                self.assertFalse(any(r.method in {"POST", "PUT"} for r in api.requests))

    def test_remote_file_must_have_only_the_verified_private_parent_and_owner(self):
        for change in [{"parents": ["other_folder"]}, {"parents": ["folder_fixture", "other_folder"]},
                       {"shared": True}, {"permissions": []}, {"size": "1"}, {"id": "other_file"}]:
            with self.subTest(change=change):
                api = DriveFixture(self.envelope)
                api.file.update(change)
                with self.assertRaises(ValueError):
                    DriveStorage("fictional", ACCOUNT, "folder_fixture", opener=api).upload_verified(self.path, self.key)

    def test_changed_truncated_or_oversized_download_never_succeeds(self):
        for downloaded in [self.envelope[:-1], self.envelope + b"extra",
                           self.envelope[:-1] + bytes([self.envelope[-1] ^ 1])]:
            self.api.ciphertext = downloaded
            with self.assertRaises(ValueError):
                self.storage.upload_verified(self.path, self.key)

    def test_wrong_key_or_non_database_archive_is_rejected_before_network(self):
        for key, envelope in [(os.urandom(32), self.envelope),
                              (self.key, encrypt_export(b"not a dump", self.key, {}))]:
            self.path.write_bytes(envelope)
            with self.assertRaises(ValueError):
                self.storage.upload_verified(self.path, key)
        self.assertEqual(self.api.requests, [])

    def test_untrusted_upload_location_never_receives_a_token_or_archive(self):
        for location in ["http://www.googleapis.com/upload/drive/v3/files?upload_id=x",
                         "https://untrusted.example.invalid/upload/drive/v3/files",
                         "https://www.googleapis.com@untrusted.example.invalid/upload/drive/v3/files",
                         "https://www.googleapis.com/other-path"]:
            self.api.session = location
            with self.assertRaises(ValueError):
                self.storage.upload_verified(self.path, self.key)
        self.assertFalse(any(r.method == "PUT" for r in self.api.requests))

    def test_lost_upload_reply_is_sanitized_and_never_automatically_reposted(self):
        self.api.fail_upload = True
        with self.assertRaises(RuntimeError) as error:
            self.storage.upload_verified(self.path, self.key)
        self.assertNotIn("private token", str(error.exception))
        self.assertEqual(sum(r.method == "PUT" for r in self.api.requests), 1)

    def test_oauth_refresh_errors_never_expose_provider_response_or_credentials(self):
        class BadTokenEndpoint:
            def open(self, request, timeout):
                raise HTTPError(request.full_url, 400, "private-refresh-secret", {}, io.BytesIO(b"private body"))
        with self.assertRaises(RuntimeError) as error:
            refresh_access_token("client", "private-client-secret", "private-refresh-secret", opener=BadTokenEndpoint())
        self.assertEqual(str(error.exception), "Drive authentication failed")

    def test_oauth_refresh_uses_the_fixed_endpoint_and_requires_a_bearer_token(self):
        class TokenEndpoint:
            def open(inner, request, timeout):
                self.assertEqual(request.full_url, "https://oauth2.googleapis.com/token")
                self.assertIn(b"grant_type=refresh_token", request.data)
                return Reply({"access_token": "fictional", "token_type": "Bearer"})
        self.assertEqual(refresh_access_token("client", "secret", "refresh", opener=TokenEndpoint()), "fictional")
