"""Project-scoped native hook setup; merge only entries owned by ElevenPowers."""
from __future__ import annotations

import json
import os
from pathlib import Path
import shlex
import subprocess
import tempfile

from .bridge import adapter
from .wiring import configuration

PATHS = {"codex": ".codex/hooks.json"}
MARKER = "elevenpowers-host"


def config_path(platform: str, project: Path) -> Path:
    adapter(platform)
    project = Path(project).resolve(strict=True)
    if not project.is_dir():
        raise ValueError("project must be a directory")
    target = project / PATHS[platform]
    if not target.resolve().is_relative_to(project):
        raise ValueError("configuration path escapes project root")
    return target


def read_config(path: Path) -> dict:
    if not path.exists():
        return {}
    value = json.loads(path.read_text(encoding="utf-8-sig"))
    if not isinstance(value, dict) or not isinstance(value.get("hooks", {}), dict):
        raise ValueError("native configuration and hooks must be JSON objects")
    if any(not isinstance(entries, list) for entries in value.get("hooks", {}).values()):
        raise ValueError("native hook event entries must be arrays")
    return value


def owned(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    return any(isinstance(h, dict) and h.get("statusMessage") == MARKER
               for h in entry.get("hooks", []) if isinstance(entry.get("hooks"), list))


def _without_owned(value: dict) -> dict:
    result = dict(value)
    hooks = {}
    for name, entries in result.get("hooks", {}).items():
        remaining = [entry for entry in entries if not owned(entry)]
        if remaining or not entries:
            hooks[name] = remaining
    if hooks:
        result["hooks"] = hooks
    else:
        result.pop("hooks", None)
    return result


def _write(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = json.dumps(value, indent=2, ensure_ascii=False) + "\n"
    if path.exists() and path.read_text(encoding="utf-8") == text:
        return
    fd, name = tempfile.mkstemp(prefix=".elevenpowers-", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            stream.write(text)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def install(platform: str, project: Path, python: str, source: Path) -> Path:
    path = config_path(platform, project)
    current = read_config(path)
    launcher = Path(source).resolve() / "plugin/bin/ep_host.py"
    executable = Path(python).resolve(strict=True)
    if not launcher.is_file() or not executable.is_file():
        raise ValueError("Python executable and ElevenPowers launcher must exist")
    args = [str(executable), str(launcher)]
    command = subprocess.list2cmdline(args) if os.name == "nt" else shlex.join(args)
    generated = configuration(platform, command)
    merged = _without_owned(current)
    hooks = merged.setdefault("hooks", {})
    for event, entries in generated["hooks"].items():
        for entry in entries:
            for handler in entry["hooks"]:
                handler["statusMessage"] = MARKER
        hooks.setdefault(event, []).extend(entries)
    _write(path, merged)
    return path


def remove(platform: str, project: Path) -> Path:
    path = config_path(platform, project)
    current = read_config(path)
    cleaned = _without_owned(current)
    if cleaned != current:
        _write(path, cleaned)
    return path
