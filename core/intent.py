"""Reading the agent's last message for two things the gate must respect.

A gate that blocks an agent for asking the user a question is broken: it forces
the agent to guess instead of waiting for an answer, which is the opposite of
what a verification layer should encourage. A gate with no way to accept "this
cannot be done as asked" pushes the agent toward inventing a completion, which
is the action bias that causes false completion in the first place.
"""

from __future__ import annotations

import re

ASKING = re.compile(
    r"(\?\s*$)"
    r"|\b(which|should i|would you like|do you want|shall i|let me know|"
    r"could you (confirm|clarify|tell)|waiting for|need(s)? (your )?(input|a decision))\b",
    re.I,
)
BLOCKED = re.compile(
    r"\b(cannot|can't|could not|couldn't|unable to)\b[^.]{0,60}\b"
    r"(complete|proceed|continue|do this|finish|implement|access|reach|resolve)\b"
    r"|\bblocked\b|\bnot possible\b|\brequires (access|credentials|permission)\b",
    re.I,
)


def is_question(message: str) -> bool:
    """Whether the agent stopped to ask rather than to claim completion."""
    text = (message or "").strip()
    if not text:
        return False
    tail = text.splitlines()[-1].strip() if text.splitlines() else text
    return bool(ASKING.search(tail) or ASKING.search(text[-300:]))


def is_abstention(message: str) -> bool:
    """Whether the agent is reporting a blocker rather than a completion."""
    return bool(BLOCKED.search((message or "")[:600]))
