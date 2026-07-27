# schemas.py
# Validates data coming in/out of the API. Kept separate from models.py.

from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime
from typing import Literal, Optional

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
    item_recording_mode: Literal["none", "tally", "detailed"] = "none"

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
        return self


# Optional fields the owner can change on an existing service.
class ServiceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=100)
    unit: Optional[Literal["kg", "item", "pair"]] = None
    unit_price: Optional[float] = Field(default=None, gt=0)
    item_recording_mode: Optional[Literal["none", "tally", "detailed"]] = None
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
    item_recording_mode: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Data required when the owner adds a clothing item name.
class ClothingItemTypeCreate(BaseModel):
    name: str = Field(min_length=1, max_length=100)

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
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Data required to create an order
class OrderCreate(BaseModel):
    customer_id: int
    service_type: Literal[
        "wash_fold",
        "duvet",
        "dry_cleaning_shirt",
        "dry_cleaning_trouser",
        "dry_cleaning_suit",
    ]
    quantity: float


# One clothing entry under a selected service.
# Tally services can use a quantity; detailed garments are saved one at a time.
class OrderItemCreate(BaseModel):
    item_type_id: int = Field(gt=0)
    quantity: int = Field(default=1, gt=0)
    description: Optional[str] = Field(default=None, max_length=200)
    is_damaged: Optional[bool] = None
    damage_note: Optional[str] = Field(default=None, max_length=300)
    stain_note: Optional[str] = Field(default=None, max_length=300)

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
    quantity: float = Field(gt=0)
    items: list[OrderItemCreate] = Field(default_factory=list)


# New order format used by the mixed-service employee workflow.
class DetailedOrderCreate(BaseModel):
    customer_id: int = Field(gt=0)
    services: list[DetailedOrderServiceCreate] = Field(min_length=1)

    @model_validator(mode="after")
    def prevent_duplicate_services(self):
        service_ids = [service.service_id for service in self.services]
        if len(service_ids) != len(set(service_ids)):
            raise ValueError("Select each service only once per order")
        return self


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
    item_recording_mode: str
    item_check_status: str
    items: list[OrderItemOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Replaces the saved items for one order service when staff return later.
class OrderItemsUpdate(BaseModel):
    items: list[OrderItemCreate] = Field(default_factory=list)


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
    total_price: float
    status: str
    created_at: datetime
    ready_at: Optional[datetime]
    collected_at: Optional[datetime]
    service_lines: list[OrderServiceLineOut] = Field(default_factory=list)

    class Config:
        from_attributes = True


# Data returned after login: the JWT itself
class Token(BaseModel):
    access_token: str
    token_type: str
    role: str

# Data required to create a new employee account (owner-only action)
class UserCreate(BaseModel):
    username: str
    password: str
    role: Literal["owner", "employee"]

# Data returned when listing/confirming a user (never includes the password)
class UserOut(BaseModel):
    id: int
    username: str
    role: str
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
