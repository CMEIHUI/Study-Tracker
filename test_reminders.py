import tempfile
from datetime import datetime, timedelta

from reminders import Reminder, ReminderManager
from database import DatabaseManager


def make_temp_database():
    temp_file = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
    temp_file.close()
    return DatabaseManager(temp_file.name)


def test_add_and_load_reminder():
    database = make_temp_database()
    manager = ReminderManager(database)
    reminder = Reminder(
        reminder_id=None,
        title="Study SQL",
        message="Review joins and aggregations.",
        reminder_type="Study",
        due_at=(datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
        repeat="Daily",
    )
    assert manager.add_reminder(reminder) is True

    reminders = manager.get_reminders(unread_only=True)
    assert len(reminders) == 1
    assert reminders[0].title == "Study SQL"
    assert reminders[0].repeat == "Daily"


def test_mark_reminder_done():
    database = make_temp_database()
    manager = ReminderManager(database)
    reminder = Reminder(
        reminder_id=None,
        title="Task due",
        message="Finish the assignment.",
        reminder_type="Task",
        due_at=datetime.now().strftime("%Y-%m-%d"),
        repeat="Once",
    )
    assert manager.add_reminder(reminder) is True
    reminders = manager.get_reminders(unread_only=True)
    assert len(reminders) == 1
    assert manager.mark_reminder_done(reminders[0].id) is True
    assert manager.get_reminders(unread_only=True) == []
