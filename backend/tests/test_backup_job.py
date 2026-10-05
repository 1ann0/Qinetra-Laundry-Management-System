"""A scheduled job must fail safely before exporting from an unintended project."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from ops.backup_job import run_job


class BackupJobTests(unittest.TestCase):
    def test_wrong_project_and_plaintext_connection_never_start_export(self):
        with tempfile.TemporaryDirectory() as folder:
            settings = Path(folder) / ".env"
            for connection in ["postgresql://qlms_backup.abcdefghijklmnopqrst:fictional@aws-1-eu-central-1.pooler.supabase.com/postgres?sslmode=require",
                               "postgresql://qlms_backup.bbbbbbbbbbbbbbbbbbbb:fictional@aws-1-eu-central-1.pooler.supabase.com/postgres"]:
                settings.write_text(f"QLMS_BACKUP_DATABASE_URL={connection}\nQLMS_BACKUP_PROJECT_REF=bbbbbbbbbbbbbbbbbbbb\nQLMS_BACKUP_KEY_FILE=unused\nQLMS_BACKUP_LOCAL_FOLDER=unused\nQLMS_BACKUP_INDEPENDENT_FOLDER=unused\n")
                with patch("ops.backup_job.export_database") as export, self.assertRaises(ValueError):
                    run_job(settings)
                export.assert_not_called()

    def test_backup_destinations_cannot_contain_the_key(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            settings = root / ".env"
            settings.write_text("QLMS_BACKUP_DATABASE_URL=postgresql://qlms_backup.bbbbbbbbbbbbbbbbbbbb:fictional@aws-1-eu-central-1.pooler.supabase.com/postgres?sslmode=require\n"
                               f"QLMS_BACKUP_PROJECT_REF=bbbbbbbbbbbbbbbbbbbb\nQLMS_BACKUP_KEY_FILE={root / 'key'}\nQLMS_BACKUP_LOCAL_FOLDER={root}\nQLMS_BACKUP_INDEPENDENT_FOLDER=unused\n")
            with patch("ops.backup_job.export_database") as export, self.assertRaises(ValueError):
                run_job(settings)
            export.assert_not_called()
