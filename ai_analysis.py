from collections import Counter
from datetime import date, datetime, timedelta


def _parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(str(value), fmt).date()
        except ValueError:
            continue
    return None


def _normalize_status(value):
    return str(value or "").strip().lower()


def _extract_task_fields(task):
    if not task:
        return None, ""
    if len(task) >= 7:
        return task[5], task[6]
    if len(task) >= 6:
        return task[4], task[5]
    if len(task) >= 5:
        return task[4], ""
    return None, ""


def analyze_study_data(tasks, sessions, reference_date=None):
    """Build AI-ready study metrics from real task and session records."""
    if reference_date is None:
        reference_date = datetime.now().date()

    total_study_minutes = 0
    daily_study_minutes = 0
    weekly_study_minutes = 0
    monthly_study_minutes = 0
    current_month = reference_date.strftime("%Y-%m")

    subject_minutes = Counter()
    study_dates = []
    known_subjects = set()

    for session in sessions or []:
        if not session or len(session) <= 2:
            continue
        try:
            duration = int(session[2])
        except (TypeError, ValueError):
            continue
        total_study_minutes += duration
        subject_name = str(session[1] or "Unassigned")
        subject_minutes[subject_name] += duration
        if subject_name:
            known_subjects.add(subject_name)
        session_date = _parse_date(session[3]) if len(session) > 3 else None
        if session_date is None:
            continue
        study_dates.append(session_date)
        if session_date == reference_date:
            daily_study_minutes += duration
        if reference_date - timedelta(days=6) <= session_date <= reference_date:
            weekly_study_minutes += duration
        if session_date.strftime("%Y-%m") == current_month:
            monthly_study_minutes += duration

    total_tasks = len(tasks or [])
    completed_tasks = 0
    pending_tasks = 0
    overdue_tasks = 0
    task_completion_rate = 0.0

    for task in tasks or []:
        if not task:
            continue
        deadline, status_value = _extract_task_fields(task)
        status = _normalize_status(status_value)
        subject_name = str(task[1] or "Unassigned").strip() if len(task) > 1 else "Unassigned"
        if subject_name:
            known_subjects.add(subject_name)
        if status == "completed" or status == "complete":
            completed_tasks += 1
        else:
            pending_tasks += 1

        deadline_date = _parse_date(deadline)
        if deadline_date is not None and deadline_date < reference_date and status not in {"completed", "complete"}:
            overdue_tasks += 1

    if total_tasks > 0:
        task_completion_rate = (completed_tasks / total_tasks) * 100

    study_dates = sorted(set(study_dates))
    streak = 0
    current_day = reference_date
    while current_day in study_dates:
        streak += 1
        current_day -= timedelta(days=1)

    # Build subject performance data.
    subject_performance = []
    for subject_name, minutes in sorted(subject_minutes.items(), key=lambda item: item[1], reverse=True):
        subject_performance.append(
            {
                "subject": subject_name,
                "study_minutes": int(minutes),
            }
        )

    most_studied_subject = None
    least_studied_subject = None
    if subject_performance:
        most_studied_subject = subject_performance[0]["subject"]
        least_studied_subject = subject_performance[-1]["subject"]

    strong_subjects = [item["subject"] for item in subject_performance[:2]]

    metrics = {
        "total_study_minutes": int(total_study_minutes),
        "daily_study_minutes": int(daily_study_minutes),
        "weekly_study_minutes": int(weekly_study_minutes),
        "monthly_study_minutes": int(monthly_study_minutes),
        "completed_tasks": int(completed_tasks),
        "pending_tasks": int(pending_tasks),
        "overdue_tasks": int(overdue_tasks),
        "completion_rate": float(task_completion_rate),
        "study_streak": int(streak),
        "subject_performance": subject_performance,
        "most_studied_subject": most_studied_subject,
        "least_studied_subject": least_studied_subject,
        "strong_subjects": strong_subjects,
        "primary_weak_subject": None,
        "weak_subjects": [],
        "reference_date": reference_date,
        "total_tasks": int(total_tasks),
    }

    productivity_score = _calculate_productivity_score(metrics)
    metrics["productivity_score"] = productivity_score

    weak_subjects = _identify_weak_subjects(subject_minutes, total_study_minutes, known_subjects=known_subjects)
    metrics["weak_subjects"] = weak_subjects
    if weak_subjects:
        metrics["primary_weak_subject"] = weak_subjects[0]

    metrics["predicted_exam_score"] = _predict_exam_score(metrics)
    metrics["predicted_exam_outlook"] = _predict_exam_outlook(metrics)

    return {"metrics": metrics}


def _calculate_productivity_score(metrics):
    completion = metrics.get("completion_rate", 0.0) / 100.0
    streak = min(metrics.get("study_streak", 0), 7)
    weekly = metrics.get("weekly_study_minutes", 0)
    monthly = metrics.get("monthly_study_minutes", 0)
    consistency = 0.0
    if monthly > 0:
        consistency = min(weekly / float(monthly), 1.0)
    elif weekly > 0:
        consistency = 1.0

    score = completion * 60 + (streak / 7.0) * 20 + consistency * 20
    score -= min(metrics.get("overdue_tasks", 0) * 5, 20)
    return max(0, min(100, int(round(score))))


def _identify_weak_subjects(subject_minutes, total_minutes, known_subjects=None):
    if not subject_minutes and not known_subjects:
        return []

    subject_names = set(known_subjects or [])
    subject_names.update(subject_minutes.keys())
    if not subject_names:
        return []

    zero_minutes_subjects = sorted(
        [name for name in subject_names if subject_minutes.get(name, 0) <= 0],
        key=lambda name: (subject_minutes.get(name, 0), name),
    )
    if zero_minutes_subjects:
        return zero_minutes_subjects[:2]

    sorted_subjects = sorted(subject_names, key=lambda name: (subject_minutes.get(name, 0), name))
    average_minutes = (total_minutes / len(subject_names)) if total_minutes and subject_names else 0
    threshold = min(average_minutes, 60)
    weak = [name for name in sorted_subjects if subject_minutes.get(name, 0) < threshold]

    if not weak and len(sorted_subjects) > 1:
        weak = [sorted_subjects[0]]

    return weak[:2]


def _predict_exam_score(metrics):
    productivity = metrics.get("productivity_score", 0)
    completion_rate = metrics.get("completion_rate", 0.0)
    weak_subjects = metrics.get("weak_subjects", [])
    weak_penalty = min(len(weak_subjects) * 6, 18)
    base = productivity * 0.6 + completion_rate * 0.25
    score = int(max(40, min(100, round(base - weak_penalty + 5))))
    return score


def _predict_exam_outlook(metrics):
    score = metrics.get("predicted_exam_score", None)
    if score is None:
        return "Insufficient data to predict exam performance."
    if score >= 90:
        return "Excellent readiness; you are well-positioned for strong exam performance."
    if score >= 75:
        return "Good readiness; continue reinforcing weak areas and maintaining consistency."
    if score >= 60:
        return "Moderate readiness; focus on completing pending tasks and weak subjects."
    return "Low readiness; prioritize key topics and reduce overdue tasks before the exam."


def _format_duration(minutes):
    hours, remainder = divmod(int(minutes), 60)
    if hours and remainder:
        return f"{hours}h {remainder}m"
    if hours:
        return f"{hours}h"
    return f"{remainder}m"


def build_ai_analysis_text(analysis):
    metrics = analysis.get("metrics", {})
    total_study_minutes = metrics.get("total_study_minutes", 0)
    daily_study_minutes = metrics.get("daily_study_minutes", 0)
    weekly_study_minutes = metrics.get("weekly_study_minutes", 0)
    monthly_study_minutes = metrics.get("monthly_study_minutes", 0)
    completed_tasks = metrics.get("completed_tasks", 0)
    pending_tasks = metrics.get("pending_tasks", 0)
    overdue_tasks = metrics.get("overdue_tasks", 0)
    completion_rate = metrics.get("completion_rate", 0.0)
    streak = metrics.get("study_streak", 0)
    productivity_score = metrics.get("productivity_score")
    weak_subjects = metrics.get("weak_subjects", [])
    most_studied_subject = metrics.get("most_studied_subject") or "No data"
    least_studied_subject = metrics.get("least_studied_subject") or "No data"
    subject_performance = metrics.get("subject_performance", [])

    summary_lines = []
    summary_lines.append("AI Study Analysis")
    summary_lines.append("=" * 78)
    summary_lines.append("Study Performance Summary")
    summary_lines.append("-" * 78)

    if productivity_score is not None:
        summary_lines.append(
            f"Your current productivity score is {productivity_score}/100. "
            + (
                "This score reflects strong completion, steady habits, and balanced weekly study." if productivity_score >= 70
                else "A few adjustments to task planning and subject balance can raise it further."
            )
        )

    if weekly_study_minutes > 0 and daily_study_minutes > 0:
        if weekly_study_minutes >= daily_study_minutes * 5:
            summary_lines.append(
                f"Your study consistency is strong this week. You logged {weekly_study_minutes} minutes across the week, with {daily_study_minutes} minutes today."
            )
        else:
            summary_lines.append(
                f"Your study volume is steady, but your weekly focus is lighter than expected. You logged {weekly_study_minutes} minutes this week and {daily_study_minutes} minutes today."
            )
    else:
        summary_lines.append("You have not recorded enough study sessions to evaluate your recent trend yet.")

    if completion_rate >= 70:
        summary_lines.append(
            f"Your task completion rate is {completion_rate:.1f}%, which shows good follow-through on planned work."
        )
    elif completion_rate >= 40:
        summary_lines.append(
            f"Your task completion rate is {completion_rate:.1f}%, so there is room to close more outstanding work each day."
        )
    else:
        summary_lines.append(
            f"Your task completion rate is {completion_rate:.1f}%, and finishing tasks earlier would improve your momentum."
        )

    if weak_subjects:
        weak_subjects_text = ", ".join(weak_subjects)
        summary_lines.append(
            f"Your analysis identifies {weak_subjects_text} as subject(s) that would benefit from more focused review time."
        )

    predicted_score = metrics.get("predicted_exam_score")
    predicted_outlook = metrics.get("predicted_exam_outlook")
    if predicted_score is not None:
        summary_lines.append("")
        summary_lines.append("Exam Performance Prediction")
        summary_lines.append("-" * 78)
        summary_lines.append(
            f"Predicted exam readiness score: {predicted_score}/100. {predicted_outlook}"
        )

    summary_lines.append("")
    summary_lines.append("Strengths")
    summary_lines.append("-" * 78)
    strengths = []
    if streak >= 3:
        strengths.append(f"You have maintained a {streak}-day study streak, showing strong consistency.")
    if total_study_minutes >= 180:
        strengths.append("Your total study time is healthy, which suggests you are investing real effort over time.")
    if completion_rate >= 50:
        strengths.append("You are finishing a meaningful share of your planned tasks.")
    if productivity_score is not None and productivity_score >= 70:
        strengths.append("Your productivity score shows that your current balance of planning and execution is effective.")
    if most_studied_subject != "No data":
        strengths.append(f"{most_studied_subject} is your strongest subject based on recorded study time.")
    summary_lines.extend(strengths or ["You are building a solid study routine, even if the data is still emerging."])

    summary_lines.append("")
    summary_lines.append("Areas for Improvement")
    summary_lines.append("-" * 78)
    weaknesses = []
    if overdue_tasks > 0:
        weaknesses.append(f"You have {overdue_tasks} overdue task(s), which may be slowing your progress.")
    if pending_tasks > completed_tasks:
        weaknesses.append("Pending tasks still outnumber completed tasks, so prioritizing the next small win will help.")
    if completion_rate < 60:
        weaknesses.append("Your task completion rate is lower than expected, so focus on smaller daily goals.")
    if weekly_study_minutes < monthly_study_minutes and monthly_study_minutes > 0:
        weaknesses.append("Your weekly study time is lower than your monthly average, which may indicate an uneven schedule.")
    if weak_subjects:
        weaknesses.append(
            f"{weak_subjects[0]} appears to be a weaker subject area and would benefit from more intentional review."
        )
    summary_lines.extend(weaknesses or ["Your current data does not expose a major weakness yet."])

    summary_lines.append("")
    summary_lines.append("Personalized Recommendations")
    summary_lines.append("-" * 78)
    recommendations = []
    if overdue_tasks > 0:
        recommendations.append("Revisit overdue tasks first and turn them into a short list for today.")
    if completion_rate < 70:
        recommendations.append("Divide large tasks into smaller daily goals to increase completion confidence.")
    if streak < 3:
        recommendations.append("Aim for a short daily session even on busy days to rebuild momentum.")
    if weak_subjects:
        recommendations.append(
            f"Schedule a short review session for {weak_subjects[0]} to strengthen a subject that is currently underrepresented in your study plan."
        )
    elif most_studied_subject != "No data":
        recommendations.append(f"Keep your momentum in {most_studied_subject} while scheduling lighter review work for other subjects.")
    if not recommendations:
        recommendations.append("Continue your current routine and keep reviewing your weekly study patterns.")
    summary_lines.extend(recommendations)

    summary_lines.append("")
    summary_lines.append("Task Completion Suggestions")
    summary_lines.append("-" * 78)
    if pending_tasks > 0:
        summary_lines.append(
            f"You currently have {pending_tasks} pending task(s) and {completed_tasks} completed task(s). Completing one high-priority item first can improve your follow-through."
        )
    else:
        summary_lines.append("You do not have any pending tasks at the moment; keep maintaining the same pace.")

    summary_lines.append("")
    summary_lines.append("Time Management Suggestions")
    summary_lines.append("-" * 78)
    if weekly_study_minutes > 0 and daily_study_minutes > 0:
        summary_lines.append(
            "Try to keep your daily study sessions consistent so your weekly totals remain predictable."
        )
    else:
        summary_lines.append("Add a short daily study session to build reliable study habits over time.")

    if subject_performance:
        summary_lines.append("Subject performance snapshot:")
        for item in subject_performance[:3]:
            subject_name = item["subject"]
            minutes = item["study_minutes"]
            hours, remaining_minutes = divmod(minutes, 60)
            summary_lines.append(f"- {subject_name}: {hours}h {remaining_minutes}m")

    summary_lines.append("")
    summary_lines.append("Data source: real study sessions and tasks stored in your database.")
    return "\n".join(summary_lines)


def build_ai_report_text(analysis, period="Monthly", start_date=None, end_date=None):
    metrics = analysis.get("metrics", {})
    total_tasks = metrics.get("total_tasks", 0)
    completed_tasks = metrics.get("completed_tasks", 0)
    pending_tasks = metrics.get("pending_tasks", 0)
    overdue_tasks = metrics.get("overdue_tasks", 0)
    completion_rate = metrics.get("completion_rate", 0.0)
    total_study_minutes = metrics.get("total_study_minutes", 0)
    streak = metrics.get("study_streak", 0)
    most_studied_subject = metrics.get("most_studied_subject") or "No data"
    least_studied_subject = metrics.get("least_studied_subject") or "No data"
    subject_performance = metrics.get("subject_performance", [])

    period_label = str(period or "Monthly").lower()
    if start_date and end_date:
        range_label = f"from {start_date} to {end_date}"
    else:
        range_label = "for the selected period"

    total_study_hours = _format_duration(total_study_minutes)
    strengths = []
    weaknesses = []
    recommendations = []
    improvements = []

    if streak >= 3:
        strengths.append(f"You maintained a {streak}-day study streak, which indicates strong consistency.")
    if completion_rate >= 70:
        strengths.append("Your task completion rate is strong, showing good follow-through on planned work.")
    elif completion_rate >= 40:
        strengths.append("You are making steady progress, even if some planned tasks remain open.")
    if most_studied_subject != "No data":
        strengths.append(f"{most_studied_subject} emerged as your most-studied subject during this period.")

    if overdue_tasks > 0:
        weaknesses.append(f"You still have {overdue_tasks} overdue task(s), which may be limiting momentum.")
    if pending_tasks > completed_tasks:
        weaknesses.append("Pending tasks outnumber completed tasks, so your workload may benefit from tighter prioritization.")
    if completion_rate < 60:
        weaknesses.append("Your completion rate is below your ideal range, so smaller daily targets would likely help.")

    if overdue_tasks > 0:
        recommendations.append("Revisit overdue items first and convert them into a short action list for the next study block.")
    if completion_rate < 70:
        recommendations.append("Break larger tasks into smaller daily goals so completion feels more manageable.")
    if streak < 3:
        recommendations.append("Aim for a short daily session even on busy days to rebuild momentum.")
    if most_studied_subject != "No data":
        recommendations.append(f"Keep your momentum in {most_studied_subject} while giving lighter review time to other subjects.")
    if not recommendations:
        recommendations.append("Keep your current routine and review the balance between study time and completed work each week.")

    improvements.append("Schedule a brief review session at the end of each study block to close open tasks more consistently.")
    improvements.append("Prioritize one high-impact task at the start of each day to strengthen follow-through.")
    if most_studied_subject != "No data":
        improvements.append(f"Use the next period to reinforce {most_studied_subject} with a focused review plan and lighter practice in weaker subjects.")

    summary_paragraph = (
        f"During this {period_label} report period {range_label}, you completed {completed_tasks} out of {total_tasks} tasks, "
        f"achieving a completion rate of {completion_rate:.1f}%. You logged {total_study_hours} of study time and "
        f"{('showed strong consistency with a ' + str(streak) + '-day streak.') if streak >= 3 else 'maintained a steady routine.'}"
    )
    if most_studied_subject != "No data":
        summary_paragraph += f" {most_studied_subject} was the most studied subject."
    if least_studied_subject != "No data" and least_studied_subject != most_studied_subject:
        summary_paragraph += f" {least_studied_subject} received the least recorded study time."

    productivity_score = metrics.get("productivity_score")
    weak_subjects = metrics.get("weak_subjects", [])
    predicted_exam_score = metrics.get("predicted_exam_score")
    predicted_exam_outlook = metrics.get("predicted_exam_outlook", "")

    report_lines = []
    report_lines.append("AI-Powered Study Report")
    report_lines.append("=" * 78)
    report_lines.append(summary_paragraph)
    report_lines.append("")
    report_lines.append("Study Performance Summary")
    report_lines.append("-" * 78)
    report_lines.append(
        f"You recorded {total_study_hours} of study time across the selected period. "
        f"The completion rate was {completion_rate:.1f}% with {completed_tasks} completed task(s) and {pending_tasks} pending task(s)."
    )
    report_lines.append("")
    report_lines.append("Total Study Time")
    report_lines.append("-" * 78)
    report_lines.append(f"Total recorded study time: {total_study_hours}")
    report_lines.append("")
    report_lines.append("Task Analysis")
    report_lines.append("-" * 78)
    report_lines.append(f"Completed tasks: {completed_tasks}")
    report_lines.append(f"Pending tasks: {pending_tasks}")
    report_lines.append(f"Overdue tasks: {overdue_tasks}")
    report_lines.append(f"Completion rate: {completion_rate:.1f}%")
    report_lines.append("")
    report_lines.append("Subject Performance Analysis")
    report_lines.append("-" * 78)
    if subject_performance:
        for item in subject_performance[:4]:
            subject_name = item["subject"]
            minutes = item["study_minutes"]
            report_lines.append(f"- {subject_name}: {_format_duration(minutes)}")
    else:
        report_lines.append("No subject study data was recorded in the selected period.")
    report_lines.append("")
    if weak_subjects:
        report_lines.append("Weak Subject Focus")
        report_lines.append("-" * 78)
        report_lines.append(
            f"Focus on {weak_subjects[0]} as a weaker area and schedule a short, high-value review session for it next."
        )
        report_lines.append("")
    if productivity_score is not None:
        report_lines.append("Productivity Score")
        report_lines.append("-" * 78)
        report_lines.append(
            f"Your productivity score for this period is {productivity_score}/100, which measures your task completion, consistency, and study balance."
        )
        report_lines.append("")
    if predicted_exam_score is not None:
        predicted_outlook = metrics.get("predicted_exam_outlook", "")
        report_lines.append("Exam Performance Prediction")
        report_lines.append("-" * 78)
        report_lines.append(
            f"Predicted exam readiness score: {predicted_exam_score}/100. {predicted_outlook}"
        )
        report_lines.append("")
    report_lines.append("Study Habit Analysis")
    report_lines.append("-" * 78)
    report_lines.append(
        f"Your study streak is {streak} day(s), and your consistency trend suggests that daily planning has a measurable impact on follow-through."
    )
    report_lines.append("")
    report_lines.append("Strengths")
    report_lines.append("-" * 78)
    report_lines.extend(strengths or ["Your current pattern shows steady effort and a willingness to keep moving forward."])
    report_lines.append("")
    report_lines.append("Weaknesses")
    report_lines.append("-" * 78)
    report_lines.extend(weaknesses or ["No major weaknesses surfaced from the available data."])
    report_lines.append("")
    report_lines.append("Personalized Recommendations")
    report_lines.append("-" * 78)
    report_lines.extend(recommendations)
    report_lines.append("")
    report_lines.append("Suggested Improvements for the Next Study Period")
    report_lines.append("-" * 78)
    report_lines.extend(improvements)
    report_lines.append("")
    report_lines.append("Data source: real study sessions and tasks stored in your database.")
    return "\n".join(report_lines)

