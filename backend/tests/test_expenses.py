"""Fictional Owner costs keep money and correction history without duplicate saves."""
from datetime import date
from decimal import Decimal
from uuid import uuid4
import unittest
import os
from pathlib import Path

from sqlalchemy import text

import models
from owner_reports import build_report, csv_report, xlsx_report
import test_discount_policy as fixtures
import test_transaction_safety as transaction_fixtures


class ExpenseHttpTests(unittest.TestCase):
    setUp = fixtures.DiscountPolicyHttpTests.setUp
    tearDown = fixtures.DiscountPolicyHttpTests.tearDown
    post = fixtures.DiscountPolicyHttpTests.post

    def body(self, **changes):
        return {'paid_date':'2026-10-13','category':'supplies','amount':'250.50',
                'payment_method':'cash','reference':'Fictional receipt 1','note':'Fictional detergent', **changes}

    def create(self, **changes):
        status, result = self.post('/expenses',self.body(**changes))
        self.assertEqual(status,200,result)
        return result

    def test_owner_create_replay_and_employee_denial(self):
        key = uuid4()
        for _ in range(2):
            status, result = self.post('/expenses',self.body(),key=key)
            self.assertEqual(status,200,result)
            self.assertEqual(Decimal(result['amount']),Decimal('250.50'))
        self.assertEqual(self.post('/expenses',self.body(amount=251),key=key)[0],409)
        self.assertEqual(self.post('/expenses',self.body(),role='employee')[0],403)
        self.assertEqual(self.post('/expenses',self.body(),role=None)[0],401)
        with self.Session() as db:
            self.assertEqual(db.query(models.Expense).count(),1)
            self.assertEqual(db.query(models.ExpenseChange).count(),1)

    def test_invalid_details_and_trusted_fields_do_not_write(self):
        for changes in [{'amount':0},{'amount':-1},{'amount':'NaN'},{'amount':'2.001'},
                        {'category':'profit'},{'payment_method':'card'},{'paid_date':'2099-01-01'},
                        {'reference':'bad\x00ref'},{'note':'bad\x01note'}, {'revision':100},{'is_voided':True}]:
            self.assertEqual(self.post('/expenses',self.body(**changes))[0],422,changes)
        with self.Session() as db:
            self.assertEqual(db.query(models.Expense).count(),0)

    def test_correction_preserves_original_replay_and_stale_rejection(self):
        expense = self.create()
        key = uuid4()
        corrected = self.body(amount='200',payment_method='mpesa') | {
            'expected_revision':0,'reason':'Fictional method and amount correction','is_voided':False}
        path = f"/expenses/{expense['id']}/corrections"
        status, result = self.post(path,corrected,key=key)
        self.assertEqual(status,200,result)
        self.assertEqual(result['revision'],1)
        self.assertEqual(Decimal(result['original_details']['amount']),Decimal('250.50'))
        self.assertEqual(self.post(path,corrected,key=key)[0],200)
        status, stale = self.post(path,corrected)
        self.assertEqual(status,409)
        self.assertEqual(stale['detail']['save_state'],'not_saved')
        self.assertEqual(self.post(path,corrected | {'expected_revision':True})[0],422)
        self.assertEqual(self.post(path,corrected,role='employee')[0],403)
        status, history = self.post(f"/expenses/{expense['id']}",{},method='GET')
        self.assertEqual(status,200)
        self.assertEqual(len(history['corrections']),1)
        self.assertEqual(history['corrections'][0]['before_details']['payment_method'],'cash')
        self.assertEqual(history['corrections'][0]['after_details']['payment_method'],'mpesa')
        self.assertEqual(self.post(f"/expenses/{expense['id']}",{},method='GET',role='employee')[0],403)
        self.assertEqual(self.post(f"/expenses/{expense['id']}",{},method='DELETE')[0],405)

    def test_reports_apply_paid_dates_methods_and_keep_voided_history(self):
        first = self.create()
        self.create(category='utilities',amount=100,payment_method='mpesa')
        self.create(category='rent',paid_date='2026-09-30',amount=1000)
        with self.Session() as db:
            report = build_report(db,'expenses',start_date=date(2026,10,13),end_date=date(2026,10,13))
            self.assertEqual(report['summary']['cash_expenses'],Decimal('250.50'))
            self.assertEqual(report['summary']['mpesa_expenses'],Decimal('100'))
            self.assertEqual(report['summary']['total_expenses'],Decimal('350.50'))
            self.assertEqual(len(report['sections'][0]['rows']),2)
            self.assertEqual(build_report(db,'expenses',category='utilities')['summary']['total_expenses'],100)
            self.assertEqual(build_report(db,'expenses',payment_method='cash')['summary']['total_expenses'],Decimal('1250.50'))
        change = self.body() | {'is_voided':True,'expected_revision':0,'reason':'Fictional duplicate expense reversal'}
        self.assertEqual(self.post(f"/expenses/{first['id']}/corrections",change)[0],200)
        with self.Session() as db:
            report = build_report(db,'expenses',start_date=date(2026,10,13))
            self.assertEqual(report['summary']['total_expenses'],100)
            self.assertEqual(len(report['sections'][0]['rows']),2)
            self.assertEqual(len(report['sections'][1]['rows']),1)
            self.assertTrue(csv_report(report).startswith(b'\xef\xbb\xbf'))
            self.assertTrue(xlsx_report(report).startswith(b'PK'))

    def test_report_and_detail_access_requires_owner(self):
        self.assertEqual(self.post('/dashboard/reports/expenses',{},method='GET',role='employee')[0],403)
        self.assertEqual(self.post('/dashboard/reports/expenses',{},method='GET',role=None)[0],401)
        self.assertEqual(self.post('/expenses/999999',{},method='GET')[0],404)


@unittest.skipUnless(os.getenv('QLMS_TEST_DATABASE_URL'),'Requires disposable PostgreSQL')
class ExpensePostgresTests(unittest.TestCase):
    seed = transaction_fixtures.SaveFixtures.seed
    tearDown = transaction_fixtures.PostgresSaveTests.tearDown
    race = transaction_fixtures.PostgresSaveTests.race

    def setUp(self):
        transaction_fixtures.PostgresSaveTests.setUp(self)
        self.user.role = 'owner'
        self.db.commit()

    def body(self):
        from expense_routes import ExpenseInput
        return ExpenseInput(paid_date=date(2026,10,13),category='supplies',amount=100,payment_method='cash')

    def test_concurrent_replay_creates_one_expense_and_immutable_original(self):
        from expense_routes import create_expense
        key, body = uuid4(), self.body()
        operation = lambda db,user: create_expense(body,db,user,idempotency_key=key)
        outcomes = self.race([operation,operation])
        self.assertEqual([status for status,_ in outcomes],[200,200])
        self.assertEqual(self.db.query(models.Expense).count(),1)
        self.assertEqual(self.db.query(models.ExpenseChange).count(),1)

    def test_competing_corrections_reject_stale_and_lost_reply_replays(self):
        from expense_routes import create_expense, correct_expense, ExpenseCorrectionInput
        expense = create_expense(self.body(),self.db,self.user,idempotency_key=uuid4())
        change = ExpenseCorrectionInput(**self.body().model_dump(),expected_revision=0,reason='Fictional check',is_voided=False)
        change.amount = Decimal('75')
        outcomes = self.race([lambda db,user: correct_expense(expense.id,change,db,user,idempotency_key=uuid4()),
                              lambda db,user: correct_expense(expense.id,change,db,user,idempotency_key=uuid4())])
        self.assertEqual(sorted(status for status,_ in outcomes),[200,409])
        self.assertEqual(self.db.query(models.ExpenseChange).count(),2)
        expense = self.db.query(models.Expense).one()
        key = uuid4()
        next_change = ExpenseCorrectionInput(**self.body().model_dump(),expected_revision=1,reason='Fictional reversal',is_voided=True)
        first = correct_expense(expense.id,next_change,self.db,self.user,idempotency_key=key)
        again = correct_expense(expense.id,next_change,self.db,self.user,idempotency_key=key)
        self.assertEqual(first.id,again.id)
        self.assertEqual(self.db.query(models.ExpenseChange).count(),3)
        self.assertEqual(Decimal(again.original_details['amount']),100)

    def test_repeat_migration_keeps_records_and_browser_roles_denied(self):
        migration = (Path(__file__).parents[1]/'migrations/025_add_expenses.sql').read_text()
        funding_migration = (Path(__file__).parents[1]/'migrations/026_add_expense_funding.sql').read_text()
        self.db.close()
        with self.engine.begin() as connection:
            connection.execute(text('DROP TABLE expense_changes; DROP TABLE expenses'))
        with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql(migration)
            connection.exec_driver_sql(funding_migration)
        from expense_routes import create_expense
        owner = self.db.get(models.User,self.user_id)
        expense = create_expense(self.body(),self.db,owner,idempotency_key=uuid4())
        self.db.close()
        with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql(migration)
            connection.exec_driver_sql(funding_migration)
            self.assertEqual(connection.execute(text('SELECT count(*) FROM expenses')).scalar(),1)
            self.assertEqual(connection.execute(text('SELECT count(*) FROM expense_changes')).scalar(),1)
            for table in ('expenses','expense_changes'):
                self.assertTrue(connection.execute(text('SELECT relrowsecurity FROM pg_class WHERE oid=to_regclass(:name)'),{'name':table}).scalar())
                for role in ('anon','authenticated'):
                    if connection.execute(text('SELECT EXISTS(SELECT 1 FROM pg_roles WHERE rolname=:role)'),{'role':role}).scalar():
                        self.assertFalse(connection.execute(text("SELECT has_table_privilege(:role,:table,'SELECT')"),{'role':role,'table':table}).scalar())


if __name__ == '__main__':
    unittest.main()
