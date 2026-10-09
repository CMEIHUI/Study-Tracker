import os
import sys
import tkinter as tk

sys.path.insert(0, os.getcwd())
from setting import SettingsWindow, SettingsManager

root = tk.Tk()
root.withdraw()
try:
    sm = SettingsManager()
    print('manager ok', sm.get_all_settings())
    frame = SettingsWindow(root, settings_manager=sm)
    print('window ok')
except Exception as exc:
    import traceback
    traceback.print_exc()
finally:
    root.destroy()
