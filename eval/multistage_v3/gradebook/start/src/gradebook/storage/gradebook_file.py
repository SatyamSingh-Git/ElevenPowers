"""The gradebook file: a course, its roster and its scores in one JSON document."""
import json
from pathlib import Path

from ..errors import ConfigError
from ..model.scores import Score
from ..model.student import Student
from ..services.gradebook import Gradebook
from .course_config import course_from_dict, course_to_dict

FORMAT_VERSION = 1


def save_gradebook(book, path):
    document = {
        "format": FORMAT_VERSION,
        "course": course_to_dict(book.course),
        "students": [
            {"student_id": s.student_id, "last_name": s.last_name, "first_name": s.first_name}
            for s in book.students
        ],
        "scores": [
            {"student_id": student_id, "assignment_id": assignment_id, "points": score.points,
             "submitted_day": score.submitted_day, "excused": score.excused}
            for student_id, assignment_id, score in book.sheet.items()
        ],
    }
    Path(path).write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")


def load_gradebook(path):
    path = Path(path)
    if not path.is_file():
        raise ConfigError(f"no gradebook at {path}; start one with `gradebook new`")
    document = json.loads(path.read_text(encoding="utf-8"))
    version = document.get("format")
    if version != FORMAT_VERSION:
        raise ConfigError(f"{path.name}: gradebook format {version} is not supported")
    book = Gradebook(course_from_dict(document["course"]))
    for entry in document["students"]:
        book.add_student(Student(entry["student_id"], entry["last_name"], entry["first_name"]))
    for entry in document["scores"]:
        # Saved scores were checked when they were recorded; restore them as they are.
        book.sheet.set(entry["student_id"], entry["assignment_id"],
                       Score(entry["points"], entry["submitted_day"], entry["excused"]))
    return book
