"""Owner snapshots share calculations across JSON, CSV and Excel; no report writes data."""
import csv
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import io
import json
import re

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select, or_, func, case
from sqlalchemy.orm.attributes import set_committed_value
import xlsxwriter

import models
from response_security import safe_csv_text
from expense_routes import EXPENSE_CATEGORIES, EXPENSE_FUNDING_SOURCES

NAIROBI = timezone(timedelta(hours=3))
MAX_RECORDS = 5000
MAX_ROWS = 20000
MAX_REPORT_BYTES = 10 * 1024 * 1024
REPORTS = {"orders", "customer", "service", "money", "attention", "catalogue", "expenses"}
STATUSES = {"received", "in_progress", "ready", "collected", "cancelled"}
ATTENTION = {"due_today", "production_late", "ready", "overdue", "holds", "outsourcing", "outstanding", "refund_due"}
DEFINITIONS = [
    "Dates are inclusive Nairobi business dates. Orders use booking dates, receipts use received dates and adjustments use effective dates.",
    "Balances, holds and attention are CURRENT at generation, not historical opening or closing balances. Customer balances ignore dates; order/service balances refer to the orders selected by booking filters.",
    "Entry corrections restate the original receipt date. Refunds are separate money-out events on their effective date.",
    "Receipts and net cash movement are not profit. Mixed-order payments and refunds belong to the whole order; no service cash allocation is inferred.",
    "Quantities with different saved units are never added together. Cancelled work is identified separately and excluded from booked-service totals.",
    "This download is an independent snapshot. Spreadsheet edits do not change QLMS; it is not a database backup or certified eTIMS invoice.",
]


def bounded(query):
    rows = query.limit(MAX_RECORDS + 1).all()
    if len(rows) > MAX_RECORDS:
        raise HTTPException(413, "This report is too large. Narrow its filters; nothing has been truncated.")
    return rows


def order_graph(db, query):
    # Bound every source table before materializing related records; never fetch once per order.
    orders = bounded(query.order_by(models.Order.order_date.desc(), models.Order.id.desc()))
    ids = [order.id for order in orders]
    if not ids:
        return orders
    lines = bounded(db.query(models.OrderServiceLine).filter(models.OrderServiceLine.order_id.in_(ids)).order_by(models.OrderServiceLine.id))
    payments = bounded(db.query(models.Payment).filter(models.Payment.order_id.in_(ids)).order_by(models.Payment.received_date, models.Payment.id))
    adjustments = bounded(db.query(models.PaymentAdjustment).filter(models.PaymentAdjustment.order_id.in_(ids)).order_by(models.PaymentAdjustment.effective_date, models.PaymentAdjustment.id))
    holds = bounded(db.query(models.OrderHold).filter(models.OrderHold.order_id.in_(ids), models.OrderHold.resolved_at.is_(None)))
    line_ids = [line.id for line in lines]
    handovers = bounded(db.query(models.OutsourceHandover).filter(models.OutsourceHandover.order_service_line_id.in_(line_ids))) if line_ids else []
    handover_ids = [handover.id for handover in handovers]
    items = bounded(db.query(models.OutsourceHandoverItem).filter(models.OutsourceHandoverItem.handover_id.in_(handover_ids))) if handover_ids else []
    def grouped(rows, field):
        groups = {}
        for row in rows:
            groups.setdefault(getattr(row, field), []).append(row)
        return groups
    adjustments_by_payment = grouped(adjustments, "payment_id")
    for payment in payments:
        set_committed_value(payment, "adjustments", adjustments_by_payment.get(payment.id, []))
    items_by_handover = grouped(items, "handover_id")
    for handover in handovers:
        set_committed_value(handover, "items", items_by_handover.get(handover.id, []))
    by_line = {handover.order_service_line_id: handover for handover in handovers}
    for line in lines:
        set_committed_value(line, "outsourcing_handover", by_line.get(line.id))
    for relationship, rows in [("service_lines", lines), ("payments", payments), ("payment_adjustments", adjustments), ("holds", holds)]:
        groups = grouped(rows, "order_id")
        for order in orders:
            set_committed_value(order, relationship, groups.get(order.id, []))
    return orders


def aware(value):
    return value.replace(tzinfo=timezone.utc) if value is not None and value.tzinfo is None else value


def attention_flags(order, now):
    flags = []
    active = order.status not in {"collected", "cancelled"}
    promised = aware(order.promised_ready_at)
    if active and promised and promised.astimezone(NAIROBI).date() == now.astimezone(NAIROBI).date():
        flags.append("due_today")
    if order.status in {"received", "in_progress"} and promised and promised < now:
        flags.append("production_late")
    if order.status == "ready":
        flags.append("ready")
        if order.ready_at and aware(order.ready_at) <= now - timedelta(days=7):
            flags.append("overdue")
    if active and any(hold.resolved_at is None for hold in order.holds):
        flags.append("holds")
    if active and any(
        (line.outsourcing_required and line.outsourcing_handover is None)
        or (line.outsourcing_handover and (line.outsourcing_handover.unresolved_issue_count
            or (line.outsourcing_handover.outstanding_count and aware(line.outsourcing_handover.expected_return_at) < now)))
        for line in order.service_lines
    ):
        flags.append("outsourcing")
    if order.balance_due > 0:
        flags.append("outstanding")
    if order.refund_due > 0:
        flags.append("refund_due")
    return flags


def columns(*specs):
    return [{"key": key, "label": label, "type": kind} for key, label, kind in specs]


ORDER_COLUMNS = columns(("ticket", "Ticket", "text"), ("customer_name", "Customer", "text"),
    ("customer_phone", "Phone", "text"), ("booking_date", "Booking date", "date"), ("status", "Current status", "text"),
    ("services", "Saved services", "text"), ("promised_ready", "Promised ready (Nairobi)", "text"),
    ("order_value", "Whole order value KES", "money"), ("net_charge", "Current whole order charge KES", "money"),
    ("amount_paid", "Current net whole order payments KES", "money"), ("balance_due", "Current balance KES", "money"),
    ("refund_due", "Current refund due KES", "money"), ("attention", "Current attention", "text"), ("holds", "Unresolved holds", "text"))
RECEIPT_COLUMNS = columns(("ticket", "Ticket", "text"), ("customer_name", "Customer", "text"), ("customer_phone", "Phone", "text"),
    ("date", "Received date", "date"), ("method", "Method", "text"), ("original_amount", "Original receipt KES", "money"),
    ("entry_errors", "Entry corrections KES", "money"), ("amount", "Corrected receipt KES", "money"), ("actor", "Recorded by", "text"))
ADJUSTMENT_COLUMNS = columns(("ticket", "Ticket", "text"), ("customer_name", "Customer", "text"), ("customer_phone", "Phone", "text"),
    ("date", "Effective date", "date"), ("method", "Method", "text"), ("amount", "Amount KES", "money"),
    ("purpose", "Purpose", "text"), ("reason", "Reason", "text"), ("actor", "Recorded by", "text"))


def build_report(db, report_name, *, start_date=None, end_date=None, customer_id=None, service_id=None,
                 status=None, payment_method=None, attention=None, category=None, now=None):
    if report_name not in REPORTS:
        raise HTTPException(404, "Unknown report")
    if start_date and end_date and end_date < start_date:
        raise HTTPException(400, "End date cannot be before start date")
    if status and status not in STATUSES or payment_method and payment_method not in {"cash", "mpesa"}:
        raise HTTPException(422, "Choose a recognized status or payment method")
    if attention and attention not in ATTENTION:
        raise HTTPException(422, "Choose a recognized attention list")
    if category and category not in EXPENSE_CATEGORIES:
        raise HTTPException(422, "Choose a recognized expense category")
    supported = {
        "orders": {"start_date", "end_date", "customer_id", "service_id", "status"},
        "customer": {"start_date", "end_date", "customer_id", "status", "payment_method"},
        "service": {"start_date", "end_date", "service_id", "status", "customer_id"},
        "money": {"start_date", "end_date", "customer_id", "payment_method"},
        "attention": {"customer_id", "service_id", "status", "attention"}, "catalogue": set(),
        "expenses": {"start_date", "end_date", "category", "payment_method"},
    }
    filters = {key: value for key, value in {"start_date": start_date, "end_date": end_date, "customer_id": customer_id,
        "service_id": service_id, "status": status, "payment_method": payment_method, "attention": attention, "category":category}.items() if value is not None}
    if set(filters) - supported[report_name]:
        raise HTTPException(422, "A filter does not apply to this report")
    if report_name == "customer" and customer_id is None or report_name == "service" and service_id is None:
        raise HTTPException(422, "Select the customer or service for this report")
    for model, identifier in [(models.Customer, customer_id), (models.Service, service_id)]:
        if identifier is not None and (identifier <= 0 or db.get(model, identifier) is None):
            raise HTTPException(404, "Selected customer or service was not found")
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Report generation requires a timezone")
    result = {"report": report_name, "generated_at": now.isoformat(), "timezone": "Africa/Nairobi",
              "filters": {key: value.isoformat() if isinstance(value, date) else value for key, value in filters.items()},
              "definitions": DEFINITIONS, "summary": {}, "sections": []}
    def section(key, title, fields, rows):
        result["sections"].append({"key": key, "title": title, "columns": fields, "rows": rows})
        if sum(len(part["rows"]) for part in result["sections"]) > MAX_ROWS:
            raise HTTPException(413, "This report is too large. Narrow its filters; nothing has been truncated.")
    if report_name == "expenses":
        query = db.query(models.Expense)
        if start_date:
            query = query.filter(models.Expense.paid_date >= start_date)
        if end_date:
            query = query.filter(models.Expense.paid_date <= end_date)
        if category:
            query = query.filter(models.Expense.category == category)
        if payment_method:
            query = query.filter(models.Expense.payment_method == payment_method)
        expenses = bounded(query.order_by(models.Expense.paid_date.desc(),models.Expense.id.desc()))
        rows = [{"expense_id":item.id,"paid_date":item.paid_date.isoformat(),"category":item.category,
            "amount":item.amount,"method":item.payment_method,"reference":item.reference,"note":item.note,
            "funding_source":EXPENSE_FUNDING_SOURCES.get(item.funding_source,"Not confirmed"),
            "state":"Reversed" if item.is_voided else "Recorded","actor":item.confirmed_by_username,"revision":item.revision} for item in expenses]
        section("expenses","Expenses on corrected paid dates",columns(("expense_id","Expense","number"),
            ("paid_date","Paid date","date"),("category","Category","text"),("amount","Expense KES","money"),
            ("method","Method","text"),("funding_source","Paid from","text"),("reference","Reference","text"),("note","Note","text"),
            ("state","State","text"),("actor","Recorded by","text"),("revision","Revision","number")),rows)
        ids = [item.id for item in expenses]
        changes = bounded(db.query(models.ExpenseChange).filter(models.ExpenseChange.expense_id.in_(ids),models.ExpenseChange.revision > 0)
            .order_by(models.ExpenseChange.id)) if ids else []
        section("expense_changes","Correction history for selected expenses",columns(("expense_id","Expense","number"),
            ("revision","Revision","number"),("recorded_at","Recorded at (Nairobi)","text"),("reason","Reason","text"),
            ("before","Before details","text"),("after","After details","text"),("actor","Corrected by","text")),
            [{"expense_id":item.expense_id,"revision":item.revision,"recorded_at":aware(item.created_at).astimezone(NAIROBI).isoformat(),
              "reason":item.reason,"before":json.dumps(item.before_details,ensure_ascii=False),"after":json.dumps(item.after_details,ensure_ascii=False),
              "actor":item.confirmed_by_username} for item in changes])
        cash = sum((item.amount for item in expenses if not item.is_voided and item.payment_method == "cash"),Decimal("0"))
        mpesa = sum((item.amount for item in expenses if not item.is_voided and item.payment_method == "mpesa"),Decimal("0"))
        result["summary"] = {"cash_expenses":cash,"mpesa_expenses":mpesa,"total_expenses":cash+mpesa}
        for source, key in (("shop","shop_funded_expenses"),("owner","owner_funded_expenses"),(None,"unconfirmed_funding_expenses")):
            result["summary"][key] = sum((item.amount for item in expenses if not item.is_voided and item.funding_source == source),Decimal("0"))
        result["definitions"] = [*DEFINITIONS,"Expense totals use the current corrected paid date/category/method; reversed expenses stay visible but are excluded. History shows changes to the selected expenses, not a statement of cash on their correction dates. Original details remain available on each expense.",
            "Expenses do not include till additions or Owner withdrawals. Expense totals alone do not establish service margins or profit.",
            "All business costs remain in totals, including personally paid costs. Paid from identifies shop money, Owner's own money or Not confirmed. Cash/M-Pesa identifies the payment method, not the funding source. These are expense totals, not a till reconciliation."]
        return result
    services = bounded(db.query(models.Service).order_by(models.Service.name))
    by_code = {service.code: service for service in services}
    if report_name == "catalogue":
        clothes = bounded(db.query(models.ClothingItemType).order_by(models.ClothingItemType.name))
        clothing_names = {item.id: item.name for item in clothes}
        section("services", "Services", columns(("name", "Service", "text"), ("code", "Code", "text"), ("unit", "Unit", "text"),
            ("price", "Current price KES", "money"), ("active", "Active", "text"), ("category", "Category", "text"),
            ("recording", "Clothing recording", "text"), ("default_clothing", "Default clothing type", "text"), ("turnaround", "Turnaround minutes", "number")),
            [{"name": s.name, "code": s.code, "unit": s.unit, "price": s.unit_price, "active": "Yes" if s.is_active else "No",
              "category": s.category, "recording": s.item_recording_mode,
              "default_clothing": clothing_names.get(s.default_item_type_id, "Not fixed"), "turnaround": s.turnaround_minutes} for s in services])
        section("clothing", "Clothing types", columns(("name", "Clothing type", "text"), ("group", "Group", "text"), ("active", "Active", "text")),
                [{"name": c.name, "group": c.item_group, "active": "Yes" if c.is_active else "No"} for c in clothes])
        return result
    def in_period(value):
        return (start_date is None or value >= start_date) and (end_date is None or value <= end_date)
    def date_query(query, field):
        if start_date:
            query = query.filter(field >= start_date)
        if end_date:
            query = query.filter(field <= end_date)
        return query
    query = db.query(models.Order)
    if customer_id is not None:
        query = query.filter(models.Order.customer_id == customer_id)
    if status:
        query = query.filter(models.Order.status == status)
    if service_id is not None:
        service = db.get(models.Service, service_id)
        query = query.filter(or_(models.Order.service_lines.any(models.OrderServiceLine.service_id == service_id),
            ~models.Order.service_lines.any() & (models.Order.service_type == service.code)))
    if report_name in {"orders", "service"}:
        query = date_query(query, models.Order.order_date)
    if report_name == "money":
        receipts = date_query(select(models.Payment.order_id), models.Payment.received_date)
        adjustments = date_query(select(models.PaymentAdjustment.order_id), models.PaymentAdjustment.effective_date)
        query = query.filter(or_(models.Order.id.in_(receipts), models.Order.id.in_(adjustments)))
    if report_name == "attention":
        # Exclude settled archives before bounding the live queue; closed orders may still owe money.
        paid = select(models.Payment.order_id, func.sum(models.Payment.amount).label("total")).group_by(models.Payment.order_id).subquery()
        adjusted = select(models.PaymentAdjustment.order_id, func.sum(models.PaymentAdjustment.amount).label("total"),
            func.sum(case(((models.PaymentAdjustment.kind == "refund") &
                (models.PaymentAdjustment.refund_purpose == "service_refund"), models.PaymentAdjustment.amount), else_=0)).label("service_refunds")
            ).group_by(models.PaymentAdjustment.order_id).subquery()
        net_paid = func.coalesce(paid.c.total, 0) - func.coalesce(adjusted.c.total, 0)
        net_charge = case((models.Order.status == "cancelled", 0),
            else_=models.Order.total_price - func.coalesce(adjusted.c.service_refunds, 0))
        query = query.outerjoin(paid, paid.c.order_id == models.Order.id).outerjoin(adjusted, adjusted.c.order_id == models.Order.id).filter(
            or_(models.Order.status.notin_(["collected", "cancelled"]), net_charge != net_paid))
    orders = order_graph(db, query)
    customer_ids = {order.customer_id for order in orders}
    customers = bounded(db.query(models.Customer).filter(models.Customer.id.in_(customer_ids))) if customer_ids else []
    by_customer = {customer.id: customer for customer in customers}
    def contact(order):
        customer = by_customer[order.customer_id]
        return {"order_id": order.id, "customer_id": customer.id, "ticket": order.ticket_number,
                "customer_name": customer.name, "customer_phone": customer.phone}
    def order_row(order):
        return {**contact(order), "booking_date": order.order_date.isoformat(), "status": order.status,
            "services": "; ".join(f"{line.service_name}: {line.quantity} {line.service_unit}" for line in order.service_lines) or order.service_type,
            "promised_ready": aware(order.promised_ready_at).astimezone(NAIROBI).isoformat() if order.promised_ready_at else "Not recorded",
            "order_value": Decimal(str(order.total_price)), "net_charge": order.net_charge, "amount_paid": order.amount_paid,
            "balance_due": order.balance_due, "refund_due": order.refund_due,
            "attention": ", ".join(attention_flags(order, now)),
            "holds": "; ".join(hold.reason for hold in order.holds if hold.resolved_at is None)}
    if report_name in {"orders", "customer"}:
        section("orders", "Work booked in selected period", ORDER_COLUMNS, [order_row(o) for o in orders if in_period(o.order_date)])
    if report_name == "service":
        rows = []
        for order in orders:
            if order.status == "cancelled":
                continue
            if order.service_lines:
                rows.extend({**contact(order), "booking_date": order.order_date.isoformat(), "service": line.service_name,
                    "quantity": line.quantity, "unit": line.service_unit, "unit_price": line.unit_price, "booked_value": line.line_total}
                    for line in order.service_lines if line.service_id == service_id)
            else:
                legacy = by_code.get(order.service_type)
                rows.append({**contact(order), "booking_date": order.order_date.isoformat(), "service": legacy.name if legacy else order.service_type,
                    "quantity": order.quantity, "unit": "kg" if order.service_type == "wash_fold" else "item",
                    "unit_price": order.unit_price, "booked_value": order.total_price})
        section("service_lines", "Service work booked", columns(("ticket", "Ticket", "text"), ("customer_name", "Customer", "text"),
            ("booking_date", "Booking date", "date"), ("service", "Saved service", "text"), ("quantity", "Quantity", "number"),
            ("unit", "Saved unit", "text"), ("unit_price", "Saved unit price KES", "money"), ("booked_value", "Booked service value KES", "money")), rows)
        section("related_orders", "Related whole orders — current money", ORDER_COLUMNS, [order_row(order) for order in orders])
        units = {}
        for row in rows:
            units[row["unit"]] = units.get(row["unit"], Decimal("0")) + Decimal(str(row["quantity"]))
        result["summary"] = {"booked_value": sum((Decimal(str(row["booked_value"])) for row in rows), Decimal("0")),
                             **{f"quantity_{unit}": value for unit, value in units.items()}}
    if report_name == "attention":
        rows = [order_row(order) for order in orders if attention_flags(order, now)
                and (not attention or attention in attention_flags(order, now))]
        section("attention", "Current attention — not date-filtered", ORDER_COLUMNS, rows)
        result["summary"] = {flag: sum(flag in row["attention"].split(", ") for row in rows) for flag in sorted(ATTENTION)}
    if report_name in {"customer", "money"}:
        received, refunds, corrections = [], [], []
        for order in orders:
            payments = {payment.id: payment for payment in order.payments}
            for payment in order.payments:
                if payment.payment_method not in {"cash", "mpesa"} or not in_period(payment.received_date):
                    continue
                if payment_method and payment.payment_method != payment_method:
                    continue
                errors = sum((Decimal(str(a.amount)) for a in payment.adjustments if a.kind == "entry_error"), Decimal("0"))
                received.append({**contact(order), "date": payment.received_date.isoformat(), "method": payment.payment_method,
                    "original_amount": payment.amount, "entry_errors": errors, "amount": Decimal(str(payment.amount)) - errors,
                    "actor": payment.confirmed_by_username})
            for item in order.payment_adjustments:
                if not in_period(item.effective_date):
                    continue
                method = item.refund_method if item.kind == "refund" else payments[item.payment_id].payment_method
                if payment_method and method != payment_method:
                    continue
                row = {**contact(order), "date": item.effective_date.isoformat(), "method": method, "amount": item.amount,
                    "purpose": item.refund_purpose or ("Entry correction" if item.kind == "entry_error" else "Unknown legacy purpose"),
                    "reason": item.reason, "actor": item.confirmed_by_username}
                (refunds if item.kind == "refund" else corrections).append(row)
        section("receipts", "Payments received in selected period — whole orders", RECEIPT_COLUMNS, received)
        section("refunds", "Money returned in selected period — whole orders", ADJUSTMENT_COLUMNS, refunds)
        section("corrections", "Entry corrections recorded in selected period", ADJUSTMENT_COLUMNS, corrections)
        cash = sum((row["amount"] for row in received if row["method"] == "cash"), Decimal("0"))
        mpesa = sum((row["amount"] for row in received if row["method"] == "mpesa"), Decimal("0"))
        returned = sum((Decimal(str(row["amount"])) for row in refunds), Decimal("0"))
        result["summary"] = {"cash_received": cash, "mpesa_received": mpesa, "total_received": cash + mpesa,
                             "refunds_sent": returned, "net_cash_movement": cash + mpesa - returned}
    if report_name in {"customer", "orders"}:
        balances = [order_row(order) for order in orders if order.balance_due > 0 or order.refund_due > 0]
        section("balances", "Current balances on selected orders — not historical", ORDER_COLUMNS, balances)
        result["summary"]["current_balance_due"] = sum((row["balance_due"] for row in balances), Decimal("0"))
        result["summary"]["current_refund_due"] = sum((row["refund_due"] for row in balances), Decimal("0"))
    return result


def bounded_payload(payload):
    if len(payload) > MAX_REPORT_BYTES:
        raise HTTPException(413, "This report is too large. Narrow its filters; nothing has been truncated.")
    return payload


def json_report(report):
    return bounded_payload(json.dumps(jsonable_encoder(report), ensure_ascii=False, allow_nan=False,
                                      separators=(",", ":")).encode("utf-8"))


def csv_report(report):
    json_report(report)
    buffer = io.StringIO(newline="")
    writer = csv.writer(buffer)
    writer.writerow(["QLMS", report["report"], "Generated", report["generated_at"], "Africa/Nairobi"])
    writer.writerow(["Filters", "; ".join(f"{key}={value}" for key, value in report["filters"].items()) or "All applicable records"])
    for definition in report["definitions"]:
        writer.writerow(["Definition", definition])
    for key, value in report["summary"].items():
        writer.writerow([key, value])
    for section in report["sections"]:
        writer.writerow([])
        writer.writerow([section["title"]])
        writer.writerow([column["label"] for column in section["columns"]])
        for row in section["rows"]:
            cells = []
            for column in section["columns"]:
                value = row.get(column["key"], "")
                if column["type"] not in {"money", "number"}:
                    value = str(value)
                    value = "'" + value if column["key"] == "customer_phone" or re.match(r"(?:[a-z][a-z0-9+.-]*:|www\.)", value.lstrip(), re.I) else safe_csv_text(value)
                cells.append(value)
            writer.writerow(cells)
    return bounded_payload(("\ufeff" + buffer.getvalue()).encode("utf-8"))


def xlsx_report(report):
    json_report(report)
    buffer = io.BytesIO()
    with xlsxwriter.Workbook(buffer, {"in_memory": True, "strings_to_formulas": False, "strings_to_urls": False}) as book:
        heading = book.add_format({"bold": True, "bg_color": "#005AAB", "font_color": "white"})
        money = book.add_format({"num_format": '#,##0.00 "KES"'})
        number = book.add_format({"num_format": "0.##"})
        about = book.add_worksheet("About this report")
        about.set_column(0, 0, 28)
        about.set_column(1, 1, 110)
        about.freeze_panes(1, 0)
        about.write_row(0, 0, ["QLMS report", report["report"]], heading)
        metadata = [("Generated", report["generated_at"]), ("Timezone", "Africa/Nairobi"),
                    *[(f"Filter: {key}", str(value)) for key, value in report["filters"].items()],
                    *[("Definition", definition) for definition in report["definitions"]], *report["summary"].items()]
        for index, (key, value) in enumerate(metadata, 1):
            about.write_string(index, 0, key)
            if isinstance(value, (int, float, Decimal)):
                about.write_number(index, 1, float(value), number)
            else:
                about.write_string(index, 1, value)
        for section in report["sections"]:
            sheet = book.add_worksheet(section["key"])
            sheet.freeze_panes(1, 0)
            sheet.set_column(0, len(section["columns"]) - 1, 25)
            sheet.write_row(0, 0, [column["label"] for column in section["columns"]], heading)
            if section["rows"]:
                sheet.autofilter(0, 0, len(section["rows"]), len(section["columns"]) - 1)
            for row_index, row in enumerate(section["rows"], 1):
                for column_index, column in enumerate(section["columns"]):
                    value = row.get(column["key"], "")
                    if column["type"] in {"money", "number"}:
                        sheet.write_number(row_index, column_index, float(value), money if column["type"] == "money" else number)
                    else:
                        if sheet.write_string(row_index, column_index, str(value)) != 0:
                            raise HTTPException(413, "A report cell exceeds Excel's limit. Nothing has been truncated; contact support.")
    return bounded_payload(buffer.getvalue())
