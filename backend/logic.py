# logic.py
# Business logic kept separate from main.py so it can be unit-tested directly with pytest.

from datetime import date, datetime, timezone, timedelta
from sqlalchemy.orm import Session
from sqlalchemy import case
from sqlalchemy.dialects.postgresql import insert as postgres_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert
from decimal import Decimal, ROUND_HALF_UP
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
    total_price = money(Decimal(str(unit_price)) * Decimal(str(quantity)))
    return unit_price, total_price


def money(value):
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


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
def generate_ticket_number(db: Session, order_date: date | None = None) -> str:
    ticket_date = order_date or datetime.now(timezone(timedelta(hours=3))).date()
    today_str = ticket_date.strftime("%Y%m%d")

    existing_tickets = db.query(models.Order.ticket_number).filter(
        models.Order.ticket_number.like(f"QL-{today_str}-%")
    ).all()
    existing_numbers = [
        int(ticket.rsplit("-", 1)[1]) for (ticket,) in existing_tickets
        if ticket.rsplit("-", 1)[1].isdigit()
    ]
    first_number = max(existing_numbers, default=0) + 1
    insert = postgres_insert if db.bind.dialect.name == "postgresql" else sqlite_insert
    counter = models.TicketCounter
    statement = insert(counter).values(ticket_date=ticket_date, last_number=first_number)
    # The upsert locks this date's counter across all API workers.
    statement = statement.on_conflict_do_update(
        index_elements=[counter.ticket_date],
        set_={"last_number": case(
            (counter.last_number < first_number, first_number),
            else_=counter.last_number + 1,
        )},
    ).returning(counter.last_number)
    next_number = db.execute(statement).scalar_one()
    return f"QL-{today_str}-{next_number:03d}"


# Returns the cutoff timestamp — any 'ready' order at or before this point is overdue
def get_overdue_cutoff():
    return datetime.now(timezone.utc) - timedelta(days=OVERDUE_THRESHOLD_DAYS)
