"""Independent monitor receives empty status pings, never backup data or errors."""
import io
import unittest
from unittest.mock import patch

from ops.backup_monitor import NoRedirects, main, signal


URL = "https://hc-ping.com/00000000-0000-4000-8000-000000000001"


class MonitorReply(io.BytesIO):
    status = 200


class MonitorTests(unittest.TestCase):
    def test_status_only_post_to_fixed_host_with_no_body_or_credentials(self):
        class Fixture:
            def open(inner, request, timeout):
                self.assertEqual(request.method, "POST")
                self.assertEqual(request.data, b"")
                self.assertEqual(timeout, 15)
                self.assertEqual(request.full_url, expected)
                self.assertNotIn("Authorization", request.headers)
                return MonitorReply(b"OK")
        for status, suffix in [("start", "/start"), ("success", ""), ("fail", "/fail")]:
            expected = URL + suffix
            signal(URL, status, opener=Fixture())

    def test_invalid_urls_signals_and_redirects_are_rejected(self):
        for url in [None, URL.replace("https", "http"), URL + "?secret=data", URL + "/start",
                    URL.replace("hc-ping.com", "untrusted.invalid"), URL.replace("https://", "https://user:password@")]:
            with self.subTest(url=url), self.assertRaises(ValueError):
                signal(url, "success")
        with self.assertRaises(ValueError):
            signal(URL, "log")
        self.assertIsNone(NoRedirects().redirect_request(None, None, 302, "", {}, "https://untrusted.invalid"))

    def test_provider_200_not_found_or_rate_limit_cannot_claim_success(self):
        class Fixture:
            def open(inner, request, timeout):
                return MonitorReply(body)
        for body in [b"OK (not found)", b"OK (rate limited)", b"customer details", b"OK" + b" " * 200]:
            with self.subTest(body=body[:25]), self.assertRaises(RuntimeError):
                signal(URL, "success", opener=Fixture())

    def test_private_provider_errors_are_not_printed(self):
        with patch("sys.argv", ["monitor", "fail"]), patch("ops.backup_monitor.signal", side_effect=RuntimeError("secret-url private-body")), \
                patch("sys.stderr", io.StringIO()) as output:
            self.assertEqual(main(), 1)
            self.assertNotIn("secret-url", output.getvalue())
