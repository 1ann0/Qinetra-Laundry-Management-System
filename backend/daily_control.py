"""Shared daily money components; signed closing snapshots never alter the ledger."""
from decimal import Decimal
import hashlib
import json

from fastapi import HTTPException
from sqlalchemy.orm.attributes import set_committed_value

import models
from owner_reports import bounded, MAX_RECORDS


def money(value):
    return Decimal(str(value))


def snapshot_values(values):
    # Keep KES as decimal text in previews and signed JSON, never binary floats.
    return json.loads(json.dumps(values, default=str, allow_nan=False))


def activities_for_dates(db, business_dates):
    """Read all selected days together inside the caller's consistent transaction."""
    days = sorted(set(business_dates))
    if len(days) > 366:
        raise HTTPException(413, 'Choose at most 366 closing days. Nothing has been truncated.')
    if not days:
        return {}
    payments = bounded(db.query(models.Payment).filter(
        models.Payment.received_date.in_(days),
        models.Payment.payment_method.in_(['cash', 'mpesa']),
    ).populate_existing().order_by(models.Payment.id))
    payment_ids = [item.id for item in payments]
    adjustments = bounded(db.query(models.PaymentAdjustment).filter(
        models.PaymentAdjustment.payment_id.in_(payment_ids),
    ).populate_existing().order_by(models.PaymentAdjustment.id)) if payment_ids else []
    by_payment = {}
    for item in adjustments:
        by_payment.setdefault(item.payment_id, []).append(item)
    for payment in payments:
        set_committed_value(payment, 'adjustments', by_payment.get(payment.id, []))
    refunds = bounded(db.query(models.PaymentAdjustment).filter(
        models.PaymentAdjustment.kind == 'refund',
        models.PaymentAdjustment.effective_date.in_(days),
    ).populate_existing().order_by(models.PaymentAdjustment.id))
    expenses = bounded(db.query(models.Expense).filter(
        models.Expense.paid_date.in_(days),
    ).populate_existing().order_by(models.Expense.id))
    movements = bounded(db.query(models.TillMovement).filter(
        models.TillMovement.movement_date.in_(days),
    ).populate_existing().order_by(models.TillMovement.id))
    if len(payments) + len(adjustments) + len(refunds) + len(expenses) + len(movements) > MAX_RECORDS:
        raise HTTPException(413, 'This daily check is too large. Nothing has been truncated.')

    def grouped(rows, field):
        result = {}
        for row in rows:
            result.setdefault(getattr(row, field), []).append(row)
        return result
    groups = [grouped(rows, field) for rows, field in ((payments, 'received_date'),
        (refunds, 'effective_date'), (expenses, 'paid_date'), (movements, 'movement_date'))]
    return {day: _day_components(day, *(group.get(day, []) for group in groups)) for day in days}


def daily_activity(db, business_date):
    return activities_for_dates(db, [business_date])[business_date]


def _day_components(business_date, payments, refunds, expenses, movements):

    def receipts(method):
        return sum((item.corrected_amount for item in payments if item.payment_method == method), Decimal('0'))

    def returns(method):
        return sum((money(item.amount) for item in refunds if item.refund_method == method), Decimal('0'))

    def costs(source):
        return sum((money(item.amount) for item in expenses if not item.is_voided
            and item.payment_method == 'cash' and item.funding_source == source), Decimal('0'))

    # Include identities/revisions, not just totals: equal-net later events still need review.
    source = {
        'date': business_date.isoformat(),
        'payments': [[item.id, item.order_id, item.payment_method, item.received_date.isoformat(),
            money(item.amount), [[change.id, money(change.amount), change.effective_date.isoformat()]
                for change in item.adjustments if change.kind == 'entry_error']] for item in payments],
        'refunds': [[item.id, item.payment_id, item.refund_method, money(item.amount),
            item.effective_date.isoformat()] for item in refunds],
        'expenses': [[item.id, item.paid_date.isoformat(), money(item.amount), item.payment_method,
            item.funding_source, item.is_voided, item.revision] for item in expenses],
        'movements': [[item.id, item.movement_date.isoformat(), item.kind, money(item.amount),
            item.is_voided, item.revision] for item in movements],
    }
    fingerprint = hashlib.sha256(json.dumps(source, sort_keys=True, separators=(',', ':'),
        default=str, allow_nan=False).encode('utf-8')).hexdigest()
    return {
        'date': business_date.isoformat(), 'source_fingerprint': fingerprint,
        'cash_received': receipts('cash'), 'mpesa_received': receipts('mpesa'),
        'cash_refunds': returns('cash'), 'mpesa_refunds': returns('mpesa'),
        'shop_cash_expenses': costs('shop'), 'owner_cash_expenses': costs('owner'),
        'business_expenses': sum((money(item.amount) for item in expenses if not item.is_voided), Decimal('0')),
        'till_additions': sum((money(item.amount) for item in movements if not item.is_voided and item.kind == 'addition'), Decimal('0')),
        'owner_withdrawals': sum((money(item.amount) for item in movements if not item.is_voided and item.kind == 'withdrawal'), Decimal('0')),
        'movements': [{'id': item.id, 'kind': item.kind, 'amount': money(item.amount),
            'is_voided': item.is_voided, 'revision': item.revision} for item in movements],
        'unconfirmed_cash_expenses': [{'id': item.id, 'amount': money(item.amount)} for item in expenses
            if not item.is_voided and item.payment_method == 'cash' and item.funding_source is None],
    }


def signed_details(row):
    return {key: getattr(row, key) for key in ('id', 'business_date', 'revision',
        'source_fingerprint', 'snapshot', 'reason', 'confirmed_by_username', 'created_at')}


def close_history(db, business_date):
    return bounded(db.query(models.DailyClose).filter_by(business_date=business_date)
        .populate_existing().order_by(models.DailyClose.revision.desc()))


def closing_figures(activity, *, opening_cash, counted_cash, statement_received,
                    statement_returned, till_additions=None, owner_withdrawals=None):
    till_additions = activity['till_additions'] if till_additions is None else till_additions
    owner_withdrawals = activity['owner_withdrawals'] if owner_withdrawals is None else owner_withdrawals
    expected = (money(opening_cash) + activity['cash_received'] - activity['cash_refunds']
        - activity['shop_cash_expenses'] + money(till_additions) - money(owner_withdrawals))
    return {
        'expected_cash': expected,
        'cash_difference': money(counted_cash) - expected,
        'mpesa_received_difference': money(statement_received) - activity['mpesa_received'],
        'mpesa_returned_difference': money(statement_returned) - activity['mpesa_refunds'],
    }
