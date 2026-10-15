"""Read public backup-job proof before a catch-up; uncertainty always requests a fresh backup."""
import argparse
from datetime import datetime, timedelta, timezone
import json
import os
from urllib.parse import urlencode

from ops.release_smoke import fetch_public


REPOSITORY = "1ann0/Qinetra-Laundry-Management-System"
BASE = f"https://api.github.com/repos/{REPOSITORY}/actions"
VERIFIED_STEPS = {"Require qualified retention before a scheduled run",
                  "Export encrypted archive and authenticate Drive readback", "Signal verified completion"}


def backup_window(now):
    if now.tzinfo is None:
        raise ValueError("Backup admission requires an explicit time zone")
    utc = now.astimezone(timezone.utc)
    start = utc.replace(hour=19, minute=0, second=0, microsecond=0)
    return start if utc >= start else start - timedelta(days=1)


def read_metadata(path):
    reply = fetch_public(BASE + path, timeout=20)
    if reply.status != 200:
        raise ValueError("Public workflow metadata unavailable")
    return json.loads(reply.body)


def timestamp(value):
    result = datetime.fromisoformat(value)
    if result.tzinfo is None:
        raise ValueError("Missing workflow timestamp zone")
    return result.astimezone(timezone.utc)


def backup_required(current_run_id, *, now=None, fetch_json=read_metadata):
    now = now or datetime.now(timezone.utc)
    start = backup_window(now)
    query = urlencode({"event": "schedule", "branch": "main", "status": "success", "per_page": 100,
                       "created": ">=" + start.strftime("%Y-%m-%dT%H:%M:%SZ")})
    try:
        runs = fetch_json("/workflows/pilot-backup.yml/runs?" + query)["workflow_runs"]
        if not isinstance(runs, list):
            return True
        # Three ordinary triggers/day; cap work if repeated operator reruns inflate history.
        for run in runs[:10]:
            run_id = run.get("id")
            if (type(run_id) is not int or run_id <= 0 or run_id == current_run_id
                    or run.get("event") != "schedule" or run.get("head_branch") != "main"
                    or run.get("status") != "completed" or run.get("conclusion") != "success"
                    or not start <= timestamp(run.get("created_at")) <= now):
                continue
            jobs = fetch_json(f"/runs/{run_id}/jobs?per_page=100")["jobs"]
            for job in jobs:
                if job.get("name") != "backup" or job.get("conclusion") != "success" or job.get("status") != "completed":
                    continue
                verified = {step.get("name") for step in job.get("steps", [])
                            if step.get("name") in VERIFIED_STEPS and step.get("status") == "completed"
                            and step.get("conclusion") == "success"
                            and start <= timestamp(step.get("completed_at")) <= now}
                if VERIFIED_STEPS.issubset(verified):
                    return False
    except Exception:
        # Never suppress a backup because API history is unavailable, malformed or rate-limited.
        return True
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scheduled", action="store_true")
    parser.add_argument("--run-id", type=int, default=os.environ.get("GITHUB_RUN_ID", "0"))
    args = parser.parse_args()
    required = not args.scheduled or backup_required(args.run_id)
    print("required=" + str(required).lower())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
