"""Database management for the study tracker app."""

import os
import sqlite3
from sqlite3 import Error

from .DBUserCrud import DBUserCrud
from .SubjectCrud_repair import SubjectCrud
from .TaskCrud_repair import TaskCrud
from .backup_restore import backup_database as _backup_database
from .backup_restore import restore_database as _restore_database
from .studyseesioncrud_repair import StudySessionCrud


class DatabaseError(Exception):
    """Raised when a database operation cannot be completed."""


class DatabaseManager(DBUserCrud, SubjectCrud, TaskCrud, StudySessionCrud):
    """Create tables and expose CRUD methods for the app."""

    def __init__(self, db_name="studytracker.db"):
        if db_name == ":memory:" or db_name.startswith("file:"):
            self.db_name = db_name
        else:
            self.db_name = os.path.abspath(db_name)
        self._ensure_database_directory()
        self.create_tables()

    def _ensure_database_directory(self):
        if self.db_name == ":memory:" or self.db_name.startswith("file:"):
            return
        directory = os.path.dirname(self.db_name)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)

    def _ensure_column(self, table_name, column_name, column_definition):
        """Add a missing column to an existing table without deleting data."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if column_name not in columns:
                cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_definition}")
                conn.commit()
            conn.close()
            return True
        except sqlite3.Error:
            conn.close()
            return False

    def _create_calendar_events_table(self):
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS calendar_events(
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    event_date TEXT,
                    event_type TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as exc:
            print("Migration warning:", exc)
            conn.close()
            return False

    def add_calendar_event(self, title, event_date, event_type="Study"):
        """Add a calendar event entry while keeping the existing task-based calendar flow intact."""
        self._create_calendar_events_table()
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO calendar_events(title, event_date, event_type)
                VALUES(?, ?, ?)
                """,
                (title, event_date, event_type),
            )
            conn.commit()
            conn.close()
            return True
        except sqlite3.Error as exc:
            print("Calendar event error:", exc)
            conn.close()
            return False

    def get_all_calendar_events(self):
        """Return all persisted calendar events."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, title, event_date, event_type, created_at
                FROM calendar_events
                ORDER BY event_date ASC, created_at ASC
                """
            )
            rows = cursor.fetchall()
            conn.close()
            return rows
        except sqlite3.Error:
            conn.close()
            return []

    def connect(self):
        """Create a connection to the SQLite database."""

        self._ensure_database_directory()
        try:
            if self.db_name.startswith("file:"):
                connection = sqlite3.connect(self.db_name, timeout=30, uri=True)
            else:
                connection = sqlite3.connect(self.db_name, timeout=30)
            connection.execute("PRAGMA foreign_keys = ON")
            return connection
        except Error as exc:
            print("Database Error:", exc)
            return None

    def backup_database(self, backup_path=None):
        """Create a database backup and return the backup path."""
        if not self.db_name:
            raise DatabaseError("Database path has not been initialized.")
        return _backup_database(self.db_name, backup_path)

    def restore_database(self, backup_path):
        """Restore the database from an existing backup file."""
        if not self.db_name:
            raise DatabaseError("Database path has not been initialized.")
        return _restore_database(self.db_name, backup_path)

    def create_tables(self):
        """Create or initialize the SQLite tables used by the app."""

        conn = self.connect()

        if conn is None:
            return

        cursor = conn.cursor()

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                full_name TEXT DEFAULT '',
                profile_picture TEXT DEFAULT '',
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                last_login TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS subjects(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                color TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                title TEXT,
                description TEXT,
                priority TEXT,
                deadline TEXT,
                status TEXT,
                progress INTEGER DEFAULT 0,
                subtasks_json TEXT DEFAULT '[]',
                planned_date TEXT
            )
            """
        )
        # Ensure migrations: add missing columns if older schema exists
        try:
            self._ensure_column("tasks", "planned_date", "planned_date TEXT")
            self._ensure_column("tasks", "subtasks_json", "subtasks_json TEXT DEFAULT '[]'")
            self._ensure_column("tasks", "progress", "progress INTEGER DEFAULT 0")
        except Exception:
            # Best-effort migration; continue even if migration helpers fail
            pass

        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_subject ON tasks(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_deadline ON tasks(deadline)")
        # planned_date index may fail if the column cannot be added; wrap to avoid crash
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_planned_date ON tasks(planned_date)")
        except sqlite3.OperationalError:
            pass
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_tasks_status_deadline ON tasks(status, deadline)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS study_sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                duration INTEGER,
                study_date TEXT
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_subject ON study_sessions(subject)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_study_sessions_date ON study_sessions(study_date)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS study_streaks(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                current_streak INTEGER DEFAULT 0,
                longest_streak INTEGER DEFAULT 0,
                last_active_date TEXT,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notes(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                subject TEXT,
                note TEXT,
                created_date TEXT
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS achievements(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT,
                description TEXT,
                unlocked INTEGER
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS gamification_profiles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                total_xp INTEGER DEFAULT 0,
                coins INTEGER DEFAULT 0,
                level INTEGER DEFAULT 1,
                current_level_xp INTEGER DEFAULT 0,
                current_level_target INTEGER DEFAULT 100,
                updated_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS gamification_events(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                event_type TEXT NOT NULL,
                xp_awarded INTEGER DEFAULT 0,
                coins_awarded INTEGER DEFAULT 0,
                source_type TEXT,
                source_id INTEGER,
                event_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS goals(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                goal_type TEXT NOT NULL,
                target_minutes INTEGER DEFAULT 0,
                current_minutes INTEGER DEFAULT 0,
                period_start TEXT,
                period_end TEXT,
                completed INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS notifications(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                message TEXT NOT NULL,
                is_read INTEGER DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pomodoro_sessions(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_type TEXT NOT NULL,
                duration INTEGER NOT NULL,
                session_date TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_pomodoro_sessions_date ON pomodoro_sessions(session_date)")

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS ai_history(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query_text TEXT NOT NULL,
                response_text TEXT NOT NULL,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
            """
        )

        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS settings(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                theme TEXT,
                notification INTEGER,
                pomodoro_time INTEGER,
                settings_json TEXT
            )
            """
        )

        self._ensure_column("settings", "settings_json", "settings_json TEXT")
        # Ensure user profile columns exist for existing databases
        try:
            self._ensure_column("users", "full_name", "full_name TEXT DEFAULT ''")
            self._ensure_column("users", "profile_picture", "profile_picture TEXT DEFAULT ''")
            self._ensure_column("users", "created_at", "created_at TEXT DEFAULT CURRENT_TIMESTAMP")
            self._ensure_column("users", "last_login", "last_login TEXT")
        except Exception:
            pass

        conn.commit()
        conn.close()