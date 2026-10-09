import traceback
import tkinter as tk
import customtkinter as ctk

from task import TaskWindow

try:
    root = tk.Tk()
    root.withdraw()
    win = TaskWindow(root, database=None)
    print('TaskWindow created', type(win))
    win.destroy()
    root.destroy()
except Exception:
    traceback.print_exc()
