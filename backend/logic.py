# logic.py
# Business logic kept separate from main.py so it can be unit-tested directly with pytest.

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import models

# PLACEHOLDER RATES — replace with real prices from the owner interview.
PRICING = {
    "wash_fold": 150,      # KES per kg
    "duvet": 600,          # KES per duvet
    "dry_cleaning": 400,   # KES per item
}

# How many days an order can sit in 'ready' status before it's considered overdue
OVERDUE_THRESHOLD_DAYS = 7

# Calculates unit price and total price for an order
def calculate_price(service_type: str, quantity: float):
    unit_price = PRICING[service_type]
    total_price = unit_price * quantity
    return unit_price, total_price


# Generates a unique ticket number in the format QL-YYYYMMDD-###
def generate_ticket_number(db: Session) -> str:
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")

    count_today = db.query(models.Order).filter(
        models.Order.ticket_number.like(f"QL-{today_str}-%")
    ).count()

    next_number = count_today + 1
    return f"QL-{today_str}-{next_number:03d}"


# Returns the cutoff timestamp — any 'ready' order at or before this point is overdue
def get_overdue_cutoff():
    return datetime.now(timezone.utc) - timedelta(days=OVERDUE_THRESHOLD_DAYS)
