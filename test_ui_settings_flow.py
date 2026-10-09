import customtkinter as ctk
import pytest
import tkinter as _tkinter

from dashboard import DashboardWindow
from setting import SettingsWindow


try:
    _test_root = _tkinter.Tk()
    _test_root.destroy()
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False


def test_settings_flow_shows_settings_page():
    if not GUI_AVAILABLE:
        pytest.skip("Tkinter/Tcl not available in this environment")
    root = ctk.CTk()
    root.withdraw()
    try:
        user_data = (1, "UITestUser")
        win = DashboardWindow(root, user_data, settings_manager=None)

        sidebar = win.sidebar

        # Find the Settings button and invoke it
        settings_btn = None
        for b in sidebar.navigation_frame.winfo_children():
            try:
                if b.cget("text") == "Settings":
                    settings_btn = b
                    break
            except Exception:
                continue

        assert settings_btn is not None, "Settings button not found in sidebar"
        settings_btn.invoke()

        assert "settings" in win.page_frames, "Settings page was not created"
        assert isinstance(win.page_frames["settings"], SettingsWindow)
    finally:
        try:
            root.destroy()
        except Exception:
            pass
