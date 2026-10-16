"""Funding is a business fact; missing legacy details must never be invented."""
from datetime import date
from decimal import Decimal
from uuid import uuid4
from pathlib import Path
import io
import os
import unittest
from zipfile import ZipFile
from xml.etree import ElementTree

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError

import models
import test_expenses as fixtures
from expense_routes import ExpenseInput, ExpenseCorrectionInput
from owner_reports import build_report, csv_report, xlsx_report
from transaction_safety import request_fingerprint


class ExpenseFundingTests(unittest.TestCase):
    setUp = fixtures.ExpenseHttpTests.setUp
    tearDown = fixtures.ExpenseHttpTests.tearDown
    post = fixtures.ExpenseHttpTests.post
    body = fixtures.ExpenseHttpTests.body
    create = fixtures.ExpenseHttpTests.create

    def test_old_create_and_correction_fingerprints_do_not_change(self):
        body = self.body()
        self.assertEqual(request_fingerprint('create_expense', ExpenseInput(**body)),
                         '05bd83009162ea3eeaf5e9e233504d5d50f7a5348f0fe070e5a036142f678064')
        correction = ExpenseCorrectionInput(**body, expected_revision=0,
            reason='Confirm original details', is_voided=False)
        self.assertEqual(request_fingerprint('correct_expense:1', correction),
                         'c8ce610411f854b1091ad5a08a0f88a7f9206d4a4c5f657d6b354c87c65e3e6c')

    def test_classified_create_replays_once_and_rejects_changed_funding(self):
        key = uuid4()
        body = self.body(funding_source='owner')
        for _ in range(2):
            status, saved = self.post('/expenses', body, key=key)
            self.assertEqual(status, 200, saved)
            self.assertEqual(saved['funding_source'], 'owner')
        self.assertEqual(self.post('/expenses', body | {'funding_source':'shop'}, key=key)[0],409)
        self.assertEqual(self.post('/expenses', body, role='employee')[0],403)
        for value in ['personal', '', True, 1, {'shop':True}]:
            self.assertEqual(self.post('/expenses', self.body(funding_source=value))[0],422)
        with self.Session() as db:
            self.assertEqual(db.query(models.Expense).count(),1)
            self.assertEqual(db.query(models.ExpenseChange).count(),1)

    def test_legacy_lost_create_reply_still_returns_its_original_record(self):
        key = uuid4()
        saved = self.create()
        with self.Session() as db:
            row = db.get(models.Expense,saved['id'])
            row.request_key = str(key)
            row.request_hash = '05bd83009162ea3eeaf5e9e233504d5d50f7a5348f0fe070e5a036142f678064'
            db.commit()
        status, retry = self.post('/expenses',self.body(),key=key)
        self.assertEqual(status,200,retry)
        self.assertEqual(retry['id'],saved['id'])
        self.assertIsNone(retry.get('funding_source'))
        with self.Session() as db:
            self.assertEqual(db.query(models.Expense).count(),1)

    def test_confirming_funding_preserves_original_and_old_corrections_keep_it(self):
        expense = self.create()
        path = f"/expenses/{expense['id']}/corrections"
        key = uuid4()
        body = self.body(funding_source='owner') | {'expected_revision':0,
            'reason':'Owner confirms personal payment','is_voided':False}
        status, saved = self.post(path,body,key=key)
        self.assertEqual(status,200,saved)
        self.assertEqual(saved['funding_source'],'owner')
        self.assertNotIn('funding_source',saved['original_details'])
        self.assertEqual(saved['corrections'][0]['after_details']['funding_source'],'owner')
        self.assertEqual(self.post(path,body,key=key)[1]['revision'],1)
        legacy = self.body(amount='200') | {'expected_revision':1,
            'reason':'Older screen corrects amount','is_voided':False}
        status, saved = self.post(path,legacy)
        self.assertEqual(status,200,saved)
        self.assertEqual(saved['funding_source'],'owner')
        self.assertEqual(Decimal(saved['amount']),200)
        self.assertEqual(len(saved['corrections']),2)
        self.assertNotIn('funding_source',saved['original_details'])

    def test_source_subtotals_and_exports_do_not_change_business_costs(self):
        self.create(amount=100, funding_source='shop')
        self.create(amount=50, funding_source='owner')
        unknown = self.create(amount=25, payment_method='mpesa')
        with self.Session() as db:
            report = build_report(db,'expenses',start_date=date(2026,10,13),end_date=date(2026,10,13))
            self.assertEqual(report['summary']['total_expenses'],175)
            self.assertEqual(report['summary']['cash_expenses'],150)
            self.assertEqual(report['summary']['shop_funded_expenses'],100)
            self.assertEqual(report['summary']['owner_funded_expenses'],50)
            self.assertEqual(report['summary']['unconfirmed_funding_expenses'],25)
            self.assertEqual({row['funding_source'] for row in report['sections'][0]['rows']},
                             {'Shop money',"Owner's own money",'Not confirmed'})
            self.assertIn(b'Paid from', csv_report(report))
            self.assertIn(b'Not confirmed', csv_report(report))
            with ZipFile(io.BytesIO(xlsx_report(report))) as book:
                strings = ElementTree.fromstring(book.read('xl/sharedStrings.xml'))
                texts = [''.join(item.itertext()) for item in strings]
                self.assertIn('Paid from',texts)
                self.assertIn("Owner's own money",texts)
                self.assertIn('Not confirmed',texts)
        reversal = self.body(amount=25,payment_method='mpesa') | {'expected_revision':0,
            'reason':'Duplicate legacy entry','is_voided':True}
        self.assertEqual(self.post(f"/expenses/{unknown['id']}/corrections",reversal)[0],200)
        with self.Session() as db:
            summary = build_report(db,'expenses')['summary']
            self.assertEqual(summary['unconfirmed_funding_expenses'],0)
            self.assertEqual(summary['total_expenses'],150)

    def test_old_lost_correction_reply_after_classification_does_not_undo_it(self):
        expense = self.create()
        self.assertEqual(expense['id'],1)
        path = '/expenses/1/corrections'
        key = uuid4()
        old = self.body() | {'expected_revision':0,'reason':'Confirm original details','is_voided':False}
        self.assertEqual(self.post(path,old,key=key)[0],200)
        with self.Session() as db:
            event = db.query(models.ExpenseChange).filter_by(request_key=str(key)).one()
            self.assertEqual(event.request_hash,'c8ce610411f854b1091ad5a08a0f88a7f9206d4a4c5f657d6b354c87c65e3e6c')
        changed = self.body(funding_source='owner') | {'expected_revision':1,'reason':'Confirm personal funding','is_voided':False}
        self.assertEqual(self.post(path,changed)[0],200)
        status, replay = self.post(path,old,key=key)
        self.assertEqual(status,200,replay)
        self.assertEqual(replay['funding_source'],'owner')
        self.assertEqual(replay['revision'],2)
        self.assertEqual(len(replay['corrections']),2)


@unittest.skipUnless(os.getenv('QLMS_TEST_DATABASE_URL'),'Requires disposable PostgreSQL')
class ExpenseFundingPostgresTests(unittest.TestCase):
    setUp = fixtures.ExpensePostgresTests.setUp
    tearDown = fixtures.ExpensePostgresTests.tearDown
    seed = fixtures.ExpensePostgresTests.seed
    race = fixtures.ExpensePostgresTests.race
    body = fixtures.ExpensePostgresTests.body

    def test_concurrent_classified_creation_is_one_record_and_event(self):
        from expense_routes import create_expense
        body, key = self.body().model_copy(update={'funding_source':'shop'}), uuid4()
        outcomes = self.race([lambda db,owner:create_expense(body,db,owner,idempotency_key=key)]*2)
        self.assertEqual([status for status,_ in outcomes],[200,200])
        self.assertEqual(self.db.query(models.Expense).one().funding_source,'shop')
        self.assertEqual(self.db.query(models.ExpenseChange).count(),1)

    def test_competing_funding_confirmations_and_lost_response(self):
        from expense_routes import create_expense, correct_expense
        saved = create_expense(self.body(),self.db,self.user,idempotency_key=uuid4())
        requests = [(ExpenseCorrectionInput(**self.body().model_dump(),funding_source=source,
            expected_revision=0,reason='Confirm fictional payer',is_voided=False),uuid4()) for source in ('shop','owner')]
        outcomes = self.race([lambda db,owner,b=body,k=key:correct_expense(saved.id,b,db,owner,idempotency_key=k) for body,key in requests])
        self.assertEqual(sorted(status for status,_ in outcomes),[200,409])
        body,key = next(request for request,outcome in zip(requests,outcomes) if outcome[0]==200)
        # An HTTP retry gets a fresh session, not setup's cached pre-race row.
        with self.Session() as retry_db:
            self.assertEqual(retry_db.get(models.Expense,saved.id).funding_source,body.funding_source)
            replay = correct_expense(saved.id,body,retry_db,retry_db.get(models.User,self.user_id),idempotency_key=key)
            self.assertEqual(replay.funding_source,body.funding_source)
            self.assertEqual(replay.revision,1)
            self.assertNotIn('funding_source',replay.original_details)
        self.assertEqual(self.db.query(models.ExpenseChange).count(),2)

    def test_repeat_upgrade_keeps_legacy_money_hash_and_history(self):
        from expense_routes import create_expense
        saved = create_expense(self.body(),self.db,self.user,idempotency_key=uuid4())
        expected_hash, original = saved.request_hash, saved.original_details
        self.db.close()
        with self.engine.begin() as connection:
            connection.execute(text('ALTER TABLE expenses DROP COLUMN funding_source'))
        migration = (Path(__file__).parents[1]/'migrations/026_add_expense_funding.sql').read_text()
        with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql(migration)
            row = connection.execute(text('SELECT amount,request_hash,funding_source FROM expenses')).one()
            self.assertEqual(tuple(row),(Decimal('100'),expected_hash,None))
            self.assertEqual(connection.execute(text('SELECT after_details FROM expense_changes')).scalar(),original)
            connection.execute(text("UPDATE expenses SET funding_source='owner'"))
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.execute(text('SELECT funding_source FROM expenses')).scalar(),'owner')
            self.assertEqual(connection.execute(text('SELECT after_details FROM expense_changes')).scalar(),original)
        with self.assertRaises(IntegrityError), self.engine.begin() as connection:
            connection.execute(text("UPDATE expenses SET funding_source='invented'"))


if __name__ == '__main__':
    unittest.main()
