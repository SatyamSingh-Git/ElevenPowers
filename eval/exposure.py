"""Did the runs have access to their own answers?

    python -m eval.exposure results/chunks/bundles-chunk1 --corpus E:/ep-corpus/paired.json

A repair score is a claim about what the worker could not see, and this project
published one for a hundred runs without ever stating the claim. An external
review then found the agents fetching the upstream fix: `click-bec59289`, the
single discordant pair the whole comparison rested on, has a returned
`tool_result` carrying the GitHub API's file list for
`bec59289d8cf9b9b4010642b2fee483e5f8eeefc` — its own answer commit.

The agents did nothing wrong. They were asked to make a change described by its
commit message and fetching that commit is a sensible way to do it. The boundary
was never drawn, so there was nothing to cross.

**What this can and cannot say.** A hit is strong: the task's own fix sha,
appearing in the host transcript, is not a coincidence. A miss is weak: an agent
can read the answer from a paraphrase, a changelog or a local clone without the
sha ever appearing. So this reports a floor on exposure, never absence of it.

**Why it does not filter.** It would be easy to drop the flagged runs and
recompute a cleaner score. That selects on a behaviour which may itself depend
on difficulty and on the treatment — the arm that is stopped and asked for
evidence may search differently — and a population selected on the outcome is
the E6 mistake in a new place. Report the exposure beside the score; rerun under
a declared boundary if a closed-book number is wanted.
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

# Where the host keeps a session's transcript. The bundle records the session
# id; the workspace it ran in is long gone, so the directory is matched by glob
# rather than reconstructed.
TRANSCRIPTS = Path.home() / ".claude" / "projects"

DIFF = re.compile(r"diff --git |^\+\+\+ b/|@@ -\d+", re.MULTILINE)
UPSTREAM = re.compile(r"github\.com/[\w.-]+/[\w.-]+/(pull|commit)/")


def transcript(session: str) -> Path | None:
    return next(TRANSCRIPTS.glob(f"*/{session}.jsonl"), None)


def exposure(bundle: Path, fix: str) -> list[str]:
    """What this run could see of its own answer, as far as the transcript says."""
    answer = json.loads((bundle / "answer.json").read_text(encoding="utf-8"))
    session = answer.get("session_id")
    path = transcript(session) if session else None
    if path is None:
        return ["no transcript"]

    body = path.read_text(encoding="utf-8", errors="replace")
    seen = []
    # The decisive one: the task's own fix commit, named. Abbreviations shorter
    # than eight characters collide often enough to be worthless as evidence.
    for length in (40, 12, 10, 8):
        if fix[:length] in body:
            seen.append(f"its own fix sha ({length} chars)")
            break
    if UPSTREAM.search(body):
        seen.append("an upstream pull/commit url")
    if DIFF.search(body):
        seen.append("diff hunks")
    return seen


def report(bundles: Path, corpus: Path) -> int:
    fixes = {r["name"]: r["fix"] for r in
             json.loads(corpus.read_text(encoding="utf-8"))}
    runs = sorted(d for d in bundles.iterdir() if (d / "answer.json").exists())
    if not runs:
        print(f"no bundles under {bundles}")
        return 1

    answered, missing = [], 0
    for d in runs:
        task = d.name.split("--")[0]
        if task not in fixes:
            missing += 1
            continue
        seen = exposure(d, fixes[task])
        if seen and seen != ["no transcript"]:
            answered.append((d.name, seen))

    own = [(n, s) for n, s in answered if any("fix sha" in x for x in s)]
    print(f"{len(runs)} run(s) from {bundles}")
    if missing:
        print(f"{missing} not in this corpus and skipped")
    print()
    print(f"{len(own)} name their own task's fix commit")
    print(f"{len(answered)} show any upstream-answer signal")
    print()
    for name, seen in own:
        print(f"  {name[:58]:<60}{', '.join(seen)}")

    print()
    if own:
        print("A hit is strong and a miss is weak: an answer can be read from a")
        print("paraphrase or a local clone without the sha appearing. This is a")
        print("floor on exposure. Do not drop these runs and rescore -- retrieval")
        print("may depend on difficulty and on the arm, and filtering on it")
        print("selects the population. Rerun under a declared boundary instead.")
    else:
        print("No run named its own fix commit. That is not a closed-book")
        print("certificate: it is the absence of the one signal this can see.")
    return 0


def main(argv: list[str]) -> int:
    rest = [a for a in argv[1:] if not a.startswith("-")]
    if not rest:
        print(__doc__)
        return 1
    corpus = argv[argv.index("--corpus") + 1] if "--corpus" in argv else "corpus.json"
    return report(Path(rest[0]), Path(corpus))


if __name__ == "__main__":
    sys.exit(main(sys.argv))
