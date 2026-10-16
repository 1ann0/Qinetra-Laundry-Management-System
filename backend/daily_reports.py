"""Existing report formats show signed closing figures separately from current review state."""
from decimal import Decimal

from fastapi import HTTPException

import models
from daily_control import activities_for_dates, money
from owner_reports import bounded, columns, aware, NAIROBI

MOVEMENT_NAMES = {'addition': 'Cash added to till', 'withdrawal': 'Owner withdrawal'}


def selected_dates(query, field, start_date, end_date):
    if start_date:
        query = query.filter(field >= start_date)
    if end_date:
        query = query.filter(field <= end_date)
    return query


def extend_daily_report(db, kind, report, section, start_date, end_date):
    if kind == 'closing':
        saved = bounded(selected_dates(db.query(models.DailyClose), models.DailyClose.business_date,
            start_date, end_date).order_by(models.DailyClose.business_date.desc(), models.DailyClose.revision.desc()))
        current = activities_for_dates(db, [row.business_date for row in saved])
        latest, rows = {}, []
        for row in saved:
            is_latest = row.business_date not in latest
            latest.setdefault(row.business_date, row)
            values = row.snapshot
            rows.append({'business_date': row.business_date.isoformat(), 'revision': row.revision,
                'version_state': 'Latest' if is_latest else 'Earlier',
                'review_state': 'Needs review' if row.source_fingerprint != current[row.business_date]['source_fingerprint'] else 'No later ledger change',
                **{key: money(value) for key, value in values['counts'].items()},
                **{key: money(value) for key, value in values['figures'].items()},
                'mpesa_received': money(values['activity']['mpesa_received']),
                'mpesa_refunds': money(values['activity']['mpesa_refunds']),
                'reason': row.reason, 'actor': row.confirmed_by_username,
                'signed_at': aware(row.created_at).astimezone(NAIROBI).isoformat()})
        fields = columns(('business_date','Business date','date'), ('revision','Confirmation','number'),
            ('version_state','Version','text'), ('review_state','Current review state','text'),
            ('opening_cash','Opening cash entered KES','money'), ('expected_cash','Signed expected cash KES','money'),
            ('counted_cash','Cash counted KES','money'), ('cash_difference','Counted less expected KES','money'),
            ('mpesa_received','Signed recorded M-Pesa collected KES','money'),
            ('statement_received','Statement M-Pesa collected KES','money'),
            ('mpesa_received_difference','Statement less recorded collections KES','money'),
            ('mpesa_refunds','Signed recorded M-Pesa returned KES','money'),
            ('statement_returned','Statement M-Pesa returned KES','money'),
            ('mpesa_returned_difference','Statement less recorded returns KES','money'),
            ('reason','Explanation','text'), ('actor','Confirmed by','text'), ('signed_at','Confirmed at (Nairobi)','text'))
        latest_rows = [row for row in rows if row['version_state'] == 'Latest']
        section('closing_summary','Latest Owner confirmation for each selected business date', fields, latest_rows)
        section('closing_history','Every original Owner confirmation — never rewritten', fields, rows)
        report['summary'] = {'days_confirmed': len(latest_rows),
            'days_needing_review': sum(row['review_state'] == 'Needs review' for row in latest_rows)}
        report['definitions'] = [*report['definitions'],
            'Closing amounts are the immutable figures the Owner signed for that business date, not recalculated historical balances. Negative cash difference means short; positive means extra.',
            'Current review state compares the saved financial source with current records. Later changes flag review without rewriting the signed figures; a new confirmation preserves the old version.',
            'M-Pesa compares Owner-entered statement collections and returns with recorded collections and returns, not the account balance or expense payments. A match does not verify individual transactions. Daily counts are not income and are not added across days.']
        return

    movements = bounded(selected_dates(db.query(models.TillMovement), models.TillMovement.movement_date,
        start_date, end_date).order_by(models.TillMovement.movement_date.desc(), models.TillMovement.id.desc()))
    ids = [row.id for row in movements]
    events = bounded(db.query(models.TillMovementChange).filter(models.TillMovementChange.movement_id.in_(ids))
        .order_by(models.TillMovementChange.id)) if ids else []
    originals = {row.movement_id: row.after_details for row in events if row.revision == 0}
    if any(row.id not in originals for row in movements):
        raise HTTPException(409, 'An original cash movement is missing. Contact support before using this report')
    section('till_movements','Cash movements on corrected movement dates', columns(
        ('movement_id','Movement','number'), ('movement_date','Movement date','date'),
        ('kind','Kind','text'), ('amount','Amount KES','money'), ('state','State','text'),
        ('reference','Reference','text'), ('note','Note','text'), ('actor','Recorded by','text'), ('revision','Revision','number'),
        ('original_date','Original date','date'), ('original_kind','Original kind','text'), ('original_amount','Original KES','money')),
        [{'movement_id': row.id, 'movement_date': row.movement_date.isoformat(), 'kind': MOVEMENT_NAMES[row.kind],
          'amount': row.amount, 'state': 'Reversed' if row.is_voided else 'Recorded', 'reference': row.reference,
          'note': row.note, 'actor': row.confirmed_by_username, 'revision': row.revision,
          'original_date': originals[row.id]['movement_date'], 'original_kind': MOVEMENT_NAMES[originals[row.id]['kind']],
          'original_amount': money(originals[row.id]['amount'])} for row in movements])
    changes = [row for row in events if row.revision > 0]
    section('till_changes','Corrections to the selected cash movements', columns(
        ('movement_id','Movement','number'), ('revision','Revision','number'), ('recorded_at','Corrected at (Nairobi)','text'),
        ('before_date','Before date','date'), ('after_date','After date','date'),
        ('before_kind','Before kind','text'), ('after_kind','After kind','text'),
        ('before_amount','Before KES','money'), ('after_amount','After KES','money'),
        ('after_state','After state','text'), ('reason','Explanation','text'), ('actor','Corrected by','text')),
        [{'movement_id': row.movement_id, 'revision': row.revision,
          'recorded_at': aware(row.created_at).astimezone(NAIROBI).isoformat(),
          'before_date': row.before_details['movement_date'], 'after_date': row.after_details['movement_date'],
          'before_kind': MOVEMENT_NAMES[row.before_details['kind']], 'after_kind': MOVEMENT_NAMES[row.after_details['kind']],
          'before_amount': money(row.before_details['amount']), 'after_amount': money(row.after_details['amount']),
          'after_state': 'Reversed' if row.after_details['is_voided'] else 'Recorded',
          'reason': row.reason, 'actor': row.confirmed_by_username} for row in changes])
    additions = sum((row.amount for row in movements if not row.is_voided and row.kind == 'addition'), Decimal('0'))
    withdrawals = sum((row.amount for row in movements if not row.is_voided and row.kind == 'withdrawal'), Decimal('0'))
    report['summary'] = {'cash_added': additions, 'owner_withdrawals': withdrawals, 'net_till_movement': additions-withdrawals}
    report['definitions'] = [*report['definitions'],
        'Till movements are cash additions and Owner withdrawals, not receipts, expenses or profit. Reversed movements remain visible and are excluded from totals.',
        'Date filters use current corrected movement dates. Original details and corrections remain visible for the selected movements; their correction timestamps do not define this cash-movement period.']
