import customtkinter as ctk

from datetime import datetime, date, timedelta
from tkinter import StringVar

try:
    import winsound
except ImportError:
    winsound = None

from analytics import request_analytics_refresh
from database import DatabaseManager

from models import StudySession


# ==========================================================
# TIMER WINDOW
# ==========================================================

class TimerWindow(ctk.CTkFrame):
    """
    Pomodoro Study Timer page.
    """

    def __init__(self, parent, database=None):

        super().__init__(parent)

        self.parent = parent

        self.database = database or DatabaseManager()


        # ==================================================
        # TIMER SETTINGS
        # ==================================================

        self.study_minutes = 25
        self.break_minutes = 5
        self.long_break_minutes = 15
        self.focus_minutes = 25
        self.short_break_minutes = 5
        self.pomodoro_enabled = True
        self.sound_enabled = True
        self.current_pomodoro_type = "focus"
        self.pomodoro_cycle_count = 0

        self.total_seconds = self.study_minutes * 60
        self.remaining_seconds = self.total_seconds

        self.timer_running = False
        self.timer_paused = False
        self.timer_mode = "STOPWATCH"
        self.stopwatch_seconds = 0
        self.countdown_hours = 0
        self.countdown_minutes = 25
        self.countdown_seconds = 0

        self.is_break = False
        self.timer_id = None
        self.session_start_time = None
        self.session_elapsed_seconds = 0
        self.elapsed_seconds = 0


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

            4,

            weight=1

        )


        # --------------------------------------------------
        # Timer Mode Selector
        # --------------------------------------------------

        self.timer_mode_prompt = ctk.CTkLabel(

            self.timer_frame,

            text="Timer Mode",

            font=(

                "Arial",

                20,

                "bold"

            )

        )


        self.timer_mode_prompt.grid(

            row=0,

            column=0,

            pady=(30, 5)

        )


        self.timer_mode_var = StringVar(

            value=self.timer_mode

        )


        self.mode_option_menu = ctk.CTkOptionMenu(

            self.timer_frame,

            values=[

                "STOPWATCH",

                "COUNTDOWN"

            ],

            variable=self.timer_mode_var,

            command=self.on_timer_mode_changed,

            width=200

        )


        self.mode_option_menu.grid(

            row=1,

            column=0,

            pady=(0, 10)

        )


        self.countdown_frame = ctk.CTkFrame(

            self.timer_frame,

            fg_color="transparent"

        )


        self.countdown_frame.grid(

            row=2,

            column=0,

            pady=(0, 10)

        )


        self.countdown_frame.grid_columnconfigure(

            0,

            weight=1

        )

        self.countdown_frame.grid_columnconfigure(

            1,

            weight=1

        )

        self.countdown_frame.grid_columnconfigure(

            2,

            weight=1

        )


        self.countdown_hours_var = StringVar(

            value=str(self.countdown_hours)

        )

        self.countdown_minutes_var = StringVar(

            value=str(self.countdown_minutes)

        )

        self.countdown_seconds_var = StringVar(

            value=str(self.countdown_seconds)

        )


        ctk.CTkLabel(

            self.countdown_frame,

            text="Hours"

        ).grid(

            row=0,

            column=0,

            padx=5,

            sticky="w"

        )


        ctk.CTkLabel(

            self.countdown_frame,

            text="Minutes"

        ).grid(

            row=0,

            column=1,

            padx=5,

            sticky="w"

        )


        ctk.CTkLabel(

            self.countdown_frame,

            text="Seconds"

        ).grid(

            row=0,

            column=2,

            padx=5,

            sticky="w"

        )


        self.hours_entry = ctk.CTkEntry(

            self.countdown_frame,

            width=80,

            textvariable=self.countdown_hours_var

        )


        self.hours_entry.grid(

            row=1,

            column=0,

            padx=5,

            pady=(5, 0)

        )


        self.minutes_entry = ctk.CTkEntry(

            self.countdown_frame,

            width=80,

            textvariable=self.countdown_minutes_var

        )


        self.minutes_entry.grid(

            row=1,

            column=1,

            padx=5,

            pady=(5, 0)

        )


        self.seconds_entry = ctk.CTkEntry(

            self.countdown_frame,

            width=80,

            textvariable=self.countdown_seconds_var

        )


        self.seconds_entry.grid(

            row=1,

            column=2,

            padx=5,

            pady=(5, 0)

        )


        self.countdown_description = ctk.CTkLabel(

            self.countdown_frame,

            text="Set countdown duration"

        )


        self.countdown_description.grid(

            row=2,

            column=0,

            columnspan=3,

            pady=(5, 0)

        )


        self.toggle_countdown_inputs()


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

            row=3,

            column=0,

            pady=(10, 5)

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

            row=4,

            column=0,

            pady=20

        )

        self.phase_label = ctk.CTkLabel(
            self.timer_frame,
            text="Focus Session",
            font=("Arial", 14, "bold"),
            text_color="#6b7280",
        )
        self.phase_label.grid(row=5, column=0, pady=(0, 10))

        # --------------------------------------------------
        # Progress Bar
        # --------------------------------------------------

        self.progress_bar = ctk.CTkProgressBar(

            self.timer_frame,

            width=450

        )


        self.progress_bar.grid(

            row=6,

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


        self.button_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.button_frame.pack(side="left", padx=5)

        self.start_button = ctk.CTkButton(
            self.button_frame,
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
            self.button_frame,
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

        self.resume_button = ctk.CTkButton(
            self.button_frame,
            text="Resume",
            width=120,
            height=40,
            command=self.resume_timer,
            state="disabled"
        )
        self.resume_button.pack(side="left", padx=5)

        self.reset_button = ctk.CTkButton(
            self.button_frame,
            text="Reset",
            width=120,
            height=40,
            command=self.reset_timer
        )
        self.reset_button.pack(
            side="left",
            padx=5
        )

        self.end_button = ctk.CTkButton(
            self.button_frame,
            text="End",
            width=120,
            height=40,
            command=self.end_session,
            fg_color="#DC2626",
            hover_color="#B91C1C",
            text_color="white"
        )
        self.end_button.pack(
            side="left",
            padx=5
        )

        # Preset Pomodoro buttons
        self.preset_frame = ctk.CTkFrame(self.control_frame, fg_color="transparent")
        self.preset_frame.pack(side="left", padx=(12, 0))

        self.focus_btn = ctk.CTkButton(self.preset_frame, text="Focus 25", width=100, command=lambda: self.set_preset(25, "focus"))
        self.focus_btn.pack(side="left", padx=4)
        self.short_break_btn = ctk.CTkButton(self.preset_frame, text="Short 5", width=80, command=lambda: self.set_preset(5, "short_break"))
        self.short_break_btn.pack(side="left", padx=4)
        self.long_break_btn = ctk.CTkButton(self.preset_frame, text="Long 15", width=80, command=lambda: self.set_preset(15, "long_break"))
        self.long_break_btn.pack(side="left", padx=4)
        self.custom_btn = ctk.CTkButton(self.preset_frame, text="Custom", width=80, command=lambda: self.set_preset(None, "custom"))
        self.custom_btn.pack(side="left", padx=4)


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

            pady=(5, 5)

        )

        self.save_feedback_label = ctk.CTkLabel(

            self.session_frame,

            text="Recorded time will appear here.",

            font=("Arial", 12),

            text_color="#2563eb"

        )


        self.save_feedback_label.pack(

            anchor="w",

            padx=20,

            pady=(0, 10)

        )

        self.pomodoro_switch = ctk.CTkSwitch(
            self.session_frame,
            text="Pomodoro mode",
            command=self.toggle_pomodoro
        )
        self.pomodoro_switch.pack(anchor="w", padx=20, pady=(0, 10))

        self.sound_switch = ctk.CTkSwitch(
            self.session_frame,
            text="Enable sound notification",
            command=self.toggle_sound
        )
        self.sound_switch.pack(anchor="w", padx=20, pady=(0, 10))
        self.sound_switch.select()
        self.pomodoro_switch.select()

        # Pomodoro history and stats
        self.pomo_stats_frame = ctk.CTkFrame(self.session_frame, fg_color="transparent")
        self.pomo_stats_frame.pack(fill="x", padx=20, pady=(8, 6))

        self.daily_count_label = ctk.CTkLabel(self.pomo_stats_frame, text="Today: 0 pomodoros")
        self.daily_count_label.pack(side="left", padx=(0, 12))
        self.weekly_count_label = ctk.CTkLabel(self.pomo_stats_frame, text="Last 7 days: 0 pomodoros")
        self.weekly_count_label.pack(side="left")

        self.pomo_history_frame = ctk.CTkScrollableFrame(self.session_frame, corner_radius=8, height=140)
        self.pomo_history_frame.pack(fill="both", expand=False, padx=20, pady=(8, 12))

        self.history_label = ctk.CTkLabel(
            self.session_frame,
            text="Study Session History",
            font=("Arial", 14, "bold")
        )
        self.history_label.pack(anchor="w", padx=20, pady=(10, 4))

        self.history_frame = ctk.CTkScrollableFrame(self.session_frame, corner_radius=8, height=140)
        self.history_frame.pack(fill="both", expand=False, padx=20, pady=(0, 12))

        self.refresh_pomodoro_history()
        self.load_history()


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

    def refresh_pomodoro_history(self):
        """Refresh the pomodoro history list and daily/weekly stats from the DB."""
        try:
            recent = self.database.get_recent_pomodoro_sessions(limit=20)
        except Exception:
            recent = []

        # clear existing
        for w in self.pomo_history_frame.winfo_children():
            w.destroy()

        for row in recent:
            # row: id, session_type, duration, session_date, created_at
            lbl = ctk.CTkLabel(self.pomo_history_frame, text=f"{row[3]} • {row[1].replace('_', ' ').title()} • {row[2]}m")
            lbl.pack(anchor="w", padx=8, pady=2)

        # update counts
        today = date.today()
        today_str = today.isoformat()
        week_start = (today - timedelta(days=6)).isoformat()
        week_end = today.isoformat()
        try:
            daily = self.database.get_pomodoro_count_for_date(today_str, session_type="focus")
            weekly = self.database.get_pomodoro_count_between_dates(week_start, week_end, session_type="focus")
        except Exception:
            daily = 0
            weekly = 0

        try:
            self.daily_count_label.configure(text=f"Today: {daily} pomodoros")
            self.weekly_count_label.configure(text=f"Last 7 days: {weekly} pomodoros")
        except Exception:
            pass


    def on_timer_mode_changed(self, mode):

        if self.timer_running:

            self.timer_mode_var.set(self.timer_mode)

            return


        self.timer_mode = mode

        self.toggle_countdown_inputs()

        self.reset_timer()


    def toggle_countdown_inputs(self):

        countdown_enabled = self.timer_mode == "COUNTDOWN"


        state = "normal" if countdown_enabled else "disabled"


        self.hours_entry.configure(state=state)

        self.minutes_entry.configure(state=state)

        self.seconds_entry.configure(state=state)


        self.countdown_description.configure(

            text="Set countdown duration" if countdown_enabled else "Countdown settings disabled in stopwatch mode"

        )


    def parse_countdown_duration(self):

        try:

            hours = max(0, int(self.countdown_hours_var.get()))

        except Exception:

            hours = 0

            self.countdown_hours_var.set("0")


        try:

            minutes = max(0, min(59, int(self.countdown_minutes_var.get())))

        except Exception:

            minutes = self.countdown_minutes

            self.countdown_minutes_var.set(str(minutes))


        try:

            seconds = max(0, min(59, int(self.countdown_seconds_var.get())))

        except Exception:

            seconds = self.countdown_seconds

            self.countdown_seconds_var.set(str(seconds))


        if minutes > 59:

            minutes = 59

            self.countdown_minutes_var.set(str(minutes))


        if seconds > 59:

            seconds = 59

            self.countdown_seconds_var.set(str(seconds))


        total_seconds = hours * 3600 + minutes * 60 + seconds


        if total_seconds <= 0:

            total_seconds = self.study_minutes * 60

            self.countdown_hours_var.set("0")

            self.countdown_minutes_var.set(str(self.study_minutes))

            self.countdown_seconds_var.set("0")


        self.countdown_hours = hours

        self.countdown_minutes = minutes

        self.countdown_seconds = seconds


        return total_seconds

    def set_preset(self, minutes: int, session_type: str):
        """Set a pomodoro preset and prepare countdown. If minutes is None, use current countdown fields (custom)."""
        if minutes is not None:
            self.countdown_hours_var.set("0")
            self.countdown_minutes_var.set(str(minutes))
            self.countdown_seconds_var.set("0")
        # mark current pomodoro type for save on completion
        self.current_pomodoro_type = session_type
        # set mode to COUNTDOWN and reset without saving the previous session
        self.timer_mode = "COUNTDOWN"
        self.timer_mode_var.set("COUNTDOWN")
        self.toggle_countdown_inputs()
        self.reset_timer(save_session=False)
        self.update_phase_label()


    # ======================================================
    # START TIMER
    # ======================================================

    def format_time(self, sec):

        hours = str(sec // 3600).zfill(2)

        minutes = str((sec % 3600) // 60).zfill(2)

        seconds = str(sec % 60).zfill(2)

        return f"{hours}:{minutes}:{seconds}"


    def update_timer_display(self):

        if self.timer_mode == "STOPWATCH":

            self.timer_label.configure(

                text=self.format_time(self.stopwatch_seconds)

            )

        else:

            self.timer_label.configure(

                text=self.format_time(self.remaining_seconds)

            )

    def toggle_pomodoro(self):
        self.pomodoro_enabled = bool(self.pomodoro_switch.get())
        self.session_status_label.configure(
            text="Pomodoro mode enabled." if self.pomodoro_enabled else "Pomodoro mode disabled."
        )
        self.update_phase_label()

    def toggle_sound(self):
        self.sound_enabled = bool(self.sound_switch.get())
        self.session_status_label.configure(
            text="Sound notifications enabled." if self.sound_enabled else "Sound notifications disabled."
        )

    def start_timer(self):

        if self.timer_running:

            return

        self._cancel_timer_tick()

        self.timer_running = True
        self.timer_paused = False
        self.session_start_time = datetime.now()
        self.session_elapsed_seconds = 0

        self.start_button.configure(state="disabled")
        self.pause_button.configure(state="normal")
        self.resume_button.configure(state="disabled")
        self.elapsed_seconds = 0
        self.save_feedback_label.configure(text="Recording time...")

        if self.timer_mode == "STOPWATCH":

            if not self.timer_paused:

                self.stopwatch_seconds = 0

            self.mode_label.configure(text="STOPWATCH")

            self.session_status_label.configure(text="Stopwatch is running...")

            self.save_feedback_label.configure(
                text=f"Recorded: {self.format_time(self.stopwatch_seconds)}"
            )

            self.progress_bar.set(min(self.stopwatch_seconds / 3600, 1.0))

        else:

            # If pomodoro mode is enabled and a current_pomodoro_type is set, use preset minutes
            if self.pomodoro_enabled and getattr(self, "current_pomodoro_type", None) in ("focus", "short_break", "long_break"):
                # duration from countdown fields already set by set_preset
                self.remaining_seconds = self.parse_countdown_duration()
            else:
                self.remaining_seconds = self.parse_countdown_duration()

            self.total_seconds = self.remaining_seconds

            self.mode_label.configure(text="COUNTDOWN")

            self.session_status_label.configure(text="Countdown timer is running...")

            self.save_feedback_label.configure(
                text=f"Elapsed: {self.format_time(self.session_elapsed_seconds)}"
            )

            self.progress_bar.set(1 - self.remaining_seconds / max(1, self.total_seconds))

        self.update_timer_display()

        self.tick_timer()


    def _cancel_timer_tick(self):
        if self.timer_id is None:
            return
        try:
            self.after_cancel(self.timer_id)
        except Exception:
            pass
        self.timer_id = None

    def _schedule_next_tick(self):
        self._cancel_timer_tick()
        self.timer_id = self.after(1000, self.tick_timer)

    def tick_timer(self):
        self.timer_id = None

        if not self.timer_running:
            return

        if self.timer_mode == "STOPWATCH":

            self.stopwatch_seconds += 1

            self.session_elapsed_seconds += 1
            self.elapsed_seconds += 1

            self.update_timer_display()

            self.save_feedback_label.configure(
                text=f"Recorded: {self.format_time(self.stopwatch_seconds)}"
            )

            self.progress_bar.set(min(self.stopwatch_seconds / 3600, 1.0))

            self._schedule_next_tick()

            return

        self.remaining_seconds -= 1
        self.session_elapsed_seconds += 1
        self.elapsed_seconds += 1

        self.update_timer_display()

        self.save_feedback_label.configure(
            text=f"Elapsed: {self.format_time(self.session_elapsed_seconds)}"
        )

        progress_value = 1 - (self.remaining_seconds / max(1, self.total_seconds))
        self.progress_bar.set(max(0.0, min(1.0, progress_value)))

        if self.remaining_seconds <= 0:
            self.handle_timer_complete()
            return

        self._schedule_next_tick()


    def pause_timer(self):

        self.timer_running = False
        self.timer_paused = True

        self._cancel_timer_tick()

        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="normal")
        self.start_button.configure(state="disabled")

        self.session_status_label.configure(

            text="Timer paused."

        )

    def resume_timer(self):
        if self.timer_running:
            return

        if self.timer_mode == "COUNTDOWN" and self.remaining_seconds <= 0:
            return

        self._cancel_timer_tick()

        self.timer_running = True
        self.timer_paused = False
        self.pause_button.configure(state="normal")
        self.resume_button.configure(state="disabled")
        self.start_button.configure(state="disabled")
        self.session_status_label.configure(text="Timer resumed.")
        self.tick_timer()


    def reset_timer(self, save_session=True):

        if save_session:
            if self.timer_mode == "STOPWATCH" and self.stopwatch_seconds > 0:
                self.save_study_session(self.stopwatch_seconds)
            elif self.timer_mode == "COUNTDOWN" and self.session_elapsed_seconds > 0:
                self.save_study_session(self.session_elapsed_seconds)

        self.timer_running = False
        self.timer_paused = False

        self._cancel_timer_tick()

        self.session_elapsed_seconds = 0
        self.elapsed_seconds = 0
        self.is_break = False

        if self.timer_mode == "COUNTDOWN":
            self.remaining_seconds = self.parse_countdown_duration()
            self.total_seconds = self.remaining_seconds
            self.mode_label.configure(text="COUNTDOWN")
            self.timer_label.configure(text=self.format_time(self.remaining_seconds))
        else:
            self.stopwatch_seconds = 0
            self.mode_label.configure(text="STOPWATCH")
            self.timer_label.configure(text=self.format_time(self.stopwatch_seconds))

        self.progress_bar.set(0)

        self.start_button.configure(state="normal")
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.save_feedback_label.configure(text="")
        self.save_feedback_label.configure(text="Recorded time will appear here.")
        self.session_status_label.configure(
            text="Timer reset."
        )

    def handle_timer_complete(self):
        self.timer_running = False
        self._cancel_timer_tick()
        self.pause_button.configure(state="disabled")
        self.resume_button.configure(state="disabled")
        self.start_button.configure(state="normal")

        if self.timer_mode == "COUNTDOWN":
            completed_type = getattr(self, "current_pomodoro_type", "focus")
            is_pomodoro = self.pomodoro_enabled and completed_type is not None

            if completed_type == "focus":
                self.save_study_session(self.session_elapsed_seconds)

            try:
                if is_pomodoro:
                    duration_minutes = max(1, self.session_elapsed_seconds // 60)
                    session_date = datetime.now().strftime("%Y-%m-%d")
                    self.database.add_pomodoro_session(completed_type, duration_minutes, session_date)
                    self.refresh_pomodoro_history()
                    self.play_notification()

                    if completed_type == "focus":
                        self.pomodoro_cycle_count = getattr(self, "pomodoro_cycle_count", 0) + 1
                        if self.pomodoro_cycle_count % 4 == 0:
                            self.set_preset(self.long_break_minutes, "long_break")
                        else:
                            self.set_preset(self.short_break_minutes, "short_break")
                        self.session_status_label.configure(text="Focus complete! Starting break...")
                        self.start_timer()
                        return
                    else:
                        self.set_preset(self.focus_minutes, "focus")
                        self.current_pomodoro_type = "focus"
                        self.session_status_label.configure(text="Break complete! Ready for next focus session.")
                        self.save_feedback_label.configure(text="Ready for next focus session.")
                        return
            except Exception:
                pass

            self.session_elapsed_seconds = 0
            self.elapsed_seconds = 0
            self.remaining_seconds = self.parse_countdown_duration()
            self.total_seconds = self.remaining_seconds
            self.progress_bar.set(0)
            self.mode_label.configure(text="COUNTDOWN")
            self.timer_label.configure(text=self.format_time(self.remaining_seconds))
            self.session_status_label.configure(text="Countdown complete.")
            return

        self.session_status_label.configure(text="Stopwatch reached its configured limit.")


    # ======================================================
    # SAVE STUDY SESSION
    # ======================================================

    def play_notification(self):
        if not self.sound_enabled:
            return
        try:
            if winsound:
                winsound.Beep(1000, 300)
            else:
                self.bell()
        except Exception:
            try:
                self.bell()
            except Exception:
                pass

    def update_phase_label(self):
        if self.timer_mode == "STOPWATCH":
            text = "Stopwatch mode"
        else:
            phase = getattr(self, "current_pomodoro_type", "focus")
            if phase == "focus":
                text = "Focus Session"
            elif phase == "short_break":
                text = "Short Break"
            elif phase == "long_break":
                text = "Long Break"
            else:
                text = "Custom Countdown"
        try:
            self.phase_label.configure(text=text)
        except Exception:
            pass

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

                session.get_study_date()

            )

        )


        if success:
            request_analytics_refresh()
            self.session_status_label.configure(

                text=(

                    f"Saved {duration} minute study session for analytics and reports."

                )

            )
            self.save_feedback_label.configure(

                text=f"Last saved session: {duration} minutes."

            )

        else:

            self.session_status_label.configure(

                text="Unable to save study session."

            )
            self.save_feedback_label.configure(text="")

    def end_session(self):

        if not self.timer_running:
            return

        self.timer_running = False
        self.timer_paused = False
        self._cancel_timer_tick()

        current_subject = self.subject_combobox.get()
        duration_minutes = max(1, self.elapsed_seconds // 60)
        study_date = datetime.now().strftime("%Y-%m-%d")

        self.database.add_study_session(
            current_subject,
            duration_minutes,
            study_date
        )

        self.load_history()
        self._refresh_dashboard_data()

        self.elapsed_seconds = 0
        self.session_elapsed_seconds = 0
        self.update_timer_display()

    def _refresh_dashboard_data(self):
        current = getattr(self, "master", None)
        for _ in range(6):
            if current is None:
                break
            if hasattr(current, "load_dashboard_data") and callable(getattr(current, "load_dashboard_data")):
                try:
                    current.load_dashboard_data()
                except Exception:
                    pass
                return
            current = getattr(current, "master", None)

    def load_history(self):
        for widget in self.history_frame.winfo_children():
            widget.destroy()

        sessions = self.database.get_all_study_sessions()

        for session in sessions:
            ctk.CTkLabel(
                self.history_frame,
                text=f"{session[1]}  {session[2]} min"
            ).pack(anchor="w", padx=8, pady=2)


    # ======================================================
    # CLOSE WINDOW
    # ======================================================

    def close_window(self):
        self.timer_running = False
        self.timer_paused = False
        self._cancel_timer_tick()
        self.session_elapsed_seconds = 0
        self.database = None
        self.destroy()

    def destroy(self):
        self.timer_running = False
        self.timer_paused = False
        self._cancel_timer_tick()
        super().destroy()