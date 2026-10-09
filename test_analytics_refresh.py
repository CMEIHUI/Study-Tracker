from analytics import build_analytics_cache_signature, should_refresh_analytics


def test_build_analytics_cache_signature_distinguishes_changed_data():
    tasks_a = [(1, "Math", "Task A", "", "High", "2026-01-01", "Pending")]
    sessions_a = [(1, "Math", 30, "2026-01-01")]
    subject_stats_a = [("Math", 1800)]
    study_dates_a = ["2026-01-01"]

    tasks_b = [(1, "Math", "Task A", "", "High", "2026-01-01", "Completed")]
    sessions_b = [(1, "Math", 45, "2026-01-01")]
    subject_stats_b = [("Math", 2700)]
    study_dates_b = ["2026-01-02"]

    signature_a = build_analytics_cache_signature(tasks_a, sessions_a, subject_stats_a, study_dates_a)
    signature_b = build_analytics_cache_signature(tasks_b, sessions_b, subject_stats_b, study_dates_b)

    assert signature_a != signature_b


def test_should_refresh_analytics_skips_identical_payloads():
    assert should_refresh_analytics(force=False, previous_signature="same", current_signature="same") is False
    assert should_refresh_analytics(force=True, previous_signature="same", current_signature="same") is True
    assert should_refresh_analytics(force=False, previous_signature=None, current_signature="same") is True
