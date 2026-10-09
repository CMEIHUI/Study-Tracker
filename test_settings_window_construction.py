import os
import sys

import customtkinter as ctk

sys.path.insert(0, os.getcwd())

from setting import SettingsManager, SettingsWindow


class DummyDatabase:
    def __init__(self):
        self.saved = None

    def get_settings(self):
        if self.saved is None:
            return None
        return (1, self.saved[0], self.saved[1], self.saved[2], self.saved[3])

    def save_settings(self, theme, notification, pomodoro_time, settings_json=None):
        self.saved = [theme, notification, pomodoro_time, settings_json]
        return True


def test_settings_window_constructs_with_parent_frame():
    root = ctk.CTk()
    root.withdraw()
    try:
        manager = SettingsManager(database=DummyDatabase())
        frame = ctk.CTkFrame(root)
        frame.pack()
        window = SettingsWindow(frame, database=DummyDatabase(), settings_manager=manager)
        assert window.winfo_exists()
    finally:
        try:
            root.destroy()
        except Exception:
            pass
