# schemas.py
# Validates data coming in/out of the API. Kept separate from models.py.

from pydantic import BaseModel
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
