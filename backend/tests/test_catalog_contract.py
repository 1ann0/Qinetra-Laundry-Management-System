import unittest

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import auth
import main
import models
import schemas


class CatalogSchemaTests(unittest.TestCase):
    # A valid service keeps the clean values the API will save.
    def test_valid_service_is_accepted(self):
        service = schemas.ServiceCreate(
            name="  Shoe Cleaning  ",
            unit="pair",
            unit_price=600,
            item_recording_mode="tally",
        )

        self.assertEqual(service.name, "Shoe Cleaning")
        self.assertEqual(service.unit, "pair")
        self.assertEqual(service.unit_price, 600)
        self.assertEqual(service.item_recording_mode, "tally")

    # Turnaround must be positive because it becomes a customer promise.
    def test_invalid_turnaround_is_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.ServiceCreate(
                name="Shoe Cleaning",
                unit="pair",
                unit_price=600,
                turnaround_minutes=0,
            )

    # Prices must be positive so an accidental zero-priced service is rejected.
    def test_zero_service_price_is_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.ServiceCreate(
                name="Shoe Cleaning",
                unit="pair",
                unit_price=0,
            )

    # The three supported pricing units keep calculations understandable.
    def test_unknown_service_unit_is_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.ServiceCreate(
                name="Shoe Cleaning",
                unit="bundle",
                unit_price=600,
            )

    # Names containing only spaces should not enter the shop catalogue.
    def test_blank_catalog_names_are_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.ServiceCreate(name="   ", unit="item", unit_price=100)

        with self.assertRaises(ValidationError):
            schemas.ClothingItemTypeCreate(name="   ")

    # Deactivation is supported so old records never need catalogue deletion.
    def test_catalog_entries_can_be_deactivated(self):
        service_update = schemas.ServiceUpdate(is_active=False)
        item_update = schemas.ClothingItemTypeUpdate(is_active=False)

        self.assertFalse(service_update.is_active)
        self.assertFalse(item_update.is_active)

    # Clothing names must state which employee list should display them.
    def test_unknown_clothing_item_group_is_rejected(self):
        with self.assertRaises(ValidationError):
            schemas.ClothingItemTypeCreate(
                name="Curtain",
                item_group="household",
            )

    # Detailed garments need piece-based pricing so completion can be checked.
    def test_detailed_garments_cannot_use_kg_pricing(self):
        with self.assertRaises(ValidationError):
            schemas.ServiceCreate(
                name="Detailed Dry Cleaning",
                unit="kg",
                unit_price=500,
                item_recording_mode="detailed",
            )

    # A Dry Cleaning price must identify the garment it is charging for.
    def test_dry_cleaning_service_requires_linked_garment(self):
        with self.assertRaises(ValidationError):
            schemas.ServiceCreate(
                name="Dry Cleaning - Jacket",
                unit="item",
                unit_price=500,
                category="dry_cleaning",
                item_recording_mode="detailed",
            )

        service = schemas.ServiceCreate(
            name="Dry Cleaning - Jacket",
            unit="item",
            unit_price=500,
            category="dry_cleaning",
            default_item_type_id=4,
            item_recording_mode="detailed",
        )
        self.assertEqual(service.default_item_type_id, 4)


class CatalogPermissionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.owner = models.User(
            username="catalog_owner",
            password_hash="not-used",
            role="owner",
        )
        self.employee = models.User(
            username="catalog_employee",
            password_hash="not-used",
            role="employee",
        )
        self.db.add_all([self.owner, self.employee])
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_employee_can_add_an_active_laundry_tally_item(self):
        saved_item = main.create_clothing_item_type(
            schemas.ClothingItemTypeCreate(
                name="  School Skirt  ",
                item_group="laundry",
            ),
            db=self.db,
            current_user=self.employee,
        )

        self.assertEqual(saved_item.name, "School Skirt")
        self.assertEqual(saved_item.item_group, "laundry")
        self.assertTrue(saved_item.is_active)

    def test_employee_cannot_add_dry_cleaning_or_shared_items(self):
        for item_group in ["dry_cleaning", "both"]:
            with self.assertRaises(HTTPException) as error:
                main.create_clothing_item_type(
                    schemas.ClothingItemTypeCreate(
                        name=f"Employee {item_group}",
                        item_group=item_group,
                    ),
                    db=self.db,
                    current_user=self.employee,
                )
            self.assertEqual(error.exception.status_code, 403)

    def test_owner_keeps_full_item_group_control(self):
        saved_item = main.create_clothing_item_type(
            schemas.ClothingItemTypeCreate(
                name="Evening Gown",
                item_group="dry_cleaning",
            ),
            db=self.db,
            current_user=self.owner,
        )
        self.assertEqual(saved_item.item_group, "dry_cleaning")

    def test_inactive_duplicate_must_be_restored_by_the_owner(self):
        existing_item = models.ClothingItemType(
            name="School Sweater",
            item_group="laundry",
            is_active=False,
        )
        self.db.add(existing_item)
        self.db.commit()

        with self.assertRaises(HTTPException) as error:
            main.create_clothing_item_type(
                schemas.ClothingItemTypeCreate(name="school sweater"),
                db=self.db,
                current_user=self.employee,
            )

        self.assertEqual(error.exception.status_code, 400)
        self.assertIn("inactive", error.exception.detail)
        self.assertEqual(
            self.db.query(models.ClothingItemType).filter(
                models.ClothingItemType.name.ilike("school sweater")
            ).count(),
            1,
        )

    def test_active_duplicate_does_not_create_a_second_catalogue_item(self):
        main.create_clothing_item_type(
            schemas.ClothingItemTypeCreate(name="Track Suit"),
            db=self.db,
            current_user=self.employee,
        )

        with self.assertRaises(HTTPException) as error:
            main.create_clothing_item_type(
                schemas.ClothingItemTypeCreate(name="track suit"),
                db=self.db,
                current_user=self.owner,
            )

        self.assertEqual(error.exception.status_code, 400)
        self.assertEqual(
            self.db.query(models.ClothingItemType).filter(
                models.ClothingItemType.name.ilike("track suit")
            ).count(),
            1,
        )

    def test_create_requires_login_but_updates_remain_owner_only(self):
        expected_dependencies = {
            ("POST", "/catalog/item-types"): auth.get_current_user,
            ("PATCH", "/catalog/item-types/{item_type_id}"): auth.require_owner,
        }

        for route in main.app.routes:
            for method in getattr(route, "methods", None) or set():
                route_key = (method, route.path)
                if route_key not in expected_dependencies:
                    continue
                dependency_calls = {
                    dependency.call for dependency in route.dependant.dependencies
                }
                self.assertIn(expected_dependencies.pop(route_key), dependency_calls)

        self.assertEqual(expected_dependencies, {})


if __name__ == "__main__":
    unittest.main()
