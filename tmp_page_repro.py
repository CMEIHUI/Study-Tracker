import customtkinter as ctk
from dashboard import DashboardWindow

ctk.set_appearance_mode('Light')
ctk.set_default_color_theme('blue')
root = ctk.CTk()
root.withdraw()
try:
    window = DashboardWindow(root, (1, 'Test User'), settings_manager=None)
    print('dashboard created')
    window.show_page('tasks')
    print('tasks page shown')
    window.show_page('reports')
    print('reports page shown')
    root.update()
finally:
    root.destroy()
