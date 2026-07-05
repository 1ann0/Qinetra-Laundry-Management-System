# main.py
# Entry point of the FastAPI backend. All API routes live or are wired up here.

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import Optional
from database import get_db
import models
import schemas
import logic

app = FastAPI()

# Allows the frontend (different domain) to call this backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check route
@app.get("/")
def read_root():
    return {"status": "QLMS backend is running"}


# Creates a new customer
@app.post("/customers", response_model=schemas.CustomerOut)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    new_customer = models.Customer(name=customer.name, phone=customer.phone)
    db.add(new_customer)
    db.commit()
    db.refresh(new_customer)
    return new_customer


# Lists all customers, or searches by name/phone if 'search' is given
@app.get("/customers", response_model=list[schemas.CustomerOut])
def list_customers(search: Optional[str] = None, db: Session = Depends(get_db)):
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
def create_order(order: schemas.OrderCreate, db: Session = Depends(get_db)):
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
def list_orders(status: Optional[str] = None, db: Session = Depends(get_db)):
    query = db.query(models.Order)

    if status:
        query = query.filter(models.Order.status == status)

    return query.order_by(models.Order.created_at.desc()).all()
