"""Project overrides and manifest-backed verification defaults.

Conventional root manifests supply commands automatically. Project-owned
.elevenpowers/config.json overrides them or disables discovery; no setup file
is generated or overwritten by detection.
"""

from __future__ import annotations

import json
import os
import tomllib
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
    scan: dict = field(default_factory=dict)
    auto_detect: bool = True
    strength: dict = field(default_factory=dict)
    milestone_advice: dict = field(default_factory=dict)
    rule_gate: bool = False
    """Under `strict`, may a declared rule left behind stop the agent once? Off until measured against the note."""
    origins: dict[str, str] = field(default_factory=dict)
    """Commands borrowed from a project's tox, make or CI declaration, by the file they came from."""

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
    if not isinstance(raw, dict):
        raw = {}

    # The environment wins, so a profile can be changed for one session without
    # editing a file that is probably committed.
    profile = os.environ.get("EP_PROFILE") or raw.get("profile") or DEFAULT_PROFILE
    if profile not in PROFILES:
        profile = DEFAULT_PROFILE

    commands = raw.get("commands") or {}
    if not isinstance(commands, dict):
        commands = {}
    auto_detect = raw.get("auto_detect", True) is not False
    origins: dict[str, str] = {}
    effective = discover_commands(root, origins) if auto_detect else {}
    # An empty explicit command disables discovery for that need.
    explicit = {k: v.strip() for k, v in commands.items() if isinstance(v, str)}
    effective.update(explicit)
    return Config(
        origins={k: v for k, v in origins.items() if k not in explicit},
        profile=profile,
        scan=raw.get("scan", {}),
        auto_detect=auto_detect,
        commands={k: v for k, v in effective.items() if v},
        strength=raw.get('strength', {}),
        milestone_advice=raw.get('milestone_advice', {}),
        rule_gate=raw.get('rule_gate') is True,
    )


def _node_commands(root: Path) -> dict[str, str]:
    """Read conventional verification entry points, never execute discovery.

    Only the selected project root is consulted. Conflicting package-manager
    declarations are left for an explicit override rather than guessed.
    """
    pkg = root / "package.json"
    if pkg.is_file():
        try:
            data = json.loads(pkg.read_text(encoding="utf-8-sig"))
        except (ValueError, OSError):
            return {}
        if not isinstance(data, dict) or not isinstance(data.get("scripts", {}), dict):
            return {}
        scripts = {k: v for k, v in data.get("scripts", {}).items()
                   if isinstance(v, str) and v.strip()}
        declared = data.get("packageManager", "")
        manager = declared.split("@", 1)[0] if isinstance(declared, str) else ""
        allowed = {"npm", "pnpm", "yarn", "bun"}
        if declared and manager not in allowed:
            return {}
        if not manager:
            locks = {tool for name, tool in (
                ("package-lock.json", "npm"), ("npm-shrinkwrap.json", "npm"),
                ("pnpm-lock.yaml", "pnpm"), ("yarn.lock", "yarn"),
                ("bun.lock", "bun"), ("bun.lockb", "bun"),
            ) if (root / name).is_file()}
            if len(locks) > 1:
                return {}
            manager = next(iter(locks), "npm")
        choices = {"tests": ("ci", "test"), "typecheck": ("typecheck",),
                   "build": ("build",), "lint": ("lint",), "benchmark": ("benchmark", "bench")}
        return {need: f"{manager} run {name}"
                for need, names in choices.items()
                for name in [next((n for n in names if n in scripts), "")] if name}
    return {}


def discover_commands(root: Path, origins: dict | None = None) -> dict[str, str]:
    """Combine conventional root entry points; root package scripts win.

    With none of those naming a test command, the one the project declares in
    tox, make or CI is borrowed, and `origins` records where it came from.
    """
    commands = _node_commands(root)
    candidates: list[dict[str, str]] = []
    if (root / "Cargo.toml").is_file():
        candidates.append({"tests": "cargo test", "typecheck": "cargo check", "build": "cargo build"})
    if (root / "go.mod").is_file():
        candidates.append({"tests": "go test ./...", "build": "go build ./..."})
    pytest_configured = (root / "pytest.ini").is_file()
    try:
        data = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
        pytest_configured |= isinstance(data.get("tool", {}).get("pytest", {}).get("ini_options"), dict)
    except (OSError, ValueError, AttributeError):
        pass
    if pytest_configured:
        candidates.append({"tests": "python -m pytest"})
    # Multiple native stacks need an aggregate command chosen by the project.
    for need in {key for candidate in candidates for key in candidate}:
        values = {candidate[need] for candidate in candidates if need in candidate}
        if need not in commands and len(values) == 1:
            commands[need] = values.pop()
    if "tests" not in commands:
        from .test_command import declared
        found = declared(root)
        if found:
            commands["tests"] = found[0]
            if origins is not None:
                origins["tests"] = found[1]
    return commands


def declare(root: Path, need: str, command: str) -> None:
    """Set one command in the project's own file, leaving everything else as written.

    `save` would write the discovered commands into the file too, freezing them.
    """
    command = command.strip()
    if not command:
        raise ValueError(f"the {need} command is empty")
    path = root / ".elevenpowers" / FILE
    raw = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
    if not isinstance(raw, dict) or not isinstance(raw.get("commands", {}), dict):
        raise ValueError(f"{path} is not a settings object")
    raw.setdefault("commands", {})[need] = command
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(raw, indent=2), encoding="utf-8")


def save(root: Path, config: Config) -> None:
    path = root / ".elevenpowers" / FILE
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps({"profile": config.profile, "commands": config.commands,
                    "scan": config.scan, "auto_detect": config.auto_detect,
                    "strength": config.strength, "milestone_advice": config.milestone_advice,
                    "rule_gate": config.rule_gate}, indent=2),
        encoding="utf-8",
    )
