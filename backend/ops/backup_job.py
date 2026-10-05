"""Unattended backup runner; configuration stays in a private local file."""
import argparse
from pathlib import Path
import sys

from dotenv import dotenv_values
from ops.backup import export_database, project_ref
from sqlalchemy.engine import make_url


def run_job(configuration_file):
    settings = dotenv_values(configuration_file)
    required = ["QLMS_BACKUP_DATABASE_URL", "QLMS_BACKUP_PROJECT_REF", "QLMS_BACKUP_KEY_FILE", "QLMS_BACKUP_LOCAL_FOLDER", "QLMS_BACKUP_INDEPENDENT_FOLDER"]
    if any(not settings.get(name) for name in required):
        raise ValueError("Backup configuration is incomplete")
    url = settings["QLMS_BACKUP_DATABASE_URL"]
    if project_ref(make_url(url)) != settings["QLMS_BACKUP_PROJECT_REF"]:
        raise ValueError("Backup connection belongs to a different project")
    if make_url(url).query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("Backup connection must be encrypted")
    key_file = Path(settings["QLMS_BACKUP_KEY_FILE"]).resolve()
    for destination in [settings["QLMS_BACKUP_LOCAL_FOLDER"], settings["QLMS_BACKUP_INDEPENDENT_FOLDER"]]:
        if key_file.is_relative_to(Path(destination).resolve()):
            raise ValueError("Keep keys outside backup destinations")
    # Do not load DATABASE_URL/SECRET_KEY from the application or enable automatic deletion.
    encrypted, copied = export_database(url, settings.get("QLMS_DB_SCHEMA", "qlms"), key_file.read_bytes(),
                      settings["QLMS_BACKUP_LOCAL_FOLDER"], settings["QLMS_BACKUP_INDEPENDENT_FOLDER"])
    marker = Path(settings["QLMS_BACKUP_LOCAL_FOLDER"]) / "last-success.json"
    import json
    from datetime import datetime, timezone
    marker.write_text(json.dumps({"completed_at": datetime.now(timezone.utc).isoformat(),
                                 "archive": encrypted.name, "second_copy_verified": copied is not None,
                                 "remote_upload_verified": False}) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    arguments = parser.parse_args()
    try:
        run_job(arguments.config)
    except Exception as error:
        # Never print credentials, SQL or the private configuration on a scheduler failure.
        print(f"QLMS backup failed ({type(error).__name__}). Inspect configuration privately; stop trial entry until recovery is verified.", file=sys.stderr)
        return 1
    print("Encrypted archive and second copy verified. Check cloud synchronization independently.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
