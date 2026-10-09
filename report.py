"""
report.py

Study Tracker Pro

Study Report Module.

Features:
- Generate study report
- Display study statistics
- Subject analysis
- Task analysis
- Export report to TXT file
"""

import calendar

import customtkinter as ctk

from tkinter import messagebox

from tkinter import filedialog

from datetime import datetime, timedelta

from database import DatabaseManager
from ai_service import generate_weekly_report, generate_monthly_report
from task_manager import BackgroundTaskManager
from utils import run_in_background, set_loading_state, handle_operation_error

try:
    from fpdf import FPDF
except ImportError:
    FPDF = None


# ==========================================================
# REPORT WINDOW
# ==========================================================

class ReportWindow(ctk.CTkFrame):
    """
    Study Report page.
    """

    def __init__(self, parent, database=None, settings_manager=None):

        super().__init__(parent)


        self.parent = parent


        self.database = database or DatabaseManager()
        self.settings_manager = settings_manager

        self._report_generation_in_progress = False
        self._report_loaded = False
        self._task_manager = BackgroundTaskManager()

        self.create_layout()
        self.apply_application_settings(self.settings_manager.get_all_settings() if self.settings_manager else None)

    def on_show(self):
        if not self._report_generation_in_progress and not self._report_loaded:
            self.generate_report()


    # ======================================================
    # CREATE LAYOUT
    # ======================================================

    def create_layout(self):

        self.grid_columnconfigure(

            0,

            weight=1

        )

        self.grid_rowconfigure(2, weight=1)

        self.create_header()

        self.create_controls()

        self.create_report_area()

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

            text="Study Report",

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

                "Review your study progress and achievements."

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

            command=self.generate_report

        )
        self.refresh_button.grid(

            row=0,

            column=1,

            rowspan=2,

            padx=10

        )


    # ======================================================
    # CONTROLS AREA
    # ======================================================

    def create_controls(self):

        self.control_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.control_frame.grid(row=1, column=0, sticky="ew", padx=25, pady=(0, 10))
        self.control_frame.grid_columnconfigure(0, weight=0)
        self.control_frame.grid_columnconfigure(1, weight=1)
        self.control_frame.grid_columnconfigure(2, weight=0)
        self.control_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(self.control_frame, text="Report Type:", font=("Arial", 12, "bold")).grid(
            row=0, column=0, sticky="w", padx=(0, 10), pady=5
        )

        self.period_var = ctk.StringVar(value="Monthly")
        self.period_menu = ctk.CTkOptionMenu(
            self.control_frame,
            values=["Daily", "Weekly", "Monthly", "Custom Range"],
            variable=self.period_var,
            command=self._toggle_range_inputs,
            width=160,
        )
        self.period_menu.grid(row=0, column=1, sticky="w", padx=5, pady=5)

        self.range_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.range_frame.grid(row=0, column=2, columnspan=2, sticky="ew", padx=(15, 0), pady=5)
        self.range_frame.grid_columnconfigure(0, weight=0)
        self.range_frame.grid_columnconfigure(1, weight=1)
        self.range_frame.grid_columnconfigure(2, weight=0)
        self.range_frame.grid_columnconfigure(3, weight=1)

        ctk.CTkLabel(self.range_frame, text="Start:", font=("Arial", 11)).grid(row=0, column=0, sticky="w", padx=(0, 6))
        self.start_date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.start_entry = ctk.CTkEntry(self.range_frame, textvariable=self.start_date_var, width=120)
        self.start_entry.grid(row=0, column=1, sticky="w", padx=(0, 10))

        ctk.CTkLabel(self.range_frame, text="End:", font=("Arial", 11)).grid(row=0, column=2, sticky="w", padx=(0, 6))
        self.end_date_var = ctk.StringVar(value=datetime.now().strftime("%Y-%m-%d"))
        self.end_entry = ctk.CTkEntry(self.range_frame, textvariable=self.end_date_var, width=120)
        self.end_entry.grid(row=0, column=3, sticky="w")

        ctk.CTkButton(
            self.control_frame,
            text="Generate",
            width=110,
            command=self.generate_report,
        ).grid(row=0, column=4, sticky="e", padx=(12, 0), pady=5)

        self._toggle_range_inputs(self.period_var.get())

    def _toggle_range_inputs(self, _value):
        is_custom = self.period_var.get() == "Custom Range"
        state = "normal" if is_custom else "disabled"
        self.start_entry.configure(state=state)
        self.end_entry.configure(state=state)

    # ======================================================
    # REPORT AREA
    # ======================================================

    def create_report_area(self):

        self.report_textbox = ctk.CTkTextbox(

            self,

            font=(

                "Consolas",

                14

            )

        )


        self.report_textbox.grid(

            row=2,

            column=0,

            sticky="nsew",

            padx=25,

            pady=15

        )

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
        self._configure_textbox_tab_size(self.report_textbox, tab_size)

    # ======================================================
    # BUTTON AREA
    # ======================================================

    def create_buttons(self):

        self.button_frame = ctk.CTkFrame(

            self,

            fg_color="transparent"

        )


        self.button_frame.grid(

            row=3,

            column=0,

            sticky="ew",

            padx=25,

            pady=(5, 25)

        )


        ctk.CTkButton(

            self.button_frame,

            text="Export Report",

            width=160,

            height=40,

            command=self.export_report

        ).pack(

            side="left",

            padx=5

        )

        ctk.CTkButton(

            self.button_frame,

            text="Export PDF",

            width=160,

            height=40,

            command=self.export_report_as_pdf

        ).pack(

            side="left",

            padx=5

        )


        self.generate_button = ctk.CTkButton(

            self.button_frame,

            text="Generate Again",

            width=160,

            height=40,

            command=self.generate_report

        )
        self.generate_button.pack(

            side="left",

            padx=5

        )


    # ======================================================
    # GENERATE REPORT
    # ======================================================

    def generate_report(self):
        if self._report_generation_in_progress:
            return

        self._report_generation_in_progress = True
        self.report_textbox.delete("1.0", "end")
        self.report_textbox.insert("1.0", "Generating report...\n\nThis may take a moment.")
        self._set_report_loading_state()
        try:
            period = self.period_var.get() or "Monthly"
            start_date, end_date = self._get_date_range(period)
            self._task_manager.submit_task(
                "report",
                target=self._build_report_content,
                callback=self._display_report_content,
                error_callback=self._show_report_error,
                widget=self,
                period=period,
                start_date=start_date,
                end_date=end_date,
            )
        except Exception as error:
            self._show_report_error(error)

    def _set_report_loading_state(self):
        for button_widget in self._get_report_buttons():
            set_loading_state(button_widget=button_widget, text="Generating report...", loading=True)

    def _get_report_buttons(self):
        buttons = []
        if hasattr(self, "generate_button") and self.generate_button is not None:
            buttons.append(self.generate_button)
        if hasattr(self, "refresh_button") and self.refresh_button is not None:
            buttons.append(self.refresh_button)
        if not buttons and hasattr(self, "button_frame"):
            for child in self.button_frame.winfo_children():
                if getattr(child, "cget", None) and child.cget("text") in {"Generate Again", "Refresh"}:
                    buttons.append(child)
        return buttons

    def _build_report_content(self, period, start_date, end_date):
        tasks = self.database.get_tasks_by_date_range(start_date, end_date) if self.database else []
        sessions = self.database.get_study_sessions_by_date_range(start_date, end_date) if self.database else []
        filtered_tasks = self._filter_tasks(tasks, start_date, end_date)
        filtered_sessions = self._filter_sessions(sessions, start_date, end_date)
        return self.create_report_text(
            filtered_tasks,
            filtered_sessions,
            period,
            start_date,
            end_date,
        )

    def _display_report_content(self, report):
        self._report_generation_in_progress = False
        self.report_textbox.delete("1.0", "end")
        self.report_textbox.insert("1.0", report)
        self._reset_report_loading_state()

    def _show_report_error(self, error, safe_message=None):
        self._report_generation_in_progress = False
        self._reset_report_loading_state()
        friendly_message = safe_message or handle_operation_error(
            error,
            context="generating report",
            user_message="We couldn't generate the report right now.",
        )
        messagebox.showerror("Report Error", friendly_message)

    def _reset_report_loading_state(self):
        for button_widget in self._get_report_buttons():
            set_loading_state(button_widget=button_widget, text="Generate Again", loading=False)

    def _get_date_range(self, period):
        today = datetime.now().date()
        if period == "Daily":
            return today, today
        if period == "Weekly":
            start_date = today - timedelta(days=today.weekday())
            return start_date, start_date + timedelta(days=6)
        if period == "Monthly":
            first_day = today.replace(day=1)
            if today.month == 12:
                last_day = datetime(today.year + 1, 1, 1).date() - timedelta(days=1)
            else:
                last_day = datetime(today.year, today.month + 1, 1).date() - timedelta(days=1)
            return first_day, last_day

        start_value = self.start_date_var.get().strip()
        end_value = self.end_date_var.get().strip()
        start_date = self._parse_date(start_value)
        end_date = self._parse_date(end_value)
        if start_date is None:
            start_date = today
        if end_date is None:
            end_date = today
        if end_date < start_date:
            start_date, end_date = end_date, start_date
        return start_date, end_date

    def _parse_date(self, value):
        if not value:
            return None
        for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"):
            try:
                return datetime.strptime(str(value), fmt).date()
            except ValueError:
                continue
        return None

    def _filter_tasks(self, tasks, start_date, end_date):
        filtered = []
        for task in tasks:
            if not task:
                continue
            deadline = None
            if len(task) > 5 and task[5]:
                deadline = self._parse_date(task[5])
            if deadline is None:
                filtered.append(task)
                continue
            if start_date <= deadline <= end_date:
                filtered.append(task)
        return filtered

    def _filter_sessions(self, sessions, start_date, end_date):
        filtered = []
        for session in sessions:
            if not session or len(session) <= 3:
                continue
            try:
                session_date = self._parse_date(session[3])
            except (TypeError, ValueError):
                continue
            if session_date and start_date <= session_date <= end_date:
                filtered.append(session)
        return filtered

    # ======================================================
    # CREATE REPORT TEXT
    # ======================================================

    def create_report_text(self, tasks, sessions, period, start_date, end_date):
        total_tasks = len(tasks)
        completed_tasks = 0
        pending_tasks = 0

        for task in tasks:
            status = str(task[6]).strip().lower() if len(task) > 6 else ""
            if status == "completed":
                completed_tasks += 1
            else:
                pending_tasks += 1

        completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

        total_minutes = 0
        subject_study_time = {}
        for session in sessions:
            if len(session) <= 2:
                continue
            try:
                duration = int(session[2])
            except (TypeError, ValueError):
                continue
            total_minutes += duration
            subject = str(session[1] or "Unassigned")
            subject_study_time[subject] = subject_study_time.get(subject, 0) + duration

        total_hours, remaining_minutes = divmod(total_minutes, 60)
        report_date = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if period == "Weekly":
            analysis_text = generate_weekly_report(tasks, sessions, start_date=start_date, end_date=end_date)
        elif period == "Monthly":
            analysis_text = generate_monthly_report(tasks, sessions, start_date=start_date, end_date=end_date)
        else:
            analysis_text = generate_monthly_report(tasks, sessions, start_date=start_date, end_date=end_date)

        report_lines = []
        report_lines.append("=" * 78)
        report_lines.append("                 STUDY TRACKER PRO REPORT")
        report_lines.append("=" * 78)
        report_lines.append(f"Report Generated : {report_date}")
        report_lines.append(f"Report Type      : {period}")
        report_lines.append(
            f"Date Range       : {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}"
        )
        report_lines.append("")
        report_lines.append("GENERAL SUMMARY")
        report_lines.append("-" * 78)
        report_lines.append(f"Completed Tasks  : {completed_tasks}")
        report_lines.append(f"Pending Tasks    : {pending_tasks}")
        report_lines.append(f"Completion Rate  : {completion_rate:.1f}%")
        report_lines.append(f"Study Sessions  : {len(sessions)}")
        report_lines.append(f"Total Study Time : {total_hours} hour(s) {remaining_minutes} minute(s)")
        report_lines.append("")

        report_lines.append("AI STUDY ANALYSIS")
        report_lines.append("-" * 78)
        report_lines.extend(analysis_text.splitlines())
        report_lines.append("")
        report_lines.append("SUBJECT PROGRESS")
        report_lines.append("-" * 78)
        if subject_study_time:
            for subject, minutes in sorted(subject_study_time.items(), key=lambda item: item[1], reverse=True):
                subject_hours, subject_minutes = divmod(minutes, 60)
                percent = (minutes / total_minutes * 100) if total_minutes else 0
                report_lines.append(
                    f"{subject:<20}: {subject_hours}h {subject_minutes}m ({percent:.1f}%)"
                )
        else:
            report_lines.append("No subject study data recorded.")
        report_lines.append("")

        report_lines.append("STUDY SESSIONS")
        report_lines.append("-" * 78)
        if sessions:
            for session in sessions:
                if len(session) <= 3:
                    continue
                subject = str(session[1] or "Unassigned")
                duration = str(session[2])
                study_date = str(session[3])
                report_lines.append(f"{study_date} | {subject} | {duration} min")
        else:
            report_lines.append("No study sessions recorded in this period.")
        report_lines.append("")

        report_lines.append("TASK LIST")
        report_lines.append("-" * 78)
        if tasks:
            for task in tasks:
                title = str(task[2] or "Untitled") if len(task) > 2 else "Untitled"
                subject = str(task[1] or "Unassigned") if len(task) > 1 else "Unassigned"
                status = str(task[6] or "Pending") if len(task) > 6 else "Pending"
                deadline = str(task[5] or "No deadline") if len(task) > 5 else "No deadline"
                report_lines.append(f"[{status}] {title} | Subject: {subject} | Deadline: {deadline}")
        else:
            report_lines.append("No tasks found for this period.")
        report_lines.append("")
        report_lines.append("=" * 78)
        report_lines.append("End of Study Tracker Pro Report")
        report_lines.append("=" * 78)
        return "\n".join(report_lines)


    # ======================================================
    # EXPORT REPORT
    # ======================================================

    def destroy(self):
        self._report_generation_in_progress = False
        self.database = None
        super().destroy()

    def export_report(self):

        report_content = (

            self.report_textbox

            .get(

                "1.0",

                "end"

            )

        )

        if report_content.strip() == "Generating report...":
            messagebox.showinfo("Report Export", "Please wait until the current report generation completes.")
            return

        if not report_content.strip():

            messagebox.showwarning(

                "Warning",

                "There is no report to export."

            )


            return


        file_path = filedialog.asksaveasfilename(

            defaultextension=".txt",

            filetypes=[

                (

                    "Text Files",

                    "*.txt"

                ),

                (

                    "Markdown Files",

                    "*.md"

                ),

                (

                    "All Files",

                    "*.*"

                )

            ],

            title="Save Study Report"

        )


        if not file_path:

            return


        try:

            with open(

                file_path,

                "w",

                encoding="utf-8"

            ) as file:

                file.write(

                    report_content

                )


            messagebox.showinfo(

                "Success",

                "Report exported successfully."

            )


        except Exception as error:

            messagebox.showerror(

                "Error",

                (

                    f"Unable to export report.\n"

                    f"{error}"

                )

            )

    def export_report_as_pdf(self):
        report_content = self.report_textbox.get("1.0", "end").strip()
        if not report_content:
            messagebox.showwarning("Warning", "There is no report to export.")
            return

        if FPDF is None:
            messagebox.showerror(
                "PDF Export Unavailable",
                "PDF export requires the fpdf2 package. Please install it and try again."
            )
            return

        file_path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[
                ("PDF Files", "*.pdf"),
                ("All Files", "*.*"),
            ],
            title="Save Study Report as PDF",
        )

        if not file_path:
            return

        try:
            pdf = FPDF()
            pdf.set_auto_page_break(auto=True, margin=15)
            pdf.add_page()
            pdf.set_font("Arial", size=11)
            for line in report_content.splitlines():
                pdf.multi_cell(0, 7, line)
            pdf.output(file_path)
            messagebox.showinfo("Success", "PDF report exported successfully.")
        except Exception as error:
            messagebox.showerror(
                "Error",
                f"Unable to export report to PDF.\n{error}"
            )