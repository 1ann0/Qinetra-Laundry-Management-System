"""Human-only transfer of existing backup settings into Qinetra's main-only GitHub environment."""
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

from dotenv import dotenv_values
from sqlalchemy.engine import make_url
from ops.backup import project_ref
from ops.backup_budget import APPROVED_BUDGET_BYTES

REPOSITORY = "1ann0/Qinetra-Laundry-Management-System"
ENVIRONMENT = "qinetra-pilot-backup"
PROJECT = "istweeaqtykwfuhntgik"
WORKFLOW_SHA256 = "a3c4f530c8f5fb0f4c71c99e68cf5e064a6876a1a60354e6ec8f37ce733a81e0"
SECRET_NAMES = ("QLMS_BACKUP_DATABASE_URL", "QLMS_BACKUP_KEY_BASE64", "QLMS_BACKUP_DRIVE_ACCOUNT",
                "QLMS_BACKUP_DRIVE_FOLDER_ID", "QLMS_DRIVE_CLIENT_ID", "QLMS_DRIVE_CLIENT_SECRET",
                "QLMS_DRIVE_REFRESH_TOKEN", "QLMS_BACKUP_MONITOR_URL")
SAFE_FAILURES = frozenset({
    "Use the qualified Qinetra pilot settings", "Use the approved backup account", "Retention must be 90 days",
    "Storage budget must be 5 GB", "Use the restricted encrypted pilot backup connection",
    "Use exactly one existing key source", "Existing key must contain exactly 32 bytes",
    "Private configuration is incomplete or malformed", "Use the existing private monitor URL",
    "Reviewed workflow has not been installed on main", "Sign in to the existing repository owner's GitHub account",
    "Unexpected repository or hosting budget", "Daily backup is already enabled; do not reinstall live credentials",
    "Existing environment must allow only main; its protections were preserved",
    "Environment permits an unexpected branch or tag", "Secret-name readback is incomplete",
})


def prepare_secrets(settings):
    if (settings.get("QLMS_BACKUP_PROVIDER") != "google_drive"
            or settings.get("QLMS_DB_SCHEMA") != "qlms"
            or settings.get("QLMS_BACKUP_PROJECT_REF") != PROJECT):
        raise ValueError("Use the qualified Qinetra pilot settings")
    if settings.get("QLMS_BACKUP_DRIVE_ACCOUNT") != "qinetraian@gmail.com":
        raise ValueError("Use the approved backup account")
    if settings.get("QLMS_BACKUP_RETENTION_DAYS") != "90":
        raise ValueError("Retention must be 90 days")
    # The qualified backup job already uses this agreed default when the optional field is absent.
    if (settings.get("QLMS_BACKUP_STORAGE_BUDGET_BYTES") or str(APPROVED_BUDGET_BYTES)) != str(APPROVED_BUDGET_BYTES):
        raise ValueError("Storage budget must be 5 GB")
    url = make_url(settings.get("QLMS_BACKUP_DATABASE_URL") or "")
    if (project_ref(url) != PROJECT or url.get_backend_name() != "postgresql"
            or (url.username or "").split(".", 1)[0] != "qlms_backup"
            or url.query.get("sslmode") not in {"require", "verify-ca", "verify-full"}):
        raise ValueError("Use the restricted encrypted pilot backup connection")
    key_file, encoded = settings.get("QLMS_BACKUP_KEY_FILE"), settings.get("QLMS_BACKUP_KEY_BASE64")
    if bool(key_file) == bool(encoded):
        raise ValueError("Use exactly one existing key source")
    if key_file:
        with Path(key_file).open("rb") as source:
            key = source.read(33)
    else:
        key = base64.b64decode(encoded, validate=True)
    if len(key) != 32:
        raise ValueError("Existing key must contain exactly 32 bytes")
    secrets = {name: settings.get(name) for name in SECRET_NAMES}
    secrets["QLMS_BACKUP_KEY_BASE64"] = base64.b64encode(key).decode("ascii")
    if any(not isinstance(value, str) or not value or len(value.encode()) > 48000
           or any(character in value for character in "\r\n\0") for value in secrets.values()):
        raise ValueError("Private configuration is incomplete or malformed")
    if not re.fullmatch(r"https://hc-ping\.com/[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", secrets["QLMS_BACKUP_MONITOR_URL"]):
        raise ValueError("Use the existing private monitor URL")
    return secrets


def run_gh(executable, arguments, body=None, *, missing_ok=False):
    environment = {**os.environ, "GH_HOST": "github.com", "GH_PROMPT_DISABLED": "1"}
    environment.pop("GH_DEBUG", None)
    result = subprocess.run([str(executable), *arguments], input=body, text=True, encoding="utf-8",
                            capture_output=True, timeout=90, env=environment)
    if result.returncode:
        if missing_ok and "HTTP 404" in result.stderr:
            return None
        # CLI errors may echo request details: retain only a safe stage/error class.
        raise RuntimeError("GitHub operation failed; inspect privately")
    return result.stdout


def install(executable, secrets):
    def api(path, payload=None, *, missing_ok=False):
        arguments = ["api", path, "--hostname", "github.com"]
        if payload is not None:
            arguments += ["--method", "PUT", "--input", "-"]
        result = run_gh(executable, arguments, None if payload is None else json.dumps(payload), missing_ok=missing_ok)
        return json.loads(result) if result else None

    prefix = f"repos/{REPOSITORY}"
    if api("user").get("login") != "1ann0":
        raise ValueError("Sign in to the existing repository owner's GitHub account")
    repo = api(prefix)
    if repo.get("full_name") != REPOSITORY or repo.get("default_branch") != "main" or repo.get("private") is not False:
        raise ValueError("Unexpected repository or hosting budget")
    workflow = api(prefix + "/contents/.github/workflows/pilot-backup.yml?ref=main")
    if hashlib.sha256(base64.b64decode(workflow["content"]).replace(b"\r\n", b"\n")).hexdigest() != WORKFLOW_SHA256:
        raise ValueError("Reviewed workflow has not been installed on main")
    daily = api(prefix + "/actions/variables/QLMS_HOSTED_BACKUP_ENABLED", missing_ok=True)
    if daily and daily.get("value") == "true":
        raise ValueError("Daily backup is already enabled; do not reinstall live credentials")
    env_path = prefix + f"/environments/{ENVIRONMENT}"
    existing = api(env_path, missing_ok=True)
    policy = {"protected_branches": False, "custom_branch_policies": True}
    if existing is None:
        api(env_path, {"deployment_branch_policy": policy})
        run_gh(executable, ["api", env_path + "/deployment-branch-policies", "--hostname", "github.com",
                           "--method", "POST", "--input", "-"], json.dumps({"name": "main", "type": "branch"}))
    elif existing.get("deployment_branch_policy") != policy:
        raise ValueError("Existing environment must allow only main; its protections were preserved")
    policies = api(env_path + "/deployment-branch-policies?per_page=100")
    listed = policies.get("branch_policies", [])
    if policies.get("total_count") != 1 or len(listed) != 1 or listed[0].get("name") != "main" or listed[0].get("type") != "branch":
        raise ValueError("Environment permits an unexpected branch or tag")
    for name in ("QLMS_BACKUP_QUALIFICATION_ENABLED", "QLMS_HOSTED_BACKUP_ENABLED"):
        run_gh(executable, ["variable", "set", name, "--repo", REPOSITORY, "--body", "false"])
    for name, value in secrets.items():
        # Send each secret only through stdin, without a plaintext staging file or command-line value.
        run_gh(executable, ["secret", "set", name, "--repo", REPOSITORY, "--env", ENVIRONMENT], value)
    names = json.loads(run_gh(executable, ["secret", "list", "--repo", REPOSITORY, "--env", ENVIRONMENT, "--json", "name"]))
    if not set(secrets).issubset({item["name"] for item in names}):
        raise ValueError("Secret-name readback is incomplete")
    for name, value in (("QLMS_BACKUP_PROJECT_REF", PROJECT), ("QLMS_BACKUP_CLEANUP_ENABLED", "true")):
        run_gh(executable, ["variable", "set", name, "--repo", REPOSITORY, "--env", ENVIRONMENT, "--body", value])
    run_gh(executable, ["variable", "set", "QLMS_BACKUP_QUALIFICATION_ENABLED", "--repo", REPOSITORY, "--body", "true"])


def main():
    if not sys.stdin.isatty():
        print("FAIL: run private installation in your own interactive terminal outside Codex.")
        return 1
    root = Path(__file__).resolve().parents[2]
    stage = "confirmation"
    try:
        print("Transfer the existing settings to GitHub's main-only backup environment.")
        print("This includes the backup key. Keep your two separate recovery copies. Daily scheduling stays OFF.")
        if input("After retention PASS, type INSTALL BACKUP to continue: ").strip() != "INSTALL BACKUP":
            raise ValueError("Installation not confirmed")
        stage = "private configuration validation"
        settings = dotenv_values(root / "backend/ops/private/.env.pilot-hosted-backup", interpolate=False)
        secrets = prepare_secrets(settings)
        stage = "protected GitHub installation"
        install(root / "tmp/github-cli/gh.exe", secrets)
    except (Exception, KeyboardInterrupt) as error:
        reason = str(error) if str(error) in SAFE_FAILURES else type(error).__name__
        print(f"FAIL: {stage} ({reason}); do not enable daily scheduling.")
        return 1
    print("PASS: private cloud backup settings installed; main-only protection verified; daily schedule remains OFF.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
