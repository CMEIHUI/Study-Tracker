import json

from setting import SettingsManager


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


def test_settings_manager_persists_appearance_mode_across_instances():
    database = DummyDatabase()
    first_manager = SettingsManager(database=database)
    first_manager.update_setting("appearance_mode", "Dark")
    first_manager.save_settings()

    second_manager = SettingsManager(database=database)
    assert second_manager.get_setting("appearance_mode") == "Dark"

    payload = json.loads(database.saved[3])
    assert payload["appearance_mode"] == "Dark"


def test_settings_manager_persists_custom_background_settings():
    database = DummyDatabase()
    manager = SettingsManager(database=database)
    manager.update_setting("appearance_mode", "Custom")
    manager.update_setting("background_image_path", r"C:\\images\\background.png")
    manager.save_settings()

    reloaded_manager = SettingsManager(database=database)
    assert reloaded_manager.get_setting("appearance_mode") == "Custom"
    assert reloaded_manager.get_setting("background_image_path") == r"C:\\images\\background.png"

    payload = json.loads(database.saved[3])
    assert payload["appearance_mode"] == "Custom"
    assert payload["background_image_path"] == r"C:\\images\\background.png"


def test_settings_manager_persists_daily_goal_hours():
    database = DummyDatabase()
    manager = SettingsManager(database=database)
    manager.update_setting("daily_goal_hours", 4)
    manager.save_settings()

    reloaded_manager = SettingsManager(database=database)
    assert reloaded_manager.get_setting("daily_goal_hours") == 4

    payload = json.loads(database.saved[3])
    assert payload["daily_goal_hours"] == 4
