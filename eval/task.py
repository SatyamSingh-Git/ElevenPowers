"""The shape of a seeded-bug task.

Its own module so that suites can import it without importing each other: the
repository-shaped tasks and the single-function ones both need it, and having
one import the other made a cycle.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Task:
    name: str
    prompt: str
    files: dict[str, str]
    hidden: str
    why: str
    naive: tuple[str, str] | None = None
    """The fix an agent reaches for first, as (path, replacement body).

    A task only measures verification if running the existing suite would catch
    this. Where it would not, no amount of evidence-gathering helps and the task
    measures raw capability instead: both a weak and a strong model failed every
    such task, and both resolved every task whose naive fix turned the suite red.
    """
