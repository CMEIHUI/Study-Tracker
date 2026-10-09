from datetime import datetime

from ai_analysis import analyze_study_data, build_ai_analysis_text, build_ai_report_text


def test_analyze_study_data_uses_real_metrics_and_builds_sections():
    tasks = [
        (1, "Math", "Finish algebra review", "High", "2026-07-20", "Completed"),
        (2, "Science", "Read chapter 3", "Medium", "2026-07-21", "Pending"),
        (3, "History", "Outline essay", "Low", "2026-07-15", "Pending"),
    ]
    sessions = [
        (1, "Math", 45, "2026-07-20"),
        (2, "Math", 30, "2026-07-19"),
        (3, "Science", 20, "2026-07-19"),
        (4, "Science", 15, "2026-07-18"),
    ]

    analysis = analyze_study_data(
        tasks,
        sessions,
        reference_date=datetime(2026, 7, 20).date(),
    )

    assert analysis["metrics"]["total_study_minutes"] == 110
    assert analysis["metrics"]["daily_study_minutes"] == 45
    assert analysis["metrics"]["weekly_study_minutes"] == 110
    assert analysis["metrics"]["monthly_study_minutes"] == 110
    assert analysis["metrics"]["completed_tasks"] == 1
    assert analysis["metrics"]["pending_tasks"] == 2
    assert analysis["metrics"]["overdue_tasks"] == 1
    assert analysis["metrics"]["completion_rate"] == 33.33333333333333
    assert analysis["metrics"]["study_streak"] == 3
    assert analysis["metrics"]["most_studied_subject"] == "Math"
    assert analysis["metrics"]["least_studied_subject"] == "Science"
    assert isinstance(analysis["metrics"].get("productivity_score"), int)
    assert analysis["metrics"].get("weak_subjects") == ["History"]
    assert analysis["metrics"].get("primary_weak_subject") == "History"

    text = build_ai_analysis_text(analysis)
    assert "Study Performance Summary" in text
    assert "Strengths" in text
    assert "Areas for Improvement" in text
    assert "Personalized Recommendations" in text
    assert "Task Completion Suggestions" in text
    assert "Time Management Suggestions" in text

    report_text = build_ai_report_text(
        analysis,
        period="Weekly",
        start_date=datetime(2026, 7, 13).date(),
        end_date=datetime(2026, 7, 20).date(),
    )
    assert "Study Performance Summary" in report_text
    assert "Total Study Time" in report_text
    assert "Task Analysis" in report_text
    assert "Subject Performance Analysis" in report_text
    assert "Study Habit Analysis" in report_text
    assert "Strengths" in report_text
    assert "Weaknesses" in report_text
    assert "Personalized Recommendations" in report_text
    assert "Suggested Improvements for the Next Study Period" in report_text
