"""A token that exists only in the answer, and must be seen to flip.

    python -m eval.canary --corpus E:/ep-corpus/corpus.json results/chunks/bundles-chunk1

`eval.exposure` looks for the task's own fix sha. That is a strong hit and a
weak miss: an agent can read the answer from a paraphrase, a changelog or a
release note without the sha ever appearing. This looks for the *content* of the
answer instead.

**The token.** Identifiers the upstream fix introduces that appear **nowhere in
the base tree** the agent was given. A name the fix invented is something the
run cannot have read locally, so finding one in a returned tool result means the
run reached upstream.

**Why it exists.** PLAN §4.1 says a boundary is untested prevention until the
canary has been **found with the boundary off and absent with it on**, both
observed. Without that pair, "no exposure detected" is indistinguishable from a
screen that never fires — which is the failure this project has now made three
times in other places. `eval.exposure` was never given that pair either, and
this module is what would give it one.

**Where it is strong and where it is not.**

- A token in a **returned tool result** is strong: the run was handed the
  answer's own vocabulary by something outside the workspace.
- A token in the **agent's own writing** is weak, and is reported separately
  rather than counted. Two people fixing the same bug can land on the same
  function name, and a screen that cannot tell convergence from retrieval would
  manufacture the finding it was built to detect.
- Tokens shorter than seven characters are dropped. `kw_only` is a plausible
  independent invention; `_resolve_types_cached` is not.

Like `eval.exposure`, this reports a floor and refuses to filter. A run flagged
here is not disqualified; it is a run whose score means something different, and
dropping it would select on a behaviour that may itself depend on difficulty and
on the treatment.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
from pathlib import Path

from collections import Counter

from .exposure import transcript

GIT = ["git", "-c", "core.autocrlf=false", "-c", "core.eol=lf"]

# Identifiers, not words: something that could be a symbol in the patched code.
IDENT = re.compile(r"\b[A-Za-z_][A-Za-z0-9_]{6,}\b")

# A name the fix brought into existence. Covers the Python shapes the mined
# corpus actually contains; a language this misses simply yields no canary for
# that task, which `report` says out loud rather than reading as innocence.
DEFINES = (
    re.compile(r"^\s*def\s+([A-Za-z_]\w+)"),
    re.compile(r"^\s*class\s+([A-Za-z_]\w+)"),
    re.compile(r"^\s*([A-Za-z_]\w+)\s*(?::[^=]+)?=[^=]"),
    re.compile(r"^\s*self\.([A-Za-z_]\w+)\s*(?::[^=]+)?=[^=]"),
)

# Names common enough that inventing one independently is unremarkable. Not an
# exhaustive list and not meant to be — it is the difference between a screen
# that reports a floor and one that reports noise.
ORDINARY = frozenset("""
    __init__ __repr__ __slots__ __class__ __module__ __qualname__ __getattr__
    isinstance property classmethod staticmethod NotImplemented ValueError
    TypeError KeyError RuntimeError Exception attribute argument parameter
    default factory converter validator instance function returns callable
    metadata annotations deprecated warnings collections itertools functools
    dataclass frozenset namedtuple Optional Sequence Iterable Callable
""".split())


def _git(repo: str, *args: str) -> str:
    done = subprocess.run([*GIT, "-C", repo, *args], capture_output=True,
                          text=True, encoding="utf-8", errors="replace")
    return done.stdout if done.returncode == 0 else ""


def tokens(repo: str, base: str, fix: str, limit: int = 40) -> list[str]:
    """Identifiers the fix introduces that the base tree does not contain.

    Added lines only: a name the fix *removed* was in the base, and a name it
    merely moved is not new vocabulary either.
    """
    diff = _git(repo, "diff", f"{fix}^", fix)
    if not diff:
        return []
    added = set()
    for line in diff.splitlines():
        if not line.startswith("+") or line.startswith("+++"):
            continue
        body = line[1:].strip()
        # Prose the fix added is not vocabulary the fix invented. A docstring
        # contributed `According`, `Determine` and `Iterates`, and a model
        # writing ordinary English hits all three without going anywhere.
        if body.startswith(("#", '"""', "'''", "*", "..")):
            continue
        # Names the fix DEFINES, not names it uses. `inspect.getattr_static` is
        # absent from the base tree and an agent can reach for it unaided,
        # because it belongs to the standard library rather than to this
        # project. A definition is something the fix invented, which is the
        # only kind of vocabulary a run cannot have arrived at locally.
        for pattern in DEFINES:
            added.update(pattern.findall(body))
    # Distinctive shapes only: an underscore, or CamelCase with more than one
    # hump. `fallback_signers` and `BadTimeSignature` are not independently
    # invented; `fallback` and `signers` are ordinary words that happen to
    # appear in a diff. This screen reports a floor, so precision matters more
    # than recall.
    added = {t for t in added
             if len(t) > 6 and ("_" in t or sum(c.isupper() for c in t) > 1)}
    added -= ORDINARY
    if not added:
        return []

    # One pass over the base tree rather than one `git grep` per candidate:
    # forty subprocesses per task made this unusable on the real corpus.
    #
    # `-e` binds to ONE pattern. Writing `"-e", *added` put it before the first
    # token only and left the rest to be read as pathspecs, so the base tree was
    # searched for a single identifier, nothing was excluded, and every run came
    # back flagged on words like `context` and `datetime`. A screen that fires
    # on everything is the false positive this module was written to avoid, and
    # it announced itself by reporting 52 hits out of 52.
    patterns = [arg for token in sorted(added) for arg in ("-e", token)]
    present = set(_git(repo, "grep", "-hoIF", *patterns, base).split())
    return sorted(added - present)[:limit]


def caught(bundle: Path, marks: list[str]) -> tuple[list[str], list[str], dict[str, str], dict[str, int]]:
    """Tokens the run was handed before it used them, and tokens it reached itself.

    **Order is the evidence, not presence.** A token arriving in a tool result
    *before* the agent has written it anywhere is a name it did not invent. The
    same token arriving afterwards is the agent reading back its own work —
    pytest naming the test it just wrote, `cat` showing the file it just saved.

    Presence alone was tried first and it reported 26 of 36 runs, because
    `"tool_use_id"` appears in the assistant's own tool *calls* as well as in
    the results coming back, so every Write of a new symbol counted as being
    handed it. The give-away was `wrote it without being handed it: 0`: a screen
    that never finds the innocent case is not distinguishing the cases.
    """
    if not marks:
        return [], [], {}, {}
    answer_path = bundle / "answer.json"
    if not answer_path.exists():
        return [], [], {}, {}
    session = json.loads(answer_path.read_text(encoding="utf-8")).get("session_id")
    path = transcript(session) if session else None
    if path is None:
        return [], [], {}, {}

    first_given: dict[str, int] = {}
    first_used: dict[str, int] = {}
    calls: dict[str, tuple[str, str]] = {}
    via: dict[str, str] = {}
    for turn, line in enumerate(path.read_text(encoding="utf-8", errors="replace").splitlines()):
        try:
            entry = json.loads(line)
        except json.JSONDecodeError:
            continue
        content = (entry.get("message") or {}).get("content")
        if not isinstance(content, list):
            continue
        for part in content:
            if part.get("type") == "tool_use":
                args = part.get("input") or {}
                calls[part.get("id")] = (part.get("name") or "?",
                                         str(args.get("command") or args.get("file_path") or ""))
            if not any(mark in line for mark in marks):
                continue
            blob = json.dumps(part)
            # A tool_result is content flowing INTO the run. Assistant text and
            # tool_use are the run's own output.
            into = part.get("type") == "tool_result"
            for mark in marks:
                if mark not in blob:
                    continue
                if into:
                    if mark not in first_given:
                        first_given[mark] = turn
                        name, argument = calls.get(part.get("tool_use_id"), ("?", ""))
                        via[mark] = f"{name} {argument}".strip()
                else:
                    first_used.setdefault(mark, turn)

    handed = sorted(m for m, at in first_given.items()
                    if at < first_used.get(m, 1 << 30))
    reached = sorted(m for m in first_used if m not in handed)
    return handed, reached, {m: via[m] for m in handed if m in via}, dict(first_given)


# What kind of door the answer came through. `Bash` alone says nothing - the
# same tool runs `cat` and `gh pr diff` - so the command decides, not the name.
UPSTREAM_CALL = re.compile(r"\b(gh|curl|wget|git clone|git fetch|pip download)\b")
INSTALLED = re.compile(r"site-packages|dist-packages", re.I)


SEVERITY = ("local workspace", "installed package", "upstream network")


def _channel(source: str) -> str:
    if source.startswith(("WebFetch", "WebSearch")) or UPSTREAM_CALL.search(source):
        return "upstream network"
    if INSTALLED.search(source):
        return "installed package"
    return "local workspace"


def report(bundles: Path, corpus: Path) -> int:
    rows = {r["name"]: r for r in json.loads(corpus.read_text(encoding="utf-8"))}
    runs = sorted(d for d in bundles.iterdir() if (d / "answer.json").exists())
    if not runs:
        print(f"no runs under {bundles}")
        return 1

    marks: dict[str, list[str]] = {}
    channel: Counter = Counter()
    flagged = weak = 0
    for run in runs:
        task = json.loads((run / "manifest.json").read_text(encoding="utf-8"))["task"]
        row = rows.get(task)
        if not row:
            continue
        if task not in marks:
            marks[task] = tokens(row["repo"], row["base"], row["fix"])
        handed, wrote, via, order = caught(run, marks[task])
        if handed:
            flagged += 1
            # The STRONGEST channel the run used, not the earliest. The
            # question is whether this run was closed-book at all, and a run
            # that reads its workspace first and then runs `gh pr diff` is not
            # made local by the order it did them in.
            source = max((via[m] for m in handed if m in via),
                         key=lambda c: SEVERITY.index(_channel(c)), default="?")
            channel[_channel(source)] += 1
            print(f"  HANDED  {run.name}: {', '.join(handed[:3])}")
            print(f"          via {source[:88]}")
        elif wrote:
            weak += 1
            print(f"  reached {run.name}: {', '.join(wrote[:4])}")

    coverage = sum(1 for t in marks.values() if t)
    # A run on a task with no canary cannot be flagged, so counting it in the
    # denominator would dilute the rate with runs the screen was never able to
    # see. The rate is over the runs this could have caught.
    watchable = sum(1 for r in runs
                    if marks.get(json.loads((r / "manifest.json")
                                            .read_text(encoding="utf-8"))["task"]))
    print(f"\n{len(runs)} runs, {len(marks)} tasks, {coverage} with a usable canary")
    print(f"runs the screen could see at all   : {watchable}")
    print(f"handed the answer's own vocabulary : {flagged}"
          + (f"  ({flagged / watchable:.0%} of watchable)" if watchable else ""))
    print(f"reached it without being handed it : {weak}  (convergence, not retrieval)")
    if channel:
        print("\nwhere the answer came from:")
        for kind, n in channel.most_common():
            print(f"  {kind:22s} {n}")
    if not coverage:
        print("\nNo task produced a token. This says nothing about exposure - it says")
        print("the canary could not be built, which is a different sentence.")
    elif not flagged:
        print("\nNothing found. Under PLAN 4.1 that is only meaningful once this same")
        print("screen has been SEEN to fire with the boundary off. Until both states")
        print("have been observed, a quiet screen and a broken one look identical.")
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    if "--corpus" not in argv:
        print(__doc__)
        return 1
    at = argv.index("--corpus")
    # The value after `--corpus` is not a positional, whichever side it is
    # given on. Reading it as one made the corpus path arrive as the bundles
    # directory, which fails loudly here and would not everywhere.
    rest = [a for i, a in enumerate(argv[1:], 1)
            if not a.startswith("-") and i != at + 1]
    if not rest:
        print(__doc__)
        return 1
    return report(Path(rest[0]), Path(argv[at + 1]))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
