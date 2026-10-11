"""Human-run, credential-private Google folder consent for the existing pilot runner."""
import base64
import hashlib
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import re
import secrets
import sys
import time
from urllib.parse import parse_qs, urlencode, urlsplit
from urllib.request import Request, build_opener
import webbrowser

from dotenv import dotenv_values

from ops.drive_storage import DriveStorage, NoRedirects, send_request


PROJECT = "istweeaqtykwfuhntgik"
PRIVATE = Path(__file__).resolve().parent / "private"
AUTH_URL = "https://accounts.google.com/o/oauth2/v2/auth"
TOKEN_URL = "https://oauth2.googleapis.com/token"
SCOPE = "https://www.googleapis.com/auth/drive.file"
GRANT_KEYS = ("QLMS_DRIVE_CLIENT_ID", "QLMS_DRIVE_CLIENT_SECRET", "QLMS_DRIVE_REFRESH_TOKEN")


def private_value(value):
    if not isinstance(value, str) or not re.fullmatch(r"[A-Za-z0-9._~/+=-]{1,8192}", value):
        raise ValueError("Invalid private authorization value")
    return value


def validate_client(data):
    if not isinstance(data, dict) or not isinstance(data.get("installed"), dict):
        raise ValueError("Use the downloaded Google Desktop application client")
    client = data.get("installed", {})
    if (client.get("auth_uri"), client.get("token_uri")) != (AUTH_URL, TOKEN_URL):
        raise ValueError("Use the downloaded Google Desktop application client")
    if not private_value(client.get("client_id")).endswith(".apps.googleusercontent.com"):
        raise ValueError("Invalid Google client")
    private_value(client.get("client_secret"))
    return client


def validate_destination(settings):
    if (settings.get("QLMS_BACKUP_PROJECT_REF"), settings.get("QLMS_BACKUP_PROVIDER"),
            settings.get("QLMS_DB_SCHEMA")) != (PROJECT, "google_drive", "qlms"):
        raise ValueError("Use the existing pilot backup configuration")
    if not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", settings.get("QLMS_BACKUP_DRIVE_FOLDER_ID") or ""):
        raise ValueError("The approved folder is missing")
    if not re.fullmatch(r"[^\s@]+@[^\s@]+", settings.get("QLMS_BACKUP_DRIVE_ACCOUNT") or ""):
        raise ValueError("The approved account is missing")


def authorization_url(client, folder, account, redirect_uri, state, verifier):
    challenge = base64.urlsafe_b64encode(hashlib.sha256(verifier.encode()).digest()).rstrip(b"=").decode()
    return AUTH_URL + "?" + urlencode({
        "client_id": client["client_id"], "redirect_uri": redirect_uri, "response_type": "code",
        "scope": SCOPE, "access_type": "offline", "prompt": "consent", "trigger_onepick": "true",
        "file_ids": folder, "mimetypes": "application/vnd.google-apps.folder", "allow_folder_selection": "true",
        "include_granted_scopes": "false", "login_hint": account, "state": state,
        "code_challenge": challenge, "code_challenge_method": "S256",
    })


def callback_code(path, state, folder):
    if len(path) > 16384:
        raise ValueError("Invalid callback")
    parsed = urlsplit(path)
    fields = parse_qs(parsed.query, keep_blank_values=True, max_num_fields=20)
    if (parsed.path != "/callback" or parsed.scheme or parsed.netloc or parsed.fragment
            or any(len(values) != 1 for values in fields.values()) or "error" in fields
            or fields.get("state") != [state] or fields.get("picked_file_ids") != [folder]
            or fields.get("scope") != [SCOPE]):
        raise ValueError("Consent did not select exactly the approved folder and scope")
    return private_value(fields.get("code", [None])[0])


def exchange_code(client, code, redirect_uri, verifier, *, opener=None):
    body = urlencode({"client_id": client["client_id"], "client_secret": client["client_secret"],
                      "code": code, "redirect_uri": redirect_uri, "code_verifier": verifier,
                      "grant_type": "authorization_code"}).encode()
    request = Request(TOKEN_URL, data=body, headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST")
    data, _ = send_request(opener or build_opener(NoRedirects()), request)
    tokens = json.loads(data)
    if (tokens.get("scope") != SCOPE or tokens.get("token_type", "").casefold() != "bearer"
            or type(tokens.get("expires_in")) is not int or not 0 < tokens["expires_in"] <= 86400
            or "refresh_token_expires_in" in tokens):
        raise ValueError("Authorization is broader than required or time-limited")
    private_value(tokens.get("access_token"))
    private_value(tokens.get("refresh_token"))
    return tokens


def save_grant(path, client, tokens):
    values = (client["client_id"], client["client_secret"], tokens["refresh_token"])
    # Preserve the existing owner-only file ACL; validate all replacements before writing.
    with path.open("r+", encoding="utf-8", newline="") as output:
        content = output.read()
        for name, value in zip(GRANT_KEYS, values):
            content, count = re.subn(r"^" + name + r"=[^\r\n]*(?=\r?$)", lambda _: name + "=" + private_value(value),
                                    content, flags=re.MULTILINE)
            if count != 1:
                raise ValueError("Each private grant setting must appear exactly once")
        output.seek(0)
        output.write(content)
        output.truncate()


def verify_and_save(path, client, tokens, settings, *, opener=None):
    DriveStorage(tokens["access_token"], settings["QLMS_BACKUP_DRIVE_ACCOUNT"],
                 settings["QLMS_BACKUP_DRIVE_FOLDER_ID"], opener=opener).check_destination()
    save_grant(path, client, tokens)


def consent_server(state, folder):
    class LoopbackServer(HTTPServer):
        def get_request(self):
            connection, address = super().get_request()
            connection.settimeout(5)
            return connection, address

    class Callback(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass  # Callback URLs contain private authorization codes.

        def do_GET(self):
            status, message = 400, "Consent not accepted. Return to your private terminal."
            if self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}":
                try:
                    self.server.code = callback_code(self.path, state, folder)
                    status, message = 200, "Consent received. Close this tab and check your private terminal."
                except ValueError:
                    pass
            self.send_response(status)
            self.send_header("Content-Type", "text/plain; charset=utf-8")
            self.send_header("Cache-Control", "no-store")
            self.send_header("Referrer-Policy", "no-referrer")
            self.send_header("Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(message.encode())

    server = LoopbackServer(("127.0.0.1", 0), Callback)
    server.timeout, server.code = 1, None
    return server


def run_authorization():
    settings_path = PRIVATE / ".env.pilot-hosted-backup"
    settings = dotenv_values(settings_path, interpolate=False)
    validate_destination(settings)
    client_path = PRIVATE / "google-desktop-client.json"
    if client_path.stat().st_size > 16384:
        raise ValueError("Invalid client file")
    client = validate_client(json.loads(client_path.read_text(encoding="utf-8")))
    print("Use the existing business account and select only its recorded private backup folder.")
    print("In Google Auth platform > Audience, confirm this app is In production. Testing grants expire.")
    if input("Type IN PRODUCTION after checking: ").strip() != "IN PRODUCTION":
        raise ValueError("Production consent has not been confirmed")
    state, verifier = secrets.token_urlsafe(32), secrets.token_urlsafe(48)
    with consent_server(state, settings["QLMS_BACKUP_DRIVE_FOLDER_ID"]) as server:
        redirect_uri = f"http://127.0.0.1:{server.server_port}/callback"
        url = authorization_url(client, settings["QLMS_BACKUP_DRIVE_FOLDER_ID"],
                                settings["QLMS_BACKUP_DRIVE_ACCOUNT"], redirect_uri, state, verifier)
        if not webbrowser.open(url, new=1):
            raise RuntimeError("The private browser could not be opened")
        deadline = time.monotonic() + 300
        while server.code is None and time.monotonic() < deadline:
            server.handle_request()
        if server.code is None:
            raise TimeoutError("Private consent did not finish within five minutes")
        tokens = exchange_code(client, server.code, redirect_uri, verifier)
    verify_and_save(settings_path, client, tokens, settings)


def main():
    if not sys.stdin.isatty():
        print("FAIL: run private Drive consent in your own interactive terminal outside Codex.")
        return 1
    try:
        run_authorization()
    except Exception as error:
        print(f"FAIL: private Drive consent ({type(error).__name__}); no backup schedule activated.")
        return 1
    print("PASS: selected private Drive folder and account verified; runner consent saved privately. Schedule remains off.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
