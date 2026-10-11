"""Create an owner-readable backup key without printing it or overwriting one."""
import argparse
import getpass
import os
from pathlib import Path
import subprocess
import sys


def create_key(path):
    path = Path(path).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)
    output = path.open("xb")
    try:
        with output:
            # Secure the empty file before writing any key bytes.
            if os.name == "nt":
                identity = os.environ.get("USERDOMAIN", "") + "\\" + getpass.getuser()
                subprocess.run(["icacls", str(path), "/inheritance:r", "/grant:r", identity + ":(F)"], check=True, capture_output=True)
            else:
                path.chmod(0o600)
            output.write(os.urandom(32))
    except Exception:
        path.unlink()  # Only the new key created by this invocation.
        raise RuntimeError("Key permissions could not be restricted") from None


def main():
    if not sys.stdin.isatty():
        print("FAIL: create the recovery key in your own interactive terminal outside Codex.")
        return 1
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--key-file", required=True)
    arguments = parser.parse_args()
    try:
        create_key(arguments.key_file)
    except Exception as error:
        print(f"FAIL: private recovery key creation ({type(error).__name__}); existing keys are never overwritten.")
        return 1
    print("PASS: recovery key created privately. Store separate Owner and human-maintainer copies outside Drive before live entry.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
