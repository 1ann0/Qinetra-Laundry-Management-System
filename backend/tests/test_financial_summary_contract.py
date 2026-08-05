import unittest
from datetime import date, datetime, timezone

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models


class FinancialSummaryTests(unittest.TestCase):
    # Use a temporary database so financial calculations never touch Supabase.
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.owner = models.User(
            username="test_owner",
            password_hash="not-used-by-this-test",
            role="owner",
        )
        self.employee = models.User(
            username="test_employee",
            password_hash="not-used-by-this-test",
            role="employee",
        )
        self.customer = models.Customer(name="Test Customer", phone="0700000000")
        self.second_customer = models.Customer(
            name="Second Customer",
            phone="0711111111",
        )
        self.db.add_all([
            self.owner,
            self.employee,
            self.customer,
            self.second_customer,
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def add_order(self, ticket_number, total_price, created_at, customer=None):
        order = models.Order(
            ticket_number=ticket_number,
            customer_id=(customer or self.customer).id,
            service_type="wash_fold",
            quantity=1,
            unit_price=total_price,
            total_price=total_price,
            order_date=created_at.astimezone(main.NAIROBI_TIMEZONE).date(),
            created_at=created_at,
        )
        self.db.add(order)
        self.db.commit()
        return order

    def add_payment(self, order, method, amount, created_at):
        payment = models.Payment(
            order_id=order.id,
            payment_method=method,
            amount=amount,
            confirmed_by_id=self.owner.id,
            confirmed_by_username=self.owner.username,
            received_date=created_at.astimezone(main.NAIROBI_TIMEZONE).date(),
            created_at=created_at,
        )
        self.db.add(payment)
        self.db.commit()

    # Orders use their booking time while receipts use the payment time.
    def test_orders_and_received_payments_use_separate_dates(self):
        selected_order = self.add_order(
            "QL-20260802-001",
            600,
            datetime(2026, 8, 2, 8, tzinfo=timezone.utc),
        )
        older_order = self.add_order(
            "QL-20260731-001",
            900,
            datetime(2026, 7, 31, 8, tzinfo=timezone.utc),
            self.second_customer,
        )
        self.add_payment(
            selected_order,
            "cash",
            200,
            datetime(2026, 8, 2, 9, tzinfo=timezone.utc),
        )
        self.add_payment(
            older_order,
            "mpesa",
            300,
            datetime(2026, 8, 2, 10, tzinfo=timezone.utc),
        )
        self.add_payment(
            older_order,
            "legacy",
            400,
            datetime(2026, 8, 2, 11, tzinfo=timezone.utc),
        )

        summary = main.financial_summary(
            date(2026, 8, 2),
            date(2026, 8, 2),
            self.db,
            self.owner,
        )

        self.assertEqual(summary.orders_booked, 1)
        self.assertEqual(summary.gross_order_value, 600)
        self.assertEqual(summary.discounts_given, 0)
        self.assertEqual(summary.order_value, 600)
        self.assertEqual(summary.cash_received, 200)
        self.assertEqual(summary.mpesa_received, 300)
        self.assertEqual(summary.total_received, 500)
        self.assertEqual(summary.outstanding_orders, 1)
        self.assertEqual(summary.outstanding_balance, 400)
        self.assertEqual(len(summary.daily_received), 1)
        self.assertEqual(summary.daily_received[0].date, date(2026, 8, 2))
        self.assertEqual(summary.daily_received[0].amount, 500)
        self.assertEqual(
            [customer.customer_name for customer in summary.customer_revenue],
            ["Second Customer", "Test Customer"],
        )
        self.assertEqual(
            [customer.total_received for customer in summary.customer_revenue],
            [300, 200],
        )
        self.assertEqual(len(summary.top_services), 1)
        self.assertEqual(summary.top_services[0].service_name, "Wash & Fold")
        self.assertEqual(summary.top_services[0].order_count, 1)
        self.assertEqual(summary.top_services[0].booked_value, 600)

    # A Nairobi day starts at 21:00 UTC on the previous calendar date.
    def test_nairobi_day_boundaries_are_used(self):
        inside_start = self.add_order(
            "QL-20260802-002",
            150,
            datetime(2026, 8, 1, 21, tzinfo=timezone.utc),
        )
        self.add_order(
            "QL-20260801-001",
            200,
            datetime(2026, 8, 1, 20, 59, 59, tzinfo=timezone.utc),
        )
        self.add_order(
            "QL-20260803-001",
            300,
            datetime(2026, 8, 2, 21, tzinfo=timezone.utc),
        )
        self.add_payment(
            inside_start,
            "cash",
            150,
            datetime(2026, 8, 2, 20, 59, 59, tzinfo=timezone.utc),
        )

        summary = main.financial_summary(
            date(2026, 8, 2),
            date(2026, 8, 2),
            self.db,
            self.owner,
        )

        self.assertEqual(summary.orders_booked, 1)
        self.assertEqual(summary.order_value, 150)
        self.assertEqual(summary.total_received, 150)
        self.assertEqual(summary.outstanding_balance, 0)
        self.assertEqual(summary.daily_received[0].date, date(2026, 8, 2))
        self.assertEqual(summary.daily_received[0].amount, 150)

    # Empty days remain in the series so the line graph shows real gaps.
    def test_daily_series_includes_zero_payment_days(self):
        order = self.add_order(
            "QL-20260803-001",
            300,
            datetime(2026, 8, 3, 8, tzinfo=timezone.utc),
        )
        self.add_payment(
            order,
            "mpesa",
            300,
            datetime(2026, 8, 3, 9, tzinfo=timezone.utc),
        )

        summary = main.financial_summary(
            date(2026, 8, 2),
            date(2026, 8, 4),
            self.db,
            self.owner,
        )

        self.assertEqual(
            [point.date for point in summary.daily_received],
            [date(2026, 8, 2), date(2026, 8, 3), date(2026, 8, 4)],
        )
        self.assertEqual(
            [point.amount for point in summary.daily_received],
            [0, 300, 0],
        )

    def test_empty_period_returns_zero_totals(self):
        summary = main.financial_summary(
            date(2026, 8, 5),
            date(2026, 8, 5),
            self.db,
            self.owner,
        )

        self.assertEqual(summary.orders_booked, 0)
        self.assertEqual(summary.gross_order_value, 0)
        self.assertEqual(summary.discounts_given, 0)
        self.assertEqual(summary.order_value, 0)
        self.assertEqual(summary.cash_received, 0)
        self.assertEqual(summary.mpesa_received, 0)
        self.assertEqual(summary.total_received, 0)
        self.assertEqual(summary.outstanding_orders, 0)
        self.assertEqual(summary.outstanding_balance, 0)
        self.assertEqual(len(summary.daily_received), 1)
        self.assertEqual(summary.daily_received[0].amount, 0)
        self.assertEqual(summary.customer_revenue, [])
        self.assertEqual(summary.top_services, [])

    # Mixed service lines and older single-service orders belong in one ranking.
    def test_top_services_include_mixed_and_legacy_orders(self):
        wash_fold = models.Service(
            code="wash_fold",
            name="Wash & Fold",
            unit="kg",
            unit_price=150,
            category="general",
            item_recording_mode="tally",
        )
        duvet = models.Service(
            code="duvet",
            name="Duvet Cleaning",
            unit="item",
            unit_price=800,
            category="general",
            item_recording_mode="none",
        )
        self.db.add_all([wash_fold, duvet])
        self.db.commit()

        mixed_order = self.add_order(
            "QL-20260804-001",
            1000,
            datetime(2026, 8, 4, 8, tzinfo=timezone.utc),
        )
        mixed_order.service_type = "mixed"
        mixed_order.quantity = 2
        mixed_order.service_lines.extend([
            models.OrderServiceLine(
                service_id=wash_fold.id,
                service_name=wash_fold.name,
                service_unit=wash_fold.unit,
                quantity=2,
                unit_price=150,
                subtotal=300,
                item_recording_mode="tally",
                item_check_status="completed",
            ),
            models.OrderServiceLine(
                service_id=duvet.id,
                service_name=duvet.name,
                service_unit=duvet.unit,
                quantity=1,
                unit_price=800,
                subtotal=800,
                discount_amount=100,
                item_recording_mode="none",
                item_check_status="not_required",
            ),
        ])

        legacy_order = self.add_order(
            "QL-20260804-002",
            450,
            datetime(2026, 8, 4, 9, tzinfo=timezone.utc),
        )
        legacy_order.quantity = 3
        legacy_order.unit_price = 150
        self.db.commit()

        summary = main.financial_summary(
            date(2026, 8, 4),
            date(2026, 8, 4),
            self.db,
            self.owner,
        )

        self.assertEqual(
            [service.service_name for service in summary.top_services],
            ["Wash & Fold", "Duvet Cleaning"],
        )
        self.assertEqual(summary.gross_order_value, 1550)
        self.assertEqual(summary.discounts_given, 100)
        self.assertEqual(summary.order_value, 1450)
        self.assertEqual(summary.top_services[0].booked_value, 750)
        self.assertEqual(summary.top_services[0].quantity_booked, 5)
        self.assertEqual(summary.top_services[0].order_count, 2)
        self.assertEqual(summary.top_services[1].booked_value, 700)
        self.assertEqual(summary.top_services[1].order_count, 1)

    def test_end_date_before_start_date_is_rejected(self):
        with self.assertRaises(HTTPException) as invalid_range:
            main.financial_summary(
                date(2026, 8, 3),
                date(2026, 8, 2),
                self.db,
                self.owner,
            )

        self.assertEqual(invalid_range.exception.status_code, 400)
        self.assertEqual(
            invalid_range.exception.detail,
            "End date cannot be before start date",
        )

    # FastAPI applies the owner dependency before the route function runs.
    def test_financial_summary_route_requires_owner(self):
        matching_routes = [
            route
            for route in main.app.routes
            if route.path == "/dashboard/financial-summary"
        ]

        self.assertEqual(len(matching_routes), 1)
        dependency_calls = {
            dependency.call
            for dependency in matching_routes[0].dependant.dependencies
        }
        self.assertIn(auth.require_owner, dependency_calls)

    def test_employee_is_rejected_by_owner_check(self):
        with self.assertRaises(HTTPException) as denied:
            auth.require_owner(self.employee)

        self.assertEqual(denied.exception.status_code, 403)
        self.assertEqual(denied.exception.detail, "Owner access required")


if __name__ == "__main__":
    unittest.main()
