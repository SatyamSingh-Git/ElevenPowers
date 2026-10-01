"""Project-scoped native hook setup; merge only entries owned by ElevenPowers."""
from __future__ import annotations

import json
import base64
import os
from pathlib import Path
import shlex
import re
import tempfile

from .bridge import adapter
from .wiring import configuration

PATHS = {"claude": ".claude/settings.local.json", "codex": ".codex/hooks.json", "gemini": ".gemini/settings.json", "cursor": ".cursor/hooks.json",
         "copilot": ".github/hooks/elevenpowers.json"}
MARKER = "elevenpowers-host"
WINDOWS_PREFIX = "powershell.exe -NoProfile -NonInteractive -EncodedCommand "


def invocation(args: list[str]) -> str:
    if os.name != "nt":
        return shlex.join(args)
    # Encode the entire invocation, including event args. This works when the
    # parent host uses either cmd or PowerShell, without expanding path text.
    script = "& " + " ".join("'" + a.replace("'", "''") + "'" for a in args) + "; exit $LASTEXITCODE"
    return WINDOWS_PREFIX + base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def invocation_args(command: str) -> list[str]:
    try:
        if command.startswith(WINDOWS_PREFIX):
            script = base64.b64decode(command[len(WINDOWS_PREFIX):], validate=True).decode("utf-16-le")
            words = re.findall(r"'((?:[^']|'')*)'", script)
            args = [w.replace("''", "'") for w in words]
            expected = "& " + " ".join("'" + a.replace("'", "''") + "'" for a in args) + "; exit $LASTEXITCODE"
            return args if script == expected else []
        if os.name == "nt":
            return [a[1:-1] if a.startswith('"') and a.endswith('"') else a
                    for a in shlex.split(command, posix=False)]
        return shlex.split(command)
    except (ValueError, UnicodeError):
        return []


def config_path(platform: str, project: Path) -> Path:
    if platform != 'claude':
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
    if isinstance(command, str):
        words = invocation_args(command)
        if len(words) == 4 and Path(words[1]).name == "ep_host.py" and words[2] == "cursor" and words[3] in adapter("cursor").EVENTS:
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
    launcher = Path(source).resolve() / ('plugin/bin/ep_hook.py' if platform == 'claude' else 'plugin/bin/ep_host.py')
    executable = Path(python).resolve(strict=True)
    if not launcher.is_file() or not executable.is_file():
        raise ValueError("Python executable and ElevenPowers launcher must exist")
    args = [str(executable), str(launcher)]
    if platform == 'claude':
        from ..wiring import hooks_json
        generated = hooks_json('COMMAND')
    else:
        generated = configuration(platform, args if platform == "copilot" else "COMMAND")
    merged = _without_owned(current)
    if platform in {"cursor", "copilot"}:
        merged["version"] = 1
    hooks = merged.setdefault("hooks", {})
    for event, entries in generated["hooks"].items():
        for entry in entries:
            if platform != "copilot":
                for handler in entry.get("hooks", [entry]):
                    handler["command"] = invocation([*args, event] if platform == 'claude' else [*args, platform, event])
            for handler in entry.get("hooks", []):
                handler["name" if platform == "gemini" else "statusMessage"] = MARKER
        hooks.setdefault(event, []).extend(entries)
    changed = merged != current
    _write(path, merged)
    from .readiness import configured
    configured(platform, project, path, changed)
    return path


def remove(platform: str, project: Path) -> Path:
    path = config_path(platform, project)
    current = read_config(path)
    cleaned = _without_owned(current)
    if cleaned != current:
        _write(path, cleaned)
    from .readiness import removed
    removed(platform, project)
    return path
