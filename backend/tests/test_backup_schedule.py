"""Public job metadata can prevent duplicate scheduled exports, never suppress an unproved backup."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from ops.backup_schedule import backup_required, backup_window


NOW = datetime(2026, 10, 15, 20, 17, tzinfo=timezone.utc)


class BackupScheduleTests(unittest.TestCase):
    def setUp(self):
        self.run = {"id": 123, "event": "schedule", "head_branch": "main", "status": "completed",
                    "conclusion": "success", "created_at": "2026-10-15T19:00:01Z",
                    "repository": {"full_name": "1ann0/Qinetra-Laundry-Management-System"}}
        self.job = {"name": "backup", "status": "completed", "conclusion": "success", "steps": [
            {"name": name, "status": "completed", "conclusion": "success", "completed_at": "2026-10-15T19:01:00Z"}
            for name in ("Require qualified retention before a scheduled run",
                         "Export encrypted archive and authenticate Drive readback", "Signal verified completion")]}
        self.calls = []

    def fetch(self, path):
        self.calls.append(path)
        if "/jobs?" in path:
            return {"total_count": 1, "jobs": [self.job]}
        return {"total_count": 1, "workflow_runs": [self.run]}

    def required(self):
        return backup_required(999, now=NOW, fetch_json=self.fetch)

    def test_successful_scheduled_archive_retention_and_monitor_skip_duplicate(self):
        self.assertFalse(self.required())
        self.assertEqual(len(self.calls), 2)
        self.assertIn("event=schedule", self.calls[0])
        self.assertIn("status=success", self.calls[0])
        self.assertIn("/runs/123/jobs?", self.calls[1])

    def test_manual_old_current_wrong_branch_and_incomplete_runs_do_not_suppress(self):
        for change in ({"event": "workflow_dispatch"}, {"created_at": "2026-10-14T19:00:00Z"},
                       {"id": 999}, {"head_branch": "practice"}, {"status": "in_progress"},
                       {"conclusion": "failure"}, {"created_at": "2026-10-16T19:00:00Z"}):
            with self.subTest(change=change):
                previous = self.run.copy()
                self.run.update(change)
                self.assertTrue(self.required())
                self.run = previous

    def test_overall_success_without_each_real_step_cannot_suppress(self):
        for change in ("skipped", "failure", "missing", "old", "no_time"):
            with self.subTest(change=change):
                previous = deepcopy(self.job)
                if change == "missing":
                    self.job["steps"].pop()
                elif change in ("old", "no_time"):
                    self.job["steps"][1]["completed_at"] = "2026-10-14T19:00:00Z" if change == "old" else None
                else:
                    self.job["steps"][1]["conclusion"] = change
                self.assertTrue(self.required())
                self.job = previous

    def test_metadata_from_another_repository_cannot_suppress_the_pilot_backup(self):
        self.run["repository"] = {"full_name": "other-owner/another-laundry"}
        self.assertTrue(self.required())

    def test_unknown_history_or_provider_failure_makes_a_fresh_backup(self):
        for reply in ({}, {"workflow_runs": []}, {"workflow_runs": "wrong"}):
            self.assertTrue(backup_required(999, now=NOW, fetch_json=lambda path: reply))
        def unavailable(path):
            raise RuntimeError("fictional sensitive provider error")
        self.assertTrue(backup_required(999, now=NOW, fetch_json=unavailable))

    def test_midnight_nairobi_and_late_trigger_keep_the_original_backup_day(self):
        for hours in (0, 1, 3, 8, 23):
            moment = datetime(2026, 10, 15, 19, tzinfo=timezone.utc) + timedelta(hours=hours)
            self.assertEqual(backup_window(moment), datetime(2026, 10, 15, 19, tzinfo=timezone.utc))
        self.assertEqual(backup_window(datetime(2026, 10, 16, 19, tzinfo=timezone.utc)).day, 16)
        with self.assertRaises(ValueError):
            backup_window(NOW.replace(tzinfo=None))

    def test_budgeted_fallback_is_bounded_when_history_is_large_or_malformed(self):
        def many(path):
            self.calls.append(path)
            if "/jobs?" in path:
                return {"jobs": []}
            return {"workflow_runs": [self.run | {"id": number} for number in range(1, 101)]}
        self.assertTrue(backup_required(999, now=NOW, fetch_json=many))
        self.assertLessEqual(len(self.calls), 11)


if __name__ == "__main__":
    unittest.main()
