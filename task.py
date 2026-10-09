import customtkinter as ctk

import json

from datetime import date, datetime, timedelta
from tkinter import messagebox

from database import DatabaseManager

from models import StudyTask
from analytics import request_analytics_refresh
from utils import ValidationError, validate_date_string, validate_required_field, run_in_background, handle_operation_error


# ==========================================================
# TASK WINDOW
# ==========================================================

class TaskWindow(ctk.CTkFrame):
    """
    Task management page.
    """

    def __init__(self, parent, database=None, settings_manager=None):

        super().__init__(parent)

        self.parent = parent

        self.database = database or DatabaseManager()
        self.settings_manager = settings_manager

        self.selected_task_id = None
        self._tasks_loaded = False
        self._subjects_loaded = False

        self.create_layout()

        self.load_subjects()

        self.load_tasks(force=True)
        self.apply_application_settings(self.settings_manager.get_all_settings() if self.settings_manager else None)

    def apply_application_settings(self, settings=None):
        # No-op default for task window theme/appearance integration.
        return


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


        self.content_frame = ctk.CTkFrame(

            self

        )

        self.content_frame.grid(

            row=1,

            column=0,

            sticky="nsew",

            padx=20,

            pady=20

        )


        self.content_frame.grid_columnconfigure(

            1,

            weight=1

        )


        self.content_frame.grid_rowconfigure(

            0,

            weight=1

        )


        self.create_form()

        self.create_task_list()


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

            padx=20,

            pady=(20, 5)

        )


        self.header_frame.grid_columnconfigure(

            0,

            weight=1

        )


        ctk.CTkLabel(

            self.header_frame,

            text="Task Management",

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


        ctk.CTkButton(

            self.header_frame,

            text="Refresh",

            width=100,

            command=self.load_tasks

        ).grid(

            row=0,

            column=1,

            padx=10

        )


    # ======================================================
    # TASK FORM
    # ======================================================

    def create_form(self):

        self.form_frame = ctk.CTkScrollableFrame(

            self.content_frame,

            width=330

        )


        self.form_frame.grid(

            row=0,

            column=0,

            sticky="nsew",

            padx=(10, 20),

            pady=10

        )


        ctk.CTkLabel(

            self.form_frame,

            text="Task Details",

            font=(

                "Arial",

                20,

                "bold"

            )

        ).pack(

            pady=(15, 25)

        )


        # --------------------------------------------------
        # Subject
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Subject"

        ).pack(

            anchor="w",

            padx=20

        )


        self.subject_combobox = ctk.CTkComboBox(

            self.form_frame,

            width=280,

            values=[

                "No Subject"

            ]

        )


        self.subject_combobox.pack(

            padx=20,

            pady=(5, 15)

        )


        # --------------------------------------------------
        # Task Title
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Task Title"

        ).pack(

            anchor="w",

            padx=20

        )


        self.title_entry = ctk.CTkEntry(

            self.form_frame,

            width=280,

            placeholder_text=(

                "e.g. Complete Python Assignment"

            )

        )


        self.title_entry.pack(

            padx=20,

            pady=(5, 15)

        )


        # --------------------------------------------------
        # Description
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Description"

        ).pack(

            anchor="w",

            padx=20

        )


        self.description_textbox = ctk.CTkTextbox(

            self.form_frame,

            width=280,

            height=100

        )


        self.description_textbox.pack(

            padx=20,

            pady=(5, 15)

        )


        # --------------------------------------------------
        # Priority
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Priority"

        ).pack(

            anchor="w",

            padx=20

        )


        self.priority_combobox = ctk.CTkComboBox(

            self.form_frame,

            width=280,

            values=[

                "High",

                "Medium",

                "Low"

            ]

        )


        self.priority_combobox.set(

            "Medium"

        )


        self.priority_combobox.pack(

            padx=20,

            pady=(5, 15)

        )


        # --------------------------------------------------
        # Deadline
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Deadline"

        ).pack(

            anchor="w",

            padx=20

        )


        self.deadline_entry = ctk.CTkEntry(

            self.form_frame,

            width=280,

            placeholder_text=(

                "YYYY-MM-DD"

            )

        )


        self.deadline_entry.pack(

            padx=20,

            pady=(5, 15)

        )

        # --------------------------------------------------
        # Progress
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Progress"

        ).pack(

            anchor="w",

            padx=20

        )


        self.progress_slider = ctk.CTkSlider(

            self.form_frame,

            width=280,

            from_=0,

            to=100,

            number_of_steps=100,

            command=self.on_progress_change

        )


        self.progress_slider.set(0)

        self.progress_slider.pack(

            padx=20,

            pady=(5, 5)

        )


        self.progress_label = ctk.CTkLabel(

            self.form_frame,

            text="0%"

        )


        self.progress_label.pack(

            anchor="w",

            padx=20,

            pady=(0, 15)

        )

        # --------------------------------------------------
        # Planned Date
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Planned Date"

        ).pack(

            anchor="w",

            padx=20

        )


        self.planned_date_entry = ctk.CTkEntry(

            self.form_frame,

            width=280,

            placeholder_text=(

                "YYYY-MM-DD"

            )

        )


        self.planned_date_entry.pack(

            padx=20,

            pady=(5, 15)

        )

        # --------------------------------------------------
        # Subtasks
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Subtasks (one per line)"

        ).pack(

            anchor="w",

            padx=20

        )


        self.subtasks_textbox = ctk.CTkTextbox(

            self.form_frame,

            width=280,

            height=100

        )


        self.subtasks_textbox.pack(

            padx=20,

            pady=(5, 20)

        )

        # --------------------------------------------------
        # Add Button
        # --------------------------------------------------

        self.add_button = ctk.CTkButton(

            self.form_frame,

            text="Add Task",

            width=280,

            height=40,

            command=self.add_task

        )


        self.add_button.pack(

            padx=20,

            pady=5

        )


        # --------------------------------------------------
        # Update Button
        # --------------------------------------------------

        self.update_button = ctk.CTkButton(

            self.form_frame,

            text="Update Task",

            width=280,

            height=40,

            command=self.update_task,

            state="disabled"

        )


        self.update_button.pack(

            padx=20,

            pady=5

        )


        # --------------------------------------------------
        # Delete Button
        # --------------------------------------------------

        self.delete_button = ctk.CTkButton(
            self.form_frame,
            text="Delete Task",
            width=280,
            height=40,
            fg_color="gray",
            command=self.delete_task,
            state="disabled",
        )

        self.delete_button.pack(
            padx=20,
            pady=5
        )


        # --------------------------------------------------
        # Complete Button
        # --------------------------------------------------

        self.complete_button = ctk.CTkButton(

            self.form_frame,

            text="Mark Completed",

            width=280,

            height=40,

            command=self.complete_task,

            state="disabled"

        )


        self.complete_button.pack(

            padx=20,

            pady=5

        )


        # --------------------------------------------------
        # Clear Button
        # --------------------------------------------------

        ctk.CTkButton(

            self.form_frame,

            text="Clear Form",

            width=280,

            height=40,

            fg_color="transparent",

            border_width=1,

            command=self.clear_form

        ).pack(

            padx=20,

            pady=5

        )


    # ======================================================
    # TASK LIST
    # ======================================================

    def create_task_list(self):

        self.list_frame = ctk.CTkFrame(

            self.content_frame

        )

        self.list_frame.grid(

            row=0,

            column=1,

            sticky="nsew",

            padx=10,

            pady=10

        )


        self.list_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.list_frame.grid_rowconfigure(

            2,

            weight=1

        )


        # --------------------------------------------------
        # Title
        # --------------------------------------------------

        ctk.CTkLabel(

            self.list_frame,

            text="Your Tasks",

            font=(

                "Arial",

                20,

                "bold"

            )

        ).grid(

            row=0,

            column=0,

            sticky="w",

            padx=20,

            pady=15

        )


        # --------------------------------------------------
        # Search
        # --------------------------------------------------

        self.search_entry = ctk.CTkEntry(

            self.list_frame,

            width=300,

            placeholder_text=(

                "Search tasks..."

            )

        )


        self.search_entry.grid(

            row=0,

            column=0,

            sticky="e",

            padx=20,

            pady=15

        )


        self.search_entry.bind(

            "<KeyRelease>",

            self.search_tasks

        )


        # --------------------------------------------------
        # Filters
        # --------------------------------------------------

        self.filter_frame = ctk.CTkFrame(

            self.list_frame,

            fg_color="transparent"

        )


        self.filter_frame.grid(

            row=1,

            column=0,

            sticky="ew",

            padx=20,

            pady=5

        )


        ctk.CTkLabel(

            self.filter_frame,

            text="Status:"

        ).pack(

            side="left",

            padx=5

        )


        self.status_filter = ctk.CTkComboBox(

            self.filter_frame,

            width=150,

            values=[

                "All",

                "Pending",

                "Completed"

            ],

            command=lambda value:

            self.load_tasks()

        )


        self.status_filter.set(

            "All"

        )


        self.status_filter.pack(

            side="left",

            padx=5

        )


        ctk.CTkLabel(

            self.filter_frame,

            text="Priority:"

        ).pack(

            side="left",

            padx=5

        )


        self.priority_filter = ctk.CTkComboBox(

            self.filter_frame,

            width=150,

            values=[

                "All",

                "High",

                "Medium",

                "Low"

            ],

            command=lambda value:

            self.load_tasks()

        )


        self.priority_filter.set(

            "All"

        )


        self.priority_filter.pack(

            side="left",

            padx=5

        )

        ctk.CTkLabel(
            self.filter_frame,
            text="Planned:"
        ).pack(side="left", padx=5)

        self.planned_filter = ctk.CTkComboBox(
            self.filter_frame,
            width=150,
            values=[
                "All",
                "Today",
                "This Week",
                "No Plan"
            ],
            command=lambda value: self.load_tasks()
        )
        self.planned_filter.set("All")
        self.planned_filter.pack(side="left", padx=5)

        ctk.CTkLabel(
            self.filter_frame,
            text="Progress:"
        ).pack(side="left", padx=5)

        self.progress_filter = ctk.CTkComboBox(
            self.filter_frame,
            width=170,
            values=[
                "All",
                "Not Started",
                "In Progress",
                "Complete"
            ],
            command=lambda value: self.load_tasks()
        )
        self.progress_filter.set("All")
        self.progress_filter.pack(side="left", padx=5)

        ctk.CTkLabel(
            self.filter_frame,
            text="Sort:"
        ).pack(side="left", padx=5)

        self.sort_filter = ctk.CTkComboBox(
            self.filter_frame,
            width=180,
            values=[
                "Due date",
                "Planned date",
                "Priority",
                "Status"
            ],
            command=lambda value: self.load_tasks()
        )
        self.sort_filter.set("Due date")
        self.sort_filter.pack(side="left", padx=5)

        # --------------------------------------------------
        # Scrollable Task List
        # --------------------------------------------------

        self.task_scrollable = ctk.CTkScrollableFrame(

            self.list_frame

        )


        self.task_scrollable.grid(

            row=2,

            column=0,

            sticky="nsew",

            padx=10,

            pady=10

        )


    # ======================================================
    # LOAD SUBJECTS
    # ======================================================

    def load_subjects(self, force=False):
        if not force and getattr(self, "_subjects_loaded", False):
            return
        self._subjects_loaded = True
        run_in_background(
            self,
            self._load_subjects_data,
            callback=self._apply_subjects_data,
            error_callback=self._show_task_error,
        )

    def on_progress_change(self, value):
        try:
            percent = int(float(value))
            if hasattr(self, 'progress_label'):
                self.progress_label.configure(text=f"{percent}%")
        except Exception:
            pass

    def _load_subjects_data(self):
        subjects = self.database.get_all_subjects() if self.database else []
        return [subject[1] for subject in subjects]

    def _apply_subjects_data(self, subject_names):
        self._subjects_loaded = True
        if subject_names is None:
            subject_names = []
        if not subject_names:
            subject_names = ["No Subject"]
        self.subject_combobox.configure(values=subject_names)
        self.subject_combobox.set(subject_names[0])

    def _show_task_error(self, error, safe_message=None):
        friendly_message = safe_message or handle_operation_error(
            error,
            context="refreshing task data",
            user_message="We couldn't refresh tasks right now.",
        )
        messagebox.showerror("Task Error", friendly_message)


    def parse_deadline(self, deadline):
        """Convert a deadline string into a date object when possible."""
        if not deadline or str(deadline).strip().lower() in ("", "no deadline"):
            return None
        try:
            return datetime.strptime(str(deadline).strip(), "%Y-%m-%d").date()
        except ValueError:
            try:
                return datetime.strptime(str(deadline).strip(), "%Y-%m-%d %H:%M:%S").date()
            except ValueError:
                return None

    def is_overdue(self, deadline, status):
        """Return True when a pending task is already overdue."""
        if not deadline or str(deadline).strip().lower() in ("", "no deadline"):
            return False
        if str(status).strip().lower() == "completed":
            return False
        parsed_deadline = self.parse_deadline(deadline)
        if parsed_deadline is None:
            return False
        return parsed_deadline < date.today()

    def get_badge_style(self, task):
        """Return display color and label information for a task card."""
        status = str(task[6]).strip().lower() if len(task) > 6 else "pending"
        priority = str(task[4]).strip().lower() if len(task) > 4 else "medium"
        deadline = task[5] if len(task) > 5 else ""

        if status == "completed":
            return ("#22c55e", "✓ Completed", "#22c55e")
        if self.is_overdue(deadline, status):
            return ("#f59e0b", "⚠ Overdue", "#f59e0b")
        if priority == "high":
            return ("#ef4444", "! High priority", "#ef4444")
        if status == "pending":
            return ("#3b82f6", "● Pending", "#3b82f6")
        return ("#64748b", "● Pending", "#64748b")

    # ======================================================
    # LOAD TASKS
    # ======================================================

    def load_tasks(self, force=False):
        self._tasks_loaded = True
        for widget in self.task_scrollable.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.task_scrollable, text="Loading tasks...", font=("Arial", 13)).pack(pady=20)
        run_in_background(
            self,
            self._load_tasks_data,
            callback=self._apply_tasks_data,
            error_callback=self._show_task_error,
        )

    def _load_tasks_data(self):
        tasks = self.database.get_all_tasks() if self.database else []
        status_filter = self.status_filter.get()
        priority_filter = self.priority_filter.get()
        planned_filter = self.planned_filter.get()
        progress_filter = self.progress_filter.get()
        sort_mode = self.sort_filter.get()
        keyword = self.search_entry.get().strip().lower()
        filtered_tasks = []

        for task in tasks:
            subject = str(task[1]).lower()
            title = str(task[2]).lower()
            priority = task[4]
            status = task[6]
            progress = int(task[7] or 0) if len(task) > 7 and task[7] is not None else 0
            planned_date = task[9] if len(task) > 9 else ""

            if status_filter != "All" and status != status_filter:
                continue
            if priority_filter != "All" and priority != priority_filter:
                continue
            if planned_filter == "Today":
                if not planned_date or self.parse_deadline(planned_date) != date.today():
                    continue
            elif planned_filter == "This Week":
                parsed = self.parse_deadline(planned_date)
                if parsed is None or parsed > date.today() + timedelta(days=7) or parsed < date.today():
                    continue
            elif planned_filter == "No Plan":
                if planned_date and str(planned_date).strip():
                    continue
            if progress_filter == "Not Started" and progress != 0:
                continue
            if progress_filter == "In Progress" and not (0 < progress < 100):
                continue
            if progress_filter == "Complete" and progress != 100:
                continue
            if keyword and keyword not in title and keyword not in subject:
                continue
            filtered_tasks.append(task)

        if sort_mode == "Priority":
            priority_order = {"High": 0, "Medium": 1, "Low": 2}
            filtered_tasks.sort(
                key=lambda task: (
                    priority_order.get(str(task[4]).strip(), 99),
                    str(task[2]).lower(),
                )
            )
        elif sort_mode == "Status":
            filtered_tasks.sort(
                key=lambda task: (
                    str(task[6]).lower(),
                    str(task[2]).lower(),
                )
            )
        elif sort_mode == "Planned date":
            filtered_tasks.sort(
                key=lambda task: (
                    self.parse_deadline(task[9]) is None,
                    self.parse_deadline(task[9]) or date.max,
                    str(task[2]).lower(),
                )
            )
        else:
            filtered_tasks.sort(
                key=lambda task: (
                    self.parse_deadline(task[5]) is None,
                    self.parse_deadline(task[5]) or date.max,
                    str(task[2]).lower(),
                )
            )
        return filtered_tasks

    def _apply_tasks_data(self, filtered_tasks):
        self._tasks_loaded = True
        for widget in self.task_scrollable.winfo_children():
            widget.destroy()
        if not filtered_tasks:
            ctk.CTkLabel(self.task_scrollable, text="No tasks found.", font=("Arial", 13)).pack(pady=40)
            return
        for task in filtered_tasks:
            self.create_task_card(task)


    # ======================================================
    # CREATE TASK CARD
    # ======================================================

    def create_task_card(self, task):
        """Create a task card with task details, badges, and action buttons."""

        task_id = task[0]
        subject = task[1]
        title = task[2]
        description = task[3]
        priority = task[4]
        deadline = task[5]
        status = task[6]
        progress = int(task[7] or 0) if len(task) > 7 and task[7] is not None else 0
        subtasks_json = task[8] if len(task) > 8 else "[]"
        planned_date = task[9] if len(task) > 9 else ""
        border_color, status_text, badge_color = self.get_badge_style(task)

        card = ctk.CTkFrame(
            self.task_scrollable,
            corner_radius=14,
            border_width=2,
            border_color=border_color
        )
        card.pack(fill="x", padx=10, pady=7)

        ctk.CTkLabel(
            card,
            text=status_text,
            text_color=badge_color,
            font=("Arial", 12, "bold"),
            anchor="w"
        ).pack(anchor="w", padx=18, pady=(12, 4))

        ctk.CTkLabel(
            card,
            text=title,
            font=("Arial", 16, "bold"),
            anchor="w"
        ).pack(anchor="w", padx=18, pady=(0, 3))

        ctk.CTkLabel(
            card,
            text=f"Subject: {subject}",
            anchor="w"
        ).pack(anchor="w", padx=18, pady=2)

        ctk.CTkLabel(
            card,
            text=f"Priority: {priority}",
            anchor="w"
        ).pack(anchor="w", padx=18, pady=2)

        ctk.CTkLabel(
            card,
            text=f"Deadline: {deadline}",
            anchor="w"
        ).pack(anchor="w", padx=18, pady=2)

        ctk.CTkLabel(
            card,
            text=f"Status: {status}",
            anchor="w"
        ).pack(anchor="w", padx=18, pady=2)

        ctk.CTkLabel(
            card,
            text=f"Planned: {planned_date or 'No plan'}",
            anchor="w"
        ).pack(anchor="w", padx=18, pady=2)

        ctk.CTkLabel(
            card,
            text=f"Progress: {progress}%",
            anchor="w"
        ).pack(anchor="w", padx=18, pady=2)

        progress_widget = ctk.CTkProgressBar(
            card,
            width=260
        )
        progress_widget.set(progress / 100)
        progress_widget.pack(anchor="w", padx=18, pady=(0, 10))

        subtasks = []
        try:
            subtasks = json.loads(subtasks_json or "[]")
        except (ValueError, TypeError):
            subtasks = []
        if subtasks:
            ctk.CTkLabel(
                card,
                text=f"Subtasks: {len(subtasks)}",
                anchor="w"
            ).pack(anchor="w", padx=18, pady=(0, 2))

        if self.is_overdue(deadline, status):
            ctk.CTkLabel(
                card,
                text="Overdue",
                text_color="#f59e0b",
                font=("Arial", 12, "bold"),
                anchor="w"
            ).pack(anchor="w", padx=18, pady=(2, 6))

        button_frame = ctk.CTkFrame(card, fg_color="transparent")
        button_frame.pack(fill="x", padx=15, pady=(4, 15))

        ctk.CTkButton(
            button_frame,
            text="Edit",
            width=80,
            command=lambda: self.select_task(task)
        ).pack(side="left", padx=5)

        if str(status).strip().lower() == "pending":
            ctk.CTkButton(
                button_frame,
                text="Complete",
                width=100,
                command=lambda: self.complete_specific_task(task_id)
            ).pack(side="left", padx=5)
        else:
            ctk.CTkButton(
                button_frame,
                text="Reopen",
                width=100,
                command=lambda: self.reopen_specific_task(task_id)
            ).pack(side="left", padx=5)


    # ======================================================
    # ADD TASK
    # ======================================================

    def add_task(self):

        try:
            subject = self.subject_combobox.get().strip() or "General"
            title = validate_required_field(self.title_entry.get(), "Task title")
            description = self.description_textbox.get("1.0", "end").strip()
            priority = self.priority_combobox.get() or "Medium"
            deadline = self.deadline_entry.get().strip()
            deadline = validate_date_string(deadline, "Deadline") if deadline else "No Deadline"
            planned_date = self.planned_date_entry.get().strip()
            planned_date = validate_date_string(planned_date, "Planned Date") if planned_date else ""
            progress = int(self.progress_slider.get() or 0)
            subtasks_list = [
                item.strip()
                for item in self.subtasks_textbox.get("1.0", "end").splitlines()
                if item.strip()
            ]
            subtasks_json = json.dumps(subtasks_list)

            task = StudyTask(
                subject=subject,
                title=title,
                description=description,
                priority=priority,
                deadline=deadline,
                status="Pending",
            )

            success = self.database.add_task(
                task.get_subject(),
                task.get_title(),
                task.get_description(),
                task.get_priority(),
                task.get_deadline(),
                task.get_status(),
                progress=progress,
                subtasks_json=subtasks_json,
                planned_date=planned_date,
            )
            if success:
                messagebox.showinfo("Success", "Task added successfully.")
                self.clear_form()
                self.load_tasks()
            else:
                raise RuntimeError("Unable to add task. Please try again.")
        except ValidationError as error:
            messagebox.showwarning("Validation Error", str(error))
        except RuntimeError as error:
            friendly_message = handle_operation_error(
                error,
                context="adding task",
                user_message="We couldn't add the task. Please try again.",
            )
            messagebox.showerror("Error", friendly_message)
        except Exception as error:
            friendly_message = handle_operation_error(
                error,
                context="adding task",
                user_message="We couldn't add the task. Please try again.",
            )
            messagebox.showerror("Unexpected Error", friendly_message)


    # ======================================================
    # SELECT TASK
    # ======================================================

    def select_task(

        self,

        task

    ):

        self.selected_task_id = task[0]


        self.subject_combobox.set(

            task[1]

        )


        self.title_entry.delete(

            0,

            "end"

        )


        self.title_entry.insert(

            0,

            task[2]

        )


        self.description_textbox.delete(

            "1.0",

            "end"

        )


        self.description_textbox.insert(

            "1.0",

            task[3]

        )


        self.priority_combobox.set(

            task[4]

        )


        self.deadline_entry.delete(

            0,

            "end"

        )


        self.deadline_entry.insert(

            0,

            task[5]

        )

        progress_value = int(task[7] or 0) if len(task) > 7 and task[7] is not None else 0
        self.progress_slider.set(progress_value)
        self.progress_label.configure(text=f"{progress_value}%")

        self.planned_date_entry.delete(
            0,
            "end"
        )
        self.planned_date_entry.insert(
            0,
            task[9] if len(task) > 9 and task[9] is not None else ""
        )

        subtasks_value = ""
        try:
            subtasks_list = json.loads(task[8] if len(task) > 8 else "[]")
            if isinstance(subtasks_list, list):
                subtasks_value = "\n".join(str(item) for item in subtasks_list)
        except (ValueError, TypeError):
            subtasks_value = ""

        self.subtasks_textbox.delete(
            "1.0",
            "end"
        )
        self.subtasks_textbox.insert(
            "1.0",
            subtasks_value
        )

        self.add_button.configure(

            state="disabled"

        )


        self.update_button.configure(

            state="normal"

        )


        self.delete_button.configure(

            state="normal"

        )


        self.complete_button.configure(

            state="normal"

        )


    # ======================================================
    # UPDATE TASK
    # ======================================================

    def update_task(self):

        if not self.selected_task_id:
            messagebox.showwarning("Warning", "Please select a task first.")
            return

        try:
            subject = self.subject_combobox.get().strip() or "General"
            title = validate_required_field(self.title_entry.get(), "Task title")
            description = self.description_textbox.get("1.0", "end").strip()
            priority = self.priority_combobox.get() or "Medium"
            deadline = self.deadline_entry.get().strip()
            deadline = validate_date_string(deadline, "Deadline") if deadline else "No Deadline"

            planned_date = self.planned_date_entry.get().strip()
            planned_date = validate_date_string(planned_date, "Planned Date") if planned_date else ""
            progress = int(self.progress_slider.get() or 0)
            subtasks_list = [
                item.strip()
                for item in self.subtasks_textbox.get("1.0", "end").splitlines()
                if item.strip()
            ]
            subtasks_json = json.dumps(subtasks_list)

            success = self.database.update_task(
                self.selected_task_id,
                subject,
                title,
                description,
                priority,
                deadline,
                progress=progress,
                subtasks_json=subtasks_json,
                planned_date=planned_date,
            )
            if success:
                messagebox.showinfo("Success", "Task updated successfully.")
                self.clear_form()
                self.load_tasks()
                request_analytics_refresh()
            else:
                raise RuntimeError("Unable to update task. Please try again.")
        except ValidationError as error:
            messagebox.showwarning("Validation Error", str(error))
        except RuntimeError as error:
            friendly_message = handle_operation_error(
                error,
                context="updating task",
                user_message="We couldn't update the task. Please try again.",
            )
            messagebox.showerror("Error", friendly_message)
        except Exception as error:
            friendly_message = handle_operation_error(
                error,
                context="updating task",
                user_message="We couldn't update the task. Please try again.",
            )
            messagebox.showerror("Unexpected Error", friendly_message)


    # ======================================================
    # DELETE TASK
    # ======================================================

    def delete_task(self):

        if not self.selected_task_id:

            messagebox.showwarning(

                "Warning",

                "Please select a task first."

            )

            return


        answer = messagebox.askyesno(

            "Confirm Delete",

            "Are you sure you want to delete this task?"

        )


        if not answer:

            return


        success = (

            self.database
            .delete_task(

                self.selected_task_id

            )

        )


        if success:

            messagebox.showinfo(

                "Success",

                "Task deleted successfully."

            )


            self.clear_form()

            self.load_tasks()
            request_analytics_refresh()


        else:

            messagebox.showerror(

                "Error",

                "Unable to delete task."

            )


    # ======================================================
    # COMPLETE SELECTED TASK
    # ======================================================

    def complete_task(self):

        if not self.selected_task_id:

            messagebox.showwarning(

                "Warning",

                "Please select a task first."

            )

            return


        success = (

            self.database
            .complete_task(

                self.selected_task_id

            )

        )


        if success:

            messagebox.showinfo(

                "Success",

                "Task marked as completed."

            )


            self.clear_form()

            self.load_tasks()
            request_analytics_refresh()


    # ======================================================
    # COMPLETE SPECIFIC TASK
    # ======================================================

    def complete_specific_task(

        self,

        task_id

    ):

        success = (

            self.database
            .complete_task(

                task_id

            )

        )


        if success:

            self.load_tasks()
            request_analytics_refresh()


    # ======================================================
    # REOPEN TASK
    # ======================================================

    def reopen_specific_task(

        self,

        task_id

    ):

        success = (

            self.database
            .reopen_task(

                task_id

            )

        )


        if success:

            self.load_tasks()
            request_analytics_refresh()


    # ======================================================
    # SEARCH TASK
    # ======================================================

    def search_tasks(

        self,

        event=None

    ):

        self.load_tasks()


    # ======================================================
    # CLEAR FORM
    # ======================================================

    def clear_form(self):

        self.selected_task_id = None


        self.title_entry.delete(

            0,

            "end"

        )


        self.description_textbox.delete(

            "1.0",

            "end"

        )


        self.deadline_entry.delete(

            0,

            "end"

        )

        self.priority_combobox.set(

            "Medium"

        )

        self.progress_slider.set(0)
        self.progress_label.configure(text="0%")
        self.planned_date_entry.delete(0, "end")
        self.subtasks_textbox.delete("1.0", "end")

        self.add_button.configure(

            state="normal"

        )


        self.update_button.configure(

            state="disabled"

        )


        self.delete_button.configure(

            state="disabled"

        )


        self.complete_button.configure(

            state="disabled"

        )