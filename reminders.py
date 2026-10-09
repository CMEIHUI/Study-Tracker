import logging
import platform
import threading
from datetime import datetime, timedelta
from typing import List, Optional

try:
    from plyer import notification
except ImportError:
    notification = None

from database import DatabaseManager

LOGGER = logging.getLogger(__name__)

REMINDER_TYPES = ["Study", "Exam", "Task"]
REPEAT_OPTIONS = ["Once", "Daily", "Weekly", "Monthly"]


def get_notification_backend_available() -> bool:
    return notification is not None


class Reminder:
    def __init__(
        self,
        reminder_id: Optional[int],
        title: str,
        message: str,
        reminder_type: str,
        due_at: str,
        repeat: str = "Once",
        is_done: int = 0,
        created_at: Optional[str] = None,
    ):
        self.id = reminder_id
        self.title = title
        self.message = message
        self.reminder_type = reminder_type
        self.due_at = due_at
        self.repeat = repeat
        self.is_done = is_done
        self.created_at = created_at or datetime.now().isoformat()

    def to_tuple(self):
        return (
            self.title,
            self.message,
            self.reminder_type,
            self.due_at,
            self.repeat,
            self.is_done,
        )

    @staticmethod
    def parse(row):
        if not row:
            return None
        return Reminder(
            reminder_id=row[0],
            title=row[1],
            message=row[2],
            reminder_type=row[3],
            due_at=row[4],
            repeat=row[5],
            is_done=row[6],
            created_at=row[7],
        )


class ReminderManager:
    def __init__(self, database: DatabaseManager = None):
        self.database = database or DatabaseManager()
        self._scheduler_thread = None
        self._stop_event = threading.Event()
        self._ensure_reminders_table()

    def _ensure_reminders_table(self) -> bool:
        conn = self.database.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS reminders(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    message TEXT NOT NULL,
                    reminder_type TEXT NOT NULL,
                    due_at TEXT NOT NULL,
                    repeat TEXT DEFAULT 'Once',
                    is_done INTEGER DEFAULT 0,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            return True
        except Exception as exc:
            LOGGER.warning("Unable to create reminders table: %s", exc)
            return False
        finally:
            conn.close()

    def add_reminder(self, reminder: Reminder) -> bool:
        conn = self.database.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO reminders(title, message, reminder_type, due_at, repeat, is_done)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                reminder.to_tuple(),
            )
            conn.commit()
            return True
        except Exception as exc:
            LOGGER.warning("Unable to save reminder: %s", exc)
            return False
        finally:
            conn.close()

    def get_reminders(self, due_before: Optional[str] = None, unread_only: bool = False) -> List[Reminder]:
        conn = self.database.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            query = "SELECT id, title, message, reminder_type, due_at, repeat, is_done, created_at FROM reminders"
            clauses = []
            params = []
            if unread_only:
                clauses.append("is_done=0")
            if due_before:
                clauses.append("due_at <= ?")
                params.append(due_before)
            if clauses:
                query += " WHERE " + " AND ".join(clauses)
            query += " ORDER BY due_at ASC, created_at ASC"
            cursor.execute(query, tuple(params))
            return [Reminder.parse(row) for row in cursor.fetchall()]
        except Exception as exc:
            LOGGER.warning("Unable to load reminders: %s", exc)
            return []
        finally:
            conn.close()

    def mark_reminder_done(self, reminder_id: int) -> bool:
        conn = self.database.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE reminders SET is_done=1 WHERE id=?",
                (reminder_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as exc:
            LOGGER.warning("Unable to mark reminder done: %s", exc)
            return False
        finally:
            conn.close()

    def _calculate_next_due(self, reminder: Reminder) -> Optional[str]:
        try:
            due = datetime.fromisoformat(reminder.due_at)
        except ValueError:
            return None
        if reminder.repeat == "Daily":
            return (due + timedelta(days=1)).isoformat()
        if reminder.repeat == "Weekly":
            return (due + timedelta(weeks=1)).isoformat()
        if reminder.repeat == "Monthly":
            month = due.month + 1
            year = due.year + (month - 1) // 12
            month = (month - 1) % 12 + 1
            day = min(due.day, 28)
            return datetime(year, month, day, due.hour, due.minute, due.second).isoformat()
        return None

    def update_reminder(self, reminder: Reminder) -> bool:
        if reminder.id is None:
            return False
        conn = self.database.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE reminders
                SET title=?, message=?, reminder_type=?, due_at=?, repeat=?, is_done=?
                WHERE id=?
                """,
                (
                    reminder.title,
                    reminder.message,
                    reminder.reminder_type,
                    reminder.due_at,
                    reminder.repeat,
                    reminder.is_done,
                    reminder.id,
                ),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as exc:
            LOGGER.warning("Unable to update reminder: %s", exc)
            return False
        finally:
            conn.close()

    def reschedule_reminder(self, reminder: Reminder) -> bool:
        next_due = self._calculate_next_due(reminder)
        if not next_due:
            return False
        conn = self.database.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "UPDATE reminders SET due_at=?, is_done=0 WHERE id=?",
                (next_due, reminder.id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except Exception as exc:
            LOGGER.warning("Unable to reschedule reminder: %s", exc)
            return False
        finally:
            conn.close()

    def _notify_desktop(self, reminder: Reminder):
        if notification is None:
            return
        try:
            notification.notify(
                title=f"{reminder.reminder_type} Reminder",
                message=f"{reminder.title}: {reminder.message}",
                timeout=10,
            )
        except Exception as exc:
            LOGGER.warning("Desktop notification failed: %s", exc)

    def dispatch_due_reminders(self):
        due_now = datetime.now().isoformat()
        reminders = self.get_reminders(due_before=due_now, unread_only=True)
        for reminder in reminders:
            self._notify_desktop(reminder)
            if reminder.repeat != "Once":
                self.reschedule_reminder(reminder)
            else:
                self.mark_reminder_done(reminder.id)

    def start_scheduler(self, interval_seconds: int = 60):
        if self._scheduler_thread and self._scheduler_thread.is_alive():
            return
        self._stop_event.clear()

        def scheduler():
            while not self._stop_event.is_set():
                try:
                    self.dispatch_due_reminders()
                except Exception as exc:
                    LOGGER.warning("Reminder scheduler error: %s", exc)
                self._stop_event.wait(interval_seconds)

        self._scheduler_thread = threading.Thread(target=scheduler, daemon=True)
        self._scheduler_thread.start()

    def stop_scheduler(self):
        self._stop_event.set()
        if self._scheduler_thread is not None:
            self._scheduler_thread.join(timeout=1)
