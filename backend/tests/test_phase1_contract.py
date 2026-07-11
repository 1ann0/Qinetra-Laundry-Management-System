import unittest

from pydantic import ValidationError

import auth
import logic
import main
import schemas


class PricingContractTests(unittest.TestCase):
    def test_confirmed_service_prices(self):
        expected_prices = {
            "wash_fold": 150,
            "duvet": 800,
            "dry_cleaning_shirt": 350,
            "dry_cleaning_trouser": 350,
            "dry_cleaning_suit": 750,
        }

        self.assertEqual(logic.PRICING, expected_prices)

        for service_type, unit_price in expected_prices.items():
            self.assertEqual(
                logic.calculate_price(service_type, 2),
                (unit_price, unit_price * 2),
            )

    def test_generic_dry_cleaning_is_no_longer_accepted(self):
        with self.assertRaises(ValidationError):
            schemas.OrderCreate(
                customer_id=1,
                service_type="dry_cleaning",
                quantity=1,
            )


class AuthenticationContractTests(unittest.TestCase):
    def test_operational_routes_require_current_user(self):
        operational_routes = {
            ("POST", "/customers"),
            ("GET", "/customers"),
            ("POST", "/orders"),
            ("GET", "/orders"),
            ("GET", "/orders/overdue"),
            ("PATCH", "/orders/{order_id}/status"),
        }

        for route in main.app.routes:
            for method in route.methods or set():
                route_key = (method, route.path)
                if route_key not in operational_routes:
                    continue

                dependency_calls = {
                    dependency.call for dependency in route.dependant.dependencies
                }
                self.assertIn(auth.get_current_user, dependency_calls, route_key)
                operational_routes.remove(route_key)

        self.assertEqual(operational_routes, set())


if __name__ == "__main__":
    unittest.main()
