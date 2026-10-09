import sqlite3


class SubjectCrud:
    """Subject CRUD helpers for the database manager."""

    def add_subject(self, name, color):
        """Add a new subject."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO subjects(name, color)
                VALUES(?, ?)
                """,
                (name, color),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_subject(self, subject_id):
        """Get one subject by ID."""
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM subjects
            WHERE id=?
            """,
            (subject_id,),
        )
        subject = cursor.fetchone()
        conn.close()
        return subject

    def get_subject_by_name(self, name):
        """Get one subject by name."""
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM subjects
            WHERE name=?
            """,
            (name,),
        )
        subject = cursor.fetchone()
        conn.close()
        return subject

    def get_all_subjects(self):
        """Get all subjects."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM subjects
            ORDER BY name ASC
            """
        )
        subjects = cursor.fetchall()
        conn.close()
        return subjects

    def update_subject(self, subject_id, name, color):
        """Update a subject record."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE subjects
                SET name=?, color=?
                WHERE id=?
                """,
                (name, color, subject_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def delete_subject(self, subject_id):
        """Delete a subject."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM subjects
                WHERE id=?
                """,
                (subject_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def subject_exists(self, name):
        """Check whether a subject already exists."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id
            FROM subjects
            WHERE name=?
            """,
            (name,),
        )
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def total_subjects(self):
        """Return total number of subjects."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM subjects
            """
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_subject_names(self):
        """Return subject names as a list."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT name
            FROM subjects
            ORDER BY name ASC
            """
        )
        rows = cursor.fetchall()
        conn.close()
        return [row[0] for row in rows]
