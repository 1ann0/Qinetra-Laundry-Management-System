"""Only fictional key bytes are created; real recovery keys belong to humans."""
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

from ops.init_backup_key import create_key


class PrivateKeyTests(unittest.TestCase):
    def test_private_permissions_are_set_before_key_bytes_are_written(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fictional.key"
            def restrict(*args, **kwargs):
                self.assertEqual(path.read_bytes(), b"")
            windows = SimpleNamespace(name="nt", environ={}, urandom=Mock(return_value=b"k" * 32))
            with patch("ops.init_backup_key.os", windows), \
                    patch("ops.init_backup_key.subprocess.run", side_effect=restrict) as acl, \
                    patch("ops.init_backup_key.getpass.getuser", return_value="fictional-user"):
                create_key(path)
            self.assertEqual(path.read_bytes(), b"k" * 32)
            self.assertIn("/inheritance:r", acl.call_args.args[0])

    def test_existing_key_is_never_overwritten_and_permission_failure_leaves_no_key(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "fictional.key"
            path.write_bytes(b"existing-fictional-key")
            with self.assertRaises(FileExistsError):
                create_key(path)
            self.assertEqual(path.read_bytes(), b"existing-fictional-key")
            fresh = Path(folder) / "new-fictional.key"
            windows = SimpleNamespace(name="nt", environ={}, urandom=Mock(return_value=b"k" * 32))
            with patch("ops.init_backup_key.os", windows), \
                    patch("ops.init_backup_key.subprocess.run", side_effect=OSError("fictional failure")), \
                    patch("ops.init_backup_key.getpass.getuser", return_value="fictional-user"):
                with self.assertRaises(RuntimeError):
                    create_key(fresh)
            windows.urandom.assert_not_called()
            self.assertFalse(fresh.exists())


if __name__ == "__main__":
    unittest.main()
