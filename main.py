"""
Study Tracker
Main Entry Point

Author:  
CHAN MEI HUI
FONG YUE CHEE 
MONG WEN QI 
VENGADISWARA BILLIE THEERAN 
"""

import logging
import customtkinter as ctk

from auth import LoginWindow
from config import FONT_FAMILY
from python.database.databasemanager import DatabaseManager
from setting import SettingsManager


SETTINGS_MANAGER = None


def initialize():
    """Initialize application data and shared settings state."""
    logging.basicConfig(
        filename="studytracker.log",
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logging.getLogger("study_tracker").info("Starting Study Tracker Pro")

    global SETTINGS_MANAGER
    DatabaseManager()
    if SETTINGS_MANAGER is None:
        SETTINGS_MANAGER = SettingsManager()
    SETTINGS_MANAGER.load_settings()
    SETTINGS_MANAGER.apply_settings()
    return SETTINGS_MANAGER


def main():
    settings_manager = initialize()
    ctk.set_default_color_theme(settings_manager.get_setting("theme") or "blue")

    original_button_init = ctk.CTkButton.__init__

    def patched_ctkbutton_init(self, *args, **kwargs):
        if "corner_radius" not in kwargs:
            kwargs["corner_radius"] = 12
        if "height" not in kwargs:
            kwargs["height"] = 42
        if "font" not in kwargs:
            kwargs["font"] = (FONT_FAMILY, 14, "bold")
        if "fg_color" not in kwargs:
            kwargs["fg_color"] = "#2563EB"
        if "hover_color" not in kwargs:
            kwargs["hover_color"] = "#1D4ED8"
        if "text_color" not in kwargs:
            kwargs["text_color"] = "white"
        return original_button_init(self, *args, **kwargs)

    ctk.CTkButton.__init__ = patched_ctkbutton_init

    app = LoginWindow(settings_manager=settings_manager)
    app.mainloop()


if __name__ == "__main__":

    main()