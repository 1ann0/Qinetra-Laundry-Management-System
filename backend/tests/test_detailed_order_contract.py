import unittest

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import logic
import main
import models
import schemas


class DetailedOrderSchemaTests(unittest.TestCase):
    # Mixed orders accept different services and keep each service's items together.
    def test_mixed_order_request_is_accepted(self):
        order = schemas.DetailedOrderCreate(
            customer_id=4,
            services=[
                {
                    "service_id": 1,
                    "quantity": 5.5,
                    "items": [{"item_type_id": 2, "quantity": 3}],
                },
                {
                    "service_id": 3,
                    "quantity": 1,
                    "items": [
                        {
                            "item_type_id": 1,
                            "description": "Navy long-sleeved shirt",
                            "is_damaged": False,
                            "stain_note": "Ink stain on left sleeve",
                        }
                    ],
                },
            ],
        )

        self.assertEqual(len(order.services), 2)
        self.assertEqual(order.services[0].items[0].quantity, 3)

    # Selecting the same service twice would make item ownership unclear.
    def test_duplicate_services_are_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.DetailedOrderCreate(
                customer_id=4,
                services=[
                    {"service_id": 1, "quantity": 2},
                    {"service_id": 1, "quantity": 3},
                ],
            )

    # Quantities must be positive before the request reaches price calculation.
    def test_zero_service_and_item_quantities_are_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.DetailedOrderServiceCreate(service_id=1, quantity=0)

        with self.assertRaises(ValidationError):
            schemas.OrderItemCreate(item_type_id=1, quantity=0)

    # Blank optional notes are stored as null instead of meaningless spaces.
    def test_optional_item_notes_are_cleaned(self):
        item = schemas.OrderItemCreate(
            item_type_id=1,
            description="  Navy shirt  ",
            damage_note="   ",
        )

        self.assertEqual(item.description, "Navy shirt")
        self.assertIsNone(item.damage_note)


class ItemCheckRuleTests(unittest.TestCase):
    # Services with no clothing list never create a pending warning.
    def test_no_item_recording_is_not_required(self):
        status = logic.get_item_check_status("none", 1, [])
        self.assertEqual(status, "not_required")

    # An empty tally represents the employee choosing to complete it later.
    def test_empty_tally_is_pending(self):
        status = logic.get_item_check_status("tally", 5.5, [])
        self.assertEqual(status, "pending")

    # Any saved quick tally completes a weight-based clothing check.
    def test_quick_tally_completes_with_items(self):
        status = logic.get_item_check_status("tally", 5.5, [2, 3, 1])
        self.assertEqual(status, "completed")

    # Detailed services need one individual record for every priced garment.
    def test_detailed_items_must_match_service_quantity(self):
        self.assertEqual(
            logic.get_item_check_status("detailed", 2, [1]),
            "pending",
        )
        self.assertEqual(
            logic.get_item_check_status("detailed", 2, [1, 1]),
            "completed",
        )


class DetailedOrderRouteTests(unittest.TestCase):
    # Every new read/write route uses the same JWT protection as existing orders.
    def test_detailed_order_routes_require_login(self):
        protected_routes = {
            ("POST", "/orders/detailed"),
            ("GET", "/orders/{order_id}"),
            ("PUT", "/orders/{order_id}/services/{service_line_id}/items"),
        }

        for route in main.app.routes:
            for method in route.methods or set():
                route_key = (method, route.path)
                if route_key not in protected_routes:
                    continue

                dependency_calls = {
                    dependency.call for dependency in route.dependant.dependencies
                }
                self.assertIn(auth.get_current_user, dependency_calls, route_key)
                protected_routes.remove(route_key)

        self.assertEqual(protected_routes, set())


class DetailedOrderDatabaseTests(unittest.TestCase):
    # Use a temporary database so the real mixed-order save flow is tested safely.
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()

        self.user = models.User(
            username="test_employee",
            password_hash="not-used-by-this-test",
            role="employee",
        )
        self.customer = models.Customer(name="Test Customer", phone="0700000000")
        self.wash_fold = models.Service(
            code="wash_fold",
            name="Wash & Fold",
            unit="kg",
            unit_price=150,
            item_recording_mode="tally",
        )
        self.dry_cleaning = models.Service(
            code="dry_cleaning_shirt",
            name="Dry Cleaning - Shirt",
            unit="item",
            unit_price=350,
            item_recording_mode="detailed",
        )
        self.shirt = models.ClothingItemType(name="Shirt")
        self.trouser = models.ClothingItemType(name="Trouser")

        self.db.add_all([
            self.user,
            self.customer,
            self.wash_fold,
            self.dry_cleaning,
            self.shirt,
            self.trouser,
        ])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    # Price snapshots, service ownership and item status are saved together.
    def test_mixed_order_is_saved_with_service_lines_and_items(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 5.5,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 3}],
                },
                {
                    "service_id": self.dry_cleaning.id,
                    "quantity": 2,
                    "items": [
                        {"item_type_id": self.shirt.id, "is_damaged": False},
                        {
                            "item_type_id": self.trouser.id,
                            "is_damaged": True,
                            "damage_note": "Small tear near pocket",
                        },
                    ],
                },
            ],
        )

        order = main.create_detailed_order(request, self.db, self.user)

        self.assertEqual(order.service_type, "mixed")
        self.assertEqual(float(order.total_price), 1525)
        self.assertEqual(len(order.service_lines), 2)
        self.assertEqual(order.service_lines[0].item_check_status, "completed")
        self.assertEqual(order.service_lines[1].item_check_status, "completed")
        self.assertEqual(order.service_lines[1].service_name, "Dry Cleaning - Shirt")

    # Choosing "Do this later" saves the order but blocks the Ready stage.
    def test_pending_tally_blocks_ready_until_items_are_added(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 4,
                    "items": [],
                }
            ],
        )
        order = main.create_detailed_order(request, self.db, self.user)
        service_line = order.service_lines[0]

        self.assertEqual(service_line.item_check_status, "pending")

        with self.assertRaises(HTTPException) as blocked:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="ready"),
                self.db,
                self.user,
            )
        self.assertEqual(blocked.exception.status_code, 400)

        main.replace_order_service_items(
            order.id,
            service_line.id,
            schemas.OrderItemsUpdate(
                items=[{"item_type_id": self.shirt.id, "quantity": 4}]
            ),
            self.db,
            self.user,
        )
        ready_order = main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="ready"),
            self.db,
            self.user,
        )

        self.assertEqual(ready_order.status, "ready")


if __name__ == "__main__":
    unittest.main()
