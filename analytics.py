import hashlib
import json

import customtkinter as ctk

from tkinter import messagebox

from datetime import datetime, timedelta

from database import DatabaseManager
from ai_service import analyze_study_performance, generate_study_recommendations
from task_manager import BackgroundTaskManager
from utils import run_in_background, set_loading_state, handle_operation_error


# ==========================================================
# MATPLOTLIB IMPORT
# ==========================================================

from matplotlib.figure import Figure

from matplotlib.backends.backend_tkagg import (

    FigureCanvasTkAgg

)


_ANALYTICS_REFRESH_CALLBACKS = []


def build_analytics_cache_signature(tasks, sessions, subject_stats=None, study_dates=None):
    payload = {
        "tasks": [list(task) for task in (tasks or [])],
        "sessions": [list(session) for session in (sessions or [])],
        "subject_stats": [list(item) for item in (subject_stats or [])],
        "study_dates": [str(value) for value in (study_dates or []) if value is not None],
    }
    serialized = json.dumps(payload, sort_keys=True, default=str)
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def should_refresh_analytics(force=False, previous_signature=None, current_signature=None):
    if force:
        return True
    if previous_signature is None:
        return True
    return previous_signature != current_signature


def register_analytics_refresh_callback(callback):
    if callback not in _ANALYTICS_REFRESH_CALLBACKS:
        _ANALYTICS_REFRESH_CALLBACKS.append(callback)
    return callback


def request_analytics_refresh():
    for callback in list(_ANALYTICS_REFRESH_CALLBACKS):
        try:
            callback()
        except Exception:
            continue


# ==========================================================
# ANALYTICS WINDOW
# ==========================================================

class AnalyticsWindow(ctk.CTkFrame):
    """
    Analytics Dashboard page.
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
        self.settings_manager = settings_manager

        self._analytics_signature = None
        self._analytics_loading = False
        self._cached_chart_payload = None
        self._task_manager = BackgroundTaskManager()
        self._refresh_callback = register_analytics_refresh_callback(self.handle_external_analytics_refresh)

        self.create_layout()
        self.apply_application_settings(self.settings_manager.get_all_settings() if self.settings_manager else None)

    def on_show(self):
        if not self._analytics_loading and self._analytics_signature is None:
            self.load_analytics(force=True)


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

        self.grid_rowconfigure(

            3,

            weight=1

        )

        self.grid_rowconfigure(

            4,

            weight=1

        )


        self.create_header()


        self.create_statistics()


        self.create_chart_area()

        self.create_ai_analysis_area()


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

            text="Study Analytics",

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

                "Analyze your study progress and performance."

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


        self.refresh_button = ctk.CTkButton(

            self.header_frame,

            text="Refresh",

            width=100,

            command=self.load_analytics

        )
        self.refresh_button.grid(

            row=0,

            column=1,

            rowspan=2,

            padx=10

        )


    # ======================================================
    # STATISTICS AREA
    # ======================================================

    def create_statistics(self):

        self.statistics_frame = ctk.CTkFrame(

            self

        )


        self.statistics_frame.grid(

            row=1,

            column=0,

            sticky="ew",

            padx=25,

            pady=10

        )


        for column in range(3):

            self.statistics_frame.grid_columnconfigure(

                column,

                weight=1

            )


        for row in range(4):

            self.statistics_frame.grid_rowconfigure(

                row,

                weight=1

            )


        self.total_study_card = self.create_stat_card(

            self.statistics_frame,

            "Total Study Time",

            "0 min"

        )

        self.total_study_card.grid(

            row=0,

            column=0,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.daily_study_card = self.create_stat_card(

            self.statistics_frame,

            "Today's Study Time",

            "0 min"

        )

        self.daily_study_card.grid(

            row=0,

            column=1,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.weekly_study_card = self.create_stat_card(

            self.statistics_frame,

            "Weekly Study Time",

            "0 min"

        )

        self.weekly_study_card.grid(

            row=0,

            column=2,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.monthly_study_card = self.create_stat_card(

            self.statistics_frame,

            "Monthly Study Time",

            "0 min"

        )

        self.monthly_study_card.grid(

            row=1,

            column=0,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.subject_study_card = self.create_stat_card(

            self.statistics_frame,

            "Top Subject",

            "None"

        )

        self.subject_study_card.grid(

            row=1,

            column=1,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.completed_task_card = self.create_stat_card(

            self.statistics_frame,

            "Completed Tasks",

            "0"

        )

        self.completed_task_card.grid(

            row=1,

            column=2,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.pending_task_card = self.create_stat_card(

            self.statistics_frame,

            "Pending Tasks",

            "0"

        )

        self.pending_task_card.grid(

            row=2,

            column=0,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.completion_rate_card = self.create_stat_card(

            self.statistics_frame,

            "Completion Rate",

            "0%"

        )

        self.completion_rate_card.grid(

            row=2,

            column=1,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.streak_card = self.create_stat_card(

            self.statistics_frame,

            "Study Streak",

            "0 days"

        )

        self.streak_card.grid(

            row=2,

            column=2,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.productivity_card = self.create_stat_card(

            self.statistics_frame,

            "Productivity Score",

            "0/100"

        )

        self.productivity_card.grid(

            row=3,

            column=0,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.weak_subject_card = self.create_stat_card(

            self.statistics_frame,

            "Weak Subject",

            "None"

        )

        self.weak_subject_card.grid(

            row=3,

            column=1,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.strong_subject_card = self.create_stat_card(

            self.statistics_frame,

            "Strong Subject",

            "None"

        )

        self.strong_subject_card.grid(

            row=3,

            column=2,

            sticky="ew",

            padx=8,

            pady=10

        )

        self.exam_prediction_card = self.create_stat_card(

            self.statistics_frame,

            "Exam Prediction",

            "N/A"

        )

        self.exam_prediction_card.grid(

            row=4,

            column=0,

            columnspan=3,

            sticky="ew",

            padx=8,

            pady=10

        )


    # ======================================================
    # CREATE STAT CARD
    # ======================================================

    def create_stat_card(

        self,

        parent,

        title,

        value

    ):

        card = ctk.CTkFrame(

            parent

        )


        ctk.CTkLabel(

            card,

            text=title,

            font=(

                "Arial",

                14

            )

        ).pack(

            pady=(15, 5)

        )


        value_label = ctk.CTkLabel(

            card,

            text=value,

            font=(

                "Arial",

                24,

                "bold"

            )

        )


        value_label.pack(

            pady=(5, 15)

        )


        card.value_label = value_label


        return card


    # ======================================================
    # AI ANALYSIS AREA
    # ======================================================

    def create_ai_analysis_area(self):
        self.ai_analysis_frame = ctk.CTkFrame(self)
        self.ai_analysis_frame.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=25,
            pady=(0, 20),
        )
        self.ai_analysis_frame.grid_columnconfigure(0, weight=1)
        self.ai_analysis_frame.grid_rowconfigure(1, weight=0)
        self.ai_analysis_frame.grid_rowconfigure(2, weight=1)

        ctk.CTkLabel(
            self.ai_analysis_frame,
            text="AI Study Analysis",
            font=("Arial", 18, "bold"),
        ).grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))

        self.subject_breakdown_frame = ctk.CTkFrame(self.ai_analysis_frame, fg_color="transparent")
        self.subject_breakdown_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=(0, 10))
        self.subject_breakdown_frame.grid_columnconfigure(0, weight=1)
        self.subject_breakdown_frame.grid_columnconfigure(1, weight=1)
        self.subject_breakdown_frame.grid_columnconfigure(2, weight=1)

        self.strong_subject_label = ctk.CTkLabel(
            self.subject_breakdown_frame,
            text="Strong Subject: No data",
            font=("Arial", 12, "bold"),
            anchor="w",
        )
        self.strong_subject_label.grid(row=0, column=0, sticky="w", padx=(0, 10))

        self.weak_subject_label = ctk.CTkLabel(
            self.subject_breakdown_frame,
            text="Weak Subject: No data",
            font=("Arial", 12, "bold"),
            anchor="w",
        )
        self.weak_subject_label.grid(row=0, column=1, sticky="w", padx=(0, 10))

        self.exam_outlook_label = ctk.CTkLabel(
            self.subject_breakdown_frame,
            text="Exam Readiness: No data",
            font=("Arial", 12, "bold"),
            anchor="w",
        )
        self.exam_outlook_label.grid(row=0, column=2, sticky="w")

        self.ai_analysis_textbox = ctk.CTkTextbox(
            self.ai_analysis_frame,
            height=180,
            font=("Arial", 12),
            wrap="word",
        )
        self.ai_analysis_textbox.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        self.ai_analysis_textbox.configure(state="disabled")

    def _configure_textbox_tab_size(self, textbox, tab_size):
        if textbox is None:
            return
        if not isinstance(tab_size, int):
            try:
                tab_size = int(tab_size)
            except Exception:
                tab_size = 4
        try:
            if hasattr(textbox, "_textbox"):
                textbox._textbox.configure(tabs=(f"{tab_size}c",))
        except Exception:
            pass

    def apply_application_settings(self, settings=None):
        if settings is None:
            settings = self.settings_manager.get_all_settings() if self.settings_manager else {}
        tab_size = 4
        if isinstance(settings, dict):
            try:
                tab_size = int(settings.get("tab_size", 4))
            except Exception:
                tab_size = 4
        self._configure_textbox_tab_size(self.ai_analysis_textbox, tab_size)

    # ======================================================
    # CHART AREA
    # ======================================================

    def create_chart_area(self):

        self.chart_frame = ctk.CTkScrollableFrame(

            self

        )


        self.chart_frame.grid(

            row=2,

            column=0,

            sticky="nsew",

            padx=25,

            pady=15

        )

        self.chart_frame.grid_columnconfigure(0, weight=1)
        self.chart_frame.grid_columnconfigure(1, weight=1)
        self.chart_frame.grid_rowconfigure(0, weight=1)
        self.chart_frame.grid_rowconfigure(1, weight=1)
        self.chart_frame.grid_rowconfigure(2, weight=1)

        self.study_chart_frame = ctk.CTkFrame(self.chart_frame)
        self.study_chart_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        self.weekly_chart_frame = ctk.CTkFrame(self.chart_frame)
        self.weekly_chart_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

        self.subject_chart_frame = ctk.CTkFrame(self.chart_frame)
        self.subject_chart_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        self.productivity_chart_frame = ctk.CTkFrame(self.chart_frame)
        self.productivity_chart_frame.grid(row=1, column=1, sticky="nsew", padx=10, pady=10)

        self.monthly_chart_frame = ctk.CTkFrame(self.chart_frame)
        self.monthly_chart_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=10)

        self.status_chart_frame = ctk.CTkFrame(self.chart_frame)
        self.status_chart_frame.grid(row=2, column=1, sticky="nsew", padx=10, pady=10)


    # ======================================================
    # LOAD ANALYTICS
    # ======================================================

    def load_analytics(self, force=False):
        if self._analytics_loading and not force:
            return

        if force or self._analytics_signature is None:
            self._set_loading_state()

        self._analytics_loading = True
        self._task_manager.submit_task(
            "analytics",
            target=self._load_analytics_data,
            callback=self._apply_analytics_data,
            error_callback=self._show_analytics_error,
            widget=self,
            force=force,
        )

    def handle_external_analytics_refresh(self):
        if getattr(self, "winfo_exists", None) and not self.winfo_exists():
            return
        self.load_analytics(force=False)

    def _set_loading_state(self):
        self.ai_analysis_textbox.configure(state="normal")
        self.ai_analysis_textbox.delete("1.0", "end")
        self.ai_analysis_textbox.insert("1.0", "AI is analyzing your study data...")
        self.ai_analysis_textbox.configure(state="disabled")
        if hasattr(self, "refresh_button"):
            set_loading_state(button_widget=self.refresh_button, text="Loading analytics...", loading=True)
        elif hasattr(self, "header_frame"):
            for child in self.header_frame.winfo_children():
                if getattr(child, "cget", None) and child.cget("text") == "Refresh":
                    set_loading_state(button_widget=child, text="Loading analytics...", loading=True)
                    break

    def _load_analytics_data(self, force=False):
        tasks = self.database.get_all_tasks() if self.database else []
        sessions = self.database.get_all_study_sessions() if self.database else []
        subject_stats = self.database.get_subject_statistics() if self.database else []
        study_dates = self.database.get_study_dates() if self.database else []
        stats_payload = self._build_statistics_payload(
            tasks,
            sessions,
            subject_stats=subject_stats,
            study_dates=study_dates,
        )
        chart_payload = self._build_chart_payload(sessions, tasks)
        analysis = analyze_study_performance(
            tasks,
            sessions,
            reference_date=datetime.now().date(),
        )
        analysis_text = generate_study_recommendations(
            tasks,
            sessions,
            reference_date=datetime.now().date(),
        )
        analysis_metrics = analysis.get("metrics", {}) if isinstance(analysis, dict) else {}
        signature = build_analytics_cache_signature(tasks, sessions, subject_stats, study_dates)
        return {
            "tasks": tasks,
            "sessions": sessions,
            "subject_stats": subject_stats,
            "study_dates": study_dates,
            "analysis": analysis,
            "analysis_text": analysis_text,
            "statistics": {
                **stats_payload,
                "productivity_score": analysis_metrics.get("productivity_score", 0),
                "weak_subject": analysis_metrics.get("primary_weak_subject") or "No data",
                "strong_subject": ", ".join(analysis_metrics.get("strong_subjects", [])[:2]) or "No data",
                "predicted_exam_score": analysis_metrics.get("predicted_exam_score"),
                "predicted_exam_outlook": analysis_metrics.get("predicted_exam_outlook", "No outlook available."),
            },
            "chart_data": chart_payload,
            "signature": signature,
            "refresh_needed": should_refresh_analytics(
                force=force,
                previous_signature=self._analytics_signature,
                current_signature=signature,
            ),
        }

    def _apply_analytics_data(self, payload):
        self._analytics_loading = False
        if not payload:
            return
        if not payload.get("refresh_needed", True):
            return
        if self._cached_chart_payload == payload.get("signature"):
            return

        tasks = payload.get("tasks", [])
        sessions = payload.get("sessions", [])
        analysis_text = payload.get("analysis_text", "")
        self.update_statistics(payload.get("statistics", {}))
        self.create_study_time_chart(payload.get("chart_data", {}).get("study_time", {}))
        self.create_weekly_study_chart(payload.get("chart_data", {}).get("weekly", {}))
        self.create_subject_study_chart(payload.get("chart_data", {}).get("subject", {}))
        self.create_productivity_chart(payload.get("statistics", {}))
        self.create_monthly_study_chart(payload.get("chart_data", {}).get("monthly", {}))
        self.create_task_status_chart(
            payload.get("chart_data", {}).get("task_status", {}),
            payload.get("statistics", {}).get("completion_rate", 0),
        )
        self.update_subject_breakdown(payload.get("statistics", {}))
        self.update_ai_analysis(analysis_text)
        self._analytics_signature = payload.get("signature")
        self._cached_chart_payload = payload.get("signature")

    def _show_analytics_error(self, error, safe_message=None):
        self._analytics_loading = False
        self._reset_ai_loading_state()
        friendly_message = safe_message or handle_operation_error(
            error,
            context="loading analytics",
            user_message="We couldn't load analytics right now.",
        )
        messagebox.showerror("Analytics Error", friendly_message)

    def _reset_ai_loading_state(self):
        if hasattr(self, "refresh_button"):
            set_loading_state(button_widget=self.refresh_button, text="Refresh", loading=False)
        elif hasattr(self, "header_frame"):
            for child in self.header_frame.winfo_children():
                if getattr(child, "cget", None) and child.cget("text") == "Refresh":
                    set_loading_state(button_widget=child, text="Refresh", loading=False)
                    break


    # ======================================================
    # UPDATE STATISTICS
    # ======================================================

    def _build_statistics_payload(
        self,
        tasks,
        sessions,
        subject_stats=None,
        study_dates=None,
    ):
        total_minutes = 0
        daily_minutes = 0
        weekly_minutes = 0
        monthly_minutes = 0
        today = datetime.now().date()
        current_month = today.strftime("%Y-%m")

        for session in sessions:
            if len(session) <= 2:
                continue
            duration = int(session[2])
            total_minutes += duration
            try:
                session_date = datetime.strptime(str(session[3]), "%Y-%m-%d").date()
            except ValueError:
                continue
            if session_date == today:
                daily_minutes += duration
            if session_date >= today - timedelta(days=6):
                weekly_minutes += duration
            if session_date.strftime("%Y-%m") == current_month:
                monthly_minutes += duration

        subject_stats = subject_stats or []
        top_subject_name = "No data"
        top_subject_minutes = 0
        if subject_stats:
            top_subject_name, top_subject_minutes = subject_stats[0]

        total_tasks = len(tasks)
        completed_tasks = 0
        pending_tasks = 0
        for task in tasks:
            status = str(task[6]).strip().lower()
            if status == "completed":
                completed_tasks += 1
            else:
                pending_tasks += 1

        if total_tasks > 0:
            completion_rate = (completed_tasks / total_tasks) * 100
        else:
            completion_rate = 0

        study_dates = study_dates or []
        parsed_dates = []
        for study_date in study_dates:
            if not study_date:
                continue
            try:
                parsed_dates.append(datetime.strptime(str(study_date), "%Y-%m-%d").date())
            except ValueError:
                try:
                    parsed_dates.append(datetime.strptime(str(study_date), "%Y-%m-%d %H:%M:%S").date())
                except ValueError:
                    continue

        streak = 0
        if parsed_dates:
            unique_dates = sorted(set(parsed_dates))
            current_day = today
            while current_day in unique_dates:
                streak += 1
                current_day -= timedelta(days=1)

        return {
            "total_minutes": total_minutes,
            "daily_minutes": daily_minutes,
            "weekly_minutes": weekly_minutes,
            "monthly_minutes": monthly_minutes,
            "top_subject_name": top_subject_name,
            "top_subject_minutes": int(top_subject_minutes),
            "completed_tasks": completed_tasks,
            "pending_tasks": pending_tasks,
            "completion_rate": completion_rate,
            "streak": streak,
        }

    def update_statistics(self, stats_payload):
        stats_payload = stats_payload or {}
        self.total_study_card.value_label.configure(text=f"{stats_payload.get('total_minutes', 0)} min")
        self.daily_study_card.value_label.configure(text=f"{stats_payload.get('daily_minutes', 0)} min")
        self.weekly_study_card.value_label.configure(text=f"{stats_payload.get('weekly_minutes', 0)} min")
        self.monthly_study_card.value_label.configure(text=f"{stats_payload.get('monthly_minutes', 0)} min")

        top_subject_name = stats_payload.get("top_subject_name", "No data")
        top_subject_minutes = stats_payload.get("top_subject_minutes", 0)
        if top_subject_name == "No data":
            self.subject_study_card.value_label.configure(text="No data")
        else:
            self.subject_study_card.value_label.configure(
                text=f"{top_subject_name}: {round(top_subject_minutes / 60, 1)}h"
            )

        self.completed_task_card.value_label.configure(text=str(stats_payload.get("completed_tasks", 0)))
        self.pending_task_card.value_label.configure(text=str(stats_payload.get("pending_tasks", 0)))
        self.completion_rate_card.value_label.configure(text=f"{stats_payload.get('completion_rate', 0):.1f}%")
        self.streak_card.value_label.configure(text=f"{stats_payload.get('streak', 0)} days")
        if hasattr(self, 'productivity_card'):
            self.productivity_card.value_label.configure(text=f"{stats_payload.get('productivity_score', 0)}/100")
        if hasattr(self, 'weak_subject_card'):
            weak_subject_name = stats_payload.get('weak_subject', 'No data') or 'No data'
            self.weak_subject_card.value_label.configure(text=weak_subject_name)
        if hasattr(self, 'strong_subject_card'):
            strong_subject_name = stats_payload.get('strong_subject', 'No data') or 'No data'
            self.strong_subject_card.value_label.configure(text=strong_subject_name)
        if hasattr(self, 'exam_prediction_card'):
            predicted_score = stats_payload.get('predicted_exam_score')
            if predicted_score is not None:
                self.exam_prediction_card.value_label.configure(text=f"{predicted_score}/100")
            else:
                self.exam_prediction_card.value_label.configure(text="N/A")


    # ======================================================
    # UPDATE AI ANALYSIS
    # ======================================================

    def update_ai_analysis(self, analysis_text):
        self.ai_analysis_textbox.configure(state="normal")
        self.ai_analysis_textbox.delete("1.0", "end")
        self.ai_analysis_textbox.insert("1.0", analysis_text)
        self.ai_analysis_textbox.configure(state="disabled")
        self.ai_analysis_textbox.see("1.0")

    def update_subject_breakdown(self, stats_payload):
        stats_payload = stats_payload or {}
        strong_subject = stats_payload.get("strong_subject", "No data") or "No data"
        weak_subject = stats_payload.get("weak_subject", "No data") or "No data"
        predicted_score = stats_payload.get("predicted_exam_score")
        predicted_outlook = stats_payload.get("predicted_exam_outlook", "No outlook available.")

        self.strong_subject_label.configure(text=f"Strong Subject: {strong_subject}")
        self.weak_subject_label.configure(text=f"Weak Subject: {weak_subject}")
        if predicted_score is not None:
            self.exam_outlook_label.configure(text=f"Exam Readiness: {predicted_score}/100")
        else:
            self.exam_outlook_label.configure(text=f"Exam Readiness: No data")
        self.exam_outlook_label.configure(tooltip_text=predicted_outlook if hasattr(self.exam_outlook_label, 'tooltip_text') else predicted_outlook)

    # ======================================================
    # STUDY TIME BAR CHART
    # ======================================================

    def create_study_time_chart(self, chart_data):
        self.clear_chart_frame(self.study_chart_frame)

        if not chart_data:
            ctk.CTkLabel(self.study_chart_frame, text="No study data available.").pack(pady=40)
            return

        dates = list(chart_data.keys())
        minutes = list(chart_data.values())

        figure = Figure(figsize=(6, 4), dpi=100)
        axis = figure.add_subplot(111)
        axis.bar(dates, minutes)
        axis.set_title("Daily Study Time")
        axis.set_xlabel("Date")
        axis.set_ylabel("Minutes")
        axis.tick_params(axis="x", rotation=45)
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=self.study_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_monthly_study_chart(self, chart_data):
        self.clear_chart_frame(self.monthly_chart_frame)

        if not chart_data:
            ctk.CTkLabel(self.monthly_chart_frame, text="No monthly study data.").pack(pady=40)
            return

        figure = Figure(figsize=(6, 4), dpi=100)
        axis = figure.add_subplot(111)
        axis.bar(list(chart_data.keys()), list(chart_data.values()))
        axis.set_title("Monthly Study Time")
        axis.set_xlabel("Month")
        axis.set_ylabel("Minutes")
        axis.tick_params(axis="x", rotation=45)
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=self.monthly_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def create_subject_study_chart(self, chart_data):
        self.clear_chart_frame(self.subject_chart_frame)

        if not chart_data:
            ctk.CTkLabel(self.subject_chart_frame, text="No subject study data.").pack(pady=40)
            return

        figure = Figure(figsize=(6, 4), dpi=100)
        axis = figure.add_subplot(111)
        labels = list(chart_data.keys())
        values = [round(value / 60, 1) for value in chart_data.values()]
        axis.bar(labels, values)
        axis.set_title("Subject Study Time (hours)")
        axis.set_xlabel("Subject")
        axis.set_ylabel("Hours")
        axis.tick_params(axis="x", rotation=45)
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=self.subject_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


    # ======================================================
    # TASK STATUS PIE CHART
    # ======================================================

    def create_task_status_chart(self, chart_data, completion_rate=0):
        self.clear_chart_frame(self.status_chart_frame)

        if not chart_data:
            ctk.CTkLabel(self.status_chart_frame, text="No task data available.").pack(pady=40)
            return

        completed = int(chart_data.get("Completed", 0))
        pending = int(chart_data.get("Pending", 0))

        if completed == 0 and pending == 0:
            ctk.CTkLabel(self.status_chart_frame, text="No task data available.").pack(pady=40)
            return

        labels = ["Completed", "Pending"]
        values = [completed, pending]

        figure = Figure(figsize=(6, 4), dpi=100)
        axis = figure.add_subplot(111)
        wedges, texts, autotexts = axis.pie(
            values,
            labels=labels,
            autopct="%1.1f%%",
            startangle=90,
            wedgeprops={"edgecolor": "white"},
        )
        axis.set_title("Task Completion Status")

        if completion_rate is not None:
            axis.text(0, -1.3, f"Overall Completion Rate: {completion_rate:.1f}%", ha="center", fontsize=10)

        figure.tight_layout()
        canvas = FigureCanvasTkAgg(figure, master=self.status_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


    # ======================================================
    # WEEKLY STUDY CHART

    def create_weekly_study_chart(self, chart_data):
        self.clear_chart_frame(self.weekly_chart_frame)

        if not chart_data:
            ctk.CTkLabel(self.weekly_chart_frame, text="No weekly study data.").pack(pady=40)
            return

        dates = list(chart_data.keys())
        minutes = list(chart_data.values())

        figure = Figure(figsize=(6, 4), dpi=100)
        axis = figure.add_subplot(111)
        axis.plot(dates, minutes, marker="o", linestyle="-", color="#2a9fd6")
        axis.set_title("Weekly Study Time")
        axis.set_xlabel("Date")
        axis.set_ylabel("Minutes")
        axis.tick_params(axis="x", rotation=45)
        figure.tight_layout()

        canvas = FigureCanvasTkAgg(figure, master=self.weekly_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)


    # ======================================================
    # PRODUCTIVITY CHART

    def create_productivity_chart(self, stats_payload):
        self.clear_chart_frame(self.productivity_chart_frame)

        score = stats_payload.get("productivity_score", 0)
        completion_rate = stats_payload.get("completion_rate", 0)
        weekly_minutes = stats_payload.get("weekly_minutes", 0)
        streak = stats_payload.get("streak", 0)

        figure = Figure(figsize=(6, 4), dpi=100)
        axis = figure.add_subplot(111)

        axis.bar(["Productivity"], [score], color="#4caf50")
        axis.set_ylim(0, 100)
        axis.set_title("Productivity Score")
        axis.set_ylabel("Score")
        axis.text(0, score + 3, f"{score}/100", ha="center", va="bottom", fontsize=10)

        axis2 = axis.twinx()
        axis2.plot(["Weekly"], [weekly_minutes], marker="o", color="#e67e22")
        axis2.set_ylabel("Weekly Minutes", color="#e67e22")
        axis2.tick_params(axis="y", labelcolor="#e67e22")

        figure.tight_layout()
        canvas = FigureCanvasTkAgg(figure, master=self.productivity_chart_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

        ctk.CTkLabel(
            self.productivity_chart_frame,
            text=f"Completion Rate: {completion_rate:.1f}%   Streak: {streak} days",
            font=("Arial", 12),
        ).pack(pady=(10, 0))


    # ======================================================
    # PRIORITY CHART
    # ======================================================

    def create_priority_chart(

        self,

        tasks

    ):

        self.clear_chart_frame(

            self.priority_chart_frame

        )


        # --------------------------------------------------
        # Set Data Structure
        # --------------------------------------------------

        priorities = {

            "High": 0,

            "Medium": 0,

            "Low": 0

        }


        for task in tasks:

            priority = task[4]


            if priority in priorities:

                priorities[priority] += 1


        priority_names = list(

            priorities.keys()

        )


        priority_values = list(

            priorities.values()

        )


        if sum(

            priority_values

        ) == 0:

            ctk.CTkLabel(

                self.priority_chart_frame,

                text=(

                    "No priority data available."

                )

            ).pack(

                pady=40

            )


            return


        figure = Figure(

            figsize=(

                10,

                4

            ),

            dpi=100

        )


        axis = figure.add_subplot(

            111

        )


        axis.bar(

            priority_names,

            priority_values

        )


        axis.set_title(

            "Tasks by Priority"

        )


        axis.set_xlabel(

            "Priority"

        )


        axis.set_ylabel(

            "Number of Tasks"

        )


        figure.tight_layout()


        canvas = FigureCanvasTkAgg(

            figure,

            master=self.priority_chart_frame

        )


        canvas.draw()


        canvas.get_tk_widget().pack(

            fill="both",

            expand=True

        )


    # ======================================================
    # CLEAR CHART FRAME
    # ======================================================

    def _build_chart_payload(self, sessions, tasks):
        study_time = {}
        for session in sessions:
            if len(session) <= 2:
                continue
            try:
                session_date = str(session[3])
                duration = int(session[2])
            except (TypeError, ValueError):
                continue
            study_time[session_date] = study_time.get(session_date, 0) + duration

        monthly_data = {}
        for session in sessions:
            if len(session) <= 2:
                continue
            try:
                session_date = datetime.strptime(str(session[3]), "%Y-%m-%d").date()
                duration = int(session[2])
            except (TypeError, ValueError):
                continue
            month_key = session_date.strftime("%Y-%m")
            monthly_data[month_key] = monthly_data.get(month_key, 0) + duration

        subject_data = {}
        for session in sessions:
            if len(session) <= 2:
                continue
            subject_name = str(session[1])
            duration = int(session[2])
            subject_data[subject_name] = subject_data.get(subject_name, 0) + duration

        task_status_data = {"Completed": 0, "Pending": 0}
        for task in tasks:
            if task[6] == "Completed":
                task_status_data["Completed"] += 1
            else:
                task_status_data["Pending"] += 1

        # Build a 7-day weekly series (today and previous 6 days) for the weekly chart
        weekly_data = {}
        try:
            today = datetime.now().date()
        except Exception:
            today = None

        if today is not None:
            # initialize keys in chronological order
            for d in range(6, -1, -1):
                day = today - timedelta(days=d)
                key = day.strftime("%Y-%m-%d")
                weekly_data[key] = 0

            for session in sessions:
                if len(session) <= 2:
                    continue
                try:
                    session_date = datetime.strptime(str(session[3]), "%Y-%m-%d").date()
                    duration = int(session[2])
                except (TypeError, ValueError):
                    # skip sessions with malformed dates
                    continue
                key = session_date.strftime("%Y-%m-%d")
                if key in weekly_data:
                    weekly_data[key] = weekly_data.get(key, 0) + duration

        return {
            "study_time": study_time,
            "weekly": weekly_data,
            "monthly": monthly_data,
            "subject": subject_data,
            "task_status": task_status_data,
        }

    def clear_chart_frame(

        self,

        frame

    ):

        for widget in (

            frame.winfo_children()

        ):

            widget.destroy()

    def destroy(self):
        self._analytics_loading = False
        self._analytics_signature = None
        self._refresh_callback = None
        self.database = None
        super().destroy()