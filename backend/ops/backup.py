"""Encrypted PostgreSQL exports; restoration is restricted to a separate database."""
import argparse
import hashlib
import json
import os
import re
import shutil
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

MAGIC = b"QLMSBK1\0"
MAX_HEADER = 4096
MAX_EXPORT = 256 * 1024 * 1024


def encrypt_export(plaintext, key, metadata):
    if len(key) != 32 or len(plaintext) > MAX_EXPORT:
        raise ValueError("Use a 32-byte key and a bounded export")
    header = json.dumps(metadata, sort_keys=True, separators=(",", ":")).encode()
    if len(header) > MAX_HEADER:
        raise ValueError("Backup metadata is too large")
    prefix = MAGIC + len(header).to_bytes(4, "big") + header
    nonce = os.urandom(12)
    return prefix + nonce + AESGCM(key).encrypt(nonce, plaintext, prefix)


def decrypt_export(envelope, key):
    try:
        if len(key) != 32 or not envelope.startswith(MAGIC):
            raise ValueError()
        header_length = int.from_bytes(envelope[len(MAGIC):len(MAGIC) + 4], "big")
        offset = len(MAGIC) + 4 + header_length
        if header_length > MAX_HEADER or len(envelope) < offset + 28 or len(envelope) > MAX_EXPORT + MAX_HEADER + 40:
            raise ValueError()
        prefix = envelope[:offset]
        metadata = json.loads(envelope[len(MAGIC) + 4:offset])
        if not isinstance(metadata, dict):
            raise ValueError()
        plaintext = AESGCM(key).decrypt(envelope[offset:offset + 12], envelope[offset + 12:], prefix)
        return plaintext, metadata
    except Exception as error:
        raise ValueError("Backup could not be authenticated") from error


def copy_encrypted_backup(source, destination_folder):
    source, folder = Path(source).resolve(), Path(destination_folder).resolve()
    if folder == source.parent:
        raise ValueError("Choose a separate backup destination")
    folder.mkdir(parents=True, exist_ok=True)
    destination = folder / source.name
    # Exclusive creation preserves earlier copies, including after a failed run.
    with source.open("rb") as incoming, destination.open("xb") as outgoing:
        shutil.copyfileobj(incoming, outgoing)
        outgoing.flush()
        os.fsync(outgoing.fileno())
    if hashlib.sha256(source.read_bytes()).digest() != hashlib.sha256(destination.read_bytes()).digest():
        raise ValueError("Independent backup copy failed verification")
    return destination


def project_ref(url):
    if url.host and re.fullmatch(r"db\.[a-z]{20}\.supabase\.co", url.host):
        return url.host.split(".")[1]
    if url.host and url.host.endswith(".pooler.supabase.com"):
        match = re.search(r"\.([a-z]{20})$", url.username or "")
        return match.group(1) if match else None
    return None


def validate_restore_target(source, target, approved_project=None):
    source, target = make_url(source), make_url(target)
    local_hosts = {"127.0.0.1", "localhost", "::1"}
    if source.get_backend_name() != "postgresql" or target.get_backend_name() != "postgresql":
        raise ValueError("PostgreSQL is required")
    source_ref, target_ref = project_ref(source), project_ref(target)
    same_host = source.host == target.host or source.host in local_hosts and target.host in local_hosts
    if source_ref and source_ref == target_ref:
        raise ValueError("Never restore into the source project")
    if same_host and source.port == target.port and source.database == target.database and not (source_ref and target_ref and source_ref != target_ref):
        raise ValueError("Never restore into the source database")
    if target.host in local_hosts and (target.database or "").startswith("qlms_restore_"):
        return
    if target_ref and source_ref and target_ref != source_ref and target_ref == approved_project:
        return
    raise ValueError("Restore requires a disposable local database or an approved separate Supabase project")


def postgres_environment(url):
    parsed = make_url(url)
    if parsed.get_backend_name() != "postgresql":
        raise ValueError("PostgreSQL is required")
    environment = os.environ.copy()
    environment.update(PGHOST=parsed.host or "", PGPORT=str(parsed.port or 5432),
                       PGDATABASE=parsed.database or "", PGUSER=parsed.username or "", PGPASSWORD=parsed.password or "")
    environment["PGSSLMODE"] = str(parsed.query.get("sslmode", "require" if parsed.host not in {"localhost", "127.0.0.1", "::1"} else "disable"))
    environment["PGCONNECT_TIMEOUT"] = "10"
    return environment


def postgres_command(tool, arguments, url, *, container=None, input_bytes=None, client_image=None):
    environment = postgres_environment(url)
    if container and client_image:
        raise ValueError("Choose one PostgreSQL client")
    if client_image:
        if tool != "pg_dump" or not re.fullmatch(r"postgres:17@sha256:[a-f0-9]{64}", client_image):
            raise ValueError("Cloud export requires a pinned PostgreSQL 17 client")
        command = ["docker", "run", "--rm", "--interactive"]
        for name in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGSSLMODE", "PGCONNECT_TIMEOUT"):
            command.extend(["--env", name])
        command.extend([client_image, tool])
    elif container:
        if not container.startswith("qlms-save-test-"):
            raise ValueError("Only the disposable test container is supported")
        # docker exec receives credentials through its environment, never command arguments.
        environment["PGHOST"], environment["PGPORT"] = "127.0.0.1", "5432"
        command = ["docker", "exec", "-i"]
        for name in ("PGHOST", "PGPORT", "PGDATABASE", "PGUSER", "PGPASSWORD", "PGSSLMODE", "PGCONNECT_TIMEOUT"):
            command.extend(["--env", name])
        command.extend([container, tool])
    else:
        command = [tool]
    result = subprocess.run(command + arguments, input=input_bytes, capture_output=True, env=environment, timeout=900)
    if result.returncode:
        # PostgreSQL errors can include customer rows or connection details.
        raise RuntimeError(f"{tool} failed; inspect privately before retrying")
    return result.stdout


def export_database(url, schema, key, output_folder, independent_folder=None, container=None, *, client_image=None):
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise ValueError("Use a simple schema name")
    dump = postgres_command("pg_dump", ["--format=custom", f"--schema={schema}", "--no-owner", "--no-privileges", "--enable-row-security"], url, container=container, client_image=client_image)
    if not dump.startswith(b"PGDMP"):
        raise ValueError("PostgreSQL did not produce a valid archive")
    created = datetime.now(timezone.utc)
    metadata = {"schema": schema, "source_ref": project_ref(make_url(url)) or "local",
                "created_at": created.isoformat(), "archive_sha256": hashlib.sha256(dump).hexdigest()}
    output_folder = Path(output_folder).resolve()
    output_folder.mkdir(parents=True, exist_ok=True)
    destination = output_folder / (created.strftime("qlms-%Y%m%dT%H%M%S%fZ") + ".qlmsbackup")
    with destination.open("xb") as output:
        output.write(encrypt_export(dump, key, metadata))
        output.flush()
        os.fsync(output.fileno())
    copied = copy_encrypted_backup(destination, independent_folder) if independent_folder else None
    return destination, copied


def restore_database(source_url, target_url, encrypted_file, key, *, approved_project=None, container=None):
    validate_restore_target(source_url, target_url, approved_project)
    archive, metadata = decrypt_export(Path(encrypted_file).read_bytes(), key)
    source_ref = project_ref(make_url(source_url)) or "local"
    if metadata.get("source_ref") != source_ref or not archive.startswith(b"PGDMP") or hashlib.sha256(archive).hexdigest() != metadata.get("archive_sha256"):
        raise ValueError("Backup does not match the selected source")
    schema = metadata.get("schema", "")
    if not re.fullmatch(r"[a-z][a-z0-9_]{0,62}", schema):
        raise ValueError("Invalid backup schema")
    engine = create_engine(target_url, connect_args={"connect_timeout": 10})
    try:
        with engine.connect() as connection:
            exists = connection.execute(text("SELECT EXISTS(SELECT 1 FROM information_schema.schemata WHERE schema_name=:schema)"), {"schema": schema}).scalar()
            if exists:
                raise ValueError("Restore requires a target without the application schema")
        postgres_command("pg_restore", ["--exit-on-error", "--single-transaction", "--no-owner", "--no-privileges", "--dbname=" + make_url(target_url).database],
                         target_url, container=container, input_bytes=archive)
    finally:
        engine.dispose()
    return metadata


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["export", "restore"])
    parser.add_argument("--key-file", required=True)
    parser.add_argument("--output-folder")
    parser.add_argument("--independent-folder")
    parser.add_argument("--encrypted-file")
    parser.add_argument("--approved-project")
    arguments = parser.parse_args()
    key_path = Path(arguments.key_file).resolve()
    key = key_path.read_bytes()
    source = os.environ["QLMS_BACKUP_DATABASE_URL"]
    if arguments.action == "export":
        if not arguments.output_folder or not arguments.independent_folder:
            parser.error("Export requires local and independent destinations")
        for folder in (arguments.output_folder, arguments.independent_folder):
            if key_path.is_relative_to(Path(folder).resolve()):
                parser.error("Keep the encryption key outside both backup destinations")
        export_database(source, os.environ.get("QLMS_DB_SCHEMA", "qlms"), key, arguments.output_folder, arguments.independent_folder)
        print("Encrypted export and second local copy verified. Remote cloud upload still requires verification.")
    else:
        if not arguments.encrypted_file:
            parser.error("Restore requires an encrypted archive")
        restore_database(source, os.environ["QLMS_RESTORE_DATABASE_URL"], arguments.encrypted_file, key, approved_project=arguments.approved_project)
        print("Separate database restoration completed; verify record and money histories before acceptance.")


if __name__ == "__main__":
    main()
