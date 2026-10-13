"""Private qualification proves actual delivery and confines deletion to its own fixtures."""
import io
import json
import unittest
from unittest.mock import MagicMock, patch

from ops.drive_authorize import PROJECT
from ops.qualify_backup_alerts import main as alert_main
from ops.qualify_retention import main as retention_main, rehearsal


SETTINGS = {"QLMS_BACKUP_PROJECT_REF": PROJECT, "QLMS_BACKUP_PROVIDER": "google_drive", "QLMS_DB_SCHEMA": "qlms",
            "QLMS_BACKUP_DRIVE_ACCOUNT": "owner@example.invalid", "QLMS_BACKUP_DRIVE_FOLDER_ID": "parent_fixture",
            "QLMS_DRIVE_CLIENT_ID": "fictional", "QLMS_DRIVE_CLIENT_SECRET": "fictional", "QLMS_DRIVE_REFRESH_TOKEN": "fictional",
            "QLMS_BACKUP_MONITOR_URL": "https://hc-ping.com/00000000-0000-4000-8000-000000000001"}


class AlertQualificationTests(unittest.TestCase):
    def test_typing_mistake_reprompts_without_sending_another_ping(self):
        replies = iter(["TEST ALERTS", "RECIEVED", " yes ", "", "YES"])
        with patch("sys.stdin.isatty", return_value=True), patch("ops.qualify_backup_alerts.dotenv_values", return_value=SETTINGS), \
                patch("ops.qualify_backup_alerts.signal") as send, patch("ops.qualify_backup_alerts.time.sleep") as wait, \
                patch("sys.stdout", io.StringIO()) as output, patch("sys.stderr", io.StringIO()):
            def reply(prompt):
                answer = next(replies)
                if answer in ["RECIEVED", " yes "]:
                    self.assertEqual(send.call_count, 2)
                    wait.assert_not_called()
                if answer in ["", "YES"]:
                    self.assertEqual(send.call_count, 3)
                    wait.assert_called_once_with(130)
                return answer

            with patch("builtins.input", side_effect=reply):
                self.assertEqual(alert_main(), 0)
        self.assertEqual([call.args[1] for call in send.call_args_list], ["success", "fail", "success", "success"])
        self.assertIn("PASS:", output.getvalue())
        self.assertNotIn(SETTINGS["QLMS_BACKUP_MONITOR_URL"], output.getvalue())

    def test_no_or_cancel_cannot_confirm_delivery_or_repeat_failure_pings(self):
        for replies, expected_statuses in [
                (["TEST ALERTS", "RECIEVED", "NO"], ["success", "fail"]),
                (["TEST ALERTS", "YES", "NO"], ["success", "fail", "success"]),
                (["TEST ALERTS", KeyboardInterrupt()], ["success", "fail"]),
                (["TEST ALERTS", "YES", EOFError()], ["success", "fail", "success"])]:
            with self.subTest(replies=replies), patch("sys.stdin.isatty", return_value=True), \
                    patch("ops.qualify_backup_alerts.dotenv_values", return_value=SETTINGS), \
                    patch("builtins.input", side_effect=replies), patch("ops.qualify_backup_alerts.signal") as send, \
                    patch("ops.qualify_backup_alerts.time.sleep"), patch("sys.stdout", io.StringIO()) as output, \
                    patch("sys.stderr", io.StringIO()) as errors:
                self.assertEqual(alert_main(), 1)
                self.assertEqual([call.args[1] for call in send.call_args_list], expected_statuses)
                self.assertNotIn("PASS:", output.getvalue())
                self.assertIn("FAIL:", errors.getvalue())

    def test_both_delivery_confirmations_and_actual_silence_are_required(self):
        with patch("sys.stdin.isatty", return_value=True), patch("ops.qualify_backup_alerts.dotenv_values", return_value=SETTINGS), \
                patch("builtins.input", side_effect=["TEST ALERTS", "RECEIVED", "RECEIVED"]), \
                patch("ops.qualify_backup_alerts.signal") as send, patch("ops.qualify_backup_alerts.time.sleep") as wait, \
                patch("sys.stdout", io.StringIO()) as output:
            self.assertEqual(alert_main(), 0)
        self.assertEqual([call.args[1] for call in send.call_args_list], ["success", "fail", "success", "success"])
        wait.assert_called_once_with(130)
        self.assertIn("human confirms", output.getvalue())
        self.assertNotIn(SETTINGS["QLMS_BACKUP_MONITOR_URL"], output.getvalue())

    def test_missing_email_or_secret_exception_cannot_pass(self):
        for replies in [["TEST ALERTS", "NOT RECEIVED"], ["TEST ALERTS", "RECEIVED", "NOT RECEIVED"]]:
            with patch("sys.stdin.isatty", return_value=True), patch("ops.qualify_backup_alerts.dotenv_values", return_value=SETTINGS), \
                    patch("builtins.input", side_effect=replies), patch("ops.qualify_backup_alerts.signal"), \
                    patch("ops.qualify_backup_alerts.time.sleep"), patch("sys.stdout", io.StringIO()), patch("sys.stderr", io.StringIO()) as output:
                self.assertEqual(alert_main(), 1)
                self.assertIn("FAIL:", output.getvalue())
        with patch("sys.stdin.isatty", return_value=True), patch("ops.qualify_backup_alerts.dotenv_values", side_effect=RuntimeError("private URL and token")), \
                patch("sys.stderr", io.StringIO()) as output:
            self.assertEqual(alert_main(), 1)
            self.assertNotIn("private URL", output.getvalue())


class RetentionQualificationTests(unittest.TestCase):
    def setUp(self):
        self.parent, self.child = MagicMock(), MagicMock()
        self.parent.folder_id, self.parent.account = "parent_fixture", "owner@example.invalid"
        self.created_name = None
        self.extra_contents = False
        self.folder_id = "temporary_fixture"
        self.parent.request.side_effect = self.request
        self.parent.metadata.side_effect = self.metadata
        self.parent.private_owner.return_value = True
        self.child.upload_verified.side_effect = ["expired_fixture", "fresh_fixture", "unrelated_fixture"]
        self.child.expired_archives.side_effect = [[("expired_fixture", b"digest")], []]
        self.child.prune_expired.return_value = 1
        self.child.private_owner.return_value = True
        self.child.metadata.return_value = {"parents": ["temporary_fixture"]}

    def request(self, url, **kwargs):
        if kwargs.get("method") == "POST":
            body = json.loads(kwargs["data"])
            self.assertEqual(body["parents"], ["parent_fixture"])
            self.created_name = body["name"]
            return json.dumps({"id": self.folder_id}).encode(), {}
        if kwargs.get("method") == "DELETE":
            self.assertTrue(url.endswith("/temporary_fixture"))
            return b"", {}
        files = [{"id": "fresh_fixture"}, {"id": "unrelated_fixture"}]
        if self.extra_contents:
            files.append({"id": "not_our_file"})
        return json.dumps({"files": files}).encode(), {}

    def metadata(self, file_id):
        self.assertEqual(file_id, "temporary_fixture")
        return {"id": file_id, "name": self.created_name, "parents": ["parent_fixture"],
                "mimeType": "application/vnd.google-apps.folder", "capabilities": {"canDelete": True}}

    def run_rehearsal(self):
        with patch("ops.qualify_retention.refresh_access_token", return_value="fictional"), \
                patch("ops.qualify_retention.DriveStorage", side_effect=[self.parent, self.child]):
            rehearsal(SETTINGS)

    def test_only_new_child_fixture_folder_is_written_and_removed(self):
        self.run_rehearsal()
        self.child.prune_expired.assert_called_once()
        self.assertEqual(self.child.prune_expired.call_args.args[1:], (PROJECT, "fresh_fixture", 90))
        deletes = [call for call in self.parent.request.call_args_list if call.kwargs.get("method") == "DELETE"]
        self.assertEqual(len(deletes), 1)
        self.assertTrue(deletes[0].args[0].endswith("/temporary_fixture"))
        self.assertTrue(all("parent_fixture?alt=media" not in call.args[0] for call in self.parent.request.call_args_list))

    def test_real_destination_as_new_id_or_unknown_child_file_is_never_deleted(self):
        self.folder_id = "parent_fixture"
        with self.assertRaises(ValueError):
            self.run_rehearsal()
        self.child.upload_verified.assert_not_called()
        self.assertFalse(any(call.kwargs.get("method") == "DELETE" for call in self.parent.request.call_args_list))
        self.setUp()
        self.extra_contents = True
        with self.assertRaises(ValueError):
            self.run_rehearsal()
        self.assertFalse(any(call.kwargs.get("method") == "DELETE" for call in self.parent.request.call_args_list))

    def test_unknown_upload_or_bad_plan_does_not_prune_real_destination(self):
        self.child.expired_archives.side_effect = [[("unrelated_fixture", b"digest")]]
        with self.assertRaises(ValueError):
            self.run_rehearsal()
        self.child.prune_expired.assert_not_called()
        self.parent.prune_expired.assert_not_called()

    def test_safe_failures_hide_credential_details_and_require_interactive_use(self):
        with patch("sys.stdin.isatty", return_value=True), patch("builtins.input", return_value="TEST RETENTION"), \
                patch("ops.qualify_retention.dotenv_values", side_effect=RuntimeError("private-token")), patch("sys.stderr", io.StringIO()) as output:
            self.assertEqual(retention_main(), 1)
            self.assertNotIn("private-token", output.getvalue())
        with patch("sys.stdin.isatty", return_value=False), patch("ops.qualify_retention.dotenv_values") as load, patch("sys.stderr", io.StringIO()):
            self.assertEqual(retention_main(), 1)
            load.assert_not_called()
