"""Private API responses and a bounded login form before credential parsing."""
import json
import logging

LOGIN_BODY_LIMIT = 8192


def private_headers(https=False):
    headers = {
        "Cache-Control": "no-store, private, max-age=0",
        "Pragma": "no-cache",
        "X-Content-Type-Options": "nosniff",
        "X-Frame-Options": "DENY",
        "Referrer-Policy": "no-referrer",
        "Permissions-Policy": "camera=(), microphone=(), geolocation=()",
    }
    if https:
        headers["Strict-Transport-Security"] = "max-age=31536000"
    return headers


class ResponseSecurityMiddleware:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            return await self.app(scope, receive, send)
        response_started = False

        async def secure_send(message):
            nonlocal response_started
            if message["type"] == "http.response.start":
                response_started = True
                additions = {key.lower().encode(): value.encode() for key, value in private_headers(scope["scheme"] == "https").items()}
                existing = [(key, value) for key, value in message.get("headers", []) if key.lower() not in additions]
                message = {**message, "headers": existing + list(additions.items())}
            await send(message)

        async def protected_call(inner_receive):
            try:
                await self.app(scope, inner_receive, secure_send)
            except Exception as error:
                # ServerErrorMiddleware rethrows errors after handling them; catch here
                # so Uvicorn cannot log SQL parameters or customer content in a traceback.
                logging.getLogger("qlms").error("Request failed: method=%s path=%s type=%s", scope["method"], scope["path"], type(error).__name__)
                if response_started:
                    raise RuntimeError("QLMS response interrupted") from None
                await secure_send({"type": "http.response.start", "status": 500, "headers": [(b"content-type", b"application/json")]})
                await send({"type": "http.response.body", "body": b'{"detail":"QLMS could not complete this request"}'})

        if scope["path"] == "/auth/login" and scope["method"] == "POST":
            headers = dict(scope.get("headers", []))
            size = headers.get(b"content-length", b"0")
            oversized = size.isdigit() and int(size) > LOGIN_BODY_LIMIT
            body = bytearray()
            while not oversized:
                message = await receive()
                if message["type"] == "http.disconnect":
                    return
                body.extend(message.get("body", b""))
                oversized = len(body) > LOGIN_BODY_LIMIT
                if not message.get("more_body", False):
                    break
            if oversized:
                payload = json.dumps({"detail": "Sign-in request is too large"}).encode()
                await secure_send({"type": "http.response.start", "status": 413, "headers": [(b"content-type", b"application/json")]})
                return await send({"type": "http.response.body", "body": payload})

            sent = False

            async def limited_receive():
                nonlocal sent
                if not sent:
                    sent = True
                    return {"type": "http.request", "body": bytes(body), "more_body": False}
                return await receive()

            return await protected_call(limited_receive)
        await protected_call(receive)


def safe_csv_text(value):
    # CSV quoting alone cannot stop a spreadsheet from evaluating a formula.
    if value and (value[0] in "\t\r\n" or value.lstrip().startswith(("=", "+", "-", "@", "＝", "＋", "－", "＠"))):
        return "'" + value
    return value
