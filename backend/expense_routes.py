"""Owner costs are replayable; reversals preserve the original immutable event."""
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

import auth
import models
from database import get_db
from transaction_safety import commit_once, find_saved_order, lock_save_reference, reject_unsaved_change, request_fingerprint

EXPENSE_CATEGORIES = {"supplies", "utilities", "rent", "wages", "outsourcing", "other"}
EXPENSE_FUNDING_SOURCES = {"shop": "Shop money", "owner": "Owner's own money"}
router = APIRouter(prefix="/expenses", tags=["Owner expenses"])


class ExpenseInput(BaseModel):
    model_config = {"extra":"forbid"}
    paid_date: date
    category: Literal["supplies", "utilities", "rent", "wages", "outsourcing", "other"]
    amount: Decimal = Field(gt=0, le=9999999999, decimal_places=2, allow_inf_nan=False)
    payment_method: Literal["cash", "mpesa"]
    # Missing funding must keep pre-upgrade pending saves' exact fingerprints.
    funding_source: Literal["shop", "owner"] | None = Field(default=None, exclude_if=lambda value: value is None)
    reference: str = Field(default="", max_length=100)
    note: str = Field(default="", max_length=1000)

    @field_validator("paid_date")
    @classmethod
    def paid_not_future(cls, value):
        if value > datetime.now(timezone(timedelta(hours=3))).date():
            raise ValueError("Choose a paid date on or before today in Nairobi")
        return value

    @field_validator("amount", mode="before")
    @classmethod
    def amount_not_boolean(cls, value):
        if isinstance(value, bool):
            raise ValueError("Enter an amount in KES")
        return value

    @field_validator("reference", "note")
    @classmethod
    def clean_text(cls, value, info):
        allowed = "\n" if info.field_name == "note" else ""
        if any((ord(char) < 32 and char not in allowed) or ord(char) == 127 for char in value):
            raise ValueError("Remove control characters")
        return value.strip()


class ExpenseCorrectionInput(ExpenseInput):
    expected_revision: int = Field(ge=0, strict=True)
    reason: str = Field(min_length=1, max_length=200)
    is_voided: bool = Field(strict=True)

    @field_validator("reason")
    @classmethod
    def correction_reason(cls, value):
        if not value.strip() or any(ord(char)<32 or ord(char)==127 for char in value):
            raise ValueError("Explain this correction")
        return value.strip()


class ExpenseChangeOut(BaseModel):
    model_config = {"from_attributes":True}
    id: int
    before_details: dict | None
    after_details: dict
    reason: str
    revision: int
    confirmed_by_username: str
    created_at: datetime


class ExpenseOut(ExpenseInput):
    model_config = {"from_attributes":True}
    id: int
    is_voided: bool
    revision: int
    confirmed_by_username: str
    created_at: datetime
    original_details: dict | None
    corrections: list[ExpenseChangeOut]


def details(expense):
    values = {field:getattr(expense,field) for field in ExpenseInput.model_fields}
    return {**ExpenseInput(**values).model_dump(mode="json"), "is_voided":expense.is_voided}


def get_expense(db, expense_id, *, lock=False):
    query = db.query(models.Expense).filter_by(id=expense_id)
    if lock:
        query = query.populate_existing().with_for_update()
    expense = query.first()
    if expense is None:
        raise HTTPException(404,"Expense not found")
    return expense


@router.get("/{expense_id}", response_model=ExpenseOut)
def read_expense(expense_id: int, db: Session = Depends(get_db), owner: models.User = Depends(auth.require_owner)):
    return get_expense(db, expense_id)


@router.post("", response_model=ExpenseOut)
def create_expense(body: ExpenseInput, db: Session = Depends(get_db), owner: models.User = Depends(auth.require_owner), *,
                   idempotency_key: Annotated[UUID, Header()]):
    fingerprint = request_fingerprint("create_expense",body)
    lock_save_reference(db,idempotency_key)
    saved = find_saved_order(db,models.Expense,idempotency_key,fingerprint,owner.id)
    if saved is not None:
        return saved
    expense = models.Expense(**body.model_dump(),request_key=str(idempotency_key),request_hash=fingerprint,
        confirmed_by_id=owner.id,confirmed_by_username=owner.username)
    db.add(expense)
    db.flush()
    db.add(models.ExpenseChange(expense_id=expense.id,before_details=None,after_details=details(expense),
        reason="Expense recorded",revision=0,request_key=str(idempotency_key),request_hash=fingerprint,
        confirmed_by_id=owner.id,confirmed_by_username=owner.username))
    saved = commit_once(db,models.Expense,idempotency_key,fingerprint,owner.id)
    if saved is not None:
        return saved
    db.refresh(expense)
    return expense


@router.post("/{expense_id}/corrections", response_model=ExpenseOut)
def correct_expense(expense_id: int, body: ExpenseCorrectionInput, db: Session = Depends(get_db),
                    owner: models.User = Depends(auth.require_owner), *, idempotency_key: Annotated[UUID, Header()]):
    fingerprint = request_fingerprint(f"correct_expense:{expense_id}",body)
    lock_save_reference(db,idempotency_key)
    saved = find_saved_order(db,models.ExpenseChange,idempotency_key,fingerprint,owner.id)
    if saved is not None:
        return saved
    expense = get_expense(db,expense_id,lock=True)
    if expense.revision != body.expected_revision:
        raise reject_unsaved_change("QLMS-STALE-RECORD","This expense changed on another screen")
    before = details(expense)
    for field in ExpenseInput.model_fields:
        if field == "funding_source" and body.funding_source is None:
            continue
        setattr(expense,field,getattr(body,field))
    expense.is_voided = body.is_voided
    expense.revision += 1
    db.add(models.ExpenseChange(expense_id=expense.id,before_details=before,after_details=details(expense),
        reason=body.reason,revision=expense.revision,request_key=str(idempotency_key),request_hash=fingerprint,
        confirmed_by_id=owner.id,confirmed_by_username=owner.username))
    saved = commit_once(db,models.ExpenseChange,idempotency_key,fingerprint,owner.id)
    if saved is not None:
        return saved
    db.refresh(expense)
    return expense
