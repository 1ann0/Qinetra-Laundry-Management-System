# main.py
# Entry point of the FastAPI backend. All API routes live or are wired up here.

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError
from typing import Optional
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

    if recording_mode == "detailed":
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
        if sum(item.quantity for item in item_inputs) > service_quantity:
            raise HTTPException(
                status_code=400,
                detail="Detailed garments cannot exceed the selected service quantity",
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

    saved_items = [
        models.OrderItem(
            item_type_id=item.item_type_id,
            item_name=item_types_by_id[item.item_type_id].name,
            quantity=item.quantity,
            description=item.description,
            is_damaged=item.is_damaged,
            damage_note=item.damage_note,
            stain_note=item.stain_note,
        )
        for item in item_inputs
    ]
    item_status = logic.get_item_check_status(
        recording_mode,
        service_quantity,
        [item.quantity for item in item_inputs],
    )
    return saved_items, item_status


# Health check route
@app.get("/")
def read_root():
    return {"status": "QLMS backend is running"}


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
    # Check for an existing customer with the same phone number, before creating the new one
    existing = db.query(models.Customer).filter(models.Customer.phone == customer.phone).first()

    new_customer = models.Customer(name=customer.name, phone=customer.phone)
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)

    # If a match was found, attach a warning instead of blocking creation
    warning = None
    if existing:
        warning = f"This phone number is already linked to '{existing.name}' (customer ID {existing.id}). A new record was still created — verify this isn't a duplicate."

    return schemas.CustomerCreateResponse(customer=new_customer, duplicate_warning=warning)


# Lists all customers, or searches by name/phone if 'search' is given
@app.get("/customers", response_model=list[schemas.CustomerOut])
def list_customers(
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Customer)

    if search:
        query = query.filter(
            or_(
                models.Customer.name.ilike(f"%{search}%"),
                models.Customer.phone.ilike(f"%{search}%")
            )
        )

    return query.order_by(models.Customer.id.desc()).all()


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


# Adds a clothing item name to the tally list. Owner-only.
@app.post("/catalog/item-types", response_model=schemas.ClothingItemTypeOut)
def create_clothing_item_type(
    item_type: schemas.ClothingItemTypeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_owner),
):
    existing = db.query(models.ClothingItemType).filter(
        models.ClothingItemType.name.ilike(item_type.name)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="This clothing item already exists")

    new_item_type = models.ClothingItemType(
        name=item_type.name,
        item_group=item_type.item_group,
    )
    db.add(new_item_type)
    db.commit()
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
):
    customer = db.query(models.Customer).filter(models.Customer.id == order.customer_id).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    unit_price, total_price = logic.calculate_price(order.service_type, order.quantity)
    order_date = get_nairobi_today()
    ticket_number = logic.generate_ticket_number(db, order_date)

    new_order = models.Order(
        ticket_number=ticket_number,
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
    db.commit()
    db.refresh(new_order)
    return new_order


# Creates a mixed-service order while keeping the old order fields as a
# compatibility summary for the currently deployed frontend.
@app.post("/orders/detailed", response_model=schemas.OrderOut)
def create_detailed_order(
    order: schemas.DetailedOrderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
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
        subtotal = (unit_price * quantity).quantize(Decimal("0.01"))
        discount_amount = Decimal(str(line_input.discount_amount)).quantize(
            Decimal("0.01")
        )
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

    first_line = prepared_lines[0]
    is_mixed_order = len(prepared_lines) > 1
    ticket_number = logic.generate_ticket_number(db, order_date)

    new_order = models.Order(
        ticket_number=ticket_number,
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
            item_check_status=prepared["item_status"],
            items=prepared["items"],
        )
        new_order.service_lines.append(service_line)

    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


# Lists all orders, optionally filtered by status (received/in_progress/ready/collected)
@app.get("/orders", response_model=list[schemas.OrderOut])
def list_orders(
    status: Optional[str] = None,
    outstanding: bool = False,
    due_today: bool = False,
    production_late: bool = False,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Order)

    if status:
        query = query.filter(models.Order.status == status)

    now = datetime.now(timezone.utc)
    if due_today:
        local_now = now.astimezone(NAIROBI_TIMEZONE)
        local_start = local_now.replace(hour=0, minute=0, second=0, microsecond=0)
        local_end = local_start + timedelta(days=1)
        query = query.filter(
            models.Order.status != "collected",
            models.Order.promised_ready_at >= local_start.astimezone(timezone.utc),
            models.Order.promised_ready_at < local_end.astimezone(timezone.utc),
        )

    if production_late:
        query = query.filter(
            models.Order.status.in_(["received", "in_progress"]),
            models.Order.promised_ready_at < now,
        )

    if due_today or production_late:
        orders = query.order_by(models.Order.promised_ready_at.asc()).all()
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

    existing_item_type_ids = {item.item_type_id for item in service_line.items}
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

    service_line.items.clear()
    service_line.items.extend(saved_items)
    service_line.item_check_status = item_status

    db.commit()
    db.refresh(service_line)
    return service_line


# Records a confirmed Cash or M-PESA payment without overwriting earlier payments.
@app.post("/orders/{order_id}/payments", response_model=schemas.OrderOut)
def record_order_payment(
    order_id: int,
    payment: schemas.PaymentCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    # Lock this order while checking its balance so two staff cannot overpay it.
    order = (
        db.query(models.Order)
        .filter(models.Order.id == order_id)
        .with_for_update()
        .first()
    )
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    if order.status == "collected":
        raise HTTPException(
            status_code=400,
            detail="Payments cannot be changed after an order is collected",
        )

    if not payment.confirmed:
        raise HTTPException(
            status_code=400,
            detail="Confirm that the shop received the payment before saving it",
        )

    payment_amount = Decimal(str(payment.amount)).quantize(Decimal("0.01"))
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

    new_payment = models.Payment(
        order_id=order.id,
        payment_method=payment.payment_method,
        amount=payment_amount,
        confirmed_by_id=current_user.id,
        confirmed_by_username=current_user.username,
        received_date=received_date,
    )
    db.add(new_payment)
    db.commit()
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

    if status_update.status == "ready":
        pending_item_checks = db.query(models.OrderServiceLine).filter(
            models.OrderServiceLine.order_id == order_id,
            models.OrderServiceLine.item_check_status == "pending",
        ).count()
        if pending_item_checks:
            raise HTTPException(
                status_code=400,
                detail="Complete the pending clothing check before this order is ready",
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

    orders = db.query(models.Order).filter(
        models.Order.order_date >= start_date,
        models.Order.order_date <= end_date,
    ).all()
    payments = db.query(models.Payment).filter(
        models.Payment.received_date >= start_date,
        models.Payment.received_date <= end_date,
        models.Payment.payment_method.in_(["cash", "mpesa"]),
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
        payment_amount = Decimal(str(payment.amount))
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

    return schemas.FinancialSummary(
        start_date=start_date,
        end_date=end_date,
        orders_booked=len(orders),
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
        cash_received=cash_received,
        mpesa_received=mpesa_received,
        total_received=cash_received + mpesa_received,
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

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket Number", "Customer ID", "Order Date", "Services",
        "Subtotal Before Discount", "Discount", "Discount Reason",
        "Discounted By", "Total Price",
        "Amount Paid", "Balance Due", "Payment Status", "Payment Methods",
        "Payment Received Dates", "Status", "Recorded At", "Ready At",
        "Collected At"
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
        writer.writerow([
            order.ticket_number, order.customer_id, order.order_date,
            service_summary, format_money(order.subtotal_before_discount),
            format_money(order.discount_amount), order.discount_reason or "",
            order.discounted_by_username or "",
            format_money(order.total_price), format_money(order.amount_paid),
            format_money(order.balance_due),
            order.payment_status, payment_methods, payment_received_dates,
            order.status,
            order.created_at, order.ready_at, order.collected_at
        ])
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=qlms_orders_export.csv"}
    )
