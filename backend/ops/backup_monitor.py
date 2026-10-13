"""Send only backup status to the independent monitor; never attach logs or data."""
import argparse
import os
import re
import sys
from urllib.request import HTTPRedirectHandler, Request, build_opener


class NoRedirects(HTTPRedirectHandler):
    # This standalone monitor must work even if backup dependencies fail to install.
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def signal(url, status, *, opener=None):
    if (not isinstance(url, str) or not re.fullmatch(r"https://hc-ping\.com/[a-f0-9]{8}(?:-[a-f0-9]{4}){3}-[a-f0-9]{12}", url)
            or status not in {"start", "success", "fail"}):
        raise ValueError("Use the private monitor URL and a recognized signal")
    suffix = "" if status == "success" else "/" + status
    try:
        request = Request(url + suffix, data=b"", method="POST")
        with (opener or build_opener(NoRedirects())).open(request, timeout=15) as response:
            if response.status != 200 or response.read(128) != b"OK":
                raise ValueError("Monitor did not acknowledge this signal")
    except Exception:
        raise RuntimeError("Private backup monitor signal failed") from None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("status", choices=["start", "success", "fail"])
    status = parser.parse_args().status
    try:
        signal(os.environ.get("QLMS_BACKUP_MONITOR_URL"), status)
    except Exception as error:
        print(f"FAIL: backup monitor signal ({type(error).__name__}). Inspect privately.", file=sys.stderr)
        return 1
    print("Backup monitor signal acknowledged. Mail delivery still requires verification.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
