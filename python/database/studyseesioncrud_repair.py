import calendar
import sqlite3
from datetime import date, timedelta


class StudySessionCrud:
    """Study session CRUD helpers for the database manager."""

    XP_BADGE_THRESHOLDS = [
        (100, "Bronze Badge"),
        (500, "Silver Badge"),
        (1000, "Gold Badge"),
    ]

    def _compute_level(self, total_xp):
        """Compute the current level from total XP."""
        level = 1 + max(0, int(total_xp or 0) // 100)
        current_level_xp = int(total_xp or 0) % 100
        return level, current_level_xp

    def _compute_badges(self, total_xp, current_streak):
        """Return badge metadata and unlocked state based on XP and streak."""
        return [
            {
                "title": "🥉 Beginner Scholar",
                "description": "Earn 100 XP to receive your first study badge.",
                "reward": "Bronze Badge",
                "unlocked": int(total_xp or 0) >= 100,
            },
            {
                "title": "🥈 Consistent Learner",
                "description": "Earn 500 XP to unlock the silver study badge.",
                "reward": "Silver Badge",
                "unlocked": int(total_xp or 0) >= 500,
            },
            {
                "title": "🥇 Study Master",
                "description": "Earn 1000 XP to unlock the gold study badge.",
                "reward": "Gold Badge",
                "unlocked": int(total_xp or 0) >= 1000,
            },
            {
                "title": "🏆 30-Day Streak Champion",
                "description": "Keep your study streak alive for 30 days in a row.",
                "reward": "Streak Champion",
                "unlocked": int(current_streak or 0) >= 30,
            },
        ]

    def _get_xp_badge_label(self, total_xp):
        """Return the current earned XP badge label."""
        if int(total_xp or 0) >= 1000:
            return "Gold Badge"
        if int(total_xp or 0) >= 500:
            return "Silver Badge"
        if int(total_xp or 0) >= 100:
            return "Bronze Badge"
        return None

    def _ensure_gamification_profile(self):
        """Create the single persisted profile row if it does not exist yet."""
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, total_xp, coins, level, current_level_xp, current_level_target
                FROM gamification_profiles
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO gamification_profiles(total_xp, coins, level, current_level_xp, current_level_target, updated_at)
                    VALUES(0, 0, 1, 0, 100, CURRENT_TIMESTAMP)
                    """
                )
                conn.commit()
                cursor.execute(
                    """
                    SELECT id, total_xp, coins, level, current_level_xp, current_level_target
                    FROM gamification_profiles
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
                row = cursor.fetchone()
            return row
        except sqlite3.Error:
            return None
        finally:
            conn.close()

    def _store_gamification_profile(self, total_xp, coins, level=None, current_level_xp=None):
        """Update the single-profile SQLite row with the current XP, coins, and level state."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute("SELECT id FROM gamification_profiles LIMIT 1")
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    """
                    INSERT INTO gamification_profiles(total_xp, coins, level, current_level_xp, current_level_target, updated_at)
                    VALUES(?, ?, ?, ?, 100, CURRENT_TIMESTAMP)
                    """,
                    (int(total_xp), int(coins), int(level or 1), int(current_level_xp or 0)),
                )
            else:
                level = level if level is not None else self._compute_level(total_xp)[0]
                current_level_xp = current_level_xp if current_level_xp is not None else self._compute_level(total_xp)[1]
                cursor.execute(
                    """
                    UPDATE gamification_profiles
                    SET total_xp=?, coins=?, level=?, current_level_xp=?, current_level_target=100, updated_at=CURRENT_TIMESTAMP
                    WHERE id=?
                    """,
                    (int(total_xp), int(coins), int(level), int(current_level_xp), row[0]),
                )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def _award_gamification_event(self, event_type, source_type=None, source_id=None, duration_minutes=0):
        """Award XP and coins for a specific event only once per unique source."""
        reward_map = {
            "task_completed": (10, 10),
            "study_session": (max(0, int(duration_minutes or 0) // 60) * 20, max(0, int(duration_minutes or 0) // 60) * 20),
            "daily_login": (5, 5),
        }
        xp_awarded, coins_awarded = reward_map.get(event_type, (0, 0))
        if xp_awarded <= 0 and coins_awarded <= 0:
            return False

        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, total_xp, coins, level, current_level_xp, current_level_target
                FROM gamification_profiles
                ORDER BY id DESC
                LIMIT 1
                """
            )
            profile_row = cursor.fetchone()
            if profile_row is None:
                cursor.execute(
                    """
                    INSERT INTO gamification_profiles(total_xp, coins, level, current_level_xp, current_level_target, updated_at)
                    VALUES(0, 0, 1, 0, 100, CURRENT_TIMESTAMP)
                    """
                )
                conn.commit()
                cursor.execute(
                    """
                    SELECT id, total_xp, coins, level, current_level_xp, current_level_target
                    FROM gamification_profiles
                    ORDER BY id DESC
                    LIMIT 1
                    """
                )
                profile_row = cursor.fetchone()

            cursor.execute(
                """
                SELECT id
                FROM gamification_events
                WHERE event_type=?
                  AND COALESCE(source_type, '')=?
                  AND COALESCE(source_id, -1)=?
                  AND date(event_date) = date('now')
                """,
                (event_type, source_type or "", int(source_id or -1)),
            )
            if cursor.fetchone():
                return False

            cursor.execute(
                """
                INSERT INTO gamification_events(event_type, xp_awarded, coins_awarded, source_type, source_id, event_date, created_at)
                VALUES(?, ?, ?, ?, ?, date('now'), CURRENT_TIMESTAMP)
                """,
                (event_type, xp_awarded, coins_awarded, source_type, source_id),
            )

            total_xp = int(profile_row[1] or 0) + xp_awarded
            coins = int(profile_row[2] or 0) + coins_awarded
            level, current_level_xp = self._compute_level(total_xp)
            cursor.execute(
                """
                UPDATE gamification_profiles
                SET total_xp=?, coins=?, level=?, current_level_xp=?, current_level_target=100, updated_at=CURRENT_TIMESTAMP
                WHERE id=?
                """,
                (int(total_xp), int(coins), int(level), int(current_level_xp), int(profile_row[0])),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def _award_daily_login_xp(self, user_id):
        """Reward the daily login once per calendar day."""
        today = date.today().isoformat()
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id
                FROM gamification_events
                WHERE event_type='daily_login'
                  AND source_type='user'
                  AND source_id=?
                  AND event_date=?
                """,
                (int(user_id), today),
            )
            if cursor.fetchone():
                return False
            updated = self._award_gamification_event("daily_login", source_type="user", source_id=int(user_id), duration_minutes=0)
            if updated:
                cursor.execute(
                    """
                    UPDATE users
                    SET last_login=?
                    WHERE id=?
                    """,
                    (today, int(user_id)),
                )
                conn.commit()
            return updated
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_gamification_state(self):
        """Return the persisted gamification state for the current profile."""
        profile = self._ensure_gamification_profile()
        if profile is None:
            return {
                "total_xp": 0,
                "coins": 0,
                "level": 1,
                "current_level_xp": 0,
                "current_level_target": 100,
                "unlocked_achievements": 0,
                "badges": [],
                "badge_label": None,
            }

        total_xp = int(profile[1] or 0)
        coins = int(profile[2] or 0)
        level = int(profile[3] or 1)
        current_level_xp = int(profile[4] or 0)
        current_level_target = int(profile[5] or 100)
        current_streak = self.get_current_study_streak()
        badges = self._compute_badges(total_xp, current_streak)
        return {
            "total_xp": total_xp,
            "coins": coins,
            "level": level,
            "current_level_xp": current_level_xp,
            "current_level_target": current_level_target,
            "unlocked_achievements": 0,
            "badges": badges,
            "badge_label": self._get_xp_badge_label(total_xp),
        }

    def add_study_session(self, subject, duration, study_date):
        """Add a new study session and refresh the persisted streak summary."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO study_sessions(subject, duration, study_date)
                VALUES(?, ?, ?)
                """,
                (subject, duration, study_date),
            )
            conn.commit()
            refreshed = self.refresh_study_streak_summary()
            self._award_gamification_event("study_session", source_type="study_session", source_id=cursor.lastrowid, duration_minutes=int(duration or 0))
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_all_study_sessions(self):
        """Get all study sessions ordered by study date."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM study_sessions
                ORDER BY study_date DESC
                """
            )
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def get_recent_study_sessions(self, limit=5):
        """Get a limited set of recent study sessions."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM study_sessions
                ORDER BY study_date DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def get_study_sessions_by_subject(self, subject):
        """Get study sessions for a specific subject."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM study_sessions
            WHERE subject=?
            ORDER BY study_date DESC
            """,
            (subject,),
        )
        sessions = cursor.fetchall()
        conn.close()
        return sessions

    def get_study_sessions_by_date(self, study_date):
        """Get study sessions for a specific date."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM study_sessions
            WHERE study_date=?
            ORDER BY id DESC
            """,
            (study_date,),
        )
        sessions = cursor.fetchall()
        conn.close()
        return sessions

    def get_total_study_minutes(self):
        """Return the total study minutes."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT COALESCE(SUM(duration), 0)
            FROM study_sessions
            """
        )
        total = cursor.fetchone()[0]
        conn.close()
        return total

    def get_total_study_hours(self):
        """Return total study hours."""
        total_minutes = self.get_total_study_minutes()
        return round(total_minutes / 60, 2)

    def _compute_daily_active_days(self):
        """Return the set of unique study dates where the user studied at least 30 minutes."""
        conn = self.connect()
        if conn is None:
            return {}
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT study_date, COALESCE(SUM(duration), 0) AS total_minutes
                FROM study_sessions
                GROUP BY study_date
                ORDER BY study_date ASC
                """
            )
            active_days = {}
            for study_date, total_minutes in cursor.fetchall():
                if not study_date:
                    continue
                try:
                    parsed_date = date.fromisoformat(str(study_date))
                except ValueError:
                    try:
                        parsed_date = date.fromisoformat(str(study_date).split(" ")[0])
                    except ValueError:
                        continue
                if int(total_minutes or 0) >= 30:
                    active_days[parsed_date] = int(total_minutes or 0)
            return active_days
        except sqlite3.Error:
            return {}
        finally:
            conn.close()

    def _compute_streak_summary(self):
        """Compute current and longest active study streaks using the 30-minute threshold."""
        active_days = self._compute_daily_active_days()
        if not active_days:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_active_date": None,
            }

        sorted_active_dates = sorted(active_days)
        today = date.today()
        current_streak = 0
        cursor_date = today
        while cursor_date in active_days:
            current_streak += 1
            cursor_date = cursor_date - timedelta(days=1)

        longest_streak = 0
        run_length = 0
        previous_date = None
        for active_date in sorted_active_dates:
            if previous_date is None:
                run_length = 1
            elif active_date - previous_date == timedelta(days=1):
                run_length += 1
            else:
                longest_streak = max(longest_streak, run_length)
                run_length = 1
            previous_date = active_date
        longest_streak = max(longest_streak, run_length)

        return {
            "current_streak": current_streak,
            "longest_streak": longest_streak,
            "last_active_date": sorted_active_dates[-1].isoformat(),
        }

    def _store_streak_summary(self, summary):
        """Persist the computed study streak summary inside SQLite."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                "SELECT id FROM study_streaks LIMIT 1"
            )
            row = cursor.fetchone()
            if row:
                cursor.execute(
                    """
                    UPDATE study_streaks
                    SET current_streak = ?, longest_streak = ?, last_active_date = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (
                        int(summary.get("current_streak", 0)),
                        int(summary.get("longest_streak", 0)),
                        summary.get("last_active_date"),
                        row[0],
                    ),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO study_streaks(current_streak, longest_streak, last_active_date, updated_at)
                    VALUES(?, ?, ?, CURRENT_TIMESTAMP)
                    """,
                    (
                        int(summary.get("current_streak", 0)),
                        int(summary.get("longest_streak", 0)),
                        summary.get("last_active_date"),
                    ),
                )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def refresh_study_streak_summary(self):
        """Calculate and persist the current study streak summary."""
        summary = self._compute_streak_summary()
        self._store_streak_summary(summary)
        return summary

    def get_study_streak_summary(self):
        """Return the persisted study streak summary, refreshing it from live sessions when needed."""
        conn = self.connect()
        if conn is None:
            return {
                "current_streak": 0,
                "longest_streak": 0,
                "last_active_date": None,
            }
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT current_streak, longest_streak, last_active_date
                FROM study_streaks
                ORDER BY id DESC
                LIMIT 1
                """
            )
            row = cursor.fetchone()
            conn.close()
        except sqlite3.Error:
            conn.close()
            row = None

        if row is None:
            summary = self.refresh_study_streak_summary()
        else:
            summary = {
                "current_streak": int(row[0] or 0),
                "longest_streak": int(row[1] or 0),
                "last_active_date": row[2],
            }
            live_summary = self._compute_streak_summary()
            if live_summary["longest_streak"] > summary["longest_streak"] or live_summary["current_streak"] != summary["current_streak"]:
                summary = live_summary
                self._store_streak_summary(summary)
        return summary

    def get_study_streak_calendar(self, year=None, month=None):
        """Return a month calendar payload with active study days, plus the persisted streak totals."""
        today = date.today()
        if year is None:
            year = today.year
        if month is None:
            month = today.month

        year = int(year)
        month = int(month)
        first_day = date(year, month, 1)
        if month == 12:
            next_month_date = date(year + 1, 1, 1)
        else:
            next_month_date = date(year, month + 1, 1)

        conn = self.connect()
        if conn is None:
            return {
                "year": year,
                "month": month,
                "active_days": [],
                "current_streak": 0,
                "longest_streak": 0,
                "days_in_month": calendar.monthrange(year, month)[1],
                "first_weekday": calendar.monthrange(year, month)[0],
            }

        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT study_date, COALESCE(SUM(duration), 0) AS total_minutes
                FROM study_sessions
                WHERE study_date >= ? AND study_date < ?
                GROUP BY study_date
                """,
                (first_day.isoformat(), next_month_date.isoformat()),
            )
            active_days = []
            for study_date, total_minutes in cursor.fetchall():
                if not study_date:
                    continue
                try:
                    parsed_date = date.fromisoformat(str(study_date))
                except ValueError:
                    try:
                        parsed_date = date.fromisoformat(str(study_date).split(" ")[0])
                    except ValueError:
                        continue
                if int(total_minutes or 0) >= 30:
                    active_days.append(parsed_date.day)
        except sqlite3.Error:
            active_days = []
        finally:
            conn.close()

        summary = self.get_study_streak_summary()
        return {
            "year": year,
            "month": month,
            "active_days": sorted(set(active_days)),
            "current_streak": int(summary.get("current_streak", 0) or 0),
            "longest_streak": int(summary.get("longest_streak", 0) or 0),
            "days_in_month": calendar.monthrange(year, month)[1],
            "first_weekday": calendar.monthrange(year, month)[0],
        }

    def get_current_study_streak(self):
        """Calculate current consecutive-day study streak ending today."""
        return self.get_study_streak_summary().get("current_streak", 0)

    def get_longest_study_streak(self):
        """Return the longest consecutive study streak recorded for the active-day rule."""
        return self.get_study_streak_summary().get("longest_streak", 0)

    def get_study_hours_by_subject(self):
        """Return study hours aggregated by subject."""
        conn = self.connect()
        if conn is None:
            return {}
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT subject, SUM(duration)
            FROM study_sessions
            GROUP BY subject
            """
        )
        rows = cursor.fetchall()
        conn.close()
        study_hours = {}
        for subject_name, minutes in rows:
            study_hours[subject_name] = round(minutes / 60, 2)
        return study_hours

    def delete_study_session(self, session_id):
        """Delete a study session."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM study_sessions
                WHERE id=?
                """,
                (session_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def add_note(self, subject, note, created_date):
        """Add a study note."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO notes(subject, note, created_date)
                VALUES(?, ?, ?)
                """,
                (subject, note, created_date),
            )
            conn.commit()
            return True
        except sqlite3.Error as error:
            print("Error adding note:", error)
            return False
        finally:
            conn.close()

    def get_all_notes(self):
        """Get all notes."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM notes
            ORDER BY created_date DESC
            """
        )
        notes = cursor.fetchall()
        conn.close()
        return notes

    def get_notes_by_subject(self, subject):
        """Get notes for a specific subject."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM notes
            WHERE subject=?
            ORDER BY created_date DESC
            """,
            (subject,),
        )
        notes = cursor.fetchall()
        conn.close()
        return notes

    def update_note(self, note_id, subject, note, created_date):
        """Update a study note."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE notes
                SET subject=?, note=?, created_date=?
                WHERE id=?
                """,
                (subject, note, created_date, note_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def delete_note(self, note_id):
        """Delete a study note."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                DELETE FROM notes
                WHERE id=?
                """,
                (note_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    # --------------------------------------------------
    # Pomodoro session helpers
    # --------------------------------------------------
    def add_pomodoro_session(self, session_type, duration_minutes, session_date):
        """Record a pomodoro session (focus/short_break/long_break/custom)."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO pomodoro_sessions(session_type, duration, session_date)
                VALUES(?, ?, ?)
                """,
                (session_type, int(duration_minutes), session_date),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_recent_pomodoro_sessions(self, limit=20):
        """Return recent pomodoro sessions (most recent first)."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT id, session_type, duration, session_date, created_at
                FROM pomodoro_sessions
                ORDER BY session_date DESC, id DESC
                LIMIT ?
                """,
                (limit,),
            )
            rows = cursor.fetchall()
            return rows
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def get_pomodoro_count_for_date(self, date_str, session_type="focus"):
        """Return number of pomodoro focus sessions for a given date (YYYY-MM-DD)."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pomodoro_sessions
                WHERE session_date = ? AND session_type = ?
                """,
                (date_str, session_type),
            )
            count = cursor.fetchone()[0]
            return int(count or 0)
        except sqlite3.Error:
            return 0
        finally:
            conn.close()

    def get_pomodoro_count_between_dates(self, start_date, end_date, session_type="focus"):
        """Return count of pomodoro focus sessions between two dates inclusive."""
        conn = self.connect()
        if conn is None:
            return 0
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT COUNT(*)
                FROM pomodoro_sessions
                WHERE session_date >= ? AND session_date <= ? AND session_type = ?
                """,
                (start_date, end_date, session_type),
            )
            count = cursor.fetchone()[0]
            return int(count or 0)
        except sqlite3.Error:
            return 0
        finally:
            conn.close()

    def add_achievement(self, title, description, unlocked=0):
        """Add an achievement."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO achievements(title, description, unlocked)
                VALUES(?, ?, ?)
                """,
                (title, description, unlocked),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_all_achievements(self):
        """Get all achievements."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM achievements
            ORDER BY id
            """
        )
        achievements = cursor.fetchall()
        conn.close()
        return achievements

    def unlock_achievement(self, achievement_id):
        """Unlock an achievement."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE achievements
                SET unlocked=1
                WHERE id=?
                """,
                (achievement_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def add_goal(self, goal_type, target_minutes, current_minutes=0, period_start=None, period_end=None, completed=0):
        """Create a daily or weekly study goal record."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO goals(goal_type, target_minutes, current_minutes, period_start, period_end, completed)
                VALUES(?, ?, ?, ?, ?, ?)
                """,
                (goal_type, target_minutes, current_minutes, period_start, period_end, completed),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_goals(self, goal_type=None):
        """Return persisted goals; optionally filter by goal type."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            if goal_type:
                cursor.execute(
                    """
                    SELECT *
                    FROM goals
                    WHERE goal_type=?
                    ORDER BY created_at DESC
                    """,
                    (goal_type,),
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM goals
                    ORDER BY created_at DESC
                    """
                )
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def update_goal_progress(self, goal_id, current_minutes, completed=0):
        """Update a goal's current progress and completion state."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE goals
                SET current_minutes=?, completed=?
                WHERE id=?
                """,
                (current_minutes, completed, goal_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def update_goal_target(self, goal_id, target_minutes):
        """Update a goal's target minutes without resetting progress."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE goals
                SET target_minutes=?
                WHERE id=?
                """,
                (target_minutes, goal_id),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def add_notification(self, title, message, is_read=0):
        """Persist a local notification record for the dashboard/notifications area."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO notifications(title, message, is_read)
                VALUES(?, ?, ?)
                """,
                (title, message, is_read),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_notifications(self, unread_only=False):
        """Return notifications; optionally return only unread items."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            if unread_only:
                cursor.execute(
                    """
                    SELECT *
                    FROM notifications
                    WHERE is_read=0
                    ORDER BY created_at DESC
                    """
                )
            else:
                cursor.execute(
                    """
                    SELECT *
                    FROM notifications
                    ORDER BY created_at DESC
                    """
                )
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def mark_notification_read(self, notification_id):
        """Mark a notification as read."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                UPDATE notifications
                SET is_read=1
                WHERE id=?
                """,
                (notification_id,),
            )
            conn.commit()
            return cursor.rowcount > 0
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def add_ai_history(self, query_text, response_text):
        """Persist AI interaction history for the local user session."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                INSERT INTO ai_history(query_text, response_text)
                VALUES(?, ?)
                """,
                (query_text, response_text),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_ai_history(self, limit=10):
        """Return the latest AI history rows."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        try:
            cursor.execute(
                """
                SELECT *
                FROM ai_history
                ORDER BY created_at DESC
                LIMIT ?
                """,
                (limit,),
            )
            return cursor.fetchall()
        except sqlite3.Error:
            return []
        finally:
            conn.close()

    def clear_ai_history(self):
        """Remove all persisted AI assistant chat history."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM ai_history")
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_settings(self):
        """Get the most recent settings row."""
        conn = self.connect()
        if conn is None:
            return None
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT *
            FROM settings
            ORDER BY id DESC
            LIMIT 1
            """
        )
        settings = cursor.fetchone()
        conn.close()
        return settings

    def save_settings(self, theme, notification, pomodoro_time, settings_json=None):
        """Save the app settings while preserving older columns and adding payload support."""
        conn = self.connect()
        if conn is None:
            return False
        cursor = conn.cursor()
        try:
            cursor.execute("DELETE FROM settings")
            cursor.execute(
                """
                INSERT INTO settings(theme, notification, pomodoro_time, settings_json)
                VALUES(?, ?, ?, ?)
                """,
                (theme, notification, pomodoro_time, settings_json),
            )
            conn.commit()
            return True
        except sqlite3.Error:
            return False
        finally:
            conn.close()

    def get_daily_study_statistics(self):
        """Return daily study statistics."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT study_date, SUM(duration)
            FROM study_sessions
            GROUP BY study_date
            ORDER BY study_date
            """
        )
        statistics = cursor.fetchall()
        conn.close()
        return statistics

    def get_subject_statistics(self):
        """Return subject study statistics."""
        conn = self.connect()
        if conn is None:
            return []
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT subject, SUM(duration)
            FROM study_sessions
            GROUP BY subject
            ORDER BY SUM(duration) DESC
            """
        )
        statistics = cursor.fetchall()
        conn.close()
        return statistics

    def get_study_dates(self):
        """Return the distinct study dates."""
        conn = self.connect()
        if conn is None:
            return set()
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT DISTINCT study_date
            FROM study_sessions
            """
        )
        rows = cursor.fetchall()
        conn.close()
        study_dates = set()
        for row in rows:
            study_dates.add(row[0])
        return study_dates

    def get_dashboard_statistics(self):
        """Return dashboard statistics."""
        task_statistics = self.get_task_statistics()
        study_hours = self.get_total_study_hours()
        total_subjects = self.total_subjects()
        statistics = {
            "total_tasks": task_statistics["total"],
            "completed_tasks": task_statistics["completed"],
            "pending_tasks": task_statistics["pending"],
            "completion_rate": task_statistics["completion_rate"],
            "study_hours": study_hours,
            "subjects": total_subjects,
        }
        return statistics
