"""Read-only public release checks; never load credentials or fetch shop records."""
import argparse
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.parse import quote, urljoin, urlsplit
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


class SmokeFailure(ValueError):
    pass


@dataclass(frozen=True)
class HttpResult:
    status: int
    headers: dict
    body: bytes


def public_origin(value):
    parsed = urlsplit(value)
    if (parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password
            or parsed.query or parsed.fragment or parsed.path not in ("", "/")):
        raise SmokeFailure("Use public HTTPS origins without credentials, paths or query strings")
    return value.rstrip("/")


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, response, code, message, headers, new_url):
        return None


def fetch_public(url, *, timeout=35, read_body=True):
    # Canonical .html redirects are allowed only within the requested origin.
    origin = urlsplit(url)._replace(path="", query="", fragment="").geturl()
    opener = build_opener(ProxyHandler({}), NoRedirect())
    for _ in range(4):
        try:
            response = opener.open(Request(url, headers={"User-Agent": "QLMS-release-smoke/1.0"}), timeout=timeout)
        except HTTPError as error:
            response = error
        with response:
            status = response.code
            headers = {key.lower(): value for key, value in response.headers.items()}
            if status in (301, 302, 303, 307, 308):
                destination = urljoin(url, headers.get("location", ""))
                parsed = urlsplit(destination)
                if (public_origin(parsed._replace(path="", query="", fragment="").geturl()) != origin
                        or parsed.query or parsed.fragment):
                    raise SmokeFailure("Unexpected redirect outside the approved public origin")
                url = destination
                continue
            # Denial probes never read a body, even if authorization is broken.
            body = response.read(8 * 1024 * 1024 + 1) if read_body else b""
            if len(body) > 8 * 1024 * 1024:
                raise SmokeFailure("Public response exceeded the smoke-check size limit")
            return HttpResult(status, headers, body)
    raise SmokeFailure("Too many public hosting redirects")


def verify_release(manifest, frontend, api, source, *, fetch=fetch_public):
    frontend, api = public_origin(frontend), public_origin(api)
    if (not re.fullmatch(r"[0-9a-f]{40}", source) or manifest.get("source") != source
            or manifest.get("apiOrigin") != api):
        raise SmokeFailure("Manifest source/API origin does not match the approved release")
    assets = manifest.get("assets")
    if not isinstance(assets, dict) or not 1 <= len(assets) <= 1000:
        raise SmokeFailure("Use a nonempty, bounded public asset manifest")
    for name, expected in assets.items():
        if (not isinstance(name, str) or not re.fullmatch(r"[A-Za-z0-9_./@!+-]+", name)
                or name.startswith("/") or any(part in ("", ".", "..") for part in name.split("/"))
                or not isinstance(expected, str) or not re.fullmatch(r"[0-9a-f]{64}", expected)):
            raise SmokeFailure("Invalid public asset path or hash")
    if not {"index.html", "login.html", "dashboard.html", "reports.html", "expenses.html"}.issubset(assets):
        raise SmokeFailure("Manifest is missing required staff pages")

    def request(origin, path, **options):
        try:
            return fetch(origin + path, **options)
        except Exception:
            # Do not print server bodies, driver errors, private headers or exception URLs.
            raise SmokeFailure(f"Public request failed: {path}") from None

    def check_headers(reply, label, *, page=False):
        cache = {item.strip().lower() for item in reply.headers.get("cache-control", "").split(",")}
        required = {"x-content-type-options": "nosniff", "x-frame-options": "DENY", "referrer-policy": "no-referrer"}
        if not {"no-store", "private"}.issubset(cache) or any(reply.headers.get(key) != value for key, value in required.items()):
            raise SmokeFailure(f"Missing private/security headers: {label}")
        if page:
            directives = {part.strip().split()[0]: part.strip().split()[1:]
                          for part in reply.headers.get("content-security-policy", "").split(";") if part.strip()}
            if (set(directives.get("connect-src", [])) != {"'self'", api}
                    or directives.get("frame-ancestors") != ["'none'"]
                    or reply.headers.get("strict-transport-security") != "max-age=31536000"):
                raise SmokeFailure(f"Wrong API origin or browser security policy: {label}")

    ready = request(api, "/health/ready", timeout=120)
    try:
        is_ready = ready.status == 200 and json.loads(ready.body).get("status") == "ready"
    except (ValueError, AttributeError):
        is_ready = False
    if not is_ready:
        raise SmokeFailure("API readiness failed; do not promote this release")
    check_headers(ready, "API readiness")
    contract = request(api, "/openapi.json")
    try:
        paths = json.loads(contract.body)["paths"] if contract.status == 200 else {}
        has_contract = {"/expenses", "/dashboard/summary", "/dashboard/reports/{report_name}"}.issubset(paths)
    except (ValueError, KeyError, TypeError):
        has_contract = False
    if not has_contract:
        raise SmokeFailure("API contract is missing required expense/report routes")
    denials = ("/expenses/1", "/dashboard/summary", "/dashboard/reports/catalogue")
    for path in denials:
        reply = request(api, path, read_body=False)
        if reply.status not in (401, 403):
            raise SmokeFailure(f"Owner endpoint did not deny anonymous access: {path}")
        check_headers(reply, path)

    def check_asset(pair):
        name, expected = pair
        reply = request(frontend, "/" + quote(name, safe="/"))
        allowed = (200, 404) if name == "404.html" else (200,)
        if reply.status not in allowed or hashlib.sha256(reply.body).hexdigest() != expected:
            raise SmokeFailure(f"Hosted asset mismatch: {name}")
        return name.endswith(".js") and api.encode() in reply.body

    public_assets = [(name, expected) for name, expected in assets.items() if name != "_headers"]
    with ThreadPoolExecutor(max_workers=8) as pool:
        compiled_api = any(list(pool.map(check_asset, public_assets)))
    if not compiled_api:
        raise SmokeFailure("Compiled frontend assets do not contain the approved API origin")
    pages = [(name, expected) for name, expected in assets.items() if name.endswith(".html") and name != "404.html"]
    for name, expected in pages:
        path = "/" if name == "index.html" else "/" + name[:-5]
        reply = request(frontend, path)
        if reply.status != 200 or hashlib.sha256(reply.body).hexdigest() != expected:
            raise SmokeFailure(f"Hosted page missing or serving the wrong document: {path}")
        check_headers(reply, path, page=True)
    return {"checked_at": datetime.now(timezone.utc).isoformat(), "source": source,
            "frontend": frontend, "api_origin": api, "public_asset_count": len(public_assets),
            "page_count": len(pages), "anonymous_denial_count": len(denials), "passed": True,
            "authenticated_workflows_checked": False, "api_commit_verified": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--frontend", required=True)
    parser.add_argument("--api", required=True)
    parser.add_argument("--source", required=True, help="Approved full frontend source SHA")
    parser.add_argument("--output", type=Path, help="New public JSON evidence file; never overwrites an existing file")
    args = parser.parse_args()
    try:
        if args.manifest.stat().st_size > 1024 * 1024:
            raise SmokeFailure("Public asset manifest exceeded its size limit")
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        result = verify_release(manifest, args.frontend, args.api, args.source)
        if args.output:
            with args.output.open("x", encoding="utf-8") as destination:
                destination.write(json.dumps(result, indent=2) + "\n")
    except SmokeFailure as error:
        print(f"FAIL: {error}")
        return 1
    except (OSError, ValueError, TypeError, AttributeError):
        print("FAIL: could not read the public manifest or create new public evidence; no files overwritten")
        return 1
    print(f"PASS: {result['public_asset_count']} public asset hashes, {result['page_count']} pages, "
          f"API readiness/contract and {result['anonymous_denial_count']} anonymous denials verified.")
    print("Private staff workflows and the API commit still require separate release evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
