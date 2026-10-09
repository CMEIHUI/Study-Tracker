import os
import shutil
import sqlite3
import tempfile
import unittest

from python.database.databasemanager import DatabaseManager
from python.database.backup_restore import backup_database, restore_database, DatabaseBackupError


class BackupRestoreTests(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.temp_db.close()
        self.database = DatabaseManager(db_name=self.temp_db.name)
        self.backup_dir = tempfile.mkdtemp()

    def tearDown(self):
        if os.path.exists(self.temp_db.name):
            os.remove(self.temp_db.name)
        if os.path.exists(self.backup_dir):
            shutil.rmtree(self.backup_dir)

    def test_backup_database_creates_backup_file(self):
        backup_path = backup_database(self.temp_db.name, os.path.join(self.backup_dir, "backup.db"))
        self.assertTrue(os.path.isfile(backup_path))
        self.assertEqual(os.path.basename(backup_path), "backup.db")

    def test_restore_database_replaces_database_file(self):
        self.database.add_task("Math", "Backup test", "desc", "High", "2026-07-20", "Pending")
        backup_path = backup_database(self.temp_db.name, os.path.join(self.backup_dir, "restore.db"))

        os.remove(self.temp_db.name)
        restored_path = restore_database(self.temp_db.name, backup_path)

        self.assertTrue(os.path.isfile(restored_path))
        conn = sqlite3.connect(restored_path)
        cursor = conn.cursor()
        cursor.execute("SELECT title FROM tasks WHERE title = ?", ("Backup test",))
        row = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "Backup test")

    def test_backup_database_raises_when_db_missing(self):
        missing_path = os.path.join(self.backup_dir, "missing.db")
        with self.assertRaises(DatabaseBackupError):
            backup_database(missing_path)

    def test_restore_database_raises_when_backup_missing(self):
        missing_backup = os.path.join(self.backup_dir, "missing_backup.db")
        with self.assertRaises(DatabaseBackupError):
            restore_database(self.temp_db.name, missing_backup)


if __name__ == "__main__":
    unittest.main()
