"""Actual PostgreSQL races and snapshots, using only the guarded local test runner."""
from datetime import date
from decimal import Decimal
import os
from pathlib import Path
from types import SimpleNamespace
from concurrent.futures import ThreadPoolExecutor
from threading import Event, get_ident
from unittest.mock import patch
import unittest
from uuid import uuid4

from sqlalchemy import event, text
from sqlalchemy.exc import DBAPIError

import models
from daily_close_routes import CloseInput, TillInput, confirm_close, create_movement, read_close
import test_expenses as fixtures


@unittest.skipUnless(os.getenv('QLMS_TEST_DATABASE_URL'), 'Requires disposable local PostgreSQL')
class DailyClosePostgresTests(unittest.TestCase):
    setUp = fixtures.ExpensePostgresTests.setUp
    tearDown = fixtures.ExpensePostgresTests.tearDown
    seed = fixtures.ExpensePostgresTests.seed
    race = fixtures.ExpensePostgresTests.race
    day = date(2026, 10, 13)

    def preview(self):
        result = read_close(self.day, self.db, self.user)
        self.db.rollback()
        return result

    def body(self):
        preview = self.preview()
        return CloseInput(business_date=self.day, opening_cash=200, counted_cash=200,
            statement_received=0, statement_returned=0, expected_revision=0,
            expected_fingerprint=preview['activity']['source_fingerprint'])

    def test_same_reference_concurrent_close_returns_one_immutable_version(self):
        body, key = self.body(), uuid4()
        def save(db, owner):
            return SimpleNamespace(id=confirm_close(body, db, owner, idempotency_key=key)['id'])
        outcomes = self.race([save, save])
        self.assertEqual(outcomes[0], outcomes[1], outcomes)
        self.assertEqual(outcomes[0][0], 200, outcomes)
        self.assertEqual(self.db.query(models.DailyClose).count(), 1)

    def test_waiting_replay_uses_committed_result_even_when_its_snapshot_started_earlier(self):
        import daily_close_routes
        body, key = self.body(), uuid4()
        primary_ready, secondary_waiting = Event(), Event()
        primary_thread = []
        original_commit = daily_close_routes.commit_once
        def pause_primary(db, *args):
            if get_ident() == primary_thread[0]:
                primary_ready.set()
                self.assertTrue(secondary_waiting.wait(8), 'Second request never reached its reference lock')
            return original_commit(db, *args)
        def observe_secondary(connection, cursor, statement, *args):
            if primary_thread and get_ident() != primary_thread[0] and 'pg_advisory_xact_lock' in statement:
                secondary_waiting.set()
        def save(primary=False):
            if primary:
                primary_thread.append(get_ident())
            with self.Session() as db:
                return confirm_close(body, db, db.get(models.User, self.user_id), idempotency_key=key)
        event.listen(self.engine, 'before_cursor_execute', observe_secondary)
        try:
            with patch.object(daily_close_routes, 'commit_once', side_effect=pause_primary), ThreadPoolExecutor(max_workers=2) as pool:
                first = pool.submit(save, True)
                self.assertTrue(primary_ready.wait(8))
                second = pool.submit(save)
                self.assertEqual(first.result(timeout=20)['id'], second.result(timeout=20)['id'])
        finally:
            event.remove(self.engine, 'before_cursor_execute', observe_secondary)
        self.assertEqual(self.db.query(models.DailyClose).count(), 1)

    def test_competing_different_references_cannot_sign_the_same_revision(self):
        body = self.body()
        def save(db, owner):
            return SimpleNamespace(id=confirm_close(body, db, owner, idempotency_key=uuid4())['id'])
        outcomes = self.race([save, save])
        self.assertEqual(sorted(status for status, _ in outcomes), [200, 409], outcomes)
        rejected = next(result for status, result in outcomes if status == 409)
        self.assertEqual(rejected['save_state'], 'not_saved')
        self.assertEqual(self.db.query(models.DailyClose).count(), 1)

    def test_till_same_reference_concurrency_saves_one_original_event(self):
        body = TillInput(movement_date=self.day, kind='addition', amount=50)
        key = uuid4()
        outcomes = self.race([lambda db, owner: create_movement(body, db, owner, idempotency_key=key)] * 2)
        self.assertEqual(outcomes[0], outcomes[1], outcomes)
        self.assertEqual(outcomes[0][0], 200)
        self.assertEqual(self.db.query(models.TillMovement).count(), 1)
        self.assertEqual(self.db.query(models.TillMovementChange).count(), 1)

    def test_money_committed_during_preview_appears_in_the_next_snapshot_and_flags_review(self):
        order = models.Order(ticket_number='QL-CLOSE-SNAPSHOT', customer_id=self.customer_id,
            service_type='wash_fold', quantity=1, unit_price=1000, total_price=1000, order_date=self.day)
        self.db.add(order)
        self.db.commit()
        order_id = order.id
        confirm_close(self.body(), self.db, self.user, idempotency_key=uuid4())
        inserted = []
        def add_money(connection, cursor, statement, *args):
            if inserted or not statement.lstrip().startswith('SELECT') or 'FROM expenses' not in statement:
                return
            inserted.append(True)
            with self.Session() as writer:
                writer.add(models.Payment(order_id=order_id, payment_method='cash', amount=300,
                    received_date=self.day, confirmed_by_id=self.user_id, confirmed_by_username='save_test'))
                writer.commit()
        event.listen(self.engine, 'before_cursor_execute', add_money)
        try:
            preview = self.preview()
            self.assertTrue(inserted)
            self.assertEqual(Decimal(preview['activity']['cash_received']), 0)
            self.assertFalse(preview['needs_review'])
        finally:
            event.remove(self.engine, 'before_cursor_execute', add_money)
        current = self.preview()
        self.assertEqual(Decimal(current['activity']['cash_received']), 300)
        self.assertTrue(current['needs_review'])
        self.assertEqual(current['latest']['snapshot']['activity']['cash_received'], '0')

    def test_preview_is_read_only_and_pool_isolation_is_restored(self):
        read_close(self.day, self.db, self.user)
        with self.assertRaises(DBAPIError):
            self.db.execute(text("UPDATE users SET username='tampered'"))
        self.db.rollback()
        self.assertEqual(self.db.connection().get_isolation_level(), 'READ COMMITTED')

    def test_repeat_additive_migration_preserves_signed_history(self):
        migration = (Path(__file__).parents[1] / 'migrations/027_add_daily_close.sql').read_text()
        movement = create_movement(TillInput(movement_date=self.day, kind='withdrawal', amount=20),
            self.db, self.user, idempotency_key=uuid4())
        body = self.body().model_copy(update={'counted_cash': Decimal('180')})
        saved = confirm_close(body, self.db, self.user, idempotency_key=uuid4())
        self.db.rollback()
        with self.engine.connect().execution_options(isolation_level='AUTOCOMMIT') as connection:
            connection.exec_driver_sql(migration)
            connection.exec_driver_sql(migration)
            self.assertEqual(connection.execute(text('SELECT count(*) FROM daily_closes')).scalar(), 1)
            self.assertEqual(connection.execute(text('SELECT snapshot FROM daily_closes')).scalar(), saved['snapshot'])
            self.assertEqual(connection.execute(text('SELECT count(*) FROM till_movement_changes')).scalar(), 1)
            for table in ('till_movements', 'till_movement_changes', 'daily_closes'):
                self.assertTrue(connection.execute(text('SELECT relrowsecurity FROM pg_class WHERE oid=CAST(:table AS regclass)'), {'table': table}).scalar())
