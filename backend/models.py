# models.py
# Defines our database tables as Python classes.

from sqlalchemy import Boolean, Column, Integer, String, Numeric, ForeignKey, TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from decimal import Decimal
from database import Base

# Owner/employee login accounts
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# Customer records
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# Laundry services the owner can manage without changing the code.
class Service(Base):
    __tablename__ = "services"

    id = Column(Integer, primary_key=True, index=True)
    code = Column(String(50), unique=True, nullable=False)
    name = Column(String(100), unique=True, nullable=False)
    unit = Column(String(20), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    category = Column(String(30), nullable=False, default="general")
    default_item_type_id = Column(
        Integer,
        ForeignKey("clothing_item_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_recording_mode = Column(String(20), nullable=False, default="none")
    turnaround_minutes = Column(Integer, nullable=False, default=180)
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# Clothing names used by the employee when tallying received items.
class ClothingItemType(Base):
    __tablename__ = "clothing_item_types"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    item_group = Column(String(20), nullable=False, default="laundry")
    is_active = Column(Boolean, nullable=False, default=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# Laundry orders, linked to a customer
class Order(Base):
    __tablename__ = "orders"

    id = Column(Integer, primary_key=True, index=True)
    ticket_number = Column(String(30), unique=True, nullable=False)
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False)
    service_type = Column(String(20), nullable=False)
    quantity = Column(Numeric, nullable=False)
    unit_price = Column(Numeric, nullable=False)
    total_price = Column(Numeric, nullable=False)
    status = Column(String(20), nullable=False, default="received")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    promised_ready_at = Column(TIMESTAMP(timezone=True), nullable=True)
    peak_delay_minutes = Column(Integer, nullable=False, default=0)
    ready_at = Column(TIMESTAMP(timezone=True), nullable=True)
    collected_at = Column(TIMESTAMP(timezone=True), nullable=True)

    # Detailed service lines are additive, so older orders can keep their
    # original single-service columns while new mixed orders use these rows.
    service_lines = relationship(
        "OrderServiceLine",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderServiceLine.id",
    )
    payments = relationship(
        "Payment",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="Payment.id",
    )

    # Payment totals are derived from history so staff never type over a balance.
    @property
    def amount_paid(self):
        return sum(
            (Decimal(str(payment.amount)) for payment in self.payments),
            Decimal("0"),
        )

    @property
    def balance_due(self):
        balance = Decimal(str(self.total_price)) - self.amount_paid
        return max(balance, Decimal("0"))

    @property
    def payment_status(self):
        if self.amount_paid <= 0:
            return "unpaid"
        if self.balance_due > 0:
            return "part_paid"
        return "paid"


# A service selected within an order, with its original name and price saved.
class OrderServiceLine(Base):
    __tablename__ = "order_service_lines"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    service_id = Column(Integer, ForeignKey("services.id"), nullable=False)
    service_name = Column(String(100), nullable=False)
    service_unit = Column(String(20), nullable=False)
    quantity = Column(Numeric(10, 2), nullable=False)
    unit_price = Column(Numeric(10, 2), nullable=False)
    subtotal = Column(Numeric(10, 2), nullable=False)
    fixed_item_type_id = Column(
        Integer,
        ForeignKey("clothing_item_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_recording_mode = Column(String(20), nullable=False)
    item_check_status = Column(String(20), nullable=False, default="not_required")

    order = relationship("Order", back_populates="service_lines")
    items = relationship(
        "OrderItem",
        back_populates="service_line",
        cascade="all, delete-orphan",
        order_by="OrderItem.id",
    )


# Clothing counted or identified under one particular order service.
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    order_service_line_id = Column(
        Integer,
        ForeignKey("order_service_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    item_type_id = Column(Integer, ForeignKey("clothing_item_types.id"), nullable=False)
    item_name = Column(String(100), nullable=False)
    quantity = Column(Integer, nullable=False)
    description = Column(String(200), nullable=True)
    is_damaged = Column(Boolean, nullable=True)
    damage_note = Column(String(300), nullable=True)
    stain_note = Column(String(300), nullable=True)

    service_line = relationship("OrderServiceLine", back_populates="items")


# Append-only payment history confirmed by a staff member at the shop.
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    payment_method = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    confirmed_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payments")
