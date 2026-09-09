"""Infer which claims a request implies.

Deterministic first. A model call is the documented fallback, not the default:
this version costs no tokens and no latency, and it is testable offline against
labelled traces (P3). If measurement shows the heuristic misreading real
requests, `infer` gains a model call for the cases it marks uncertain.
"""

from __future__ import annotations

import re

from .obligations import Claim

PATTERNS: list[tuple[re.Pattern, Claim]] = [
    # `\w{2,}Error` catches a pasted TypeError or ValueError, where the word
    # "error" never stands alone. Pasting a stack trace is the commonest way a
    # real session reports a bug.
    (re.compile(r"\b(fix|bug|broken|fail\w*|regression|crash|error|race|deadlock|leak"
                r"|traceback|exception)\b|\w{2,}Error\b", re.I), Claim.BUG_FIXED),
    (re.compile(r"\b(migrat\w+|schema change|alter table|backfill)\b", re.I), Claim.MIGRATION_SAFE),
    (re.compile(r"\b(refactor|rename|extract|move|reorganis\w+|reorganiz\w+|clean up|tidy)\b", re.I), Claim.REFACTOR_SAFE),
    (re.compile(r"\b(faster|speed up|optimi[sz]e|performance|latency|slow)\b", re.I), Claim.PERF_IMPROVED),
    (re.compile(r"\b(upgrade|bump|update)\b.*\b(dependenc\w+|package|version|lockfile)\b", re.I), Claim.DEPS_UPDATED),
    (re.compile(r"\b(add|implement|support|introduce|build|create|enable)\b", re.I), Claim.FEATURE_ADDED),
]

DOCS_ONLY = re.compile(r"\b(readme|changelog|docs?|documentation|comment|typo|wording)\b", re.I)
CODE_WORDS = re.compile(r"\b(function|test|endpoint|api|component|module|class|bug|fix)\b", re.I)

QUESTION = re.compile(
    r"^\s*(what|why|how|where|which|who|when|is|are|does|do|can|could|should|would|explain|describe|tell me|show me)\b",
    re.I,
)
# Anchored to the front of the message. Unanchored, a bare "read" anywhere in
# the text ruled out a claim, so a pasted "cannot read property" stack trace was
# classified as a request to go and read something.
NO_CLAIM = re.compile(
    r"^\s*(?:please\s+|can you\s+|could you\s+|just\s+|now\s+)?"
    r"(explain|understand|review|read|look at|investigate|explore|summari[sz]e|compare)\b",
    re.I,
)


def infer(request: str) -> list[Claim]:
    """Zero or more claims. Zero means the runtime stays out of the way."""
    text = request.strip()
    if not text:
        return []

    if QUESTION.match(text) and not re.search(r"\b(fix|add|implement|change|update|remove)\b", text, re.I):
        return []
    if NO_CLAIM.search(text) and not re.search(r"\b(fix|add|implement|then)\b", text, re.I):
        return []

    if DOCS_ONLY.search(text) and not CODE_WORDS.search(text):
        return [Claim.DOCS_CHANGED]

    found = [claim for pattern, claim in PATTERNS if pattern.search(text)]
    if not found:
        # No fallback claim. Across 3,557 real turns, claiming a feature for any
        # sentence longer than two words attached obligations to more than half
        # of all turns, most of which changed nothing. Work that says nothing
        # about itself is claimed when it starts editing instead.
        return []

    # A fix inside a refactor is a fix; a perf change that is also a refactor is
    # a perf change. Earlier patterns win, and only one claim is kept unless the
    # request plainly asks for two separate things.
    primary = found[0]
    if primary in (Claim.BUG_FIXED, Claim.MIGRATION_SAFE, Claim.PERF_IMPROVED):
        return [primary]
    return [found[0]]


def opens_new_task(request: str) -> bool:
    """Whether this prompt sets a subject of its own.

    One in five real prompts is four words or fewer, and "continue", "go on" and
    "yes" carry their intent in the conversation rather than in the message.
    Such a prompt must not clear the obligations of work already under way: a
    gate that switches itself off when the user says continue is switched off
    for much of a real session.
    """
    text = request.strip()
    if not text:
        return False
    if infer(text):
        return True
    return bool(QUESTION.match(text) or NO_CLAIM.search(text))
