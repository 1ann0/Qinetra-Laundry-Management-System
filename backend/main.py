# main.py
# Entry point of the FastAPI backend. All API routes live or are wired up here.

from fastapi import FastAPI, Depends, HTTPException, Header
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from sqlalchemy.exc import IntegrityError
from typing import Optional, Annotated
from uuid import UUID
from datetime import date, datetime, timezone, timedelta
from decimal import Decimal
from fastapi.responses import StreamingResponse
import csv
import io
import os
import re
from database import get_db
import models
import schemas
import logic
import auth
from customer_phone import normalize_kenyan_phone, phone_search_digits
from discount_policy import read_discount_policy, enforce_employee_discount
from transaction_safety import (
    request_fingerprint, find_saved_order, commit_once,
    lock_save_reference, reject_unsaved_change,
)

# Kenya uses UTC+3 throughout the year, with no daylight-saving changes.
NAIROBI_TIMEZONE = timezone(timedelta(hours=3))

app = FastAPI()

# Allow only the configured frontend addresses to call the API from a browser.
local_origins = "http://localhost:3000,http://127.0.0.1:3000"
allowed_origins = [
    origin.strip()
    for origin in os.getenv("ALLOWED_ORIGINS", local_origins).split(",")
    if origin.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Staff may read their ceiling; only an owner can change or inspect its history.
@app.get("/settings/discount-policy", response_model=schemas.DiscountPolicyOut)
def get_discount_policy(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    return read_discount_policy(db)


@app.get("/settings/discount-policy/history", response_model=list[schemas.DiscountPolicyChangeOut])
def get_discount_policy_history(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    return db.query(models.DiscountPolicyChange).order_by(models.DiscountPolicyChange.id.desc()).limit(50).all()


@app.post("/settings/discount-policy", response_model=schemas.DiscountPolicyOut)
def update_discount_policy(
    change: schemas.DiscountPolicyUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint("update_discount_policy", change)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.DiscountPolicyChange, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    policy = read_discount_policy(db, lock=True)
    if policy.revision != change.expected_revision:
        raise reject_unsaved_change("QLMS-STALE-RECORD", "The discount policy changed on another screen")

    before_percent = policy.employee_max_discount_percent
    policy.employee_max_discount_percent = change.employee_max_discount_percent
    policy.revision += 1
    policy.updated_at = datetime.now(timezone.utc)
    db.add(policy)
    db.flush()
    db.add(models.DiscountPolicyChange(
        policy_id=policy.id, before_percent=before_percent,
        after_percent=policy.employee_max_discount_percent, revision=policy.revision,
        request_key=str(idempotency_key), request_hash=fingerprint,
        confirmed_by_id=current_user.id, confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.DiscountPolicyChange, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(policy)
    return policy


def get_nairobi_today() -> date:
    return datetime.now(NAIROBI_TIMEZONE).date()


# Turn a service name into a short internal code used by the API and database.
def make_service_code(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# Use the employee-confirmed promise, or calculate one from the slowest service.
def get_promised_ready_at(
    requested_time: Optional[datetime],
    turnaround_minutes: int,
    peak_delay_minutes: int,
) -> datetime:
    now = datetime.now(timezone.utc)

    if requested_time is None:
        return now + timedelta(
            minutes=turnaround_minutes + peak_delay_minutes,
        )

    if requested_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Promised completion time must include a timezone",
        )

    promised_time = requested_time.astimezone(timezone.utc)
    if promised_time <= now:
        raise HTTPException(
            status_code=400,
            detail="Promised completion time must be in the future",
        )

    return promised_time


def get_expected_return_at(requested_time: datetime) -> datetime:
    if requested_time.tzinfo is None:
        raise HTTPException(
            status_code=400,
            detail="Expected return time must include a timezone",
        )
    expected_time = requested_time.astimezone(timezone.utc)
    if expected_time <= datetime.now(timezone.utc):
        raise HTTPException(
            status_code=400,
            detail="Expected return time must be in the future",
        )
    return expected_time


# Convert inclusive Nairobi calendar dates into the UTC boundaries stored by PostgreSQL.
def get_financial_date_boundaries(start_date: date, end_date: date):
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )

    local_start = datetime.combine(
        start_date,
        datetime.min.time(),
        tzinfo=NAIROBI_TIMEZONE,
    )
    local_end = datetime.combine(
        end_date + timedelta(days=1),
        datetime.min.time(),
        tzinfo=NAIROBI_TIMEZONE,
    )
    return (
        local_start.astimezone(timezone.utc),
        local_end.astimezone(timezone.utc),
    )


# SQLite tests can return naive timestamps even though PostgreSQL keeps UTC offsets.
def get_nairobi_payment_date(payment_time: datetime) -> date:
    if payment_time.tzinfo is None:
        payment_time = payment_time.replace(tzinfo=timezone.utc)
    return payment_time.astimezone(NAIROBI_TIMEZONE).date()


# Validate the garment linked to a fixed Dry Cleaning service.
def get_service_item_type(
    db: Session,
    item_type_id: Optional[int],
    allowed_inactive_id: Optional[int] = None,
):
    if item_type_id is None:
        return None

    item_type = db.query(models.ClothingItemType).filter(
        models.ClothingItemType.id == item_type_id
    ).first()
    if not item_type:
        raise HTTPException(status_code=400, detail="The linked garment was not found")
    if not item_type.is_active and item_type_id != allowed_inactive_id:
        raise HTTPException(
            status_code=400,
            detail=f"{item_type.name} is inactive and cannot be linked",
        )
    if item_type.item_group not in {"dry_cleaning", "both"}:
        raise HTTPException(
            status_code=400,
            detail=f"{item_type.name} is not in the Dry Cleaning garment list",
        )
    return item_type


# Stop a fixed-price garment service from being saved under a different item name.
def check_fixed_service_items(
    item_inputs: list[schemas.OrderItemCreate],
    fixed_item_type_id: Optional[int],
):
    if fixed_item_type_id and any(
        item.item_type_id != fixed_item_type_id for item in item_inputs
    ):
        raise HTTPException(
            status_code=400,
            detail="The clothing details must match the selected Dry Cleaning garment",
        )


# Validates and prepares clothing rows before an order or later edit is saved.
# Inactive item types are only allowed when they were already on that order.
def prepare_order_items(
    db: Session,
    item_inputs: list[schemas.OrderItemCreate],
    recording_mode: str,
    service_quantity: float,
    allowed_inactive_ids: Optional[set[int]] = None,
):
    allowed_inactive_ids = allowed_inactive_ids or set()

    if recording_mode == "none":
        if item_inputs:
            raise HTTPException(
                status_code=400,
                detail="This service does not require a clothing list",
            )
        return [], "not_required"

    item_type_ids = [item.item_type_id for item in item_inputs]
    if recording_mode == "tally" and len(item_type_ids) != len(set(item_type_ids)):
        raise HTTPException(
            status_code=400,
            detail="Each clothing type should appear once in a quick tally",
        )

    if recording_mode == "tally":
        for item in item_inputs:
            if any([
                item.description,
                item.is_damaged is not None,
                item.damage_note,
                item.stain_note,
            ]):
                raise HTTPException(
                    status_code=400,
                    detail="Add damage and stain details to the affected piece, not the full tally",
                )
            if len(item.exceptions) > item.quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Condition notes cannot exceed the number of counted items",
                )

    if recording_mode == "detailed":
        if any(item.exceptions for item in item_inputs):
            raise HTTPException(
                status_code=400,
                detail="Detailed garments already have their own condition fields",
            )
        if any(item.quantity != 1 for item in item_inputs):
            raise HTTPException(
                status_code=400,
                detail="Detailed garments must be recorded one at a time",
            )
        if any(item.is_damaged is None for item in item_inputs):
            raise HTTPException(
                status_code=400,
                detail="Confirm whether every detailed garment is already damaged",
            )
        if any(not item.description for item in item_inputs):
            raise HTTPException(
                status_code=400,
                detail="Describe every detailed garment so it can be identified",
            )

    if not item_type_ids:
        return [], "pending"

    item_types = db.query(models.ClothingItemType).filter(
        models.ClothingItemType.id.in_(set(item_type_ids))
    ).all()
    item_types_by_id = {item_type.id: item_type for item_type in item_types}

    for item_type_id in set(item_type_ids):
        item_type = item_types_by_id.get(item_type_id)
        if not item_type:
            raise HTTPException(status_code=400, detail="A clothing item was not found")
        if not item_type.is_active and item_type_id not in allowed_inactive_ids:
            raise HTTPException(
                status_code=400,
                detail=f"{item_type.name} is inactive and cannot be added",
            )
        expected_group = (
            "laundry" if recording_mode == "tally" else "dry_cleaning"
        )
        if (
            item_type.item_group not in {expected_group, "both"}
            and item_type_id not in allowed_inactive_ids
        ):
            list_name = (
                "Laundry tally" if expected_group == "laundry" else "Dry Cleaning"
            )
            raise HTTPException(
                status_code=400,
                detail=f"{item_type.name} is not in the {list_name} list",
            )

    saved_items = []
    for item in item_inputs:
        saved_items.append(models.OrderItem(
            item_type_id=item.item_type_id,
            item_name=item_types_by_id[item.item_type_id].name,
            quantity=item.quantity,
            description=item.description,
            is_damaged=item.is_damaged,
            damage_note=item.damage_note,
            stain_note=item.stain_note,
            exceptions=[
                models.OrderItemException(
                    description=exception.description,
                    is_damaged=exception.is_damaged,
                    damage_note=exception.damage_note,
                    stain_note=exception.stain_note,
                )
                for exception in item.exceptions
            ],
        ))
    item_status = logic.get_item_check_status(
        recording_mode,
        service_quantity,
        [item.quantity for item in item_inputs],
    )
    return saved_items, item_status


# Store a plain-data snapshot so later catalogue changes cannot rewrite history.
def make_item_snapshot(items: list[models.OrderItem]):
    return [
        {
            "item_type_id": item.item_type_id,
            "garment_reference": item.garment_reference,
            "item_name": item.item_name,
            "quantity": item.quantity,
            "description": item.description,
            "is_damaged": item.is_damaged,
            "damage_note": item.damage_note,
            "stain_note": item.stain_note,
            "exceptions": [
                {
                    "description": exception.description,
                    "is_damaged": exception.is_damaged,
                    "damage_note": exception.damage_note,
                    "stain_note": exception.stain_note,
                }
                for exception in item.exceptions
            ],
        }
        for item in items
    ]


def make_item_history(
    items: list[models.OrderItem],
    item_status: str,
    revision: int,
    current_user: models.User,
    change_reason: Optional[str] = None,
):
    return models.OrderItemCheckHistory(
        revision=revision,
        check_status=item_status,
        item_snapshot=make_item_snapshot(items),
        changed_by_id=current_user.id,
        changed_by_username=current_user.username,
        change_reason=change_reason,
    )


# References identify physical garments independently from the quantity charged.
def assign_garment_references(order: models.Order, items: list[models.OrderItem]):
    for item in items:
        if item.garment_reference:
            continue
        next_number = order.next_garment_number or 1
        item.garment_reference = (
            f"{order.ticket_number}-G{next_number:02d}"
        )
        order.next_garment_number = next_number + 1


# Keep saved garment identities during corrections while replacing their details.
def merge_detailed_item_replacement(
    order: models.Order,
    service_line: models.OrderServiceLine,
    item_inputs: list[schemas.OrderItemCreate],
    prepared_items: list[models.OrderItem],
):
    existing_items = {item.id: item for item in service_line.items}
    submitted_ids = [
        item.existing_item_id
        for item in item_inputs
        if item.existing_item_id is not None
    ]
    if len(submitted_ids) != len(set(submitted_ids)):
        raise HTTPException(400, "Each saved garment can appear only once")
    if any(item_id not in existing_items for item_id in submitted_ids):
        raise HTTPException(400, "A saved garment does not belong to this service")

    replacement_items = []
    for item_input, prepared_item in zip(item_inputs, prepared_items):
        if item_input.existing_item_id is None:
            assign_garment_references(order, [prepared_item])
            replacement_items.append(prepared_item)
            continue

        saved_item = existing_items[item_input.existing_item_id]
        saved_item.item_type_id = prepared_item.item_type_id
        saved_item.item_name = prepared_item.item_name
        saved_item.quantity = prepared_item.quantity
        saved_item.description = prepared_item.description
        saved_item.is_damaged = prepared_item.is_damaged
        saved_item.damage_note = prepared_item.damage_note
        saved_item.stain_note = prepared_item.stain_note
        saved_item.exceptions = prepared_item.exceptions
        assign_garment_references(order, [saved_item])
        replacement_items.append(saved_item)

    return replacement_items


# Health check route
@app.get("/")
def read_root():
    return {"status": "QLMS backend is running"}


# Return the same session shape after login or a valid token renewal.
def build_session_response(user: models.User):
    token = auth.create_access_token(
        user_id=user.id,
        role=user.role,
        token_version=user.token_version,
    )
    return {
        "access_token": token,
        "token_type": "bearer",
        "role": user.role,
        "user_id": user.id,
        "username": user.username,
    }


# Logs a user in: checks username/password, returns a signed JWT with their role
@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    username = form_data.username.strip()
    user = db.query(models.User).filter(models.User.username == username).first()

    if (
        not user
        or not auth.verify_password(form_data.password, user.password_hash)
        or not user.is_active
    ):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    return build_session_response(user)


# Renew a still-valid session while the employee is actively using QLMS.
@app.post("/auth/refresh", response_model=schemas.Token)
def refresh_session(
    current_user: models.User = Depends(auth.get_current_user),
):
    return build_session_response(current_user)


# Staff accounts are managed by an active owner. The first owner is still
# created privately with create_owner.py, never through a public route.
@app.get("/users", response_model=list[schemas.UserOut])
def list_users(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    return db.query(models.User).order_by(models.User.id.asc()).all()


@app.post("/users", response_model=schemas.UserOut)
def create_user(
    user: schemas.UserCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = models.User(
        username=user.username,
        password_hash=auth.hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Username already taken")
    db.refresh(new_user)
    return new_user


def get_managed_user(user_id: int, db: Session, lock_accounts: bool = False):
    if lock_accounts:
        # Staff changes are rare, so locking the short account list keeps two
        # owners from concurrently removing each other's final-owner access.
        users = (
            db.query(models.User)
            .order_by(models.User.id.asc())
            .with_for_update()
            .populate_existing()
            .all()
        )
        user = next((account for account in users if account.id == user_id), None)
    else:
        user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


def active_owner_count(db: Session) -> int:
    return db.query(models.User).filter(
        models.User.role == "owner",
        models.User.is_active.is_(True),
    ).count()


def confirm_managing_owner(current_user: models.User):
    if not current_user.is_active or current_user.role != "owner":
        raise HTTPException(status_code=403, detail="Owner access required")


@app.patch("/users/{user_id}/status", response_model=schemas.UserOut)
def update_user_status(
    user_id: int,
    status_update: schemas.UserStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    user = get_managed_user(user_id, db, lock_accounts=True)
    confirm_managing_owner(current_user)
    if user.is_active == status_update.is_active:
        return user

    if user.id == current_user.id and not status_update.is_active:
        raise HTTPException(
            status_code=400,
            detail="You cannot deactivate your own account",
        )

    if (
        user.role == "owner"
        and user.is_active
        and not status_update.is_active
        and active_owner_count(db) <= 1
    ):
        raise HTTPException(
            status_code=400,
            detail="At least one active owner must remain",
        )

    user.is_active = status_update.is_active
    user.token_version += 1
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}/role", response_model=schemas.UserOut)
def update_user_role(
    user_id: int,
    role_update: schemas.UserRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    user = get_managed_user(user_id, db, lock_accounts=True)
    confirm_managing_owner(current_user)
    if user.role == role_update.role:
        return user

    if user.id == current_user.id:
        raise HTTPException(
            status_code=400,
            detail="You cannot change your own role",
        )

    if (
        user.role == "owner"
        and user.is_active
        and role_update.role != "owner"
        and active_owner_count(db) <= 1
    ):
        raise HTTPException(
            status_code=400,
            detail="At least one active owner must remain",
        )

    user.role = role_update.role
    user.token_version += 1
    db.commit()
    db.refresh(user)
    return user


@app.patch("/users/{user_id}/password", response_model=schemas.UserOut)
def reset_user_password(
    user_id: int,
    password_reset: schemas.UserPasswordReset,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    user = get_managed_user(user_id, db, lock_accounts=True)
    confirm_managing_owner(current_user)
    user.password_hash = auth.hash_password(password_reset.password)
    user.token_version += 1
    db.commit()
    db.refresh(user)
    return user


# Creates a new customer
@app.post("/customers", response_model=schemas.CustomerCreateResponse)
def create_customer(
    customer: schemas.CustomerCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    canonical_phone = normalize_kenyan_phone(customer.phone)
    # Serialize phone checks with contact edits so simultaneous saves see each other.
    lock_save_reference(db, f"customer-phone:{canonical_phone}")
    existing = db.query(models.Customer).filter(
        models.Customer.phone_normalized == canonical_phone,
    ).first()
    if existing and not customer.allow_duplicate:
        raise HTTPException(
            status_code=409,
            detail="This phone number is already saved. Check the matching customer before creating another record.",
        )

    new_customer = models.Customer(
        name=customer.name,
        phone=customer.phone,
        phone_normalized=canonical_phone,
    )
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    # If a match was found, attach a warning instead of blocking creation
    warning = None
    if existing:
        warning = "A separate customer was created with a phone number already in use."

    return schemas.CustomerCreateResponse(customer=new_customer, duplicate_warning=warning)


@app.get("/customers/{customer_id}/corrections", response_model=list[schemas.CustomerCorrectionOut])
def list_customer_corrections(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer.corrections


@app.post("/customers/{customer_id}/corrections", response_model=schemas.CustomerOut)
def correct_customer_details(
    customer_id: int,
    correction: schemas.CustomerCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"customer-details:{customer_id}", correction)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.CustomerCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved

    customer = (
        db.query(models.Customer)
        .filter(models.Customer.id == customer_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not customer:
        raise HTTPException(404, "Customer not found")
    saved = find_saved_order(db, models.CustomerCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    if not correction.confirmed:
        raise HTTPException(400, "Confirm the customer's new details before saving")
    if (customer.name, customer.phone) != (correction.expected_name, correction.expected_phone):
        raise reject_unsaved_change("QLMS-STALE-RECORD", "Customer details changed. Reload before correcting them")
    if (customer.name, customer.phone) == (correction.new_name, correction.new_phone):
        raise HTTPException(400, "Enter a changed name or phone number")

    canonical_phone = normalize_kenyan_phone(correction.new_phone)
    try:
        previous_phone = normalize_kenyan_phone(customer.phone)
    except ValueError:
        previous_phone = None  # Allow an owner to repair invalid legacy contact data.
    phone_changed = canonical_phone != previous_phone
    lock_save_reference(db, f"customer-phone:{canonical_phone}")
    duplicate = db.query(models.Customer).filter(
        models.Customer.id != customer.id,
        models.Customer.phone_normalized == canonical_phone,
    ).first()
    if phone_changed and duplicate and not correction.allow_shared_phone:
        raise reject_unsaved_change("QLMS-PHONE-SHARED", "This phone belongs to another saved customer. Check the match or confirm that they share a number")

    before_state = {"name": customer.name, "phone": customer.phone}
    customer.name = correction.new_name
    customer.phone = correction.new_phone
    customer.phone_normalized = canonical_phone
    db.add(models.CustomerCorrection(
        customer_id=customer.id,
        before_state=before_state,
        after_state={"name": customer.name, "phone": customer.phone},
        reason=correction.reason,
        shared_phone_confirmed=bool(phone_changed and duplicate and correction.allow_shared_phone),
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.CustomerCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(customer)
    return customer


# Find exact phone matches before staff decide whether this is the same person.
@app.get("/customers/phone-match", response_model=list[schemas.CustomerOut])
def find_customers_by_phone(
    phone: str,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    try:
        canonical_phone = normalize_kenyan_phone(phone)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return db.query(models.Customer).filter(
        models.Customer.phone_normalized == canonical_phone,
    ).order_by(models.Customer.id.desc()).all()


# Lists all customers, or searches by name/phone if 'search' is given
@app.get("/customers", response_model=list[schemas.CustomerOut])
def list_customers(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Customer)

    search_text = search.strip() if search else ""
    if search_text:
        phone_digits = phone_search_digits(search_text)
        phone_filter = (
            models.Customer.phone_normalized.ilike(f"%{phone_digits}%")
            if phone_digits
            else False
        )
        query = query.filter(
            or_(
                models.Customer.name.ilike(f"%{search_text}%"),
                models.Customer.phone.ilike(f"%{search_text}%"),
                phone_filter,
            )
        )

    return query.order_by(models.Customer.id.desc()).all()


@app.get("/customers/{customer_id}", response_model=schemas.CustomerOut)
def get_customer_details(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    customer = db.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(404, "Customer not found")
    return customer


# Lists active laundry services for staff, or all services for the owner setup page.
@app.get("/catalog/services", response_model=list[schemas.ServiceOut])
def list_services(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Service)

    if not include_inactive:
        query = query.filter(models.Service.is_active.is_(True))

    return query.order_by(models.Service.name.asc()).all()


# Adds a laundry service. Only the owner can change the shop catalogue.
@app.post("/catalog/services", response_model=schemas.ServiceOut)
def create_service(
    service: schemas.ServiceCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    service_code = make_service_code(service.name)
    if not service_code:
        raise HTTPException(status_code=400, detail="Enter a service name using letters or numbers")

    existing = db.query(models.Service).filter(
        or_(
            models.Service.code == service_code,
            models.Service.name.ilike(service.name),
        )
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="A similar service already exists")

    get_service_item_type(db, service.default_item_type_id)
    new_service = models.Service(
        code=service_code,
        name=service.name,
        unit=service.unit,
        unit_price=service.unit_price,
        category=service.category,
        default_item_type_id=service.default_item_type_id,
        item_recording_mode=service.item_recording_mode,
        turnaround_minutes=service.turnaround_minutes or (
            4320 if service.category == "dry_cleaning" else 180
        ),
    )
    db.add(new_service)
    db.commit()
    db.refresh(new_service)
    return new_service


# Updates a service or hides it from future orders without removing its history.
@app.patch("/catalog/services/{service_id}", response_model=schemas.ServiceOut)
def update_service(
    service_id: int,
    service_update: schemas.ServiceUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    service = db.query(models.Service).filter(models.Service.id == service_id).first()
    if not service:
        raise HTTPException(status_code=404, detail="Service not found")

    changes = service_update.model_dump(exclude_unset=True)
    updated_unit = changes.get("unit", service.unit)
    updated_recording_mode = changes.get(
        "item_recording_mode",
        service.item_recording_mode,
    )
    updated_category = changes.get("category", service.category)
    updated_item_type_id = changes.get(
        "default_item_type_id",
        service.default_item_type_id,
    )
    if updated_recording_mode == "detailed" and updated_unit == "kg":
        raise HTTPException(
            status_code=400,
            detail="Detailed garment services must use item or pair pricing",
        )
    if (
        updated_category == "dry_cleaning"
        and updated_recording_mode == "detailed"
        and updated_item_type_id is None
    ):
        raise HTTPException(
            status_code=400,
            detail="Select the garment linked to this Dry Cleaning service",
        )
    if updated_item_type_id is not None and updated_recording_mode != "detailed":
        raise HTTPException(
            status_code=400,
            detail="A linked garment requires individual garment details",
        )

    get_service_item_type(
        db,
        updated_item_type_id,
        allowed_inactive_id=service.default_item_type_id,
    )

    if "name" in changes:
        duplicate = db.query(models.Service).filter(
            models.Service.id != service_id,
            models.Service.name.ilike(changes["name"]),
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="A service with this name already exists")

    for field, value in changes.items():
        setattr(service, field, value)

    db.commit()
    db.refresh(service)
    return service


# Lists clothing names used by the tally screen.
@app.get("/catalog/item-types", response_model=list[schemas.ClothingItemTypeOut])
def list_clothing_item_types(
    include_inactive: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.ClothingItemType)

    if not include_inactive:
        query = query.filter(models.ClothingItemType.is_active.is_(True))

    return query.order_by(models.ClothingItemType.name.asc()).all()


# Adds a clothing item name. Employees may add Laundry tally choices only;
# broader catalogue control remains owner-only.
@app.post("/catalog/item-types", response_model=schemas.ClothingItemTypeOut)
def create_clothing_item_type(
    item_type: schemas.ClothingItemTypeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    if current_user.role != "owner" and item_type.item_group != "laundry":
        raise HTTPException(
            status_code=403,
            detail="Employees can add Laundry tally items only",
        )

    existing = db.query(models.ClothingItemType).filter(
        models.ClothingItemType.name.ilike(item_type.name)
    ).first()
    if existing:
        if not existing.is_active:
            raise HTTPException(
                status_code=400,
                detail=(
                    "This clothing item exists but is inactive. "
                    "Ask the owner to restore it in Shop setup"
                ),
            )
        raise HTTPException(status_code=400, detail="This clothing item already exists")

    new_item_type = models.ClothingItemType(
        name=item_type.name,
        item_group=item_type.item_group,
    )
    db.add(new_item_type)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=400,
            detail="This clothing item already exists",
        )
    db.refresh(new_item_type)
    return new_item_type


# Updates or deactivates a clothing item without deleting old records.
@app.patch("/catalog/item-types/{item_type_id}", response_model=schemas.ClothingItemTypeOut)
def update_clothing_item_type(
    item_type_id: int,
    item_update: schemas.ClothingItemTypeUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    item_type = db.query(models.ClothingItemType).filter(
        models.ClothingItemType.id == item_type_id
    ).first()
    if not item_type:
        raise HTTPException(status_code=404, detail="Clothing item not found")

    changes = item_update.model_dump(exclude_unset=True)
    if "name" in changes:
        duplicate = db.query(models.ClothingItemType).filter(
            models.ClothingItemType.id != item_type_id,
            models.ClothingItemType.name.ilike(changes["name"]),
        ).first()
        if duplicate:
            raise HTTPException(status_code=400, detail="This clothing item already exists")

    if changes.get("item_group") == "laundry":
        linked_service = db.query(models.Service).filter(
            models.Service.default_item_type_id == item_type_id,
            models.Service.category == "dry_cleaning",
            models.Service.is_active.is_(True),
        ).first()
        if linked_service:
            raise HTTPException(
                status_code=400,
                detail="This garment is linked to an active Dry Cleaning service",
            )

    for field, value in changes.items():
        setattr(item_type, field, value)

    db.commit()
    db.refresh(item_type)
    return item_type


# Creates a new order: checks the customer exists, calculates price, generates ticket number
@app.post("/orders", response_model=schemas.OrderOut)
def create_order(
    order: schemas.OrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint("create_order", order)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.Order, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    if order.service_type != "wash_fold" and not order.quantity.is_integer():
        raise HTTPException(400, "This service requires a whole-number quantity")
    customer = db.query(models.Customer).filter(models.Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    unit_price, total_price = logic.calculate_price(order.service_type, order.quantity)
    order_date = get_nairobi_today()
    ticket_number = logic.generate_ticket_number(db, order_date)

    new_order = models.Order(
        ticket_number=ticket_number,
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        created_by_id=current_user.id,
        customer_id=order.customer_id,
        service_type=order.service_type,
        quantity=order.quantity,
        unit_price=unit_price,
        total_price=total_price,
        order_date=order_date,
        promised_ready_at=get_promised_ready_at(
            order.promised_ready_at,
            4320 if order.service_type.startswith("dry_cleaning") else 180,
            order.peak_delay_minutes,
        ),
        peak_delay_minutes=order.peak_delay_minutes,
    )
    db.add(new_order)
    saved = commit_once(db, models.Order, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(new_order)
    return new_order


# Creates a mixed-service order while keeping the old order fields as a
# compatibility summary for the currently deployed frontend.
@app.post("/orders/detailed", response_model=schemas.OrderOut)
def create_detailed_order(
    order: schemas.DetailedOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint("create_detailed_order", order)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.Order, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    customer = db.query(models.Customer).filter(
        models.Customer.id == order.customer_id
    ).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    order_date = order.order_date or get_nairobi_today()
    if order_date > get_nairobi_today():
        raise HTTPException(
            status_code=400,
            detail="Order date cannot be in the future",
        )

    requested_service_ids = [line.service_id for line in order.services]
    active_services = db.query(models.Service).filter(
        models.Service.id.in_(requested_service_ids),
        models.Service.is_active.is_(True),
    ).all()
    services_by_id = {service.id: service for service in active_services}

    if len(services_by_id) != len(requested_service_ids):
        raise HTTPException(
            status_code=400,
            detail="One or more selected services are unavailable",
        )

    turnaround_minutes = max(
        service.turnaround_minutes for service in active_services
    )
    promised_ready_at = get_promised_ready_at(
        order.promised_ready_at,
        turnaround_minutes,
        order.peak_delay_minutes,
    )

    prepared_lines = []
    total_discount = Decimal("0")
    total_price = Decimal("0")

    for line_input in order.services:
        service = services_by_id[line_input.service_id]
        quantity = Decimal(str(line_input.quantity))

        if any(item.existing_item_id for item in line_input.items):
            raise HTTPException(
                status_code=400,
                detail="Saved garment references can only be used when editing an order",
            )

        if service.unit != "kg" and quantity != quantity.to_integral_value():
            raise HTTPException(
                status_code=400,
                detail=f"{service.name} requires a whole-number quantity",
            )

        check_fixed_service_items(
            line_input.items,
            service.default_item_type_id,
        )
        saved_items, item_status = prepare_order_items(
            db,
            line_input.items,
            service.item_recording_mode,
            line_input.quantity,
        )
        unit_price = Decimal(str(service.unit_price))
        subtotal = logic.money(unit_price * quantity)
        discount_amount = logic.money(line_input.discount_amount)
        if discount_amount >= subtotal:
            raise HTTPException(
                status_code=400,
                detail=f"Discount for {service.name} must be less than its subtotal",
            )
        line_total = subtotal - discount_amount
        total_discount += discount_amount
        total_price += line_total

        prepared_lines.append({
            "service": service,
            "quantity": quantity,
            "unit_price": unit_price,
            "subtotal": subtotal,
            "discount_amount": discount_amount,
            "line_total": line_total,
            "items": saved_items,
            "item_status": item_status,
        })

    enforce_employee_discount(db, current_user, total_price + total_discount, total_discount)

    first_line = prepared_lines[0]
    is_mixed_order = len(prepared_lines) > 1
    ticket_number = logic.generate_ticket_number(db, order_date)

    new_order = models.Order(
        ticket_number=ticket_number,
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        created_by_id=current_user.id,
        customer_id=order.customer_id,
        service_type="mixed" if is_mixed_order else first_line["service"].code,
        quantity=len(prepared_lines) if is_mixed_order else first_line["quantity"],
        unit_price=total_price if is_mixed_order else first_line["unit_price"],
        total_price=total_price,
        order_date=order_date,
        discount_reason=order.discount_reason if total_discount > 0 else None,
        discounted_by_username=(
            current_user.username if total_discount > 0 else None
        ),
        promised_ready_at=promised_ready_at,
        peak_delay_minutes=order.peak_delay_minutes,
    )

    for prepared in prepared_lines:
        service = prepared["service"]
        if service.item_recording_mode == "detailed":
            assign_garment_references(new_order, prepared["items"])
        check_time = (
            datetime.now(timezone.utc)
            if prepared["item_status"] == "completed"
            else None
        )
        service_line = models.OrderServiceLine(
            service_id=service.id,
            service_name=service.name,
            service_unit=service.unit,
            quantity=prepared["quantity"],
            unit_price=prepared["unit_price"],
            subtotal=prepared["subtotal"],
            discount_amount=prepared["discount_amount"],
            fixed_item_type_id=service.default_item_type_id,
            item_recording_mode=service.item_recording_mode,
            outsourcing_required=(
                service.category == "dry_cleaning"
                and service.item_recording_mode == "detailed"
            ),
            item_check_status=prepared["item_status"],
            item_checked_by_id=(
                current_user.id if prepared["item_status"] == "completed" else None
            ),
            item_checked_by_username=(
                current_user.username
                if prepared["item_status"] == "completed"
                else None
            ),
            item_checked_at=check_time,
            items=prepared["items"],
        )
        if service.item_recording_mode != "none":
            service_line.item_history.append(make_item_history(
                prepared["items"],
                prepared["item_status"],
                0,
                current_user,
            ))
        new_order.service_lines.append(service_line)

    if order.initial_payment is not None:
        initial = order.initial_payment
        payment = schemas.PaymentCreate(
            payment_method=initial.payment_method,
            amount=total_price if initial.amount is None else initial.amount,
            confirmed=initial.confirmed,
            received_date=initial.received_date,
        )
        new_order.payments.append(prepare_payment(new_order, payment, current_user))

    db.add(new_order)
    saved = commit_once(db, models.Order, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(new_order)
    return new_order


# Lists orders using counter search or exact customer/service history filters.
@app.get("/orders", response_model=list[schemas.OrderOut])
def list_orders(
    status: Optional[str] = None,
    search: Optional[str] = None,
    customer_id: Optional[int] = None,
    service_id: Optional[int] = None,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    outstanding: bool = False,
    due_today: bool = False,
    production_late: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Order)

    search_text = search.strip() if search else ""
    if search_text:
        search_pattern = f"%{search_text}%"
        legacy_service_pattern = f"%{make_service_code(search_text)}%"
        query = query.join(
            models.Customer,
            models.Customer.id == models.Order.customer_id,
        ).filter(
            or_(
                models.Order.ticket_number.ilike(search_pattern),
                models.Customer.name.ilike(search_pattern),
                models.Customer.phone.ilike(search_pattern),
                models.Order.service_type.ilike(legacy_service_pattern),
                models.Order.service_lines.any(
                    models.OrderServiceLine.service_name.ilike(search_pattern),
                ),
            )
        )

    if status:
        query = query.filter(models.Order.status == status)

    if customer_id is not None:
        query = query.filter(models.Order.customer_id == customer_id)

    if service_id is not None:
        service = db.query(models.Service).filter(
            models.Service.id == service_id,
        ).first()
        if not service:
            return []

        # New mixed orders use service lines, while older orders keep a code.
        query = query.filter(
            or_(
                models.Order.service_type == service.code,
                models.Order.service_lines.any(
                    models.OrderServiceLine.service_id == service_id,
                ),
            )
        )

    if start_date and end_date and end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )
    if start_date:
        query = query.filter(models.Order.order_date >= start_date)
    if end_date:
        query = query.filter(models.Order.order_date <= end_date)

    now = datetime.now(timezone.utc)
    if due_today:
        local_now = now.astimezone(NAIROBI_TIMEZONE)
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)
        query = query.filter(
            models.Order.status.notin_(["collected", "cancelled"]),
            models.Order.promised_ready_at >= local_start.astimezone(timezone.utc),
            models.Order.promised_ready_at < local_end.astimezone(timezone.utc),
        )

    if production_late:
        query = query.filter(
            models.Order.status.in_(["received", "in_progress"]),
            models.Order.promised_ready_at < now,
        )

    is_history_filter = any(
        value is not None
        for value in (customer_id, service_id, start_date, end_date)
    )
    if not status and not search_text and not is_history_filter:
        query = query.filter(models.Order.status != "cancelled")
    if due_today or production_late:
        orders = query.order_by(models.Order.promised_ready_at.asc()).all()
    elif is_history_filter:
        orders = query.order_by(
            models.Order.order_date.desc(),
            models.Order.created_at.desc(),
        ).all()
    else:
        orders = query.order_by(models.Order.created_at.desc()).all()
    if outstanding:
        return [order for order in orders if order.balance_due > 0]
    return orders


# Dedicated overdue section: orders stuck in 'ready' status past the threshold.
# Computed fresh on every request — nothing stored, no scheduled job.
@app.get("/orders/overdue", response_model=list[schemas.OrderOut])
def list_overdue_orders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    cutoff = logic.get_overdue_cutoff()
    return db.query(models.Order).filter(
        models.Order.status == "ready",
        models.Order.ready_at <= cutoff
    ).order_by(models.Order.ready_at.asc()).all()


# Returns one complete order for its individual receipt and item-editing page.
@app.get("/orders/{order_id}", response_model=schemas.OrderOut)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


# Replaces one service's clothing records when an employee completes the check later.
@app.put(
    "/orders/{order_id}/services/{service_line_id}/items",
    response_model=schemas.OrderServiceLineOut,
)
def replace_order_service_items(
    order_id: int,
    service_line_id: int,
    item_update: schemas.OrderItemsUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Lock the order while replacing items so two devices cannot overwrite a check.
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status in {"ready", "collected"}:
        raise HTTPException(
            status_code=400,
            detail="Clothing items cannot be changed after the order is ready",
        )

    service_line = db.query(models.OrderServiceLine).filter(
        models.OrderServiceLine.id == service_line_id,
        models.OrderServiceLine.order_id == order_id,
    ).first()
    if not service_line:
        raise HTTPException(status_code=404, detail="Order service not found")

    if service_line.outsourcing_handover or service_line.in_house_at:
        raise HTTPException(
            status_code=400,
            detail="Clothing details cannot change after the dry-cleaning handling choice",
        )

    db.refresh(service_line)
    if item_update.expected_revision != service_line.item_revision:
        raise reject_unsaved_change("QLMS-STALE-RECORD", "The clothing details changed on another screen. Open the order again before editing")

    if service_line.item_check_status == "completed" and not item_update.change_reason:
        raise HTTPException(
            status_code=400,
            detail="Enter why the completed clothing check needs to change",
        )

    # Preserve the current state when the first correction is made to an older order.
    if not service_line.item_history:
        service_line.item_history.append(models.OrderItemCheckHistory(
            revision=service_line.item_revision,
            check_status=service_line.item_check_status,
            item_snapshot=make_item_snapshot(list(service_line.items)),
            changed_by_id=service_line.item_checked_by_id,
            changed_by_username=(
                service_line.item_checked_by_username or "Earlier QLMS record"
            ),
        ))

    existing_item_type_ids = {item.item_type_id for item in service_line.items}
    if (
        service_line.item_recording_mode != "detailed"
        and any(item.existing_item_id for item in item_update.items)
    ):
        raise HTTPException(
            status_code=400,
            detail="Saved garment references are only used for detailed garments",
        )
    check_fixed_service_items(
        item_update.items,
        service_line.fixed_item_type_id,
    )
    saved_items, item_status = prepare_order_items(
        db,
        item_update.items,
        service_line.item_recording_mode,
        float(service_line.quantity),
        allowed_inactive_ids=existing_item_type_ids,
    )

    if service_line.item_recording_mode == "detailed":
        saved_items = merge_detailed_item_replacement(
            order,
            service_line,
            item_update.items,
            saved_items,
        )
    service_line.items = saved_items
    service_line.item_check_status = item_status
    service_line.item_revision += 1
    if item_status == "completed":
        service_line.item_checked_by_id = current_user.id
        service_line.item_checked_by_username = current_user.username
        service_line.item_checked_at = datetime.now(timezone.utc)
    else:
        service_line.item_checked_by_id = None
        service_line.item_checked_by_username = None
        service_line.item_checked_at = None
    service_line.item_history.append(make_item_history(
        saved_items,
        item_status,
        service_line.item_revision,
        current_user,
        item_update.change_reason,
    ))

    db.commit()
    db.refresh(service_line)
    return service_line


# Send every checked physical garment on one detailed service to the cleaner.
@app.post(
    "/orders/{order_id}/services/{service_line_id}/outsourcing",
    response_model=schemas.OrderServiceLineOut,
)
def create_outsource_handover(
    order_id: int,
    service_line_id: int,
    handover_input: schemas.OutsourceHandoverCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {"received", "in_progress"}:
        raise HTTPException(
            status_code=400,
            detail="A dry-cleaner handover can only be recorded before the order is ready",
        )

    service_line = db.query(models.OrderServiceLine).filter(
        models.OrderServiceLine.id == service_line_id,
        models.OrderServiceLine.order_id == order_id,
    ).first()
    if not service_line:
        raise HTTPException(status_code=404, detail="Order service not found")
    if service_line.item_recording_mode != "detailed":
        raise HTTPException(
            status_code=400,
            detail="Only individually recorded garments can be sent to a dry cleaner",
        )
    if service_line.item_check_status != "completed" or not service_line.items:
        raise HTTPException(
            status_code=400,
            detail="Complete the garment check before recording the dry-cleaner handover",
        )
    if service_line.outsourcing_handover:
        raise HTTPException(
            status_code=400,
            detail="This service already has a dry-cleaner handover",
        )
    if service_line.in_house_at:
        raise HTTPException(
            status_code=400,
            detail="This dry cleaning was already confirmed as handled in the shop",
        )

    handover = models.OutsourceHandover(
        partner_name=handover_input.partner_name,
        expected_return_at=get_expected_return_at(
            handover_input.expected_return_at,
        ),
        sent_by_id=current_user.id,
        sent_by_username=current_user.username,
        items=[
            models.OutsourceHandoverItem(
                order_item_id=item.id,
                garment_reference=item.garment_reference,
            )
            for item in service_line.items
        ],
    )
    service_line.outsourcing_handover = handover
    db.commit()
    db.refresh(service_line)
    return service_line


# The owner records an exceptional in-shop job instead of an outside handover.
@app.post(
    "/orders/{order_id}/services/{service_line_id}/in-house",
    response_model=schemas.OrderServiceLineOut,
)
def confirm_in_house_dry_cleaning(
    order_id: int,
    service_line_id: int,
    confirmation: schemas.InHouseDryCleaningConfirm,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {"received", "in_progress"}:
        raise HTTPException(
            status_code=400,
            detail="The handling choice cannot change after the order is ready",
        )

    service_line = db.query(models.OrderServiceLine).filter(
        models.OrderServiceLine.id == service_line_id,
        models.OrderServiceLine.order_id == order_id,
    ).first()
    if not service_line:
        raise HTTPException(status_code=404, detail="Order service not found")
    if not service_line.outsourcing_required:
        raise HTTPException(
            status_code=400,
            detail="This service does not need a dry-cleaning handling choice",
        )
    if service_line.item_check_status != "completed":
        raise HTTPException(
            status_code=400,
            detail="Complete the garment check before confirming in-shop cleaning",
        )
    if service_line.outsourcing_handover:
        raise HTTPException(
            status_code=400,
            detail="This service already left for the outside dry cleaner",
        )
    if service_line.in_house_at:
        raise HTTPException(
            status_code=400,
            detail="In-shop cleaning is already confirmed for this service",
        )

    service_line.in_house_reason = confirmation.reason
    service_line.in_house_by_id = current_user.id
    service_line.in_house_by_username = current_user.username
    service_line.in_house_at = datetime.now(timezone.utc)
    db.commit()
    db.refresh(service_line)
    return service_line


# Confirm one or more returned pieces without hiding garments still outside.
@app.post(
    "/orders/{order_id}/outsourcing/{handover_id}/returns",
    response_model=schemas.OrderServiceLineOut,
)
def record_outsource_returns(
    order_id: int,
    handover_id: int,
    return_input: schemas.OutsourceReturnCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status not in {"received", "in_progress"}:
        raise HTTPException(
            status_code=400,
            detail="Dry-cleaner returns cannot change after the order is ready",
        )

    handover = (
        db.query(models.OutsourceHandover)
        .join(models.OrderServiceLine)
        .filter(
            models.OutsourceHandover.id == handover_id,
            models.OrderServiceLine.order_id == order_id,
        )
        .first()
    )
    if not handover:
        raise HTTPException(status_code=404, detail="Dry-cleaner handover not found")

    handover_items = {item.id: item for item in handover.items}
    requested_ids = [item.handover_item_id for item in return_input.items]
    if any(item_id not in handover_items for item_id in requested_ids):
        raise HTTPException(
            status_code=400,
            detail="A returned garment is not part of this handover",
        )
    if any(handover_items[item_id].returned_at for item_id in requested_ids):
        raise HTTPException(
            status_code=400,
            detail="A returned garment was already confirmed",
        )

    returned_at = datetime.now(timezone.utc)
    for returned_input in return_input.items:
        item = handover_items[returned_input.handover_item_id]
        item.returned_by_id = current_user.id
        item.returned_by_username = current_user.username
        item.returned_at = returned_at
        item.return_condition = returned_input.return_condition
        item.issue_note = returned_input.issue_note

    db.commit()
    db.refresh(handover.service_line)
    return handover.service_line


# Only the owner closes a discrepancy; the original return note remains visible.
@app.patch(
    "/orders/{order_id}/outsourcing/{handover_id}/returns/{handover_item_id}/resolve",
    response_model=schemas.OrderServiceLineOut,
)
def resolve_outsource_issue(
    order_id: int,
    handover_id: int,
    handover_item_id: int,
    resolution: schemas.OutsourceIssueResolve,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    handover_item = (
        db.query(models.OutsourceHandoverItem)
        .join(models.OutsourceHandover)
        .join(models.OrderServiceLine)
        .filter(
            models.OutsourceHandoverItem.id == handover_item_id,
            models.OutsourceHandover.id == handover_id,
            models.OrderServiceLine.order_id == order_id,
        )
        .first()
    )
    if not handover_item:
        raise HTTPException(status_code=404, detail="Returned garment not found")
    if handover_item.return_condition != "issue":
        raise HTTPException(
            status_code=400,
            detail="This returned garment has no issue to resolve",
        )
    if handover_item.issue_resolved_at:
        raise HTTPException(
            status_code=400,
            detail="This return issue is already resolved",
        )

    handover_item.issue_resolved_by_id = current_user.id
    handover_item.issue_resolved_by_username = current_user.username
    handover_item.issue_resolved_at = datetime.now(timezone.utc)
    handover_item.resolution_note = resolution.resolution_note
    db.commit()
    db.refresh(handover_item.handover.service_line)
    return handover_item.handover.service_line


# Pause an order while staff wait for the customer to answer a clothing question.
@app.post("/orders/{order_id}/holds", response_model=schemas.OrderOut)
def place_customer_reply_hold(
    order_id: int,
    hold_input: schemas.OrderHoldCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    if order.status in {"ready", "collected"}:
        raise HTTPException(
            status_code=400,
            detail="A customer reply hold cannot be added after the order is ready",
        )

    active_hold = db.query(models.OrderHold).filter(
        models.OrderHold.order_id == order_id,
        models.OrderHold.resolved_at.is_(None),
    ).first()
    if active_hold:
        raise HTTPException(
            status_code=400,
            detail="This order is already waiting for a customer reply",
        )

    db.add(models.OrderHold(
        order_id=order.id,
        reason=hold_input.reason,
        created_by_id=current_user.id,
        created_by_username=current_user.username,
    ))
    db.commit()
    db.expire(order, ["holds"])
    return order


# Close the hold only after recording what the customer confirmed.
@app.patch(
    "/orders/{order_id}/holds/{hold_id}/resolve",
    response_model=schemas.OrderOut,
)
def resolve_customer_reply_hold(
    order_id: int,
    hold_id: int,
    resolution: schemas.OrderHoldResolve,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    hold = db.query(models.OrderHold).filter(
        models.OrderHold.id == hold_id,
        models.OrderHold.order_id == order_id,
    ).first()
    if not hold:
        raise HTTPException(status_code=404, detail="Customer reply hold not found")
    if hold.resolved_at is not None:
        raise HTTPException(
            status_code=400,
            detail="This hold was already closed. Open the order again.",
        )

    hold.resolved_by_id = current_user.id
    hold.resolved_by_username = current_user.username
    hold.resolution_note = resolution.resolution_note
    hold.resolved_at = datetime.now(timezone.utc)
    db.commit()
    db.expire(order, ["holds"])
    return order


# Records a confirmed Cash or M-PESA payment without overwriting earlier payments.
@app.post("/orders/{order_id}/payments", response_model=schemas.OrderOut)
def record_order_payment(
    order_id: int,
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"payment:{order_id}", payment)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.Payment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    # Lock this order while checking its balance so two staff cannot overpay it.
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # A second copy may have waited for the first payment's order lock.
    saved = find_saved_order(db, models.Payment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.expire(order, ["payments", "payment_adjustments"])
    new_payment = prepare_payment(order, payment, current_user)
    new_payment.order_id = order.id
    new_payment.request_key = str(idempotency_key)
    new_payment.request_hash = fingerprint
    db.add(new_payment)
    saved = commit_once(db, models.Payment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(order)
    return order


def prepare_payment(order, payment, current_user):
    """Validate a receipt of money without committing it separately from its order."""

    if order.status == "cancelled" or (order.status == "collected" and current_user.role != "owner"):
        raise HTTPException(
            status_code=400,
            detail="Only the owner can settle a corrected balance after collection; cancelled orders cannot take payments",
        )

    if not payment.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirm that the shop received the payment before saving it",
        )

    payment_amount = logic.money(payment.amount)
    if payment_amount <= 0:
        raise HTTPException(
            status_code=400,
            detail="Payment must be at least KES 0.01",
        )
    if payment_amount > order.balance_due:
        raise HTTPException(
            status_code=400,
            detail=f"Payment cannot exceed the remaining balance of KES {order.balance_due}",
        )

    received_date = payment.received_date or get_nairobi_today()
    if received_date > get_nairobi_today():
        raise HTTPException(
            status_code=400,
            detail="Payment received date cannot be in the future",
        )
    if received_date < order.order_date:
        raise HTTPException(
            status_code=400,
            detail="Payment received date cannot be before the order date",
        )

    return models.Payment(
        order_id=order.id,
        payment_method=payment.payment_method,
        amount=payment_amount,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
        received_date=received_date,
    )


# Keep the original receipt; an owner links each correction to that payment.
@app.post("/orders/{order_id}/payments/{payment_id}/adjustments", response_model=schemas.OrderOut)
def adjust_order_payment(
    order_id: int,
    payment_id: int,
    adjustment: schemas.PaymentAdjustmentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"payment-adjustment:{order_id}:{payment_id}", adjustment)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.PaymentAdjustment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved

    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    saved = find_saved_order(db, models.PaymentAdjustment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    if adjustment.kind == "refund":
        raise HTTPException(400, "Open the current refund form and choose the refund purpose before saving")
    if order.status == "cancelled":
        raise HTTPException(400, "A cancelled order's payment cannot be corrected")

    payment = db.query(models.Payment).filter(
        models.Payment.id == payment_id,
        models.Payment.order_id == order_id,
    ).first()
    if payment is None or payment.payment_method not in {"cash", "mpesa"}:
        raise HTTPException(404, "Confirmed payment not found for this order")
    if not adjustment.confirmed:
        raise HTTPException(400, "Confirm the correction before saving it")

    db.expire(order, ["payment_adjustments"])
    db.expire(payment, ["adjustments"])
    amount = logic.money(adjustment.amount)
    already_adjusted = sum(
        (Decimal(str(item.amount)) for item in payment.adjustments),
        Decimal("0"),
    )
    if amount <= 0 or amount > Decimal(str(payment.amount)) - already_adjusted:
        raise HTTPException(400, "Amount must be greater than zero and no more than the payment left to correct")

    today = get_nairobi_today()
    effective_date = adjustment.effective_date or today
    if adjustment.kind == "refund":
        if effective_date < payment.received_date or effective_date > today:
            raise HTTPException(400, "Refund date must be between the payment date and today")
    else:
        if adjustment.effective_date and adjustment.effective_date != payment.received_date:
            raise HTTPException(400, "A mistaken entry is corrected on its original payment date")
        effective_date = payment.received_date

    db.add(models.PaymentAdjustment(
        order_id=order.id,
        payment_id=payment.id,
        kind=adjustment.kind,
        refund_method=adjustment.refund_method,
        amount=amount,
        reason=adjustment.reason,
        effective_date=effective_date,
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.PaymentAdjustment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(order)
    return order


@app.post("/orders/{order_id}/refunds", response_model=schemas.OrderOut)
def refund_order_payment(
    order_id: int,
    refund: schemas.RefundCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"refund:{order_id}", refund)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.PaymentAdjustment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    order = (db.query(models.Order).filter(models.Order.id == order_id)
             .populate_existing().with_for_update().first())
    if order is None:
        raise HTTPException(404, "Order not found")
    db.expire(order, ["payments", "payment_adjustments"])
    if not refund.confirmed:
        raise HTTPException(400, "Confirm that the customer received the money before saving")
    payment = next((item for item in order.payments if item.id == refund.payment_id), None)
    if payment is None or payment.payment_method not in {"cash", "mpesa"}:
        raise HTTPException(404, "Confirmed payment not found for this order")
    already_adjusted = sum(
        (Decimal(str(item.amount)) for item in order.payment_adjustments if item.payment_id == payment.id),
        Decimal("0"),
    )
    if refund.amount > Decimal(str(payment.amount)) - already_adjusted:
        raise HTTPException(400, "Refund exceeds the money remaining on the selected payment")
    if refund.effective_date < payment.received_date or refund.effective_date > get_nairobi_today():
        raise HTTPException(400, "Refund date must be between the payment date and today")
    # A service refund changes the charge; returning an overpayment must not
    # reduce it a second time. Both leave the clothing's custody unchanged.
    available = order.net_charge if refund.refund_purpose == "service_refund" else order.refund_due
    if refund.amount > available:
        detail = "remaining charge" if refund.refund_purpose == "service_refund" else "refund due"
        raise HTTPException(400, f"Refund exceeds the {detail} of KES {available}")
    db.add(models.PaymentAdjustment(
        order_id=order.id, payment_id=payment.id, kind="refund",
        refund_purpose=refund.refund_purpose, refund_method=refund.refund_method,
        amount=refund.amount, reason=refund.reason, effective_date=refund.effective_date,
        request_key=str(idempotency_key), request_hash=fingerprint,
        confirmed_by_id=current_user.id, confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.PaymentAdjustment, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(order)
    return order


def order_stage_snapshot(order):
    return {
        "status": order.status,
        "ready_at": order.ready_at.isoformat() if order.ready_at else None,
        "collected_at": order.collected_at.isoformat() if order.collected_at else None,
    }


@app.post("/orders/{order_id}/corrections", response_model=schemas.OrderOut)
def correct_order_stage(
    order_id: int,
    correction: schemas.OrderCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"order-correction:{order_id}", correction)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved

    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(404, "Order not found")
    saved = find_saved_order(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    if not correction.confirmed:
        raise HTTPException(400, "Confirm this correction before saving it")
    if order.status != correction.expected_status:
        raise reject_unsaved_change("QLMS-STALE-RECORD", "The order stage changed. Reload the order before correcting it")

    before_state = order_stage_snapshot(order)
    if correction.action == "cancel":
        if order.status != "received":
            raise HTTPException(400, "Only an order still at Received can be cancelled")
        if order.amount_paid != 0:
            raise HTTPException(400, "Correct or refund all recorded payments before cancelling this order")
        if any(line.outsourcing_handover for line in order.service_lines):
            raise HTTPException(400, "An order sent to the dry cleaner cannot be cancelled here")
        if any(line.in_house_at for line in order.service_lines):
            raise HTTPException(400, "An order already handled in the shop cannot be cancelled here")
        if any(hold.resolved_at is None for hold in order.holds):
            raise HTTPException(400, "Close the customer-reply hold before cancelling")
        if not correction.goods_returned:
            raise HTTPException(400, "Confirm that all customer items have been returned before cancelling")
        order.status = "cancelled"
    else:
        previous_stage = {
            "in_progress": "received",
            "ready": "in_progress",
            "collected": "ready",
        }.get(order.status)
        if not previous_stage:
            raise HTTPException(400, "This order cannot move back another stage")
        if order.status == "collected" and not correction.still_in_shop:
            raise HTTPException(400, "Confirm the order is still in the shop before reversing collection")
        order.status = previous_stage
        if previous_stage == "in_progress":
            order.ready_at = None
        elif previous_stage == "ready":
            order.collected_at = None

    db.add(models.OrderCorrection(
        order_id=order.id,
        action=correction.action,
        before_state=before_state,
        after_state=order_stage_snapshot(order),
        reason=correction.reason,
        goods_returned_confirmed=correction.action == "cancel" and correction.goods_returned,
        still_in_shop_confirmed=before_state["status"] == "collected" and correction.still_in_shop,
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(order)
    return order


def quantity_snapshot(order, line):
    return {
        "service_line_id": line.id if line else None,
        "service_name": line.service_name if line else "Wash & Fold",
        "quantity": str(line.quantity if line else order.quantity),
        "unit_price": str(line.unit_price if line else order.unit_price),
        "subtotal": str(line.subtotal if line else order.total_price),
        "discount_amount": str(line.discount_amount if line else 0),
        "order_total": str(order.total_price),
    }


@app.post("/orders/{order_id}/quantity-corrections", response_model=schemas.OrderOut)
def correct_order_quantity(
    order_id: int,
    correction: schemas.OrderQuantityCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"quantity-correction:{order_id}", correction)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved

    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(404, "Order not found")
    saved = find_saved_order(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    if order.status == "cancelled":
        raise HTTPException(400, "A cancelled order's quantity cannot be corrected")
    if not correction.confirmed:
        raise HTTPException(400, "Confirm the quantity and new price before saving")

    db.expire(order, ["service_lines", "payments", "payment_adjustments"])
    line = next((item for item in order.service_lines if item.id == correction.service_line_id), None)
    if order.service_lines and line is None:
        raise HTTPException(404, "Select a saved service on this order")
    if line and line.service_unit != "kg":
        raise HTTPException(400, "This correction currently supports kg services only")
    if not line and order.service_type != "wash_fold":
        raise HTTPException(400, "This older order's quantity cannot be corrected here")

    old_quantity = Decimal(str(line.quantity if line else order.quantity))
    if Decimal(str(correction.expected_quantity)) != old_quantity:
        raise reject_unsaved_change("QLMS-STALE-RECORD", "The quantity changed. Reload this order before correcting it")
    before_state = quantity_snapshot(order, line)
    new_quantity = Decimal(str(correction.new_quantity))
    unit_price = Decimal(str(line.unit_price if line else order.unit_price))
    new_subtotal = logic.money(unit_price * new_quantity)
    old_line_total = line.line_total if line else Decimal(str(order.total_price))
    if line:
        if correction.new_discount_amount is None and Decimal(str(line.discount_amount)) > 0:
            raise HTTPException(400, "Confirm the new discount amount for this service")
        new_discount = logic.money(correction.new_discount_amount or 0)
    else:
        if correction.new_discount_amount not in {None, 0}:
            raise HTTPException(400, "This older order has no service discount to change")
        new_discount = Decimal("0")
    if new_discount >= new_subtotal:
        raise HTTPException(400, "Discount must be less than the new service subtotal")
    new_total = logic.money(Decimal(str(order.total_price)) - old_line_total + new_subtotal - new_discount)
    if new_total < order.service_refunds:
        raise HTTPException(400, "The new total cannot be below service refunds already returned")
    if new_quantity == old_quantity:
        raise HTTPException(400, "Enter a different kg quantity before saving")

    if line:
        old_discount = Decimal(str(line.discount_amount))
        line.quantity = new_quantity
        line.subtotal = new_subtotal
        line.discount_amount = new_discount
        if len(order.service_lines) == 1:
            order.quantity = new_quantity
        if new_discount != old_discount:
            order.discount_reason = correction.reason if any(
                Decimal(str(item.discount_amount)) > 0 for item in order.service_lines
            ) else None
            order.discounted_by_username = current_user.username if order.discount_reason else None
    else:
        order.quantity = new_quantity
    order.total_price = new_total

    db.add(models.OrderCorrection(
        order_id=order.id,
        action="quantity",
        before_state=before_state,
        after_state=quantity_snapshot(order, line),
        reason=correction.reason,
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(order)
    return order


@app.post("/orders/{order_id}/customer-corrections", response_model=schemas.OrderOut)
def correct_order_customer(
    order_id: int,
    correction: schemas.OrderCustomerCorrectionCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
    *,
    idempotency_key: Annotated[UUID, Header()],
):
    fingerprint = request_fingerprint(f"customer-correction:{order_id}", correction)
    lock_save_reference(db, idempotency_key)
    saved = find_saved_order(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved

    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(404, "Order not found")
    saved = find_saved_order(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    if not correction.confirmed:
        raise HTTPException(400, "Confirm the correct customer before saving")
    if order.customer_id != correction.expected_customer_id:
        raise reject_unsaved_change("QLMS-STALE-RECORD", "This order's customer changed. Reload before correcting it")
    if correction.new_customer_id == order.customer_id:
        raise HTTPException(400, "Select a different customer for this ticket")
    previous_customer = db.get(models.Customer, order.customer_id)
    new_customer = db.get(models.Customer, correction.new_customer_id)
    if not new_customer:
        raise HTTPException(404, "Selected customer not found")

    order.customer_id = new_customer.id
    db.add(models.OrderCorrection(
        order_id=order.id,
        action="customer_reassign",
        before_state={"customer_id": previous_customer.id, "customer_name": previous_customer.name},
        after_state={"customer_id": new_customer.id, "customer_name": new_customer.name},
        reason=correction.reason,
        request_key=str(idempotency_key),
        request_hash=fingerprint,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
    ))
    saved = commit_once(db, models.OrderCorrection, idempotency_key, fingerprint, current_user.id)
    if saved is not None:
        return saved
    db.refresh(order)
    return order


# Updates an order's status, and stamps ready_at / collected_at when relevant
@app.patch("/orders/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Lock the row so two devices cannot move the same order at the same time.
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .populate_existing()
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    next_status = {
        "received": "in_progress",
        "in_progress": "ready",
        "ready": "collected",
    }.get(order.status)
    if status_update.status != next_status:
        raise HTTPException(
            status_code=400,
            detail="Orders can only move forward by one stage at a time",
        )

    if status_update.status in {"in_progress", "ready"}:
        pending_item_checks = db.query(models.OrderServiceLine).filter(
            models.OrderServiceLine.order_id == order_id,
            models.OrderServiceLine.item_check_status == "pending",
        ).count()
        if pending_item_checks:
            raise HTTPException(
                status_code=400,
                detail="Complete the clothing check before washing starts",
            )

        active_hold = db.query(models.OrderHold).filter(
            models.OrderHold.order_id == order_id,
            models.OrderHold.resolved_at.is_(None),
        ).first()
        if active_hold:
            raise HTTPException(
                status_code=400,
                detail="Record the customer's reply and close the hold before moving this order",
            )

    if status_update.status == "ready":
        missing_handovers = db.query(models.OrderServiceLine).filter(
            models.OrderServiceLine.order_id == order_id,
            models.OrderServiceLine.outsourcing_required.is_(True),
            models.OrderServiceLine.in_house_at.is_(None),
            ~models.OrderServiceLine.outsourcing_handover.has(),
        ).count()
        if missing_handovers:
            raise HTTPException(
                status_code=400,
                detail="Record the dry-cleaner handover or ask the owner to confirm in-shop cleaning before marking this order ready",
            )

        unresolved_outsourcing = (
            db.query(models.OutsourceHandoverItem)
            .join(models.OutsourceHandover)
            .join(models.OrderServiceLine)
            .filter(
                models.OrderServiceLine.order_id == order_id,
                or_(
                    models.OutsourceHandoverItem.returned_at.is_(None),
                    and_(
                        models.OutsourceHandoverItem.return_condition == "issue",
                        models.OutsourceHandoverItem.issue_resolved_at.is_(None),
                    ),
                ),
            )
            .count()
        )
        if unresolved_outsourcing:
            raise HTTPException(
                status_code=400,
                detail="Confirm every outsourced garment return and resolve any issue before marking this order ready",
            )

    if status_update.status == "collected" and order.balance_due > 0:
        raise HTTPException(
            status_code=400,
            detail=f"Record the remaining payment of KES {order.balance_due} before collection",
        )

    order.status = status_update.status

    if status_update.status == "ready":
        order.ready_at = datetime.now(timezone.utc)
    elif status_update.status == "collected":
        order.collected_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(order)
    return order

# Dashboard summary: counts of orders per status, plus overdue count. Owner-only.
@app.get("/dashboard/summary", response_model=schemas.DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_owner)):
    cutoff = logic.get_overdue_cutoff()
    all_orders = db.query(models.Order).all()
    outstanding_orders = [
        order for order in all_orders if order.balance_due > 0
    ]

    return schemas.DashboardSummary(
        received=db.query(models.Order).filter(models.Order.status == "received").count(),
        in_progress=db.query(models.Order).filter(models.Order.status == "in_progress").count(),
        ready=db.query(models.Order).filter(models.Order.status == "ready").count(),
        collected=db.query(models.Order).filter(models.Order.status == "collected").count(),
        overdue=db.query(models.Order).filter(
            models.Order.status == "ready",
            models.Order.ready_at <= cutoff
        ).count(),
        unpaid=len(outstanding_orders),
        outstanding_balance=sum(
            (order.balance_due for order in outstanding_orders),
            Decimal("0"),
        ),
    )


# Date-filtered order value and received-money totals for the owner.
@app.get("/dashboard/financial-summary", response_model=schemas.FinancialSummary)
def financial_summary(
    start_date: date,
    end_date: date,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    if end_date < start_date:
        raise HTTPException(
            status_code=400,
            detail="End date cannot be before start date",
        )

    period_orders = db.query(models.Order).filter(
        models.Order.order_date >= start_date,
        models.Order.order_date <= end_date,
    ).all()
    orders = [order for order in period_orders if order.status != "cancelled"]
    payments = db.query(models.Payment).filter(
        models.Payment.received_date >= start_date,
        models.Payment.received_date <= end_date,
        models.Payment.payment_method.in_(["cash", "mpesa"]),
    ).all()
    refunds = db.query(models.PaymentAdjustment).filter(
        models.PaymentAdjustment.kind == "refund",
        models.PaymentAdjustment.effective_date >= start_date,
        models.PaymentAdjustment.effective_date <= end_date,
    ).all()

    daily_totals = {
        start_date + timedelta(days=day_offset): Decimal("0")
        for day_offset in range((end_date - start_date).days + 1)
    }
    cash_received = Decimal("0")
    mpesa_received = Decimal("0")
    customer_totals = {}
    service_totals = {}

    # Service lines hold the exact booked quantities and values for mixed orders.
    # Older orders use their original single-service columns as a safe fallback.
    service_catalog = db.query(models.Service).all()
    services_by_id = {service.id: service for service in service_catalog}
    services_by_code = {service.code: service for service in service_catalog}

    for order in orders:
        if order.service_lines:
            booked_services = []
            for line in order.service_lines:
                current_service = services_by_id.get(line.service_id)
                booked_services.append({
                    "service_id": line.service_id,
                    "service_name": (
                        current_service.name
                        if current_service
                        else line.service_name
                    ),
                    "service_unit": line.service_unit,
                    "quantity": Decimal(str(line.quantity)),
                    "booked_value": Decimal(str(line.line_total)),
                    "key": (line.service_id, line.service_unit),
                })
        else:
            legacy_service = services_by_code.get(order.service_type)
            if legacy_service:
                legacy_name = legacy_service.name
            elif order.service_type == "wash_fold":
                legacy_name = "Wash & Fold"
            else:
                legacy_name = order.service_type.replace("_", " ").title()
            legacy_unit = "kg" if order.service_type == "wash_fold" else "item"
            legacy_key = (
                legacy_service.id
                if legacy_service
                else f"legacy:{order.service_type}",
                legacy_unit,
            )
            booked_services = [
                {
                    "service_id": legacy_service.id if legacy_service else None,
                    "service_name": legacy_name,
                    "service_unit": legacy_unit,
                    "quantity": Decimal(str(order.quantity)),
                    "booked_value": Decimal(str(order.total_price)),
                    "key": legacy_key,
                }
            ]

        for booked_service in booked_services:
            service_total = service_totals.setdefault(
                booked_service["key"],
                {
                    "service_id": booked_service["service_id"],
                    "service_name": booked_service["service_name"],
                    "service_unit": booked_service["service_unit"],
                    "order_ids": set(),
                    "quantity_booked": Decimal("0"),
                    "booked_value": Decimal("0"),
                },
            )
            service_total["order_ids"].add(order.id)
            service_total["quantity_booked"] += booked_service["quantity"]
            service_total["booked_value"] += booked_service["booked_value"]

    payment_order_ids = {payment.order_id for payment in payments}
    payment_orders = (
        db.query(models.Order).filter(models.Order.id.in_(payment_order_ids)).all()
        if payment_order_ids
        else []
    )
    payment_orders_by_id = {order.id: order for order in payment_orders}
    customer_ids = {order.customer_id for order in payment_orders}
    customers = (
        db.query(models.Customer).filter(models.Customer.id.in_(customer_ids)).all()
        if customer_ids
        else []
    )
    customers_by_id = {customer.id: customer for customer in customers}

    for payment in payments:
        # An entry mistake restates the original day's receipt. A real refund
        # remains a separate cash-out event on the date money was returned.
        payment_amount = Decimal(str(payment.amount)) - sum(
            (Decimal(str(item.amount)) for item in payment.adjustments
             if item.kind == "entry_error"),
            Decimal("0"),
        )
        if payment.payment_method == "cash":
            cash_received += payment_amount
        else:
            mpesa_received += payment_amount

        payment_date = payment.received_date
        daily_totals[payment_date] += payment_amount

        order = payment_orders_by_id[payment.order_id]
        customer_totals[order.customer_id] = (
            customer_totals.get(order.customer_id, Decimal("0"))
            + payment_amount
        )

    outstanding_orders = [order for order in orders if order.balance_due > 0]
    refunds_sent = sum(
        (Decimal(str(refund.amount)) for refund in refunds),
        Decimal("0"),
    )

    return schemas.FinancialSummary(
        start_date=start_date,
        end_date=end_date,
        orders_booked=len(orders),
        cancelled_orders=len(period_orders) - len(orders),
        gross_order_value=sum(
            (order.subtotal_before_discount for order in orders),
            Decimal("0"),
        ),
        discounts_given=sum(
            (order.discount_amount for order in orders),
            Decimal("0"),
        ),
        order_value=sum(
            (Decimal(str(order.total_price)) for order in orders),
            Decimal("0"),
        ),
        service_refunds=sum((order.service_refunds for order in orders), Decimal("0")),
        net_charge=sum((order.net_charge for order in orders), Decimal("0")),
        refund_due=sum((order.refund_due for order in orders), Decimal("0")),
        cash_received=cash_received,
        mpesa_received=mpesa_received,
        total_received=cash_received + mpesa_received,
        refunds_sent=refunds_sent,
        net_cash_movement=cash_received + mpesa_received - refunds_sent,
        outstanding_orders=len(outstanding_orders),
        outstanding_balance=sum(
            (order.balance_due for order in outstanding_orders),
            Decimal("0"),
        ),
        daily_received=[
            schemas.DailyReceivedTotal(date=day, amount=amount)
            for day, amount in daily_totals.items()
        ],
        customer_revenue=[
            schemas.CustomerRevenue(
                customer_id=customer_id,
                customer_name=customers_by_id[customer_id].name,
                customer_phone=customers_by_id[customer_id].phone,
                total_received=amount,
            )
            for customer_id, amount in sorted(
                customer_totals.items(),
                key=lambda item: (-item[1], customers_by_id[item[0]].name.lower()),
            )
        ],
        top_services=[
            schemas.TopServiceBooking(
                service_id=service_total["service_id"],
                service_name=service_total["service_name"],
                service_unit=service_total["service_unit"],
                order_count=len(service_total["order_ids"]),
                quantity_booked=service_total["quantity_booked"],
                booked_value=service_total["booked_value"],
            )
            for service_total in sorted(
                service_totals.values(),
                key=lambda item: (
                    -item["booked_value"],
                    -len(item["order_ids"]),
                    item["service_name"].lower(),
                    item["service_unit"],
                ),
            )
        ],
    )


# Exports all orders as a downloadable CSV file. Owner-only.
@app.get("/dashboard/export")
def export_orders_csv(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_owner)):
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()

    # Keep spreadsheet quantities short while money always has two decimal places.
    def format_quantity(value):
        return format(Decimal(str(value)).normalize(), "f")

    def format_money(value):
        return f"{Decimal(str(value)):.2f}"

    def correction_description(item):
        before = item.before_state
        after = item.after_state
        if item.action == "customer_reassign":
            change = (
                f"{before['customer_name']} (#{before['customer_id']}) to "
                f"{after['customer_name']} (#{after['customer_id']})"
            )
        elif item.action == "quantity":
            change = f"{before['service_name']} {before['quantity']} to {after['quantity']} kg"
        else:
            change = f"{before['status']} to {after['status']}"
        return f"#{item.id} {item.action}: {change}; {item.confirmed_by_username}; {item.reason}"

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket Number", "Customer ID", "Order Date", "Services",
        "Subtotal Before Discount", "Discount", "Discount Reason",
        "Discounted By", "Total Price", "Effective Order Value",
        "Amount Paid", "Entry Corrections", "Refunds Returned",
        "Balance Due", "Payment Status", "Payment Methods",
        "Payment Received Dates", "Status", "Recorded At", "Ready At",
        "Collected At", "Order Correction History", "Payment Adjustment History",
        "Service Refunds", "Net Charge", "Refund Due"
    ])
    for order in orders:
        service_summary = (
            "; ".join(
                f"{line.service_name} ({format_quantity(line.quantity)} {line.service_unit})"
                for line in order.service_lines
            )
            if order.service_lines
            else f"{order.service_type} ({order.quantity})"
        )
        payment_methods = (
            ", ".join(payment.payment_method for payment in order.payments)
            if order.payments
            else "None"
        )
        payment_received_dates = (
            ", ".join(str(payment.received_date) for payment in order.payments)
            if order.payments
            else "None"
        )
        entry_corrections = sum(
            (Decimal(str(item.amount)) for item in order.payment_adjustments
             if item.kind == "entry_error"),
            Decimal("0"),
        )
        refunds_returned = sum(
            (Decimal(str(item.amount)) for item in order.payment_adjustments
             if item.kind == "refund"),
            Decimal("0"),
        )
        correction_history = "; ".join(
            correction_description(item) for item in order.corrections
        )
        adjustment_history = "; ".join(
            f"#{item.id} {item.kind}: {format_money(item.amount)} on "
            f"{item.effective_date}; {item.confirmed_by_username}; {item.reason}"
            + (f"; purpose={item.refund_purpose or 'not recorded'}; method={item.refund_method}" if item.kind == "refund" else "")
            for item in order.payment_adjustments
        )
        writer.writerow([
            order.ticket_number, order.customer_id, order.order_date,
            service_summary, format_money(order.subtotal_before_discount),
            format_money(order.discount_amount), order.discount_reason or "",
            order.discounted_by_username or "",
            format_money(order.total_price),
            format_money(order.net_charge),
            format_money(order.amount_paid),
            format_money(entry_corrections), format_money(refunds_returned),
            format_money(order.balance_due),
            order.payment_status, payment_methods, payment_received_dates,
            order.status,
            order.created_at, order.ready_at, order.collected_at,
            correction_history, adjustment_history,
            format_money(order.service_refunds), format_money(order.net_charge), format_money(order.refund_due),
        ])
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=qlms_orders_export.csv"}
    )
