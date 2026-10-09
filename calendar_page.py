import customtkinter as ctk

from tkinter import messagebox

import calendar

from datetime import datetime, date


from database import DatabaseManager
from utils import run_in_background, handle_operation_error


# ==========================================================
# CALENDAR WINDOW
# ==========================================================

class CalendarWindow(ctk.CTkFrame):
    """
    Calendar page for Study Tracker Pro.
    """

    def __init__(

        self,

        parent,

        database=None

    ):

        super().__init__(parent)


        self.parent = parent


        self.database = database or DatabaseManager()


        # --------------------------------------------------
        # Current Date
        # --------------------------------------------------

        current_date = datetime.now()


        self.current_year = (

            current_date.year

        )


        self.current_month = (

            current_date.month

        )


        self.selected_date = (

            current_date.strftime(

                "%Y-%m-%d"

            )

        )


        self.create_layout()


        self.bind("<Configure>", self.on_resize)

        self.display_calendar()
        self.display_tasks_for_date(self.selected_date)
        self.update_upcoming_deadlines()
        self.update_session_summary()


    # ======================================================
    # CREATE LAYOUT
    # ======================================================

    def create_layout(self):
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=0)
        self.grid_rowconfigure(1, weight=1)
        self.grid_rowconfigure(2, weight=0)

        self.create_header()
        self.create_calendar_area()
        self.create_task_area()
        self.create_event_area()

    def on_resize(self, event=None):
        if not hasattr(self, "task_frame"):
            return
        width = self.winfo_width()
        if width < 1000:
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=0)
            self.task_frame.grid_remove()
            self.task_frame.grid_configure(row=2, column=0, columnspan=2, sticky="nsew")
            self.task_frame.grid()
        else:
            self.grid_columnconfigure(0, weight=1)
            self.grid_columnconfigure(1, weight=1)
            self.task_frame.grid_remove()
            self.task_frame.grid_configure(row=1, column=1, sticky="nsew")
            self.task_frame.grid()


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

            columnspan=2,

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

            text="Study Calendar",

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

                "View your tasks and deadlines."

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


        ctk.CTkButton(

            self.header_frame,

            text="Today",

            width=100,

            command=self.go_to_today

        ).grid(

            row=0,

            column=1,

            rowspan=2,

            padx=10

        )


    # ======================================================
    # CALENDAR AREA
    # ======================================================

    def create_calendar_area(self):

        self.calendar_frame = ctk.CTkFrame(

            self

        )


        self.calendar_frame.grid(
            row=1,
            column=0,
            sticky="nsew",
            padx=(25, 10),
            pady=15
        )


        self.calendar_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.calendar_frame.grid_rowconfigure(

            1,

            weight=1

        )


        # --------------------------------------------------
        # Month Navigation
        # --------------------------------------------------

        self.month_navigation = ctk.CTkFrame(

            self.calendar_frame,

            fg_color="transparent"

        )


        self.month_navigation.grid(

            row=0,

            column=0,

            sticky="ew",

            padx=20,

            pady=20

        )


        self.month_navigation.grid_columnconfigure(

            1,

            weight=1

        )


        ctk.CTkButton(

            self.month_navigation,

            text="<",

            width=50,

            command=self.previous_month

        ).grid(

            row=0,

            column=0,

            padx=5

        )


        self.month_label = ctk.CTkLabel(

            self.month_navigation,

            text="",

            font=(

                "Arial",

                22,

                "bold"

            )

        )


        self.month_label.grid(

            row=0,

            column=1

        )


        ctk.CTkButton(

            self.month_navigation,

            text=">",

            width=50,

            command=self.next_month

        ).grid(

            row=0,

            column=2,

            padx=5

        )


        # --------------------------------------------------
        # Calendar Grid
        # --------------------------------------------------

        self.calendar_grid = ctk.CTkFrame(

            self.calendar_frame

        )


        self.calendar_grid.grid(

            row=1,

            column=0,

            sticky="nsew",

            padx=20,

            pady=(0, 20)

        )


        for column in range(7):

            self.calendar_grid.grid_columnconfigure(

                column,

                weight=1

            )


        for row in range(7):

            self.calendar_grid.grid_rowconfigure(

                row,

                weight=1

            )


    # ======================================================
    # TASK AREA
    # ======================================================

    def create_task_area(self):

        self.task_frame = ctk.CTkFrame(

            self

        )


        self.task_frame.grid(
            row=1,
            column=1,
            sticky="nsew",
            padx=(10, 25),
            pady=15
        )
        self.task_frame.grid_propagate(False)


        self.task_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.task_frame.grid_rowconfigure(

            1,

            weight=1

        )


        self.selected_date_label = ctk.CTkLabel(

            self.task_frame,

            text="",

            font=(

                "Arial",

                20,

                "bold"

            )

        )


        self.selected_date_label.grid(

            row=0,

            column=0,

            sticky="w",

            padx=20,

            pady=20

        )

        self.upcoming_label = ctk.CTkLabel(
            self.task_frame,
            text="Upcoming deadlines",
            font=("Arial", 15, "bold")
        )
        self.upcoming_label.grid(row=1, column=0, sticky="w", padx=20, pady=(0, 8))

        self.upcoming_scrollable = ctk.CTkScrollableFrame(self.task_frame, height=150)
        self.upcoming_scrollable.grid(row=2, column=0, sticky="ew", padx=10, pady=(0, 10))

        self.daily_tasks_scrollable = ctk.CTkScrollableFrame(
            self.task_frame,
            height=220
        )

        self.daily_tasks_scrollable.grid(
            row=3,
            column=0,
            sticky="nsew",
            padx=10,
            pady=10
        )
        self.daily_tasks_scrollable.grid_columnconfigure(0, weight=1)

    def create_event_area(self):
        self.event_frame = ctk.CTkFrame(self)
        self.event_frame.grid(row=2, column=0, columnspan=2, sticky="ew", padx=25, pady=(0, 20))
        self.event_frame.grid_columnconfigure(0, weight=1)
        self.event_frame.grid_columnconfigure(1, weight=0)
        self.event_frame.grid_columnconfigure(2, weight=0)

        ctk.CTkLabel(self.event_frame, text="Quick study event", font=("Arial", 16, "bold")).grid(row=0, column=0, columnspan=3, sticky="w", padx=20, pady=(15, 10))

        self.event_entry = ctk.CTkEntry(self.event_frame, width=280, placeholder_text="e.g. Review notes")
        self.event_entry.grid(row=1, column=0, padx=20, pady=(0, 10), sticky="ew")

        self.event_date_entry = ctk.CTkEntry(self.event_frame, width=180, placeholder_text="YYYY-MM-DD")
        self.event_date_entry.grid(row=1, column=1, padx=(10, 20), pady=(0, 10), sticky="w")
        self.event_date_entry.insert(0, self.selected_date)

        ctk.CTkButton(self.event_frame, text="Add Event", width=140, command=self.add_study_event).grid(row=1, column=2, padx=(0, 20), pady=(0, 10))

        self.session_summary_label = ctk.CTkLabel(self.event_frame, text="", justify="left", wraplength=600)
        self.session_summary_label.grid(row=2, column=0, columnspan=3, sticky="w", padx=20, pady=(0, 15))


    # ======================================================
    # DISPLAY CALENDAR
    # ======================================================

    def display_calendar(self):

        # Clear old calendar widgets

        for widget in (

            self.calendar_grid

            .winfo_children()

        ):

            widget.destroy()


        month_name = calendar.month_name[

            self.current_month

        ]


        self.month_label.configure(

            text=(

                f"{month_name} "

                f"{self.current_year}"

            )

        )


        # --------------------------------------------------
        # Tuple Data Structure
        # --------------------------------------------------

        weekdays = (

            "Monday",

            "Tuesday",

            "Wednesday",

            "Thursday",

            "Friday",

            "Saturday",

            "Sunday"

        )


        for column, day_name in enumerate(

            weekdays

        ):

            ctk.CTkLabel(

                self.calendar_grid,

                text=day_name[:3],

                font=(

                    "Arial",

                    13,

                    "bold"

                )

            ).grid(

                row=0,

                column=column,

                sticky="nsew",

                padx=2,

                pady=2

            )


        # --------------------------------------------------
        # Calendar Matrix
        # --------------------------------------------------

        month_calendar = calendar.monthcalendar(

            self.current_year,

            self.current_month

        )


        for row_index, week in enumerate(

            month_calendar,

            start=1

        ):


            for column_index, day in enumerate(

                week

            ):


                if day == 0:

                    empty_label = ctk.CTkLabel(

                        self.calendar_grid,

                        text=""

                    )


                    empty_label.grid(

                        row=row_index,

                        column=column_index,

                        sticky="nsew",

                        padx=2,

                        pady=2

                    )


                    continue


                date_string = (

                    f"{self.current_year}-"

                    f"{self.current_month:02d}-"

                    f"{day:02d}"

                )


                day_button = ctk.CTkButton(

                    self.calendar_grid,

                    text=str(day),

                    height=60,

                    command=lambda date=date_string:

                    self.select_date(

                        date

                    )

                )


                day_button.grid(

                    row=row_index,

                    column=column_index,

                    sticky="nsew",

                    padx=2,

                    pady=2

                )


                # Highlight today's date

                today = datetime.now().strftime(

                    "%Y-%m-%d"

                )


                if date_string == today:

                    day_button.configure(

                        border_width=2

                    )


                # Highlight selected date

                if date_string == self.selected_date:

                    day_button.configure(

                        fg_color=ctk.ThemeManager

                        .theme["CTkButton"]

                        ["hover_color"]

                    )


    # ======================================================
    # SELECT DATE
    # ======================================================

    def select_date(

        self,

        date_string

    ):

        self.selected_date = date_string
        self.event_date_entry.delete(0, "end")
        self.event_date_entry.insert(0, date_string)

        self.display_calendar()
        run_in_background(
            self,
            self._load_date_details,
            callback=self._apply_date_details,
            error_callback=self._show_calendar_error,
            date_string=date_string,
        )

    def _load_date_details(self, date_string):
        tasks = self.database.get_tasks_for_date(date_string) if self.database else []
        sessions = self.database.get_study_sessions_by_date(date_string) if self.database else []
        daily_tasks = []
        session_items = []
        for task in tasks:
            deadline = task[5]
            if str(deadline) == str(date_string):
                daily_tasks.append(task)
        for session in sessions:
            if len(session) >= 3 and str(session[3]) == str(date_string):
                session_items.append(session)
        return date_string, daily_tasks, session_items

    def _apply_date_details(self, payload):
        if not payload:
            return
        date_string, daily_tasks, session_items = payload
        self._render_date_details(date_string, daily_tasks, session_items)

    def _render_date_details(self, date_string, daily_tasks, session_items):
        for widget in self.daily_tasks_scrollable.winfo_children():
            widget.destroy()
        self.selected_date_label.configure(text=f"Tasks for {date_string}")
        if not daily_tasks:
            ctk.CTkLabel(self.daily_tasks_scrollable, text="No tasks for this date.").pack(pady=40)
            return
        for task in daily_tasks:
            self.create_daily_task_card(task)
        if session_items:
            ctk.CTkLabel(
                self.daily_tasks_scrollable,
                text="Study sessions",
                font=("Arial", 14, "bold")
            ).pack(anchor="w", padx=15, pady=(10, 5))
            for session in session_items:
                ctk.CTkLabel(
                    self.daily_tasks_scrollable,
                    text=f"• {session[1]} • {session[2]} min",
                    anchor="w"
                ).pack(anchor="w", padx=15, pady=2)

    def _show_calendar_error(self, error, safe_message=None):
        friendly_message = safe_message or handle_operation_error(
            error,
            context="refreshing calendar",
            user_message="We couldn't refresh the calendar right now.",
        )
        messagebox.showerror("Calendar Error", friendly_message)


    # ======================================================
    # DISPLAY TASKS FOR SELECTED DATE
    # ======================================================

    def display_tasks_for_date(

        self,

        date_string

    ):
        self.selected_date_label.configure(text=f"Tasks for {date_string}")
        self.daily_tasks_scrollable.winfo_children()
        run_in_background(
            self,
            self._load_date_details,
            callback=self._apply_date_details,
            error_callback=self._show_calendar_error,
            date_string=date_string,
        )


    # ======================================================
    # CREATE DAILY TASK CARD
    # ======================================================

    def create_daily_task_card(

        self,

        task

    ):

        task_id = task[0]

        subject = task[1]

        title = task[2]

        description = task[3]

        priority = task[4]

        deadline = task[5]

        status = task[6]


        card = ctk.CTkFrame(

            self.daily_tasks_scrollable

        )


        card.pack(

            fill="x",

            padx=5,

            pady=7

        )


        ctk.CTkLabel(

            card,

            text=title,

            font=(

                "Arial",

                16,

                "bold"

            ),

            anchor="w"

        ).pack(

            anchor="w",

            padx=15,

            pady=(15, 5)

        )


        ctk.CTkLabel(

            card,

            text=(

                f"Subject: {subject}"

            ),

            anchor="w"

        ).pack(

            anchor="w",

            padx=15,

            pady=2

        )


        ctk.CTkLabel(

            card,

            text=(

                f"Priority: {priority}"

            ),

            anchor="w"

        ).pack(

            anchor="w",

            padx=15,

            pady=2

        )


        ctk.CTkLabel(

            card,

            text=(

                f"Status: {status}"

            ),

            anchor="w"

        ).pack(

            anchor="w",

            padx=15,

            pady=(2, 15)

        )


    # ======================================================
    # PREVIOUS MONTH
    # ======================================================

    def update_upcoming_deadlines(self):
        run_in_background(
            self,
            self._load_upcoming_deadlines,
            callback=self._apply_upcoming_deadlines,
            error_callback=self._show_calendar_error,
        )

    def _load_upcoming_deadlines(self):
        today = date.today().strftime("%Y-%m-%d")
        tasks = self.database.get_upcoming_tasks(from_date=today, limit=None) if self.database else []
        upcoming = []
        for task in tasks:
            deadline = str(task[5]).strip()
            if deadline and deadline.lower() != "no deadline":
                try:
                    parsed = datetime.strptime(deadline, "%Y-%m-%d").date()
                    upcoming.append((parsed, task))
                except ValueError:
                    continue
        upcoming.sort(key=lambda item: item[0])
        return upcoming

    def _apply_upcoming_deadlines(self, upcoming):
        for widget in self.upcoming_scrollable.winfo_children():
            widget.destroy()
        if not upcoming:
            ctk.CTkLabel(self.upcoming_scrollable, text="No upcoming deadlines.").pack(anchor="w", padx=10, pady=10)
            return
        for parsed_date, task in upcoming[:5]:
            ctk.CTkLabel(
                self.upcoming_scrollable,
                text=f"{parsed_date} • {task[2]} ({task[4]})",
                anchor="w"
            ).pack(anchor="w", padx=10, pady=3)

    def update_session_summary(self):
        run_in_background(
            self,
            self._load_session_summary,
            callback=self._apply_session_summary,
            error_callback=self._show_calendar_error,
        )

    def _load_session_summary(self):
        sessions = self.database.get_all_study_sessions() if self.database else []
        total_minutes = sum(int(session[2]) for session in sessions if len(session) > 2)
        return len(sessions), total_minutes

    def _apply_session_summary(self, payload):
        if not payload:
            return
        session_count, total_minutes = payload
        self.session_summary_label.configure(text=f"Completed study sessions: {session_count} • Total minutes tracked: {total_minutes}")

    def add_study_event(self):
        event_name = self.event_entry.get().strip()
        event_date = self.event_date_entry.get().strip()
        if not event_name:
            messagebox.showwarning("Validation", "Please enter a study event name.")
            return
        if not event_date:
            event_date = self.selected_date
        try:
            datetime.strptime(event_date, "%Y-%m-%d")
        except ValueError:
            messagebox.showerror("Validation", "Please use YYYY-MM-DD format.")
            return
        self.database.add_task("Calendar", event_name, f"Study event for {event_date}", "Medium", event_date, "Pending")
        self.event_entry.delete(0, "end")
        self.display_tasks_for_date(event_date)
        self.update_upcoming_deadlines()

    def previous_month(self):

        self.current_month -= 1


        if self.current_month < 1:

            self.current_month = 12

            self.current_year -= 1


        self.display_calendar()


    # ======================================================
    # NEXT MONTH
    # ======================================================

    def next_month(self):

        self.current_month += 1


        if self.current_month > 12:

            self.current_month = 1

            self.current_year += 1


        self.display_calendar()


    # ======================================================
    # GO TO TODAY
    # ======================================================

    def go_to_today(self):

        today = datetime.now()


        self.current_year = today.year

        self.current_month = today.month


        self.selected_date = today.strftime(

            "%Y-%m-%d"

        )


        self.display_calendar()


        self.display_tasks_for_date(

            self.selected_date

        )