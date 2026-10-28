"""Report cards: one text file per student, ready to print or send home."""
from pathlib import Path

from ..grading.explain import explain_grade
from .progress import progress_report, render_progress


def write_report_cards(book, folder, as_of=None):
    """Write `<student_id>.txt` for every student into `folder`; return the paths written."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    written = []
    for student in book.students:
        report = progress_report(book, student.student_id, as_of)
        explanation = explain_grade(book.course, book.grade(student.student_id, as_of))
        text = render_progress(report) + "\nHow the grade is reached:\n"
        text += "".join(f"  {line}\n" for line in explanation)
        path = folder / f"{_safe_name(student.student_id)}.txt"
        path.write_text(text, encoding="utf-8")
        written.append(path)
    return written


def _safe_name(student_id):
    return "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in student_id)
