"""Owner-only backup/contact preferences; operational activation is separate."""
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID

from fastapi import Depends, Header
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import get_db
from transaction_safety import commit_once, find_saved_order, lock_save_reference, reject_unsaved_change, request_fingerprint

def read_alert_settings(db, *, lock=False):
    if lock:
        lock_save_reference(db, "qlms:alert-settings")
    saved = db.query(models.AlertSettings).populate_existing().filter_by(id=1).first()
    return saved or models.AlertSettings(id=1, owner_email=None, backup_minute=1320, revision=0)


def get_alert_settings(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_owner)):
    return read_alert_settings(db)


def get_alert_history(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_owner)):
    return db.query(models.AlertSettingsChange).order_by(models.AlertSettingsChange.id.desc()).limit(50).all()


def update_alert_settings(change: schemas.AlertSettingsUpdate, db: Session = Depends(get_db),
                          current_user: models.User = Depends(auth.require_owner), *,
                          idempotency_key: Annotated[UUID, Header()]):
    fingerprint = request_fingerprint("update_alert_settings", change)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.AlertSettingsChange, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    settings = read_alert_settings(db, lock=True)
    if settings.revision != change.expected_revision:
        raise reject_unsaved_change("QLMS-STALE-RECORD", "Alert preferences changed on another screen")
    hour, minute = map(int, change.backup_time.split(":"))
    before_email, before_minute = settings.owner_email, settings.backup_minute
    settings.owner_email = change.owner_email
    settings.backup_minute = hour * 60 + minute
    settings.revision += 1
    settings.updated_at = datetime.now(timezone.utc)
    db.add(settings)
    db.flush()
    db.add(models.AlertSettingsChange(settings_id=settings.id, before_email=before_email,
               after_email=settings.owner_email, before_backup_minute=before_minute,
               after_backup_minute=settings.backup_minute, revision=settings.revision,
               request_key=str(idempotency_key), request_hash=fingerprint,
               confirmed_by_id=current_user.id, confirmed_by_username=current_user.username))
    saved = commit_once(db, models.AlertSettingsChange, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(settings)
    return settings
