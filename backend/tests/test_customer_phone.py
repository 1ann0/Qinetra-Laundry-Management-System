"""Customer phone rules stay consistent across registration, search and M-PESA."""

import unittest

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from customer_phone import (
    display_kenyan_phone,
    normalize_kenyan_phone,
    phone_search_digits,
)
import main
import models
import schemas


class KenyanPhoneTests(unittest.TestCase):
    def test_common_formats_share_one_canonical_value(self):
        expected = "254712345678"
        for phone in [
            "0712345678",
            "0712 345 678",
            "0712-345-678",
            "712345678",
            "254712345678",
            "+254 712 345 678",
        ]:
            with self.subTest(phone=phone):
                self.assertEqual(normalize_kenyan_phone(phone), expected)

    def test_newer_01_mobile_numbers_are_supported(self):
        self.assertEqual(normalize_kenyan_phone("0112 345 678"), "254112345678")

    def test_display_uses_the_familiar_local_format(self):
        self.assertEqual(display_kenyan_phone("+254 712 345 678"), "0712345678")

    def test_malformed_or_non_mobile_values_are_rejected(self):
        for phone in ["", "254", "020 123 4567", "0712ABC678", "07123456789"]:
            with self.subTest(phone=phone), self.assertRaises(ValueError):
                normalize_kenyan_phone(phone)

    def test_partial_phone_search_removes_only_safe_formatting(self):
        self.assertEqual(phone_search_digits("+254 712"), "254712")
        self.assertEqual(phone_search_digits("0712-34"), "25471234")
        self.assertEqual(phone_search_digits("Alice"), "")


class CustomerPhoneDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        models.Base.metadata.create_all(self.engine)
        self.db = sessionmaker(bind=self.engine)()
        self.employee = models.User(
            username="customer_test",
            password_hash="unused",
            role="employee",
        )
        self.db.add(self.employee)
        self.db.commit()

    def tearDown(self):
        self.db.close()
        self.engine.dispose()

    def test_invalid_customer_phone_is_rejected_before_database_work(self):
        with self.assertRaises(ValidationError):
            schemas.CustomerCreate(name="Jane Wanjiku", phone="020 123 4567")

    def test_duplicate_requires_an_explicit_separate_customer_choice(self):
        first = main.create_customer(
            schemas.CustomerCreate(name="Jane Wanjiku", phone="0712 345 678"),
            self.db,
            self.employee,
        )
        self.assertEqual(first.customer.phone, "0712345678")
        self.assertEqual(
            self.db.get(models.Customer, first.customer.id).phone_normalized,
            "254712345678",
        )

        with self.assertRaises(HTTPException) as duplicate:
            main.create_customer(
                schemas.CustomerCreate(
                    name="John Wanjiku",
                    phone="+254 712 345 678",
                ),
                self.db,
                self.employee,
            )
        self.assertEqual(duplicate.exception.status_code, 409)

        second = main.create_customer(
            schemas.CustomerCreate(
                name="John Wanjiku",
                phone="+254 712 345 678",
                allow_duplicate=True,
            ),
            self.db,
            self.employee,
        )
        self.assertIsNotNone(second.duplicate_warning)
        self.assertEqual(self.db.query(models.Customer).count(), 2)

    def test_phone_match_and_search_accept_different_formats(self):
        saved = main.create_customer(
            schemas.CustomerCreate(name="Jane Wanjiku", phone="0712345678"),
            self.db,
            self.employee,
        ).customer

        matches = main.find_customers_by_phone(
            "+254 712 345 678",
            self.db,
            self.employee,
        )
        international_results = main.list_customers(
            search="254 712",
            db=self.db,
            current_user=self.employee,
        )
        local_results = main.list_customers(
            search="0712",
            db=self.db,
            current_user=self.employee,
        )

        self.assertEqual([customer.id for customer in matches], [saved.id])
        self.assertEqual([customer.id for customer in international_results], [saved.id])
        self.assertEqual([customer.id for customer in local_results], [saved.id])


if __name__ == "__main__":
    unittest.main()
