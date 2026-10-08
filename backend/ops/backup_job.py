"""Unattended backups from private configuration or a protected runner environment."""
import argparse
import base64
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import sys

from dotenv import dotenv_values
from ops.backup import export_database, project_ref
from ops.drive_storage import DriveStorage, refresh_access_token
from sqlalchemy.engine import make_url


def run_job(configuration_file=None):
    settings = dotenv_values(configuration_file) if configuration_file else dict(os.environ)
    cloud = settings.get("QLMS_BACKUP_PROVIDER") == "google_drive"
    if settings.get("QLMS_BACKUP_PROVIDER") not in {None, "", "local_copy", "google_drive"}:
        raise ValueError("Unsupported backup provider")
    required = ["QLMS_BACKUP_DATABASE_URL", "QLMS_BACKUP_PROJECT_REF", "QLMS_BACKUP_LOCAL_FOLDER"]
    required += (["QLMS_BACKUP_DRIVE_ACCOUNT", "QLMS_BACKUP_DRIVE_FOLDER_ID", "QLMS_DRIVE_CLIENT_ID",
                  "QLMS_DRIVE_CLIENT_SECRET", "QLMS_DRIVE_REFRESH_TOKEN", "QLMS_BACKUP_RETENTION_DAYS",
                  "QLMS_BACKUP_PG_CLIENT_IMAGE"] if cloud else ["QLMS_BACKUP_KEY_FILE", "QLMS_BACKUP_INDEPENDENT_FOLDER"])
    if any(not settings.get(name) for name in required):
        raise ValueError("Backup configuration is incomplete")
    url = settings["QLMS_BACKUP_DATABASE_URL"]
    parsed = make_url(url)
    if project_ref(parsed) != settings["QLMS_BACKUP_PROJECT_REF"]:
        raise ValueError("Backup connection belongs to a different project")
    if parsed.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}:
        raise ValueError("Backup connection must be encrypted")
    key_file_value, key_base64 = settings.get("QLMS_BACKUP_KEY_FILE"), settings.get("QLMS_BACKUP_KEY_BASE64")
    if bool(key_file_value) == bool(key_base64):
        raise ValueError("Configure exactly one private backup key source")
    if key_file_value:
        key_file = Path(key_file_value).resolve()
        for destination in [settings["QLMS_BACKUP_LOCAL_FOLDER"], settings.get("QLMS_BACKUP_INDEPENDENT_FOLDER")]:
            if destination and key_file.is_relative_to(Path(destination).resolve()):
                raise ValueError("Keep keys outside backup destinations")
        key = key_file.read_bytes()
    else:
        key = base64.b64decode(key_base64, validate=True)
    if len(key) != 32:
        raise ValueError("Backup key must contain exactly 32 bytes")
    storage, client_image, retention = None, None, None
    schema = settings.get("QLMS_DB_SCHEMA", "qlms")
    if cloud:
        if (parsed.username or "").split(".", 1)[0] != "qlms_backup" or schema != "qlms":
            raise ValueError("Cloud export requires the restricted backup role and private schema")
        client_image = settings["QLMS_BACKUP_PG_CLIENT_IMAGE"]
        if not re.fullmatch(r"postgres:17@sha256:[a-f0-9]{64}", client_image):
            raise ValueError("Cloud export requires a pinned PostgreSQL 17 client")
        retention = int(settings["QLMS_BACKUP_RETENTION_DAYS"])
        if not 1 <= retention <= 3650:
            raise ValueError("Invalid agreed retention period")
        token = refresh_access_token(settings["QLMS_DRIVE_CLIENT_ID"], settings["QLMS_DRIVE_CLIENT_SECRET"], settings["QLMS_DRIVE_REFRESH_TOKEN"])
        storage = DriveStorage(token, settings["QLMS_BACKUP_DRIVE_ACCOUNT"], settings["QLMS_BACKUP_DRIVE_FOLDER_ID"])
        storage.check_destination()
    # Do not load DATABASE_URL/SECRET_KEY from the application or enable automatic deletion.
    encrypted, copied = export_database(url, schema, key, settings["QLMS_BACKUP_LOCAL_FOLDER"],
                                       None if cloud else settings["QLMS_BACKUP_INDEPENDENT_FOLDER"], client_image=client_image)
    remote_id = storage.upload_verified(encrypted, key) if storage else None
    if cloud and (not isinstance(remote_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", remote_id)):
        raise ValueError("Cloud backup has no verified remote reference")
    marker = Path(settings["QLMS_BACKUP_LOCAL_FOLDER"]) / "last-success.json"
    marker.write_text(json.dumps({"completed_at": datetime.now(timezone.utc).isoformat(),
                                 "archive": encrypted.name, "second_copy_verified": copied is not None,
                                 "remote_upload_verified": remote_id is not None,
                                 "remote_file_id": remote_id, "archive_bytes": encrypted.stat().st_size,
                                 "retention_days": retention, "automatic_deletion": False}) + "\n", encoding="utf-8")
    return remote_id is not None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--config")
    source.add_argument("--environment", action="store_true")
    arguments = parser.parse_args()
    try:
        remote_verified = run_job(arguments.config)
    except Exception as error:
        # Never print credentials, SQL or the private configuration on a scheduler failure.
        print(f"QLMS backup failed ({type(error).__name__}). Inspect configuration privately; stop trial entry until recovery is verified.", file=sys.stderr)
        return 1
    print("Encrypted Drive archive downloaded and authenticated." if remote_verified else
          "Encrypted archive and second copy verified. Check cloud synchronization independently.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
