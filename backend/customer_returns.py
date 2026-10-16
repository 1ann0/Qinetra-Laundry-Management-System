"""Recorded intake days support Owner follow-up; no messages or customer records are written."""
from datetime import timedelta
from fastapi import HTTPException
from sqlalchemy import and_, case, func, or_
import models
from customer_phone import phone_search_digits
from owner_reports import bounded, columns, NAIROBI

GROUPS = {"recent", "7_29", "30_89", "90_plus", "never"}


def extend_return_report(db, result, section, start_date, end_date, return_group, search, now):
    if return_group and return_group not in GROUPS:
        raise HTTPException(422, "Choose a customer return group")
    if search is not None and len(search) > 100:
        raise HTTPException(422, "Keep customer search to 100 characters")
    today = now.astimezone(NAIROBI).date()
    period = [True]
    if start_date:
        period.append(models.Order.order_date >= start_date)
    if end_date:
        period.append(models.Order.order_date <= end_date)
    visits = db.query(models.Order.customer_id.label("customer_id"),
        func.min(models.Order.order_date).label("first_visit"), func.max(models.Order.order_date).label("last_visit"),
        func.count(func.distinct(models.Order.order_date)).label("visits"),
        func.count(func.distinct(case((and_(*period), models.Order.order_date)))).label("period_visits"),
        func.sum(case((models.Order.status.notin_(["collected", "cancelled"]), 1), else_=0)).label("open_orders"),
    ).filter(models.Order.status != "cancelled", models.Order.order_date <= today).group_by(models.Order.customer_id).subquery()
    query = db.query(models.Customer, visits.c.first_visit, visits.c.last_visit, visits.c.visits,
        visits.c.period_visits, visits.c.open_orders).outerjoin(visits, visits.c.customer_id == models.Customer.id)
    if search and search.strip():
        term = search.strip().lower()
        conditions = [func.lower(models.Customer.name).contains(term, autoescape=True), models.Customer.phone.contains(term, autoescape=True)]
        digits = phone_search_digits(search)
        if digits:
            conditions.append(models.Customer.phone_normalized.contains(digits, autoescape=True))
        query = query.filter(or_(*conditions))
    customers = bounded(query.order_by(visits.c.last_visit, models.Customer.name, models.Customer.id))
    rows = []
    summary = dict.fromkeys(("matching_customers", "new_this_week", "new_this_month", "new_in_period", "repeat_in_period"), 0)
    monday = today - timedelta(days=today.weekday())
    for customer, first, last, count, period_count, open_count in customers:
        days = (today - last).days if last else None
        group = "never" if days is None else "recent" if days < 7 else "7_29" if days < 30 else "30_89" if days < 90 else "90_plus"
        if return_group and group != return_group:
            continue
        summary["matching_customers"] += 1
        if first:
            summary["new_this_week"] += first >= monday
            summary["new_this_month"] += first >= today.replace(day=1)
            summary["new_in_period"] += (not start_date or first >= start_date) and (not end_date or first <= end_date)
            summary["repeat_in_period"] += bool(period_count and ((start_date and first < start_date) or period_count > 1))
        rows.append({"customer_id": customer.id, "customer_name": customer.name, "customer_phone": customer.phone,
            "first_visit": first.isoformat() if first else "", "last_visit": last.isoformat() if last else "",
            "days_away": days if days is not None else "", "visits": count or 0, "open_orders": open_count or 0,
            "return_group": group, "next_step": "Check their open laundry first." if open_count else
                "No visit recorded yet." if last is None else "Review their history, then follow up personally if welcome."})
    result["summary"] = summary
    result["definitions"] = [
        "A visit is a distinct Nairobi booking date with a non-cancelled order. Payments, collections, profile creation and future bookings are not visits.",
        "First/last visits and days away use all available recorded history as of today. Dates filter new/repeat activity only; return groups remain CURRENT.",
        "New means first recorded visit, not necessarily new to Qinetra before this system. Repeat counts customers with a later visit in the period, once per customer.",
        "Counts apply to the selected search/group. This week starts Monday; this month starts on the first day, both in Nairobi.",
        "Seven days away does not mean a lost customer. Check open laundry and previous services before a personal follow-up. No message is sent by this report.",
    ]
    section("customer_returns", "Customer returns — current last visits", columns(
        ("customer_name","Customer","text"),("customer_phone","Phone","text"),("last_visit","Last visit","date"),
        ("days_away","Days since last visit","number"),("first_visit","First recorded visit","date"),
        ("visits","Recorded visit days","number"),("open_orders","Open orders","number"),
        ("return_group","Return group","text"),("next_step","Suggested next step","text")), rows)
