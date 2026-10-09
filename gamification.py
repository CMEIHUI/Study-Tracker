"""Simple gamification helpers exposing the app's gamification features.

This module provides thin convenience wrappers around the existing
`DatabaseManager` gamification methods (XP, coins, levels, achievements).

Usage examples:
    from gamification import get_profile, progress_percentage
    print(get_profile())
    print(progress_percentage())

"""
from typing import Optional

from database import DatabaseManager


_db = DatabaseManager()


def complete_task(task_id: int) -> bool:
    """Mark a task completed and award task XP/coins.

    Returns True when the task status was updated and rewards applied.
    """
    return _db.complete_task(int(task_id))


def add_study_session(subject: str, duration_minutes: int, study_date: str) -> bool:
    """Add a study session (duration in minutes) and award study XP.

    For each full hour studied the system awards 20 XP and 20 coins.
    """
    return _db.add_study_session(subject, int(duration_minutes), study_date)


def daily_login(user_id: int) -> bool:
    """Award the daily login XP (once per calendar day) for the given user id."""
    return _db._award_daily_login_xp(int(user_id))


def get_profile() -> dict:
    """Return the persisted gamification profile state.

    Keys: total_xp, coins, level, current_level_xp, current_level_target, unlocked_achievements
    """
    return _db.get_gamification_state()


def progress_percentage() -> int:
    """Return the current level progress as an integer percentage (0-100)."""
    p = get_profile()
    target = int(p.get("current_level_target") or 0)
    current = int(p.get("current_level_xp") or 0)
    if target <= 0:
        return 0
    try:
        return int((current / target) * 100)
    except Exception:
        return 0


def badges() -> list:
    """Return the list of computed badges and their unlocked state."""
    return get_profile().get("badges", [])


def current_badge() -> Optional[str]:
    """Return the current highest earned badge label, if any."""
    return get_profile().get("badge_label")


def achievements() -> list:
    """Return the list of achievements (rows from the `achievements` table)."""
    return _db.get_all_achievements()


def unlock_achievement_by_title(title: str) -> bool:
    """Find an achievement by title and unlock it."""
    for ach in achievements():
        # achievements rows: id, title, description, unlocked
        if ach[1] == title:
            return _db.unlock_achievement(ach[0])
    return False
