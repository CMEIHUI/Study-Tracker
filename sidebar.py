"""
sidebar.py

Study Tracker Pro

Reusable sidebar navigation component.
"""

import customtkinter as ctk

from design_system import DesignSystem


# ==========================================================
# SIDEBAR CLASS
# ==========================================================

class Sidebar(ctk.CTkFrame):
    """
    Reusable navigation sidebar.

    This class demonstrates:

    1. Class
    2. Object
    3. Inheritance
    4. Encapsulation
    5. Callback functions
    6. List data structure
    """

    def __init__(
        self,
        master,
        navigation_callback=None,
        logout_callback=None
    ):

        self.design = DesignSystem()
        super().__init__(
            master,
            width=180,
            corner_radius=0,
            fg_color="#0F172A",
        )

        self.navigation_callback = navigation_callback
        self.logout_callback = logout_callback

        self.pack_propagate(False)
        self.configure(border_width=0)

        # LIST DATA STRUCTURE
        #
        # Each item contains:
        #
        # (Button Text, Navigation Name, Icon)

        self.navigation_items = [
            ("Dashboard", "dashboard", "🏠"),
            ("Search", "search", "🔍"),
            ("Subjects", "subjects", "📚"),
            ("Tasks", "tasks", "✅"),
            ("Timer", "timer", "⏱"),
            ("Calendar", "calendar", "📅"),
            ("Analytics", "analytics", "📈"),
            ("Reports", "reports", "📝"),
            ("AI Assistant", "ai_assistant", "🤖"),
            ("Profile", "profile", "👤"),
            ("Settings", "settings", "⚙️"),
        ]


        self.create_widgets()


    # ======================================================
    # CREATE WIDGETS
    # ======================================================

    def create_widgets(self):

        self.create_logo()

        self.create_navigation_buttons()

        self.create_logout_button()


    # ======================================================
    # LOGO
    # ======================================================

    def create_logo(self):

        self.logo_label = self.design.create_label(
            self,
            text="Study Tracker",
            size="xl",
            weight="bold",
            text_color="#f8fafc"
        )


        self.logo_label.pack(

            pady=(32, 4)

        )


        self.subtitle_label = self.design.create_label(
            self,
            text="PRO",
            size="sm",
            weight="bold",
            text_color="#93c5fd"
        )


        self.subtitle_label.pack(

            pady=(0, 24)

        )


    # ======================================================
    # NAVIGATION BUTTONS
    # ======================================================

    def create_navigation_buttons(self):

        self.navigation_frame = ctk.CTkFrame(

            self,

            fg_color="transparent"

        )


        self.navigation_frame.pack(

            fill="both",

            expand=True,

            padx=10,
            pady=(0, 8)

        )


        for button_text, page_name, icon in self.navigation_items:
            self.create_navigation_button(button_text, page_name, icon)


    def create_navigation_button(

        self,

        button_text,

        page_name,

        icon=None

    ):

        label_text = f"{icon}  {button_text}" if icon else button_text

        button = self.design.create_button(
            self.navigation_frame,
            text=label_text,
            command=lambda page=page_name: self.navigate(page),
            style="secondary",
            height=46,
            corner_radius=16,
            border_width=0,
            fg_color="transparent",
            hover_color="#1E40AF",
            text_color="white",
        )

        button.pack(
            fill="x",
            padx=12,
            pady=6,
        )


    # ======================================================
    # NAVIGATION
    # ======================================================

    def navigate(

        self,

        page_name

    ):

        if self.navigation_callback:

            self.navigation_callback(

                page_name

            )


    # ======================================================
    # LOGOUT BUTTON
    # ======================================================

    def create_logout_button(self):

        self.logout_button = ctk.CTkButton(
            self,
            text="Logout",
            command=self.logout,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white",
            corner_radius=10,
            height=40,
        )


        self.logout_button.pack(

            side="bottom",

            fill="x",

            padx=20,

            pady=20

        )


    def logout(self):

        if self.logout_callback:

            self.logout_callback()


    # ======================================================
    # ACTIVE PAGE
    # ======================================================

    def set_active_page(

        self,

        page_name

    ):

        """

        Highlights the current page.

        """

        for button in (

            self.navigation_frame
            .winfo_children()

        ):

            button.configure(

                fg_color="transparent",
                hover_color="#1E40AF",
                border_color="#334155",
                text_color="white"

            )


        for index, item in enumerate(self.navigation_items):
            _, current_page, _ = item
            if current_page == page_name:
                active_button = self.navigation_frame.winfo_children()[index]
                active_button.configure(
                    fg_color="#2563EB",
                    hover_color="#1d4ed8",
                    border_color="#2563EB",
                    text_color="#ffffff"
                )


    # ======================================================
    # ENABLE / DISABLE SIDEBAR
    # ======================================================

    def enable_sidebar(self):

        for button in (

            self.navigation_frame
            .winfo_children()

        ):

            button.configure(

                state="normal"

            )


        self.logout_button.configure(

            state="normal"

        )


    def disable_sidebar(self):

        for button in (

            self.navigation_frame
            .winfo_children()

        ):

            button.configure(

                state="disabled"

            )


        self.logout_button.configure(

            state="disabled"

        )

