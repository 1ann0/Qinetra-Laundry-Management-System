"""Recognise a repeated save without accepting different details under its key."""
import hashlib
import json

from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy import text

import models


def reject_unsaved_change(code, message):
    """Use only after replay lookup, when this request has not committed."""
    return HTTPException(409, detail={
        "code": code, "message": message, "save_state": "not_saved",
    })


def lock_save_reference(db, key):
    # Wait for an in-flight copy before checking dates, prices or its saved result.
    # Otherwise a retry could fail validation while the first copy is still saving.
    if db.bind.dialect.name == "postgresql":
        lock_id = int.from_bytes(hashlib.sha256(str(key).encode()).digest()[:8], "big", signed=True)
        db.execute(text("SELECT pg_advisory_xact_lock(:lock_id)"), {"lock_id": lock_id})


def request_fingerprint(operation, payload):
    content = json.dumps(
        {"operation": operation, "body": payload.model_dump(mode="json")},
        sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def find_saved_order(db, record_type, key, fingerprint, user_id):
    saved = db.query(record_type).filter(record_type.request_key == str(key)).first()
    if saved is None:
        return None
    actor_id = saved.created_by_id if record_type is models.Order else saved.confirmed_by_id
    if actor_id != user_id or saved.request_hash != fingerprint:
        raise HTTPException(409, detail={
            "code": "QLMS-SAVE-CONFLICT",
            "message": "This save reference was already used for different details",
            "save_state": "unknown",
        })
    # Return the original order with its current balance and status.
    if record_type is models.Order:
        return saved
    if record_type is models.CustomerCorrection:
        return saved.customer
    if record_type is models.DiscountPolicyChange:
        return saved.policy
    return saved.order


def commit_once(db, record_type, key, fingerprint, user_id):
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # A simultaneous copy may have completed while this request was waiting.
        saved = find_saved_order(db, record_type, key, fingerprint, user_id)
        if saved is not None:
            return saved
        raise
    return None
