import hashlib
import logging
import threading

from datetime import datetime


LOGGER = logging.getLogger("study_tracker")
LOGGER.addHandler(logging.NullHandler())


class ValidationError(ValueError):
    """Raised when a user input is invalid or missing."""


def validate_required_field(value, field_name, allow_empty=False):
    """Ensure a required field is present and not blank."""
    if value is None:
        raise ValidationError(f"{field_name} is required.")
    if isinstance(value, str):
        value = value.strip()
    if not value and not allow_empty:
        raise ValidationError(f"{field_name} is required.")
    return value


def validate_date_string(value, field_name):
    """Validate that a date string is in YYYY-MM-DD format."""
    cleaned = validate_required_field(value, field_name, allow_empty=True)
    if cleaned in (None, ""):
        return ""
    try:
        datetime.strptime(cleaned, "%Y-%m-%d")
    except ValueError as exc:
        raise ValidationError(f"{field_name} must use YYYY-MM-DD format.") from exc
    return cleaned


# ==========================================================
# PASSWORD HASHING
# ==========================================================

def hash_password(password):

    """
    Convert a plain-text password into a secure hash.

    Parameters:
        password (str): User password

    Returns:
        str: SHA-256 hashed password
    """

    password_bytes = password.encode(

        "utf-8"

    )


    hashed_password = hashlib.sha256(

        password_bytes

    ).hexdigest()


    return hashed_password


# ==========================================================
# VERIFY PASSWORD
# ==========================================================

def verify_password(

    password,

    hashed_password

):

    """
    Verify whether a password matches
    the stored password hash.
    """

    return (

        hash_password(

            password

        )

        == hashed_password

    )


# ==========================================================
# VALIDATE DATE
# ==========================================================

def validate_date(

    date_string

):

    """
    Validate date format.

    Required format:

        YYYY-MM-DD

    Example:

        2026-07-16
    """

    try:

        datetime.strptime(

            date_string,

            "%Y-%m-%d"

        )


        return True


    except ValueError:

        return False


# ==========================================================
# FORMAT MINUTES
# ==========================================================

def format_minutes(

    minutes

):

    """
    Convert minutes into hours and minutes.

    Example:

        90 minutes

    becomes:

        1 hour 30 minutes
    """

    minutes = int(

        minutes

    )


    hours = minutes // 60


    remaining_minutes = minutes % 60


    if hours > 0:

        return (

            f"{hours} hour(s) "

            f"{remaining_minutes} minute(s)"

        )


    return (

        f"{remaining_minutes} minute(s)"

    )


# ==========================================================
# GET CURRENT DATE
# ==========================================================

def get_current_date():

    """

    Return the current date.

    Format:

        YYYY-MM-DD
    """

    return datetime.now().strftime(

        "%Y-%m-%d"

    )


# ==========================================================
# GET CURRENT DATETIME
# ==========================================================

def get_current_datetime():

    """

    Return current date and time.
    """

    return datetime.now().strftime(

        "%Y-%m-%d %H:%M:%S"

    )


# ==========================================================
# CALCULATE COMPLETION RATE
# ==========================================================

def _schedule_ui_callback(widget, callback, *args):
    """Safely schedule a callback on the Tkinter UI thread when possible."""
    if callback is None:
        return False
    if widget is None:
        try:
            callback(*args)
            return True
        except Exception:
            return False
    try:
        if hasattr(widget, "winfo_exists") and not widget.winfo_exists():
            return False
        if hasattr(widget, "after"):
            try:
                widget.after(0, lambda: callback(*args))
                return True
            except Exception:
                return False
    except Exception:
        # Widget may not be attached to an active Tk event loop.
        return False

    try:
        callback(*args)
        return True
    except Exception:
        return False


def handle_operation_error(error, context=None, user_message="We couldn't complete that action right now."):
    """Log a technical error and return a safe user-facing message."""
    message_context = context or "operation"
    if isinstance(error, ValidationError):
        # Ensure validation problems are logged at ERROR so tests and monitoring capture them
        LOGGER.error("Validation error during %s: %s", message_context, error)
        return user_message

    LOGGER.exception("Unhandled error during %s", message_context)
    return user_message


def run_in_background(widget, target, callback=None, error_callback=None, *args, **kwargs):
    """Run a blocking function in a background thread and update the UI on completion."""
    def worker():
        try:
            result = target(*args, **kwargs)
            _schedule_ui_callback(widget, callback, result)
        except Exception as exc:
            safe_message = handle_operation_error(exc, context=kwargs.get("context") or getattr(target, "__name__", "background operation"))
            _schedule_ui_callback(widget, error_callback, exc, safe_message)

    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return thread


def set_loading_state(label_widget=None, button_widget=None, text="", loading=False):
    """Update a status label and button state for async work without touching the UI from a worker thread."""
    if label_widget is not None:
        try:
            label_widget.configure(text=text)
        except Exception:
            pass
    if button_widget is not None:
        try:
            button_widget.configure(state="disabled" if loading else "normal")
        except Exception:
            pass


def animate_progress(progress_widget, target, duration=400, steps=20):
    """Animate a CTkProgressBar from its last known value to target (0..1).

    Stores the animated value on the widget as `_animated_value` to preserve state.
    Uses `after` to smoothly step the progress over `duration` milliseconds.
    """
    try:
        target = float(max(0.0, min(1.0, float(target))))
    except Exception:
        try:
            progress_widget.set(max(0.0, min(1.0, float(target))))
        except Exception:
            pass
        return

    try:
        current = float(getattr(progress_widget, "_animated_value", 0.0) or 0.0)
    except Exception:
        current = 0.0

    try:
        steps = max(1, int(steps))
        delta = (target - current) / steps

        def step(i=0, val=current):
            new_val = val + delta
            try:
                progress_widget.set(max(0.0, min(1.0, new_val)))
                setattr(progress_widget, "_animated_value", new_val)
            except Exception:
                pass
            if i < steps - 1:
                try:
                    progress_widget.after(int(duration / steps), lambda: step(i + 1, new_val))
                except Exception:
                    pass

        step()
    except Exception:
        try:
            progress_widget.set(target)
            setattr(progress_widget, "_animated_value", target)
        except Exception:
            pass


def calculate_completion_rate(

    completed_tasks,

    total_tasks

):

    """

    Calculate task completion percentage.
    """

    if total_tasks == 0:

        return 0


    return (

        completed_tasks

        / total_tasks

    ) * 100


# ==========================================================
# CLEAN TEXT
# ==========================================================

def clean_text(

    text

):

    """

    Remove unnecessary spaces
    from user input.
    """

    if text is None:

        return ""


    return text.strip()


# ==========================================================
# CHECK EMPTY VALUE
# ==========================================================

def is_empty(

    value

):

    """

    Check whether a value is empty.
    """

    if value is None:

        return True


    if str(value).strip() == "":

        return True


    return False


# ==========================================================
# GET PRIORITY VALUE
# ==========================================================

def get_priority_value(

    priority

):

    """

    Return numerical priority value.

    High   = 3
    Medium = 2
    Low    = 1
    """

    priority_values = {

        "High": 3,

        "Medium": 2,

        "Low": 1

    }


    return priority_values.get(

        priority,

        0

    )


# ==========================================================
# SORT TASKS BY PRIORITY
# ==========================================================

def sort_tasks_by_priority(

    tasks

):

    """

    Sort tasks based on priority.

    This function uses:

    - List
    - Dictionary
    - Lambda function
    """

    return sorted(

        tasks,

        key=lambda task:

        get_priority_value(

            task[4]

        ),

        reverse=True

    )