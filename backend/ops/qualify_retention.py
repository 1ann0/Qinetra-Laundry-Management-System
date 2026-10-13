"""Human-only Drive retention rehearsal in a newly created temporary child folder."""
from datetime import datetime, timedelta, timezone
from dotenv import dotenv_values
import hashlib
import json
import os
from pathlib import Path
import re
import sys
import tempfile
from uuid import uuid4
from urllib.parse import urlencode

from ops.backup import encrypt_export
from ops.drive_authorize import PRIVATE, PROJECT, validate_destination
from ops.drive_storage import API, DriveStorage, refresh_access_token


def rehearsal(settings):
    validate_destination(settings)
    token = refresh_access_token(settings["QLMS_DRIVE_CLIENT_ID"], settings["QLMS_DRIVE_CLIENT_SECRET"], settings["QLMS_DRIVE_REFRESH_TOKEN"])
    parent = DriveStorage(token, settings["QLMS_BACKUP_DRIVE_ACCOUNT"], settings["QLMS_BACKUP_DRIVE_FOLDER_ID"])
    parent.check_destination()
    name = "QLMS temporary retention rehearsal " + uuid4().hex
    data, _ = parent.request(API + "/files?fields=id", method="POST", data=json.dumps({"name": name,
        "mimeType": "application/vnd.google-apps.folder", "parents": [parent.folder_id]}).encode(),
        headers={"Content-Type": "application/json"})
    folder_id = json.loads(data).get("id")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", folder_id or "") or folder_id == parent.folder_id:
        raise ValueError("Uncertain temporary folder creation; inspect privately before retrying")
    folder = parent.metadata(folder_id)
    if (not parent.private_owner(folder, folder_id) or folder.get("parents") != [parent.folder_id]
            or folder.get("name") != name or folder.get("mimeType") != "application/vnd.google-apps.folder"):
        raise ValueError("Temporary folder destination is unverified")
    child = DriveStorage(token, parent.account, folder_id)
    references = {}
    try:
        child.check_destination()
        key, now = os.urandom(32), datetime.now(timezone.utc)
        dump = b"PGDMP encrypted fictional retention fixture; no customer data"
        metadata = {"schema": "qlms", "source_ref": PROJECT, "archive_sha256": hashlib.sha256(dump).hexdigest()}
        with tempfile.TemporaryDirectory(prefix="qlms-retention-fixture-") as directory:
            for kind, created in [("expired", now - timedelta(days=91)), ("fresh", now)]:
                path = Path(directory) / created.strftime("qlms-%Y%m%dT%H%M%S%fZ.qlmsbackup")
                path.write_bytes(encrypt_export(dump, key, {**metadata, "created_at": created.isoformat()}))
                references[kind] = child.upload_verified(path, key)
            note = Path(directory) / "unrelated-fixture.qlmsbackup"
            note.write_bytes(encrypt_export(dump, key, {**metadata, "created_at": now.isoformat()}))
            references["unrelated"] = child.upload_verified(note, key)
            plan = child.expired_archives(key, PROJECT, references["fresh"], 90)
            if [item[0] for item in plan] != [references["expired"]]:
                raise ValueError("Retention selected an unexpected fixture")
            if child.prune_expired(key, PROJECT, references["fresh"], 90) != 1:
                raise ValueError("Expired fixture was not removed")
            for kind in ("fresh", "unrelated"):
                remaining = child.metadata(references[kind])
                if not child.private_owner(remaining, references[kind]) or remaining.get("parents") != [folder_id]:
                    raise ValueError("Retention failed to preserve a fixture")
            if child.expired_archives(key, PROJECT, references["fresh"], 90):
                raise ValueError("Expired fixture still appears after deletion")
    finally:
        # Remove only this uniquely named, verified child; never the real backup destination.
        parent.check_destination()
        current = parent.metadata(folder_id)
        if (not parent.private_owner(current, folder_id) or current.get("parents") != [parent.folder_id]
                or current.get("name") != name or current.get("capabilities", {}).get("canDelete") is not True):
            raise ValueError("Temporary retention folder cleanup requires private review")
        data, _ = parent.request(API + "/files?" + urlencode({
            "q": "'" + folder_id + "' in parents and trashed=false", "fields": "files(id),nextPageToken,incompleteSearch", "pageSize": 1000}))
        contents = json.loads(data)
        if (contents.get("nextPageToken") or contents.get("incompleteSearch", False) is not False
                or not isinstance(contents.get("files"), list)
                or any(item.get("id") not in references.values() for item in contents["files"])):
            raise ValueError("Unrecognized temporary contents require private review")
        parent.request(API + "/files/" + folder_id, method="DELETE")


def main():
    try:
        if not sys.stdin.isatty():
            raise ValueError("Use your own private terminal")
        if input("Type TEST RETENTION to rehearse only disposable encrypted fixtures: ").strip() != "TEST RETENTION":
            raise ValueError("Private rehearsal not confirmed")
        rehearsal(dotenv_values(PRIVATE / ".env.pilot-hosted-backup"))
        print("PASS: expired encrypted fixture removed; fresh and unrelated fixtures preserved; temporary child folder cleaned up. Real backups unchanged; daily cleanup remains off.")
        return 0
    except Exception as error:
        print(f"FAIL: private retention rehearsal ({type(error).__name__}); inspect before retrying; daily cleanup remains off.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
