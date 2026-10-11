"""Storage calculations use bytes, not a forecast of shop trading volume."""
import unittest

from ops.backup_budget import backup_projection


class BackupBudgetTests(unittest.TestCase):
    def test_small_fixture_and_ten_mb_archive_use_exact_decimal_bytes(self):
        small = backup_projection(103573, 90)
        self.assertEqual(small["projected_retained_bytes"], 9321570)
        self.assertEqual(small["usable_budget_bytes"], 4000000000)
        self.assertEqual(small["reserved_bytes"], 1000000000)
        self.assertEqual(backup_projection(10000000, 90)["projected_retained_bytes"], 900000000)

    def test_20_percent_headroom_boundary_has_no_rounding_error(self):
        self.assertEqual(backup_projection(44444444, 90)["maximum_daily_bytes"], 44444444)
        with self.assertRaises(ValueError):
            backup_projection(44444445, 90)

    def test_rejects_unknown_negative_fractional_or_unapproved_budget(self):
        for arguments in [(0, 90), (-1, 90), (True, 90), (1.5, 90), (10, 0),
                          (10, True), (10, 90, 0), (10, 90, 5000000001)]:
            with self.subTest(arguments=arguments), self.assertRaises(ValueError):
                backup_projection(*arguments)


if __name__ == "__main__":
    unittest.main()
