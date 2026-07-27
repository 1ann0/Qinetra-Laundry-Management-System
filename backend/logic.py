# logic.py
# Business logic kept separate from main.py so it can be unit-tested directly with pytest.

from datetime import datetime, timezone, timedelta
from sqlalchemy.orm import Session
import models

# Rates confirmed for Qinetra Laundry's current service catalogue.
PRICING = {
    "wash_fold": 150,      # KES per kg
    "duvet": 800,          # KES per duvet
    "dry_cleaning_shirt": 350,
    "dry_cleaning_trouser": 350,
    "dry_cleaning_suit": 750,
}

# How many days an order can sit in 'ready' status before it's considered overdue
OVERDUE_THRESHOLD_DAYS = 7

# Calculates unit price and total price for an order
def calculate_price(service_type: str, quantity: float):
    unit_price = PRICING[service_type]
    total_price = unit_price * quantity
    return unit_price, total_price


# Works out whether a selected service still needs its clothing check.
# Detailed services only complete when each priced item has its own record.
def get_item_check_status(
    recording_mode: str,
    service_quantity: float,
    item_quantities: list[int],
) -> str:
    if recording_mode == "none":
        return "not_required"

    if not item_quantities:
        return "pending"

    if recording_mode == "tally":
        return "completed"

    recorded_items = sum(item_quantities)
    return "completed" if recorded_items == service_quantity else "pending"


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
