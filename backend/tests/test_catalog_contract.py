import unittest

from pydantic import ValidationError

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


if __name__ == "__main__":
    unittest.main()
