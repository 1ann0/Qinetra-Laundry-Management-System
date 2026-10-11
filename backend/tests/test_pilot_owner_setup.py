"""Owner bootstrap guards use fictional settings and never load private files."""
from contextlib import redirect_stdout
from io import StringIO
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from ops import pilot_owner_setup as setup


def fictional_runtime():
    return {
        "QLMS_ENV": "production", "QLMS_DB_SCHEMA": "qlms", "QLMS_DB_USER": "qlms_runtime",
        "DATABASE_URL": "postgresql://qlms_runtime." + setup.PROJECT
            + ":fictional-password-only@" + setup.HOST + ":5432/postgres?sslmode=require",
        "SECRET_KEY": "fictional-signing-secret-at-least-thirty-two-bytes",
    }


class PilotOwnerSetupTests(unittest.TestCase):
    def test_import_and_noninteractive_run_never_load_credentials(self):
        with patch.object(setup.sys.stdin, "isatty", return_value=False), \
                patch.object(setup, "load_settings") as load, redirect_stdout(StringIO()):
            self.assertEqual(setup.main(), 1)
        load.assert_not_called()

    def test_rejects_practice_admin_weak_secret_and_unencrypted_destinations(self):
        changes = [
            {"QLMS_ENV": "development"}, {"QLMS_DB_SCHEMA": "public"},
            {"QLMS_DB_USER": "postgres"}, {"SECRET_KEY": "short"},
            {"DATABASE_URL": "sqlite:///fictional.sqlite"},
            {"DATABASE_URL": fictional_runtime()["DATABASE_URL"].replace(setup.PROJECT, "practice-project")},
            {"DATABASE_URL": fictional_runtime()["DATABASE_URL"].replace("qlms_runtime.", "postgres.")},
            {"DATABASE_URL": fictional_runtime()["DATABASE_URL"].replace(setup.HOST, "untrusted.invalid")},
            {"DATABASE_URL": fictional_runtime()["DATABASE_URL"].replace("sslmode=require", "sslmode=disable")},
            {"DATABASE_URL": fictional_runtime()["DATABASE_URL"] + "&options=untrusted"},
        ]
        for change in changes:
            with self.subTest(change=list(change)), self.assertRaises(ValueError):
                setup.validate_runtime(fictional_runtime() | change)

    def test_load_uses_only_explicit_file_and_does_not_interpolate(self):
        with tempfile.TemporaryDirectory() as folder:
            directory = Path(folder)
            values = fictional_runtime() | {"UNRELATED_VALUE": "ignore", "SECRET_KEY": "fictional-${DO_NOT_READ_ENV}-secret-long-enough"}
            (directory / ".env.pilot-runtime").write_text(
                "\n".join(key + "=" + value for key, value in values.items()), encoding="utf-8")
            settings = setup.load_settings(directory)
        self.assertNotIn("UNRELATED_VALUE", settings)
        self.assertEqual(settings["SECRET_KEY"], values["SECRET_KEY"])

    def test_role_schema_privileges_and_catalogue_only_counts_are_checked(self):
        connection = MagicMock()
        connection.exec_driver_sql.return_value.fetchone.side_effect = [
            ("qlms_runtime", "qlms"), (False, False, False, False, False), (22, 30, 0, 0, 0, 0)]
        engine = MagicMock()
        engine.connect.return_value.__enter__.return_value = connection
        setup.check_database(engine)
        self.assertEqual(connection.exec_driver_sql.call_args_list[0].args, ("SET TRANSACTION READ ONLY",))

    def test_existing_accounts_records_or_privileged_role_block_bootstrap(self):
        rows = [
            [("postgres", "qlms"), (False,) * 5, (22, 30, 0, 0, 0, 0)],
            [("qlms_runtime", "public"), (False,) * 5, (22, 30, 0, 0, 0, 0)],
            [("qlms_runtime", "qlms"), (True, False, False, False, False), (22, 30, 0, 0, 0, 0)],
            [("qlms_runtime", "qlms"), (False,) * 5, (22, 30, 1, 0, 0, 0)],
            [("qlms_runtime", "qlms"), (False,) * 5, (22, 30, 0, 1, 0, 0)],
        ]
        for result in rows:
            with self.subTest(result=result), self.assertRaises(ValueError):
                connection = MagicMock()
                connection.exec_driver_sql.return_value.fetchone.side_effect = result
                engine = MagicMock()
                engine.connect.return_value.__enter__.return_value = connection
                setup.check_database(engine)

    def test_only_validated_environment_reaches_private_bootstrap(self):
        settings = fictional_runtime()
        def bootstrap():
            self.assertEqual(os.environ["DATABASE_URL"], settings["DATABASE_URL"])
            self.assertEqual(os.environ["PYTHON_DOTENV_DISABLED"], "1")
            return 0
        with patch.dict(os.environ, {}, clear=True), patch.object(setup.sys.stdin, "isatty", return_value=True), \
                patch.object(setup, "load_settings", return_value=settings), \
                patch.object(setup, "prepare_database") as prepare, \
                patch.object(setup, "run_bootstrap", side_effect=bootstrap), redirect_stdout(StringIO()):
            self.assertEqual(setup.main(), 0)
        prepare.assert_called_once_with()

    def test_failure_never_prints_a_driver_exception_or_prompts_for_a_password(self):
        hidden = "fictional-password-that-must-not-be-printed"
        output = StringIO()
        with patch.object(setup.sys.stdin, "isatty", return_value=True), \
                patch.object(setup, "load_settings", side_effect=RuntimeError(hidden)), \
                patch.object(setup, "run_bootstrap") as bootstrap, redirect_stdout(output):
            self.assertEqual(setup.main(), 1)
        bootstrap.assert_not_called()
        self.assertIn("FAIL", output.getvalue())
        self.assertNotIn(hidden, output.getvalue())


if __name__ == "__main__":
    unittest.main()
