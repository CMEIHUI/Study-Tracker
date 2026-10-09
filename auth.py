"""
auth.py

Study Tracker Pro

This module handles:

1. User Registration
2. User Login
3. Password Validation
4. Logout
5. User Session Management
6. OOP GUI Classes
"""

import os
import re
import sys
import tkinter as tk
import customtkinter as ctk

# Ensure Tk can resolve its bundled Tcl/Tk libraries on Windows-based runs.
if os.name == "nt":
    tcl_root = os.path.join(sys.prefix, "tcl")
    tcl_dir = os.path.join(tcl_root, "tcl8.6")
    tk_dir = os.path.join(tcl_root, "tk8.6")
    init_tcl = os.path.join(tcl_dir, "init.tcl")
    if os.path.isfile(init_tcl):
        os.environ.setdefault("TCL_LIBRARY", tcl_dir)
    if os.path.isdir(tk_dir):
        os.environ.setdefault("TK_LIBRARY", tk_dir)

from tkinter import messagebox

from database import DatabaseManager
from design_system import DesignSystem
from appearance_manager import AppearanceManager
from setting import SettingsManager
from datetime import datetime


# ==========================================================
# USER SESSION
# ==========================================================

class UserSession:
    """
    Stores the currently logged-in user.

    This class demonstrates encapsulation
    and class-level session management.
    """

    current_user = None

    @classmethod
    def login(cls, user_data):

        cls.current_user = user_data


    @classmethod
    def logout(cls):

        cls.current_user = None


    @classmethod
    def is_logged_in(cls):

        return cls.current_user is not None


    @classmethod
    def get_user(cls):

        return cls.current_user


    @classmethod
    def get_user_id(cls):

        if cls.current_user:

            return cls.current_user[0]

        return None


    @classmethod
    def get_username(cls):

        if cls.current_user:

            return cls.current_user[1]

        return None


    @classmethod
    def get_email(cls):

        if cls.current_user:

            return cls.current_user[2]

        return None


# ==========================================================
# AUTHENTICATION VALIDATOR
# ==========================================================

class AuthenticationValidator:
    """
    Validates user registration and login information.
    """

    MIN_PASSWORD_LENGTH = 6


    @staticmethod
    def validate_username(username):

        if not username:

            return False, "Username is required."

        if len(username) < 3:

            return False, (
                "Username must contain at least 3 characters."
            )

        if " " in username:

            return False, (
                "Username cannot contain spaces."
            )

        return True, ""


    @staticmethod
    def validate_email(email):

        if not email:

            return False, "Email is required."

        email_pattern = (

            r"^[a-zA-Z0-9._%+-]+@"
            r"[a-zA-Z0-9.-]+\."
            r"[a-zA-Z]{2,}$"

        )

        if not re.match(
            email_pattern,
            email
        ):

            return False, (
                "Please enter a valid email address."
            )

        return True, ""


    @staticmethod
    def validate_password(password):

        if not password:

            return False, (
                "Password is required."
            )

        if len(password) < 6:

            return False, (
                "Password must contain at least 6 characters."
            )

        return True, ""


    @staticmethod
    def validate_registration(
        username,
        email,
        password,
        confirm_password
    ):

        valid, message = (

            AuthenticationValidator
            .validate_username(username)

        )

        if not valid:

            return False, message


        valid, message = (

            AuthenticationValidator
            .validate_email(email)

        )

        if not valid:

            return False, message


        valid, message = (

            AuthenticationValidator
            .validate_password(password)

        )

        if not valid:

            return False, message


        if password != confirm_password:

            return False, (
                "Passwords do not match."
            )


        return True, ""


# ==========================================================
# REGISTER WINDOW
# ==========================================================

class RegisterWindow(ctk.CTkFrame):
    """Registration form hosted inside the authentication window."""

    def __init__(
        self,
        parent,
        on_success=None
    ):

        super().__init__(parent, corner_radius=20, fg_color="transparent")

        self.parent = parent
        self.on_success = on_success

        self.database = DatabaseManager()
        self.design = DesignSystem()

        self.create_widgets()

    def create_widgets(self):

        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color="#0F172A"
        )

        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=20,
            pady=20
        )

        # Top-left quick back button for easy navigation to the login view
        self.top_back_button = self.design.create_button(
            self.main_frame,
            text="← Back",
            width=100,
            height=30,
            fg_color="transparent",
            hover_color="#334155",
            command=self._go_back
        )
        self.top_back_button.place(x=10, y=10)

        self.design.create_label(
            self.main_frame,
            text="Create Account",
            size="2xl",
            weight="bold",
            text_color="white"
        ).pack(pady=25)

        self.design.create_label(
            self.main_frame,
            text="Username",
            text_color="white"
        ).pack(anchor="w", padx=30)

        self.username_entry = self.design.create_entry(
            self.main_frame,
            placeholder="Enter username",
            width=420,
            height=40,
            fg_color="white",
            border_color="#3B82F6",
            border_width=2
        )
        self.username_entry.pack(pady=8, padx=30, fill="x")

        self.design.create_label(
            self.main_frame,
            text="Email",
            text_color="white"
        ).pack(anchor="w", padx=30)

        self.email_entry = self.design.create_entry(
            self.main_frame,
            placeholder="Enter email",
            width=420,
            height=40,
            fg_color="white",
            border_color="#3B82F6",
            border_width=2
        )
        self.email_entry.pack(pady=8, padx=30, fill="x")

        self.design.create_label(
            self.main_frame,
            text="Password",
            text_color="white"
        ).pack(anchor="w", padx=30)

        self.password_entry = self.design.create_entry(
            self.main_frame,
            placeholder="Enter password",
            show="*",
            width=420,
            height=40,
            fg_color="white",
            border_color="#3B82F6",
            border_width=2
        )
        self.password_entry.pack(pady=8, padx=30, fill="x")

        self.design.create_label(
            self.main_frame,
            text="Confirm Password",
            text_color="white"
        ).pack(anchor="w", padx=30)

        self.confirm_password_entry = self.design.create_entry(
            self.main_frame,
            placeholder="Confirm password",
            show="*",
            width=420,
            height=40,
            fg_color="white",
            border_color="#3B82F6",
            border_width=2
        )
        self.confirm_password_entry.pack(pady=8, padx=30, fill="x")

        self.register_button = self.design.create_button(
            self.main_frame,
            text="Register",
            width=420,
            height=45,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            corner_radius=12,
            command=self.register_user
        )
        # Ensure the register button is clearly visible with enough space
        self.register_button.pack(pady=28, padx=30, fill="x", expand=True)

        self.design.create_button(
            self.main_frame,
            text="Back to Login",
            width=420,
            height=60,
            fg_color="#475569",
            hover_color="#334155",
            command=self._go_back
        ).pack(pady=8, padx=30, fill="x", expand=True)

    def _go_back(self):
        if self.on_success:
            self.on_success()
        else:
            self.pack_forget()

    def register_user(self):
        username = self.username_entry.get().strip()
        email = self.email_entry.get().strip()
        password = self.password_entry.get()
        confirm_password = self.confirm_password_entry.get()

        valid, message = AuthenticationValidator.validate_registration(
            username,
            email,
            password,
            confirm_password,
        )

        if not valid:
            messagebox.showerror("Registration Error", message)
            return

        if self.database.user_exists(username):
            messagebox.showerror("Registration Error", "Username already exists.")
            return

        if self.database.email_exists(email):
            messagebox.showerror("Registration Error", "Email already exists.")
            return

        success = self.database.register_user(username, email, password)

        if success:
            messagebox.showinfo("Success", "Account created successfully.")
            if self.on_success:
                self.on_success()
            else:
                self.pack_forget()
        else:
            messagebox.showerror("Error", "Unable to create account.")


# ==========================================================
# LOGIN WINDOW
# ==========================================================

class LoginWindow(ctk.CTk):

    """
    Main authentication window that hosts login and registration forms.
    """

    def __init__(self, settings_manager=None):

        super().__init__()
        self.configure(fg_color="#0F172A")

        self.database = DatabaseManager()
        self.design = DesignSystem()
        self.settings_manager = settings_manager or SettingsManager(self.database)
        self.appearance_manager = AppearanceManager.get_instance()
        self.appearance_manager.load_settings(self.settings_manager.get_all_settings())
        self.settings_manager.apply_settings(target=self)

        self.title(
            "Study Tracker Pro - Login"
        )

        self.geometry(
            "900x860"
        )
        self.minsize(680, 720)
        self.resizable(
            True,
            True
        )

        self.current_view = "login"
        self._create_background_layer()
        self.create_widgets()

    def _create_background_layer(self):
        self.background_label = tk.Label(self, bg="#0F172A", bd=0, highlightthickness=0)
        self.background_label.place(x=0, y=0, relwidth=1, relheight=1)
        self.background_label.lower()
        self.bind("<Configure>", self.apply_appearance_settings, add="+")
        self.appearance_manager.register_observer(self._handle_appearance_update)

    def _handle_appearance_update(self, state, target=None):
        if not hasattr(self, "background_label"):
            return
        if state.get("appearance_mode") != "Custom" or not state.get("background_image_object"):
            self.background_label.configure(image="")
            self.background_label.image = None
            return
        photo = state.get("background_image_object")
        self.background_label.configure(image=photo, bg="#0F172A")
        self.background_label.image = photo
        try:
            self.background_label.update_idletasks()
        except Exception:
            pass

    def apply_appearance_settings(self, event=None):
        if not hasattr(self, "background_label"):
            return
        self.appearance_manager.apply_current_state(target=self, settings=self.settings_manager.get_all_settings())

    def create_widgets(self):
        self.main_frame = ctk.CTkFrame(
            self,
            corner_radius=20,
            fg_color="#0F172A"
        )

        self.main_frame.pack(
            fill="both",
            expand=True,
            padx=50,
            pady=50
        )

        self.design.create_label(
            self.main_frame,
            text="Study Tracker Pro",
            size="3xl",
            weight="bold",
            text_color="white"
        ).pack(pady=(40, 10))

        self.design.create_label(
            self.main_frame,
            text="Organize your learning. Track your progress.",
            size="lg",
            text_color="white"
        ).pack(pady=(0, 35))

        self.auth_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )
        self.auth_frame.pack(fill="both", expand=True, padx=20, pady=(0, 30))

        self.show_login()
        self.bind("<Return>", self.handle_enter_key)

    def handle_enter_key(self, event):
        if self.current_view == "register":
            self.register_user()
            return "break"
        self.login()
        return "break"

    def clear_auth_frame(self):
        for widget in self.auth_frame.winfo_children():
            widget.destroy()

    def show_login(self):
        self.current_view = "login"
        self.clear_auth_frame()
        self.title("Study Tracker Pro - Login")

        self.design.create_label(
            self.auth_frame,
            text="Username",
            text_color="white"
        ).pack(anchor="w", padx=50)

        self.username_entry = self.design.create_entry(
            self.auth_frame,
            placeholder="Enter username",
            width=420,
            height=40,
            fg_color="white",
            border_color="#3B82F6",
            border_width=2
        )
        self.username_entry.pack(pady=(5, 20), padx=30, fill="x")

        self.design.create_label(
            self.auth_frame,
            text="Password",
            text_color="white"
        ).pack(anchor="w", padx=50)

        self.password_entry = self.design.create_entry(
            self.auth_frame,
            placeholder="Enter password",
            show="*",
            width=420,
            height=40,
            fg_color="white",
            border_color="#3B82F6",
            border_width=2
        )
        self.password_entry.pack(pady=(5, 25), padx=30, fill="x")

        self.design.create_button(
            self.auth_frame,
            text="Login",
            width=400,
            height=45,
            fg_color="#2563EB",
            hover_color="#1D4ED8",
            text_color="white",
            corner_radius=12,
            command=self.login
        ).pack(pady=10)

        self.design.create_button(
            self.auth_frame,
            text="Create New Account",
            width=400,
            height=40,
            fg_color="transparent",
            border_width=1,
            hover_color="#2563eb",
            text_color="white",
            command=self.show_register
        ).pack(pady=10)

    def show_register(self):
        self.current_view = "register"
        self.clear_auth_frame()
        self.title("Study Tracker Pro - Create Account")
        self.register_frame = RegisterWindow(self.auth_frame, on_success=self.show_login)
        self.register_frame.pack(fill="both", expand=True)

    def login(self):

        username = (

            self.username_entry
            .get()
            .strip()

        )


        password = (

            self.password_entry
            .get()

        )


        if not username:

            messagebox.showwarning(

                "Login",

                "Please enter your username."

            )

            return


        if not password:

            messagebox.showwarning(

                "Login",

                "Please enter your password."

            )

            return


        user = (

            self.database
            .login_user(

                username,

                password

            )

        )


        if user:

            UserSession.login(

                user

            )

            try:
                # update last_login timestamp
                self.database.set_last_login(UserSession.get_user_id(), datetime.now().isoformat())
            except Exception:
                pass

            messagebox.showinfo(

                "Login Successful",

                f"Welcome, {username}!"

            )


            self.open_dashboard()


        else:

            messagebox.showerror(

                "Login Failed",

                "Invalid username or password."

            )


    def open_register(self):
        self.show_register()

    def clear_login(self):
        if hasattr(self, "username_entry"):
            self.username_entry.delete(0, "end")
        if hasattr(self, "password_entry"):
            self.password_entry.delete(0, "end")

    def register_user(self):
        if not hasattr(self, "register_frame") or self.register_frame is None:
            return
        self.register_frame.register_user()


    def open_dashboard(self):

        """
        Opens dashboard after successful login.
        """

        self.withdraw()


        try:

            from dashboard import DashboardWindow


            dashboard = DashboardWindow(

                self,

                UserSession.get_user(),
                settings_manager=self.settings_manager,
            )


            dashboard.protocol(

                "WM_DELETE_WINDOW",

                self.logout

            )


        except ImportError as error:

            messagebox.showerror(

                "Application Error",

                f"Unable to open dashboard:\n{error}"

            )


            self.deiconify()


    def logout(self):

        UserSession.logout()

        self.destroy()


# ==========================================================
# PASSWORD MANAGER
# ==========================================================

class PasswordManager:
    """
    Handles password-related operations.
    """

    def __init__(self):

        self.database = DatabaseManager()


    def change_password(

        self,

        user_id,

        old_password,

        new_password,

        confirm_password

    ):

        if new_password != confirm_password:

            return False, (

                "New passwords do not match."

            )


        valid, message = (

            AuthenticationValidator
            .validate_password(

                new_password

            )

        )


        if not valid:

            return False, message


        user = (

            self.database
            .get_user_by_id(

                user_id

            )

        )


        if not user:

            return False, (

                "User does not exist."

            )


        if user[3] != old_password:

            return False, (

                "Old password is incorrect."

            )


        success = (

            self.database
            .change_password(

                user_id,

                new_password

            )

        )


        if success is None:

            return True, (

                "Password changed successfully."

            )


        return True, (

            "Password changed successfully."

        )