"""Privately test failure and missing-run email delivery without running a backup."""
from dotenv import dotenv_values
import sys
import time

from ops.backup_monitor import signal
from ops.drive_authorize import PRIVATE, validate_destination


def confirm_email(prompt):
    while True:
        answer = input(prompt).strip().upper()
        if answer in {"YES", "RECEIVED"}:
            return
        if answer in {"NO", "NOT RECEIVED"}:
            raise ValueError("Email not received")
        print("Type YES only after that email arrives, or NO to stop if it has not arrived.")


def main():
    try:
        if not sys.stdin.isatty():
            raise ValueError("Use your own private terminal")
        settings = dotenv_values(PRIVATE / ".env.pilot-hosted-backup")
        validate_destination(settings)
        url = settings.get("QLMS_BACKUP_MONITOR_URL")
        print("Use the qualification check with Period 1 minute, Grace time 1 minute and company email enabled.")
        if input("Type TEST ALERTS to confirm these test settings: ").strip() != "TEST ALERTS":
            raise ValueError("Test settings not confirmed")
        signal(url, "success")
        signal(url, "fail")
        print("Look for the qualification failure email in the company inbox (including Spam).")
        confirm_email("Has the failure email arrived? Type YES after reading it, or NO to stop: ")
        signal(url, "success")
        print("Recovery ping acknowledged. Now wait 130 seconds (just over two minutes) with no more pings.", flush=True)
        time.sleep(130)
        print("Look for a NEW qualification Down/missing-run email, separate from the earlier failure email.")
        confirm_email("Has the NEW Down email arrived? Type YES after reading it, or NO to stop: ")
        signal(url, "success")
        print("PASS: private monitor signals acknowledged; human confirms failure and missing-run emails received. Change to the daily schedule before activation. No backup or database operation ran.")
        return 0
    except (Exception, KeyboardInterrupt) as error:
        print(f"FAIL: private alert qualification ({type(error).__name__}); schedule remains off.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
