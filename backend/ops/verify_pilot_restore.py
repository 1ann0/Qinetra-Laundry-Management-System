"""Human-only recovery proof: fresh Drive download into a disposable local database."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
import tempfile
import time
from uuid import uuid4

from dotenv import dotenv_values
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL, make_url

from ops.backup import decrypt_export, postgres_command, project_ref, restore_database
from ops.drive_authorize import PRIVATE, PROJECT, validate_destination
from ops.drive_storage import API, MAX_ENVELOPE, DriveStorage, refresh_access_token

IMAGE = "postgres:17@sha256:67f41722b7a8cbdb868a44a4995c846eddfdc2973bccb291ce937dce88ad5675"
IDENTIFIER = r'"?[a-z][a-z0-9_]*"?'
COPY = re.compile(rf"COPY qlms\.({IDENTIFIER}) \(({IDENTIFIER}(?:, {IDENTIFIER})*)\) FROM stdin;")
SEQUENCE = re.compile(r"SELECT pg_catalog\.setval\('qlms\.([a-z][a-z0-9_]*)', (-?[0-9]+), (true|false)\);")


def data_manifest(data):
    """Compare every COPY row (including duplicates) and sequence without printing data."""
    tables, sequences, current = {}, {}, None
    for line in data.decode("utf-8").split("\n"):
        if current is not None:
            if line == r"\.":
                current = None
            else:
                tables[current][line] += 1
            continue
        match = COPY.fullmatch(line)
        if match:
            current = match.groups()
            if current in tables:
                raise ValueError("Duplicate archive table")
            tables[current] = Counter()
        elif line.startswith("COPY ") or line.startswith("INSERT "):
            raise ValueError("Unexpected archive data format")
        elif line.startswith("SELECT pg_catalog.setval("):
            sequence = SEQUENCE.fullmatch(line)
            if not sequence or sequence[1] in sequences:
                raise ValueError("Unexpected archive sequence")
            sequences[sequence[1]] = (int(sequence[2]), sequence[3])
    if current is not None or not tables:
        raise ValueError("Incomplete archive data")
    return tables, sequences


def recovery_settings(settings):
    validate_destination(settings)
    parsed = make_url(settings.get("QLMS_BACKUP_DATABASE_URL") or "")
    if (parsed.get_backend_name() != "postgresql" or project_ref(parsed) != PROJECT
            or (parsed.username or "").split(".", 1)[0] != "qlms_backup"
            or parsed.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}
            or settings.get("QLMS_BACKUP_PG_CLIENT_IMAGE") != IMAGE
            or not settings.get("QLMS_BACKUP_LOCAL_FOLDER")
            or not settings.get("QLMS_BACKUP_KEY_FILE")
            or any(not settings.get(name) for name in ("QLMS_DRIVE_CLIENT_ID", "QLMS_DRIVE_CLIENT_SECRET", "QLMS_DRIVE_REFRESH_TOKEN"))):
        raise ValueError("Use the existing restricted pilot backup configuration")


def download_archive(settings, recovery_key, destination):
    marker = json.loads((Path(settings["QLMS_BACKUP_LOCAL_FOLDER"]) / "last-success.json").read_text(encoding="utf-8"))
    if (marker.get("remote_upload_verified") is not True
            or not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", marker.get("remote_file_id") or "")
            or type(marker.get("archive_bytes")) is not int
            or not 0 < marker["archive_bytes"] <= MAX_ENVELOPE):
        raise ValueError("No verified remote backup marker")
    token = refresh_access_token(settings["QLMS_DRIVE_CLIENT_ID"], settings["QLMS_DRIVE_CLIENT_SECRET"], settings["QLMS_DRIVE_REFRESH_TOKEN"])
    storage = DriveStorage(token, settings["QLMS_BACKUP_DRIVE_ACCOUNT"], settings["QLMS_BACKUP_DRIVE_FOLDER_ID"])
    storage.check_destination()
    file_id = marker["remote_file_id"]
    remote = storage.metadata(file_id)
    if (not storage.private_owner(remote, file_id) or remote.get("parents") != [storage.folder_id]
            or remote.get("size") != str(marker["archive_bytes"]) or remote.get("mimeType") != "application/octet-stream"):
        raise ValueError("Remote recovery archive is outside the verified destination")
    envelope, _ = storage.request(API + "/files/" + file_id + "?alt=media", limit=marker["archive_bytes"])
    dump, metadata = decrypt_export(envelope, recovery_key)
    if (len(envelope) != marker["archive_bytes"] or metadata.get("schema") != "qlms"
            or metadata.get("source_ref") != PROJECT or not dump.startswith(b"PGDMP")
            or hashlib.sha256(dump).hexdigest() != metadata.get("archive_sha256")):
        raise ValueError("Remote archive does not match the pilot")
    storage.check_destination()
    with Path(destination).open("xb") as output:
        output.write(envelope)
    return dump


def docker(arguments, *, environment=None):
    result = subprocess.run(["docker", "--context", "default", *arguments], env=environment,
                            capture_output=True, timeout=60)
    if result.returncode:
        raise RuntimeError("Disposable recovery database command failed")
    return result.stdout.decode().strip()


def restore_and_compare(source_url, archive, key, *, required_roles=("qlms_runtime", "qlms_backup")):
    container = "qlms-save-test-restore-" + uuid4().hex
    password = secrets.token_urlsafe(32)
    environment = os.environ.copy()
    environment.update(POSTGRES_PASSWORD=password, POSTGRES_DB="qlms_restore_check", DOCKER_CONTEXT="default")
    # A memory-backed database mount avoids persisting recovered rows in a host volume.
    engine, created = None, False
    previous_context = os.environ.get("DOCKER_CONTEXT")
    os.environ["DOCKER_CONTEXT"] = "default"
    try:
        created = True
        docker(["run", "--detach", "--pull=never", "--name", container,
                "--publish", "127.0.0.1::5432", "--memory", "768m", "--cpus", "1",
                "--tmpfs", "/var/lib/postgresql/data:rw,noexec,nosuid,size=512m",
                "--env", "POSTGRES_PASSWORD", "--env", "POSTGRES_DB", IMAGE], environment=environment)
        binding = docker(["port", container, "5432/tcp"])
        if not re.fullmatch(r"127\.0\.0\.1:[0-9]{1,5}", binding):
            raise ValueError("Restore must listen only on local loopback")
        target = URL.create("postgresql+psycopg2", username="postgres", password=password,
                            host="127.0.0.1", port=int(binding.split(":")[1]), database="qlms_restore_check",
                            query={"sslmode": "disable"})
        engine = create_engine(target, connect_args={"connect_timeout": 2})
        deadline = time.monotonic() + 45
        while True:
            try:
                with engine.connect() as connection:
                    connection.execute(text("SELECT 1"))
                break
            except Exception:
                if time.monotonic() >= deadline:
                    raise RuntimeError("Disposable recovery database did not become ready") from None
                time.sleep(1)
        with engine.begin() as connection:
            for role in required_roles:
                if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", role):
                    raise ValueError("Invalid disposable policy role")
                connection.exec_driver_sql(f'CREATE ROLE "{role}" NOLOGIN')
        dump, _ = decrypt_export(Path(archive).read_bytes(), key)
        expected = data_manifest(postgres_command("pg_restore", ["--data-only", "--no-owner", "--no-privileges", "--file=-"],
                                                  target, container=container, input_bytes=dump))
        restore_database(source_url, target, archive, key, container=container)
        restored = data_manifest(postgres_command("pg_dump", ["--data-only", "--schema=qlms", "--no-owner", "--no-privileges"],
                                                  target, container=container))
        if restored != expected:
            raise ValueError("Restored rows or sequence values differ from the archive")
        return len(expected[0])
    finally:
        if engine is not None:
            engine.dispose()
        try:
            if created:
                docker(["rm", "--force", "--volumes", container])
        finally:
            if previous_context is None:
                os.environ.pop("DOCKER_CONTEXT", None)
            else:
                os.environ["DOCKER_CONTEXT"] = previous_context


def main():
    try:
        if not sys.stdin.isatty():
            raise ValueError("Run privately in your own interactive terminal")
        settings = dotenv_values(PRIVATE / ".env.pilot-hosted-backup")
        recovery_settings(settings)
        copy = Path(input("Private recovery-key COPY path (keep it out of chat): ").strip().strip('"')).resolve()
        original = Path(settings["QLMS_BACKUP_KEY_FILE"]).resolve()
        if (copy == original or original.exists() and copy.samefile(original)
                or copy.is_relative_to(Path(settings["QLMS_BACKUP_LOCAL_FOLDER"]).resolve())):
            raise ValueError("Select a separately stored recovery-key copy")
        key = copy.read_bytes()
        if len(key) != 32:
            raise ValueError("Invalid recovery-key copy")
        started = time.monotonic()
        with tempfile.TemporaryDirectory(prefix="qlms-private-recovery-") as folder:
            archive = Path(folder) / "recovery.qlmsbackup"
            download_archive(settings, key, archive)
            tables = restore_and_compare(settings["QLMS_BACKUP_DATABASE_URL"], archive, key)
        elapsed = time.monotonic() - started
        if elapsed > 4 * 60 * 60:
            raise ValueError("Recovery exceeded the four-hour objective")
        print(f"PASS: fresh Drive download authenticated with recovery-key copy; {tables} tables and sequence values match; separate local restore and cleanup completed in {elapsed:.1f} seconds. Schedule remains off.")
        return 0
    except Exception as error:
        print(f"FAIL: private recovery proof ({type(error).__name__}); schedule remains off. No pilot database was changed.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
