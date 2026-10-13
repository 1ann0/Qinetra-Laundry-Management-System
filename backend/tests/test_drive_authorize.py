"""Automation consent uses fictional credentials, selected folders and loopback callbacks."""
from contextlib import redirect_stdout
from io import StringIO
import json
import http.client
from pathlib import Path
import tempfile
import threading
import unittest
from unittest.mock import patch
from urllib.parse import parse_qs, urlencode, urlsplit

from ops import drive_authorize as grant
from tests.test_drive_storage import ACCOUNT, DriveFixture, Reply


CLIENT = {"client_id": "fictional.apps.googleusercontent.com", "client_secret": "fictional-client-secret",
          "auth_uri": grant.AUTH_URL, "token_uri": grant.TOKEN_URL}
TOKENS = {"access_token": "fictional-access", "refresh_token": "fictional-refresh",
          "scope": grant.SCOPE, "token_type": "Bearer", "expires_in": 3600}


def callback(**changes):
    fields = {"state": "fictional-state", "picked_file_ids": "folder_fixture", "code": "fictional-code",
              "scope": grant.SCOPE} | changes
    return "/callback?" + urlencode(fields)


class GrantTests(unittest.TestCase):
    def test_authorization_selects_only_one_folder_with_pkce_and_offline_scope(self):
        url = grant.authorization_url(CLIENT, "folder_fixture", "owner@example.invalid",
                                      "http://127.0.0.1:43210/callback", "fictional-state", "fictional-verifier")
        parsed = urlsplit(url)
        self.assertEqual(parsed.scheme + "://" + parsed.netloc + parsed.path, grant.AUTH_URL)
        query = parse_qs(parsed.query)
        for name, value in {"scope": grant.SCOPE, "access_type": "offline", "prompt": "consent",
                            "trigger_onepick": "true", "file_ids": "folder_fixture",
                            "allow_folder_selection": "true", "include_granted_scopes": "false",
                            "code_challenge_method": "S256", "state": "fictional-state"}.items():
            self.assertEqual(query[name], [value])
        self.assertEqual(query["code_challenge"], ["KzA6JaCnPXMihJJl4lfZNLysEtBe41G9T_PSfBOwW24"])
        self.assertNotIn("client_secret", query)
        self.assertNotIn("allow_multiple", query)

    def test_callback_rejects_wrong_state_folder_scope_path_duplicates_or_cancellation(self):
        invalid = [callback(state="other"), callback(picked_file_ids="wrong_folder"),
                   callback(picked_file_ids="folder_fixture,other"), callback(scope=grant.SCOPE + " email"),
                   callback(error="access_denied"), callback(code=""), callback(code="private\r\ncode"),
                   callback() + "&state=fictional-state", callback().replace("/callback?", "/other?"),
                   "/callback?" + "x" * 16385]
        for path in invalid:
            with self.subTest(path=path[:30]), self.assertRaises(ValueError):
                grant.callback_code(path, "fictional-state", "folder_fixture")
        self.assertEqual(grant.callback_code(callback(), "fictional-state", "folder_fixture"), "fictional-code")

    def test_client_file_and_destination_checks_block_web_clients_and_wrong_project(self):
        self.assertEqual(grant.validate_client({"installed": CLIENT}), CLIENT)
        for data in [{"web": CLIENT}, {"installed": CLIENT | {"token_uri": "https://untrusted.invalid"}},
                     {"installed": CLIENT | {"client_id": "other"}},
                     {"installed": CLIENT | {"client_secret": "bad\nsecret"}}]:
            with self.assertRaises(ValueError):
                grant.validate_client(data)
        settings = {"QLMS_BACKUP_PROJECT_REF": grant.PROJECT, "QLMS_BACKUP_PROVIDER": "google_drive",
                    "QLMS_DB_SCHEMA": "qlms", "QLMS_BACKUP_DRIVE_ACCOUNT": "owner@example.invalid",
                    "QLMS_BACKUP_DRIVE_FOLDER_ID": "folder_fixture"}
        grant.validate_destination(settings)
        for changes in [{"QLMS_BACKUP_PROJECT_REF": "practice"}, {"QLMS_BACKUP_DRIVE_FOLDER_ID": "../other"},
                        {"QLMS_BACKUP_DRIVE_ACCOUNT": ""}, {"QLMS_DB_SCHEMA": "public"}]:
            with self.assertRaises(ValueError):
                grant.validate_destination(settings | changes)

    def test_token_exchange_is_post_only_pkce_and_requires_reusable_narrow_grant(self):
        class Transport:
            def open(self, request, timeout):
                self.request = request
                return Reply(TOKENS)
        transport = Transport()
        self.assertEqual(grant.exchange_code(CLIENT, "fictional-code", "http://127.0.0.1:43210/callback",
                                             "fictional-verifier", opener=transport), TOKENS)
        self.assertEqual(transport.request.full_url, grant.TOKEN_URL)
        self.assertEqual(transport.request.method, "POST")
        self.assertEqual(parse_qs(transport.request.data.decode())["code_verifier"], ["fictional-verifier"])
        for changes in [{"scope": grant.SCOPE + " email"}, {"refresh_token": ""}, {"token_type": "MAC"},
                        {"refresh_token_expires_in": 604800}, {"access_token": "bad\r\ntoken"}, {"expires_in": True}]:
            with patch.object(grant, "send_request", return_value=(json.dumps(TOKENS | changes).encode(), {})), \
                    self.assertRaises(ValueError):
                grant.exchange_code(CLIENT, "fictional-code", "http://127.0.0.1:43210/callback", "fictional-verifier")

    def test_private_update_preserves_other_settings_and_checks_every_field_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fictional.env"
            original = "KEEP=fictional\n" + "\n".join(name + "=" for name in grant.GRANT_KEYS) + "\n"
            path.write_text(original, encoding="utf-8")
            grant.save_grant(path, CLIENT, TOKENS)
            saved = path.read_text(encoding="utf-8")
            self.assertIn("KEEP=fictional", saved)
            self.assertIn("QLMS_DRIVE_REFRESH_TOKEN=fictional-refresh", saved)
            invalid = original + "QLMS_DRIVE_CLIENT_ID=duplicate\n"
            path.write_text(invalid, encoding="utf-8")
            with self.assertRaises(ValueError):
                grant.save_grant(path, CLIENT, TOKENS)
            self.assertEqual(path.read_text(encoding="utf-8"), invalid)

    def test_verified_account_and_private_folder_are_required_before_saving(self):
        api = DriveFixture(b"fictional")
        api.account = "wrong@example.invalid"
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fictional.env"
            original = "\n".join(name + "=" for name in grant.GRANT_KEYS)
            path.write_text(original, encoding="utf-8")
            settings = {"QLMS_BACKUP_DRIVE_ACCOUNT": "owner@example.invalid", "QLMS_BACKUP_DRIVE_FOLDER_ID": "folder_fixture"}
            with self.assertRaises(ValueError):
                grant.verify_and_save(path, CLIENT, TOKENS, settings, opener=api)
            self.assertEqual(path.read_text(encoding="utf-8"), original)

    def test_noninteractive_use_loads_no_credentials_and_failures_are_sanitized(self):
        with patch.object(grant.sys.stdin, "isatty", return_value=False), \
                patch.object(grant, "run_authorization") as run, redirect_stdout(StringIO()) as output:
            self.assertEqual(grant.main(), 1)
        run.assert_not_called()
        self.assertNotIn("fictional-refresh", output.getvalue())
        with patch.object(grant.sys.stdin, "isatty", return_value=True), \
                patch.object(grant, "run_authorization", side_effect=RuntimeError("private secret")), \
                redirect_stdout(StringIO()) as output:
            self.assertEqual(grant.main(), 1)
        self.assertNotIn("private secret", output.getvalue())

    def test_successful_verified_grant_updates_only_private_settings(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fictional.env"
            path.write_text("\n".join(name + "=" for name in grant.GRANT_KEYS), encoding="utf-8")
            settings = {"QLMS_BACKUP_DRIVE_ACCOUNT": ACCOUNT, "QLMS_BACKUP_DRIVE_FOLDER_ID": "folder_fixture"}
            grant.verify_and_save(path, CLIENT, TOKENS, settings, opener=DriveFixture(b"fictional"))
            self.assertIn("QLMS_DRIVE_REFRESH_TOKEN=fictional-refresh", path.read_text(encoding="utf-8"))

    def test_setup_failures_explain_known_checks_but_never_echo_unknown_private_errors(self):
        cases = [
            (grant.validate_destination, {}, "Use the existing pilot backup configuration"),
            (grant.validate_client, {"web": CLIENT}, "Use the downloaded Google Desktop application client"),
            (grant.validate_client, {"installed": CLIENT | {"client_id": "wrong"}}, "Invalid Google client"),
        ]
        for validator, data, expected in cases:
            with self.subTest(expected=expected):
                with self.assertRaises(ValueError) as failure:
                    validator(data)
                with patch.object(grant.sys.stdin, "isatty", return_value=True), \
                        patch.object(grant, "run_authorization", side_effect=failure.exception), \
                        redirect_stdout(StringIO()) as output:
                    self.assertEqual(grant.main(), 1)
                self.assertIn(expected, output.getvalue())
                self.assertIn("no backup schedule activated", output.getvalue())
        for failure in [ValueError("private-client-secret"),
                        json.JSONDecodeError("private-client-secret", "private-document", 0)]:
            with patch.object(grant.sys.stdin, "isatty", return_value=True), \
                    patch.object(grant, "run_authorization", side_effect=failure), \
                    redirect_stdout(StringIO()) as output:
                self.assertEqual(grant.main(), 1)
            self.assertIn(type(failure).__name__, output.getvalue())
            self.assertNotIn("private-client-secret", output.getvalue())
            self.assertNotIn("private-document", output.getvalue())

    def test_loopback_callback_rejects_foreign_host_and_does_not_echo_codes_or_log(self):
        with grant.consent_server("fictional-state", "folder_fixture") as server:
            self.assertEqual(server.server_address[0], "127.0.0.1")
            for host, status in [("untrusted.invalid", 400), (f"127.0.0.1:{server.server_port}", 200)]:
                thread = threading.Thread(target=server.handle_request)
                thread.start()
                try:
                    connection = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=5)
                    connection.request("GET", callback(), headers={"Host": host})
                    response = connection.getresponse()
                    self.assertEqual(response.status, status)
                    self.assertEqual(response.headers["Cache-Control"], "no-store")
                    self.assertNotIn("fictional-code", response.read().decode())
                    if status == 400:
                        self.assertIsNone(server.code)
                    connection.close()
                finally:
                    thread.join(timeout=6)
                    self.assertFalse(thread.is_alive())
            self.assertEqual(server.code, "fictional-code")


if __name__ == "__main__":
    unittest.main()
