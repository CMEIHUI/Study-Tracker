from datetime import date


class Person:
    """
    Parent class representing a general person.
    """

    def __init__(
        self,
        username,
        email
    ):
        """
        Constructor.

        Encapsulation is demonstrated using
        protected attributes.
        """

        self._username = username

        self._email = email


    # ------------------------------------------------------
    # Getter: Username
    # ------------------------------------------------------

    def get_username(self):

        return self._username


    # ------------------------------------------------------
    # Setter: Username
    # ------------------------------------------------------

    def set_username(
        self,
        username
    ):

        if username.strip() != "":

            self._username = username


    # ------------------------------------------------------
    # Getter: Email
    # ------------------------------------------------------

    def get_email(self):

        return self._email


    # ------------------------------------------------------
    # Setter: Email
    # ------------------------------------------------------

    def set_email(
        self,
        email
    ):

        if "@" in email:

            self._email = email


    # ------------------------------------------------------
    # Polymorphism Method
    # ------------------------------------------------------

    def get_role(self):

        return "Person"


    # ------------------------------------------------------
    # String Representation
    # ------------------------------------------------------

    def __str__(self):

        return (
            f"Username: {self._username}, "
            f"Email: {self._email}"
        )


# ==========================================================
# STUDENT CLASS
# ==========================================================

class Student(Person):
    """
    Student inherits from Person.

    This demonstrates:

    Inheritance
    Method Overriding
    Encapsulation
    """

    def __init__(
        self,
        username,
        email,
        student_id=None
    ):

        super().__init__(
            username,
            email
        )

        self._student_id = student_id

        # SET
        # Stores unique study dates

        self._study_days = set()


    # ------------------------------------------------------
    # Student ID
    # ------------------------------------------------------

    def get_student_id(self):

        return self._student_id


    def set_student_id(
        self,
        student_id
    ):

        self._student_id = student_id


    # ------------------------------------------------------
    # Study Day Management
    # ------------------------------------------------------

    def add_study_day(
        self,
        study_date
    ):

        self._study_days.add(
            study_date
        )


    def remove_study_day(
        self,
        study_date
    ):

        self._study_days.discard(
            study_date
        )


    def get_study_days(self):

        return self._study_days.copy()


    def get_study_streak(self):

        return len(
            self._study_days
        )


    # ------------------------------------------------------
    # Method Overriding
    # ------------------------------------------------------

    def get_role(self):

        return "Student"


    def __str__(self):

        return (
            f"Student: {self._username}, "
            f"Email: {self._email}, "
            f"Student ID: {self._student_id}"
        )


# ==========================================================
# STUDY ITEM CLASS
# ==========================================================

class StudyItem:
    """
    Parent class for study-related objects.
    """

    def __init__(
        self,
        title
    ):

        self._title = title


    def get_title(self):

        return self._title


    def set_title(
        self,
        title
    ):

        if title.strip() != "":

            self._title = title


    # ------------------------------------------------------
    # Polymorphism Method
    # ------------------------------------------------------

    def get_item_type(self):

        return "Study Item"


    def display_info(self):

        return self._title


# ==========================================================
# STUDY TASK CLASS
# ==========================================================

class StudyTask(StudyItem):
    """
    StudyTask inherits from StudyItem.

    Demonstrates:

    Inheritance
    Encapsulation
    Method Overriding
    """

    # TUPLE

    PRIORITIES = (
        "High",
        "Medium",
        "Low"
    )


    STATUSES = (
        "Pending",
        "Completed"
    )


    def __init__(
        self,
        subject,
        title,
        description="",
        priority="Medium",
        deadline="",
        status="Pending",
        task_id=None
    ):

        super().__init__(
            title
        )

        self._task_id = task_id

        self._subject = subject

        self._description = description

        self._priority = priority

        self._deadline = deadline

        self._status = status


    # ------------------------------------------------------
    # Task ID
    # ------------------------------------------------------

    def get_task_id(self):

        return self._task_id


    # ------------------------------------------------------
    # Subject
    # ------------------------------------------------------

    def get_subject(self):

        return self._subject


    def set_subject(
        self,
        subject
    ):

        self._subject = subject


    # ------------------------------------------------------
    # Description
    # ------------------------------------------------------

    def get_description(self):

        return self._description


    def set_description(
        self,
        description
    ):

        self._description = description


    # ------------------------------------------------------
    # Priority
    # ------------------------------------------------------

    def get_priority(self):

        return self._priority


    def set_priority(
        self,
        priority
    ):

        if priority in self.PRIORITIES:

            self._priority = priority


    # ------------------------------------------------------
    # Deadline
    # ------------------------------------------------------

    def get_deadline(self):

        return self._deadline


    def set_deadline(
        self,
        deadline
    ):

        self._deadline = deadline


    # ------------------------------------------------------
    # Status
    # ------------------------------------------------------

    def get_status(self):

        return self._status


    def complete(self):

        self._status = "Completed"


    def reopen(self):

        self._status = "Pending"


    def is_completed(self):

        return (
            self._status == "Completed"
        )


    # ------------------------------------------------------
    # Polymorphism
    # ------------------------------------------------------

    def get_item_type(self):

        return "Study Task"


    def display_info(self):

        return {

            "title":
                self._title,

            "subject":
                self._subject,

            "priority":
                self._priority,

            "deadline":
                self._deadline,

            "status":
                self._status

        }


    def __str__(self):

        return (
            f"{self._title} | "
            f"{self._subject} | "
            f"{self._priority} | "
            f"{self._status}"
        )


# ==========================================================
# SUBJECT CLASS
# ==========================================================

class Subject:
    """
    Represents an academic subject.
    """

    def __init__(
        self,
        name,
        color="#1f6aa5",
        subject_id=None
    ):

        self._subject_id = subject_id

        self._name = name

        self._color = color


    # ------------------------------------------------------
    # Subject ID
    # ------------------------------------------------------

    def get_subject_id(self):

        return self._subject_id


    # ------------------------------------------------------
    # Name
    # ------------------------------------------------------

    def get_name(self):

        return self._name


    def set_name(
        self,
        name
    ):

        if name.strip() != "":

            self._name = name


    # ------------------------------------------------------
    # Color
    # ------------------------------------------------------

    def get_color(self):

        return self._color


    def set_color(
        self,
        color
    ):

        self._color = color


    def __str__(self):

        return self._name


# ==========================================================
# STUDY SESSION CLASS
# ==========================================================

class StudySession:
    """
    Represents one study session.
    """

    def __init__(
        self,
        subject,
        duration,
        study_date=None,
        session_id=None
    ):

        self._session_id = session_id

        self._subject = subject

        self._duration = duration

        self._study_date = (

            study_date

            if study_date

            else date.today().isoformat()

        )


    # ------------------------------------------------------
    # Session ID
    # ------------------------------------------------------

    def get_session_id(self):

        return self._session_id


    # ------------------------------------------------------
    # Subject
    # ------------------------------------------------------

    def get_subject(self):

        return self._subject


    # ------------------------------------------------------
    # Duration
    # ------------------------------------------------------

    def get_duration(self):

        return self._duration


    def set_duration(
        self,
        duration
    ):

        if duration >= 0:

            self._duration = duration


    # ------------------------------------------------------
    # Study Date
    # ------------------------------------------------------

    def get_study_date(self):

        return self._study_date


    def get_duration_hours(self):

        return round(

            self._duration / 60,

            2

        )


    def __str__(self):

        return (
            f"{self._subject} - "
            f"{self._duration} minutes - "
            f"{self._study_date}"
        )


# ==========================================================
# NOTE CLASS
# ==========================================================

class Note:
    """
    Represents a study note.
    """

    def __init__(
        self,
        subject,
        note,
        created_date=None,
        note_id=None
    ):

        self._note_id = note_id

        self._subject = subject

        self._note = note

        self._created_date = (

            created_date

            if created_date

            else date.today().isoformat()

        )


    def get_note_id(self):

        return self._note_id


    def get_subject(self):

        return self._subject


    def set_subject(
        self,
        subject
    ):

        self._subject = subject


    def get_note(self):

        return self._note


    def set_note(
        self,
        note
    ):

        if note.strip() != "":

            self._note = note


    def get_created_date(self):

        return self._created_date


    def __str__(self):

        return (
            f"{self._subject}: "
            f"{self._note}"
        )


# ==========================================================
# ACHIEVEMENT CLASS
# ==========================================================

class Achievement:
    """
    Represents an achievement.
    """

    def __init__(
        self,
        title,
        description,
        unlocked=False,
        achievement_id=None
    ):

        self._achievement_id = achievement_id

        self._title = title

        self._description = description

        self._unlocked = unlocked


    def get_achievement_id(self):

        return self._achievement_id


    def get_title(self):

        return self._title


    def get_description(self):

        return self._description


    def is_unlocked(self):

        return self._unlocked


    def unlock(self):

        self._unlocked = True


    def lock(self):

        self._unlocked = False


    def __str__(self):

        status = (

            "Unlocked"

            if self._unlocked

            else "Locked"

        )

        return (
            f"{self._title} - "
            f"{status}"
        )


# ==========================================================
# STUDY TRACKER CLASS
# ==========================================================

class StudyTracker:
    """
    Main business logic class.

    Demonstrates composition by managing
    multiple study objects.
    """

    def __init__(self):

        # LIST

        self._tasks = []


        # DICTIONARY

        self._subjects = {}


        # SET

        self._study_dates = set()


        # LIST

        self._sessions = []


    # ------------------------------------------------------
    # Subject Management
    # ------------------------------------------------------

    def add_subject(
        self,
        subject
    ):

        self._subjects[
            subject.get_name()
        ] = subject


    def remove_subject(
        self,
        subject_name
    ):

        if subject_name in self._subjects:

            del self._subjects[
                subject_name
            ]


    def get_subjects(self):

        return self._subjects.copy()


    # ------------------------------------------------------
    # Task Management
    # ------------------------------------------------------

    def add_task(
        self,
        task
    ):

        self._tasks.append(
            task
        )


    def remove_task(
        self,
        task
    ):

        if task in self._tasks:

            self._tasks.remove(
                task
            )


    def get_tasks(self):

        return self._tasks.copy()


    # ------------------------------------------------------
    # Study Session Management
    # ------------------------------------------------------

    def add_session(
        self,
        session
    ):

        self._sessions.append(
            session
        )


        self._study_dates.add(

            session.get_study_date()

        )


    def get_sessions(self):

        return self._sessions.copy()


    # ------------------------------------------------------
    # Statistics
    # ------------------------------------------------------

    def get_total_tasks(self):

        return len(
            self._tasks
        )


    def get_completed_tasks(self):

        return len([

            task

            for task in self._tasks

            if task.is_completed()

        ])


    def get_pending_tasks(self):

        return len([

            task

            for task in self._tasks

            if not task.is_completed()

        ])


    def get_total_study_minutes(self):

        return sum(

            session.get_duration()

            for session in self._sessions

        )


    def get_study_days(self):

        return self._study_dates.copy()


    # ------------------------------------------------------
    # Dictionary Statistics
    # ------------------------------------------------------

    def get_study_hours_by_subject(self):

        study_hours = {}


        for session in self._sessions:

            subject = (

                session.get_subject()

            )


            duration = (

                session.get_duration()

            )


            if subject not in study_hours:

                study_hours[subject] = 0


            study_hours[subject] += (

                duration / 60

            )


        return study_hours