import tempfile
import unittest
from datetime import date, timedelta
from pathlib import Path

from database import DatabaseManager


class GamificationSystemTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "studytracker.db"
        self.database = DatabaseManager(str(self.db_path))

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_completed_task_awards_xp_and_coins(self):
        self.database.add_task("Math", "Finish algebra", "Review", "High", date.today().isoformat())
        task = self.database.get_all_tasks()[0]
        self.database.complete_task(task[0])

        state = self.database.get_gamification_state()

        self.assertGreaterEqual(state["total_xp"], 10)
        self.assertGreaterEqual(state["coins"], 10)
        self.assertGreaterEqual(state["level"], 1)

    def test_study_one_hour_awards_xp(self):
        self.database.add_study_session("Math", 60, date.today().isoformat())

        state = self.database.get_gamification_state()

        self.assertGreaterEqual(state["total_xp"], 20)
        self.assertGreaterEqual(state["coins"], 20)

    def test_badges_unlock_at_xp_thresholds(self):
        for index in range(10):
            self.database.add_task("Math", f"Complete task {index+1}", "Review", "High", date.today().isoformat())
            task = self.database.get_all_tasks()[index]
            self.database.complete_task(task[0])

        state = self.database.get_gamification_state()
        self.assertEqual(state["badge_label"], "Bronze Badge")
        self.assertTrue(any(badge["title"] == "🥉 Beginner Scholar" and badge["unlocked"] for badge in state["badges"]))

        self.database._store_gamification_profile(500, state["coins"], level=state["level"], current_level_xp=0)
        state = self.database.get_gamification_state()
        self.assertEqual(state["badge_label"], "Silver Badge")
        self.assertTrue(any(badge["title"] == "🥈 Consistent Learner" and badge["unlocked"] for badge in state["badges"]))

        self.database._store_gamification_profile(1000, state["coins"], level=state["level"], current_level_xp=0)
        state = self.database.get_gamification_state()
        self.assertEqual(state["badge_label"], "Gold Badge")
        self.assertTrue(any(badge["title"] == "🥇 Study Master" and badge["unlocked"] for badge in state["badges"]))

    def test_thirty_day_streak_champion_unlocks(self):
        start_date = date.today() - timedelta(days=29)
        for offset in range(30):
            session_date = (start_date + timedelta(days=offset)).isoformat()
            self.database.add_study_session("Math", 30, session_date)

        state = self.database.get_gamification_state()
        self.assertTrue(any(badge["title"] == "🏆 30-Day Streak Champion" and badge["unlocked"] for badge in state["badges"]))

    def test_daily_login_awards_xp_once_per_day(self):
        self.database.register_user("gamer", "gamer@example.com", "secret")
        user = self.database.login_user("gamer", "secret")
        self.assertIsNotNone(user)

        first_state = self.database.get_gamification_state()
        self.assertGreaterEqual(first_state["total_xp"], 5)

        second_login = self.database.login_user("gamer", "secret")
        self.assertIsNotNone(second_login)

        second_state = self.database.get_gamification_state()
        self.assertEqual(second_state["total_xp"], first_state["total_xp"])


if __name__ == "__main__":
    unittest.main()
