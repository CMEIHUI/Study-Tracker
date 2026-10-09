"""
settings.py

Study Tracker Pro

Application Settings Module.

Features:
- Appearance mode
- UI scaling
- Save settings
- Reset settings
- User preferences
"""

import json
import os

import customtkinter as ctk

from tkinter import messagebox
from PIL import Image, ImageOps, ImageTk

from database import DatabaseManager
from appearance_manager import AppearanceManager, normalize_appearance_mode, load_background_image


DEFAULT_SETTINGS = {
    "appearance_mode": "System",
    "theme": "blue",
    "background_image_path": "",
    "ui_scaling": "100%",
    "notifications": True,
    "notification_interval": "15",
    "timer_duration": 25,
    "short_break_duration": 5,
    "long_break_duration": 15,
    "daily_goal_hours": 2,
    "auto_start_timer": False,
    "show_completed_tasks": True,
    "confirm_before_reset": True,
}

VALID_APPEARANCE_MODES = {"System", "Light", "Dark", "Custom"}


# ==========================================================
# SETTINGS CLASS
# ==========================================================

class SettingsManager:
    """Manage persisted application settings."""

    def __init__(self, database=None):
        self.database = database or DatabaseManager()
        self.settings = DEFAULT_SETTINGS.copy()
        self.appearance_manager = AppearanceManager.get_instance()
        self.load_settings()

    def _normalize_settings_payload(self):
        payload = self.settings.copy()
        payload["appearance_mode"] = normalize_appearance_mode(payload.get("appearance_mode", "System"))
        payload["theme"] = str(payload.get("theme") or "blue")
        payload["background_image_path"] = str(payload.get("background_image_path") or "")
        payload["ui_scaling"] = str(payload.get("ui_scaling") or "100%")
        payload["notifications"] = bool(payload.get("notifications", True))
        payload["timer_duration"] = int(payload.get("timer_duration", 25))
        payload["short_break_duration"] = int(payload.get("short_break_duration", 5))
        payload["long_break_duration"] = int(payload.get("long_break_duration", 15))
        payload["daily_goal_hours"] = int(payload.get("daily_goal_hours", 2))
        payload["auto_start_timer"] = bool(payload.get("auto_start_timer", False))
        payload["show_completed_tasks"] = bool(payload.get("show_completed_tasks", True))
        payload["confirm_before_reset"] = bool(payload.get("confirm_before_reset", True))
        return payload

    def load_settings(self):
        row = self.database.get_settings() if hasattr(self.database, "get_settings") else None
        if row is None:
            self.settings = DEFAULT_SETTINGS.copy()
            self.settings["appearance_mode"] = normalize_appearance_mode(self.settings.get("appearance_mode"))
            return

        payload = {}
        raw_payload = None
        if isinstance(row, (list, tuple)):
            if len(row) >= 5:
                raw_payload = row[4]
            elif len(row) >= 2:
                raw_payload = row[1]

        if raw_payload:
            try:
                payload = json.loads(raw_payload) if isinstance(raw_payload, str) else raw_payload
            except (TypeError, ValueError):
                payload = {}

        self.settings.update(DEFAULT_SETTINGS)
        if isinstance(payload, dict):
            self.settings.update(payload)

        if isinstance(payload, dict) and "appearance_mode" in payload:
            self.settings["appearance_mode"] = normalize_appearance_mode(payload.get("appearance_mode"))
        else:
            self.settings["appearance_mode"] = normalize_appearance_mode(self.settings.get("appearance_mode"))

        if isinstance(payload, dict) and "background_image_path" in payload:
            self.settings["background_image_path"] = str(payload.get("background_image_path") or "")
        else:
            self.settings["background_image_path"] = str(self.settings.get("background_image_path") or "")

        if "notifications" not in payload and len(row) >= 3:
            self.settings["notifications"] = bool(row[2])
        if "timer_duration" not in payload and len(row) >= 4 and row[3] is not None:
            self.settings["timer_duration"] = int(row[3])

        self.settings["appearance_mode"] = normalize_appearance_mode(self.settings.get("appearance_mode"))

    def get_setting(self, setting_name):
        return self.settings.get(setting_name)

    def update_setting(self, setting_name, value):
        if setting_name == "appearance_mode":
            value = normalize_appearance_mode(value)
        self.settings[setting_name] = value

    def get_all_settings(self):
        return self.settings.copy()

    def save_settings(self):
        payload = self._normalize_settings_payload()
        self.settings.update(payload)
        payload_json = json.dumps(payload)
        if hasattr(self.database, "save_settings"):
            try:
                self.database.save_settings(
                    str(payload.get("theme") or "blue"),
                    int(payload["notifications"]),
                    int(payload["timer_duration"]),
                    payload_json,
                )
            except TypeError:
                self.database.save_settings(
                    str(payload.get("theme") or "blue"),
                    int(payload["notifications"]),
                    int(payload["timer_duration"]),
                )
        return payload_json

    def apply_settings(self, target=None):
        appearance_mode = normalize_appearance_mode(self.settings.get("appearance_mode", "System"))
        theme = self.settings.get("theme", "blue")
        scaling = self.settings.get("ui_scaling", "100%")
        self.settings["appearance_mode"] = appearance_mode
        self.settings["background_image_path"] = str(self.settings.get("background_image_path") or "")
        if appearance_mode != "Custom":
            self.appearance_manager.appearance_mode = appearance_mode
            self.appearance_manager.background_image_path = ""
            self.appearance_manager.background_image_object = None
        else:
            self.appearance_manager.appearance_mode = "Custom"
            self.appearance_manager.background_image_path = self.settings["background_image_path"]
        self.appearance_manager.apply_current_state(target=target, settings=self.settings)
        ctk.set_default_color_theme(theme)
        try:
            scaling_value = float(str(scaling).replace("%", "")) / 100
        except ValueError:
            scaling_value = 1.0
        ctk.set_widget_scaling(scaling_value)

        if target is not None and hasattr(target, "apply_appearance_settings"):
            target.apply_appearance_settings(self.get_all_settings())
        if target is not None and hasattr(target, "apply_application_settings"):
            target.apply_application_settings(self.get_all_settings())

    def reset_settings(self):
        self.settings = DEFAULT_SETTINGS.copy()
        self.settings["appearance_mode"] = "System"
        self.save_settings()
        self.apply_settings()
        return self.settings["appearance_mode"]


# ==========================================================
# SETTINGS WINDOW
# ==========================================================

class SettingsWindow(ctk.CTkFrame):
    """
    Settings page.
    """

    def __init__(

        self,

        parent,
        database=None,
        settings_manager=None,

    ):

        super().__init__(parent)

        self.parent = parent
        self.database = database or DatabaseManager()
        self.settings_manager = settings_manager or SettingsManager(self.database)

        self.create_layout()
        self.load_current_settings()
        self.settings_manager.apply_settings(target=self.winfo_toplevel())


    # ======================================================
    # CREATE LAYOUT
    # ======================================================

    def create_layout(self):

        self.grid_columnconfigure(

            0,

            weight=1

        )


        self.grid_rowconfigure(

            1,

            weight=1

        )


        self.create_header()


        self.create_settings_area()


        self.create_buttons()


    # ======================================================
    # HEADER
    # ======================================================

    def create_header(self):

        self.header_frame = ctk.CTkFrame(

            self,

            fg_color="transparent"

        )


        self.header_frame.grid(

            row=0,

            column=0,

            sticky="ew",

            padx=25,

            pady=(25, 10)

        )


        self.header_frame.grid_columnconfigure(

            0,

            weight=1

        )


        ctk.CTkLabel(

            self.header_frame,

            text="Settings",

            font=(

                "Arial",

                28,

                "bold"

            )

        ).grid(

            row=0,

            column=0,

            sticky="w"

        )


        ctk.CTkLabel(

            self.header_frame,

            text=(

                "Customize your Study Tracker Pro experience."

            ),

            font=(

                "Arial",

                14

            )

        ).grid(

            row=1,

            column=0,

            sticky="w",

            pady=5

        )


    # ======================================================
    # SETTINGS AREA
    # ======================================================

    def create_settings_area(self):

        self.settings_frame = ctk.CTkScrollableFrame(

            self

        )


        self.settings_frame.grid(

            row=1,

            column=0,

            sticky="nsew",

            padx=25,

            pady=15

        )


        self.settings_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.create_appearance_section()
        self.create_preferences_section()
        self.create_timer_section()
        self.create_notification_section()
        self.create_reset_section()
        self.create_about_section()


    # ======================================================
    # APPEARANCE SECTION
    # ======================================================

    def create_appearance_section(self):

        self.appearance_frame = ctk.CTkFrame(

            self.settings_frame

        )


        self.appearance_frame.pack(

            fill="x",

            padx=10,

            pady=10

        )


        ctk.CTkLabel(

            self.appearance_frame,

            text="Appearance",

            font=(

                "Arial",

                20,

                "bold"

            )

        ).pack(

            anchor="w",

            padx=20,

            pady=(20, 5)

        )


        ctk.CTkLabel(

            self.appearance_frame,

            text=(

                "Choose the appearance mode of the application."

            )

        ).pack(

            anchor="w",

            padx=20,

            pady=5

        )


        self.appearance_combobox = ctk.CTkComboBox(

            self.appearance_frame,

            width=250,

            values=[

                "System",

                "Light",

                "Dark",
                "Custom"

            ],

            command=self.change_appearance

        )

        self.appearance_combobox.pack(anchor="w", padx=20, pady=(5, 10))

        ctk.CTkLabel(
            self.appearance_frame,
            text="Color Theme",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.theme_combobox = ctk.CTkComboBox(
            self.appearance_frame,
            width=250,
            values=["blue", "green", "dark-blue", "sweetkind"],
            command=self.change_theme,
        )
        self.theme_combobox.pack(anchor="w", padx=20, pady=(5, 10))

        ctk.CTkLabel(
            self.appearance_frame,
            text="Background Image",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.background_button = ctk.CTkButton(
            self.appearance_frame,
            text="Upload Image",
            width=250,
            command=self.select_background_image,
        )
        self.background_button.pack(anchor="w", padx=20, pady=(5, 5))

        self.background_status_label = ctk.CTkLabel(
            self.appearance_frame,
            text="No custom background selected",
            wraplength=250,
            justify="left",
        )
        self.background_status_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.background_preview_label = ctk.CTkLabel(
            self.appearance_frame,
            text="No preview available",
            width=250,
            height=150,
            fg_color="#1f1f1f",
            corner_radius=8,
            anchor="center",
            justify="center",
            wraplength=230,
        )
        self.background_preview_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.remove_background_button = ctk.CTkButton(
            self.appearance_frame,
            text="Remove Custom Background",
            width=250,
            command=self.remove_background,
        )
        self.remove_background_button.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(
            self.appearance_frame,
            text="UI Scaling",
            font=("Arial", 14, "bold"),
        ).pack(anchor="w", padx=20, pady=(0, 5))

        self.scaling_combobox = ctk.CTkComboBox(
            self.appearance_frame,
            width=250,
            values=["80%", "90%", "100%", "110%", "120%"],
            command=self.change_scaling,
        )
        self.scaling_combobox.pack(anchor="w", padx=20, pady=(5, 10))

        

    # ======================================================
    # PREFERENCES SECTION
    # ======================================================

    def create_preferences_section(self):

        self.preferences_frame = ctk.CTkFrame(self.settings_frame)
        self.preferences_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            self.preferences_frame,
            text="User Preferences",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.show_completed_switch = ctk.CTkSwitch(
            self.preferences_frame,
            text="Show completed tasks by default",
        )
        self.show_completed_switch.pack(anchor="w", padx=20, pady=(5, 5))

        self.auto_start_switch = ctk.CTkSwitch(
            self.preferences_frame,
            text="Auto-start timer after a reset",
        )
        self.auto_start_switch.pack(anchor="w", padx=20, pady=(5, 5))

        self.confirm_reset_switch = ctk.CTkSwitch(
            self.preferences_frame,
            text="Ask before resetting application data",
        )
        self.confirm_reset_switch.pack(anchor="w", padx=20, pady=(5, 20))

    # ======================================================
    # TIMER SECTION
    # ======================================================

    def create_timer_section(self):

        self.timer_frame = ctk.CTkFrame(self.settings_frame)
        self.timer_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            self.timer_frame,
            text="Timer Settings",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        ctk.CTkLabel(self.timer_frame, text="Pomodoro duration (min)").pack(anchor="w", padx=20, pady=(5, 2))
        self.pomodoro_var = ctk.StringVar(value="25")
        self.pomodoro_menu = ctk.CTkOptionMenu(
            self.timer_frame,
            values=["15", "20", "25", "30", "45", "60"],
            variable=self.pomodoro_var,
        )
        self.pomodoro_menu.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.timer_frame, text="Short break (min)").pack(anchor="w", padx=20, pady=(5, 2))
        self.short_break_var = ctk.StringVar(value="5")
        self.short_break_menu = ctk.CTkOptionMenu(
            self.timer_frame,
            values=["3", "5", "10", "15"],
            variable=self.short_break_var,
        )
        self.short_break_menu.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.timer_frame, text="Long break (min)").pack(anchor="w", padx=20, pady=(5, 2))
        self.long_break_var = ctk.StringVar(value="15")
        self.long_break_menu = ctk.CTkOptionMenu(
            self.timer_frame,
            values=["10", "15", "20", "30"],
            variable=self.long_break_var,
        )
        self.long_break_menu.pack(anchor="w", padx=20, pady=(0, 10))

        ctk.CTkLabel(self.timer_frame, text="Daily study goal (hours)").pack(anchor="w", padx=20, pady=(5, 2))
        self.daily_goal_var = ctk.StringVar(value="2")
        self.daily_goal_entry = ctk.CTkEntry(
            self.timer_frame,
            width=120,
            textvariable=self.daily_goal_var,
        )
        self.daily_goal_entry.pack(anchor="w", padx=20, pady=(0, 20))

    # ======================================================
    # NOTIFICATION SECTION
    # ======================================================

    def create_notification_section(self):

        self.notification_frame = ctk.CTkFrame(self.settings_frame)
        self.notification_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            self.notification_frame,
            text="Notifications",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        self.notification_switch = ctk.CTkSwitch(
            self.notification_frame,
            text="Enable study notifications",
        )
        self.notification_switch.pack(anchor="w", padx=20, pady=(5, 5))

        ctk.CTkLabel(self.notification_frame, text="Reminder interval (min)").pack(anchor="w", padx=20, pady=(5, 2))
        self.notification_interval_var = ctk.StringVar(value="15")
        self.notification_interval_menu = ctk.CTkOptionMenu(
            self.notification_frame,
            values=["5", "10", "15", "30"],
            variable=self.notification_interval_var,
        )
        self.notification_interval_menu.pack(anchor="w", padx=20, pady=(0, 20))

    # ======================================================
    # RESET SECTION
    # ======================================================

    def create_reset_section(self):
        self.reset_frame = ctk.CTkFrame(self.settings_frame)
        self.reset_frame.pack(fill="x", padx=10, pady=10)

        ctk.CTkLabel(
            self.reset_frame,
            text="Data Management",
            font=("Arial", 20, "bold"),
        ).pack(anchor="w", padx=20, pady=(20, 5))

        ctk.CTkButton(
            self.reset_frame,
            text="Reset Application Data",
            fg_color="#d9534f",
            hover_color="#c9302c",
            command=self.reset_application_data,
        ).pack(anchor="w", padx=20, pady=(5, 20))


    # ======================================================
    # ABOUT SECTION
    # ======================================================

    def create_about_section(self):

        self.about_frame = ctk.CTkFrame(

            self.settings_frame

        )


        self.about_frame.pack(

            fill="x",

            padx=10,

            pady=10

        )


        ctk.CTkLabel(

            self.about_frame,

            text="About Study Tracker Pro",

            font=(

                "Arial",

                20,

                "bold"

            )

        ).pack(

            anchor="w",

            padx=20,

            pady=(20, 5)

        )


        ctk.CTkLabel(

            self.about_frame,

            text=(

                "Study Tracker Pro is a Python-based "

                "study management application.\n\n"

                "Version: 1.0.0\n"

                "Developed using Python and CustomTkinter."

            ),

            justify="left"

        ).pack(

            anchor="w",

            padx=20,

            pady=(5, 20)

        )


    # ======================================================
    # BUTTONS
    # ======================================================

    def create_buttons(self):

        self.button_frame = ctk.CTkFrame(

            self,

            fg_color="transparent"

        )


        self.button_frame.grid(

            row=2,

            column=0,

            sticky="ew",

            padx=25,

            pady=(5, 25)

        )


        ctk.CTkButton(

            self.button_frame,

            text="Save Settings",

            width=150,

            height=40,

            command=self.save_settings

        ).pack(

            side="left",

            padx=5

        )


        ctk.CTkButton(

            self.button_frame,

            text="Reset Settings",

            width=150,

            height=40,

            command=self.reset_settings

        ).pack(

            side="left",

            padx=5

        )


    # ======================================================
    # LOAD CURRENT SETTINGS
    # ======================================================

    def load_current_settings(self):
        appearance_mode = self.settings_manager.get_setting("appearance_mode") or "System"
        theme = self.settings_manager.get_setting("theme") or "blue"
        background_image_path = self.settings_manager.get_setting("background_image_path") or ""
        ui_scaling = self.settings_manager.get_setting("ui_scaling") or "100%"
        notifications = bool(self.settings_manager.get_setting("notifications"))
        pomodoro = str(self.settings_manager.get_setting("timer_duration") or "25")
        short_break = str(self.settings_manager.get_setting("short_break_duration") or "5")
        long_break = str(self.settings_manager.get_setting("long_break_duration") or "15")
        interval = str(self.settings_manager.get_setting("notification_interval") or "15")
        auto_start = bool(self.settings_manager.get_setting("auto_start_timer"))
        show_completed = bool(self.settings_manager.get_setting("show_completed_tasks"))
        confirm_reset = bool(self.settings_manager.get_setting("confirm_before_reset"))

        self.appearance_combobox.set(appearance_mode)
        self.theme_combobox.set(theme)
        if background_image_path:
            self.background_status_label.configure(text=background_image_path)
        else:
            self.background_status_label.configure(text="No custom background selected")
        self.update_background_preview(background_image_path)
        self.scaling_combobox.set(ui_scaling)
        self.pomodoro_var.set(pomodoro)
        self.short_break_var.set(short_break)
        self.long_break_var.set(long_break)
        self.daily_goal_var.set(str(self.settings_manager.get_setting("daily_goal_hours") or 2))
        self.notification_interval_var.set(interval)
        self.notification_switch.select() if notifications else self.notification_switch.deselect()
        self.auto_start_switch.select() if auto_start else self.auto_start_switch.deselect()
        self.show_completed_switch.select() if show_completed else self.show_completed_switch.deselect()
        self.confirm_reset_switch.select() if confirm_reset else self.confirm_reset_switch.deselect()


    # ======================================================
    # CHANGE APPEARANCE
    # ======================================================

    def change_appearance(self, value):
        normalized_value = normalize_appearance_mode(value)
        self.settings_manager.update_setting("appearance_mode", normalized_value)
        if normalized_value != "Custom":
            self.settings_manager.update_setting("background_image_path", "")
            self.background_status_label.configure(text="No custom background selected")
        self.settings_manager.save_settings()
        self.settings_manager.apply_settings(target=self.winfo_toplevel())

    def select_background_image(self):
        appearance_manager = AppearanceManager.get_instance()
        state = appearance_manager.select_background_image(
            parent=self.winfo_toplevel(),
            target=self.winfo_toplevel(),
            settings_manager=self.settings_manager,
        )
        if state is None:
            return
        self.appearance_combobox.set("Custom")
        background_image_path = state.get("background_image_path") or ""
        self.background_status_label.configure(
            text=background_image_path if background_image_path else "No custom background selected"
        )
        self.update_background_preview(background_image_path)

    def remove_background(self):
        appearance_manager = AppearanceManager.get_instance()
        appearance_manager.remove_custom_background(
            target=self.winfo_toplevel(),
            settings_manager=self.settings_manager,
        )
        self.appearance_combobox.set("Light")
        self.background_status_label.configure(text="No custom background selected")
        self.update_background_preview(None)

    def change_theme(self, value):
        ctk.set_default_color_theme(value)
        self.settings_manager.update_setting("theme", value)
        self.settings_manager.save_settings()

    def update_background_preview(self, image_path):
        if image_path:
            image_preview = load_background_image(image_path, size=(250, 150))
            if image_preview is not None:
                self.background_preview_label.configure(image=image_preview, text="")
                self.background_preview_label.image = image_preview
                return

        self.background_preview_label.configure(image=None, text="No preview available")
        self.background_preview_label.image = None


    # ======================================================
    # CHANGE SCALING
    # ======================================================

    def change_scaling(self, value):
        scaling_value = int(value.replace("%", ""))
        scaling_factor = scaling_value / 100
        ctk.set_widget_scaling(scaling_factor)
        self.settings_manager.update_setting("ui_scaling", value)
        self.settings_manager.save_settings()



    # ======================================================
    # SAVE SETTINGS
    # ======================================================

    def save_settings(self):
        try:
            appearance_mode = normalize_appearance_mode(self.appearance_combobox.get())
            theme = self.theme_combobox.get()
            ui_scaling = self.scaling_combobox.get()
            notifications = bool(self.notification_switch.get())
            timer_duration = int(self.pomodoro_var.get())
            short_break_duration = int(self.short_break_var.get())
            long_break_duration = int(self.long_break_var.get())
            daily_goal_hours = int(self.daily_goal_var.get())
            notification_interval = self.notification_interval_var.get()
            auto_start_timer = bool(self.auto_start_switch.get())
            show_completed_tasks = bool(self.show_completed_switch.get())
            confirm_before_reset = bool(self.confirm_reset_switch.get())

            self.settings_manager.update_setting("appearance_mode", appearance_mode)
            if appearance_mode != "Custom":
                self.settings_manager.update_setting("background_image_path", "")
                self.background_status_label.configure(text="No custom background selected")
            self.settings_manager.update_setting("theme", theme)
            self.settings_manager.update_setting("ui_scaling", ui_scaling)
            self.settings_manager.update_setting("notifications", notifications)
            self.settings_manager.update_setting("timer_duration", timer_duration)
            self.settings_manager.update_setting("short_break_duration", short_break_duration)
            self.settings_manager.update_setting("long_break_duration", long_break_duration)
            self.settings_manager.update_setting("daily_goal_hours", daily_goal_hours)
            self.settings_manager.update_setting("notification_interval", notification_interval)
            self.settings_manager.update_setting("auto_start_timer", auto_start_timer)
            self.settings_manager.update_setting("show_completed_tasks", show_completed_tasks)
            self.settings_manager.update_setting("confirm_before_reset", confirm_before_reset)
            self.settings_manager.save_settings()
            self.settings_manager.apply_settings(target=self.winfo_toplevel())
            messagebox.showinfo("Settings Saved", "Your settings have been saved successfully.")
        except ValueError as error:
            messagebox.showwarning("Invalid Input", f"Please enter valid numeric values.\n{error}")
        except Exception as error:
            messagebox.showerror("Unexpected Error", f"Unable to save settings.\n{error}")


    # ======================================================
    # RESET SETTINGS
    # ======================================================

    def reset_settings(self):
        answer = messagebox.askyesno("Reset Settings", "Are you sure you want to reset all settings?")
        if not answer:
            return

        self.settings_manager.reset_settings()
        self.load_current_settings()
        self.settings_manager.apply_settings(target=self.winfo_toplevel())
        messagebox.showinfo("Settings Reset", "Settings have been reset successfully.")

    def reset_application_data(self):
        if self.settings_manager.get_setting("confirm_before_reset") is not False:
            answer = messagebox.askyesno("Reset Application Data", "This will clear your study data. Continue?")
            if not answer:
                return

        try:
            conn = self.database.connect()
            if conn is None:
                raise RuntimeError("The database could not be opened.")
            cursor = conn.cursor()
            cursor.execute("DELETE FROM tasks")
            cursor.execute("DELETE FROM subjects")
            cursor.execute("DELETE FROM study_sessions")
            cursor.execute("DELETE FROM notes")
            cursor.execute("DELETE FROM achievements")
            conn.commit()
            conn.close()
            messagebox.showinfo("Reset Complete", "Application data has been cleared.")
        except RuntimeError as error:
            messagebox.showerror("Reset Failed", str(error))
        except Exception as error:
            messagebox.showerror("Reset Failed", f"Unable to clear data.\n{error}")