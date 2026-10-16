"""Daily cash checks use recorded money, never booked value or personal pockets."""
from datetime import date, datetime, timezone
from decimal import Decimal
import unittest
from uuid import uuid4

import models
from daily_control import daily_activity, closing_figures
from expense_routes import ExpenseInput, create_expense
from owner_reports import build_report
import test_financial_summary_contract as fixtures


class DailyControlTests(unittest.TestCase):
    setUp = fixtures.FinancialSummaryTests.setUp
    tearDown = fixtures.FinancialSummaryTests.tearDown
    add_order = fixtures.FinancialSummaryTests.add_order

    day = date(2026, 10, 13)

    def payment(self, order, method, amount, *, received=None):
        row = models.Payment(order_id=order.id, payment_method=method, amount=amount,
            received_date=received or self.day, confirmed_by_id=self.owner.id,
            confirmed_by_username=self.owner.username)
        self.db.add(row)
        self.db.commit()
        return row

    def adjustment(self, payment, kind, amount, *, effective=None, method=None):
        row = models.PaymentAdjustment(order_id=payment.order_id, payment_id=payment.id,
            kind=kind, amount=amount, effective_date=effective or self.day,
            refund_method=method, reason='Fictional money correction',
            refund_purpose='excess_payment' if kind == 'refund' else None,
            confirmed_by_id=self.owner.id, confirmed_by_username=self.owner.username)
        self.db.add(row)
        self.db.commit()
        return row

    def expense(self, amount, source, method='cash'):
        return create_expense(ExpenseInput(paid_date=self.day, category='supplies',
            amount=amount, payment_method=method, funding_source=source),
            self.db, self.owner, idempotency_key=uuid4())

    def fixture(self):
        # Money today can belong to work booked on an older day.
        order = self.add_order('QL-FICTIONAL-CLOSE', 3000,
            datetime(2026, 10, 12, 8, tzinfo=timezone.utc))
        cash = self.payment(order, 'cash', 1100)
        mpesa = self.payment(order, 'mpesa', 800)
        self.adjustment(cash, 'entry_error', 100, effective=date(2026, 10, 14))
        self.adjustment(mpesa, 'entry_error', 100)
        self.adjustment(cash, 'refund', 100, method='cash')
        self.adjustment(mpesa, 'refund', 50, method='mpesa')
        self.expense(150, 'shop')
        self.expense(300, 'owner')
        self.expense(80, 'owner', 'mpesa')
        return order, cash, mpesa

    def test_hand_count_personal_cost_and_separate_mpesa_totals(self):
        self.fixture()
        activity = daily_activity(self.db, self.day)
        figures = closing_figures(activity, opening_cash=Decimal('200'),
            counted_cash=Decimal('850'), statement_received=Decimal('700'),
            statement_returned=Decimal('50'), till_additions=Decimal('50'),
            owner_withdrawals=Decimal('100'))
        self.assertEqual(activity['cash_received'], 1000)
        self.assertEqual(activity['mpesa_received'], 700)
        self.assertEqual(activity['cash_refunds'], 100)
        self.assertEqual(activity['mpesa_refunds'], 50)
        self.assertEqual(activity['shop_cash_expenses'], 150)
        self.assertEqual(activity['owner_cash_expenses'], 300)
        self.assertEqual(figures['expected_cash'], 900)
        self.assertEqual(figures['cash_difference'], -50)
        self.assertEqual(figures['mpesa_received_difference'], 0)
        self.assertEqual(figures['mpesa_returned_difference'], 0)
        money = build_report(self.db, 'money', start_date=self.day, end_date=self.day)
        self.assertEqual(money['summary']['cash_received'], activity['cash_received'])
        self.assertEqual(money['summary']['mpesa_received'], activity['mpesa_received'])
        self.assertEqual(money['summary']['refunds_sent'], activity['cash_refunds'] + activity['mpesa_refunds'])

    def test_unknown_cash_funding_is_actionable_but_reversed_entries_are_excluded(self):
        unknown = self.expense(25, None)
        self.expense(10, None, 'mpesa')
        activity = daily_activity(self.db, self.day)
        self.assertEqual([item['id'] for item in activity['unconfirmed_cash_expenses']], [unknown.id])
        unknown.is_voided = True
        unknown.revision += 1
        self.db.commit()
        self.assertEqual(daily_activity(self.db, self.day)['unconfirmed_cash_expenses'], [])

    def test_fingerprint_is_stable_without_customer_contact_or_generation_time(self):
        self.fixture()
        first = daily_activity(self.db, self.day)['source_fingerprint']
        self.customer.name = 'Fictional renamed customer'
        self.customer.phone = '0722222222'
        self.db.commit()
        self.assertEqual(daily_activity(self.db, self.day)['source_fingerprint'], first)

    def test_later_entry_error_changes_original_day_and_equal_net_events_change_proof(self):
        order, cash, _ = self.fixture()
        first = daily_activity(self.db, self.day)
        self.adjustment(cash, 'entry_error', 10, effective=date(2026, 10, 14))
        self.payment(order, 'cash', 10)
        changed = daily_activity(self.db, self.day)
        self.assertEqual(changed['cash_received'], first['cash_received'])
        self.assertNotEqual(changed['source_fingerprint'], first['source_fingerprint'])

    def test_empty_day_and_next_day_receipts_do_not_fabricate_opening_cash(self):
        order, _, _ = self.fixture()
        self.payment(order, 'cash', 123, received=date(2026, 10, 14))
        empty = daily_activity(self.db, date(2026, 10, 11))
        self.assertEqual(empty['cash_received'], 0)
        self.assertNotIn('opening_cash', empty)
        self.assertEqual(daily_activity(self.db, self.day)['cash_received'], 1000)

    def test_decimal_cents_are_not_float_differences(self):
        empty = daily_activity(self.db, self.day)
        figures = closing_figures(empty, opening_cash=Decimal('0.30'),
            counted_cash=Decimal('0.10'), statement_received=Decimal('0.00'),
            statement_returned=Decimal('0.00'))
        self.assertEqual(figures['cash_difference'], Decimal('-0.20'))
        self.assertIsInstance(figures['cash_difference'], Decimal)

    def test_multiple_report_days_share_bounded_source_queries(self):
        from daily_control import activities_for_dates
        from sqlalchemy import event
        order, _, _ = self.fixture()
        self.payment(order, 'cash', 123, received=date(2026,10,14))
        statements=[]
        def record(connection,cursor,statement,*args):
            if statement.lstrip().startswith('SELECT'):
                statements.append(statement)
        event.listen(self.engine,'before_cursor_execute',record)
        try:
            days=activities_for_dates(self.db,[self.day,date(2026,10,14)])
        finally:
            event.remove(self.engine,'before_cursor_execute',record)
        self.assertEqual(days[self.day]['cash_received'],1000)
        self.assertEqual(days[date(2026,10,14)]['cash_received'],123)
        self.assertLessEqual(len(statements),6)
        self.assertEqual(days[self.day]['source_fingerprint'],daily_activity(self.db,self.day)['source_fingerprint'])

    def test_cash_return_from_an_mpesa_payment_uses_the_actual_refund_method(self):
        _, _, mpesa = self.fixture()
        self.adjustment(mpesa, 'refund', 25, method='cash')
        activity = daily_activity(self.db, self.day)
        self.assertEqual(activity['cash_refunds'], 125)
        self.assertEqual(activity['mpesa_refunds'], 50)
