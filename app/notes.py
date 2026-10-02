import os

from app.models import Course, GradedGroup, GradedItem


def _item_label(group: GradedGroup, item: GradedItem) -> str:
    return group.name if len(group.items) == 1 else f"{group.name} {item.number}"


def _course_items(course: Course) -> list[tuple[GradedGroup, GradedItem]]:
    """Returns (group, item) pairs for a course, sorted chronologically by due date."""
    pairs = [(group, item) for group in course.groups for item in group.items]
    return sorted(pairs, key=lambda pair: pair[1].due_date)


def _item_line(group: GradedGroup, item: GradedItem) -> str:
    pct = item.weight * group.total_weight * 100
    pct_str = f"{pct:.0f}%" if pct == round(pct) else f"{pct:.1f}%"
    lines = [f"- [ ] {_item_label(group, item)} — {item.due_date} ({pct_str})"]
    if item.description:
        lines.append(f"  - {item.description}")
    if item.important_notes:
        lines.append("  - Note: " + "; ".join(item.important_notes))
    return "\n".join(lines)


def course_to_note(course: Course) -> str:
    """Renders one course's graded items as a paste-ready markdown checklist."""
    lines = [f"## {course.code} — {course.name}"]

    if course.description:
        lines += ["", course.description]
    if course.important_notes:
        lines += ["", "**Course policies:**"]
        lines += [f"- {note}" for note in course.important_notes]

    group_notes = [
        f"- {group.name}: " + "; ".join(group.important_notes)
        for group in course.groups
        if group.important_notes
    ]
    if group_notes:
        lines += ["", "**Category notes:**", *group_notes]

    lines.append("")
    lines += [_item_line(group, item) for group, item in _course_items(course)]
    return "\n".join(lines)


def to_notes(courses: list[Course]) -> str:
    """Renders all courses as one paste-ready markdown document, grouped by course."""
    return "\n\n".join(course_to_note(course) for course in courses)


def write_notes(courses: list[Course], out_dir: str) -> None:
    """Writes one markdown file per course plus a combined 'All Courses.md', into out_dir."""
    os.makedirs(out_dir, exist_ok=True)
    for course in courses:
        with open(os.path.join(out_dir, f"{course.code}.md"), "w") as f:
            f.write(course_to_note(course))
    with open(os.path.join(out_dir, "All Courses.md"), "w") as f:
        f.write(to_notes(courses))
