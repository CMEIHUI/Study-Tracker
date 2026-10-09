import tkinter as tk
from profile import ProfileWindow
from database import DatabaseManager

root = tk.Tk()
root.withdraw()
try:
    ProfileWindow(root, DatabaseManager(), user_id=1)
    print('created')
except Exception:
    import traceback
    traceback.print_exc()
finally:
    root.destroy()
