import customtkinter as ctk

from tkinter import messagebox

from database import DatabaseManager

from models import Subject
from utils import ValidationError, validate_date_string, validate_required_field, run_in_background, handle_operation_error


# ==========================================================
# SUBJECT WINDOW
# ==========================================================

class SubjectWindow(ctk.CTkFrame):
    """
    Subject management page.
    """

    def __init__(self, parent, database=None):

        super().__init__(parent)

        self.parent = parent

        self.database = database or DatabaseManager()

        self.selected_subject_id = None
        self._subjects_loaded = False

        self.create_layout()

        self.load_subjects(force=True)

    def get_subject_metrics(self, subject_name):
        """Return task count, completed count, pending count, and study time for a subject."""
        tasks = self.database.get_tasks_by_subject(subject_name)
        completed_count = 0
        pending_count = 0

        for task in tasks:
            status = str(task[6]).strip().lower() if len(task) > 6 else ""
            if status == "completed":
                completed_count += 1
            else:
                pending_count += 1

        study_hours = 0.0
        try:
            study_hours_by_subject = self.database.get_study_hours_by_subject()
            study_hours = study_hours_by_subject.get(subject_name, 0.0)
        except Exception:
            study_hours = 0.0

        if tasks:
            progress = round((completed_count / len(tasks)) * 100, 1)
        else:
            progress = 0.0

        return {
            "task_count": len(tasks),
            "completed": completed_count,
            "pending": pending_count,
            "study_hours": round(study_hours, 1),
            "progress": progress,
        }

    def update_details_panel(self, subject):
        """Populate the details panel with the selected subject statistics."""
        if subject is None:
            self.details_title_label.configure(text="Subject Overview")
            self.details_summary_label.configure(text="Select a subject to view details.")
            self.details_details_label.configure(text="")
            self.details_progress_label.configure(text="Progress: 0%")
            self.details_progress_bar.set(0)
            return

        subject_name = subject[1]
        stats = self.get_subject_metrics(subject_name)
        self.details_title_label.configure(text=f"{subject_name}")
        self.details_summary_label.configure(
            text=(
                f"{stats['task_count']} tasks • {stats['completed']} completed • "
                f"{stats['pending']} pending"
            )
        )
        self.details_details_label.configure(
            text=(
                f"Study time: {stats['study_hours']}h • "
                f"Progress: {stats['progress']}%"
            )
        )
        self.details_progress_label.configure(text=f"Progress: {stats['progress']}%")
        self.details_progress_bar.set(stats['progress'] / 100)

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

        self.create_subject_list()


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

            text="Subject Management",

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

            command=self.load_subjects

        ).grid(

            row=0,

            column=1,

            padx=10

        )


    # ======================================================
    # SUBJECT FORM
    # ======================================================

    def create_form(self):

        self.form_frame = ctk.CTkFrame(

            self.content_frame,

            width=300

        )


        self.form_frame.grid(

            row=0,

            column=0,

            sticky="nsew",

            padx=(10, 20),

            pady=10

        )


        self.form_frame.grid_propagate(

            False

        )


        ctk.CTkLabel(

            self.form_frame,

            text="Subject Details",

            font=(

                "Arial",

                20,

                "bold"

            )

        ).pack(

            pady=(25, 30)

        )


        # --------------------------------------------------
        # Subject Name
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Subject Name"

        ).pack(

            anchor="w",

            padx=25

        )


        self.name_entry = ctk.CTkEntry(

            self.form_frame,

            placeholder_text=(

                "e.g. Python Programming"

            ),

            width=250

        )


        self.name_entry.pack(

            padx=25,

            pady=(5, 20)

        )


        # --------------------------------------------------
        # Subject Color
        # --------------------------------------------------

        ctk.CTkLabel(

            self.form_frame,

            text="Subject Color"

        ).pack(

            anchor="w",

            padx=25

        )


        self.color_entry = ctk.CTkEntry(

            self.form_frame,

            placeholder_text=(

                "#1f6aa5"

            ),

            width=250

        )


        self.color_entry.pack(

            padx=25,

            pady=(5, 20)

        )


        # --------------------------------------------------
        # Add Button
        # --------------------------------------------------

        self.add_button = ctk.CTkButton(

            self.form_frame,

            text="Add Subject",

            width=250,

            height=40,

            command=self.add_subject

        )


        self.add_button.pack(

            padx=25,

            pady=10

        )


        # --------------------------------------------------
        # Update Button
        # --------------------------------------------------

        self.update_button = ctk.CTkButton(

            self.form_frame,

            text="Update Subject",

            width=250,

            height=40,

            command=self.update_subject,

            state="disabled"

        )


        self.update_button.pack(

            padx=25,

            pady=10

        )


        # --------------------------------------------------
        # Delete Button
        # --------------------------------------------------

        self.delete_button = ctk.CTkButton(

            self.form_frame,

            text="Delete Subject",

            width=250,

            height=40,

            fg_color="gray",

            command=self.delete_subject,

            state="disabled"

        )


        self.delete_button.pack(

            padx=25,

            pady=10

        )

        self.details_frame = ctk.CTkFrame(
            self.form_frame,
            fg_color="transparent"
        )
        self.details_frame.pack(
            fill="x",
            padx=25,
            pady=(10, 10)
        )

        ctk.CTkLabel(
            self.details_frame,
            text="Subject Overview",
            font=("Arial", 16, "bold")
        ).pack(anchor="w")

        self.details_title_label = ctk.CTkLabel(
            self.details_frame,
            text="Select a subject to view details",
            font=("Arial", 14, "bold")
        )
        self.details_title_label.pack(anchor="w", pady=(8, 4))

        self.details_summary_label = ctk.CTkLabel(
            self.details_frame,
            text="",
            wraplength=240,
            justify="left"
        )
        self.details_summary_label.pack(anchor="w", pady=(0, 4))

        self.details_details_label = ctk.CTkLabel(
            self.details_frame,
            text="",
            wraplength=240,
            justify="left"
        )
        self.details_details_label.pack(anchor="w", pady=(0, 4))

        self.details_progress_bar = ctk.CTkProgressBar(
            self.details_frame,
            width=220,
            height=10
        )
        self.details_progress_bar.pack(fill="x", pady=(6, 4))
        self.details_progress_bar.set(0)

        self.details_progress_label = ctk.CTkLabel(
            self.details_frame,
            text="Progress: 0%"
        )
        self.details_progress_label.pack(anchor="w")

        # --------------------------------------------------
        # Clear Button
        # --------------------------------------------------

        ctk.CTkButton(

            self.form_frame,

            text="Clear",

            width=250,

            height=40,

            fg_color="transparent",

            border_width=1,

            command=self.clear_form

        ).pack(

            padx=25,

            pady=10

        )


    # ======================================================
    # SUBJECT LIST
    # ======================================================

    def create_subject_list(self):

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


        self.list_frame.grid_rowconfigure(

            1,

            weight=1

        )


        self.list_frame.grid_columnconfigure(

            0,

            weight=1

        )


        ctk.CTkLabel(

            self.list_frame,

            text="Your Subjects",

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

            pady=20

        )


        # --------------------------------------------------
        # Search Bar
        # --------------------------------------------------

        self.search_entry = ctk.CTkEntry(

            self.list_frame,

            placeholder_text=(

                "Search subjects..."

            ),

            width=250

        )


        self.search_entry.grid(

            row=0,

            column=0,

            sticky="e",

            padx=20,

            pady=20

        )


        self.search_entry.bind(

            "<KeyRelease>",

            self.search_subjects

        )


        # --------------------------------------------------
        # Scrollable List
        # --------------------------------------------------

        self.subject_scrollable = ctk.CTkScrollableFrame(

            self.list_frame

        )


        self.subject_scrollable.grid(

            row=1,

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
        for widget in self.subject_scrollable.winfo_children():
            widget.destroy()
        ctk.CTkLabel(self.subject_scrollable, text="Loading subjects...", font=("Arial", 13)).pack(pady=20)
        run_in_background(
            self,
            self._load_subjects_data,
            callback=self._apply_subjects_data,
            error_callback=self._show_subject_error,
        )

    def _load_subjects_data(self):
        return self.database.get_all_subjects() if self.database else []

    def _apply_subjects_data(self, subjects):
        self._subjects_loaded = True
        for widget in self.subject_scrollable.winfo_children():
            widget.destroy()
        if not subjects:
            ctk.CTkLabel(self.subject_scrollable, text="No subjects found. Add your first subject.", font=("Arial", 13)).pack(pady=40)
            return
        for subject in subjects:
            self.create_subject_card(subject)

    def _show_subject_error(self, error, safe_message=None):
        friendly_message = safe_message or handle_operation_error(
            error,
            context="refreshing subject list",
            user_message="We couldn't refresh subjects right now.",
        )
        messagebox.showerror("Subject Error", friendly_message)


    # ======================================================
    # CREATE SUBJECT CARD
    # ======================================================

    def create_subject_card(

        self,

        subject

    ):

        subject_id = subject[0]

        name = subject[1]

        color = subject[2]

        stats = self.get_subject_metrics(name)

        card = ctk.CTkFrame(

            self.subject_scrollable,
            corner_radius=14

        )


        card.pack(

            fill="x",

            padx=10,

            pady=7

        )

        color_label = ctk.CTkLabel(

            card,

            text="●",

            font=(

                "Arial",

                30

            ),

            text_color=color

        )


        color_label.pack(

            side="left",

            padx=(15, 10),

            pady=15

        )

        content_frame = ctk.CTkFrame(card, fg_color="transparent")
        content_frame.pack(side="left", fill="both", expand=True, padx=(0, 10), pady=10)

        ctk.CTkLabel(
            content_frame,
            text=name,
            font=(

                "Arial",

                16,

                "bold"

            )
        ).pack(anchor="w")

        ctk.CTkLabel(
            content_frame,
            text=(
                f"{stats['task_count']} tasks • {stats['study_hours']}h studied • "
                f"{stats['completed']} completed"
            ),
            font=("Arial", 12)
        ).pack(anchor="w", pady=(2, 4))

        progress_bar = ctk.CTkProgressBar(content_frame, height=8)
        progress_bar.pack(fill="x", pady=(2, 4))
        progress_bar.set(stats['progress'] / 100)

        ctk.CTkLabel(
            content_frame,
            text=f"Progress: {stats['progress']}%",
            font=("Arial", 11)
        ).pack(anchor="w")

        buttons_frame = ctk.CTkFrame(card, fg_color="transparent")
        buttons_frame.pack(side="right", padx=10, pady=10)

        ctk.CTkButton(
            buttons_frame,
            text="View",
            width=70,
            command=lambda subject=subject: self.select_subject(subject)
        ).pack(pady=(0, 6))

        ctk.CTkButton(
            buttons_frame,
            text="Edit",
            width=70,
            command=lambda subject=subject: self.select_subject(subject)
        ).pack()


    # ======================================================
    # ADD SUBJECT
    # ======================================================

    def add_subject(self):

        try:
            name = validate_required_field(
                self.name_entry.get(),
                "Subject name",
            )
            color = self.color_entry.get().strip() or "#1f6aa5"
            if not color:
                color = "#1f6aa5"

            subject = Subject(name=name, color=color)

            existing_subjects = self.database.get_all_subjects()
            for existing in existing_subjects:
                if existing[1].lower() == name.lower():
                    raise ValidationError("This subject already exists.")

            success = self.database.add_subject(
                subject.get_name(),
                subject.get_color(),
            )
            if success:
                messagebox.showinfo("Success", "Subject added successfully.")
                self.clear_form()
                self.load_subjects()
            else:
                raise RuntimeError("Unable to add subject. Please try again.")
        except ValidationError as error:
            messagebox.showwarning("Validation Error", str(error))
        except RuntimeError as error:
            friendly_message = handle_operation_error(
                error,
                context="adding subject",
                user_message="We couldn't add the subject. Please try again.",
            )
            messagebox.showerror("Error", friendly_message)
        except Exception as error:
            friendly_message = handle_operation_error(
                error,
                context="adding subject",
                user_message="We couldn't add the subject. Please try again.",
            )
            messagebox.showerror("Unexpected Error", friendly_message)


    # ======================================================
    # SELECT SUBJECT
    # ======================================================

    def select_subject(

        self,

        subject

    ):

        self.selected_subject_id = subject[0]


        self.name_entry.delete(

            0,

            "end"

        )


        self.name_entry.insert(

            0,

            subject[1]

        )


        self.color_entry.delete(

            0,

            "end"

        )


        self.color_entry.insert(

            0,

            subject[2]

        )


        self.update_button.configure(

            state="normal"

        )


        self.delete_button.configure(

            state="normal"

        )


        self.add_button.configure(

            state="disabled"

        )

        self.update_details_panel(subject)


    # ======================================================
    # UPDATE SUBJECT
    # ======================================================

    def update_subject(self):

        if not self.selected_subject_id:
            messagebox.showwarning("Warning", "Please select a subject first.")
            return

        try:
            name = validate_required_field(self.name_entry.get(), "Subject name")
            color = self.color_entry.get().strip() or "#1f6aa5"
            if not color:
                color = "#1f6aa5"

            success = self.database.update_subject(
                self.selected_subject_id,
                name,
                color,
            )
            if success:
                messagebox.showinfo("Success", "Subject updated successfully.")
                self.clear_form()
                self.load_subjects()
            else:
                raise RuntimeError("Unable to update subject. Please try again.")
        except ValidationError as error:
            messagebox.showwarning("Validation Error", str(error))
        except RuntimeError as error:
            friendly_message = handle_operation_error(
                error,
                context="updating subject",
                user_message="We couldn't update the subject. Please try again.",
            )
            messagebox.showerror("Error", friendly_message)
        except Exception as error:
            friendly_message = handle_operation_error(
                error,
                context="updating subject",
                user_message="We couldn't update the subject. Please try again.",
            )
            messagebox.showerror("Unexpected Error", friendly_message)


    # ======================================================
    # DELETE SUBJECT
    # ======================================================

    def delete_subject(self):

        if not self.selected_subject_id:

            messagebox.showwarning(

                "Warning",

                "Please select a subject first."

            )

            return


        answer = messagebox.askyesno(

            "Confirm Delete",

            (

                "Are you sure you want "
                "to delete this subject?"

            )

        )


        if not answer:

            return


        success = (

            self.database
            .delete_subject(

                self.selected_subject_id

            )

        )


        if success:

            messagebox.showinfo(

                "Success",

                "Subject deleted successfully."

            )


            self.clear_form()

            self.load_subjects()


        else:

            messagebox.showerror(

                "Error",

                "Unable to delete subject."

            )


    # ======================================================
    # SEARCH SUBJECTS
    # ======================================================

    def search_subjects(

        self,

        event=None

    ):

        keyword = (

            self.search_entry
            .get()
            .strip()
            .lower()

        )


        subjects = (

            self.database
            .get_all_subjects()

        )


        for widget in (

            self.subject_scrollable
            .winfo_children()

        ):

            widget.destroy()


        for subject in subjects:

            name = subject[1].lower()


            if keyword in name:

                self.create_subject_card(

                    subject

                )


    # ======================================================
    # CLEAR FORM
    # ======================================================

    def clear_form(self):

        self.selected_subject_id = None


        self.name_entry.delete(

            0,

            "end"

        )


        self.color_entry.delete(

            0,

            "end"

        )


        self.update_button.configure(

            state="disabled"

        )


        self.delete_button.configure(

            state="disabled"

        )


        self.add_button.configure(

            state="normal"

        )

        self.update_details_panel(None)