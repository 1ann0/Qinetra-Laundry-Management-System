"""Create an owner-readable backup key without printing it or overwriting one."""
import argparse
import getpass
import os
from pathlib import Path
import subprocess


def create_key(path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as output:
        output.write(os.urandom(32))
    try:
        if os.name == "nt":
            identity = os.environ.get("USERDOMAIN", "") + "\\" + getpass.getuser()
            subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", identity + ":(F)"], check=True, capture_output=True)
        else:
            path.chmod(0o600)
    except Exception:
        path.unlink()  # Only the new key created by this invocation.
        raise RuntimeError("Key permissions could not be restricted") from None


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", required=True)
    create_key(parser.parse_args().key_file)
    print("Key created privately. Keep a recoverable owner-controlled copy separate from the backups before live entry.")
