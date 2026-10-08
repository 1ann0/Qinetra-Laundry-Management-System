# models.py
# Defines our database tables as Python classes.

from sqlalchemy import (
    BigInteger,
    Boolean,
    CheckConstraint,
    Column,
    Date,
    ForeignKey,
    Integer,
    JSON,
    Numeric,
    String,
    TIMESTAMP,
    UniqueConstraint,
)
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
    is_active = Column(Boolean, nullable=False, default=True, server_default="true")
    token_version = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())


# Shared login limits survive process restarts without storing raw identifiers.
class LoginAttemptBucket(Base):
    __tablename__ = "login_attempt_buckets"
    __table_args__ = (CheckConstraint("attempts > 0", name="login_attempt_positive"),)

    bucket_key = Column(String(64), primary_key=True)
    window_start = Column(BigInteger, nullable=False, index=True)
    attempts = Column(Integer, nullable=False)


# One shop-wide ceiling; individual accepted orders keep their recorded prices.
class DiscountPolicy(Base):
    __tablename__ = "discount_policies"
    __table_args__ = (
        CheckConstraint("id = 1", name="discount_policy_singleton"),
        CheckConstraint("employee_max_discount_percent >= 0 AND employee_max_discount_percent <= 100", name="discount_policy_percent_bounds"),
        CheckConstraint("revision >= 0", name="discount_policy_revision_bounds"),
    )

    id = Column(Integer, primary_key=True)
    employee_max_discount_percent = Column(Numeric(5, 2), nullable=False, default=0, server_default="0")
    revision = Column(Integer, nullable=False, default=0, server_default="0")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)


# Policy changes are attributed and replayable even after a later owner edit.
class DiscountPolicyChange(Base):
    __tablename__ = "discount_policy_changes"

    id = Column(Integer, primary_key=True)
    policy_id = Column(Integer, ForeignKey("discount_policies.id", ondelete="RESTRICT"), nullable=False)
    before_percent = Column(Numeric(5, 2), nullable=False)
    after_percent = Column(Numeric(5, 2), nullable=False)
    revision = Column(Integer, nullable=False)
    request_key = Column(String(36), unique=True, nullable=False)
    request_hash = Column(String(64), nullable=False)
    confirmed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    policy = relationship("DiscountPolicy")


# Private shop setup preferences; email is never an authentication permission.
class AlertSettings(Base):
    __tablename__ = "alert_settings"
    __table_args__ = (
        CheckConstraint("id = 1", name="alert_settings_singleton"),
        CheckConstraint("backup_minute >= 0 AND backup_minute < 1440", name="alert_backup_minute_bounds"),
        CheckConstraint("revision >= 0", name="alert_settings_revision_bounds"),
    )

    id = Column(Integer, primary_key=True)
    owner_email = Column(String(254), nullable=True)
    backup_minute = Column(Integer, nullable=False, default=1320, server_default="1320")
    revision = Column(Integer, nullable=False, default=0, server_default="0")
    updated_at = Column(TIMESTAMP(timezone=True), nullable=True)

    @property
    def backup_time(self):
        return f"{self.backup_minute // 60:02d}:{self.backup_minute % 60:02d}"


# Contacts are private; changing them does not enable a delivery provider or scheduler.
class AlertSettingsChange(Base):
    __tablename__ = "alert_settings_changes"

    id = Column(Integer, primary_key=True)
    settings_id = Column(Integer, ForeignKey("alert_settings.id", ondelete="RESTRICT"), nullable=False)
    before_email = Column(String(254), nullable=True)
    after_email = Column(String(254), nullable=False)
    before_backup_minute = Column(Integer, nullable=False)
    after_backup_minute = Column(Integer, nullable=False)
    revision = Column(Integer, nullable=False)
    request_key = Column(String(36), unique=True, nullable=False)
    request_hash = Column(String(64), nullable=False)
    confirmed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    settings = relationship("AlertSettings")

    @property
    def before_backup_time(self):
        return f"{self.before_backup_minute // 60:02d}:{self.before_backup_minute % 60:02d}"

    @property
    def after_backup_time(self):
        return f"{self.after_backup_minute // 60:02d}:{self.after_backup_minute % 60:02d}"


# Customer records
class Customer(Base):
    __tablename__ = "customers"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    phone = Column(String(20), nullable=False)
    phone_normalized = Column(String(12), nullable=True, index=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    corrections = relationship(
        "CustomerCorrection",
        back_populates="customer",
        cascade="all, delete-orphan",
        order_by="CustomerCorrection.id",
    )


# Name/phone edits keep the old contact values for the owner audit.
class CustomerCorrection(Base):
    __tablename__ = "customer_corrections"

    id = Column(Integer, primary_key=True, index=True)
    customer_id = Column(Integer, ForeignKey("customers.id", ondelete="CASCADE"), nullable=False)
    before_state = Column(JSON, nullable=False)
    after_state = Column(JSON, nullable=False)
    reason = Column(String(300), nullable=False)
    shared_phone_confirmed = Column(Boolean, nullable=False, default=False)
    request_key = Column(String(36), unique=True, nullable=True)
    request_hash = Column(String(64), nullable=True)
    confirmed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    customer = relationship("Customer", back_populates="corrections")


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
    order_date = Column(Date, nullable=False, server_default=func.current_date())
    discount_reason = Column(String(120), nullable=True)
    discounted_by_username = Column(String(50), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    promised_ready_at = Column(TIMESTAMP(timezone=True), nullable=True)
    peak_delay_minutes = Column(Integer, nullable=False, default=0)
    ready_at = Column(TIMESTAMP(timezone=True), nullable=True)
    collected_at = Column(TIMESTAMP(timezone=True), nullable=True)
    request_key = Column(String(36), unique=True, nullable=True)
    request_hash = Column(String(64), nullable=True)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    next_garment_number = Column(Integer, nullable=False, default=1, server_default="1")

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
    payment_adjustments = relationship(
        "PaymentAdjustment",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="PaymentAdjustment.id",
    )
    corrections = relationship(
        "OrderCorrection",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderCorrection.id",
    )
    holds = relationship(
        "OrderHold",
        back_populates="order",
        cascade="all, delete-orphan",
        order_by="OrderHold.id",
    )

    # Payment totals are derived from history so staff never type over a balance.
    @property
    def amount_paid(self):
        payments_total = sum(
            (Decimal(str(payment.amount)) for payment in self.payments),
            Decimal("0"),
        )
        adjustments_total = sum(
            (Decimal(str(adjustment.amount)) for adjustment in self.payment_adjustments),
            Decimal("0"),
        )
        return payments_total - adjustments_total

    @property
    def service_refunds(self):
        return sum(
            (Decimal(str(item.amount)) for item in self.payment_adjustments
             if item.kind == "refund" and item.refund_purpose == "service_refund"),
            Decimal("0"),
        )

    @property
    def net_charge(self):
        if self.status == "cancelled":
            return Decimal("0")
        return Decimal(str(self.total_price)) - self.service_refunds

    @property
    def refund_due(self):
        return max(self.amount_paid - self.net_charge, Decimal("0"))

    @property
    def balance_due(self):
        balance = self.net_charge - self.amount_paid
        return max(balance, Decimal("0"))

    @property
    def payment_status(self):
        if self.status == "cancelled":
            return "cancelled"
        if self.refund_due > 0:
            return "refund_due"
        if self.net_charge == 0:
            return "settled"
        if self.amount_paid <= 0:
            return "unpaid"
        if self.balance_due > 0:
            return "part_paid"
        return "paid"

    @property
    def subtotal_before_discount(self):
        if self.service_lines:
            return sum(
                (Decimal(str(line.subtotal)) for line in self.service_lines),
                Decimal("0"),
            )
        return Decimal(str(self.total_price))

    @property
    def discount_amount(self):
        return sum(
            (Decimal(str(line.discount_amount)) for line in self.service_lines),
            Decimal("0"),
        )


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
    discount_amount = Column(Numeric(10, 2), nullable=False, default=0)
    fixed_item_type_id = Column(
        Integer,
        ForeignKey("clothing_item_types.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_recording_mode = Column(String(20), nullable=False)
    outsourcing_required = Column(Boolean, nullable=False, default=False, server_default="false")
    in_house_reason = Column(String(300), nullable=True)
    in_house_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    in_house_by_username = Column(String(50), nullable=True)
    in_house_at = Column(TIMESTAMP(timezone=True), nullable=True)
    item_check_status = Column(String(20), nullable=False, default="not_required")
    item_revision = Column(Integer, nullable=False, default=0, server_default="0")
    item_checked_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    item_checked_by_username = Column(String(50), nullable=True)
    item_checked_at = Column(TIMESTAMP(timezone=True), nullable=True)

    order = relationship("Order", back_populates="service_lines")
    items = relationship(
        "OrderItem",
        back_populates="service_line",
        cascade="all, delete-orphan",
        order_by="OrderItem.id",
    )
    item_history = relationship(
        "OrderItemCheckHistory",
        back_populates="service_line",
        cascade="all, delete-orphan",
        order_by="OrderItemCheckHistory.revision",
    )
    outsourcing_handover = relationship(
        "OutsourceHandover",
        back_populates="service_line",
        cascade="all, delete-orphan",
        uselist=False,
    )

    @property
    def line_total(self):
        return Decimal(str(self.subtotal)) - Decimal(str(self.discount_amount))


# Clothing counted or identified under one particular order service.
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(Integer, primary_key=True, index=True)
    garment_reference = Column(String(50), unique=True, nullable=True, index=True)
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
    exceptions = relationship(
        "OrderItemException",
        back_populates="order_item",
        cascade="all, delete-orphan",
        order_by="OrderItemException.id",
    )
    outsourcing_record = relationship(
        "OutsourceHandoverItem",
        back_populates="order_item",
        uselist=False,
    )


# One affected piece inside a quick tally. It adds detail without changing the count.
class OrderItemException(Base):
    __tablename__ = "order_item_exceptions"
    __table_args__ = (
        CheckConstraint(
            "description IS NOT NULL OR is_damaged OR stain_note IS NOT NULL",
            name="order_item_exception_has_detail",
        ),
        CheckConstraint(
            "NOT is_damaged OR damage_note IS NOT NULL",
            name="order_item_exception_damage_has_note",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_item_id = Column(
        Integer,
        ForeignKey("order_items.id", ondelete="CASCADE"),
        nullable=False,
    )
    description = Column(String(200), nullable=True)
    is_damaged = Column(Boolean, nullable=False, default=False)
    damage_note = Column(String(300), nullable=True)
    stain_note = Column(String(300), nullable=True)

    order_item = relationship("OrderItem", back_populates="exceptions")


# Immutable snapshots preserve what staff recorded at every clothing-check revision.
class OrderItemCheckHistory(Base):
    __tablename__ = "order_item_check_history"
    __table_args__ = (
        UniqueConstraint(
            "order_service_line_id",
            "revision",
            name="uq_item_check_history_line_revision",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_service_line_id = Column(
        Integer,
        ForeignKey("order_service_lines.id", ondelete="CASCADE"),
        nullable=False,
    )
    revision = Column(Integer, nullable=False)
    check_status = Column(String(20), nullable=False)
    item_snapshot = Column(JSON, nullable=False)
    changed_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    changed_by_username = Column(String(50), nullable=False)
    change_reason = Column(String(200), nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    service_line = relationship("OrderServiceLine", back_populates="item_history")


# One attributed dispatch of a detailed service to an outside cleaner.
class OutsourceHandover(Base):
    __tablename__ = "outsource_handovers"

    id = Column(Integer, primary_key=True, index=True)
    order_service_line_id = Column(
        Integer,
        ForeignKey("order_service_lines.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    partner_name = Column(String(100), nullable=False)
    expected_return_at = Column(TIMESTAMP(timezone=True), nullable=False)
    sent_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    sent_by_username = Column(String(50), nullable=False)
    sent_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    service_line = relationship("OrderServiceLine", back_populates="outsourcing_handover")
    items = relationship(
        "OutsourceHandoverItem",
        back_populates="handover",
        cascade="all, delete-orphan",
        order_by="OutsourceHandoverItem.id",
    )

    @property
    def outstanding_count(self):
        return sum(item.returned_at is None for item in self.items)

    @property
    def unresolved_issue_count(self):
        return sum(
            item.return_condition == "issue" and item.issue_resolved_at is None
            for item in self.items
        )


# Return state is stored per physical garment so partial returns remain visible.
class OutsourceHandoverItem(Base):
    __tablename__ = "outsource_handover_items"
    __table_args__ = (
        CheckConstraint(
            "(returned_at IS NULL AND returned_by_username IS NULL "
            "AND return_condition IS NULL AND issue_note IS NULL) OR "
            "(returned_at IS NOT NULL AND returned_by_username IS NOT NULL "
            "AND return_condition IN ('returned_ok', 'issue') "
            "AND ((return_condition = 'returned_ok' AND issue_note IS NULL) "
            "OR (return_condition = 'issue' AND issue_note IS NOT NULL)))",
            name="outsource_return_state_complete",
        ),
        CheckConstraint(
            "(issue_resolved_at IS NULL AND issue_resolved_by_username IS NULL "
            "AND resolution_note IS NULL) OR "
            "(issue_resolved_at IS NOT NULL AND issue_resolved_by_username IS NOT NULL "
            "AND resolution_note IS NOT NULL AND return_condition = 'issue')",
            name="outsource_issue_resolution_complete",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    handover_id = Column(
        Integer,
        ForeignKey("outsource_handovers.id", ondelete="CASCADE"),
        nullable=False,
    )
    order_item_id = Column(
        Integer,
        ForeignKey("order_items.id", ondelete="RESTRICT"),
        nullable=False,
        unique=True,
    )
    garment_reference = Column(String(50), nullable=False)
    returned_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    returned_by_username = Column(String(50), nullable=True)
    returned_at = Column(TIMESTAMP(timezone=True), nullable=True)
    return_condition = Column(String(20), nullable=True)
    issue_note = Column(String(300), nullable=True)
    issue_resolved_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    issue_resolved_by_username = Column(String(50), nullable=True)
    issue_resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)
    resolution_note = Column(String(300), nullable=True)

    handover = relationship("OutsourceHandover", back_populates="items")
    order_item = relationship("OrderItem", back_populates="outsourcing_record")


# An unresolved customer question pauses work without hiding why it was paused.
class OrderHold(Base):
    __tablename__ = "order_holds"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(
        Integer,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
    )
    hold_type = Column(String(30), nullable=False, default="customer_reply")
    reason = Column(String(300), nullable=False)
    created_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())
    resolved_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    resolved_by_username = Column(String(50), nullable=True)
    resolution_note = Column(String(300), nullable=True)
    resolved_at = Column(TIMESTAMP(timezone=True), nullable=True)

    order = relationship("Order", back_populates="holds")


# Append-only payment history confirmed by a staff member at the shop.
class Payment(Base):
    __tablename__ = "payments"

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    payment_method = Column(String(20), nullable=False)
    amount = Column(Numeric(10, 2), nullable=False)
    request_key = Column(String(36), unique=True, nullable=True)
    request_hash = Column(String(64), nullable=True)
    confirmed_by_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    confirmed_by_username = Column(String(50), nullable=False)
    received_date = Column(Date, nullable=False, server_default=func.current_date())
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())

    order = relationship("Order", back_populates="payments")
    adjustments = relationship(
        "PaymentAdjustment",
        back_populates="payment",
        cascade="all, delete-orphan",
        order_by="PaymentAdjustment.id",
    )


# A linked adjustment never edits the original receipt of money.
class PaymentAdjustment(Base):
    __tablename__ = "payment_adjustments"
    __table_args__ = (
        CheckConstraint("amount > 0", name="payment_adjustment_positive"),
        CheckConstraint(
            "kind IN ('entry_error', 'refund')",
            name="payment_adjustment_kind",
        ),
        CheckConstraint(
            "(kind = 'entry_error' AND refund_method IS NULL) "
            "OR (kind = 'refund' AND refund_method IN ('cash', 'mpesa'))",
            name="payment_adjustment_refund_method",
        ),
        CheckConstraint(
            "refund_purpose IS NULL OR (kind = 'refund' AND "
            "refund_purpose IN ('service_refund', 'excess_payment'))",
            name="payment_adjustment_refund_purpose",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    payment_id = Column(Integer, ForeignKey("payments.id", ondelete="CASCADE"), nullable=False)
    kind = Column(String(20), nullable=False)
    refund_method = Column(String(20), nullable=True)
    # NULL on older events means unknown; migration must not invent a purpose.
    refund_purpose = Column(String(20), nullable=True)
    amount = Column(Numeric(10, 2), nullable=False)
    reason = Column(String(300), nullable=False)
    effective_date = Column(Date, nullable=False)
    request_key = Column(String(36), unique=True, nullable=True)
    request_hash = Column(String(64), nullable=True)
    confirmed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    order = relationship("Order", back_populates="payment_adjustments")
    payment = relationship("Payment", back_populates="adjustments")


# Owner-only stage and cancellation events keep the state that existed before.
class OrderCorrection(Base):
    __tablename__ = "order_corrections"
    __table_args__ = (
        CheckConstraint(
            "action IN ('stage_back', 'cancel', 'quantity', 'customer_reassign')",
            name="order_correction_action",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    order_id = Column(Integer, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(20), nullable=False)
    before_state = Column(JSON, nullable=False)
    after_state = Column(JSON, nullable=False)
    reason = Column(String(300), nullable=False)
    goods_returned_confirmed = Column(Boolean, nullable=False, default=False)
    still_in_shop_confirmed = Column(Boolean, nullable=False, default=False)
    request_key = Column(String(36), unique=True, nullable=True)
    request_hash = Column(String(64), nullable=True)
    confirmed_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    confirmed_by_username = Column(String(50), nullable=False)
    created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=func.now())

    order = relationship("Order", back_populates="corrections")


# One counter per business date, locked while a ticket number is allocated.
class TicketCounter(Base):
    __tablename__ = "ticket_counters"
    ticket_date = Column(Date, primary_key=True)
    last_number = Column(Integer, nullable=False)
