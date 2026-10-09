import customtkinter as ctk
from tkinter import messagebox
from datetime import datetime
from database import DatabaseManager
from models import StudySession

class TimerWindow(ctk.CTkToplevel):
    """
    Pomodoro Study Timer.

    OOP Concepts:
    - Class
    - Object
    - Inheritance
    - Encapsulation
    - Method
    """

    def __init__(self, parent):

        super().__init__(parent)

        self.parent = parent

        self.database = DatabaseManager()

        # ==================================================
        # TIMER SETTINGS
        # ==================================================

        self.study_minutes = 25

        self.break_minutes = 5


        self.total_seconds = (

            self.study_minutes * 60

        )


        self.remaining_seconds = (

            self.total_seconds

        )


        self.timer_running = False

        self.is_break = False

        self.timer_id = None

        self.seconds = 0

        self.session_start_time = None


        self.title(

            "Study Tracker Pro - Study Timer"

        )


        self.geometry(

            "700x650"

        )


        self.minsize(

            540,

            500

        )

        self.resizable(

            True,

            True

        )


        self.protocol(

            "WM_DELETE_WINDOW",

            self.close_window

        )


        self.create_layout()

        self.load_subjects()


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

        self.create_timer_area()

        self.create_control_area()

        self.create_session_area()


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

            padx=30,

            pady=(25, 10)

        )


        self.header_frame.grid_columnconfigure(

            0,

            weight=1

        )


        ctk.CTkLabel(

            self.header_frame,

            text="Study Timer",

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

                "Focus on your study goals."

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
    # TIMER AREA
    # ======================================================

    def create_timer_area(self):

        self.timer_frame = ctk.CTkFrame(

            self

        )


        self.timer_frame.grid(

            row=1,

            column=0,

            sticky="nsew",

            padx=30,

            pady=15

        )


        self.timer_frame.grid_columnconfigure(

            0,

            weight=1

        )


        self.timer_frame.grid_rowconfigure(

            1,

            weight=1

        )


        # --------------------------------------------------
        # Timer Mode
        # --------------------------------------------------

        self.mode_label = ctk.CTkLabel(

            self.timer_frame,

            text="STOPWATCH",

            font=(

                "Arial",

                20,

                "bold"

            )

        )


        self.mode_label.grid(

            row=0,

            column=0,

            pady=(30, 10)

        )


        # --------------------------------------------------
        # Timer Display
        # --------------------------------------------------

        self.timer_label = ctk.CTkLabel(

            self.timer_frame,

            text="00:00:00",

            font=(

                "Arial",

                90,

                "bold"

            )

        )


        self.timer_label.grid(

            row=1,

            column=0,

            pady=20

        )


        # --------------------------------------------------
        # Progress Bar
        # --------------------------------------------------

        self.progress_bar = ctk.CTkProgressBar(

            self.timer_frame,

            width=450

        )


        self.progress_bar.grid(

            row=2,

            column=0,

            pady=20

        )


        self.progress_bar.set(

            0

        )


    # ======================================================
    # CONTROL AREA
    # ======================================================

    def create_control_area(self):

        self.control_frame = ctk.CTkFrame(

            self,

            fg_color="transparent"

        )


        self.control_frame.grid(

            row=2,

            column=0,

            padx=30,

            pady=15

        )


        self.start_button = ctk.CTkButton(

            self.control_frame,

            text="Start",

            width=120,

            height=40,

            command=self.start_timer

        )


        self.start_button.pack(

            side="left",

            padx=5

        )


        self.pause_button = ctk.CTkButton(

            self.control_frame,

            text="Pause",

            width=120,

            height=40,

            command=self.pause_timer,

            state="disabled"

        )


        self.pause_button.pack(

            side="left",

            padx=5

        )


        self.reset_button = ctk.CTkButton(

            self.control_frame,

            text="Reset",

            width=120,

            height=40,

            command=self.reset_timer

        )


        self.reset_button.pack(

            side="left",

            padx=5

        )


    # ======================================================
    # SESSION AREA
    # ======================================================

    def create_session_area(self):

        self.session_frame = ctk.CTkFrame(

            self

        )


        self.session_frame.grid(

            row=3,

            column=0,

            sticky="ew",

            padx=30,

            pady=(5, 25)

        )


        ctk.CTkLabel(

            self.session_frame,

            text="Study Session Information",

            font=(

                "Arial",

                17,

                "bold"

            )

        ).pack(

            anchor="w",

            padx=20,

            pady=(15, 10)

        )


        # --------------------------------------------------
        # Subject Selection
        # --------------------------------------------------

        ctk.CTkLabel(

            self.session_frame,

            text="Select Subject"

        ).pack(

            anchor="w",

            padx=20

        )


        self.subject_combobox = ctk.CTkComboBox(

            self.session_frame,

            width=300,

            values=[

                "No Subject"

            ]

        )


        self.subject_combobox.pack(

            anchor="w",

            padx=20,

            pady=(5, 15)

        )


        # --------------------------------------------------
        # Session Status
        # --------------------------------------------------

        self.session_status_label = ctk.CTkLabel(

            self.session_frame,

            text="Ready to start studying."

        )


        self.session_status_label.pack(

            anchor="w",

            padx=20,

            pady=(5, 15)

        )


    # ======================================================
    # LOAD SUBJECTS
    # ======================================================

    def load_subjects(self):

        subjects = (

            self.database

            .get_all_subjects()

        )


        subject_names = [

            subject[1]

            for subject in subjects

        ]


        if not subject_names:

            subject_names = [

                "No Subject"

            ]


        self.subject_combobox.configure(

            values=subject_names

        )


        self.subject_combobox.set(

            subject_names[0]

        )


    # ======================================================
    # START TIMER
    # ======================================================

    def format_time(self, sec):

        hours = str(sec // 3600).zfill(2)

        minutes = str((sec % 3600) // 60).zfill(2)

        seconds = str(sec % 60).zfill(2)

        return f"{hours}:{minutes}:{seconds}"


    def update_timer_display(self):

        self.timer_label.configure(

            text=self.format_time(self.seconds)

        )


    def start_timer(self):

        if self.timer_running:

            return


        self.timer_running = True

        self.session_start_time = datetime.now()

        self.start_button.configure(state="disabled")

        self.pause_button.configure(state="normal")

        self.mode_label.configure(text="STOPWATCH")

        self.session_status_label.configure(

            text="Study session is in progress..."

        )

        self.tick_timer()


    def tick_timer(self):

        if not self.timer_running:

            return

        self.seconds += 1

        self.update_timer_display()

        self.progress_bar.set(min(self.seconds / 3600, 1.0))

        self.timer_id = self.after(1000, self.tick_timer)


    def pause_timer(self):

        self.timer_running = False

        if self.timer_id:

            self.after_cancel(self.timer_id)

            self.timer_id = None

        self.pause_button.configure(state="disabled")

        self.start_button.configure(state="normal")

        if self.seconds > 0:

            self.save_study_session(self.seconds)

        self.session_status_label.configure(

            text="Timer paused."

        )


    def reset_timer(self):

        self.timer_running = False

        if self.timer_id:

            self.after_cancel(self.timer_id)

            self.timer_id = None

        self.seconds = 0

        self.mode_label.configure(text="STOPWATCH")

        self.timer_label.configure(text="00:00:00")

        self.progress_bar.set(0)

        self.start_button.configure(state="normal")

        self.pause_button.configure(state="disabled")

        self.session_status_label.configure(

            text="Timer reset."

        )


    # ======================================================
    # SAVE STUDY SESSION
    # ======================================================

    def save_study_session(self, duration_seconds=None):

        subject = (

            self.subject_combobox

            .get()

        )


        if duration_seconds is not None:

            duration = max(1, duration_seconds // 60)

        else:

            duration = self.study_minutes


        session_date = (

            datetime.now()

            .strftime(

                "%Y-%m-%d"

            )

        )


        # OOP OBJECT

        session = StudySession(

            subject=subject,

            duration=duration,

            study_date=session_date

        )


        success = (

            self.database

            .add_study_session(

                session.get_subject(),

                session.get_duration(),

                session.get_session_date()

            )

        )


        if success:

            print(

                "Study session saved successfully."

            )

        else:

            print(

                "Unable to save study session."

            )


    # ======================================================
    # CLOSE WINDOW
    # ======================================================

    def close_window(self):

        if self.timer_id:

            self.after_cancel(

                self.timer_id

            )


        self.destroy()