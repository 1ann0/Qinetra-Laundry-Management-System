"""Authenticated backup envelope, safe copies and separate restore targets."""
import os
import tempfile
import unittest
from pathlib import Path

from ops.backup import encrypt_export, decrypt_export, copy_encrypted_backup, validate_restore_target


class BackupContractTests(unittest.TestCase):
    def setUp(self):
        self.key = os.urandom(32)
        self.metadata = {"schema": "qlms", "source_ref": "fictional", "created_at": "2026-10-05T10:00:00Z"}

    def test_encrypted_dump_roundtrips_without_exposing_customer_content(self):
        original = b"PGDMP fictional customer 0700000000 and payment history"
        encrypted = encrypt_export(original, self.key, self.metadata)
        self.assertNotIn(b"0700000000", encrypted)
        self.assertEqual(decrypt_export(encrypted, self.key), (original, self.metadata))
        self.assertNotEqual(encrypted, encrypt_export(original, self.key, self.metadata))

    def test_wrong_key_tampering_truncation_and_metadata_changes_fail(self):
        encrypted = encrypt_export(b"PGDMP fixture", self.key, self.metadata)
        for value, key in [(encrypted, os.urandom(32)), (encrypted[:-1], self.key),
                           (encrypted[:-1] + bytes([encrypted[-1] ^ 1]), self.key),
                           (encrypted.replace(b"fictional", b"changedxx"), self.key), (b"bad", self.key)]:
            with self.assertRaises(ValueError):
                decrypt_export(value, key)

    def test_backup_copy_preserves_ciphertext_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            original = root / "local" / "fixture.qlmsbackup"
            original.parent.mkdir()
            original.write_bytes(encrypt_export(b"PGDMP fixture", self.key, self.metadata))
            copied = copy_encrypted_backup(original, root / "independent")
            self.assertEqual(copied.read_bytes(), original.read_bytes())
            with self.assertRaises(FileExistsError):
                copy_encrypted_backup(original, root / "independent")
            with self.assertRaises(ValueError):
                copy_encrypted_backup(original, original.parent)

    def test_live_or_ambiguous_restore_targets_are_rejected(self):
        source = "postgresql://backup:private@127.0.0.1:55432/qlms_test"
        for target in [source, "postgresql://restore:private@localhost:55432/qlms_test",
                       "postgresql://restore:private@db.example.com/postgres"]:
            with self.assertRaises(ValueError):
                validate_restore_target(source, target)
        validate_restore_target(source, "postgresql://restore:private@127.0.0.1:55432/qlms_restore_fixture")

    def test_remote_restore_needs_a_different_explicitly_approved_project(self):
        source_ref, target_ref = "a" * 20, "b" * 20
        source = f"postgresql://backup.{source_ref}:private@aws-1-eu-central-1.pooler.supabase.com/postgres"
        target = f"postgresql://restore.{target_ref}:private@aws-1-eu-central-1.pooler.supabase.com/postgres"
        with self.assertRaises(ValueError):
            validate_restore_target(source, target)
        validate_restore_target(source, target, approved_project=target_ref)
        with self.assertRaises(ValueError):
            validate_restore_target(source, source, approved_project=source_ref)
