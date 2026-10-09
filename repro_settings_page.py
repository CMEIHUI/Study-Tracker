import os
import sys
import customtkinter as ctk

sys.path.insert(0, os.getcwd())

from dashboard import DashboardWindow
from auth import UserSession
from setting import SettingsManager

root = ctk.CTk()
root.withdraw()

try:
    sm = SettingsManager()
    UserSession.login((1, 'demo', 'demo@example.com'))
    win = DashboardWindow(root, UserSession.get_user(), settings_manager=sm)
    print('dashboard created')
    win.show_page('settings')
    print('show_page ok')
except Exception as exc:
    import traceback
    traceback.print_exc()
finally:
    try:
        win.destroy()
    except Exception:
        pass
    try:
        root.destroy()
    except Exception:
        pass
