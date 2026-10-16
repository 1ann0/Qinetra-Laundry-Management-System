"""Owner-signed snapshots and attributed cash movements preserve every earlier version."""
from datetime import date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.exc import DBAPIError, IntegrityError
from sqlalchemy.orm import Session

import auth
import models
from database import get_db, start_consistent_transaction
from daily_control import daily_activity, closing_figures, snapshot_values, signed_details, close_history
from expense_routes import ExpenseInput, ExpenseCorrectionInput, ExpenseChangeOut
from transaction_safety import commit_once, find_saved_order, lock_save_reference, reject_unsaved_change, request_fingerprint

router = APIRouter(tags=['Owner daily closing'])
Money = Annotated[Decimal, Field(ge=0, le=9999999999, decimal_places=2, allow_inf_nan=False)]


class TillInput(BaseModel):
    model_config = {'extra': 'forbid'}
    movement_date: date
    kind: Literal['addition', 'withdrawal']
    amount: Money = Field(gt=0)
    reference: str = Field(default='', max_length=100)
    note: str = Field(default='', max_length=1000)

    @field_validator('movement_date')
    @classmethod
    def valid_date(cls, value):
        return ExpenseInput.paid_not_future(value)

    @field_validator('amount', mode='before')
    @classmethod
    def valid_amount(cls, value):
        return ExpenseInput.amount_not_boolean(value)

    @field_validator('reference', 'note')
    @classmethod
    def clean_text(cls, value, info):
        return ExpenseInput.clean_text(value, info)


class TillCorrection(TillInput):
    expected_revision: int = Field(ge=0, strict=True)
    reason: str = Field(min_length=1, max_length=200)
    is_voided: bool = Field(strict=True)

    @field_validator('reason')
    @classmethod
    def valid_reason(cls, value):
        return ExpenseCorrectionInput.correction_reason(value)


class TillOut(TillInput):
    model_config = {'from_attributes': True}
    id: int
    is_voided: bool
    revision: int
    confirmed_by_username: str
    created_at: datetime
    original_details: dict | None
    corrections: list[ExpenseChangeOut]


class CloseInput(BaseModel):
    model_config = {'extra': 'forbid'}
    business_date: date
    opening_cash: Money
    counted_cash: Money
    statement_received: Money
    statement_returned: Money
    expected_revision: int = Field(ge=0, strict=True)
    expected_fingerprint: str = Field(pattern=r'^[0-9a-f]{64}$')
    reason: str = Field(default='', max_length=200)

    @field_validator('business_date')
    @classmethod
    def valid_date(cls, value):
        return ExpenseInput.paid_not_future(value)

    @field_validator('opening_cash', 'counted_cash', 'statement_received', 'statement_returned', mode='before')
    @classmethod
    def valid_amount(cls, value):
        return ExpenseInput.amount_not_boolean(value)

    @field_validator('reason')
    @classmethod
    def valid_reason(cls, value):
        return ExpenseCorrectionInput.correction_reason(value) if value.strip() else ''


def consistent_owner(db, owner, *, read_only=False):
    # Authentication already read from this session; start the ledger snapshot before its first query.
    identity, version = owner.id, owner.token_version
    start_consistent_transaction(db, read_only=read_only)
    current = db.get(models.User, identity, populate_existing=True)
    if current is None or not current.is_active or current.token_version != version:
        raise HTTPException(401, 'Not authenticated')
    return auth.require_owner(current)


@router.get('/daily-close')
def read_close(business_date: Annotated[date, Query(alias='date')], db: Session = Depends(get_db),
               owner: models.User = Depends(auth.require_owner)):
    try:
        ExpenseInput.paid_not_future(business_date)
    except ValueError:
        raise HTTPException(422, 'Choose today or an earlier closing date') from None
    consistent_owner(db, owner, read_only=True)
    activity = daily_activity(db, business_date)
    history = close_history(db, business_date)
    return {'date': business_date, 'activity': snapshot_values(activity),
        'latest': signed_details(history[0]) if history else None,
        'history': [signed_details(row) for row in history],
        'needs_review': bool(history and history[0].source_fingerprint != activity['source_fingerprint'])}


@router.post('/daily-close')
def confirm_close(body: CloseInput, db: Session = Depends(get_db), owner: models.User = Depends(auth.require_owner), *,
                  idempotency_key: Annotated[UUID, Header()]):
    owner = consistent_owner(db, owner)
    fingerprint = request_fingerprint('confirm_daily_close', body)
    try:
        lock_save_reference(db, idempotency_key)
        saved = find_saved_order(db, models.DailyClose, idempotency_key, fingerprint, owner.id)
        if saved is not None:
            return signed_details(saved)
        lock_save_reference(db, 'daily-close:' + body.business_date.isoformat())
        history = close_history(db, body.business_date)
        revision = history[0].revision if history else 0
        activity = daily_activity(db, body.business_date)
        if revision != body.expected_revision or activity['source_fingerprint'] != body.expected_fingerprint:
            raise reject_unsaved_change('QLMS-STALE-RECORD', 'The daily figures changed. Reload and check them before confirming')
        if activity['unconfirmed_cash_expenses']:
            raise reject_unsaved_change('QLMS-STALE-RECORD', 'Confirm who paid each unconfirmed cash expense before closing')
        counts = {key: getattr(body, key) for key in ('opening_cash', 'counted_cash', 'statement_received', 'statement_returned')}
        figures = closing_figures(activity, **counts)
        if not body.reason and (revision or any(figures[key] != 0 for key in
                ('cash_difference', 'mpesa_received_difference', 'mpesa_returned_difference'))):
            raise HTTPException(422, 'Explain the difference or why this day is being confirmed again')
        snapshot = snapshot_values({'activity': activity, 'counts': counts, 'figures': figures})
        row = models.DailyClose(business_date=body.business_date, revision=revision + 1,
            source_fingerprint=activity['source_fingerprint'], snapshot=snapshot, reason=body.reason,
            request_key=str(idempotency_key), request_hash=fingerprint,
            confirmed_by_id=owner.id, confirmed_by_username=owner.username)
        db.add(row)
        saved = commit_once(db, models.DailyClose, idempotency_key, fingerprint, owner.id)
        return signed_details(saved or row)
    except DBAPIError as error:
        db.rollback()
        if isinstance(error, IntegrityError) or getattr(error.orig, 'pgcode', None) in {'40001', '40P01'}:
            raise reject_unsaved_change('QLMS-STALE-RECORD', 'Another save changed this day. Reload and review the saved close') from None
        raise


def movement_details(row):
    return {**TillInput.model_validate(row, from_attributes=True).model_dump(mode='json'), 'is_voided': row.is_voided}


def read_movement(db, movement_id, *, lock=False):
    query = db.query(models.TillMovement).filter_by(id=movement_id).populate_existing()
    row = (query.with_for_update() if lock else query).first()
    if row is None:
        raise HTTPException(404, 'Cash movement not found')
    return row


@router.get('/till-movements/{movement_id}', response_model=TillOut)
def get_movement(movement_id: int, db: Session = Depends(get_db), owner: models.User = Depends(auth.require_owner)):
    return read_movement(db, movement_id)


@router.post('/till-movements', response_model=TillOut)
def create_movement(body: TillInput, db: Session = Depends(get_db), owner: models.User = Depends(auth.require_owner), *,
                    idempotency_key: Annotated[UUID, Header()]):
    fingerprint = request_fingerprint('create_till_movement', body)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.TillMovement, idempotency_key, fingerprint, owner.id)
    if saved is not None:
        return saved
    row = models.TillMovement(**body.model_dump(), request_key=str(idempotency_key), request_hash=fingerprint,
        confirmed_by_id=owner.id, confirmed_by_username=owner.username)
    db.add(row)
    db.flush()
    db.add(models.TillMovementChange(movement_id=row.id, before_details=None,
        after_details=movement_details(row), reason='Cash movement recorded', revision=0,
        request_key=str(idempotency_key), request_hash=fingerprint,
        confirmed_by_id=owner.id, confirmed_by_username=owner.username))
    saved = commit_once(db, models.TillMovement, idempotency_key, fingerprint, owner.id)
    db.refresh(row)
    return saved or row


@router.post('/till-movements/{movement_id}/corrections', response_model=TillOut)
def correct_movement(movement_id: int, body: TillCorrection, db: Session = Depends(get_db),
                     owner: models.User = Depends(auth.require_owner), *, idempotency_key: Annotated[UUID, Header()]):
    fingerprint = request_fingerprint(f'correct_till_movement:{movement_id}', body)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.TillMovementChange, idempotency_key, fingerprint, owner.id)
    if saved is not None:
        return saved
    row = read_movement(db, movement_id, lock=True)
    if row.revision != body.expected_revision:
        raise reject_unsaved_change('QLMS-STALE-RECORD', 'This cash movement changed on another screen')
    before = movement_details(row)
    for key in TillInput.model_fields:
        setattr(row, key, getattr(body, key))
    row.is_voided = body.is_voided
    row.revision += 1
    db.add(models.TillMovementChange(movement_id=row.id, before_details=before,
        after_details=movement_details(row), reason=body.reason, revision=row.revision,
        request_key=str(idempotency_key), request_hash=fingerprint,
        confirmed_by_id=owner.id, confirmed_by_username=owner.username))
    saved = commit_once(db, models.TillMovementChange, idempotency_key, fingerprint, owner.id)
    db.refresh(row)
    return saved or row
