from datetime import date, datetime


def _normalize_text(value):
    return str(value or "").strip().lower()


def _parse_deadline(deadline):
    if not deadline or str(deadline).strip().lower() in ("", "no deadline"):
        return None
    try:
        return datetime.strptime(str(deadline).strip(), "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.strptime(str(deadline).strip(), "%Y-%m-%d %H:%M:%S").date()
        except ValueError:
            return None


def filter_search_results(records, keyword="", entity_type="All", status_filter="All", priority_filter="All", sort_mode="Name"):
    """Filter and sort mixed records for the global search view."""
    keyword_norm = _normalize_text(keyword)
    filtered = []

    for record in records:
        if entity_type == "Subjects" and len(record) >= 2:
            subject_name = _normalize_text(record[1])
            if keyword_norm and keyword_norm not in subject_name:
                continue
            filtered.append(record)
            continue

        if entity_type == "Tasks" and len(record) >= 7:
            subject = _normalize_text(record[1])
            title = _normalize_text(record[2])
            priority = str(record[4]).strip()
            status = str(record[6]).strip()
            if status_filter != "All" and status != status_filter:
                continue
            if priority_filter != "All" and priority != priority_filter:
                continue
            if keyword_norm and keyword_norm not in title and keyword_norm not in subject:
                continue
            filtered.append(record)
            continue

        if entity_type == "Study Sessions" and len(record) >= 3:
            subject = _normalize_text(record[1])
            study_date = _normalize_text(record[3] if len(record) > 3 else record[2])
            if keyword_norm and keyword_norm not in subject and keyword_norm not in study_date:
                continue
            filtered.append(record)
            continue

        if entity_type == "All":
            # default to task-like records when row shape fits tasks
            if len(record) >= 7:
                subject = _normalize_text(record[1])
                title = _normalize_text(record[2])
                priority = str(record[4]).strip()
                status = str(record[6]).strip()
                if status_filter != "All" and status != status_filter:
                    continue
                if priority_filter != "All" and priority != priority_filter:
                    continue
                if keyword_norm and keyword_norm not in title and keyword_norm not in subject:
                    continue
                filtered.append(record)
            elif len(record) >= 2:
                subject_name = _normalize_text(record[1])
                if keyword_norm and keyword_norm not in subject_name:
                    continue
                filtered.append(record)

    if sort_mode == "Priority":
        filtered.sort(key=lambda item: (str(item[4]).strip().lower() if len(item) > 4 else "", str(item[2]).lower() if len(item) > 2 else ""))
    elif sort_mode == "Status":
        filtered.sort(key=lambda item: (str(item[6]).lower() if len(item) > 6 else "", str(item[2]).lower() if len(item) > 2 else ""))
    elif sort_mode == "Due date" and filtered and len(filtered[0]) > 5:
        filtered.sort(key=lambda item: (_parse_deadline(item[5]) is None, _parse_deadline(item[5]) or date.max, str(item[2]).lower() if len(item) > 2 else ""))
    else:
        filtered.sort(key=lambda item: (str(item[1]).lower() if len(item) > 1 else "", str(item[2]).lower() if len(item) > 2 else ""))

    return filtered
