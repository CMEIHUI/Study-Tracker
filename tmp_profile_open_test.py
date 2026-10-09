import tkinter as tk
import customtkinter as ctk
from dashboard import DashboardWindow

root = ctk.CTk()
root.withdraw()
try:
    window = DashboardWindow(root, (1, 'testuser'), settings_manager=None)
    window.show_page('profile')
    print('page shown')
except Exception:
    import traceback
    traceback.print_exc()
finally:
    root.destroy()
