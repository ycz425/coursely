from pydantic import BaseModel, Field
from typing import Literal

GradedItemType = Literal[
    'final_exam',
    'term_test',
    'tutorial',
    'quiz',
    'assignment',
    'lab'
]


class GradedItem(BaseModel):
    number: int = Field(
        description="This item's 1-indexed position within its group (e.g. 1 for 'Quiz 1', 2 for 'Quiz 2'). "
        "If the syllabus doesn't explicitly number items, assign numbers in the order they appear."
    )
    due_date: str = Field(
        description="The due date of this item as stated in the syllabus, in YYYY-MM-DD format. "
        "If the syllabus gives only a day/month without a year, infer the year from the course term."
    )
    weight: float = Field(
        description="This item's weight as a fraction of its parent group's total_weight "
        "(the weights of all items within a group should sum to 1.0)."
    )
    description: str = Field(
        description="A short factual description of this specific item only (e.g. the topic of an "
        "assignment, or chapters covered on an exam). Empty string if the syllabus doesn't give one. "
        "Don't put information here that applies to every item in the group or to the whole course -- "
        "that belongs on the group's or course's own description instead."
    )
    important_notes: list[str] = Field(
        description="Important notes, rules, or caveats that apply only to this specific item (e.g. "
        "'open book', 'must bring a calculator', 'held in a different room'). Don't repeat notes that "
        "apply to every item in the group or to the whole course -- those belong on the group's or "
        "course's important_notes instead."
    )


class GradedGroup(BaseModel):
    name: str = Field(
        description="The display name of this graded group as given in the syllabus (e.g. 'Homework', "
        "'Midterm Exams', 'Weekly Labs') -- distinct from item_type, which is just its category."
    )
    item_type: GradedItemType = Field(
        description="The category of graded item this group represents: exam, tutorial, quiz, assignment, or lab."
    )
    total_weight: float = Field(
        description="This group's weight toward the final course grade, as a fraction of the whole course "
        "(e.g. 0.3 for 30%). The total_weight of all groups in a course should sum to 1.0."
    )
    description: str = Field(
        description="A short factual description of this assessment category as a whole (e.g. what the "
        "quizzes cover, how assignments are submitted). Empty string if the syllabus doesn't give one. "
        "Don't repeat details specific to a single item (put those on that item's description) or "
        "information about the whole course (put that on the course's description)."
    )
    important_notes: list[str] = Field(
        description="Important notes, rules, or policies that apply to every item in this group (e.g. "
        "'lowest quiz score is dropped', 'late assignments lose 10% per day'). Don't repeat course-wide "
        "policies (put those on the course's important_notes) or notes specific to a single item (put "
        "those on that item's important_notes)."
    )
    items: list[GradedItem] = Field(
        description="The individual graded items belonging to this group, as listed in the syllabus "
        "(e.g. each individual exam, quiz, or assignment)."
    )


class Course(BaseModel):
    name: str = Field(description="The full name of the course as given in the syllabus.")
    code: str = Field(description="The course code or identifier as given in the syllabus (e.g. 'CSC4780').")
    description: str = Field(
        description="A short factual description of the course overall (e.g. subject matter, format, "
        "prerequisites). Empty string if the syllabus doesn't give one. Don't include grading policy "
        "details here -- those belong on the relevant group's or item's description."
    )
    important_notes: list[str] = Field(
        description="Course-wide policies and important notes that apply across the whole course, not "
        "tied to one assessment type (e.g. late work policy, collaboration/academic integrity rules, "
        "attendance policy). Don't repeat notes specific to one group or item -- those belong on that "
        "group's or item's important_notes."
    )
    groups: list[GradedGroup] = Field(
        description="All graded categories in the course's grading scheme, each with its overall weight "
        "and the individual items within it."
    )
