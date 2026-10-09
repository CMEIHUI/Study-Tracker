import sqlite3
from datetime import date


class TaskCrud:
    """Task CRUD helpers for the database manager."""

    def add_task(
        self,
        subject,
        title,
        description,
        priority,
        deadline,
        status="Pending",
        progress=0,
        subtasks_json="[]",
        planned_date=None,
    ):
        """Add a new task."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO tasks(
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                )
                VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    int(progress or 0),
                    subtasks_json or "[]",
                    planned_date,
                ),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_task(self, task_id):
        """Get one task by ID."""
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                subject,
                title,
                description,
                priority,
                deadline,
                status,
                progress,
                subtasks_json,
                planned_date
            FROM tasks
            WHERE id=?
            """,
            (task_id,),
        )
        task = cursor.fetchone()
        conn.close()
        return task

    def get_all_tasks(self):
        """Get all tasks."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                subject,
                title,
                description,
                priority,
                deadline,
                status,
                progress,
                subtasks_json,
                planned_date
            FROM tasks
            ORDER BY deadline ASC
            """
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_subject(self, subject):
        """Get all tasks for a specific subject."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                subject,
                title,
                description,
                priority,
                deadline,
                status,
                progress,
                subtasks_json,
                planned_date
            FROM tasks
            WHERE subject=?
            ORDER BY deadline ASC
            """,
            (subject,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_status(self, status):
        """Get tasks according to their status."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                subject,
                title,
                description,
                priority,
                deadline,
                status,
                progress,
                subtasks_json,
                planned_date
            FROM tasks
            WHERE status=?
            ORDER BY deadline ASC
            """,
            (status,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_subject_and_status(self, subject, status=None):
        """Get tasks for a subject optionally filtered by status."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        if status is None:
            cursor.execute(
                """
                SELECT
                    id,
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                FROM tasks
                WHERE subject=?
                ORDER BY deadline ASC
                """,
                (subject,),
            )
        else:
            cursor.execute(
                """
                SELECT
                    id,
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                FROM tasks
                WHERE subject=? AND status=?
                ORDER BY deadline ASC
                """,
                (subject, status),
            )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_for_date(self, deadline_date, status=None):
        """Get tasks whose deadline matches a specific date, optionally filtered by status."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        if status is None:
            cursor.execute(
                """
                SELECT
                    id,
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                FROM tasks
                WHERE deadline=?
                ORDER BY deadline ASC
                """,
                (deadline_date,),
            )
        else:
            cursor.execute(
                """
                SELECT
                    id,
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                FROM tasks
                WHERE deadline=? AND status=?
                ORDER BY deadline ASC
                """,
                (deadline_date, status),
            )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_date_range(self, start_date, end_date, status=None):
        """Get tasks whose deadline falls between two dates, optionally filtered by status."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        query = [
            "SELECT id,",
            "       subject,",
            "       title,",
            "       description,",
            "       priority,",
            "       deadline,",
            "       status,",
            "       progress,",
            "       subtasks_json,",
            "       planned_date",
            "FROM tasks",
            "WHERE deadline IS NOT NULL AND deadline != ''",
            "  AND deadline >= ? AND deadline <= ?",
        ]
        params = [start_date, end_date]
        if status is None:
            query.append("ORDER BY deadline ASC")
        else:
            query.append("  AND status = ?")
            query.append("ORDER BY deadline ASC")
            params.append(status)
        cursor.execute("\n".join(query), tuple(params))
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_upcoming_tasks(self, from_date=None, limit=10):
        """Get a limited set of upcoming tasks ordered by deadline."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        if from_date is None:
            from_date = date.today().strftime("%Y-%m-%d")
        if limit is None:
            cursor.execute(
                """
                SELECT
                    id,
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                FROM tasks
                WHERE deadline IS NOT NULL AND deadline != ''
                  AND deadline >= ?
                  AND (status IS NULL OR status != 'Completed')
                ORDER BY deadline ASC
                """,
                (from_date,),
            )
        else:
            cursor.execute(
                """
                SELECT
                    id,
                    subject,
                    title,
                    description,
                    priority,
                    deadline,
                    status,
                    progress,
                    subtasks_json,
                    planned_date
                FROM tasks
                WHERE deadline IS NOT NULL AND deadline != ''
                  AND deadline >= ?
                  AND (status IS NULL OR status != 'Completed')
                ORDER BY deadline ASC
                LIMIT ?
                """,
                (from_date, limit),
            )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_overdue_tasks(self, as_of_date=None):
        """Get tasks that are overdue relative to the provided date."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        reference_date = as_of_date or ""
        cursor.execute(
            """
            SELECT
                id,
                subject,
                title,
                description,
                priority,
                deadline,
                status,
                progress,
                subtasks_json,
                planned_date
            FROM tasks
            WHERE deadline IS NOT NULL
              AND deadline != ''
              AND deadline < ?
              AND (status IS NULL OR status != 'Completed')
            ORDER BY deadline ASC
            """,
            (reference_date,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def get_tasks_by_priority(self, priority):
        """Get tasks according to priority."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                subject,
                title,
                description,
                priority,
                deadline,
                status,
                progress,
                subtasks_json,
                planned_date
            FROM tasks
            WHERE priority=?
            ORDER BY deadline ASC
            """,
            (priority,),
        )
        tasks = cursor.fetchall()
        conn.close()
        return tasks

    def update_task(
        self,
        task_id,
        subject,
        title,
        description,
        priority,
        deadline,
        progress=None,
        subtasks_json=None,
        planned_date=None,
    ):
        """Update an existing task."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            update_clause = "subject=?, title=?, description=?, priority=?, deadline=?"
            params = [subject, title, description, priority, deadline]
            if progress is not None:
                update_clause += ", progress=?"
                params.append(int(progress))
            if subtasks_json is not None:
                update_clause += ", subtasks_json=?"
                params.append(subtasks_json)
            if planned_date is not None:
                update_clause += ", planned_date=?"
                params.append(planned_date)
            params.append(task_id)
            cursor.execute(
                f"""
                UPDATE tasks
                SET {update_clause}
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

    def delete_task(self, task_id):
        """Delete a task."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM tasks
                WHERE id=?
                """,
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error as error:
            print("Error deleting task:", error)
            return False
        finally:
            conn.close()

    def complete_task(self, task_id):
        """Mark a task as completed."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tasks
                SET status='Completed'
                WHERE id=?
                """,
                (task_id,),
            )
            conn.commit()
            self._award_gamification_event("task_completed", source_type="task", source_id=int(task_id))
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def reopen_task(self, task_id):
        """Reopen a completed task."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE tasks
                SET status='Pending'
                WHERE id=?
                """,
                (task_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_pending_tasks(self):
        """Return all pending tasks."""
        return self.get_tasks_by_status("Pending")

    def get_completed_tasks(self):
        """Return all completed tasks."""
        return self.get_tasks_by_status("Completed")

    def get_task_counts_by_status(self):
        """Return status counts in a single query."""
        conn = self.connect()
        if conn is None:
            return {"Pending": 0, "Completed": 0}
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT status, COUNT(*)
            FROM tasks
            GROUP BY status
            """
        )
        rows = cursor.fetchall()
        conn.close()
        counts = {"Pending": 0, "Completed": 0}
        for status, count in rows:
            counts[str(status or "Pending")] = int(count)
        return counts

    def total_tasks(self):
        """Return total number of tasks."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            """
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def total_completed_tasks(self):
        """Return total completed tasks."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE status='Completed'
            """
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def total_pending_tasks(self):
        """Return total pending tasks."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COUNT(*)
            FROM tasks
            WHERE status='Pending'
            """
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_task_statistics(self):
        """Return task statistics using a dictionary."""
        total = self.total_tasks()
        completed = self.total_completed_tasks()
        pending = self.total_pending_tasks()
        if total > 0:
            completion_rate = (completed / total) * 100
        else:
            completion_rate = 0
        statistics = {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completion_rate": round(completion_rate, 2),
        }
        return statistics
