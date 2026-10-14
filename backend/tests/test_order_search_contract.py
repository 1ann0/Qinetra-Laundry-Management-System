import unittest
from datetime import date, datetime, timezone

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models


class OrderSearchContractTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.employee = models.User(
            username="search_employee",
            password_hash="not-used-by-this-contract",
            role="employee",
        )
        self.alice = models.Customer(name="Alice Wanjiku", phone="0712 345 678")
        self.brian = models.Customer(name="Brian Otieno", phone="0799 555 111")
        self.dry_cleaning = models.Service(
            code="dry_cleaning",
            name="Dry Cleaning",
            unit="item",
            unit_price=350,
            category="dry_cleaning",
            item_recording_mode="detailed",
            turnaround_minutes=1440,
            is_active=True,
        )
        self.wash_fold = models.Service(
            code="wash_fold",
            name="Wash & Fold",
            unit="kg",
            unit_price=150,
            category="general",
            item_recording_mode="tally",
            turnaround_minutes=180,
            is_active=True,
        )
        self.db.add_all(
            [
                self.employee,
                self.alice,
                self.brian,
                self.dry_cleaning,
                self.wash_fold,
            ]
        )
        self.db.commit()

        self.mixed_order = models.Order(
            ticket_number="QL-20260810-001",
            customer_id=self.alice.id,
            service_type="mixed",
            quantity=1,
            unit_price=750,
            total_price=750,
            status="in_progress",
            order_date=date(2026, 8, 10),
            created_at=datetime(2026, 8, 10, 8, 0, tzinfo=timezone.utc),
        )
        self.mixed_order.service_lines.append(
            models.OrderServiceLine(
                service_id=self.dry_cleaning.id,
                service_name="Dry Cleaning",
                service_unit="item",
                quantity=1,
                unit_price=750,
                subtotal=750,
                discount_amount=0,
                item_recording_mode="detailed",
                item_check_status="completed",
            )
        )
        self.legacy_order = models.Order(
            ticket_number="QL-20260809-004",
            customer_id=self.brian.id,
            service_type="wash_fold",
            quantity=3.5,
            unit_price=150,
            total_price=525,
            status="received",
            order_date=date(2026, 8, 9),
            created_at=datetime(2026, 8, 9, 9, 0, tzinfo=timezone.utc),
        )
        self.db.add_all([self.mixed_order, self.legacy_order])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def search(
        self,
        value=None,
        status=None,
        customer_id=None,
        service_id=None,
        start_date=None,
        end_date=None,
    ):
        return main.list_orders(
            status=status,
            search=value,
            customer_id=customer_id,
            service_id=service_id,
            start_date=start_date,
            end_date=end_date,
            outstanding=False,
            due_today=False,
            production_late=False,
            db=self.db,
            current_user=self.employee,
        )

    def assert_order_ids(self, orders, expected_ids):
        self.assertEqual([order.id for order in orders], expected_ids)

    def test_ticket_customer_name_and_phone_are_searchable(self):
        self.assert_order_ids(self.search("0810-001"), [self.mixed_order.id])
        self.assert_order_ids(self.search("wAnJiKu"), [self.mixed_order.id])
        self.assert_order_ids(self.search("555 111"), [self.legacy_order.id])

    def test_mixed_and_legacy_service_names_are_searchable(self):
        self.assert_order_ids(self.search("Dry Cleaning"), [self.mixed_order.id])
        self.assert_order_ids(self.search("Wash & Fold"), [self.legacy_order.id])

    def test_search_combines_with_the_existing_status_filter(self):
        self.assert_order_ids(
            self.search("Alice", status="in_progress"),
            [self.mixed_order.id],
        )
        self.assert_order_ids(self.search("Alice", status="received"), [])

    def test_blank_search_keeps_the_existing_order_list(self):
        self.assert_order_ids(
            self.search("   "),
            [self.mixed_order.id, self.legacy_order.id],
        )

    def test_unknown_search_returns_an_empty_list(self):
        self.assert_order_ids(self.search("not a real ticket"), [])

    def test_customer_history_uses_the_exact_customer_id(self):
        self.assert_order_ids(
            self.search(customer_id=self.alice.id),
            [self.mixed_order.id],
        )
        self.assert_order_ids(
            self.search(customer_id=self.brian.id),
            [self.legacy_order.id],
        )

    def test_service_history_includes_mixed_and_legacy_orders(self):
        self.assert_order_ids(
            self.search(service_id=self.dry_cleaning.id),
            [self.mixed_order.id],
        )
        self.assert_order_ids(
            self.search(service_id=self.wash_fold.id),
            [self.legacy_order.id],
        )

    def test_business_date_range_is_inclusive(self):
        self.assert_order_ids(
            self.search(
                start_date=date(2026, 8, 9),
                end_date=date(2026, 8, 10),
            ),
            [self.mixed_order.id, self.legacy_order.id],
        )
        self.assert_order_ids(
            self.search(
                start_date=date(2026, 8, 10),
                end_date=date(2026, 8, 10),
            ),
            [self.mixed_order.id],
        )

    def test_history_filters_can_be_combined(self):
        self.assert_order_ids(
            self.search(
                status="in_progress",
                customer_id=self.alice.id,
                service_id=self.dry_cleaning.id,
                start_date=date(2026, 8, 10),
                end_date=date(2026, 8, 10),
            ),
            [self.mixed_order.id],
        )
        self.assert_order_ids(
            self.search(
                customer_id=self.alice.id,
                service_id=self.wash_fold.id,
            ),
            [],
        )

    def test_reversed_date_range_is_rejected(self):
        with self.assertRaises(main.HTTPException) as error:
            self.search(
                start_date=date(2026, 8, 10),
                end_date=date(2026, 8, 9),
            )

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(error.exception.detail, "End date cannot be before start date")

    def test_unknown_service_history_is_empty(self):
        self.assert_order_ids(self.search(service_id=9999), [])

    def test_order_list_route_still_requires_authentication(self):
        order_route = next(
            route
            for route in main.app.routes
            if getattr(route, "path", None) == "/orders" and "GET" in (route.methods or set())
        )
        dependency_calls = {
            dependency.call for dependency in order_route.dependant.dependencies
        }
        self.assertIn(auth.get_current_user, dependency_calls)


if __name__ == "__main__":
    unittest.main()
