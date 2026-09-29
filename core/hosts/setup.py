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

PATHS = {"codex": ".codex/hooks.json", "gemini": ".gemini/settings.json", "cursor": ".cursor/hooks.json",
         "copilot": ".github/hooks/elevenpowers.json"}
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
    args = entry.get("args")
    if isinstance(entry.get("exec"), str) and isinstance(args, list) and len(args) == 3 and all(isinstance(a, str) for a in args):
        if Path(args[0]).name == "ep_host.py" and args[1] == "copilot" and args[2] in adapter("copilot").EVENTS:
            return True
    command = entry.get("command", "")
    if isinstance(command, str) and "ep_host.py" in command and any(
            command.endswith(f" {platform} {event}") for platform in ("cursor",)
            for event in adapter(platform).EVENTS):
        return True
    handlers = entry.get("hooks", [])
    return isinstance(handlers, list) and any(isinstance(h, dict) and
        (h.get("statusMessage") == MARKER or h.get("name") == MARKER) for h in handlers)


def _without_owned(value: dict) -> dict:
    result = dict(value)
    hooks = {}
    for name, entries in result.get("hooks", {}).items():
        remaining = []
        for entry in entries:
            if not owned(entry):
                remaining.append(entry)
                continue
            if "hooks" not in entry:
                continue
            kept = [h for h in entry["hooks"] if not (isinstance(h, dict) and
                    (h.get("statusMessage") == MARKER or h.get("name") == MARKER))]
            if kept:
                remaining.append({**entry, "hooks": kept})
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
    if platform in {"cursor", "copilot"} and current.get("version", 1) != 1:
        raise ValueError(f"unsupported {platform} hooks configuration version")
    launcher = Path(source).resolve() / "plugin/bin/ep_host.py"
    executable = Path(python).resolve(strict=True)
    if not launcher.is_file() or not executable.is_file():
        raise ValueError("Python executable and ElevenPowers launcher must exist")
    args = [str(executable), str(launcher)]
    command = subprocess.list2cmdline(args) if os.name == "nt" else shlex.join(args)
    generated = configuration(platform, args if platform == "copilot" else command)
    merged = _without_owned(current)
    if platform in {"cursor", "copilot"}:
        merged["version"] = 1
    hooks = merged.setdefault("hooks", {})
    for event, entries in generated["hooks"].items():
        for entry in entries:
            for handler in entry.get("hooks", []):
                handler["name" if platform == "gemini" else "statusMessage"] = MARKER
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
