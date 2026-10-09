import unittest
from datetime import date, timedelta

from dashboard import DashboardWindow


class DummyDatabase:
    def __init__(self):
        self.goals = []
        self.notifications = []
        self.ai_history = []
        self.goal_updates = []

    def get_goals(self):
        return list(self.goals)

    def update_goal_progress(self, goal_id, current_minutes, completed=0):
        self.goal_updates.append((goal_id, current_minutes, completed))

    def get_notifications(self, unread_only=False):
        return list(self.notifications)

    def add_notification(self, title, message, is_read=0):
        self.notifications.append((1, title, message, is_read))
        return True

    def get_ai_history(self, limit=10):
        return list(self.ai_history)

    def add_ai_history(self, query_text, response_text):
        self.ai_history.append((1, query_text, response_text))
        return True


class DashboardProDefaultsTests(unittest.TestCase):
    def test_seed_default_notifications_and_ai_history_are_persisted(self):
        window = object.__new__(DashboardWindow)
        window.database = DummyDatabase()

        window._seed_default_notifications()
        window._seed_default_ai_history()

        self.assertTrue(window.database.notifications)
        self.assertTrue(window.database.ai_history)

    def test_sync_goal_progress_updates_live_minutes_from_sessions(self):
        window = object.__new__(DashboardWindow)
        window.database = DummyDatabase()
        today = date.today().isoformat()
        week_end = (date.today() + timedelta(days=6)).isoformat()

        window.database.goals = [
            (1, "daily", 120, 0, today, today, 0, "2026-08-01"),
            (2, "weekly", 420, 0, today, week_end, 0, "2026-08-01"),
        ]
        sessions = [(1, "Math", 45, today)]

        synced_goals = window._sync_goal_progress(window.database.goals, sessions, today)

        self.assertEqual(synced_goals[0][3], 45)
        self.assertEqual(window.database.goal_updates[0][1], 45)


if __name__ == "__main__":
    unittest.main()
