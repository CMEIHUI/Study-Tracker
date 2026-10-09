import os
import tkinter as tk
from appearance_manager import AppearanceManager

root = tk.Tk()
root.geometry('800x600')
root.withdraw()

manager = AppearanceManager.get_instance()
manager.appearance_mode = 'Custom'
manager.background_image_path = r'C:\Users\User\Pictures\sample.jpg'
manager.background_image_object = None
manager._last_size = None
print('exists', os.path.exists(manager.background_image_path))
photo = manager._ensure_background_photo((800, 600))
print('photo object', photo)
print('state', manager.get_state())
root.destroy()
