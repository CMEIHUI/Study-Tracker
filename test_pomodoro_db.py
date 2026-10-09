import os
import tempfile
import unittest
from datetime import date, timedelta

from database import DatabaseManager


class PomodoroDBTests(unittest.TestCase):
    def setUp(self):
        tf = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        tf.close()
        self.db_path = tf.name
        self.db = DatabaseManager(db_name=self.db_path)

    def tearDown(self):
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_add_and_count_pomodoro_for_date(self):
        today = date.today().isoformat()
        added = self.db.add_pomodoro_session("focus", 25, today)
        self.assertTrue(added)
        count = self.db.get_pomodoro_count_for_date(today, session_type="focus")
        self.assertEqual(count, 1)

    def test_get_recent_pomodoro_sessions_ordering(self):
        d = date.today()
        for i in range(5):
            self.db.add_pomodoro_session("focus", 25 + i, (d - timedelta(days=i)).isoformat())
        recent = self.db.get_recent_pomodoro_sessions(limit=3)
        self.assertEqual(len(recent), 3)
        # Most recent first: check dates descending
        dates = [r[3] for r in recent]
        self.assertGreaterEqual(dates[0], dates[1])
        self.assertGreaterEqual(dates[1], dates[2])

    def test_count_between_dates(self):
        base = date.today()
        # add sessions on base, base-1, base-2
        for i in range(3):
            self.db.add_pomodoro_session("focus", 25, (base - timedelta(days=i)).isoformat())
        start = (base - timedelta(days=2)).isoformat()
        end = base.isoformat()
        cnt = self.db.get_pomodoro_count_between_dates(start, end, session_type="focus")
        self.assertEqual(cnt, 3)


if __name__ == "__main__":
    unittest.main()
