"""Owner sign-off preserves snapshots, corrections and uncertain-save references."""
from decimal import Decimal
from datetime import date
from uuid import uuid4
import unittest

import models
from owner_reports import build_report, csv_report, xlsx_report
from zipfile import ZipFile
import io
import test_discount_policy as fixtures


class DailyCloseHttpTests(unittest.TestCase):
    setUp = fixtures.DiscountPolicyHttpTests.setUp
    tearDown = fixtures.DiscountPolicyHttpTests.tearDown
    post = fixtures.DiscountPolicyHttpTests.post
    day = '2026-10-13'

    def preview(self):
        status, result = self.post('/daily-close?date=' + self.day, {}, method='GET')
        self.assertEqual(status, 200, result)
        return result

    def close_body(self, preview, **changes):
        return {'business_date': self.day, 'opening_cash': '200', 'counted_cash': '200',
            'statement_received': '0', 'statement_returned': '0',
            'expected_revision': preview['latest']['revision'] if preview['latest'] else 0,
            'expected_fingerprint': preview['activity']['source_fingerprint'], 'reason': '', **changes}

    def movement(self, **changes):
        body = {'movement_date': self.day, 'kind': 'addition', 'amount': '50',
            'reference': 'Fictional till top-up', 'note': 'Fictional shop cash', **changes}
        status, result = self.post('/till-movements', body)
        self.assertEqual(status, 200, result)
        return result

    def test_owner_only_daily_close_and_till_routes(self):
        for path in ('/daily-close?date=' + self.day, '/till-movements/1'):
            self.assertEqual(self.post(path, {}, method='GET', role='employee')[0], 403)
            self.assertEqual(self.post(path, {}, method='GET', role=None)[0], 401)
        preview = self.preview()
        body = self.close_body(preview)
        self.assertEqual(self.post('/daily-close', body, role='employee')[0], 403)
        self.assertEqual(self.post('/daily-close', body, role=None)[0], 401)
        movement = {'movement_date':self.day,'kind':'addition','amount':'50','reference':'','note':''}
        self.assertEqual(self.post('/till-movements',movement,role='employee')[0],403)
        self.assertEqual(self.post('/till-movements',movement,role=None)[0],401)
        correction = movement | {'expected_revision':0,'reason':'Fictional check','is_voided':False}
        self.assertEqual(self.post('/till-movements/1/corrections',correction,role='employee')[0],403)

    def test_900_expected_850_counted_requires_reason_and_saved_snapshot_is_immutable(self):
        body = self.close_body(self.preview(), opening_cash='900', counted_cash='850')
        self.assertEqual(self.post('/daily-close', body)[0], 422)
        body['reason'] = 'Owner records fictional fifty shillings short'
        status, saved = self.post('/daily-close', body)
        self.assertEqual(status, 200, saved)
        self.assertEqual(Decimal(saved['snapshot']['figures']['expected_cash']), 900)
        self.assertEqual(Decimal(saved['snapshot']['figures']['cash_difference']), -50)
        self.assertEqual(saved['revision'], 1)
        self.movement()
        current = self.preview()
        self.assertTrue(current['needs_review'])
        self.assertEqual(current['latest']['snapshot'], saved['snapshot'])
        self.assertEqual(Decimal(current['activity']['till_additions']), 50)

    def test_replay_returns_original_version_after_later_confirmation(self):
        first_body = self.close_body(self.preview())
        key = uuid4()
        status, original = self.post('/daily-close', first_body, key=key)
        self.assertEqual(status, 200, original)
        self.movement()
        second_body = self.close_body(self.preview(), counted_cash='250', reason='Reviewed fictional till addition')
        status, second = self.post('/daily-close', second_body)
        self.assertEqual(status, 200, second)
        self.assertEqual(second['revision'], 2)
        status, replay = self.post('/daily-close', first_body, key=key)
        self.assertEqual(status, 200, replay)
        self.assertEqual(replay['id'], original['id'])
        self.assertEqual(replay['revision'], 1)
        self.assertEqual(self.post('/daily-close', first_body | {'counted_cash': '201'}, key=key)[0], 409)
        self.assertEqual(len(self.preview()['history']), 2)

    def test_stale_preview_and_unknown_cash_payer_reject_before_signing(self):
        body = self.close_body(self.preview())
        self.movement()
        status, rejected = self.post('/daily-close', body)
        self.assertEqual(status, 409, rejected)
        self.assertEqual(rejected['detail']['save_state'], 'not_saved')
        status, _ = self.post('/expenses', {'paid_date': self.day, 'category': 'supplies',
            'amount': '10', 'payment_method': 'cash', 'reference': '', 'note': ''})
        self.assertEqual(status, 200)
        current = self.preview()
        self.assertEqual(len(current['activity']['unconfirmed_cash_expenses']), 1)
        self.assertEqual(self.post('/daily-close', self.close_body(current, counted_cash='250'))[0], 409)
        with self.Session() as db:
            self.assertEqual(db.query(models.DailyClose).count(), 0)

    def test_till_correction_preserves_original_and_retry_is_once(self):
        saved = self.movement()
        body = {'movement_date': self.day, 'kind': 'withdrawal', 'amount': '20',
            'reference': 'Fictional changed type', 'note': '', 'expected_revision': 0,
            'reason': 'Owner corrects fictional movement', 'is_voided': False}
        key = uuid4()
        path = f"/till-movements/{saved['id']}/corrections"
        for _ in range(2):
            status, changed = self.post(path, body, key=key)
            self.assertEqual(status, 200, changed)
            self.assertEqual(changed['revision'], 1)
            self.assertEqual(changed['original_details']['kind'], 'addition')
            self.assertEqual(changed['kind'], 'withdrawal')
        self.assertEqual(self.post(path, body)[0], 409)
        self.assertEqual(self.post(f"/till-movements/{saved['id']}", {}, method='DELETE')[0], 405)
        activity = self.preview()['activity']
        self.assertEqual(Decimal(activity['till_additions']), 0)
        self.assertEqual(Decimal(activity['owner_withdrawals']), 20)

    def test_negative_boolean_excess_precision_and_future_dates_are_rejected(self):
        body = self.close_body(self.preview())
        for field, value in [('opening_cash', '-1'), ('counted_cash', True),
                             ('statement_received', '0.001'), ('statement_returned', 'NaN'),
                             ('business_date', '2999-01-01'), ('expected_revision', True)]:
            self.assertEqual(self.post('/daily-close', body | {field: value})[0], 422, field)

    def test_future_preview_is_a_validation_error(self):
        self.assertEqual(self.post('/daily-close?date=2999-01-01', {}, method='GET')[0], 422)

    def test_preview_money_is_decimal_text_like_saved_snapshot_money(self):
        preview = self.preview()
        for key in ('cash_received', 'mpesa_received', 'cash_refunds', 'shop_cash_expenses', 'till_additions'):
            self.assertIsInstance(preview['activity'][key], str, key)

    def test_closing_and_till_reports_preserve_signed_values_and_flag_later_changes(self):
        body = self.close_body(self.preview(), opening_cash='900', counted_cash='850', reason='Fictional cash short')
        self.assertEqual(self.post('/daily-close', body)[0], 200)
        self.movement()
        with self.Session() as db:
            closing = build_report(db, 'closing', start_date=date(2026,10,13), end_date=date(2026,10,13))
            self.assertEqual(closing['summary']['days_confirmed'], 1)
            self.assertEqual(closing['summary']['days_needing_review'], 1)
            row = closing['sections'][0]['rows'][0]
            self.assertEqual(Decimal(row['expected_cash']), 900)
            self.assertEqual(Decimal(row['cash_difference']), -50)
            self.assertEqual(row['review_state'], 'Needs review')
            movements = build_report(db, 'till', start_date=date(2026,10,13), end_date=date(2026,10,13))
            self.assertEqual(movements['summary']['cash_added'], 50)
            self.assertEqual(movements['summary']['owner_withdrawals'], 0)
            self.assertIn(b'Needs review', csv_report(closing))
            with ZipFile(io.BytesIO(xlsx_report(closing))) as book:
                self.assertIsNone(book.testzip())
        self.assertEqual(self.post('/dashboard/reports/closing', {}, method='GET', role='employee')[0], 403)

    def test_moving_a_cash_record_to_another_day_flags_the_original_close(self):
        saved = self.movement()
        self.assertEqual(self.post('/daily-close',self.close_body(self.preview(),counted_cash='250'))[0],200)
        change = {'movement_date':'2026-10-14','kind':'addition','amount':'50','reference':'','note':'',
            'expected_revision':0,'reason':'Corrected fictional business date','is_voided':False}
        self.assertEqual(self.post(f"/till-movements/{saved['id']}/corrections",change)[0],200)
        old = self.preview()
        self.assertTrue(old['needs_review'])
        self.assertEqual(Decimal(old['activity']['till_additions']),0)
        self.assertEqual(Decimal(old['latest']['snapshot']['activity']['till_additions']),50)
        status, new = self.post('/daily-close?date=2026-10-14',{},method='GET')
        self.assertEqual(status,200,new)
        self.assertEqual(Decimal(new['activity']['till_additions']),50)

    def test_statement_variance_and_export_formula_protection(self):
        body=self.close_body(self.preview(),statement_received='100')
        self.assertEqual(self.post('/daily-close',body)[0],422)
        body['reason']='=SUM(1,2)'
        status,saved=self.post('/daily-close',body)
        self.assertEqual(status,200,saved)
        self.assertEqual(Decimal(saved['snapshot']['figures']['mpesa_received_difference']),100)
        with self.Session() as db:
            report=build_report(db,'closing',start_date=date(2026,10,13),end_date=date(2026,10,13))
            self.assertIn(b"'=SUM(1,2)",csv_report(report))
            with ZipFile(io.BytesIO(xlsx_report(report))) as book:
                sheet=book.read('xl/worksheets/sheet2.xml')
                self.assertNotIn(b'<f>',sheet)
