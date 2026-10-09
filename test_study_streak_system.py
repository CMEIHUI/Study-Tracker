import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from database import DatabaseManager


class StudyStreakSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "studytracker.db"
        self.database = DatabaseManager(str(self.db_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_streak_summary_tracks_current_and_longest_streak(self):
        today = date.today()
        yesterday = today - timedelta(days=1)

        self.database.add_study_session("Math", 45, yesterday.isoformat())
        self.database.add_study_session("Math", 45, today.isoformat())

        summary = self.database.get_study_streak_summary()

        self.assertEqual(summary["current_streak"], 2)
        self.assertEqual(summary["longest_streak"], 2)

    def test_streak_resets_after_one_day_miss(self):
        today = date.today()
        two_days_ago = today - timedelta(days=2)

        self.database.add_study_session("Math", 45, two_days_ago.isoformat())
        self.database.add_study_session("Math", 45, today.isoformat())

        summary = self.database.get_study_streak_summary()

        self.assertEqual(summary["current_streak"], 1)
        self.assertEqual(summary["longest_streak"], 1)

    def test_streak_calendar_marks_active_days_for_month(self):
        today = date.today()
        active_date = today - timedelta(days=0)
        inactive_date = today - timedelta(days=1)

        self.database.add_study_session("Math", 45, active_date.isoformat())
        self.database.add_study_session("Math", 15, inactive_date.isoformat())

        calendar = self.database.get_study_streak_calendar(today.year, today.month)

        self.assertIn(active_date.day, calendar["active_days"])
        self.assertNotIn(inactive_date.day, calendar["active_days"])


if __name__ == "__main__":
    unittest.main()
