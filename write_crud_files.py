from pathlib import Path

files = {
    Path('python/database/SubjectCrud.py'): '''import sqlite3


class SubjectCrud:
    \"\"\"Subject CRUD helpers for the database manager.\"\"\"

    def add_subject(self, name, color):
        \"\"\"Add a new subject.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                INSERT INTO subjects(name, color)
                VALUES(?, ?)
                \"\"\",
                (name, color),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_subject(self, subject_id):
        \"\"\"Get one subject by ID.\"\"\"
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM subjects
            WHERE id=?
            \"\"\",
            (subject_id,),
        )
        subject = cursor.fetchone()
        conn.close()
        return subject

    def get_subject_by_name(self, name):
        \"\"\"Get one subject by name.\"\"\"
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM subjects
            WHERE name=?
            \"\"\",
            (name,),
        )
        subject = cursor.fetchone()
        conn.close()
        return subject

    def get_all_subjects(self):
        \"\"\"Get all subjects.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM subjects
            ORDER BY name ASC
            \"\"\"
        )
        subjects = cursor.fetchall()
        conn.close()
        return subjects

    def update_subject(self, subject_id, name, color):
        \"\"\"Update a subject record.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                UPDATE subjects
                SET name=?, color=?
                WHERE id=?
                \"\"\",
                (name, color, subject_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def delete_subject(self, subject_id):
        \"\"\"Delete a subject.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                DELETE FROM subjects
                WHERE id=?
                \"\"\",
                (subject_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def subject_exists(self, name):
        \"\"\"Check whether a subject already exists.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT id
            FROM subjects
            WHERE name=?
            \"\"\",
            (name,),
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def total_subjects(self):
        \"\"\"Return total number of subjects.\"\"\"
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT COUNT(*)
            FROM subjects
            \"\"\"
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_subject_names(self):
        \"\"\"Return subject names as a list.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT name
            FROM subjects
            ORDER BY name ASC
            \"\"\"
        )
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
''',

    Path('python/database/TaskCrud.py'): '''import sqlite3


class TaskCrud:
    \"\"\"Task CRUD helpers for the database manager.\"\"\"

    def add_task(self, subject, title, description, priority, deadline, status=\"Pending\"):
        \"\"\"Add a new task.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                INSERT INTO tasks(subject, title, description, priority, deadline, status)
                VALUES(?, ?, ?, ?, ?, ?)
                \"\"\",
                (subject, title, description, priority, deadline, status),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_task(self, task_id):
        \"\"\"Get one task by ID.\"\"\"
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM tasks
            WHERE id=?
            \"\"\",
            (task_id,),
        )
        task = cursor.fetchone()
        conn.close()
        return task

    def get_all_tasks(self):
        \"\"\"Get all tasks.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM tasks
            ORDER BY deadline ASC
            \"\"\"
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_subject(self, subject):
        \"\"\"Get all tasks for a specific subject.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM tasks
            WHERE subject=?
            ORDER BY deadline ASC
            \"\"\",
            (subject,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_status(self, status):
        \"\"\"Get tasks according to their status.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM tasks
            WHERE status=?
            ORDER BY deadline ASC
            \"\"\",
            (status,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_priority(self, priority):
        \"\"\"Get tasks according to priority.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM tasks
            WHERE priority=?
            ORDER BY deadline ASC
            \"\"\",
            (priority,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def update_task(self, task_id, subject, title, description, priority, deadline):
        \"\"\"Update an existing task.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                UPDATE tasks
                SET subject=?, title=?, description=?, priority=?, deadline=?
                WHERE id=?
                \"\"\",
                (subject, title, description, priority, deadline, task_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def delete_task(self, task_id):
        \"\"\"Delete a task.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                DELETE FROM tasks
                WHERE id=?
                \"\"\",
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as error:
            print(\"Error deleting task:\", error)
            return False
        finally:
            conn.close()

    def complete_task(self, task_id):
        \"\"\"Mark a task as completed.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                UPDATE tasks
                SET status='Completed'
                WHERE id=?
                \"\"\",
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def reopen_task(self, task_id):
        \"\"\"Reopen a completed task.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                UPDATE tasks
                SET status='Pending'
                WHERE id=?
                \"\"\",
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_pending_tasks(self):
        \"\"\"Return all pending tasks.\"\"\"
        return self.get_tasks_by_status(\"Pending\")

    def get_completed_tasks(self):
        \"\"\"Return all completed tasks.\"\"\"
        return self.get_tasks_by_status(\"Completed\")

    def total_tasks(self):
        \"\"\"Return total number of tasks.\"\"\"
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT COUNT(*)
            FROM tasks
            \"\"\"
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def total_completed_tasks(self):
        \"\"\"Return total completed tasks.\"\"\"
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT COUNT(*)
            FROM tasks
            WHERE status='Completed'
            \"\"\"
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def total_pending_tasks(self):
        \"\"\"Return total pending tasks.\"\"\"
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT COUNT(*)
            FROM tasks
            WHERE status='Pending'
            \"\"\"
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_task_statistics(self):
        \"\"\"Return task statistics using a dictionary.\"\"\"
        total = self.total_tasks()
        completed = self.total_completed_tasks()
        pending = self.total_pending_tasks()
        if total > 0:
            completion_rate = (completed / total) * 100
        else:
            completion_rate = 0
        statistics = {
            \"total\": total,
            \"completed\": completed,
            \"pending\": pending,
            \"completion_rate\": round(completion_rate, 2),
        }
        return statistics
''',

    Path('python/database/studyseesioncrud.py'): '''import sqlite3


class StudySessionCrud:
    \"\"\"Study session CRUD helpers for the database manager.\"\"\"

    def add_study_session(self, subject, duration, study_date):
        \"\"\"Add a new study session.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                INSERT INTO study_sessions(subject, duration, study_date)
                VALUES(?, ?, ?)
                \"\"\",
                (subject, duration, study_date),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_all_study_sessions(self):
        \"\"\"Get all study sessions ordered by study date.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                SELECT *
                FROM study_sessions
                ORDER BY study_date DESC
                \"\"\"
            )
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def get_study_sessions_by_subject(self, subject):
        \"\"\"Get study sessions for a specific subject.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM study_sessions
            WHERE subject=?
            ORDER BY study_date DESC
            \"\"\",
            (subject,),
        )
        sessions = cursor.fetchall()
        conn.close()
        return sessions

    def get_total_study_minutes(self):
        \"\"\"Return the total study minutes.\"\"\"
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT COALESCE(SUM(duration), 0)
            FROM study_sessions
            \"\"\"
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_total_study_hours(self):
        \"\"\"Return total study hours.\"\"\"
        total_minutes = self.get_total_study_minutes()
        return round(total_minutes / 60, 2)

    def get_study_hours_by_subject(self):
        \"\"\"Return study hours aggregated by subject.\"\"\"
        conn = self.connect()
        if conn is None:
            return {}
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT subject, SUM(duration)
            FROM study_sessions
            GROUP BY subject
            \"\"\"
        )
        rows = cursor.fetchall()
        conn.close()
        study_hours = {}
        for subject_name, minutes in rows:
            study_hours[subject_name] = round(minutes / 60, 2)
        return study_hours

    def delete_study_session(self, session_id):
        \"\"\"Delete a study session.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                DELETE FROM study_sessions
                WHERE id=?
                \"\"\",
                (session_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def add_note(self, subject, note, created_date):
        \"\"\"Add a study note.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                INSERT INTO notes(subject, note, created_date)
                VALUES(?, ?, ?)
                \"\"\",
                (subject, note, created_date),
            )
            conn.commit()
            return True
        except sqlite3.Error as error:
            print(\"Error adding note:\", error)
            return False
        finally:
            conn.close()

    def get_all_notes(self):
        \"\"\"Get all notes.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM notes
            ORDER BY created_date DESC
            \"\"\"
        )
        notes = cursor.fetchall()
        conn.close()
        return notes

    def get_notes_by_subject(self, subject):
        \"\"\"Get notes for a specific subject.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM notes
            WHERE subject=?
            ORDER BY created_date DESC
            \"\"\",
            (subject,),
        )
        notes = cursor.fetchall()
        conn.close()
        return notes

    def update_note(self, note_id, subject, note, created_date):
        \"\"\"Update a study note.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                UPDATE notes
                SET subject=?, note=?, created_date=?
                WHERE id=?
                \"\"\",
                (subject, note, created_date, note_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def delete_note(self, note_id):
        \"\"\"Delete a study note.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                DELETE FROM notes
                WHERE id=?
                \"\"\",
                (note_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def add_achievement(self, title, description, unlocked=0):
        \"\"\"Add an achievement.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                INSERT INTO achievements(title, description, unlocked)
                VALUES(?, ?, ?)
                \"\"\",
                (title, description, unlocked),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_all_achievements(self):
        \"\"\"Get all achievements.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM achievements
            ORDER BY id
            \"\"\"
        )
        achievements = cursor.fetchall()
        conn.close()
        return achievements

    def unlock_achievement(self, achievement_id):
        \"\"\"Unlock an achievement.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                \"\"\"
                UPDATE achievements
                SET unlocked=1
                WHERE id=?
                \"\"\",
                (achievement_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_settings(self):
        \"\"\"Get the most recent settings row.\"\"\"
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT *
            FROM settings
            ORDER BY id DESC
            LIMIT 1
            \"\"\"
        )
        settings = cursor.fetchone()
        conn.close()
        return settings

    def save_settings(self, theme, notification, pomodoro_time):
        \"\"\"Save the app settings.\"\"\"
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(\"DELETE FROM settings\")
            cursor.execute(
                \"\"\"
                INSERT INTO settings(theme, notification, pomodoro_time)
                VALUES(?, ?, ?)
                \"\"\",
                (theme, notification, pomodoro_time),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_daily_study_statistics(self):
        \"\"\"Return daily study statistics.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT study_date, SUM(duration)
            FROM study_sessions
            GROUP BY study_date
            ORDER BY study_date
            \"\"\"
        )
        statistics = cursor.fetchall()
        conn.close()
        return statistics

    def get_subject_statistics(self):
        \"\"\"Return subject study statistics.\"\"\"
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT subject, SUM(duration)
            FROM study_sessions
            GROUP BY subject
            ORDER BY SUM(duration) DESC
            \"\"\"
        )
        statistics = cursor.fetchall()
        conn.close()
        return statistics

    def get_study_dates(self):
        \"\"\"Return the distinct study dates.\"\"\"
        conn = self.connect()
        if conn is None:
            return set()
        cursor = conn.cursor()
        cursor.execute(
            \"\"\"
            SELECT DISTINCT study_date
            FROM study_sessions
            \"\"\"
        )
        rows = cursor.fetchall()
        conn.close()
        study_dates = set()
        for row in rows:
            study_dates.add(row[0])
        return study_dates

    def get_dashboard_statistics(self):
        \"\"\"Return dashboard statistics.\"\"\"
        task_statistics = self.get_task_statistics()
        study_hours = self.get_total_study_hours()
        total_subjects = self.total_subjects()
        statistics = {
            \"total_tasks\": task_statistics[\"total\"],
            \"completed_tasks\": task_statistics[\"completed\"],
            \"pending_tasks\": task_statistics[\"pending\"],
            \"completion_rate\": task_statistics[\"completion_rate\"],
            \"study_hours\": study_hours,
            \"subjects\": total_subjects,
        }
        return statistics
''',
}
for path, content in files.items():
    path.write_text(content, encoding='utf-8')
    print('wrote', path)
