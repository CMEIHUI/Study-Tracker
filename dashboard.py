import os
import tkinter as tk
import customtkinter as ctk
from tkinter import messagebox
from datetime import date, datetime, timedelta
from database import DatabaseManager

# Track and cancel pending after callbacks for all Tk widgets on destroy.
# This avoids "invalid command name" Tcl errors when scheduled callbacks fire
# after a widget has already been destroyed during test teardown.
if not hasattr(tk, "_ctk_after_patched"):
    _original_misc_after = tk.Misc.after
    _original_misc_destroy = tk.Misc.destroy

    def _patched_misc_after(self, ms, func=None, *args, _original_misc_after=_original_misc_after, **kwargs):
        callback_id = _original_misc_after(self, ms, func, *args, **kwargs)
        try:
            self._ctk_after_callback_ids.append(callback_id)
        except AttributeError:
            self._ctk_after_callback_ids = [callback_id]
        except Exception:
            pass
        return callback_id

    def _patched_misc_destroy(self, *args, _original_misc_destroy=_original_misc_destroy, **kwargs):
        for callback_id in getattr(self, "_ctk_after_callback_ids", []):
            try:
                self.after_cancel(callback_id)
            except Exception:
                pass
        self._ctk_after_callback_ids = []
        return _original_misc_destroy(self, *args, **kwargs)

    tk.Misc.after = _patched_misc_after
    tk.Misc.destroy = _patched_misc_destroy
    tk._ctk_after_patched = True

# Suppress harmless Tk after-callback errors from CustomTkinter internal cleanup.
# Some callbacks may still fire after a widget is destroyed, producing
# "invalid command name" Tcl errors during teardown.
_original_report_callback_exception = tk.Tk.report_callback_exception

def _report_callback_exception(self, exc, val, tb):
    if isinstance(exc, tk.TclError) and "invalid command name" in str(val):
        return
    return _original_report_callback_exception(self, exc, val, tb)

try:
    tk.Tk.report_callback_exception = _report_callback_exception
except Exception:
    pass
from sidebar import Sidebar
from appearance_manager import AppearanceManager
from models import (
    Student,
    StudyTask,
    StudySession,
    Subject
)
from ai_service import analyze_study_performance
from subject import SubjectWindow
from task import TaskWindow
from timer import TimerWindow
from calendar_page import CalendarWindow
from analytics import AnalyticsWindow
from report import ReportWindow
from setting import SettingsWindow
from reminders import Reminder, ReminderManager, REMINDER_TYPES, REPEAT_OPTIONS
from search_utils import filter_search_results
from design_system import DesignSystem
from utils import run_in_background, handle_operation_error, animate_progress


# ==========================================================
class GlobalSearch(ctk.CTkFrame):
    """Global search panel for subjects, tasks, and sessions."""
    def __init__(self, master, database):
        super().__init__(master, corner_radius=15)
        self.design = DesignSystem()
        self.database = database
        self._search_cache = None
        self.create_widgets()
        self.load_results()

    def create_widgets(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self.header_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=20, pady=(20, 10))
        self.header_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.header_frame,
            text="Global Search",
            size="2xl",
            weight="bold"
        ).grid(row=0, column=0, sticky="w")

        self.design.create_label(
            self.header_frame,
            text="Find subjects, tasks, and study sessions in one place.",
            size="sm",
            text_color=self.design.get_color("text_secondary")
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        self.controls_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.controls_frame.grid(row=1, column=0, sticky="ew", padx=20, pady=(0, 10))

        self.search_entry = self.design.create_entry(
            self.controls_frame,
            placeholder="Search by keyword...",
            width=320,
            height=44
        )
        self.search_entry.grid(row=0, column=0, sticky="w", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", lambda event: self.load_results())

        self.entity_filter = ctk.CTkComboBox(
            self.controls_frame,
            width=170,
            values=["All", "Subjects", "Tasks", "Study Sessions"],
            command=lambda value: self.load_results()
        )
        self.entity_filter.set("All")
        self.entity_filter.grid(row=0, column=1, sticky="w", padx=5)

        self.status_filter = ctk.CTkComboBox(
            self.controls_frame,
            width=140,
            values=["All", "Pending", "Completed"],
            command=lambda value: self.load_results()
        )
        self.status_filter.set("All")
        self.status_filter.grid(row=0, column=2, sticky="w", padx=5)

        self.priority_filter = ctk.CTkComboBox(
            self.controls_frame,
            width=140,
            values=["All", "High", "Medium", "Low"],
            command=lambda value: self.load_results()
        )
        self.priority_filter.set("All")
        self.priority_filter.grid(row=0, column=3, sticky="w", padx=5)

        self.sort_filter = ctk.CTkComboBox(
            self.controls_frame,
            width=150,
            values=["Name", "Due date", "Priority", "Status"],
            command=lambda value: self.load_results()
        )
        self.sort_filter.set("Name")
        self.sort_filter.grid(row=0, column=4, sticky="w", padx=5)

        self.results_container = ctk.CTkScrollableFrame(
            self,
            corner_radius=18,
            fg_color=self.design.theme["surface"],
            border_width=1,
            border_color="#E2E8F0"
        )
        self.results_container.grid(row=2, column=0, sticky="nsew", padx=20, pady=(5, 20))
        self.results_container.grid_columnconfigure(0, weight=1)

    def load_results(self):
        keyword = self.search_entry.get().strip()
        entity_type = self.entity_filter.get()
        status_filter = self.status_filter.get()
        priority_filter = self.priority_filter.get()
        sort_mode = self.sort_filter.get()
        cache_key = (keyword, entity_type, status_filter, priority_filter, sort_mode)
        if self._search_cache is not None and self._search_cache[0] == cache_key:
            self._display_search_results(self._search_cache[1])
            return

        for widget in self.results_container.winfo_children():
            widget.destroy()
        self.design.create_label(
            self.results_container,
            text="Searching...",
            size="base",
            text_color=self.design.get_color("text_secondary")
        ).pack(anchor="w", pady=20)
        run_in_background(
            self,
            self._load_search_results,
            callback=self._display_search_results,
            error_callback=self._show_search_error,
        )

    def _load_search_results(self):
        keyword = self.search_entry.get().strip()
        entity_type = self.entity_filter.get()
        status_filter = self.status_filter.get()
        priority_filter = self.priority_filter.get()
        sort_mode = self.sort_filter.get()

        subject_rows = []
        task_rows = []
        session_rows = []

        if entity_type in ("All", "Subjects"):
            subject_rows = filter_search_results(
                self.database.get_all_subjects(),
                keyword=keyword,
                entity_type="Subjects",
                status_filter=status_filter,
                priority_filter=priority_filter,
                sort_mode=sort_mode,
            )

        if entity_type in ("All", "Tasks"):
            task_rows = filter_search_results(
                self.database.get_all_tasks(),
                keyword=keyword,
                entity_type="Tasks",
                status_filter=status_filter,
                priority_filter=priority_filter,
                sort_mode=sort_mode,
            )

        if entity_type in ("All", "Study Sessions"):
            session_rows = filter_search_results(
                self.database.get_all_study_sessions(),
                keyword=keyword,
                entity_type="Study Sessions",
                status_filter=status_filter,
                priority_filter=priority_filter,
                sort_mode=sort_mode,
            )

        return subject_rows, task_rows, session_rows

    def _display_search_results(self, payload):
        if not payload:
            return
        keyword = self.search_entry.get().strip()
        entity_type = self.entity_filter.get()
        status_filter = self.status_filter.get()
        priority_filter = self.priority_filter.get()
        sort_mode = self.sort_filter.get()
        self._search_cache = ((keyword, entity_type, status_filter, priority_filter, sort_mode), payload)
        for widget in self.results_container.winfo_children():
            widget.destroy()
        subject_rows, task_rows, session_rows = payload
        if not subject_rows and not task_rows and not session_rows:
            ctk.CTkLabel(
                self.results_container,
                text="No matches found.",
                font=("Arial", 14)
            ).pack(anchor="w", pady=20)
            return
        if subject_rows:
            self.create_section("Subjects", subject_rows, self.create_subject_row)
        if task_rows:
            self.create_section("Tasks", task_rows, self.create_task_row)
        if session_rows:
            self.create_section("Study Sessions", session_rows, self.create_session_row)

    def _show_search_error(self, error, safe_message=None):
        for widget in self.results_container.winfo_children():
            widget.destroy()
        friendly_message = safe_message or handle_operation_error(
            error,
            context="searching dashboard data",
            user_message="We couldn't search right now. Please try again.",
        )
        ctk.CTkLabel(self.results_container, text=friendly_message, font=("Arial", 14)).pack(anchor="w", pady=20)

    def create_section(self, title, rows, renderer):
        self.design.create_label(
            self.results_container,
            text=title,
            size="lg",
            weight="bold"
        ).pack(anchor="w", padx=5, pady=(12, 8))

        for row in rows:
            card = self.design.create_card(
                self.results_container,
                corner_radius=14,
                fg_color=self.design.theme["surface"],
                border_color="#E2E8F0"
            )
            card.pack(fill="x", padx=5, pady=6)
            renderer(card, row)

    def create_subject_row(self, parent, subject):
        self.design.create_label(
            parent,
            text="●",
            size="2xl",
            text_color=subject[2] or self.design.theme["primary"],
            weight="bold"
        ).pack(side="left", padx=(14, 10), pady=12)
        self.design.create_label(
            parent,
            text=subject[1],
            size="base",
            weight="bold"
        ).pack(side="left", padx=5, pady=12)

    def create_task_row(self, parent, task):
        self.design.create_label(
            parent,
            text=task[2],
            size="base",
            weight="bold"
        ).pack(anchor="w", padx=12, pady=(12, 4))
        self.design.create_label(
            parent,
            text=f"{task[1]} • Priority: {task[4]} • Deadline: {task[5] or 'No deadline'}",
            size="sm",
            text_color=self.design.get_color("text_secondary")
        ).pack(anchor="w", padx=12, pady=2)
        self.design.create_label(
            parent,
            text=f"Status: {task[6]}",
            size="sm",
            text_color=self.design.get_color("text_secondary")
        ).pack(anchor="w", padx=12, pady=(2, 12))

    def create_session_row(self, parent, session):
        duration_hours = round(session[2] / 60, 1) if session[2] else 0
        text = f"{session[1]} • {duration_hours}h • {session[3]}"
        self.design.create_label(
            parent,
            text=text,
            size="sm",
            text_color=self.design.get_color("text_secondary")
        ).pack(anchor="w", padx=12, pady=12)


# ==========================================================
# DASHBOARD CARD
# ==========================================================

class DashboardCard(ctk.CTkFrame):
    """
    Reusable dashboard statistics card.
    """

    def __init__(
        self,
        master,
        title,
        value="0",
        icon="●",
        subtitle="",
        progress_value=None,
        accent_color="#2563eb",
    ):

        self.design = DesignSystem()
        super().__init__(
            master,
            width=180,
            height=120,
            corner_radius=15,
            fg_color=self.design.get_color("surface"),
            border_width=1,
            border_color="#E2E8F0"
        )
        self.grid_propagate(False)

        self.title = title
        self.subtitle = subtitle
        self.accent_color = accent_color

        self.icon_frame = ctk.CTkFrame(
            self,
            corner_radius=16,
            fg_color=self.design.get_color("background"),
            border_width=0,
        )
        self.icon_frame.grid(row=0, column=0, rowspan=3, sticky="nsw", padx=(8, 8), pady=(8, 8))
        self.icon_frame.grid_rowconfigure(0, weight=1)
        self.icon_frame.grid_columnconfigure(0, weight=1)

        self.icon_label = self.design.create_label(
            self.icon_frame,
            text=icon,
            size="lg",
            weight="bold",
            text_color=accent_color,
        )
        self.icon_label.grid(row=0, column=0, padx=8, pady=8)

        self.title_label = self.design.create_label(
            self,
            text=title,
            size="xs",
            weight="bold",
            text_color=self.design.get_color("text_secondary")
        )
        self.title_label.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(8, 4))

        if subtitle:
            self.subtitle_label = self.design.create_label(
                self,
                text=subtitle,
                size="xs",
                text_color=self.design.get_color("text_secondary")
            )
            self.subtitle_label.grid(row=1, column=1, sticky="w", padx=(0, 8), pady=(0, 4))

        self.value_label = self.design.create_label(
            self,
            text=str(value),
            size="lg",
            weight="bold",
            text_color=self.design.get_color("text_primary")
        )
        self.value_label.grid(row=2, column=1, sticky="w", padx=(0, 8), pady=(4, 8))

        if progress_value is not None:
            self.progress_bar = ctk.CTkProgressBar(
                self,
                height=6,
                fg_color=self.design.get_color("background"),
                progress_color=accent_color,
                corner_radius=4,
            )
            self.progress_bar.grid(row=3, column=1, columnspan=1, sticky="ew", padx=(0, 14), pady=(0, 16))
            self.progress_bar.set(max(0.0, min(1.0, float(progress_value))))

        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=0)

    def update_value(self, value):
        self.value_label.configure(text=str(value))

    def set_progress(self, value):
        if hasattr(self, "progress_bar"):
            try:
                animate_progress(self.progress_bar, max(0.0, min(1.0, float(value))))
            except Exception:
                try:
                    self.progress_bar.set(max(0.0, min(1.0, float(value))))
                except Exception:
                    pass


# ==========================================================
# DASHBOARD WINDOW
# ==========================================================

class DashboardWindow(ctk.CTkToplevel):
    """
    Main application dashboard.
    """

    def __init__(
        self,
        parent,
        user_data,
        settings_manager=None,
    ):

        super().__init__(
            parent
        )


        self.parent = parent

        self.user_data = user_data

        self.database = DatabaseManager()
        self.design = DesignSystem()
        self.settings_manager = settings_manager or getattr(parent, "settings_manager", None)
        if self.settings_manager is None:
            from setting import SettingsManager
            self.settings_manager = SettingsManager(self.database)
        self.appearance_manager = AppearanceManager.get_instance()
        self.appearance_manager.load_settings(self.settings_manager.get_all_settings())
        self.settings_manager.apply_settings(target=self)
        self.reminder_manager = ReminderManager(self.database)

        self.title(
            "Study Tracker Pro - Dashboard"
        )


        self.geometry(
            "1250x750"
        )


        self.minsize(
            900,
            600
        )

        self.resizable(
            True,
            True
        )


        self.protocol(

            "WM_DELETE_WINDOW",

            self.close_window

        )


        self._create_background_layer()
        self.create_layout()
        self.reminder_manager.start_scheduler()


    def _create_background_layer(self):
        self.background_label = tk.Label(self, bg="#0f172a", bd=0, highlightthickness=0)
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
        self.background_label.configure(image=photo, bg="#0f172a")
        self.background_label.image = photo
        try:
            self.background_label.update_idletasks()
        except Exception:
            pass

    def apply_appearance_settings(self, event=None):
        if not hasattr(self, "background_label"):
            return
        self.appearance_manager.apply_current_state(target=self, settings=self.settings_manager.get_all_settings())

    def apply_application_settings(self, settings=None):
        if settings is None:
            settings = self.settings_manager.get_all_settings() if self.settings_manager is not None else {}
        if not hasattr(self, "page_container") or self.page_container is None:
            return
        for child in list(self.page_container.winfo_children()):
            if hasattr(child, "apply_application_settings"):
                try:
                    child.apply_application_settings(settings)
                except Exception:
                    pass

    def navigate_to_page(self, page_name):

        if page_name == "dashboard":
            self.show_dashboard()

        elif page_name == "search":
            self.show_page("search")

        elif page_name == "subjects":
            self.show_page("subjects")

        elif page_name == "tasks":
            self.show_page("tasks")

        elif page_name == "timer":
            self.show_page("timer")

        elif page_name == "calendar":
            self.show_page("calendar")

        elif page_name == "analytics":
            self.show_page("analytics")

        elif page_name == "reports":
            self.show_page("reports")

        elif page_name == "ai_assistant":
            self.show_page("ai_assistant")

        elif page_name == "profile":
            self.show_page("profile")

        elif page_name == "settings":
            self.show_page("settings")


    # ======================================================
    # CREATE LAYOUT
    # ======================================================

    def create_layout(self):

        self.grid_columnconfigure(
            0,
            minsize=250
        )

        self.grid_columnconfigure(
            1,
            weight=1
        )


        self.grid_rowconfigure(
            0,
            weight=1
        )


        # --------------------------------------------------
        # SIDEBAR
        # --------------------------------------------------

        self.create_sidebar()
        self.sidebar.set_active_page("dashboard")

        # --------------------------------------------------
        # MAIN CONTENT
        # --------------------------------------------------

        self.main_frame = ctk.CTkFrame(

            self,
            corner_radius=0,
            fg_color="transparent"

        )

        self.main_frame.grid(

            row=0,

            column=1,

            sticky="nsew",

            padx=(0, 16),

            pady=16

        )


        self.main_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.main_frame.grid_rowconfigure(

            3,

            weight=1

        )


        self.create_header()

        self.create_stat_cards()

        self.create_content_area()


    # ======================================================
    # SIDEBAR
    # ======================================================

    def create_sidebar(self):

        self.sidebar = Sidebar(

            self,

            navigation_callback=self.navigate_to_page,

            logout_callback=self.logout

        )

        self.sidebar.grid(

            row=0,

            column=0,

            sticky="nsew"

        )

        self.sidebar.grid_propagate(

            False

        )


    # ======================================================
    # HEADER
    # ======================================================

# ======================================================
    # HEADER
    # ======================================================

    def create_header(self):

        self.header_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )

        self.header_frame.grid(
            row=0,
            column=0,
            sticky="ew",
            padx=20,
            pady=(20, 10)
        )

        self.header_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.header_frame,
            text=f"Welcome back, {self.user_data[1]}!",
            size="3xl",
            weight="bold"
        ).grid(row=0, column=0, sticky="w")

        self.design.create_label(
            self.header_frame,
            text="Track your progress and achieve your study goals.",
            size="lg",
            text_color=self.design.get_color("text_secondary")
        ).grid(row=1, column=0, sticky="w", pady=(6, 0))


    # ======================================================
    # STATISTIC CARDS
    # ======================================================

    def create_stat_cards(self):

        self.cards_frame = ctk.CTkFrame(
            self.main_frame,
            fg_color="transparent"
        )

        self.cards_frame.grid(
            row=1,
            column=0,
            sticky="ew",
            padx=10,
            pady=8
        )

        card_configs = [
            {
                "attr": "total_subjects_card",
                "title": "Study Time",
                "value": "0h",
                "icon": "⏱️",
                "subtitle": "Focus time today",
                "accent_color": "#2563eb",
            },
            {
                "attr": "total_tasks_card",
                "title": "Tasks",
                "value": "0",
                "icon": "📝",
                "subtitle": "Open priorities",
                "accent_color": "#7c3aed",
            },
            {
                "attr": "completed_card",
                "title": "Completed",
                "value": "0",
                "icon": "✅",
                "subtitle": "Done this cycle",
                "accent_color": "#059669",
            },
            {
                "attr": "pending_card",
                "title": "Exams",
                "value": "0",
                "icon": "📚",
                "subtitle": "Soon to prepare",
                "accent_color": "#f59e0b",
            },
            {
                "attr": "study_hours_card",
                "title": "Study Hours",
                "value": "0%",
                "icon": "📈",
                "subtitle": "Today's progress",
                "accent_color": "#f97316",
                "progress_value": 0,
            },
            {
                "attr": "streak_card",
                "title": "Streak",
                "value": "0 days",
                "icon": "🔥",
                "subtitle": "Daily consistency",
                "accent_color": "#ef4444",
            },
            {
                "attr": "badges_card",
                "title": "Badges",
                "value": "0",
                "icon": "🏅",
                "subtitle": "Unlocked rewards",
                "accent_color": "#fbbf24",
            },
            {
                "attr": "progress_level_card",
                "title": "Rank",
                "value": "Beginner",
                "icon": "⭐",
                "subtitle": "Your study rank",
                "accent_color": "#10b981",
            },
            {
                "attr": "level_card",
                "title": "Level",
                "value": "Lv 1",
                "icon": "🎖️",
                "subtitle": "Experience points",
                "accent_color": "#6366f1",
            },
        ]

        self._dashboard_stat_card_widgets = []
        for config in card_configs:
            card = DashboardCard(
                self.cards_frame,
                config["title"],
                config["value"],
                icon=config["icon"],
                subtitle=config["subtitle"],
                accent_color=config["accent_color"],
            )
            setattr(self, config["attr"], card)
            self._dashboard_stat_card_widgets.append(card)

        try:
            from design_system import attach_tooltip
            if hasattr(self.level_card, "progress_bar"):
                attach_tooltip(self.level_card.progress_bar, lambda: f"{int(round(getattr(self.level_card.progress_bar, '_animated_value', 0.0) * 100))}%")
        except Exception:
            pass

        self.bind("<Configure>", self._apply_stat_card_layout, add="+")
        self._apply_stat_card_layout()

    def _apply_stat_card_layout(self, event=None):
        if not hasattr(self, "cards_frame") or self.cards_frame is None or not self.cards_frame.winfo_exists():
            return

        if not getattr(self, "_dashboard_stat_card_widgets", None):
            return

        width = max(int(self.winfo_width() or 0), 1)
        if width >= 1200:
            columns = 4
        elif width >= 900:
            columns = 3
        elif width >= 700:
            columns = 2
        else:
            columns = 1

        total_cards = len(self._dashboard_stat_card_widgets)
        rows = (total_cards + columns - 1) // columns if columns else 1

        for column in range(4):
            self.cards_frame.grid_columnconfigure(column, weight=1 if column < columns else 0)

        for row in range(rows):
            self.cards_frame.grid_rowconfigure(row, weight=1)

        for idx, card in enumerate(self._dashboard_stat_card_widgets):
            if not getattr(card, "winfo_exists", None) or not card.winfo_exists():
                continue
            row = idx // columns
            column = idx % columns
            try:
                card.grid(row=row, column=column, sticky="nsew", padx=6, pady=6)
            except tk.TclError:
                continue


    # ======================================================
    # CONTENT AREA
    # ======================================================

    def create_content_area(self):

        self.content_frame = ctk.CTkScrollableFrame(

            self.main_frame,
            corner_radius=18,
            fg_color="#111827",
            border_width=1,
            border_color="#334155"

        )


        self.content_frame.grid(

            row=3,

            column=0,

            sticky="nsew",

            padx=20,

            pady=(0, 15)

        )


        self.content_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.content_frame.grid_columnconfigure(

            1,

            weight=1

        )


        self.content_frame.grid_rowconfigure(

            0,

            weight=1

        )

        self.content_frame.grid_rowconfigure(

            1,

            weight=1

        )

        self.page_container = ctk.CTkFrame(
            self.content_frame,
            corner_radius=0,
            fg_color="transparent"
        )
        self.page_container.grid(
            row=0,
            column=0,
            sticky="nsew",
            padx=0,
            pady=0
        )
        self.page_container.grid_columnconfigure(0, weight=1)
        self.page_container.grid_columnconfigure(1, weight=1)
        self.page_container.grid_rowconfigure(0, weight=1)
        self.page_container.grid_rowconfigure(1, weight=1)

        self.page_frames = {}
        self._dashboard_loaded = False
        self._dashboard_payload = None
        self._dashboard_tasks = None
        self._dashboard_subjects = None
        self._dashboard_sessions = None
        self._dashboard_subject_stats = None
        self._dashboard_achievements = None

        self.build_dashboard_view()
        self.show_dashboard()


    def build_dashboard_view(self):

        if hasattr(self, "dashboard_view_frame") and self.dashboard_view_frame is not None:
            for widget in self.dashboard_view_frame.winfo_children():
                widget.destroy()
        else:
            self.dashboard_view_frame = ctk.CTkFrame(
                self.page_container,
                corner_radius=0,
                fg_color="transparent"
            )
            self.dashboard_view_frame.grid(
                row=0,
                column=0,
                sticky="nsew",
                padx=0,
                pady=0
            )
            self.dashboard_view_frame.grid_columnconfigure(0, weight=1)
            self.dashboard_view_frame.grid_columnconfigure(1, weight=1)
            self.dashboard_view_frame.grid_rowconfigure(0, weight=1)

        self.page_frames["dashboard"] = self.dashboard_view_frame

        self.dashboard_scroll = ctk.CTkScrollableFrame(
            self.dashboard_view_frame,
            corner_radius=18,
            fg_color="transparent"
        )
        self.dashboard_scroll.grid(row=0, column=0, columnspan=2, sticky="nsew", padx=10, pady=10)
        self.dashboard_scroll.grid_columnconfigure(0, weight=1)
        self.dashboard_scroll.grid_columnconfigure(1, weight=1)
        for row in range(7):
            if row == 0:
                weight = 0
            elif row == 1:
                weight = 1
            else:
                weight = 2
            self.dashboard_scroll.grid_rowconfigure(row, weight=weight)

        self.welcome_card = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=24,
        )
        self.welcome_card.grid(row=0, column=0, columnspan=2, sticky="ew", padx=6, pady=6)
        self.welcome_card.grid_columnconfigure(0, weight=1)

        welcome_top = ctk.CTkFrame(self.welcome_card, fg_color="transparent")
        welcome_top.pack(fill="x", padx=14, pady=(12, 6))

        self.design.create_label(
            welcome_top,
            text="👋",
            size="2xl",
            weight="bold",
            text_color="#2563eb"
        ).pack(side="left", padx=(0, 8))

        self.design.create_label(
            welcome_top,
            text=f"Welcome back, {self.user_data[1]}!",
            size="xl",
            weight="bold",
            text_color="white"
        ).pack(side="left")

        # Quick level panel placed on the right of the welcome card
        self.welcome_level_frame = ctk.CTkFrame(self.welcome_card, fg_color="transparent")
        self.welcome_level_frame.pack(side="right", padx=14, pady=(12, 6))

        self.welcome_level_button = ctk.CTkButton(
            self.welcome_level_frame,
            text="Lv 1",
            width=90,
            fg_color="#fff",
            hover=False,
            command=lambda: self._open_gamification_modal(),
        )
        self.welcome_level_button.pack(anchor="e", pady=(0, 4))

        # attach tooltip to quick level button
        try:
            from design_system import attach_tooltip
            attach_tooltip(self.welcome_level_button, "View detailed gamification stats")
        except Exception:
            pass

        self.welcome_level_progress = ctk.CTkProgressBar(
            self.welcome_level_frame,
            height=5,
            fg_color="#e2e8f0",
            progress_color="#f59e0b",
            corner_radius=4,
        )
        self.welcome_level_progress.pack(fill="x")
        try:
            from design_system import attach_tooltip
            attach_tooltip(self.welcome_level_progress, lambda: f"{int(round(getattr(self.welcome_level_progress, '_animated_value', 0.0) * 100))}%")
        except Exception:
            pass

        self.design.create_label(
            self.welcome_card,
            text="Keep momentum going with a focused study schedule.",
            size="sm",
            text_color="#CBD5E1"
        ).pack(anchor="w", padx=18, pady=(0, 14))

        self.progress_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.progress_frame.grid(row=1, column=0, sticky="nsew", padx=6, pady=6)
        self.progress_frame.grid_columnconfigure(0, weight=1)
        self.progress_frame.grid_rowconfigure(0, weight=1)

        self.design.create_label(
            self.progress_frame,
            text="📈 Weekly Progress",
            size="lg",
            weight="bold"
        ).pack(anchor="w", padx=16, pady=(14, 8))

        self.progress_bar = ctk.CTkProgressBar(
            self.progress_frame,
            height=7,
            fg_color="#e2e8f0",
            progress_color="#2563eb",
            corner_radius=5,
        )
        self.progress_bar.pack(fill="x", padx=16, pady=8)
        self.progress_bar.set(0)

        self.progress_label = self.design.create_label(
            self.progress_frame,
            text="0% completed",
            size="sm",
            text_color="#64748b"
        )
        self.progress_label.pack(anchor="w", padx=16, pady=(4, 8))

        self.dashboard_loading_label = self.design.create_label(
            self.progress_frame,
            text="",
            size="sm",
            text_color="#64748b"
        )
        self.dashboard_loading_label.pack(anchor="w", padx=20, pady=(0, 10))

        self.insight_frame = ctk.CTkFrame(
            self.progress_frame,
            fg_color="transparent"
        )
        self.insight_frame.pack(fill="x", padx=20, pady=(0, 10))

        self.insight_chart_frame = ctk.CTkFrame(
            self.progress_frame,
            fg_color="transparent"
        )
        self.insight_chart_frame.pack(fill="x", padx=20, pady=(0, 15))

        self.right_column_panel = ctk.CTkFrame(
            self.dashboard_scroll,
            fg_color="transparent"
        )
        self.right_column_panel.grid(row=1, column=1, sticky="nsew", padx=8, pady=8)
        self.right_column_panel.grid_columnconfigure(0, weight=1)
        self.right_column_panel.grid_rowconfigure(0, weight=1)
        self.right_column_panel.grid_rowconfigure(1, weight=4)

        self.goals_frame = self.design.create_card(
            self.right_column_panel,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.goals_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.goals_frame.grid_columnconfigure(0, weight=1)

        self.right_lower_panel = ctk.CTkFrame(
            self.right_column_panel,
            fg_color="transparent"
        )
        self.right_lower_panel.grid(row=1, column=0, sticky="nsew", padx=0, pady=0)
        self.right_lower_panel.grid_columnconfigure(0, weight=1)
        self.right_lower_panel.grid_rowconfigure(0, weight=1)
        self.right_lower_panel.grid_rowconfigure(1, weight=1)
        self.right_lower_panel.grid_rowconfigure(2, weight=1)

        self.notifications_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.notifications_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        self.notifications_frame.grid_columnconfigure(0, weight=1)

        self.reminder_button_frame = ctk.CTkFrame(self.notifications_frame, fg_color="transparent")
        self.reminder_button_frame.pack(fill="x", padx=15, pady=(8, 0))

        ctk.CTkButton(
            self.reminder_button_frame,
            text="Add Reminder",
            width=140,
            command=self._open_add_reminder_modal,
        ).pack(side="left", padx=(0, 10))

        self.reminder_filter = ctk.CTkComboBox(
            self.reminder_button_frame,
            width=180,
            values=["All"] + REMINDER_TYPES,
            command=lambda value: self.load_dashboard_data(),
        )
        self.reminder_filter.set("All")
        self.reminder_filter.pack(side="left")

        self.notification_content_frame = ctk.CTkFrame(self.notifications_frame, fg_color="transparent")
        self.notification_content_frame.pack(fill="both", expand=True, padx=15, pady=(8, 10))

        self.leaderboard_frame = self.design.create_card(
            self.right_lower_panel,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.leaderboard_frame.grid(row=0, column=0, sticky="nsew", padx=0, pady=(0, 8))
        self.leaderboard_frame.grid_columnconfigure(0, weight=1)

        self.ai_history_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.ai_history_frame.grid(row=3, column=0, sticky="nsew", padx=8, pady=8)
        self.ai_history_frame.grid_columnconfigure(0, weight=1)

        self.achievements_frame = self.design.create_card(
            self.right_lower_panel,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.achievements_frame.grid(row=1, column=0, sticky="nsew", padx=0, pady=8)
        self.achievements_frame.grid_columnconfigure(0, weight=1)

        self.recent_tasks_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.recent_tasks_frame.grid(row=4, column=0, sticky="nsew", padx=8, pady=8)
        self.recent_tasks_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.recent_tasks_frame,
            text="🗓️ Today's Tasks",
            size="xl",
            weight="bold"
        ).pack(anchor="w", padx=20, pady=15)

        self.tasks_scrollable = ctk.CTkScrollableFrame(
            self.recent_tasks_frame,
            corner_radius=14,
            fg_color="#f8fafc",
            border_width=1,
            border_color="#E2E8F0"
        )
        self.tasks_scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.subject_frame = self.design.create_card(
            self.right_lower_panel,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.subject_frame.grid(row=2, column=0, sticky="nsew", padx=0, pady=(8, 0))
        self.subject_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.subject_frame,
            text="📚 Subjects",
            size="xl",
            weight="bold"
        ).pack(anchor="w", padx=20, pady=15)

        self.subject_scrollable = ctk.CTkScrollableFrame(
            self.subject_frame,
            corner_radius=14,
            fg_color="#f8fafc",
            border_width=1,
            border_color="#E2E8F0"
        )
        self.subject_scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.streak_calendar_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.streak_calendar_frame.grid(row=5, column=0, columnspan=2, sticky="nsew", padx=8, pady=(8, 8))
        self.streak_calendar_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.streak_calendar_frame,
            text="🔥 Study Streak Calendar",
            size="xl",
            weight="bold"
        ).pack(anchor="w", padx=20, pady=(18, 8))

        self.streak_calendar_content = ctk.CTkFrame(
            self.streak_calendar_frame,
            fg_color="transparent"
        )
        self.streak_calendar_content.pack(fill="both", expand=True, padx=20, pady=(0, 18))

        self.exam_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#ffffff",
            border_color="#E2E8F0",
            corner_radius=20,
        )
        self.exam_frame.grid(row=6, column=0, columnspan=2, sticky="nsew", padx=8, pady=(8, 14))
        self.exam_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.exam_frame,
            text="🧪 Upcoming Exams",
            size="xl",
            weight="bold"
        ).pack(anchor="w", padx=20, pady=15)

        self.exam_scrollable = ctk.CTkScrollableFrame(
            self.exam_frame,
            corner_radius=14,
            fg_color="#f8fafc",
            border_width=1,
            border_color="#E2E8F0"
        )
        self.exam_scrollable.pack(fill="both", expand=True, padx=10, pady=10)

        self.quote_frame = self.design.create_card(
            self.dashboard_scroll,
            fg_color="#eff6ff",
            border_color="#bfdbfe",
            corner_radius=20,
        )
        self.quote_frame.grid(row=7, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 14))
        self.quote_frame.grid_columnconfigure(0, weight=1)

        self.design.create_label(
            self.quote_frame,
            text="💡 Motivational Quote",
            size="xl",
            weight="bold"
        ).pack(anchor="w", padx=20, pady=(18, 8))
        self.design.create_label(
            self.quote_frame,
            text="""Small consistent steps every day compound into extraordinary results.""",
            size="base",
            text_color="#1d4ed8",
            wraplength=720,
            justify="left"
        ).pack(anchor="w", padx=20, pady=(0, 18))


    def show_internal_page(self, title, description, detail_text=""):

        for widget in self.page_container.winfo_children():

            widget.destroy()


        panel = ctk.CTkFrame(

            self.page_container,

            fg_color="transparent"

        )

        panel.pack(

            fill="both",

            expand=True,

            padx=20,

            pady=20

        )


        self.design.create_label(
            panel,
            text=title,
            size="2xl",
            weight="bold"
        ).pack(

            anchor="w",

            padx=10,

            pady=(10, 5)

        )


        self.design.create_label(
            panel,
            text=description,
            size="base",
            text_color=self.design.get_color("text_secondary")
        ).pack(

            anchor="w",

            padx=10,

            pady=(0, 15)

        )


        self.design.create_label(
            panel,
            text=detail_text,
            size="sm",
            text_color=self.design.get_color("text_secondary"),
            wraplength=650,
            justify="left"
        ).pack(

            anchor="w",

            padx=10,

            pady=5

        )


    # ======================================================
    # DASHBOARD HELPERS
    # ======================================================

    def get_today_study_hours(self):
        if getattr(self, "_dashboard_payload", None) is not None:
            return self._dashboard_payload[1]
        today = date.today().strftime("%Y-%m-%d")
        sessions = self.database.get_study_sessions_by_date(today)
        total_minutes = sum(session[2] for session in sessions if session and len(session) >= 3)
        return round(total_minutes / 60, 1)

    def get_current_streak(self):
        if getattr(self, "_dashboard_payload", None) is not None:
            return self._dashboard_payload[2]
        study_dates = self.database.get_study_dates()
        if not study_dates:
            return 0

        parsed_dates = []
        for study_date in study_dates:
            if not study_date:
                continue
            try:
                parsed_dates.append(
                    datetime.strptime(str(study_date), "%Y-%m-%d").date()
                )
            except ValueError:
                try:
                    parsed_dates.append(
                        datetime.strptime(str(study_date), "%Y-%m-%d %H:%M:%S").date()
                    )
                except ValueError:
                    continue

        if not parsed_dates:
            return 0

        unique_dates = sorted(set(parsed_dates))
        streak = 0
        current_day = date.today()
        while current_day in unique_dates:
            streak += 1
            current_day -= timedelta(days=1)

        return streak

    def render_streak_calendar(self, calendar_data):
        for widget in self.streak_calendar_content.winfo_children():
            widget.destroy()

        if not calendar_data:
            ctk.CTkLabel(
                self.streak_calendar_content,
                text="No streak calendar available.",
                font=("Arial", 13)
            ).pack(anchor="w")
            return

        month_name = date(calendar_data["year"], calendar_data["month"], 1).strftime("%B %Y")
        summary_label = ctk.CTkLabel(
            self.streak_calendar_content,
            text=f"{month_name} • Current streak: {calendar_data['current_streak']} • Longest streak: {calendar_data['longest_streak']}",
            font=("Arial", 13, "bold")
        )
        summary_label.pack(anchor="w", pady=(0, 10))

        weekday_row = ctk.CTkFrame(self.streak_calendar_content, fg_color="transparent")
        weekday_row.pack(fill="x", pady=(0, 6))
        for weekday in ["Sun", "Mon", "Tue", "Wed", "Thu", "Fri", "Sat"]:
            label = ctk.CTkLabel(weekday_row, text=weekday, width=48, anchor="center")
            label.pack(side="left")

        grid_frame = ctk.CTkFrame(self.streak_calendar_content, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True)
        grid_frame.grid_columnconfigure(tuple(range(7)), weight=1)

        first_weekday = int(calendar_data.get("first_weekday", 0))
        days_in_month = int(calendar_data.get("days_in_month", 31))
        active_days = set(calendar_data.get("active_days", []))

        for blank_index in range(first_weekday):
            blank_label = ctk.CTkLabel(grid_frame, text="", width=48, height=36)
            blank_label.grid(row=0, column=blank_index, padx=2, pady=2)

        current_row = 0
        for day in range(1, days_in_month + 1):
            column = (first_weekday + day - 1) % 7
            row = (first_weekday + day - 1) // 7
            is_active = day in active_days
            day_bg = "#fee2e2" if is_active else "#f8fafc"
            day_border = "#ef4444" if is_active else "#E2E8F0"
            day_label = ctk.CTkLabel(
                grid_frame,
                text=str(day),
                width=48,
                height=36,
                corner_radius=10,
                fg_color=day_bg,
                text_color="#0f172a" if is_active else "#475569",
                justify="center",
                font=("Arial", 12, "bold")
            )
            day_label.grid(row=row, column=column, padx=2, pady=2, sticky="nsew")

    def render_subject_chart(self, subject_stats):
        for widget in self.insight_chart_frame.winfo_children():
            widget.destroy()

        if not subject_stats:
            ctk.CTkLabel(
                self.insight_chart_frame,
                text="No study history yet.",
                font=("Arial", 13)
            ).pack(anchor="w")
            return

        ctk.CTkLabel(
            self.insight_chart_frame,
            text="Subject momentum",
            font=("Arial", 14, "bold")
        ).pack(anchor="w", pady=(0, 8))

        max_minutes = max(minutes for _, minutes in subject_stats if minutes)
        for subject_name, minutes in subject_stats[:4]:
            row = ctk.CTkFrame(self.insight_chart_frame, fg_color="transparent")
            row.pack(fill="x", pady=3)

            ctk.CTkLabel(
                row,
                text=subject_name[:16],
                width=120,
                anchor="w"
            ).pack(side="left")

            bar = ctk.CTkProgressBar(row, width=220)
            bar.pack(side="left", padx=(10, 8), fill="x", expand=True)
            bar.set(min(1.0, minutes / max(1, max_minutes)))

            ctk.CTkLabel(
                row,
                text=f"{round(minutes / 60, 1)}h",
                width=55,
                anchor="e"
            ).pack(side="left")

    # ======================================================
    # LOAD DASHBOARD DATA
    # ======================================================

    def load_dashboard_data(self):
        if getattr(self, "_dashboard_payload", None) is not None:
            self._apply_dashboard_statistics(self._dashboard_payload)
            return
        self._set_dashboard_loading_state()
        run_in_background(
            self,
            self._load_dashboard_statistics,
            callback=self._apply_dashboard_statistics,
            error_callback=self._show_dashboard_error,
        )

    def _set_dashboard_loading_state(self):
        self.dashboard_loading_label.configure(text="Loading dashboard...")
        for card in (
            self.total_subjects_card,
            self.total_tasks_card,
            self.completed_card,
            self.pending_card,
            self.study_hours_card,
            self.streak_card,
        ):
            card.update_value("...")
        self.progress_bar.set(0)
        self.progress_label.configure(text="Loading...")
        for frame in (self.tasks_scrollable, self.subject_scrollable):
            for widget in frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(frame, text="Loading...", font=("Arial", 13)).pack(pady=20)

    def _load_dashboard_statistics(self):
        statistics = self.database.get_dashboard_statistics() if self.database else {}
        sessions = self.database.get_all_study_sessions() if self.database else []
        today = date.today().strftime("%Y-%m-%d")
        total_minutes = sum(
            session[2] for session in sessions
            if len(session) >= 4 and session[3] == today
        )
        today_hours = round(total_minutes / 60, 1)

        streak_summary = self.database.get_study_streak_summary() if self.database else {"current_streak": 0, "longest_streak": 0, "last_active_date": None}
        streak = int(streak_summary.get("current_streak", 0) or 0)
        longest_streak = int(streak_summary.get("longest_streak", 0) or 0)
        streak_calendar = self.database.get_study_streak_calendar(today.year, today.month) if self.database else {
            "year": today.year,
            "month": today.month,
            "active_days": [],
            "current_streak": streak,
            "longest_streak": longest_streak,
            "days_in_month": 31,
            "first_weekday": 0,
        }

        recent_tasks = self.database.get_upcoming_tasks(limit=10) if self.database else []
        subjects = self.database.get_all_subjects() if self.database else []
        subject_stats = self.database.get_subject_statistics() if self.database else []
        achievements = self.database.get_all_achievements() if self.database else []
        self._seed_default_goals()
        goals = self.database.get_goals() if self.database else []
        goals = self._sync_goal_progress(goals, sessions, today)
        notifications = self.database.get_notifications(unread_only=True) if self.database else []
        reminders = self.reminder_manager.get_reminders(unread_only=True) if self.reminder_manager else []
        ai_history = self.database.get_ai_history(limit=5) if self.database else []
        analysis = analyze_study_performance(recent_tasks, sessions)
        metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}
        achievements = self._synchronize_achievements(metrics, achievements)
        self._seed_default_notifications()
        self._seed_default_ai_history()
        notifications = self.database.get_notifications(unread_only=True) if self.database else []
        reminders = self.reminder_manager.get_reminders(unread_only=True) if self.reminder_manager else []
        selected_type = self.reminder_filter.get() if hasattr(self, "reminder_filter") else "All"
        if selected_type and selected_type != "All":
            reminders = [r for r in reminders if r.reminder_type == selected_type]
        ai_history = self.database.get_ai_history(limit=5) if self.database else []
        leaderboard = self._build_local_leaderboard(metrics, streak, statistics)
        gamification_state = self.database.get_gamification_state() if self.database else None
        return (
            statistics,
            today_hours,
            streak,
            longest_streak,
            recent_tasks,
            subjects,
            analysis,
            subject_stats,
            sessions,
            achievements,
            goals,
            notifications,
            reminders,
            ai_history,
            leaderboard,
            streak_calendar,
            gamification_state,
        )

    def _apply_dashboard_statistics(self, payload):
        if not payload:
            return
        self._dashboard_payload = payload
        (
            statistics,
            today_hours,
            streak,
            longest_streak,
            recent_tasks,
            subjects,
            analysis,
            subject_stats,
            sessions,
            achievements,
            goals,
            notifications,
            reminders,
            ai_history,
            leaderboard,
            streak_calendar,
            gamification_state,
        ) = payload
        self._dashboard_tasks = recent_tasks
        self._dashboard_subjects = subjects
        self._dashboard_sessions = sessions
        self._dashboard_subject_stats = subject_stats
        self._dashboard_achievements = achievements
        try:
            self.dashboard_loading_label.configure(text="")
            self.total_subjects_card.update_value(f"{today_hours}h")
            self.total_tasks_card.update_value(len(recent_tasks))
            self.completed_card.update_value(statistics["completed_tasks"])
            self.pending_card.update_value(len([task for task in recent_tasks if task and task[6] != "Completed"]))
            self.study_hours_card.update_value(f"{statistics['completion_rate']}%")
            self.streak_card.update_value(f"{streak} day(s)")
            badge_count = 0
            if gamification_state:
                badge_count = len([badge for badge in gamification_state.get("badges", []) if badge.get("unlocked")])
            self.badges_card.update_value(badge_count)
            self.progress_level_card.update_value(self._determine_progress_level(analysis.get("metrics", {}) if isinstance(analysis, dict) else {}))
            completion_rate = statistics["completion_rate"]
            self.progress_bar.set(completion_rate / 100)
            self.progress_label.configure(text=f"{completion_rate}% completed")
            for widget in self.insight_frame.winfo_children():
                widget.destroy()
            ctk.CTkLabel(
                self.insight_frame,
                text=(f"🔥 Current streak: {streak} day(s) • Longest streak: {longest_streak} day(s) • Today: {today_hours}h"),
                font=("Arial", 13)
            ).pack(anchor="w")
            self.render_streak_calendar(streak_calendar)
            self.render_subject_chart(subject_stats)
            self._render_recent_tasks(recent_tasks)
            self._render_subjects(subjects)
            self._render_upcoming_exams(recent_tasks)
            self._render_goal_progress(goals, today_hours)
            self._render_notifications(notifications)
            self._render_reminders(reminders)
            self._render_leaderboard(leaderboard)
            self._render_ai_history(ai_history)
            self._update_gamification(statistics, recent_tasks, sessions, streak, analysis, achievements=achievements)
            # Update level UI from gamification profile
            try:
                if gamification_state:
                    level = int(gamification_state.get("level", 1) or 1)
                    current_xp = int(gamification_state.get("current_level_xp", 0) or 0)
                    target = int(gamification_state.get("current_level_target", 100) or 100)
                    self.level_card.update_value(f"Lv {level}")
                    progress_ratio = (current_xp / target) if target > 0 else 0
                    self.level_card.set_progress(progress_ratio)

                    if hasattr(self, "welcome_level_button"):
                        self.welcome_level_button.configure(text=f"Lv {level}")

                    if hasattr(self, "welcome_level_progress"):
                        try:
                            animate_progress(self.welcome_level_progress, progress_ratio)
                        except Exception:
                            try:
                                self.welcome_level_progress.set(progress_ratio)
                            except Exception:
                                pass
            except Exception:
                pass
        except Exception:
            pass

    def _open_gamification_modal(self):
        """Open a small modal showing detailed gamification stats and achievements."""
        try:
            state = self.database.get_gamification_state() if self.database else None
        except Exception:
            state = None

        modal = ctk.CTkToplevel(self)
        modal.title("Gamification")
        modal.geometry("420x480")
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=16, pady=16)

        title_lbl = self.design.create_label(container, text="Your Progress", size="xl", weight="bold")
        title_lbl.pack(anchor="w", pady=(0, 8))

        total_xp = state.get("total_xp") if state else 0
        coins = state.get("coins") if state else 0
        level = state.get("level") if state else 1
        current_xp = state.get("current_level_xp") if state else 0
        target = state.get("current_level_target") if state else 100

        self.design.create_label(container, text=f"Level: {level}", size="lg", weight="bold").pack(anchor="w", pady=(6, 2))
        lvl_progress = ctk.CTkProgressBar(container, height=8, fg_color="#e2e8f0", progress_color="#f59e0b")
        lvl_progress.pack(fill="x", pady=(0, 6))
        try:
            lvl_progress.set((int(current_xp or 0) / int(target or 100)) if target else 0)
        except Exception:
            lvl_progress.set(0)

        self.design.create_label(container, text=f"XP: {total_xp} (Level: {current_xp}/{target})", size="sm", text_color=self.design.get_color("text_secondary")).pack(anchor="w", pady=(0, 8))
        self.design.create_label(container, text=f"Coins: {coins}", size="sm", text_color=self.design.get_color("text_secondary")).pack(anchor="w", pady=(0, 12))

        self.design.create_label(container, text="Badge Rewards", size="lg", weight="bold").pack(anchor="w", pady=(8, 6))
        badge_text = (
            "100 XP → Bronze Badge\n"
            "500 XP → Silver Badge\n"
            "1000 XP → Gold Badge\n"
            "30-Day streak → 30-Day Streak Champion"
        )
        self.design.create_label(container, text=badge_text, size="sm", text_color=self.design.get_color("text_secondary"), wraplength=380, justify="left").pack(anchor="w", pady=(0, 10))

        current_badge_label = state.get("badge_label") if state else None
        self.design.create_label(container, text=f"Current Badge: {current_badge_label or 'None'}", size="sm", weight="bold").pack(anchor="w", pady=(0, 12))

        self.design.create_label(container, text="Badges", size="lg", weight="bold").pack(anchor="w", pady=(8, 6))
        badges = state.get("badges", []) if state else []
        badge_frame = ctk.CTkScrollableFrame(container, corner_radius=8, height=180, fg_color=self.design.get_color("surface"))
        badge_frame.pack(fill="both", expand=True, pady=(0, 8))
        for badge in badges:
            row = ctk.CTkFrame(badge_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=6)
            self.design.create_label(row, text=badge["title"], size="sm", weight="bold").pack(side="left")
            self.design.create_label(row, text=("Unlocked" if badge["unlocked"] else "Locked"), size="sm", text_color="#22c55e" if badge["unlocked"] else self.design.get_color("text_secondary")).pack(side="right")

        self.design.create_label(container, text="Achievements", size="lg", weight="bold").pack(anchor="w", pady=(8, 6))
        achievements = self.database.get_all_achievements() if self.database else []
        ach_frame = ctk.CTkScrollableFrame(container, corner_radius=8, height=220, fg_color=self.design.get_color("surface"))
        ach_frame.pack(fill="both", expand=True, pady=(0, 8))
        for ach in achievements:
            unlocked = bool(ach[3])
            row = ctk.CTkFrame(ach_frame, fg_color="transparent")
            row.pack(fill="x", padx=8, pady=6)
            self.design.create_label(row, text=ach[1], size="sm", weight="bold").pack(side="left")
            self.design.create_label(row, text=("Unlocked" if unlocked else "Locked"), size="sm", text_color="#22c55e" if unlocked else self.design.get_color("text_secondary")).pack(side="right")

        btn = ctk.CTkButton(container, text="Close", command=modal.destroy)
        btn.pack(anchor="e", pady=(8, 0))
        

    def _seed_default_goals(self):
        if not self.database:
            return

        daily_goals = self.database.get_goals(goal_type="daily")
        weekly_goals = self.database.get_goals(goal_type="weekly")
        today = date.today().isoformat()
        week_end = (date.today() + timedelta(days=6)).isoformat()
        daily_goal_hours = 2
        try:
            daily_goal_hours = int(self.settings_manager.get_setting("daily_goal_hours") or 2)
        except Exception:
            daily_goal_hours = 2

        if not daily_goals:
            self.database.add_goal(
                "daily",
                max(1, daily_goal_hours) * 60,
                0,
                period_start=today,
                period_end=today,
            )
        if not weekly_goals:
            self.database.add_goal(
                "weekly",
                420,
                0,
                period_start=today,
                period_end=week_end,
            )

    def _seed_default_notifications(self):
        if not self.database:
            return
        existing_notifications = self.database.get_notifications(unread_only=False)
        if existing_notifications:
            return
        self.database.add_notification(
            "Daily Study Momentum",
            "Consistency is your strongest advantage. Keep your streak alive.",
            is_read=0,
        )
        self.database.add_notification(
            "Smart Goal Reminder",
            "Your daily goal is ready to be completed with a focused session.",
            is_read=0,
        )

    def _seed_default_ai_history(self):
        if not self.database:
            return
        existing_history = self.database.get_ai_history(limit=1)
        if existing_history:
            return
        self.database.add_ai_history(
            "How can I improve my focus today?",
            "Review your recent task completion and maintain a short, distraction-free session.",
        )

    def _sync_goal_progress(self, goals, sessions, today_string):
        if not self.database or not goals:
            return goals or []

        session_minutes_by_day = {}
        for session in sessions:
            if not session or len(session) < 4:
                continue
            session_date = session[3]
            if not session_date:
                continue
            try:
                parsed_date = datetime.strptime(str(session_date), "%Y-%m-%d").date()
            except ValueError:
                try:
                    parsed_date = datetime.strptime(str(session_date), "%Y-%m-%d %H:%M:%S").date()
                except ValueError:
                    continue
            session_minutes_by_day[parsed_date.isoformat()] = session_minutes_by_day.get(parsed_date.isoformat(), 0) + int(session[2] or 0)

        synced_goals = []
        for goal in goals:
            goal_id, goal_type, target_minutes, current_minutes, period_start, period_end, completed, created_at = goal
            if goal_type == "daily":
                current_minutes = int(session_minutes_by_day.get(today_string, 0))
            elif goal_type == "weekly":
                current_minutes = 0
                period_start_date = datetime.strptime(str(period_start), "%Y-%m-%d").date() if period_start else date.today()
                period_end_date = datetime.strptime(str(period_end), "%Y-%m-%d").date() if period_end else date.today() + timedelta(days=6)
                delta_days = (period_end_date - period_start_date).days
                for offset in range(delta_days + 1):
                    day = period_start_date + timedelta(days=offset)
                    current_minutes += int(session_minutes_by_day.get(day.isoformat(), 0))
            completed = 1 if current_minutes >= int(target_minutes or 0) else 0
            self.database.update_goal_progress(goal_id, current_minutes, completed=completed)
            synced_goals.append((goal_id, goal_type, target_minutes, current_minutes, period_start, period_end, completed, created_at))

        return synced_goals

    def _build_local_leaderboard(self, metrics, streak, statistics):
        xp_score = int(metrics.get("productivity_score", 0))
        total_minutes = int(statistics.get("study_hours", 0) * 60)
        score = xp_score + (streak * 15) + (total_minutes // 10)
        return [
            {
                "name": self.user_data[1] if self.user_data else "You",
                "score": score,
                "level": self._determine_progress_level(metrics),
                "streak": streak,
            }
        ]

    def _render_goal_progress(self, goals, today_hours):
        for widget in self.goals_frame.winfo_children():
            widget.destroy()
        self.design.create_label(
            self.goals_frame,
            text="🎯 Study Goal Progress",
            size="lg",
            weight="bold"
        ).pack(anchor="w", padx=15, pady=(15, 8))
        if not goals:
            self.design.create_label(
                self.goals_frame,
                text="No study goals have been set yet.",
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", padx=15, pady=(0, 15))
            ctk.CTkButton(
                self.goals_frame,
                text="Set Daily Goal",
                width=140,
                command=self._open_add_daily_goal_modal,
            ).pack(anchor="w", padx=15, pady=(0, 15))
            return

        for goal in goals[:2]:
            goal_id, goal_type, target_minutes, current_minutes, period_start, period_end, completed, created_at = goal
            progress = min(1.0, current_minutes / max(1, target_minutes))
            current_hours = round(current_minutes / 60, 1)
            target_hours = round(target_minutes / 60, 1)
            goal_frame = ctk.CTkFrame(self.goals_frame, fg_color="transparent")
            goal_frame.pack(fill="x", padx=15, pady=6)
            heading_row = ctk.CTkFrame(goal_frame, fg_color="transparent")
            heading_row.pack(fill="x")
            self.design.create_label(
                heading_row,
                text=f"{goal_type.title()} Study Goal",
                size="base",
                weight="bold"
            ).pack(side="left")
            ctk.CTkButton(
                heading_row,
                text="Edit",
                width=80,
                command=lambda goal_id=goal_id, goal_type=goal_type, target_minutes=target_minutes: self._open_edit_goal_modal(goal_id, goal_type, target_minutes),
            ).pack(side="right")
            bar = ctk.CTkProgressBar(
                goal_frame,
                orientation="horizontal",
                width=260,
                height=8,
                progress_color=self.design.get_color("primary")
            )
            bar.pack(fill="x", padx=(0, 0), pady=(6, 0))
            bar.set(progress)
            label_text = (
                f"{current_hours} / {target_hours} Hours Completed"
                if goal_type == "weekly"
                else f"{current_hours} / {target_hours} Hours Today"
            )
            remaining_minutes = max(0, int(target_minutes) - int(current_minutes))
            remaining_hours = round(remaining_minutes / 60, 1)
            remaining_text = "Goal completed" if remaining_minutes == 0 else f"Remaining: {remaining_hours}h"
            self.design.create_label(
                goal_frame,
                text=label_text,
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", pady=(6, 0))
            self.design.create_label(
                goal_frame,
                text=remaining_text,
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", pady=(2, 0))
            self.design.create_label(
                goal_frame,
                text=f"{int(progress * 100)}% complete",
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", pady=(2, 8))

    def _open_add_daily_goal_modal(self):
        self._open_goal_modal(goal_id=None, goal_type="daily", target_minutes=0)

    def _open_edit_goal_modal(self, goal_id, goal_type, target_minutes):
        self._open_goal_modal(goal_id=goal_id, goal_type=goal_type, target_minutes=target_minutes)

    def _open_goal_modal(self, goal_id=None, goal_type="weekly", target_minutes=0):
        modal = ctk.CTkToplevel(self)
        modal.title("Set Study Goal")
        modal.geometry("380x240")
        modal.transient(self)
        modal.grab_set()

        content = ctk.CTkFrame(modal, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        self.design.create_label(content, text="Study Goal", size="xl", weight="bold").pack(anchor="w", pady=(0, 12))
        goal_description = "Daily study targets keep you motivated." if goal_type == "daily" else "Weekly study targets keep you motivated."
        self.design.create_label(content, text=goal_description, size="sm", text_color=self.design.get_color("text_secondary")).pack(anchor="w", pady=(0, 10))

        ctk.CTkLabel(content, text="Target hours").pack(anchor="w", pady=(10, 4))
        target_var = tk.StringVar(value=str(int(target_minutes / 60)))
        target_entry = ctk.CTkEntry(content, width=120, textvariable=target_var)
        target_entry.pack(anchor="w")

        def save_goal():
            try:
                hours = max(0, int(target_var.get()))
            except ValueError:
                messagebox.showwarning("Invalid goal", "Please enter a valid number of hours.")
                return
            if hours <= 0:
                messagebox.showwarning("Invalid goal", "Please set a goal greater than zero hours.")
                return
            minutes = hours * 60
            if not self.database:
                return
            today = date.today().isoformat()
            week_end = (date.today() + timedelta(days=6)).isoformat()
            if goal_id is None:
                period_end = week_end if goal_type == "weekly" else today
                self.database.add_goal(goal_type, minutes, 0, period_start=today, period_end=period_end)
            else:
                period_end = week_end if goal_type == "weekly" else today
                self.database.add_goal(goal_type, minutes, 0, period_start=today, period_end=period_end)
            modal.destroy()
            self.load_dashboard_data()

        button_frame = ctk.CTkFrame(content, fg_color="transparent")
        button_frame.pack(fill="x", pady=(20, 0))
        ctk.CTkButton(button_frame, text="Save Goal", width=120, command=save_goal).pack(side="left")
        ctk.CTkButton(button_frame, text="Cancel", width=120, command=modal.destroy).pack(side="right")

    def _render_notifications(self, notifications):
        for widget in self.notification_content_frame.winfo_children():
            widget.destroy()
        self.design.create_label(
            self.notification_content_frame,
            text="🧭 Recent Activity",
            size="lg",
            weight="bold"
        ).pack(anchor="w", pady=(0, 8))
        if not notifications:
            self.design.create_label(
                self.notifications_frame,
                text="No recent activity yet.",
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", padx=15, pady=(0, 15))
            return
        for notification in notifications[:3]:
            notification_frame = ctk.CTkFrame(self.notifications_frame, fg_color="transparent")
            notification_frame.pack(fill="x", padx=15, pady=5)
            self.design.create_label(
                notification_frame,
                text=notification[1],
                size="base",
                weight="bold"
            ).pack(anchor="w")
            self.design.create_label(
                notification_frame,
                text=notification[2],
                size="sm",
                text_color=self.design.get_color("text_secondary"),
                wraplength=620,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))

    def _mark_reminder_done(self, reminder_id):
        if self.reminder_manager.mark_reminder_done(reminder_id):
            self.load_dashboard_data()

    def _open_add_reminder_modal(self):
        self._open_reminder_modal()

    def _open_edit_reminder_modal(self, reminder):
        self._open_reminder_modal(reminder)

    def _open_reminder_modal(self, reminder=None):
        modal = ctk.CTkToplevel(self)
        modal.title("Add Reminder" if reminder is None else "Edit Reminder")
        modal.geometry("480x420")
        modal.transient(self)
        modal.grab_set()

        container = ctk.CTkFrame(modal, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=20, pady=20)

        self.design.create_label(
            container,
            text="Reminder Details",
            size="xl",
            weight="bold"
        ).pack(anchor="w", pady=(0, 15))

        title_label = self.design.create_label(container, text="Title", size="sm", weight="bold")
        title_label.pack(anchor="w", pady=(0, 4))
        title_entry = ctk.CTkEntry(container, width=420)
        title_entry.pack(fill="x", pady=(0, 10))

        message_label = self.design.create_label(container, text="Message", size="sm", weight="bold")
        message_label.pack(anchor="w", pady=(0, 4))
        message_entry = ctk.CTkTextbox(container, width=420, height=100)
        message_entry.pack(fill="x", pady=(0, 10))

        type_label = self.design.create_label(container, text="Reminder Type", size="sm", weight="bold")
        type_label.pack(anchor="w", pady=(0, 4))
        type_combobox = ctk.CTkComboBox(container, width=240, values=REMINDER_TYPES)
        type_combobox.pack(anchor="w", pady=(0, 10))

        due_label = self.design.create_label(container, text="Due Date (YYYY-MM-DD)", size="sm", weight="bold")
        due_label.pack(anchor="w", pady=(0, 4))
        due_entry = ctk.CTkEntry(container, width=240)
        due_entry.pack(anchor="w", pady=(0, 10))

        repeat_label = self.design.create_label(container, text="Repeat", size="sm", weight="bold")
        repeat_label.pack(anchor="w", pady=(0, 4))
        repeat_combobox = ctk.CTkComboBox(container, width=240, values=REPEAT_OPTIONS)
        repeat_combobox.pack(anchor="w", pady=(0, 20))

        if reminder is not None:
            title_entry.insert(0, reminder.title)
            message_entry.insert("1.0", reminder.message)
            type_combobox.set(reminder.reminder_type)
            due_entry.insert(0, reminder.due_at)
            repeat_combobox.set(reminder.repeat)
        else:
            type_combobox.set(REMINDER_TYPES[0])
            repeat_combobox.set(REPEAT_OPTIONS[0])

        def save_callback():
            try:
                title = title_entry.get().strip()
                message = message_entry.get("1.0", "end").strip()
                reminder_type = type_combobox.get() or REMINDER_TYPES[0]
                due_at = due_entry.get().strip()
                repeat = repeat_combobox.get() or REPEAT_OPTIONS[0]

                if not title or not message or not due_at:
                    raise ValueError("Title, message, and due date are required.")
                datetime.strptime(due_at, "%Y-%m-%d")

                reminder_obj = Reminder(
                    reminder_id=reminder.id if reminder else None,
                    title=title,
                    message=message,
                    reminder_type=reminder_type,
                    due_at=due_at,
                    repeat=repeat,
                )
                if reminder is None:
                    self.reminder_manager.add_reminder(reminder_obj)
                else:
                    self.reminder_manager.update_reminder(reminder_obj)
                modal.destroy()
                self.load_dashboard_data()
            except Exception as exc:
                messagebox.showerror("Invalid Reminder", str(exc), parent=modal)

        button_frame = ctk.CTkFrame(container, fg_color="transparent")
        button_frame.pack(fill="x", pady=(0, 10))

        ctk.CTkButton(button_frame, text="Save", width=120, command=save_callback).pack(side="left")
        ctk.CTkButton(button_frame, text="Cancel", width=120, fg_color="#d9534f", hover_color="#c9302c", command=modal.destroy).pack(side="left", padx=(10, 0))

    def _render_reminders(self, reminders):
        for widget in self.notification_content_frame.winfo_children():
            widget.destroy()
        self.design.create_label(
            self.notification_content_frame,
            text="⏰ Upcoming Reminders",
            size="lg",
            weight="bold"
        ).pack(anchor="w", pady=(12, 8))
        if not reminders:
            self.design.create_label(
                self.notification_content_frame,
                text="No reminders scheduled.",
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", padx=15, pady=(0, 15))
            return
        for reminder in reminders[:3]:
            reminder_frame = ctk.CTkFrame(self.notification_content_frame, fg_color="transparent")
            reminder_frame.pack(fill="x", padx=15, pady=5)
            self.design.create_label(
                reminder_frame,
                text=f"{reminder.reminder_type} • {reminder.title}",
                size="base",
                weight="bold"
            ).pack(anchor="w")
            self.design.create_label(
                reminder_frame,
                text=f"{reminder.message}",
                size="sm",
                text_color=self.design.get_color("text_secondary"),
                wraplength=620,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))
            self.design.create_label(
                reminder_frame,
                text=f"Due: {reminder.due_at} • Repeat: {reminder.repeat}",
                size="xs",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", pady=(2, 0))
            button_frame = ctk.CTkFrame(reminder_frame, fg_color="transparent")
            button_frame.pack(fill="x", pady=(8, 0))
            ctk.CTkButton(
                button_frame,
                text="Mark Done",
                width=100,
                command=lambda rid=reminder.id: self._mark_reminder_done(rid),
            ).pack(side="left", padx=(0, 5))
            ctk.CTkButton(
                button_frame,
                text="Edit",
                width=100,
                command=lambda rem=reminder: self._open_edit_reminder_modal(rem),
            ).pack(side="left")

    def _render_leaderboard(self, leaderboard):
        for widget in self.leaderboard_frame.winfo_children():
            widget.destroy()
        ctk.CTkLabel(
            self.leaderboard_frame,
            text="✨ AI Suggestions",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 8))
        if not leaderboard:
            ctk.CTkLabel(self.leaderboard_frame, text="Suggestions unavailable.", font=("Arial", 12), text_color="#94a3b8").pack(anchor="w", padx=15, pady=(0, 15))
            return
        for idx, entry in enumerate(leaderboard[:3], start=1):
            row = ctk.CTkFrame(self.leaderboard_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            ctk.CTkLabel(row, text=f"#{idx} {entry['name']}", font=("Arial", 12, "bold")).pack(side="left")
            ctk.CTkLabel(row, text=f"{entry['score']} XP • {entry['level']}", font=("Arial", 11)).pack(side="right")

    def _render_ai_history(self, ai_history):
        for widget in self.ai_history_frame.winfo_children():
            widget.destroy()
        self.design.create_label(
            self.ai_history_frame,
            text="🤖 AI Suggestions",
            size="lg",
            weight="bold"
        ).pack(anchor="w", padx=15, pady=(15, 8))
        if not ai_history:
            self.design.create_label(
                self.ai_history_frame,
                text="No AI interactions yet.",
                size="sm",
                text_color=self.design.get_color("text_secondary")
            ).pack(anchor="w", padx=15, pady=(0, 15))
            return
        for history_row in ai_history[:3]:
            row = ctk.CTkFrame(self.ai_history_frame, fg_color="transparent")
            row.pack(fill="x", padx=15, pady=5)
            self.design.create_label(
                row,
                text=history_row[1],
                size="base",
                weight="bold",
                wraplength=620,
                justify="left"
            ).pack(anchor="w")
            self.design.create_label(
                row,
                text=history_row[2],
                size="sm",
                text_color=self.design.get_color("text_secondary"),
                wraplength=620,
                justify="left"
            ).pack(anchor="w", pady=(2, 0))

    def _seed_default_achievements(self):
        achievements = self.database.get_all_achievements() if self.database else []
        if achievements:
            return

        default_achievements = [
            ("First Study Session", "Log your first study session."),
            ("Task Starter", "Complete your first task."),
            ("3-Day Streak", "Maintain a 3-day study streak."),
            ("7-Day Streak", "Maintain a 7-day study streak."),
            ("Completion Champion", "Complete 80% or more of your tasks."),
            ("Productivity Pro", "Reach a productivity score of 80 or higher."),
        ]
        for title, description in default_achievements:
            self.database.add_achievement(title, description, unlocked=0)

    def _unlock_achievement_if_needed(self, metrics, achievements, title, condition):
        existing = next((row for row in achievements if row[1] == title), None)
        if existing and not bool(existing[3]) and condition:
            self.database.unlock_achievement(existing[0])

    def _synchronize_achievements(self, metrics, achievements=None):
        self._seed_default_achievements()
        achievements = achievements if achievements is not None else (self.database.get_all_achievements() if self.database else [])
        self._unlock_achievement_if_needed(metrics, achievements, "First Study Session", metrics.get("total_study_minutes", 0) >= 25)
        self._unlock_achievement_if_needed(metrics, achievements, "Task Starter", metrics.get("completed_tasks", 0) >= 1)
        self._unlock_achievement_if_needed(metrics, achievements, "3-Day Streak", metrics.get("study_streak", 0) >= 3)
        self._unlock_achievement_if_needed(metrics, achievements, "7-Day Streak", metrics.get("study_streak", 0) >= 7)
        self._unlock_achievement_if_needed(metrics, achievements, "Completion Champion", metrics.get("completion_rate", 0) >= 80)
        self._unlock_achievement_if_needed(metrics, achievements, "Productivity Pro", metrics.get("productivity_score", 0) >= 80)
        return self.database.get_all_achievements() if self.database else achievements

    def _determine_progress_level(self, metrics):
        score = metrics.get("productivity_score", 0)
        if score >= 90:
            return "Platinum"
        if score >= 70:
            return "Gold"
        if score >= 50:
            return "Silver"
        return "Bronze"

    def _render_badge_list(self, badges):
        ctk.CTkLabel(
            self.achievements_frame,
            text="Badges",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 8))

        if not badges:
            ctk.CTkLabel(
                self.achievements_frame,
                text="No badges available yet.",
                font=("Arial", 12),
                text_color="#94a3b8"
            ).pack(anchor="w", padx=15, pady=(0, 15))
        else:
            for badge in badges:
                unlocked = bool(badge.get("unlocked"))
                badge_frame = ctk.CTkFrame(
                    self.achievements_frame,
                    fg_color="#0f172a",
                    border_width=1,
                    border_color="#334155",
                    corner_radius=12,
                )
                badge_frame.pack(fill="x", padx=15, pady=6)

                ctk.CTkLabel(
                    badge_frame,
                    text=badge.get("title", ""),
                    font=("Arial", 13, "bold")
                ).pack(anchor="w", padx=12, pady=(10, 0))

                ctk.CTkLabel(
                    badge_frame,
                    text=badge.get("description", ""),
                    font=("Arial", 11),
                    wraplength=620,
                    justify="left"
                ).pack(anchor="w", padx=12, pady=(4, 8))

                ctk.CTkLabel(
                    badge_frame,
                    text="Unlocked" if unlocked else "Locked",
                    text_color="#22c55e" if unlocked else "#94a3b8",
                    font=("Arial", 11, "italic")
                ).pack(anchor="w", padx=12, pady=(0, 10))

    def _render_achievement_list(self, achievements):
        ctk.CTkLabel(
            self.achievements_frame,
            text="Achievements",
            font=("Arial", 16, "bold")
        ).pack(anchor="w", padx=15, pady=(15, 8))

        if not achievements:
            ctk.CTkLabel(
                self.achievements_frame,
                text="No achievements available yet.",
                font=("Arial", 12),
                text_color="#94a3b8"
            ).pack(anchor="w", padx=15, pady=(0, 15))
            return

        for row in achievements:
            unlocked = bool(row[3])
            achievement_frame = ctk.CTkFrame(
                self.achievements_frame,
                fg_color="#0f172a",
                border_width=1,
                border_color="#334155",
                corner_radius=12,
            )
            achievement_frame.pack(fill="x", padx=15, pady=6)

            ctk.CTkLabel(
                achievement_frame,
                text=row[1],
                font=("Arial", 13, "bold")
            ).pack(anchor="w", padx=12, pady=(10, 0))

            ctk.CTkLabel(
                achievement_frame,
                text=row[2],
                font=("Arial", 11),
                wraplength=620,
                justify="left"
            ).pack(anchor="w", padx=12, pady=(4, 8))

            ctk.CTkLabel(
                achievement_frame,
                text="Unlocked" if unlocked else "Locked",
                text_color="#22c55e" if unlocked else "#94a3b8",
                font=("Arial", 11, "italic")
            ).pack(anchor="w", padx=12, pady=(0, 10))

    def _update_gamification(self, statistics, tasks, sessions, streak, analysis, achievements=None):
        metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}
        achievements = self._synchronize_achievements(metrics, achievements)
        gamification_state = self.database.get_gamification_state() if self.database else {}
        badges = gamification_state.get("badges", [])
        badge_count = len([badge for badge in badges if badge.get("unlocked")])
        self.badges_card.update_value(str(badge_count))
        self.progress_level_card.update_value(self._determine_progress_level(metrics))
        self._render_badge_list(badges)
        self._render_achievement_list(achievements)

    def _render_recent_tasks(self, tasks):
        for widget in self.tasks_scrollable.winfo_children():
            widget.destroy()
        if not tasks:
            ctk.CTkLabel(self.tasks_scrollable, text="No tasks available.").pack(pady=30)
            return
        for task in tasks[:10]:
            self.create_task_row(task)

    def _render_upcoming_exams(self, tasks):
        for widget in self.exam_scrollable.winfo_children():
            widget.destroy()
        if not tasks:
            ctk.CTkLabel(self.exam_scrollable, text="No upcoming exams or deadlines.").pack(pady=30)
            return
        for task in tasks[:8]:
            self.create_exam_row(task)

    def _render_subjects(self, subjects):
        for widget in self.subject_scrollable.winfo_children():
            widget.destroy()
        if not subjects:
            ctk.CTkLabel(self.subject_scrollable, text="No subjects available.").pack(pady=30)
            return
        for subject in subjects:
            self.create_subject_row(subject)

    def _show_dashboard_error(self, error, safe_message=None):
        friendly_message = safe_message or handle_operation_error(
            error,
            context="loading dashboard",
            user_message="We couldn't refresh the dashboard right now.",
        )
        self.dashboard_loading_label.configure(text=friendly_message)


    # ======================================================
    # LOAD RECENT TASKS
    # ======================================================

    def load_recent_tasks(self):

        for widget in (

            self.tasks_scrollable
            .winfo_children()

        ):

            widget.destroy()


        if getattr(self, "_dashboard_payload", None) is not None:
            tasks = self._dashboard_payload[3]
        elif getattr(self, "_dashboard_tasks", None) is not None:
            tasks = self._dashboard_tasks
        else:
            self._dashboard_tasks = self.database.get_upcoming_tasks(limit=10)
            tasks = self._dashboard_tasks

        if not tasks:

            ctk.CTkLabel(

                self.tasks_scrollable,

                text="No tasks available."

            ).pack(

                pady=30

            )

            return


        for task in tasks[:10]:

            self.create_task_row(

                task

            )


    def create_task_row(

        self,

        task

    ):

        task_frame = self.design.create_card(self.tasks_scrollable, fg_color=self.design.theme["surface"], border_color="#E2E8F0")
        task_frame.pack(fill="x", padx=10, pady=8)


        # Database task format:
        #
        # id
        # subject
        # title
        # description
        # priority
        # deadline
        # status

        task_id = task[0]

        subject = task[1]

        title = task[2]

        priority = task[4]

        deadline = task[5]

        status = task[6]


        ctk.CTkLabel(

            task_frame,

            text=title,

            font=(

                "Arial",

                14,

                "bold"

            ),

            anchor="w"

        ).pack(

            anchor="w",

            padx=15,

            pady=(10, 2)

        )


        ctk.CTkLabel(

            task_frame,

            text=(

                f"{subject} | "

                f"Priority: {priority} | "

                f"Deadline: {deadline}"

            ),

            anchor="w"

        ).pack(

            anchor="w",

            padx=15,

            pady=2

        )


        ctk.CTkLabel(

            task_frame,

            text=(

                f"Status: {status}"

            )

        ).pack(

            anchor="w",

            padx=15,

            pady=(2, 10)

        )


    # ======================================================
    # LOAD SUBJECTS
    # ======================================================

    def load_subjects(self):

        for widget in (

            self.subject_scrollable
            .winfo_children()

        ):

            widget.destroy()


        subjects = (

            self.database
            .get_all_subjects()

        )


        if not subjects:

            ctk.CTkLabel(

                self.subject_scrollable,

                text="No subjects available."

            ).pack(

                pady=30

            )

            return


        for subject in subjects:

            self.create_subject_row(

                subject

            )


    def create_subject_row(

        self,

        subject

    ):

        subject_frame = self.design.create_card(self.subject_scrollable, fg_color=self.design.theme["surface"], border_color="#E2E8F0")
        subject_frame.pack(fill="x", padx=10, pady=8)


        subject_id = subject[0]

        name = subject[1]

        color = subject[2]


        ctk.CTkLabel(

            subject_frame,

            text="●",

            text_color=color,

            font=(

                "Arial",

                24

            )

        ).pack(

            side="left",

            padx=(15, 5),

            pady=10

        )


        ctk.CTkLabel(

            subject_frame,

            text=name,

            font=(

                "Arial",

                14,

                "bold"

            )

        ).pack(

            side="left",

            padx=5,

            pady=10

        )


    # ======================================================
    # NAVIGATION METHODS
    # ======================================================

    def clear_main_frame(self):
        if not hasattr(self, "page_container") or self.page_container is None:
            return

        for widget in list(self.page_container.winfo_children()):
            if widget is getattr(self, "dashboard_view_frame", None):
                widget.grid()
                continue
            try:
                widget.grid_remove()
            except Exception:
                pass

    def _switch_to_frame(self, target_frame):
        if target_frame is None:
            return
        for widget in list(self.page_container.winfo_children()):
            try:
                if widget is target_frame:
                    widget.grid()
                    widget.tkraise()
                else:
                    if hasattr(widget, "destroy") and not getattr(widget, "_is_dashboard_frame", False):
                        try:
                            widget.grid_remove()
                        except Exception:
                            pass
            except Exception:
                pass
        if hasattr(target_frame, "on_show"):
            try:
                target_frame.on_show()
            except Exception:
                pass

    def _create_page_frame(self, page_name):
        if page_name == "search":
            return GlobalSearch(self.page_container, self.database)
        if page_name == "subjects":
            return SubjectWindow(self.page_container, self.database)
        if page_name == "tasks":
            return TaskWindow(self.page_container, self.database, settings_manager=self.settings_manager)
        if page_name == "timer":
            return TimerWindow(self.page_container, self.database)
        if page_name == "calendar":
            return CalendarWindow(self.page_container, self.database)
        if page_name == "analytics":
            return AnalyticsWindow(self.page_container, self.database, settings_manager=self.settings_manager)
        if page_name == "reports":
            return ReportWindow(self.page_container, self.database, settings_manager=self.settings_manager)
        if page_name == "ai_assistant":
            from ai_assistant import AIStudyAssistantPage
            return AIStudyAssistantPage(self.page_container, self.database)
        if page_name == "settings":
            return SettingsWindow(self.page_container, self.database, settings_manager=self.settings_manager)
        if page_name == "profile":
            # Pass the logged-in user id so the profile page can load user-specific data
            from profile import ProfileWindow
            return ProfileWindow(self.page_container, self.database, user_id=self.user_data[0])
        raise ValueError(page_name)

    def show_dashboard(self):
        self.sidebar.set_active_page("dashboard")
        if not hasattr(self, "dashboard_view_frame") or self.dashboard_view_frame is None:
            self.build_dashboard_view()
        self._switch_to_frame(self.dashboard_view_frame)
        if not getattr(self, "_dashboard_loaded", False):
            self._dashboard_loaded = True
            if getattr(self, "_defer_dashboard_load", False):
                self._defer_dashboard_load = False
                self.after(100, self.load_dashboard_data)
            else:
                self.load_dashboard_data()

    def show_page(self, page_name):
        self.sidebar.set_active_page(page_name)

        if page_name == "dashboard":
            self.show_dashboard()
            return

        try:
            if page_name not in self.page_frames:
                page = self._create_page_frame(page_name)
                page.grid(
                    row=0,
                    column=0,
                    sticky="nsew",
                    padx=8,
                    pady=8
                )
                self.page_frames[page_name] = page
            self._switch_to_frame(self.page_frames[page_name])
        except Exception as error:
            messagebox.showerror(
                "Unable to open module",
                f"{error}"
            )

    def open_subjects(self):

        self.show_page("subjects")

    def open_tasks(self):

        self.show_page("tasks")

    def open_timer(self):

        self.show_page("timer")

    def open_calendar(self):

        self.show_page("calendar")

    def open_analytics(self):

        self.show_page("analytics")

    def open_reports(self):

        self.show_page("reports")

    def open_settings(self):

        self.show_page("settings")


    # ======================================================
    # LOGOUT
    # ======================================================

    def logout(self):

        answer = messagebox.askyesno(

            "Logout",

            "Are you sure you want to logout?"

        )


        if answer:

            self.close_window()


    def close_window(self):
        try:
            self.reminder_manager.stop_scheduler()
        except Exception:
            pass

        self.destroy()

        self.parent.deiconify()