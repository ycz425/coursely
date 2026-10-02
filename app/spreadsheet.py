import os
import re

from openpyxl import Workbook
from openpyxl.styles import Font
from openpyxl.worksheet.datavalidation import DataValidation
from openpyxl.worksheet.worksheet import Worksheet

from app.models import Course, GradedGroup, GradedItem

_HEADERS = ["Done", "Course", "Category", "Item", "Due Date", "% of Grade", "Description", "Notes"]

# Number format sections are positive;negative;zero;text -- TRUE stores as 1 (positive),
# FALSE as 0 (zero), so this renders booleans as checkbox glyphs instead of 1/0.
_CHECKBOX_FORMAT = '"☑";;"☐"'

_INVALID_SHEET_CHARS = re.compile(r"[\\/*?:\[\]]")


def _item_label(group: GradedGroup, item: GradedItem) -> str:
    return group.name if len(group.items) == 1 else f"{group.name} {item.number}"


def _item_notes(group: GradedGroup, item: GradedItem) -> str:
    return "; ".join([*group.important_notes, *item.important_notes])


def _course_rows(course: Course) -> list[tuple]:
    rows = [
        (
            False,
            course.code,
            group.name,
            _item_label(group, item),
            item.due_date,
            item.weight * group.total_weight,
            item.description,
            _item_notes(group, item),
        )
        for group in course.groups
        for item in group.items
    ]
    return sorted(rows, key=lambda row: row[4])


def _write_sheet(ws: Worksheet, rows: list[tuple]) -> None:
    ws.append(_HEADERS)
    for cell in ws[1]:
        cell.font = Font(bold=True)

    for row in rows:
        ws.append(row)

    last_row = len(rows) + 1
    for row_idx in range(2, last_row + 1):
        ws[f"A{row_idx}"].number_format = _CHECKBOX_FORMAT
        ws[f"F{row_idx}"].number_format = "0.0%"

    if rows:
        validation = DataValidation(type="list", formula1='"TRUE,FALSE"', allow_blank=False)
        ws.add_data_validation(validation)
        validation.add(f"A2:A{last_row}")

    for column_cells in ws.columns:
        width = max(len(str(cell.value)) for cell in column_cells)
        ws.column_dimensions[column_cells[0].column_letter].width = min(max(width + 2, 8), 50)


def course_to_workbook(course: Course) -> Workbook:
    """Renders one course's graded items as a standalone checklist workbook."""
    wb = Workbook()
    ws = wb.active
    ws.title = _INVALID_SHEET_CHARS.sub("", course.code)[:31]
    _write_sheet(ws, _course_rows(course))
    return wb


def to_workbook(courses: list[Course]) -> Workbook:
    """Renders all courses as one workbook, with one sheet per course."""
    wb = Workbook()
    wb.remove(wb.active)
    for course in courses:
        ws = wb.create_sheet(title=_INVALID_SHEET_CHARS.sub("", course.code)[:31])
        _write_sheet(ws, _course_rows(course))
    return wb


def write_xlsx(courses: list[Course], out_dir: str) -> None:
    """Writes one .xlsx per course plus a combined 'All Courses.xlsx' (one tab per course)."""
    os.makedirs(out_dir, exist_ok=True)
    for course in courses:
        course_to_workbook(course).save(os.path.join(out_dir, f"{course.code}.xlsx"))
    to_workbook(courses).save(os.path.join(out_dir, "All Courses.xlsx"))
