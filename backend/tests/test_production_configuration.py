"""Production must not silently use a local DB, public schema or migration login."""
import os
import subprocess
import sys
import unittest
from pathlib import Path


class ProductionConfigurationTests(unittest.TestCase):
    def load_configuration(self, **overrides):
        environment = os.environ.copy()
        environment.update(QLMS_ENV="production", QLMS_DB_SCHEMA="qlms", QLMS_DB_USER="qlms_runtime",
                           DATABASE_URL="postgresql://qlms_runtime:fictional@127.0.0.1:5432/unused?sslmode=require")
        environment.update(overrides)
        # Import creates an engine but never opens a network connection.
        return subprocess.run([sys.executable, "-c", "import database"], env=environment,
                              cwd=Path(__file__).resolve().parents[1], capture_output=True).returncode

    def test_explicit_private_encrypted_runtime_configuration_loads(self):
        self.assertEqual(self.load_configuration(), 0)
        self.assertEqual(self.load_configuration(DATABASE_URL="postgresql://qlms_runtime.abcdefghijklmnopqrst:fictional@pool.example.com/postgres?sslmode=require"), 0)

    def test_unsafe_production_configuration_fails_before_connecting(self):
        for changes in [dict(DATABASE_URL="sqlite://"), dict(QLMS_DB_SCHEMA="public"), dict(QLMS_DB_USER=""),
                        dict(DATABASE_URL="postgresql://qlms_runtime:fictional@127.0.0.1/unused"),
                        dict(DATABASE_URL="postgresql://postgres:fictional@127.0.0.1/unused?sslmode=require")]:
            with self.subTest(changes=changes):
                self.assertNotEqual(self.load_configuration(**changes), 0)
