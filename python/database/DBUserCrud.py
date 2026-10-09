import sqlite3


class DBUserCrud:
    """User CRUD helpers for the database manager."""

    def register_user(self, username, email, password):
        """Register a new user."""

        conn = self.connect()

        if conn is None:
            return False

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                INSERT INTO users(username, email, password)
                VALUES(?, ?, ?)
                """,
                (username, email, password),
            )
            conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False
        finally:
            conn.close()

    def login_user(self, username, password):
        """Login validation."""

        conn = self.connect()

        if conn is None:
            return None

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=?
            AND password=?
            """,
            (username, password),
        )

        user = cursor.fetchone()
        conn.close()

        if not user:
            return None

        try:
            self._award_daily_login_xp(user[0])
        except Exception:
            pass

        return user

    def get_user(self, username):
        """Get a user by username."""

        conn = self.connect()

        if conn is None:
            return None

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE username=?
            """,
            (username,),
        )

        user = cursor.fetchone()
        conn.close()

        return user

    def get_all_users(self):
        """Get all users ordered by username."""

        conn = self.connect()

        if conn is None:
            return []

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            ORDER BY username
            """
        )

        users = cursor.fetchall()
        conn.close()

        return users

    def update_user(self, user_id, username, email):
        """Update an existing user's username/email."""

        conn = self.connect()

        if conn is None:
            return False

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users
                SET username=?, email=?
                WHERE id=?
                """,
                (username, email, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def update_profile(self, user_id, full_name=None, email=None, profile_picture=None):
        """Update profile fields (full name, email, profile picture) for a user."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            updates = []
            params = []
            if full_name is not None:
                updates.append("full_name=?")
                params.append(full_name)
            if email is not None:
                updates.append("email=?")
                params.append(email)
            if profile_picture is not None:
                updates.append("profile_picture=?")
                params.append(profile_picture)
            if not updates:
                return False
            params.append(user_id)
            cursor.execute(
                f"""
                UPDATE users
                SET {', '.join(updates)}
                WHERE id=?
                """,
                params,
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_user_by_id(self, user_id):
        """Get a user by its ID."""

        conn = self.connect()

        if conn is None:
            return None

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT *
            FROM users
            WHERE id=?
            """,
            (user_id,),
        )

        user = cursor.fetchone()
        conn.close()

        return user

    def set_last_login(self, user_id, last_login_value):
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE users
                SET last_login=?
                WHERE id=?
                """,
                (last_login_value, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def change_password(self, user_id, new_password):
        """Change a user's password."""

        conn = self.connect()

        if conn is None:
            return False

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                UPDATE users
                SET password=?
                WHERE id=?
                """,
                (new_password, user_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def delete_user(self, user_id):
        """Delete a user from the database."""

        conn = self.connect()

        if conn is None:
            return False

        cursor = conn.cursor()

        try:
            cursor.execute(
                """
                DELETE FROM users
                WHERE id=?
                """,
                (user_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def user_exists(self, username):
        """Check whether a username already exists."""

        conn = self.connect()

        if conn is None:
            return False

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE username=?
            """,
            (username,),
        )

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def email_exists(self, email):
        """Check whether an email already exists."""

        conn = self.connect()

        if conn is None:
            return False

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT id
            FROM users
            WHERE email=?
            """,
            (email,),
        )

        result = cursor.fetchone()
        conn.close()

        return result is not None

    def total_users(self):
        """Return the total number of users."""

        conn = self.connect()

        if conn is None:
            return 0

        cursor = conn.cursor()

        cursor.execute(
            """
            SELECT COUNT(*)
            FROM users
            """
        )

        total = cursor.fetchone()[0]
        conn.close()

        return total