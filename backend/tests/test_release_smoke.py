"""Read-only release verification must fail for incomplete or mismatched hosting."""
import hashlib
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ops.release_smoke import HttpResult, SmokeFailure, fetch_public, main, verify_release


class ReleaseSmokeTests(unittest.TestCase):
    def setUp(self):
        self.frontend = "https://shop.example.invalid"
        self.api = "https://api.example.invalid"
        self.source = "a" * 40
        self.headers = {
            "cache-control": "no-store, private, max-age=0",
            "x-content-type-options": "nosniff", "x-frame-options": "DENY",
            "referrer-policy": "no-referrer",
            "strict-transport-security": "max-age=31536000",
            "content-security-policy": f"default-src 'self'; connect-src 'self' {self.api}; frame-ancestors 'none'",
        }
        assets = {name: b"fictional page" for name in (
            "404.html", "index.html", "login.html", "dashboard.html", "reports.html", "expenses.html",
        )}
        assets["_next/static/app.js"] = f'const api="{self.api}";'.encode()
        self.manifest = {"source": self.source, "apiOrigin": self.api,
                         "assets": {name: hashlib.sha256(body).hexdigest() for name, body in assets.items()}}
        self.responses = {self.frontend + "/" + name: HttpResult(200, self.headers.copy(), body)
                          for name, body in assets.items()}
        for name, body in assets.items():
            if name.endswith(".html") and name != "404.html":
                path = "/" if name == "index.html" else "/" + name[:-5]
                self.responses[self.frontend + path] = HttpResult(200, self.headers.copy(), body)
        self.responses[self.api + "/health/ready"] = HttpResult(200, self.headers.copy(), b'{"status":"ready"}')
        paths = {path: {} for path in ("/expenses", "/dashboard/summary", "/dashboard/reports/{report_name}")}
        self.responses[self.api + "/openapi.json"] = HttpResult(200, {}, json.dumps({"paths": paths}).encode())
        for path in ("/expenses/1", "/dashboard/summary", "/dashboard/reports/catalogue"):
            self.responses[self.api + path] = HttpResult(401, self.headers.copy(), b'{"detail":"Not authenticated"}')
        self.calls = []

    def fetch(self, url, **options):
        self.calls.append(url)
        return self.responses[url]

    def verify(self):
        return verify_release(self.manifest, self.frontend, self.api, self.source, fetch=self.fetch)

    def test_complete_release_verifies_assets_routes_readiness_and_denials(self):
        self.manifest["assets"]["_headers"] = "0" * 64
        result = self.verify()
        self.assertEqual(result["public_asset_count"], 7)
        self.assertEqual(result["page_count"], 5)
        self.assertEqual(result["anonymous_denial_count"], 3)
        self.assertFalse(result["authenticated_workflows_checked"])
        self.assertFalse(result["api_commit_verified"])
        self.assertNotIn(self.frontend + "/_headers", self.calls)

    def test_new_page_in_manifest_is_checked_without_another_route_list(self):
        body = b"fictional extra page"
        self.manifest["assets"]["customers/history.html"] = hashlib.sha256(body).hexdigest()
        self.responses[self.frontend + "/customers/history.html"] = HttpResult(200, self.headers, body)
        self.responses[self.frontend + "/customers/history"] = HttpResult(404, self.headers, b"missing")
        with self.assertRaisesRegex(SmokeFailure, "/customers/history"):
            self.verify()

    def test_closing_release_requires_its_api_contract_and_anonymous_denials(self):
        body = b'fictional closing page'
        self.manifest['assets']['daily-close.html'] = hashlib.sha256(body).hexdigest()
        for path in ('/daily-close.html', '/daily-close'):
            self.responses[self.frontend + path] = HttpResult(200, self.headers, body)
        with self.assertRaisesRegex(SmokeFailure, 'contract'):
            self.verify()
        paths = {path: {} for path in ('/expenses', '/dashboard/summary',
            '/dashboard/reports/{report_name}', '/daily-close', '/till-movements',
            '/till-movements/{movement_id}', '/till-movements/{movement_id}/corrections')}
        self.responses[self.api + '/openapi.json'] = HttpResult(200, {}, json.dumps({'paths':paths}).encode())
        probes = ('/daily-close?date=2000-01-01', '/till-movements/1',
            '/dashboard/reports/closing', '/dashboard/reports/till')
        for path in probes:
            self.responses[self.api + path] = HttpResult(401, self.headers, b'')
        self.assertEqual(self.verify()['anonymous_denial_count'], 7)
        self.responses[self.api + probes[0]] = HttpResult(200, self.headers, b'')
        with self.assertRaisesRegex(SmokeFailure, 'anonymous'):
            self.verify()

    def test_generated_next_route_payload_names_are_accepted(self):
        name, body = "expenses/__next.!KHByb3RlY3RlZCk.expenses.__PAGE__.txt", b"fictional route payload"
        self.manifest["assets"][name] = hashlib.sha256(body).hexdigest()
        self.responses[self.frontend + "/" + name.replace("!", "%21")] = HttpResult(200, {}, body)
        self.assertEqual(self.verify()["public_asset_count"], 8)

    def test_expense_probe_uses_the_existing_read_route_instead_of_the_post_collection(self):
        self.responses[self.api + "/expenses"] = HttpResult(405, self.headers, b"")
        self.responses[self.api + "/expenses/1"] = HttpResult(401, self.headers, b"")
        self.assertTrue(self.verify()["passed"])
        self.assertNotIn(self.api + "/expenses", self.calls)

    def test_missing_route_or_wrong_html_fails_even_when_asset_path_exists(self):
        for reply in (HttpResult(404, self.headers, b"not found"), HttpResult(200, self.headers, b"fallback login")):
            with self.subTest(status=reply.status):
                self.responses[self.frontend + "/expenses"] = reply
                with self.assertRaisesRegex(SmokeFailure, "/expenses"):
                    self.verify()

    def test_stale_asset_wrong_api_or_missing_security_headers_fail(self):
        original = self.responses[self.frontend + "/_next/static/app.js"]
        self.responses[self.frontend + "/_next/static/app.js"] = HttpResult(200, {}, b"old build")
        with self.assertRaisesRegex(SmokeFailure, "asset"):
            self.verify()
        self.responses[self.frontend + "/_next/static/app.js"] = original
        for field, value in (("content-security-policy", "connect-src 'self' https://wrong.example.invalid"),
                             ("cache-control", "public, max-age=3600"), ("x-frame-options", "SAMEORIGIN")):
            headers = self.headers.copy()
            headers[field] = value
            self.responses[self.frontend + "/expenses"] = HttpResult(200, headers, b"fictional page")
            with self.subTest(field=field), self.assertRaises(SmokeFailure):
                self.verify()

    def test_unready_api_or_missing_contract_or_unprotected_data_fails(self):
        ready_url = self.api + "/health/ready"
        for reply in (HttpResult(503, {}, b'{"status":"not_ready"}'), HttpResult(200, {}, b"not JSON")):
            self.responses[ready_url] = reply
            with self.subTest(status=reply.status), self.assertRaisesRegex(SmokeFailure, "readiness"):
                self.verify()
        self.responses[ready_url] = HttpResult(200, self.headers, b'{"status":"ready"}')
        contract_url = self.api + "/openapi.json"
        original = self.responses[contract_url]
        self.responses[contract_url] = HttpResult(200, {}, b'{"paths":{}}')
        with self.assertRaisesRegex(SmokeFailure, "contract"):
            self.verify()
        self.responses[contract_url] = original
        self.responses[self.api + "/expenses/1"] = HttpResult(200, self.headers, b"[]")
        with self.assertRaisesRegex(SmokeFailure, "anonymous"):
            self.verify()

    def test_invalid_manifest_or_secret_bearing_origin_fails_before_network(self):
        for changes in ({"source": "b" * 40}, {"apiOrigin": "https://wrong.example.invalid"},
                        {"assets": {"../private": "a" * 64}}, {"assets": {}},
                        {"assets": {"login.html": "not a hash"}}):
            with self.subTest(changes=changes):
                manifest = {**self.manifest, **changes}
                self.calls.clear()
                with self.assertRaises(SmokeFailure):
                    verify_release(manifest, self.frontend, self.api, self.source, fetch=self.fetch)
                self.assertEqual(self.calls, [])
        for origin in ("http://shop.example.invalid", "https://user:secret@shop.example.invalid",
                       "https://shop.example.invalid/?token=secret", "https://shop.example.invalid/path"):
            with self.subTest(origin=origin), self.assertRaises(SmokeFailure):
                verify_release(self.manifest, origin, self.api, self.source, fetch=self.fetch)

    def test_network_failures_are_sanitized_without_response_or_exception_contents(self):
        def broken_fetch(url, **options):
            raise OSError("fictional secret must never appear")
        with self.assertRaises(SmokeFailure) as failure:
            verify_release(self.manifest, self.frontend, self.api, self.source, fetch=broken_fetch)
        self.assertNotIn("fictional secret", str(failure.exception))

    def test_http_client_follows_only_same_origin_and_never_reads_denial_bodies(self):
        class Reply:
            def __init__(self, code, headers):
                self.code, self.headers = code, headers
            def __enter__(self):
                return self
            def __exit__(self, *args):
                pass
            def read(self, limit):
                raise AssertionError("A protected endpoint body must not be read")

        with patch("ops.release_smoke.build_opener") as build:
            opener = build.return_value
            opener.open.side_effect = [Reply(308, {"Location": "/expenses"}), Reply(401, {})]
            result = fetch_public(self.api + "/expenses.html", read_body=False)
            self.assertEqual(result.status, 401)
            self.assertEqual(result.body, b"")
            self.assertEqual(opener.open.call_args_list[1].args[0].full_url, self.api + "/expenses")
            opener.open.reset_mock()
            opener.open.side_effect = [Reply(302, {"Location": "https://wrong.example.invalid/login"})]
            with self.assertRaises(SmokeFailure):
                fetch_public(self.api + "/expenses")
            self.assertEqual(opener.open.call_count, 1)

    def test_cli_writes_public_evidence_once_without_overwriting_existing_files(self):
        with tempfile.TemporaryDirectory() as folder:
            manifest = Path(folder) / "manifest.json"
            output = Path(folder) / "result.json"
            manifest.write_text(json.dumps(self.manifest), encoding="utf-8")
            args = ["release_smoke", "--manifest", str(manifest), "--frontend", self.frontend,
                    "--api", self.api, "--source", self.source, "--output", str(output)]
            with redirect_stdout(io.StringIO()), patch("sys.argv", args), patch("ops.release_smoke.verify_release", return_value={
                    "public_asset_count": 7, "page_count": 5, "anonymous_denial_count": 3, "passed": True}):
                self.assertEqual(main(), 0)
                original = output.read_bytes()
                self.assertEqual(main(), 1)
                self.assertEqual(output.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
