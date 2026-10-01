"""Read-only native configuration diagnostics, separate from live-host proof."""
from pathlib import Path
import sys

from .bridge import adapter
from .setup import config_path, read_config, owned, invocation_args
from .wiring import configuration


def report(platform: str, root: Path) -> tuple[str, bool]:
    if platform == 'claude':
        from types import SimpleNamespace
        from ..wiring import EVENTS, hooks_json
        host = SimpleNamespace(EVENTS=EVENTS)
        generated = hooks_json('COMMAND')
        for entries in generated['hooks'].values():
            entries[0]['hooks'][0]['statusMessage'] = 'elevenpowers-host'
    else:
        host = adapter(platform)
        generated = configuration(platform, ["PYTHON", "LAUNCHER"] if platform == "copilot" else "COMMAND")
    lines = [f"ElevenPowers {platform}: configuration checks", f"Python {sys.version.split()[0]}"]
    try:
        path = config_path(platform, root)
        if not path.is_file():
            raise ValueError(f"missing native configuration: {path}")
        value = read_config(path)
        expected = generated["hooks"]
        errors = []
        if "version" in generated and value.get("version") != generated["version"]:
            errors.append("native configuration version differs from generated wiring")
        for event in host.EVENTS:
            found = [entry for entry in value.get("hooks", {}).get(event, []) if owned(entry)]
            if len(found) != 1:
                errors.append(f"{event}: expected one ElevenPowers subscription, found {len(found)}")
                continue
            handlers = found[0].get("hooks", [found[0]])
            wanted = expected[event][0].get("hooks", [expected[event][0]])[0]
            if platform == "copilot":
                handler = handlers[0]
                if (handler.get("args", [])[-2:] != [platform, event] or
                        not Path(handler.get("exec", "")).is_file() or
                        not Path(handler.get("args", [""])[0]).is_file() or
                        any(handler.get(k) != v for k, v in wanted.items() if k not in {"exec", "args"})):
                    errors.append(f"{event}: executable, arguments or timeout differs from generated wiring")
                continue
            args = invocation_args(handlers[0].get("command", ""))
            valid_args = (len(args) == 3 and args[-1:] == [event] if platform == 'claude'
                          else len(args) == 4 and args[-2:] == [platform, event])
            if not valid_args or not all(Path(p).is_file() for p in args[:2]):
                errors.append(f"{event}: interpreter or launcher is missing or invocation is invalid")
            if len(handlers) != 1 or any(
                    handlers[0].get(k) != v for k, v in wanted.items() if k != "command"):
                errors.append(f"{event}: command or timeout differs from generated wiring")
        lines.extend(errors or [f"ok: {len(host.EVENTS)} native event subscriptions"])
        ok = not errors
    except (ValueError, OSError) as exc:
        lines.append(f"failed: {exc}")
        ok = False
    lines.extend(getattr(host, "LIMITS", ()))
    from .readiness import activation
    try:
        live = activation(platform, root)
        lines.append(f"Callback activation: {live['state']} ({live.get('received', 0)} received, {live.get('processed', 0)} processed)")
    except (ValueError, OSError) as exc:
        lines.append(f'Callback diagnostics unavailable: {exc}')
        ok = False
    lines += ["Host enablement/trust: review in the host", "Live host session: not verified; callback observations are not host authentication"]
    return "\n".join(lines), ok
