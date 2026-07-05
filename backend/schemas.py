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


# Data required to create an order
class OrderCreate(BaseModel):
    customer_id: int
    service_type: Literal["wash_fold", "duvet", "dry_cleaning"]
    quantity: float

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
