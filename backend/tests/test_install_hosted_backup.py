"""Fictional-only installation checks: private stdin, fixed destination and default-off schedule."""
import base64
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ops.install_hosted_backup import REPOSITORY, ENVIRONMENT, prepare_secrets, install, run_gh, main


class HostedInstallerTests(unittest.TestCase):
    def settings(self, root):
        key = root / "fictional.key"
        key.write_bytes(b"f" * 32)
        return {
            "QLMS_BACKUP_PROVIDER": "google_drive", "QLMS_DB_SCHEMA": "qlms",
            "QLMS_BACKUP_PROJECT_REF": "istweeaqtykwfuhntgik",
            "QLMS_BACKUP_DATABASE_URL": "postgresql://qlms_backup.istweeaqtykwfuhntgik:fictional@aws-1-eu-central-1.pooler.supabase.com:5432/postgres?sslmode=require",
            "QLMS_BACKUP_KEY_FILE": str(key), "QLMS_BACKUP_KEY_BASE64": "",
            "QLMS_BACKUP_DRIVE_ACCOUNT": "qinetraian@gmail.com",
            "QLMS_BACKUP_DRIVE_FOLDER_ID": "fictional_folder",
            "QLMS_DRIVE_CLIENT_ID": "fictional-client.apps.googleusercontent.com",
            "QLMS_DRIVE_CLIENT_SECRET": "fictional$literal_secret",
            "QLMS_DRIVE_REFRESH_TOKEN": "fictional-refresh",
            "QLMS_BACKUP_MONITOR_URL": "https://hc-ping.com/11111111-1111-4111-8111-111111111111",
            "QLMS_BACKUP_RETENTION_DAYS": "90", "QLMS_BACKUP_STORAGE_BUDGET_BYTES": "5000000000",
        }

    def test_validates_fixed_project_key_and_allowlisted_secrets_before_mutation(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = self.settings(Path(folder))
            secrets = prepare_secrets(settings)
            self.assertEqual(len(secrets), 8)
            self.assertEqual(base64.b64decode(secrets["QLMS_BACKUP_KEY_BASE64"]), b"f" * 32)
            self.assertNotIn("QLMS_BACKUP_KEY_FILE", secrets)
            self.assertEqual(secrets["QLMS_DRIVE_CLIENT_SECRET"], "fictional$literal_secret")
            for field, value in [("QLMS_BACKUP_PROJECT_REF", "a" * 20),
                                 ("QLMS_BACKUP_DATABASE_URL", settings["QLMS_BACKUP_DATABASE_URL"].replace("require", "disable")),
                                 ("QLMS_BACKUP_DRIVE_ACCOUNT", "other@example.invalid"),
                                 ("QLMS_BACKUP_KEY_BASE64", base64.b64encode(b"g" * 32).decode()),
                                 ("QLMS_DRIVE_REFRESH_TOKEN", "bad\nvalue")]:
                with self.subTest(field=field), self.assertRaises(ValueError):
                    prepare_secrets({**settings, field: value})

    def test_cli_uses_stdin_and_captures_errors_without_secret_arguments(self):
        with patch("ops.install_hosted_backup.subprocess.run") as process:
            process.return_value.returncode = 1
            process.return_value.stderr = "HTTP 403 private-secret-must-not-escape"
            with self.assertRaises(RuntimeError) as error:
                run_gh(Path("fake-gh.exe"), ["secret", "set", "EXAMPLE"], "private-secret-must-not-escape")
            self.assertNotIn("private-secret", str(error.exception))
            args, kwargs = process.call_args
            self.assertNotIn("private-secret-must-not-escape", args[0])
            self.assertEqual(kwargs["input"], "private-secret-must-not-escape")
            self.assertTrue(kwargs["capture_output"])

    def test_noninteractive_agent_call_never_loads_private_settings(self):
        with patch("sys.stdin.isatty", return_value=False), patch("ops.install_hosted_backup.dotenv_values") as load, patch("sys.stdout", io.StringIO()) as output:
            self.assertEqual(main(), 1)
        load.assert_not_called()
        self.assertIn("outside Codex", output.getvalue())

    def test_secrets_are_main_environment_only_and_schedule_stays_off(self):
        calls = []
        def fake_gh(executable, args, body=None, **kwargs):
            calls.append((args, body))
            if args[:2] == ["api", "user"]:
                return json.dumps({"login": "1ann0"})
            if args[:2] == ["api", f"repos/{REPOSITORY}"]:
                return json.dumps({"full_name": REPOSITORY, "default_branch": "main", "private": False})
            if "contents/.github/workflows/pilot-backup.yml" in " ".join(args):
                return json.dumps({"content": base64.b64encode(b"qualified workflow").decode()})
            if args[:2] == ["api", f"repos/{REPOSITORY}/actions/variables/QLMS_HOSTED_BACKUP_ENABLED"]:
                return None
            if args[:2] == ["api", f"repos/{REPOSITORY}/environments/{ENVIRONMENT}"] and "--method" not in args:
                return None
            if "deployment-branch-policies" in " ".join(args) and "--method" not in args:
                return json.dumps({"total_count": 1, "branch_policies": [{"name": "main", "type": "branch"}]})
            if args[:2] == ["secret", "list"]:
                return json.dumps([{"name": name} for name in secrets])
            return "{}"
        secrets = {"SECRET": "fictional-sensitive"}
        with patch("ops.install_hosted_backup.run_gh", side_effect=fake_gh), patch("ops.install_hosted_backup.WORKFLOW_SHA256", __import__("hashlib").sha256(b"qualified workflow").hexdigest()):
            install(Path("fake-gh.exe"), secrets)
        secret_call = next((args, body) for args, body in calls if args[:2] == ["secret", "set"])
        self.assertIn(ENVIRONMENT, secret_call[0])
        self.assertIn(REPOSITORY, secret_call[0])
        self.assertEqual(secret_call[1], "fictional-sensitive")
        activation = [(args, body) for args, body in calls if args[:2] == ["variable", "set"]]
        daily = [args for args, body in activation if "QLMS_HOSTED_BACKUP_ENABLED" in args]
        self.assertEqual(len(daily), 1)
        self.assertEqual(daily[0][-1], "false")
        self.assertEqual(activation[-1][0][2], "QLMS_BACKUP_QUALIFICATION_ENABLED")
        self.assertEqual(activation[-1][0][-1], "true")

    def test_rejects_an_environment_that_can_expose_secrets_to_other_branches(self):
        def fake_gh(executable, args, body=None, **kwargs):
            if args[:2] == ["api", "user"]:
                return json.dumps({"login": "1ann0"})
            if args[:2] == ["api", f"repos/{REPOSITORY}"]:
                return json.dumps({"full_name": REPOSITORY, "default_branch": "main", "private": False})
            if "contents/" in " ".join(args):
                return json.dumps({"content": base64.b64encode(b"qualified workflow").decode()})
            if "actions/variables/" in " ".join(args):
                return None
            if "environments/" in " ".join(args):
                return json.dumps({"deployment_branch_policy": None})
            self.fail("No secrets should be installed")
        with patch("ops.install_hosted_backup.run_gh", side_effect=fake_gh), patch("ops.install_hosted_backup.WORKFLOW_SHA256", __import__("hashlib").sha256(b"qualified workflow").hexdigest()):
            with self.assertRaises(ValueError):
                install(Path("fake-gh.exe"), {"SECRET": "fictional-sensitive"})


if __name__ == "__main__":
    unittest.main()
