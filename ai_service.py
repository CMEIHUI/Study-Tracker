"""Dedicated AI service layer for study analytics and report generation."""

try:
    from .ai_analysis import (
        analyze_study_data,
        build_ai_analysis_text,
        build_ai_report_text,
    )
    from .utils import run_in_background
except ImportError:  # Allow direct execution from the workspace root.
    from ai_analysis import (
        analyze_study_data,
        build_ai_analysis_text,
        build_ai_report_text,
    )
    from utils import run_in_background


def analyze_study_performance(tasks, sessions, reference_date=None):
    """Create structured study analytics from real task and session records."""
    return analyze_study_data(tasks, sessions, reference_date=reference_date)


def generate_study_recommendations(tasks, sessions, reference_date=None):
    """Return a human-readable AI analysis block based on structured metrics."""
    analysis = analyze_study_performance(tasks, sessions, reference_date=reference_date)
    return build_ai_analysis_text(analysis)


def generate_weekly_report(tasks, sessions, start_date=None, end_date=None):
    """Generate a professional weekly report from structured study data."""
    analysis = analyze_study_performance(tasks, sessions, reference_date=end_date)
    return build_ai_report_text(analysis, period="Weekly", start_date=start_date, end_date=end_date)


def generate_monthly_report(tasks, sessions, start_date=None, end_date=None):
    """Generate a professional monthly report from structured study data."""
    analysis = analyze_study_performance(tasks, sessions, reference_date=end_date)
    return build_ai_report_text(analysis, period="Monthly", start_date=start_date, end_date=end_date)


def analyze_study_performance_in_background(
    widget,
    tasks,
    sessions,
    callback=None,
    error_callback=None,
    reference_date=None,
):
    """Run study analysis in a background thread and deliver the result to the UI thread."""
    return run_in_background(
        widget,
        lambda: analyze_study_performance(tasks, sessions, reference_date=reference_date),
        callback=callback,
        error_callback=error_callback,
    )


def generate_study_recommendations_in_background(
    widget,
    tasks,
    sessions,
    callback=None,
    error_callback=None,
    reference_date=None,
):
    """Run recommendation generation in a background thread and deliver the result to the UI thread."""
    return run_in_background(
        widget,
        lambda: generate_study_recommendations(tasks, sessions, reference_date=reference_date),
        callback=callback,
        error_callback=error_callback,
    )
