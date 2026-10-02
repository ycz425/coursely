import os
from datetime import date, datetime, timedelta, timezone

from app.models import Course, GradedGroup, GradedItem

_UID_DOMAIN = "couresly"


def _escape_text(text: str) -> str:
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\n", "\\n")
    )


def _fold_line(line: str) -> str:
    """Folds a line to <=75 octets per RFC 5545, continuation lines prefixed with a space."""
    encoded = line.encode("utf-8")
    if len(encoded) <= 75:
        return line

    chunks = []
    start = 0
    limit = 75
    while start < len(encoded):
        chunks.append(encoded[start:start + limit].decode("utf-8", errors="ignore"))
        start += limit
        limit = 74  # continuation lines lose a byte to the leading space
    return "\r\n ".join(chunks)


def _item_label(group: GradedGroup, item: GradedItem) -> str:
    return group.name if len(group.items) == 1 else f"{group.name} {item.number}"


def _item_description(course: Course, group: GradedGroup, item: GradedItem) -> str:
    pct = item.weight * group.total_weight * 100
    lines = [f"{pct:.1f}% of final grade"]
    if item.description:
        lines.append(item.description)
    if group.important_notes:
        lines.append(f"{group.name} notes: " + "; ".join(group.important_notes))
    if item.important_notes:
        lines.append("Notes: " + "; ".join(item.important_notes))
    return "\n".join(lines)


def _event(course: Course, group: GradedGroup, item: GradedItem, dtstamp: str) -> str:
    try:
        start = date.fromisoformat(item.due_date)
    except ValueError:
        return ""

    end = start + timedelta(days=1)
    uid = f"{course.code}-{group.item_type}-{item.number}@{_UID_DOMAIN}"
    summary = f"{course.code}: {_item_label(group, item)}"
    description = _item_description(course, group, item)

    lines = [
        "BEGIN:VEVENT",
        f"UID:{uid}",
        f"DTSTAMP:{dtstamp}",
        f"DTSTART;VALUE=DATE:{start.strftime('%Y%m%d')}",
        f"DTEND;VALUE=DATE:{end.strftime('%Y%m%d')}",
        f"SUMMARY:{_escape_text(summary)}",
        f"DESCRIPTION:{_escape_text(description)}",
        f"CATEGORIES:{group.item_type.upper()}",
        "END:VEVENT",
    ]
    return "\r\n".join(_fold_line(line) for line in lines)


def course_to_ics(course: Course) -> str:
    """Renders one course's graded items as a standalone .ics calendar."""
    return to_ics([course])


def to_ics(courses: list[Course]) -> str:
    """Renders all courses' graded items as one combined .ics calendar."""
    dtstamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    events = [
        _event(course, group, item, dtstamp)
        for course in courses
        for group in course.groups
        for item in group.items
    ]
    events = [event for event in events if event]

    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//couresly//syllabus-calendar//EN",
        "CALSCALE:GREGORIAN",
        *events,
        "END:VCALENDAR",
    ]
    return "\r\n".join(lines) + "\r\n"


def write_ics(courses: list[Course], out_dir: str) -> None:
    """Writes one .ics file per course plus a combined 'All Courses.ics', into out_dir."""
    os.makedirs(out_dir, exist_ok=True)
    for course in courses:
        with open(os.path.join(out_dir, f"{course.code}.ics"), "w", newline="") as f:
            f.write(course_to_ics(course))
    with open(os.path.join(out_dir, "All Courses.ics"), "w", newline="") as f:
        f.write(to_ics(courses))
