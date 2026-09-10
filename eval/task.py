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
