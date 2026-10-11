"""Private Drive transport; success requires authenticated remote readback."""
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urlencode, urlsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

from ops.backup import decrypt_export, MAX_EXPORT, MAX_HEADER


API = "https://www.googleapis.com/drive/v3"
UPLOAD = "https://www.googleapis.com/upload/drive/v3/files"
MAX_ENVELOPE = MAX_EXPORT + MAX_HEADER + 40


class NoRedirects(HTTPRedirectHandler):
    # An API redirect must never forward a credential to another origin.
    def redirect_request(self, request, file, code, message, headers, new_url):
        return None


def send_request(opener, request, limit=1024 * 1024):
    try:
        with opener.open(request, timeout=60) as response:
            data, headers = response.read(limit + 1), response.headers
    except Exception:
        raise RuntimeError("Private Drive request failed") from None
    if len(data) > limit:
        raise ValueError("Drive response exceeded the expected size")
    return data, headers


def refresh_access_token(client_id, client_secret, refresh_token, *, opener=None):
    if any(not value for value in [client_id, client_secret, refresh_token]):
        raise ValueError("Unattended Drive authentication is incomplete")
    body = urlencode({"client_id": client_id, "client_secret": client_secret,
                      "refresh_token": refresh_token, "grant_type": "refresh_token"}).encode()
    try:
        data, _ = send_request(opener or build_opener(NoRedirects()),
                               Request("https://oauth2.googleapis.com/token", data=body,
                                       headers={"Content-Type": "application/x-www-form-urlencoded"}, method="POST"))
        result = json.loads(data)
        token = result.get("access_token")
        if result.get("token_type", "").lower() != "bearer" or not isinstance(token, str) or not token or len(token) > 8192 or "\n" in token or "\r" in token:
            raise ValueError()
        return token
    except Exception:
        raise RuntimeError("Drive authentication failed") from None


class DriveStorage:
    def __init__(self, access_token, expected_account, folder_id, *, opener=None):
        if not isinstance(access_token, str) or not access_token or len(access_token) > 8192 or "\r" in access_token or "\n" in access_token:
            raise ValueError("Invalid Drive authentication")
        if not expected_account or not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", folder_id or ""):
            raise ValueError("Private Drive destination is incomplete")
        self.token = access_token
        self.account = expected_account.strip().casefold()
        self.folder_id = folder_id
        self.opener = opener or build_opener(NoRedirects())

    def request(self, url, *, method="GET", data=None, headers=None, limit=1024 * 1024):
        parsed = urlsplit(url)
        if parsed.scheme != "https" or parsed.netloc != "www.googleapis.com" or not parsed.path.startswith(("/drive/v3/", "/upload/drive/v3/")):
            raise ValueError("Unexpected Drive endpoint")
        request_headers = {"Authorization": "Bearer " + self.token, **(headers or {})}
        return send_request(self.opener, Request(url, data=data, headers=request_headers, method=method), limit)

    def metadata(self, file_id):
        if not re.fullmatch(r"[A-Za-z0-9_-]{3,200}", file_id or ""):
            raise ValueError("Invalid Drive file reference")
        fields = "id,mimeType,trashed,shared,permissions(type,role,emailAddress),parents,size,capabilities(canAddChildren)"
        data, _ = self.request(API + "/files/" + file_id + "?" + urlencode({"fields": fields}))
        return json.loads(data)

    def private_owner(self, metadata, expected_id):
        permissions = metadata.get("permissions", [])
        return (metadata.get("id") == expected_id and metadata.get("shared") is False
                and metadata.get("trashed") is False and len(permissions) == 1
                and permissions[0].get("type") == "user" and permissions[0].get("role") == "owner"
                and permissions[0].get("emailAddress", "").casefold() == self.account)

    def check_destination(self):
        data, _ = self.request(API + "/about?fields=user(emailAddress)")
        if json.loads(data).get("user", {}).get("emailAddress", "").casefold() != self.account:
            raise ValueError("Drive connection belongs to a different account")
        folder = self.metadata(self.folder_id)
        if not self.private_owner(folder, self.folder_id) or folder.get("mimeType") != "application/vnd.google-apps.folder" or folder.get("capabilities", {}).get("canAddChildren") is not True:
            raise ValueError("Drive destination must be private, owned and writable")

    def check_capacity(self, archive_bytes, reserved_bytes):
        if type(archive_bytes) is not int or archive_bytes <= 0 or type(reserved_bytes) is not int or reserved_bytes < 0:
            raise ValueError("Invalid backup capacity requirement")
        data, _ = self.request(API + "/about?" + urlencode({"fields": "user(emailAddress),storageQuota"}))
        about = json.loads(data)
        if about.get("user", {}).get("emailAddress", "").casefold() != self.account:
            raise ValueError("Drive connection belongs to a different account")
        quota = about.get("storageQuota", {})
        if any(not isinstance(quota.get(field), str) or not re.fullmatch(r"[0-9]{1,30}", quota[field])
               for field in ("limit", "usage")):
            raise ValueError("Actual Drive storage allowance is unknown")
        available = int(quota["limit"]) - int(quota["usage"])
        if available - archive_bytes < reserved_bytes:
            raise ValueError("Actual Drive free space cannot preserve the backup headroom")
        return available

    def upload_verified(self, archive_path, key):
        path = Path(archive_path)
        if path.suffix != ".qlmsbackup" or path.stat().st_size > MAX_ENVELOPE:
            raise ValueError("Upload only a bounded encrypted database archive")
        envelope = path.read_bytes()
        plaintext, metadata = decrypt_export(envelope, key)
        if not plaintext.startswith(b"PGDMP") or hashlib.sha256(plaintext).hexdigest() != metadata.get("archive_sha256"):
            raise ValueError("Upload requires an authenticated PostgreSQL archive")
        self.check_destination()
        body = json.dumps({"name": path.name, "parents": [self.folder_id],
                           "mimeType": "application/octet-stream"}).encode()
        _, headers = self.request(UPLOAD + "?uploadType=resumable&fields=id", method="POST", data=body,
                                  headers={"Content-Type": "application/json; charset=UTF-8",
                                           "X-Upload-Content-Type": "application/octet-stream",
                                           "X-Upload-Content-Length": str(len(envelope))})
        session = headers.get("Location", "")
        location = urlsplit(session)
        if location.scheme != "https" or location.netloc != "www.googleapis.com" or location.path != "/upload/drive/v3/files":
            raise ValueError("Unexpected Drive upload location")
        # Unknown upload outcomes are failures; never blindly POST another archive.
        result, _ = self.request(session, method="PUT", data=envelope,
                                 headers={"Content-Type": "application/octet-stream"})
        file_id = json.loads(result).get("id")
        remote = self.metadata(file_id)
        if not self.private_owner(remote, file_id) or remote.get("parents") != [self.folder_id] or remote.get("size") != str(len(envelope)) or remote.get("mimeType") != "application/octet-stream":
            raise ValueError("Uploaded archive metadata failed verification")
        downloaded, _ = self.request(API + "/files/" + file_id + "?alt=media", limit=len(envelope))
        if hashlib.sha256(downloaded).digest() != hashlib.sha256(envelope).digest() or decrypt_export(downloaded, key) != (plaintext, metadata):
            raise ValueError("Remote archive failed authenticated readback")
        self.check_destination()
        return file_id
