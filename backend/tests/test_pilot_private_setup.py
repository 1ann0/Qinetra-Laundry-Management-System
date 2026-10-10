"""Fictional credentials only: setup cannot print secrets or target the practice project."""
from contextlib import redirect_stderr, redirect_stdout
from io import StringIO
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from sqlalchemy.engine import make_url
from ops import pilot_private_setup as setup


class PrivatePilotSetupTests(unittest.TestCase):
    def write_fixtures(self, directory):
        fixture_password = "fictional-admin-password-only"
        files = {
            "admin-setup": f"QLMS_PILOT_PROJECT_REF={setup.PROJECT}\nQLMS_PILOT_DB_HOST={setup.HOST}\n"
                           f"QLMS_PILOT_DB_PORT=5432\nQLMS_PILOT_DB_NAME=postgres\nQLMS_PILOT_ADMIN_USER=postgres.{setup.PROJECT}\n"
                           f"QLMS_PILOT_ADMIN_PASSWORD={fixture_password}\n",
            "db-credentials": "QLMS_RUNTIME_PASSWORD=fictional-runtime-password-only\nQLMS_BACKUP_PASSWORD=fictional-backup-password-only\n",
            "runtime": "QLMS_ENV=production\nQLMS_DB_SCHEMA=qlms\nQLMS_DB_USER=qlms_runtime\nDATABASE_URL=\n"
                       "SECRET_KEY=fictional-signing-secret-at-least-thirty-two-bytes\nALLOWED_ORIGINS=\n",
            "hosted-backup": f"QLMS_BACKUP_PROJECT_REF={setup.PROJECT}\nQLMS_DB_SCHEMA=qlms\nQLMS_BACKUP_DATABASE_URL=\n"
                             "QLMS_DRIVE_REFRESH_TOKEN=fictional-preserved-token\n",
        }
        for name, content in files.items():
            (directory / (".env.pilot-" + name)).write_text(content, encoding="utf-8")

    def test_wrong_project_rejected_before_any_connection_or_role_change(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.write_fixtures(directory)
            path = directory / ".env.pilot-admin-setup"
            path.write_text(path.read_text().replace(setup.PROJECT, "owetwiekmoycshdijmtl"))
            with patch.object(setup.psycopg2, "connect") as connect, self.assertRaises(ValueError):
                setup.run_setup(directory)
            connect.assert_not_called()

    def test_missing_duplicate_or_other_connection_never_changes_roles(self):
        for content in ["", "DATABASE_URL=\nDATABASE_URL=\n", "DATABASE_URL=postgresql://practice/unused\n"]:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                self.write_fixtures(directory)
                (directory / ".env.pilot-runtime").write_text(content)
                with patch.object(setup, "assign_passwords") as assign, self.assertRaises(ValueError):
                    setup.run_setup(directory)
                assign.assert_not_called()

    def test_password_symbols_round_trip_and_other_private_settings_preserved(self):
        password = "fictional $!#@:/%'\\ password"
        url = setup.connection_url("qlms_runtime", password)
        parsed = make_url(url)
        self.assertEqual((parsed.username, parsed.host, parsed.password, parsed.query.get("sslmode")),
                         ("qlms_runtime." + setup.PROJECT, setup.HOST, password, "require"))
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / ".env.fixture"
            original = b"# preserve\r\nDATABASE_URL=\r\nSECRET_KEY=fictional-preserved-value\r\n"
            path.write_bytes(original)
            setup.save_connection(path, "DATABASE_URL", url)
            self.assertEqual(path.read_bytes(), original.replace(b"DATABASE_URL=", ("DATABASE_URL=" + url).encode()))

    def test_sql_receives_only_the_scram_verifier_and_rechecks_grants(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        credentials = {key: "fictional-" + role for role, key in setup.ROLE_KEYS.items()}
        with patch.object(setup, "check_database", return_value=["unchanged rights"]) as check, \
                patch.object(setup, "encrypt_password", return_value="SCRAM-SHA-256$fictional-verifier") as encrypt:
            setup.assign_passwords(connection, credentials)
        self.assertEqual(check.call_count, 2)
        self.assertEqual(encrypt.call_count, 2)
        for call in cursor.execute.call_args_list:
            self.assertTrue(call.args[0].startswith('ALTER ROLE "qlms_'))
            self.assertEqual(call.args[1], ("SCRAM-SHA-256$fictional-verifier",))
            self.assertNotIn("fictional-qlms_", call.args[0])

    def test_grant_change_raises_inside_transaction(self):
        connection = MagicMock()
        with patch.object(setup, "check_database", side_effect=[["before"], ["different"]]), \
                patch.object(setup, "encrypt_password", return_value="SCRAM-SHA-256$fictional-verifier"), \
                self.assertRaises(ValueError):
            setup.assign_passwords(connection, {key: "fictional-fixture" for key in setup.ROLE_KEYS.values()})
        self.assertIs(connection.__exit__.call_args.args[0], ValueError)

    def test_failed_role_connection_does_not_write_private_urls(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.write_fixtures(directory)
            original = (directory / ".env.pilot-runtime").read_bytes()
            connection = MagicMock()
            connection.info.ssl_in_use = True
            with patch.object(setup.psycopg2, "connect", return_value=connection), \
                    patch.object(setup, "assign_passwords"), \
                    patch.object(setup, "check_role_connection", side_effect=ValueError("fictional-secret")), \
                    redirect_stdout(StringIO()), self.assertRaises(ValueError):
                setup.run_setup(directory)
            self.assertEqual((directory / ".env.pilot-runtime").read_bytes(), original)
            connection.close.assert_called_once()

    def test_cli_failure_never_echoes_driver_secret_or_traceback(self):
        output, error = StringIO(), StringIO()
        with patch.object(setup, "run_setup", side_effect=RuntimeError("fictional-sensitive-password")), \
                redirect_stdout(output), redirect_stderr(error):
            self.assertEqual(setup.main(), 1)
        self.assertNotIn("fictional-sensitive-password", output.getvalue() + error.getvalue())
        self.assertNotIn("Traceback", error.getvalue())
        self.assertIn("FAIL: private pilot setup (RuntimeError)", error.getvalue())

    def test_unencrypted_admin_never_assigns_credentials(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            self.write_fixtures(directory)
            connection = MagicMock()
            connection.info.ssl_in_use = False
            with patch.object(setup.psycopg2, "connect", return_value=connection), \
                    patch.object(setup, "assign_passwords") as assign, self.assertRaises(ValueError):
                setup.run_setup(directory)
            assign.assert_not_called()
            connection.close.assert_called_once()

    def test_unsafe_role_authority_stops_before_count_or_grant_queries(self):
        connection = MagicMock()
        cursor = connection.cursor.return_value.__enter__.return_value
        cursor.fetchone.return_value = ("postgres", "postgres")
        cursor.fetchall.return_value = [("qlms_backup", False, False, False, False, False),
                                       ("qlms_runtime", True, False, False, False, False)]
        with self.assertRaises(ValueError):
            setup.check_database(connection)
        self.assertEqual(cursor.execute.call_count, 2)

    def test_duplicate_passwords_and_short_signing_key_are_rejected(self):
        for content in ["SECRET_KEY=short\n", "SECRET_KEY=fictional-runtime-password-only\n"]:
            with self.subTest(content=content), tempfile.TemporaryDirectory() as folder:
                directory = Path(folder)
                self.write_fixtures(directory)
                path = directory / ".env.pilot-runtime"
                path.write_text(path.read_text().replace("SECRET_KEY=fictional-signing-secret-at-least-thirty-two-bytes\n", content))
                with patch.object(setup.psycopg2, "connect") as connect, self.assertRaises(ValueError):
                    setup.run_setup(directory)
                connect.assert_not_called()
