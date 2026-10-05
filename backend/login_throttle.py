"""Database-backed fixed windows; no paid cache or per-process bypass."""
import hashlib
import hmac
import math
import time

from fastapi import HTTPException
from sqlalchemy import case, or_
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

import auth
from models import LoginAttemptBucket

WINDOW_SECONDS = 300
IP_LIMIT = 50
ACCOUNT_IP_LIMIT = 10
ACCOUNT_LIMIT = 30


def consume_login_attempt(db, peer_ip, username, now=None):
    now = time.time() if now is None else now
    window = int(now // WINDOW_SECONDS) * WINDOW_SECONDS
    insert = pg_insert if db.get_bind().dialect.name == "postgresql" else sqlite_insert
    keys = [("ip", peer_ip, IP_LIMIT), ("account", username.casefold(), ACCOUNT_LIMIT),
            ("account_ip", f"{peer_ip}\0{username.casefold()}", ACCOUNT_IP_LIMIT)]
    blocked = False
    for kind, identifier, limit in keys:
        key = hmac.new(auth.SECRET_KEY.encode(), f"login:{kind}:{identifier}".encode(), hashlib.sha256).hexdigest()
        statement = insert(LoginAttemptBucket).values(bucket_key=key, window_start=window, attempts=1)
        statement = statement.on_conflict_do_update(
            index_elements=[LoginAttemptBucket.bucket_key],
            set_={"window_start": window, "attempts": case((LoginAttemptBucket.window_start != window, 1), else_=LoginAttemptBucket.attempts + 1)},
            where=or_(LoginAttemptBucket.window_start != window, LoginAttemptBucket.attempts < limit),
        ).returning(LoginAttemptBucket.attempts)
        if db.execute(statement).scalar() is None:
            blocked = True
            break
    # Bound storage lifetime. These records are operational metadata, not audit history.
    db.query(LoginAttemptBucket).filter(LoginAttemptBucket.window_start < window - 86400).delete(synchronize_session=False)
    db.commit()
    if blocked:
        raise HTTPException(status_code=429, detail="Too many sign-in attempts. Try again shortly.",
                            headers={"Retry-After": str(max(1, math.ceil(window + WINDOW_SECONDS - now)))})
