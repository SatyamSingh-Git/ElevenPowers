"""Merging two sections' gradebooks for the same course into one."""
from ..errors import GradebookError
from ..storage.course_config import course_to_dict


def merge_sections(target, other):
    """Copy `other`'s students and scores into `target`; return how many students were added.

    Both books must describe the same course. A student in both sections is
    refused rather than guessed at, and nothing is copied when any is found.
    """
    if course_to_dict(target.course) != course_to_dict(other.course):
        raise GradebookError(f"{other.course.code} sections have different course settings")
    shared = sorted({s.student_id for s in target.students} & {s.student_id for s in other.students})
    if shared:
        raise GradebookError(f"students in both sections: {', '.join(shared)}")
    for student in other.students:
        target.add_student(student)
    for student_id, assignment_id, score in other.sheet.items():
        target.sheet.set(student_id, assignment_id, score)
    return len(other.students)
