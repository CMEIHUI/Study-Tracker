import os
import tempfile
import unittest
from datetime import date

import customtkinter as ctk

from timer import TimerWindow
from database import DatabaseManager


class DummyParent(ctk.CTk):
    pass


class TimerWindowTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.database = DatabaseManager(db_name=self.db_path)
        self.parent = DummyParent()
        self.window = TimerWindow(self.parent, database=self.database)

    def tearDown(self):
        try:
            self.window.destroy()
        except Exception:
            pass
        try:
            self.parent.destroy()
        except Exception:
            pass
        try:
            os.remove(self.db_path)
        except OSError:
            pass

    def test_parse_countdown_duration_defaults(self):
        self.window.countdown_hours_var.set('0')
        self.window.countdown_minutes_var.set('25')
        self.window.countdown_seconds_var.set('0')
        total = self.window.parse_countdown_duration()
        self.assertEqual(total, 1500)

    def test_set_preset_focus_sets_timer_mode_and_duration(self):
        self.window.set_preset(25, 'focus')
        self.assertEqual(self.window.timer_mode, 'COUNTDOWN')
        self.assertEqual(self.window.current_pomodoro_type, 'focus')
        self.assertEqual(self.window.countdown_minutes_var.get(), '25')
        self.assertEqual(self.window.countdown_seconds_var.get(), '0')

    def test_handle_timer_complete_saves_pomodoro_and_chains(self):
        self.window.set_preset(1, 'focus')
        self.window.timer_mode = 'COUNTDOWN'
        self.window.remaining_seconds = 1
        self.window.total_seconds = 1
        self.window.timer_running = True
        self.window.session_elapsed_seconds = 60
        self.window.current_pomodoro_type = 'focus'
        self.window.pomodoro_enabled = True

        # handle completion should save and schedule a short break
        self.window.handle_timer_complete()

        recent = self.database.get_recent_pomodoro_sessions(limit=5)
        self.assertGreaterEqual(len(recent), 1)
        self.assertEqual(recent[0][1], 'focus')
        self.assertEqual(self.window.current_pomodoro_type, 'short_break')
        self.assertEqual(self.window.timer_mode, 'COUNTDOWN')

    def test_handle_timer_complete_break_resets_to_focus(self):
        self.window.set_preset(5, 'short_break')
        self.window.timer_mode = 'COUNTDOWN'
        self.window.remaining_seconds = 1
        self.window.total_seconds = 1
        self.window.timer_running = True
        self.window.session_elapsed_seconds = 60
        self.window.current_pomodoro_type = 'short_break'
        self.window.pomodoro_enabled = True

        self.window.handle_timer_complete()

        self.assertEqual(self.window.current_pomodoro_type, 'focus')
        self.assertEqual(self.window.mode_label.cget('text'), 'COUNTDOWN')


if __name__ == '__main__':
    unittest.main()
