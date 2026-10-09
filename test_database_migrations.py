import os
import sqlite3
import tempfile
import unittest

from python.database.databasemanager import DatabaseManager


class DatabaseMigrationsTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.database = DatabaseManager(db_name=self.temp_db.name)

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)

    def test_calendar_events_table_and_crud(self):
        self.assertTrue(self.database.add_calendar_event("Review notes", "2026-07-20", "Study session"))
        events = self.database.get_all_calendar_events()
        self.assertGreaterEqual(len(events), 1)
        self.assertEqual(events[0][1], "Review notes")

    def test_settings_table_supports_payload_column(self):
        conn = sqlite3.connect(self.temp_db.name)
        cursor = conn.cursor()
        cursor.execute("PRAGMA table_info(settings)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        self.assertIn("settings_json", columns)

    def test_task_query_helpers_use_sql_filters(self):
        self.assertTrue(self.database.add_task("Math", "Task alpha", "desc", "High", "2026-07-10", "Pending"))
        self.assertTrue(self.database.add_task("Math", "Task beta", "desc", "Low", "2026-07-20", "Completed"))
        self.assertTrue(self.database.add_task("Science", "Task gamma", "desc", "Medium", "2026-07-25", "Pending"))

        pending_math_tasks = self.database.get_tasks_by_subject_and_status("Math", "Pending")
        self.assertEqual(len(pending_math_tasks), 1)
        self.assertEqual(pending_math_tasks[0][2], "Task alpha")

        same_day_tasks = self.database.get_tasks_for_date("2026-07-20")
        self.assertEqual(len(same_day_tasks), 1)

        overdue_tasks = self.database.get_overdue_tasks("2026-07-20")
        self.assertEqual(len(overdue_tasks), 1)

        counts = self.database.get_task_counts_by_status()
        self.assertGreaterEqual(counts["Pending"], 1)
        self.assertGreaterEqual(counts["Completed"], 1)


if __name__ == "__main__":
    unittest.main()
