# main.py
# Entry point of the FastAPI backend. All API routes live or are wired up here.

from fastapi import FastAPI, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from datetime import datetime, timezone
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


# Turn a service name into a short internal code used by the API and database.
def make_service_code(name: str) -> str:
    return re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")


# Health check route
@app.get("/")
def read_root():
    return {"status": "QLMS backend is running"}


# Logs a user in: checks username/password, returns a signed JWT with their role
@app.post("/auth/login", response_model=schemas.Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.username == form_data.username).first()

    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect username or password")

    token = auth.create_access_token(user_id=user.id, role=user.role)
    return {"access_token": token, "token_type": "bearer", "role": user.role}


# Creates a new employee/owner account. Owner-only.
@app.post("/users", response_model=schemas.UserOut)
def create_user(user: schemas.UserCreate, db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_owner)):
    existing = db.query(models.User).filter(models.User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Username already taken")

    new_user = models.User(
        username=user.username,
        password_hash=auth.hash_password(user.password),
        role=user.role,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


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

    new_service = models.Service(
        code=service_code,
        name=service.name,
        unit=service.unit,
        unit_price=service.unit_price,
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

    new_item_type = models.ClothingItemType(name=item_type.name)
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
    ticket_number = logic.generate_ticket_number(db)

    new_order = models.Order(
        ticket_number=ticket_number,
        customer_id=order.customer_id,
        service_type=order.service_type,
        quantity=order.quantity,
        unit_price=unit_price,
        total_price=total_price,
    )
    db.add(new_order)
    db.commit()
    db.refresh(new_order)
    return new_order


# Lists all orders, optionally filtered by status (received/in_progress/ready/collected)
@app.get("/orders", response_model=list[schemas.OrderOut])
def list_orders(
    status: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    query = db.query(models.Order)

    if status:
        query = query.filter(models.Order.status == status)

    return query.order_by(models.Order.created_at.desc()).all()


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


# Updates an order's status, and stamps ready_at / collected_at when relevant
@app.patch("/orders/{order_id}/status", response_model=schemas.OrderOut)
def update_order_status(
    order_id: int,
    status_update: schemas.OrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user),
):
    order = db.query(models.Order).filter(models.Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

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

    return schemas.DashboardSummary(
        received=db.query(models.Order).filter(models.Order.status == "received").count(),
        in_progress=db.query(models.Order).filter(models.Order.status == "in_progress").count(),
        ready=db.query(models.Order).filter(models.Order.status == "ready").count(),
        collected=db.query(models.Order).filter(models.Order.status == "collected").count(),
        overdue=db.query(models.Order).filter(
            models.Order.status == "ready",
            models.Order.ready_at <= cutoff
        ).count(),
    )


# Exports all orders as a downloadable CSV file. Owner-only.
@app.get("/dashboard/export")
def export_orders_csv(db: Session = Depends(get_db), current_user: models.User = Depends(auth.require_owner)):
    orders = db.query(models.Order).order_by(models.Order.created_at.desc()).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "Ticket Number", "Customer ID", "Service Type", "Quantity",
        "Unit Price", "Total Price", "Status", "Created At", "Ready At", "Collected At"
    ])
    for order in orders:
        writer.writerow([
            order.ticket_number, order.customer_id, order.service_type, order.quantity,
            order.unit_price, order.total_price, order.status,
            order.created_at, order.ready_at, order.collected_at
        ])
    output.seek(0)

    return StreamingResponse(
        output,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=qlms_orders_export.csv"}
    )
