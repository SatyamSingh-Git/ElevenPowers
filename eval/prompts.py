"""Real prompts, paired with what the turn that followed them actually did.

Claim inference has no host-recorded ground truth the way a command's exit
status does. What it has is the next best thing: a turn's own behaviour. A turn
that changed no file did not add a feature, whatever its prompt sounded like,
and a turn that rewrote six files was not a question.

That signal is a proxy and it is stated as one wherever it is used. It is wrong
at the edges, and `eval/claim_cases.py` holds hand-labelled prompts to check it
against. It is right often enough to measure a 3,500-turn corpus, which no
amount of hand labelling would reach.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from core.parsers import written_paths
from core.wiring import FILE_TOOLS

from .transcript import Turn, default_dir, load, sessions

EDIT_TOOLS = {"Edit", "Write", "NotebookEdit"}

# Agents write files through the shell as often as through an edit tool: `cat >`
# alone appeared 1,431 times in the corpus. Counting only edit tools would score
# most real work as no work.
WRITES = re.compile(
    r"""(?:^|[\s;&|(])
    (?: sed\s+-i | tee\b | mkdir\b | touch\b | mv\b | cp\b | rm\b | patch\b
      | git\s+(?:commit|apply|checkout|revert|merge|rebase|stash)
      | (?:npm|pnpm|yarn|bun)\s+(?:i|install|add)
      | pip\s+install | cargo\s+add | go\s+get
      | dd\b | curl\s+[^|]*-o\b
    )""",
    re.IGNORECASE | re.VERBOSE,
)
# A redirect that lands in a file, as opposed to `2>&1` or `> /dev/null`.
REDIRECT = re.compile(r">>?\s*(?!&|/dev/null)[\w./\\$\"'-]+")


@dataclass
class Sample:
    prompt: str
    edits: int
    writes: int
    commands: int
    session: str
    edited: tuple[str, ...] = ()

    @property
    def changed_code(self) -> bool:
        return self.edits > 0 or self.writes > 0


def did_write(command: str) -> bool:
    return bool(WRITES.search(command) or REDIRECT.search(command))


def sample(turn: Turn, session: str) -> Sample:
    edited = tuple(
        c.args.get("file_path") or "" for c in turn.calls if c.name in EDIT_TOOLS
    )
    commands = [c.args.get("command", "") for c in turn.calls if c.name == "Bash"]
    return Sample(
        prompt=turn.prompt,
        edits=len(edited),
        writes=sum(1 for c in commands if did_write(c)),
        commands=len(commands),
        session=session,
        edited=tuple(p for p in edited if p) + tuple(
            t for c in commands for t in written_paths(c)
        ),
    )


def collect(base: Path | None = None, limit: int = 0) -> list[Sample]:
    base = base or default_dir()
    out: list[Sample] = []
    for project in sorted(base.iterdir()):
        if not project.is_dir():
            continue
        for path in sessions(project):
            for turn in load(path):
                if turn.prompt:
                    out.append(sample(turn, path.stem))
            if limit and len(out) >= limit:
                return out[:limit]
    return out


__all__ = ["Sample", "collect", "did_write", "sample", "FILE_TOOLS"]
