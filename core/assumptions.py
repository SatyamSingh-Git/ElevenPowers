"""Claims about things nobody ran.

Design note: `docs/design/unverified-assumptions.md`.

One day's defects in this repository, every one of them the same shape: a
pattern was written describing some producer's output, and the producer was
never run. TAP counters, a monorepo's line prefix, how Go attaches methods, what
Rust names first, a grammar's spelling, how long a parse costs. Seven, found by
executing the real thing and reading what came back - **none** by thinking
harder about it.

That is not local. It is **API Knowledge Conflict**, 20.41% of hallucinations in
the largest taxonomy of the phenomenon (Zhang et al., arXiv:2409.20550, 1,380
annotated snippets), and the obvious remedy is measured to barely work: their
retrieval-augmented mitigation moved Pass@1 by 0.87 to 3.05 percentage points,
and other work finds that *even with oracle documentation retrieval* models
still misuse APIs, because documentation says **what** to call and not **how**
it behaves.

What does work is execution. So this module does not ask the agent to be
careful, and does not hand it more documentation. It asks the ledger a question
the ledger can answer:

    a pattern this task introduced, which never matched any output this task
    actually saw, is an assumption nobody verified

and a second one, from machinery `core/stress.py` already runs:

    a test this task added, which passes on the tree as it was, did not test
    this change

Both report. Neither refuses.
"""

from __future__ import annotations

import re
from pathlib import Path

# A string literal worth treating as a claim about text. Two or more of these,
# and it is a pattern rather than a message.
METACHARACTERS = ("^", "$", r"\d", r"\s", r"\w", r"\b", "[", "]", "(", ")",
                  "+", "*", "?", "|", "{")

# String literals on lines a diff added. Both quote styles, and Python's raw
# prefix, which is how nearly every regex in this repository is written.
LITERAL = re.compile(r"""(?:r|rb|br)?(?P<q>['"])(?P<body>(?:\\.|(?!(?P=q))[^\\])*)(?P=q)""")

MINIMUM = 6


def _added_lines(root: Path, base: str, paths: list[str]) -> list[str]:
    """Only the lines this task introduced, from git."""
    import subprocess

    if not base or not paths:
        return []
    try:
        done = subprocess.run(["git", "diff", "-U0", base, "--", *paths], cwd=root,
                              capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=60)
    except (OSError, subprocess.SubprocessError):
        return []
    if done.returncode != 0:
        return []
    return [line[1:] for line in done.stdout.splitlines()
            if line.startswith("+") and not line.startswith("+++")]


def patterns_added(root: Path, base: str, paths: list[str]) -> list[str]:
    """Regular expressions this task introduced, as written.

    Deliberately literal-by-literal rather than clever. A pattern built by
    concatenation is read in pieces, and a piece that matches nothing is still
    worth asking about - which is how `TAP_PREFIX` would have been caught.
    """
    found: list[str] = []
    for line in _added_lines(root, base, paths):
        if line.lstrip().startswith(("#", "//", "*")):
            continue                      # a comment is not a claim about text
        for match in LITERAL.finditer(line):
            body = match.group("body")
            if len(body) < MINIMUM:
                continue
            if sum(1 for mark in METACHARACTERS if mark in body) < 2:
                continue
            try:
                re.compile(body)
            except re.error:
                continue                  # not a pattern, or not one yet
            # A pattern that matches the empty string needs no skip here: it
            # matches every captured output, so it is confirmed by anything and
            # never reported. A guard for it was written, and flipping it showed
            # it did nothing - removed rather than left looking load-bearing.
            if body not in found:
                found.append(body)
    return found


def unverified(ledger, root: Path | None = None) -> list[str]:
    """Patterns this task wrote that nothing it ran ever produced.

    The question is not "is this regex correct" - nobody can answer that from
    the text. It is "did anything you actually saw look like this", which the
    ledger can answer exactly, because it kept what the commands printed.
    """
    here = root if root is not None else ledger.root
    seen = "\n".join(str(item.get("text", "")) for item in ledger.outputs)
    if not seen.strip():
        # Nothing was captured, so nothing can be confirmed *or* denied. Saying
        # "none of your patterns are verified" when no command ran at all is an
        # accusation dressed as a finding.
        return []
    out = []
    for body in patterns_added(here, ledger.base, list(ledger.touched)):
        try:
            # MULTILINE, because a pattern anchored with ^ or $ is written to
            # read one line of a runner's output, and every such pattern in this
            # repository is compiled that way. Matching without it made the
            # forward case fail - the check accusing a pattern that had in fact
            # been confirmed, which is the one error it must never make.
            if not re.search(body, seen, re.MULTILINE):
                out.append(body)
        except re.error:
            continue
    return out


def vacuous_tests(ledger) -> list[str]:
    """Tests this task added that already passed on the tree as it was.

    `core/stress.py` runs the declared check against the base commit and records
    which tests were red there. A test the task added which is **not** among
    them ran green against code that did not yet contain the change - so
    whatever it is testing, it is not this change.

    Silent unless the base tree was actually asked. No run, no accusation.
    """
    from .surface import TEST_NAME

    if not ledger.discrimination or not ledger.base:
        return []
    red = set(ledger.failed_before)
    if not red:
        # The base tree was asked and nothing came back red. That is already
        # reported as a discrimination verdict; repeating it here as a
        # complaint about every new test would be the same fact twice.
        return []
    added = [p for p in ledger.touched if TEST_NAME.search(p)]
    files_red = {r.split("::")[0].replace("\\", "/") for r in red}
    return [p for p in added if p not in files_red]


def wording(patterns: list[str], tests: list[str]) -> list[str]:
    """The report lines, or none at all."""
    said = []
    if patterns:
        shown = ", ".join(repr(p[:48]) for p in patterns[:2])
        more = f" (+{len(patterns) - 2} more)" if len(patterns) > 2 else ""
        said.append(f"unverified: {shown}{more} matched nothing this task ran. "
                    f"A pattern is a claim about output; run the thing and look")
    if tests:
        shown = ", ".join(tests[:2])
        more = f" (+{len(tests) - 2} more)" if len(tests) > 2 else ""
        said.append(f"{shown}{more} passed on the tree as it was, so it did not "
                    f"test this change")
    return said
