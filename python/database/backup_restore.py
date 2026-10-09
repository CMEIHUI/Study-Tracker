"""Backup and restore helpers for Study Tracker Pro."""

import os
import shutil
import sqlite3
from datetime import datetime
import gc


class DatabaseBackupError(Exception):
    """Raised when a backup or restore operation fails."""


def get_default_backup_name(db_path):
    base, ext = os.path.splitext(os.path.basename(db_path))
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_backup_{timestamp}{ext}"


def ensure_database_path(db_path):
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path), exist_ok=True)


def backup_database(db_path, backup_path=None):
    """Create a safe backup copy of the SQLite database."""
    if not db_path:
        raise DatabaseBackupError("Database path is required for backup.")

    if not os.path.isfile(db_path):
        raise DatabaseBackupError(f"Database file not found: {db_path}")

    backup_path = backup_path or os.path.join(
        os.path.dirname(db_path),
        get_default_backup_name(db_path),
    )

    ensure_database_path(os.path.dirname(backup_path))

    try:
        # Use a straightforward file copy to create the backup. This avoids
        # keeping sqlite3 connection objects alive which can lock files on Windows.
        shutil.copy2(db_path, backup_path)
    except OSError as exc:
        raise DatabaseBackupError(f"Unable to backup database: {exc}") from exc

    try:
        gc.collect()
    except Exception:
        pass

    return backup_path


def restore_database(db_path, backup_path):
    """Restore the SQLite database from a backup file."""
    if not db_path or not backup_path:
        raise DatabaseBackupError("Both database path and backup path are required for restore.")

    if not os.path.isfile(backup_path):
        raise DatabaseBackupError(f"Backup file not found: {backup_path}")

    ensure_database_path(os.path.dirname(db_path))

    try:
        shutil.copy2(backup_path, db_path)
    except OSError as exc:
        raise DatabaseBackupError(f"Unable to restore database: {exc}") from exc

    try:
        gc.collect()
    except Exception:
        pass

    return db_path
