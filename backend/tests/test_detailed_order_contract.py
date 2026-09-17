from uuid import uuid4
import asyncio
import unittest
from datetime import datetime, timedelta, timezone

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

    def test_damaged_tally_exception_requires_a_note(self):
        with self.assertRaises(ValidationError):
            schemas.OrderItemExceptionCreate(is_damaged=True)

    def test_outsource_issue_requires_a_note_and_duplicate_returns_are_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.OutsourceReturnItemCreate(
                handover_item_id=1,
                return_condition="issue",
            )
        with self.assertRaises(ValidationError):
            schemas.OutsourceReturnCreate(items=[
                {"handover_item_id": 1, "return_condition": "returned_ok"},
                {"handover_item_id": 1, "return_condition": "returned_ok"},
            ])

    # Only the normal or one-hour peak delay can be saved on an order.
    def test_unknown_peak_delay_is_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.DetailedOrderCreate(
                customer_id=4,
                services=[{"service_id": 1, "quantity": 1}],
                peak_delay_minutes=30,
            )

    def test_discount_requires_a_reason(self):
        with self.assertRaises(ValidationError):
            schemas.DetailedOrderCreate(
                customer_id=4,
                services=[
                    {
                        "service_id": 1,
                        "quantity": 2,
                        "discount_amount": 50,
                    }
                ],
            )


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

    # Physical pieces can exceed charged units, as with a two-piece suit.
    def test_detailed_items_can_exceed_service_quantity(self):
        self.assertEqual(
            logic.get_item_check_status("detailed", 2, [1]),
            "pending",
        )
        self.assertEqual(
            logic.get_item_check_status("detailed", 2, [1, 1]),
            "completed",
        )
        self.assertEqual(
            logic.get_item_check_status("detailed", 1, [1, 1]),
            "completed",
        )


class DetailedOrderRouteTests(unittest.TestCase):
    # Every new read/write route uses the same JWT protection as existing orders.
    def test_detailed_order_routes_require_login(self):
        protected_routes = {
            ("POST", "/orders/detailed"),
            ("GET", "/orders/{order_id}"),
            ("PUT", "/orders/{order_id}/services/{service_line_id}/items"),
            ("POST", "/orders/{order_id}/holds"),
            ("PATCH", "/orders/{order_id}/holds/{hold_id}/resolve"),
            ("POST", "/orders/{order_id}/payments"),
            ("POST", "/orders/{order_id}/services/{service_line_id}/outsourcing"),
            ("POST", "/orders/{order_id}/outsourcing/{handover_id}/returns"),
            ("POST", "/orders/{order_id}/services/{service_line_id}/in-house"),
            ("PATCH", "/orders/{order_id}/outsourcing/{handover_id}/returns/{handover_item_id}/resolve"),
        }

        for route in main.app.routes:
            for method in route.methods or set():
                route_key = (method, route.path)
                if route_key not in protected_routes:
                    continue

                dependency_calls = {
                    dependency.call for dependency in route.dependant.dependencies
                }
                expected_dependency = (
                    auth.require_owner
                    if route.path.endswith("/{handover_item_id}/resolve")
                    or route.path.endswith("/{service_line_id}/in-house")
                    else auth.get_current_user
                )
                self.assertIn(expected_dependency, dependency_calls, route_key)
                protected_routes.remove(route_key)

        self.assertEqual(protected_routes, set())

    def test_outsource_issue_resolution_requires_owner(self):
        route = next(
            route
            for route in main.app.routes
            if route.path == "/orders/{order_id}/outsourcing/{handover_id}/returns/{handover_item_id}/resolve"
        )
        dependency_calls = {
            dependency.call for dependency in route.dependant.dependencies
        }
        self.assertIn(auth.require_owner, dependency_calls)


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
        self.shirt = models.ClothingItemType(name="Shirt", item_group="both")
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
        self.dry_cleaning.category = "dry_cleaning"
        self.dry_cleaning.default_item_type_id = self.shirt.id
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
                        {
                            "item_type_id": self.shirt.id,
                            "description": "White long-sleeved shirt",
                            "is_damaged": False,
                        },
                        {
                            "item_type_id": self.shirt.id,
                            "description": "Blue short-sleeved shirt",
                            "is_damaged": True,
                            "damage_note": "Small tear near cuff",
                        },
                    ],
                },
            ],
        )

        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        self.assertEqual(order.service_type, "mixed")
        self.assertEqual(float(order.total_price), 1525)
        self.assertEqual(len(order.service_lines), 2)
        self.assertEqual(order.service_lines[0].item_check_status, "completed")
        self.assertEqual(order.service_lines[1].item_check_status, "completed")
        self.assertEqual(order.service_lines[1].service_name, "Dry Cleaning - Shirt")
        self.assertEqual(order.service_lines[1].fixed_item_type_id, self.shirt.id)
        self.assertEqual(
            [item.garment_reference for item in order.service_lines[1].items],
            [f"{order.ticket_number}-G01", f"{order.ticket_number}-G02"],
        )
        self.assertEqual(order.next_garment_number, 3)

    def test_discount_and_order_date_are_saved_without_changing_catalogue_price(self):
        order_date = main.get_nairobi_today() - timedelta(days=2)
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            order_date=order_date,
            discount_reason="  Regular customer offer  ",
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 4,
                    "discount_amount": 100,
                    "items": [
                        {"item_type_id": self.shirt.id, "quantity": 4}
                    ],
                }
            ],
        )

        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        self.assertEqual(order.order_date, order_date)
        self.assertTrue(order.ticket_number.startswith(f"QL-{order_date:%Y%m%d}-"))
        self.assertEqual(float(order.unit_price), 150)
        self.assertEqual(float(order.subtotal_before_discount), 600)
        self.assertEqual(float(order.discount_amount), 100)
        self.assertEqual(float(order.total_price), 500)
        self.assertEqual(order.discount_reason, "Regular customer offer")
        self.assertEqual(order.discounted_by_username, self.user.username)
        self.assertEqual(float(order.service_lines[0].line_total), 500)

    def test_discount_cannot_equal_the_service_subtotal(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            discount_reason="Free service",
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 1,
                    "discount_amount": 150,
                }
            ],
        )

        with self.assertRaises(HTTPException) as invalid_discount:
            main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        self.assertEqual(invalid_discount.exception.status_code, 400)
        self.assertIn("must be less than", invalid_discount.exception.detail)

    def test_future_order_date_is_rejected(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            order_date=main.get_nairobi_today() + timedelta(days=1),
            services=[{"service_id": self.wash_fold.id, "quantity": 1}],
        )

        with self.assertRaises(HTTPException) as future_order:
            main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        self.assertEqual(future_order.exception.status_code, 400)
        self.assertIn("future", future_order.exception.detail)

    # Dry Cleaning-only garments cannot be inserted into a Wash & Fold tally.
    def test_dry_cleaning_item_is_rejected_from_laundry_tally(self):
        self.trouser.item_group = "dry_cleaning"
        self.db.commit()

        with self.assertRaises(HTTPException) as wrong_list:
            main.prepare_order_items(
                self.db,
                [schemas.OrderItemCreate(item_type_id=self.trouser.id, quantity=1)],
                "tally",
                1,
            )

        self.assertEqual(wrong_list.exception.status_code, 400)
        self.assertIn("Laundry tally", wrong_list.exception.detail)

    # The employee-confirmed time is saved so the shop can track its promise.
    def test_promised_completion_time_is_saved(self):
        promised_time = datetime.now(timezone.utc) + timedelta(days=3)
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.dry_cleaning.id,
                    "quantity": 1,
                    "items": [
                        {
                            "item_type_id": self.shirt.id,
                            "description": "White office shirt",
                            "is_damaged": False,
                        }
                    ],
                }
            ],
            promised_ready_at=promised_time,
            peak_delay_minutes=60,
        )

        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        # SQLite drops timezone information, so compare the same UTC values.
        saved_time = order.promised_ready_at.replace(tzinfo=timezone.utc)
        self.assertEqual(saved_time, promised_time)
        self.assertEqual(order.peak_delay_minutes, 60)

    def test_detailed_description_is_required(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[{
                "service_id": self.dry_cleaning.id,
                "quantity": 1,
                "items": [{
                    "item_type_id": self.shirt.id,
                    "is_damaged": False,
                }],
            }],
        )

        with self.assertRaises(HTTPException) as missing_description:
            main.create_detailed_order(
                request,
                self.db,
                self.user,
                idempotency_key=uuid4(),
            )

        self.assertIn("Describe every", missing_description.exception.detail)

    def test_suit_pieces_keep_price_and_stable_references_during_corrections(self):
        self.dry_cleaning.name = "Dry Cleaning - 2-piece Suit"
        self.dry_cleaning.unit_price = 750
        self.db.commit()
        order = main.create_detailed_order(
            schemas.DetailedOrderCreate(
                customer_id=self.customer.id,
                services=[{
                    "service_id": self.dry_cleaning.id,
                    "quantity": 1,
                    "items": [
                        {
                            "item_type_id": self.shirt.id,
                            "description": "Navy suit jacket",
                            "is_damaged": False,
                        },
                        {
                            "item_type_id": self.shirt.id,
                            "description": "Matching navy trousers",
                            "is_damaged": False,
                        },
                    ],
                }],
            ),
            self.db,
            self.user,
            idempotency_key=uuid4(),
        )
        line = order.service_lines[0]
        first_item, removed_item = list(line.items)
        removed_item_id = removed_item.id
        removed_reference = removed_item.garment_reference

        saved_line = main.replace_order_service_items(
            order.id,
            line.id,
            schemas.OrderItemsUpdate(
                expected_revision=0,
                change_reason="Corrected the matching trousers",
                items=[
                    {
                        "existing_item_id": first_item.id,
                        "item_type_id": self.shirt.id,
                        "description": "Navy suit jacket",
                        "is_damaged": False,
                    },
                    {
                        "item_type_id": self.shirt.id,
                        "description": "Matching navy trousers with stripe",
                        "is_damaged": False,
                    },
                ],
            ),
            self.db,
            self.user,
        )

        self.assertEqual(float(order.total_price), 750)
        self.assertEqual(saved_line.items[0].id, first_item.id)
        self.assertEqual(saved_line.items[0].garment_reference, f"{order.ticket_number}-G01")
        self.assertEqual(saved_line.items[1].garment_reference, f"{order.ticket_number}-G03")
        self.assertNotEqual(saved_line.items[1].garment_reference, removed_reference)
        self.assertEqual(order.next_garment_number, 4)

        with self.assertRaises(HTTPException) as removed_garment:
            main.replace_order_service_items(
                order.id,
                line.id,
                schemas.OrderItemsUpdate(
                    expected_revision=1,
                    change_reason="Tried an obsolete garment record",
                    items=[{
                        "existing_item_id": removed_item_id,
                        "item_type_id": self.shirt.id,
                        "description": "Old matching trousers",
                        "is_damaged": False,
                    }],
                ),
                self.db,
                self.user,
            )
        self.assertIn("does not belong", removed_garment.exception.detail)

    def test_outsource_partial_return_and_issue_block_ready(self):
        order = main.create_detailed_order(
            schemas.DetailedOrderCreate(
                customer_id=self.customer.id,
                services=[{
                    "service_id": self.dry_cleaning.id,
                    "quantity": 1,
                    "items": [
                        {
                            "item_type_id": self.shirt.id,
                            "description": "Grey suit jacket",
                            "is_damaged": False,
                        },
                        {
                            "item_type_id": self.shirt.id,
                            "description": "Matching grey trousers",
                            "is_damaged": False,
                        },
                    ],
                }],
            ),
            self.db,
            self.user,
            idempotency_key=uuid4(),
        )
        service_line = order.service_lines[0]
        self.assertTrue(service_line.outsourcing_required)
        saved_line = main.create_outsource_handover(
            order.id,
            service_line.id,
            schemas.OutsourceHandoverCreate(
                partner_name="  Trusted Cleaner  ",
                expected_return_at=datetime.now(timezone.utc) + timedelta(days=2),
            ),
            self.db,
            self.user,
        )
        handover = saved_line.outsourcing_handover
        first_return, second_return = list(handover.items)

        self.assertEqual(handover.partner_name, "Trusted Cleaner")
        self.assertEqual(handover.outstanding_count, 2)
        self.assertEqual(
            [item.garment_reference for item in handover.items],
            [item.garment_reference for item in saved_line.items],
        )

        with self.assertRaises(HTTPException) as locked_items:
            main.replace_order_service_items(
                order.id,
                service_line.id,
                schemas.OrderItemsUpdate(
                    expected_revision=0,
                    change_reason="Too late correction",
                    items=[],
                ),
                self.db,
                self.user,
            )
        self.assertIn("handling choice", locked_items.exception.detail)

        main.record_outsource_returns(
            order.id,
            handover.id,
            schemas.OutsourceReturnCreate(items=[{
                "handover_item_id": first_return.id,
                "return_condition": "returned_ok",
            }]),
            self.db,
            self.user,
        )
        self.assertEqual(handover.outstanding_count, 1)

        with self.assertRaises(HTTPException) as duplicate_return:
            main.record_outsource_returns(
                order.id,
                handover.id,
                schemas.OutsourceReturnCreate(items=[{
                    "handover_item_id": first_return.id,
                    "return_condition": "returned_ok",
                }]),
                self.db,
                self.user,
            )
        self.assertIn("already confirmed", duplicate_return.exception.detail)

        main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="in_progress"),
            self.db,
            self.user,
        )
        with self.assertRaises(HTTPException) as missing_piece:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="ready"),
                self.db,
                self.user,
            )
        self.assertIn("outsourced garment", missing_piece.exception.detail)

        main.record_outsource_returns(
            order.id,
            handover.id,
            schemas.OutsourceReturnCreate(items=[{
                "handover_item_id": second_return.id,
                "return_condition": "issue",
                "issue_note": "New mark on the left leg",
            }]),
            self.db,
            self.user,
        )
        self.assertEqual(handover.outstanding_count, 0)
        self.assertEqual(handover.unresolved_issue_count, 1)
        with self.assertRaises(HTTPException) as unresolved_issue:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="ready"),
                self.db,
                self.user,
            )
        self.assertIn("resolve any issue", unresolved_issue.exception.detail)

        owner = models.User(
            username="test_owner",
            password_hash="not-used-by-this-test",
            role="owner",
        )
        self.db.add(owner)
        self.db.commit()
        resolved_line = main.resolve_outsource_issue(
            order.id,
            handover.id,
            second_return.id,
            schemas.OutsourceIssueResolve(
                resolution_note="Cleaner accepted responsibility and corrected it",
            ),
            self.db,
            owner,
        )
        self.assertEqual(
            resolved_line.outsourcing_handover.unresolved_issue_count,
            0,
        )
        ready_order = main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="ready"),
            self.db,
            self.user,
        )
        self.assertEqual(ready_order.status, "ready")

    def test_new_dry_cleaning_needs_handover_or_owner_in_house_confirmation(self):
        order = main.create_detailed_order(
            schemas.DetailedOrderCreate(
                customer_id=self.customer.id,
                services=[{
                    "service_id": self.dry_cleaning.id,
                    "quantity": 1,
                    "items": [{
                        "item_type_id": self.shirt.id,
                        "description": "Cream dinner shirt",
                        "is_damaged": False,
                    }],
                }],
            ),
            self.db,
            self.user,
            idempotency_key=uuid4(),
        )
        line = order.service_lines[0]
        main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="in_progress"),
            self.db,
            self.user,
        )

        with self.assertRaises(HTTPException) as missing_choice:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="ready"),
                self.db,
                self.user,
            )
        self.assertIn("dry-cleaner handover", missing_choice.exception.detail)

        owner = models.User(
            username="in_house_owner",
            password_hash="not-used-by-this-test",
            role="owner",
        )
        self.db.add(owner)
        self.db.commit()
        saved_line = main.confirm_in_house_dry_cleaning(
            order.id,
            line.id,
            schemas.InHouseDryCleaningConfirm(
                reason="Special fabric cleaned with Qinetra equipment",
            ),
            self.db,
            owner,
        )
        self.assertEqual(saved_line.in_house_by_username, owner.username)
        self.assertIsNotNone(saved_line.in_house_at)
        with self.assertRaises(HTTPException) as locked_check:
            main.replace_order_service_items(
                order.id,
                line.id,
                schemas.OrderItemsUpdate(
                    expected_revision=0,
                    change_reason="Attempted after handling choice",
                    items=[],
                ),
                self.db,
                self.user,
            )
        self.assertIn("handling choice", locked_check.exception.detail)
        self.assertEqual(
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="ready"),
                self.db,
                self.user,
            ).status,
            "ready",
        )

    # A direct API request cannot save a customer promise in the past.
    def test_past_promised_completion_time_is_rejected(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[{"service_id": self.wash_fold.id, "quantity": 1}],
            promised_ready_at=datetime.now(timezone.utc) - timedelta(minutes=5),
        )

        with self.assertRaises(HTTPException) as invalid_time:
            main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        self.assertEqual(invalid_time.exception.status_code, 400)

    # A fixed Shirt service cannot be submitted with Trouser garment details.
    def test_fixed_dry_cleaning_garment_cannot_be_changed(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.dry_cleaning.id,
                    "quantity": 1,
                    "items": [
                        {
                            "item_type_id": self.trouser.id,
                            "is_damaged": False,
                        }
                    ],
                }
            ],
        )

        with self.assertRaises(HTTPException) as wrong_garment:
            main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        self.assertEqual(wrong_garment.exception.status_code, 400)

    # Choosing "Do this later" saves the order but blocks washing from starting.
    def test_pending_tally_blocks_progress_until_items_are_added(self):
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
        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())
        service_line = order.service_lines[0]

        self.assertEqual(service_line.item_check_status, "pending")

        with self.assertRaises(HTTPException) as blocked:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="in_progress"),
                self.db,
                self.user,
            )
        self.assertEqual(blocked.exception.status_code, 400)
        self.assertIn("before washing starts", blocked.exception.detail)

        main.replace_order_service_items(
            order.id,
            service_line.id,
            schemas.OrderItemsUpdate(
                items=[{"item_type_id": self.shirt.id, "quantity": 4}]
            ),
            self.db,
            self.user,
        )
        main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="in_progress"),
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

    # Condition exceptions describe affected pieces without changing tally or price.
    def test_tally_exceptions_do_not_double_count_or_change_price(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[{
                "service_id": self.wash_fold.id,
                "quantity": 3,
                "items": [{
                    "item_type_id": self.shirt.id,
                    "quantity": 3,
                    "exceptions": [
                        {
                            "description": "Blue school shirt",
                            "is_damaged": True,
                            "damage_note": "Small tear on right sleeve",
                        },
                        {
                            "description": "White shirt",
                            "stain_note": "Dark stain on collar",
                        },
                    ],
                }],
            }],
        )

        order = main.create_detailed_order(
            request,
            self.db,
            self.user,
            idempotency_key=uuid4(),
        )
        service_line = order.service_lines[0]

        self.assertEqual(float(order.total_price), 450)
        self.assertEqual(service_line.items[0].quantity, 3)
        self.assertEqual(len(service_line.items[0].exceptions), 2)
        self.assertEqual(service_line.item_checked_by_username, self.user.username)
        self.assertIsNotNone(service_line.item_checked_at)
        self.assertEqual(len(service_line.item_history), 1)
        self.assertEqual(
            len(service_line.item_history[0].item_snapshot[0]["exceptions"]),
            2,
        )

    def test_tally_exceptions_cannot_exceed_counted_items(self):
        with self.assertRaises(HTTPException) as too_many:
            main.prepare_order_items(
                self.db,
                [schemas.OrderItemCreate(
                    item_type_id=self.shirt.id,
                    quantity=1,
                    exceptions=[
                        {"description": "Blue shirt"},
                        {"description": "White shirt"},
                    ],
                )],
                "tally",
                1,
            )

        self.assertEqual(too_many.exception.status_code, 400)
        self.assertIn("cannot exceed", too_many.exception.detail)

    # A completed check can change only with a reason, while its first version remains.
    def test_completed_item_check_correction_keeps_history(self):
        order = main.create_detailed_order(
            schemas.DetailedOrderCreate(
                customer_id=self.customer.id,
                services=[{
                    "service_id": self.wash_fold.id,
                    "quantity": 2,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 2}],
                }],
            ),
            self.db,
            self.user,
            idempotency_key=uuid4(),
        )
        service_line = order.service_lines[0]

        with self.assertRaises(HTTPException) as missing_reason:
            main.replace_order_service_items(
                order.id,
                service_line.id,
                schemas.OrderItemsUpdate(
                    items=[{"item_type_id": self.shirt.id, "quantity": 1}],
                    expected_revision=0,
                ),
                self.db,
                self.user,
            )
        self.assertEqual(missing_reason.exception.status_code, 400)

        saved_line = main.replace_order_service_items(
            order.id,
            service_line.id,
            schemas.OrderItemsUpdate(
                items=[{"item_type_id": self.shirt.id, "quantity": 1}],
                expected_revision=0,
                change_reason="One shirt belonged to another customer",
            ),
            self.db,
            self.user,
        )

        self.assertEqual(saved_line.item_revision, 1)
        self.assertEqual(len(saved_line.item_history), 2)
        self.assertEqual(saved_line.item_history[0].item_snapshot[0]["quantity"], 2)
        self.assertEqual(saved_line.item_history[1].item_snapshot[0]["quantity"], 1)
        self.assertEqual(
            saved_line.item_history[1].change_reason,
            "One shirt belonged to another customer",
        )

    # An unanswered clothing question blocks work until the reply is recorded.
    def test_customer_reply_hold_blocks_and_keeps_resolution(self):
        order = main.create_detailed_order(
            schemas.DetailedOrderCreate(
                customer_id=self.customer.id,
                services=[{
                    "service_id": self.wash_fold.id,
                    "quantity": 2,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 2}],
                }],
            ),
            self.db,
            self.user,
            idempotency_key=uuid4(),
        )

        held_order = main.place_customer_reply_hold(
            order.id,
            schemas.OrderHoldCreate(
                reason="Confirm whether bleach may be used on the white shirt",
            ),
            self.db,
            self.user,
        )
        hold = held_order.holds[0]
        self.assertEqual(hold.created_by_username, self.user.username)
        self.assertIsNone(hold.resolved_at)

        with self.assertRaises(HTTPException) as blocked:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="in_progress"),
                self.db,
                self.user,
            )
        self.assertEqual(blocked.exception.status_code, 400)
        self.assertIn("customer's reply", blocked.exception.detail)

        resolved_order = main.resolve_customer_reply_hold(
            order.id,
            hold.id,
            schemas.OrderHoldResolve(
                resolution_note="Customer said not to use bleach",
            ),
            self.db,
            self.user,
        )
        self.assertEqual(
            resolved_order.holds[0].resolution_note,
            "Customer said not to use bleach",
        )
        self.assertEqual(
            resolved_order.holds[0].resolved_by_username,
            self.user.username,
        )

        moved_order = main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="in_progress"),
            self.db,
            self.user,
        )
        self.assertEqual(moved_order.status, "in_progress")

    # Deposits append to payment history and collection waits for the full balance.
    def test_deposit_and_final_payment_control_collection(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 4,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 4}],
                }
            ],
        )
        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        deposit_order = main.record_order_payment(
            order.id,
            schemas.PaymentCreate(
                payment_method="cash",
                amount=200,
                confirmed=True,
            ),
            self.db,
            self.user, idempotency_key=uuid4()
        )
        self.assertEqual(float(deposit_order.amount_paid), 200)
        self.assertEqual(float(deposit_order.balance_due), 400)
        self.assertEqual(deposit_order.payment_status, "part_paid")

        main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="in_progress"),
            self.db,
            self.user,
        )
        main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="ready"),
            self.db,
            self.user,
        )

        with self.assertRaises(HTTPException) as blocked:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="collected"),
                self.db,
                self.user,
            )
        self.assertEqual(blocked.exception.status_code, 400)

        paid_order = main.record_order_payment(
            order.id,
            schemas.PaymentCreate(
                payment_method="mpesa",
                amount=400,
                confirmed=True,
            ),
            self.db,
            self.user, idempotency_key=uuid4()
        )
        self.assertEqual(float(paid_order.balance_due), 0)
        self.assertEqual(paid_order.payment_status, "paid")
        self.assertEqual(len(paid_order.payments), 2)

        collected_order = main.update_order_status(
            order.id,
            schemas.OrderStatusUpdate(status="collected"),
            self.db,
            self.user,
        )
        self.assertEqual(collected_order.status, "collected")

    # Staff must confirm receipt and cannot record more than the order balance.
    def test_unconfirmed_and_excess_payments_are_rejected(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 1,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 1}],
                }
            ],
        )
        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        with self.assertRaises(HTTPException) as unconfirmed:
            main.record_order_payment(
                order.id,
                schemas.PaymentCreate(
                    payment_method="mpesa",
                    amount=100,
                    confirmed=False,
                ),
                self.db,
                self.user, idempotency_key=uuid4()
            )
        self.assertEqual(unconfirmed.exception.status_code, 400)

        with self.assertRaises(HTTPException) as excess:
            main.record_order_payment(
                order.id,
                schemas.PaymentCreate(
                    payment_method="cash",
                    amount=200,
                    confirmed=True,
                ),
                self.db,
                self.user, idempotency_key=uuid4()
            )
        self.assertEqual(excess.exception.status_code, 400)

        with self.assertRaises(HTTPException) as too_small:
            main.record_order_payment(
                order.id,
                schemas.PaymentCreate(
                    payment_method="cash",
                    amount=0.001,
                    confirmed=True,
                ),
                self.db,
                self.user, idempotency_key=uuid4()
            )
        self.assertEqual(too_small.exception.status_code, 400)

    def test_payment_received_date_is_saved_and_checked(self):
        order_date = main.get_nairobi_today() - timedelta(days=2)
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            order_date=order_date,
            services=[{"service_id": self.wash_fold.id, "quantity": 2}],
        )
        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())
        received_date = order_date + timedelta(days=1)

        paid_order = main.record_order_payment(
            order.id,
            schemas.PaymentCreate(
                payment_method="cash",
                amount=100,
                confirmed=True,
                received_date=received_date,
            ),
            self.db,
            self.user, idempotency_key=uuid4()
        )

        self.assertEqual(paid_order.payments[0].received_date, received_date)

        with self.assertRaises(HTTPException) as before_order:
            main.record_order_payment(
                order.id,
                schemas.PaymentCreate(
                    payment_method="cash",
                    amount=50,
                    confirmed=True,
                    received_date=order_date - timedelta(days=1),
                ),
                self.db,
                self.user, idempotency_key=uuid4()
            )
        self.assertEqual(before_order.exception.status_code, 400)

        with self.assertRaises(HTTPException) as future_payment:
            main.record_order_payment(
                order.id,
                schemas.PaymentCreate(
                    payment_method="mpesa",
                    amount=50,
                    confirmed=True,
                    received_date=main.get_nairobi_today() + timedelta(days=1),
                ),
                self.db,
                self.user, idempotency_key=uuid4()
            )
        self.assertEqual(future_payment.exception.status_code, 400)

    # Direct API calls cannot skip the normal four-stage workflow.
    def test_order_status_cannot_skip_a_stage(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 1,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 1}],
                }
            ],
        )
        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())

        with self.assertRaises(HTTPException) as skipped:
            main.update_order_status(
                order.id,
                schemas.OrderStatusUpdate(status="ready"),
                self.db,
                self.user,
            )
        self.assertEqual(skipped.exception.status_code, 400)

    # The tracker, owner summary and CSV must agree with the receipt balance.
    def test_payment_balance_is_consistent_across_reports(self):
        request = schemas.DetailedOrderCreate(
            customer_id=self.customer.id,
            services=[
                {
                    "service_id": self.wash_fold.id,
                    "quantity": 4,
                    "items": [{"item_type_id": self.shirt.id, "quantity": 4}],
                }
            ],
        )
        order = main.create_detailed_order(request, self.db, self.user, idempotency_key=uuid4())
        main.record_order_payment(
            order.id,
            schemas.PaymentCreate(
                payment_method="cash",
                amount=200,
                confirmed=True,
            ),
            self.db,
            self.user, idempotency_key=uuid4()
        )

        outstanding_orders = main.list_orders(
            outstanding=True,
            db=self.db,
            current_user=self.user,
        )
        summary = main.dashboard_summary(self.db, self.user)
        csv_response = main.export_orders_csv(self.db, self.user)

        async def read_csv():
            parts = []
            async for part in csv_response.body_iterator:
                parts.append(part if isinstance(part, bytes) else part.encode())
            return b"".join(parts).decode()

        csv_text = asyncio.run(read_csv())

        self.assertEqual([item.id for item in outstanding_orders], [order.id])
        self.assertEqual(summary.unpaid, 1)
        self.assertEqual(summary.outstanding_balance, 400)
        self.assertIn("Wash & Fold (4 kg)", csv_text)
        self.assertIn(",600.00,0.00,,,600.00,200.00,400.00,part_paid,cash,", csv_text)


if __name__ == "__main__":
    unittest.main()
