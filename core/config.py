"""What this project has told the runtime about itself.

Two things a repository knows that no amount of scanning reliably recovers: how
its tests are run, and how much interruption its owner wants. Guessing the first
produced hints naming commands that do not exist; having no answer to the second
meant the only choice was the strictest one.

Everything here is optional. A project with no config file behaves exactly as it
did before, which is the point: configuration exists to correct the runtime, not
to be a prerequisite for it.

    .elevenpowers/config.json
    {
      "profile": "strict",
      "commands": {"tests": "make test", "typecheck": "npm run typecheck"}
    }

Command keys match the obligation they satisfy: tests, typecheck, build,
benchmark.
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from pathlib import Path

FILE = "config.json"

# How much the runtime is allowed to interrupt.
#   off     record evidence, say nothing, never block
#   guide   say what would prove the work, report at the end, never block
#   strict  the above, and refuse to stop while obligations are unmet
PROFILES = ("off", "guide", "strict")
DEFAULT_PROFILE = "strict"


@dataclass(frozen=True)
class Config:
    profile: str = DEFAULT_PROFILE
    commands: dict[str, str] = field(default_factory=dict)

    @property
    def blocks(self) -> bool:
        return self.profile == "strict"

    @property
    def speaks(self) -> bool:
        return self.profile != "off"

    @property
    def verifies(self) -> bool:
        """May the runtime run checks of its own, and keep checkpoints?

        Separate from `speaks`, because they are separate capabilities that were
        being decided by one flag. `off` is documented as *record evidence, say
        nothing, never block* - and it was building a git worktree, running the
        declared suite inside it and writing snapshot refs, then returning
        silently. An audit counted the dispatch under `off` and it is real work:
        passive observation should not be running test suites.
        """
        return self.profile != "off"

    def command_for(self, need: str) -> str:
        """The command this project uses for `need`, or an empty string."""
        return self.commands.get(need, "")

    def declares(self, need: str) -> bool:
        return bool(self.commands.get(need))


def load(root: Path) -> Config:
    raw: dict = {}
    path = root / ".elevenpowers" / FILE
    if path.exists():
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            raw = {}

    # The environment wins, so a profile can be changed for one session without
    # editing a file that is probably committed.
    profile = os.environ.get("EP_PROFILE") or raw.get("profile") or DEFAULT_PROFILE
    if profile not in PROFILES:
        profile = DEFAULT_PROFILE

    commands = raw.get("commands") or {}
    if not isinstance(commands, dict):
        commands = {}
    return Config(
        profile=profile,
        commands={k: str(v) for k, v in commands.items() if isinstance(v, str) and v},
    )


def save(root: Path, config: Config) -> None:
    path = root / ".elevenpowers" / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"profile": config.profile, "commands": config.commands}, indent=2),
        encoding="utf-8",
    )
