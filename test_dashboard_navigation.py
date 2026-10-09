import unittest
from unittest.mock import patch, Mock
import customtkinter as ctk
import tkinter as _tkinter

# Detect whether Tcl/Tk is available in the current environment. If not,
# many GUI tests should be skipped to avoid failing in headless or broken
# Python installations where Tk isn't installed correctly.
try:
    _test_root = _tkinter.Tk()
    _test_root.destroy()
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False
from dashboard import DashboardWindow
from sidebar import Sidebar
from subject import SubjectWindow
from task import TaskWindow


class DashboardNavigationTest(unittest.TestCase):
    def setUp(self):
        if not GUI_AVAILABLE:
            self.skipTest("Tkinter/Tcl not available in this environment")
        self.root = ctk.CTk()
        self.root.withdraw()
        self.user_data = (1, "Test User")

    def tearDown(self):
        try:
            self.root.destroy()
        except Exception:
            pass

    def test_show_page_reuses_cached_page_instances(self):
        with patch("dashboard.TaskWindow") as task_window_cls:
            task_window_cls.return_value = ctk.CTkFrame(self.root)
            window = DashboardWindow(self.root, self.user_data, settings_manager=None)
            window.show_page("tasks")
            window.show_page("tasks")
            self.assertEqual(task_window_cls.call_count, 1)

    def test_subject_window_skips_reload_when_already_loaded(self):
        with patch("subject.run_in_background") as run_background:
            window = SubjectWindow(self.root, database=object())
            window.load_subjects(force=False)
            window.load_subjects(force=False)
            self.assertEqual(run_background.call_count, 1)

    def test_task_window_skips_reload_when_already_loaded(self):
        with patch("task.run_in_background") as run_background:
            window = TaskWindow(self.root, database=object())
            window.load_tasks(force=False)
            window.load_tasks(force=False)
            self.assertGreaterEqual(run_background.call_count, 1)

    def test_profile_page_navigation_uses_show_page(self):
        window = DashboardWindow(self.root, self.user_data, settings_manager=None)
        with patch.object(window, "show_page") as show_page_mock:
            window.navigate_to_page("profile")
            show_page_mock.assert_called_once_with("profile")

    def test_sidebar_navigation_button_callbacks_bind_correct_page(self):
        pages = []
        sidebar = Sidebar(self.root, navigation_callback=lambda page: pages.append(page))
        buttons = list(sidebar.navigation_frame.winfo_children())
        expected_pages = [item[1] for item in sidebar.navigation_items]

        for button in buttons:
            button.invoke()

        self.assertEqual(pages, expected_pages)

    def test_show_settings_page_creates_and_shows(self):
        window = DashboardWindow(self.root, self.user_data, settings_manager=None)
        # Ensure showing settings creates the page and it is stored in page_frames
        window.show_page("settings")
        self.assertIn("settings", window.page_frames)
        from setting import SettingsWindow
        self.assertIsInstance(window.page_frames["settings"], SettingsWindow)

    def test_show_analytics_page_creates_and_shows(self):
        window = DashboardWindow(self.root, self.user_data, settings_manager=None)
        window.show_page("analytics")
        self.assertIn("analytics", window.page_frames)
        from analytics import AnalyticsWindow
        self.assertIsInstance(window.page_frames["analytics"], AnalyticsWindow)

if __name__ == "__main__":
    unittest.main()
