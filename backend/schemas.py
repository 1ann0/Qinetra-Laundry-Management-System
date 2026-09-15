# schemas.py
# Validates data coming in/out of the API. Kept separate from models.py.

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import date, datetime
from typing import Any, Literal, Optional
from decimal import Decimal


def check_quantity_precision(value):
    if Decimal(str(value)) * 100 != (Decimal(str(value)) * 100).to_integral_value():
        raise ValueError("Use at most two decimal places for the quantity")
    return value

# Data required to create a customer
class CustomerCreate(BaseModel):
    name: str
    phone: str

# Data returned after creating/fetching a customer
class CustomerOut(BaseModel):
    id: int
    name: str
    phone: str
    created_at: datetime

    class Config:
        from_attributes = True

# Response returned specifically after creating a customer.
# Includes a warning if the phone number was already linked to an existing customer.
class CustomerCreateResponse(BaseModel):
    customer: CustomerOut
    duplicate_warning: Optional[str] = None


# Data required when the owner adds a laundry service.
class ServiceCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    unit: Literal["kg", "item", "pair"]
    unit_price: float = Field(gt=0)
    category: Literal["general", "dry_cleaning"] = "general"
    default_item_type_id: Optional[int] = Field(default=None, gt=0)
    item_recording_mode: Literal["none", "tally", "detailed"] = "none"
    turnaround_minutes: Optional[int] = Field(default=None, gt=0, le=525600)

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Service name cannot be blank")
        return cleaned

    @model_validator(mode="after")
    def check_detailed_service_unit(self):
        if self.item_recording_mode == "detailed" and self.unit == "kg":
            raise ValueError("Detailed garment services must use item or pair pricing")
        if (
            self.category == "dry_cleaning"
            and self.item_recording_mode == "detailed"
            and self.default_item_type_id is None
        ):
            raise ValueError("Select the garment linked to this Dry Cleaning service")
        if (
            self.default_item_type_id is not None
            and self.item_recording_mode != "detailed"
        ):
            raise ValueError("A linked garment requires individual garment details")
        return self


# Optional fields the owner can change on an existing service.
class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    unit: Optional[Literal["kg", "item", "pair"]] = None
    unit_price: Optional[float] = Field(default=None, gt=0)
    category: Optional[Literal["general", "dry_cleaning"]] = None
    default_item_type_id: Optional[int] = Field(default=None, gt=0)
    item_recording_mode: Optional[Literal["none", "tally", "detailed"]] = None
    turnaround_minutes: Optional[int] = Field(default=None, gt=0, le=525600)
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: Optional[str]):
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Service name cannot be blank")
        return cleaned


# Service information returned to the frontend.
class ServiceOut(BaseModel):
    id: int
    code: str
    name: str
    unit: str
    unit_price: float
    category: str
    default_item_type_id: Optional[int]
    item_recording_mode: str
    turnaround_minutes: int
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Data required when an authorised user adds a clothing item name.
class ClothingItemTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    item_group: Literal["laundry", "dry_cleaning", "both"] = "laundry"

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: str):
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Clothing item name cannot be blank")
        return cleaned


# Optional fields the owner can change on an existing clothing item.
class ClothingItemTypeUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    item_group: Optional[Literal["laundry", "dry_cleaning", "both"]] = None
    is_active: Optional[bool] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, value: Optional[str]):
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("Clothing item name cannot be blank")
        return cleaned


# Clothing item information returned to the frontend.
class ClothingItemTypeOut(BaseModel):
    id: int
    name: str
    item_group: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Data required to create an order
class OrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    service_type: Literal[
        "wash_fold",
        "duvet",
        "dry_cleaning_shirt",
        "dry_cleaning_trouser",
        "dry_cleaning_suit",
    ]
    quantity: float = Field(gt=0, allow_inf_nan=False)
    promised_ready_at: Optional[datetime] = None
    peak_delay_minutes: Literal[0, 60] = 0

    _quantity_precision = field_validator("quantity")(check_quantity_precision)


# One damaged or heavily stained piece inside a quick tally.
class OrderItemExceptionCreate(BaseModel):
    description: Optional[str] = Field(default=None, max_length=200)
    is_damaged: bool = False
    damage_note: Optional[str] = Field(default=None, max_length=300)
    stain_note: Optional[str] = Field(default=None, max_length=300)

    @field_validator("description", "damage_note", "stain_note")
    @classmethod
    def clean_optional_text(cls, value: Optional[str]):
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None

    @model_validator(mode="after")
    def require_condition_detail(self):
        if self.is_damaged and not self.damage_note:
            raise ValueError("Describe the existing damage")
        if not any([
            self.description,
            self.is_damaged,
            self.stain_note,
        ]):
            raise ValueError("Describe the affected item, damage or stain")
        return self


# One clothing entry under a selected service.
# Tally services can use a quantity; detailed garments are saved one at a time.
class OrderItemCreate(BaseModel):
    item_type_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    description: Optional[str] = Field(default=None, max_length=200)
    is_damaged: Optional[bool] = None
    damage_note: Optional[str] = Field(default=None, max_length=300)
    stain_note: Optional[str] = Field(default=None, max_length=300)
    exceptions: list[OrderItemExceptionCreate] = Field(default_factory=list)

    @field_validator("description", "damage_note", "stain_note")
    @classmethod
    def clean_optional_text(cls, value: Optional[str]):
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


# One service selected for a mixed order, including any items recorded now.
class DetailedOrderServiceCreate(BaseModel):
    service_id: int = Field(gt=0)
    quantity: float = Field(gt=0, allow_inf_nan=False)
    discount_amount: float = Field(default=0, ge=0, allow_inf_nan=False)
    items: list[OrderItemCreate] = Field(default_factory=list)

    _quantity_precision = field_validator("quantity")(check_quantity_precision)


# The same confirmation/date rules apply to initial and later payments.
class PaymentCreate(BaseModel):
    payment_method: Literal["cash", "mpesa"]
    amount: float = Field(gt=0, allow_inf_nan=False)
    confirmed: bool
    received_date: Optional[date] = None


class InitialPaymentCreate(PaymentCreate):
    # Null means the full price calculated by the backend for this new order.
    amount: Optional[float] = Field(default=None, gt=0, allow_inf_nan=False)


# New order format used by the mixed-service employee workflow.
class DetailedOrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    services: list[DetailedOrderServiceCreate] = Field(min_length=1)
    order_date: Optional[date] = None
    discount_reason: Optional[str] = Field(default=None, max_length=120)
    promised_ready_at: Optional[datetime] = None
    peak_delay_minutes: Literal[0, 60] = 0
    initial_payment: Optional[InitialPaymentCreate] = None

    @model_validator(mode="after")
    def prevent_duplicate_services(self):
        service_ids = [service.service_id for service in self.services]
        if len(service_ids) != len(set(service_ids)):
            raise ValueError("Select each service only once per order")
        self.discount_reason = (
            self.discount_reason.strip() if self.discount_reason else None
        )
        if any(service.discount_amount > 0 for service in self.services):
            if not self.discount_reason:
                raise ValueError("Enter a reason for the discount")
        else:
            self.discount_reason = None
        return self


# Condition exception returned under one tally item.
class OrderItemExceptionOut(BaseModel):
    id: int
    description: Optional[str]
    is_damaged: bool
    damage_note: Optional[str]
    stain_note: Optional[str]

    class Config:
        from_attributes = True


# Clothing data returned as part of an individual order receipt.
class OrderItemOut(BaseModel):
    id: int
    item_type_id: int
    item_name: str
    quantity: int
    description: Optional[str]
    is_damaged: Optional[bool]
    damage_note: Optional[str]
    stain_note: Optional[str]
    exceptions: list[OrderItemExceptionOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# One immutable clothing-check revision shown in the audit history.
class OrderItemCheckHistoryOut(BaseModel):
    id: int
    revision: int
    check_status: str
    item_snapshot: list[dict[str, Any]]
    changed_by_username: str
    change_reason: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# A saved service line with its price snapshot and item-check progress.
class OrderServiceLineOut(BaseModel):
    id: int
    service_id: int
    service_name: str
    service_unit: str
    quantity: float
    unit_price: float
    subtotal: float
    discount_amount: float
    line_total: float
    fixed_item_type_id: Optional[int]
    item_recording_mode: str
    item_check_status: str
    item_revision: int
    item_checked_by_username: Optional[str]
    item_checked_at: Optional[datetime]
    items: list[OrderItemOut] = Field(default_factory=list)
    item_history: list[OrderItemCheckHistoryOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Replaces the saved items for one order service when staff return later.
class OrderItemsUpdate(BaseModel):
    items: list[OrderItemCreate] = Field(default_factory=list)
    expected_revision: int = Field(default=0, ge=0)
    change_reason: Optional[str] = Field(default=None, max_length=200)

    @field_validator("change_reason")
    @classmethod
    def clean_change_reason(cls, value: Optional[str]):
        if value is None:
            return value
        cleaned = value.strip()
        return cleaned or None


# Payment history shown on the receipt.
class PaymentOut(BaseModel):
    id: int
    payment_method: str
    amount: float
    confirmed_by_username: str
    received_date: date
    created_at: datetime

    class Config:
        from_attributes = True


# Data required to update an order's status
class OrderStatusUpdate(BaseModel):
    status: Literal["received", "in_progress", "ready", "collected"]

# Data returned after creating/fetching an order
class OrderOut(BaseModel):
    id: int
    ticket_number: str
    customer_id: int
    service_type: str
    quantity: float
    unit_price: float
    subtotal_before_discount: float
    discount_amount: float
    total_price: float
    status: str
    order_date: date
    discount_reason: Optional[str]
    discounted_by_username: Optional[str]
    created_at: datetime
    promised_ready_at: Optional[datetime]
    peak_delay_minutes: int
    ready_at: Optional[datetime]
    collected_at: Optional[datetime]
    service_lines: list[OrderServiceLineOut] = Field(default_factory=list)
    amount_paid: float
    balance_due: float
    payment_status: str
    payments: list[PaymentOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Data returned after login: the JWT itself
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str
    user_id: int
    username: str

# Data required to create a new employee account (owner-only action)
def validate_account_password(value: str) -> str:
    if not value.strip():
        raise ValueError("Password cannot be blank")
    if len(value.encode("utf-8")) > 72:
        raise ValueError("Password must be at most 72 bytes")
    return value


class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    password: str = Field(min_length=8)
    role: Literal["owner", "employee"]

    @field_validator("username", mode="before")
    @classmethod
    def clean_username(cls, value):
        return value.strip() if isinstance(value, str) else value

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str):
        return validate_account_password(value)


# Account-safety changes are kept as separate requests so each action is clear.
class UserStatusUpdate(BaseModel):
    is_active: bool


class UserRoleUpdate(BaseModel):
    role: Literal["owner", "employee"]


class UserPasswordReset(BaseModel):
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def check_password(cls, value: str):
        return validate_account_password(value)

# Data returned when listing/confirming a user (never includes the password)
class UserOut(BaseModel):
    id: int
    username: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True

# Data returned by the dashboard: order counts by status, plus overdue count
class DashboardSummary(BaseModel):
    received: int
    in_progress: int
    ready: int
    collected: int
    overdue: int
    unpaid: int
    outstanding_balance: float


# Money received on one Nairobi calendar day.
class DailyReceivedTotal(BaseModel):
    date: date
    amount: float


# Confirmed payments linked to one customer during the selected period.
class CustomerRevenue(BaseModel):
    customer_id: int
    customer_name: str
    customer_phone: str
    total_received: float


# Work booked under one service during the selected period.
class TopServiceBooking(BaseModel):
    service_id: Optional[int] = None
    service_name: str
    service_unit: str
    order_count: int
    quantity_booked: float
    booked_value: float


# Owner-only money snapshot for one inclusive Nairobi calendar date range.
class FinancialSummary(BaseModel):
    start_date: date
    end_date: date
    orders_booked: int
    gross_order_value: float
    discounts_given: float
    order_value: float
    cash_received: float
    mpesa_received: float
    total_received: float
    outstanding_orders: int
    outstanding_balance: float
    daily_received: list[DailyReceivedTotal]
    customer_revenue: list[CustomerRevenue]
    top_services: list[TopServiceBooking]
