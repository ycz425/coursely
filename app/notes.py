import os

from app.models import Course, GradedGroup


def _item_label(group: GradedGroup, item) -> str:
    return group.name if len(group.items) == 1 else f"{group.name} {item.number}"


def _course_todos(course: Course) -> list[tuple[str, str, float]]:
    """Returns (due_date, label, pct_of_grade) tuples for a course, sorted by due date."""
    todos = [
        (item.due_date, _item_label(group, item), item.weight * group.total_weight * 100)
        for group in course.groups
        for item in group.items
    ]
    return sorted(todos, key=lambda t: t[0])


def course_to_note(course: Course) -> str:
    """Renders one course's graded items as a paste-ready markdown checklist."""
    lines = [f"## {course.code} — {course.name}", ""]
    for due_date, label, pct in _course_todos(course):
        pct_str = f"{pct:.0f}%" if pct == round(pct) else f"{pct:.1f}%"
        lines.append(f"- [ ] {label} — {due_date} ({pct_str})")
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
