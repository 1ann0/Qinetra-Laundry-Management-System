"""The live closing release must not reapply access across existing shop tables."""
import unittest
from ops.schema_setup import daily_close_access_sql


class DailyCloseAccessTests(unittest.TestCase):
    def test_release_access_is_limited_to_the_three_new_tables_and_sequences(self):
        sql=daily_close_access_sql('qlms','qlms_runtime','qlms_backup')
        for forbidden in ('ALL TABLES', 'ALL SEQUENCES', 'ALTER DEFAULT', 'ALTER ROLE',
                          'ON SCHEMA', '.users', '.expenses', '.customers'):
            self.assertNotIn(forbidden,sql)
        for table in ('till_movements','till_movement_changes','daily_closes'):
            self.assertIn('"qlms".'+table,sql)
        self.assertNotIn('GRANT DELETE',sql)
        self.assertIn('GRANT SELECT, INSERT ON "qlms".daily_closes',sql)
        self.assertIn('GRANT SELECT, INSERT ON "qlms".till_movement_changes',sql)

    def test_unsafe_identifiers_are_rejected(self):
        with self.assertRaises(ValueError):
            daily_close_access_sql('qlms; DROP SCHEMA public','qlms_runtime','qlms_backup')
