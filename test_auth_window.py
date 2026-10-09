import tkinter as tk
import pytest

from auth import LoginWindow, RegisterWindow


def _create_tk_root_or_skip():
    try:
        root = tk.Tk()
        root.withdraw()
        return root
    except tk.TclError:
        pytest.skip("Tkinter/Tcl not available in this environment")


def test_login_window_replaces_content_inside_single_auth_window():
    root = _create_tk_root_or_skip()
    try:
        app = LoginWindow(settings_manager=None)
        app.update_idletasks()

        assert app.current_view == "login"
        assert len(app.auth_frame.winfo_children()) >= 1

        app.show_register()
        app.update_idletasks()

        assert app.current_view == "register"
        assert len(app.auth_frame.winfo_children()) == 1
        assert isinstance(app.auth_frame.winfo_children()[0], RegisterWindow)

        app.show_login()
        app.update_idletasks()

        assert app.current_view == "login"
        assert len(app.auth_frame.winfo_children()) >= 1
    finally:
        if hasattr(app, "destroy"):
            app.destroy()
        root.destroy()
