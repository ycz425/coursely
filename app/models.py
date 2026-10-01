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
    items: list[GradedItem] = Field(
        description="The individual graded items belonging to this group, as listed in the syllabus "
        "(e.g. each individual exam, quiz, or assignment)."
    )


class Course(BaseModel):
    name: str = Field(description="The full name of the course as given in the syllabus.")
    code: str = Field(description="The course code or identifier as given in the syllabus (e.g. 'CSC4780').")
    groups: list[GradedGroup] = Field(
        description="All graded categories in the course's grading scheme, each with its overall weight "
        "and the individual items within it."
    )
