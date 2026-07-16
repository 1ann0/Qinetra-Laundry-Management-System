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
