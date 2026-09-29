"""Read-only native configuration diagnostics, separate from live-host proof."""
from pathlib import Path
import sys

from .bridge import adapter
from .setup import config_path, read_config, owned
from .wiring import configuration


def report(platform: str, root: Path) -> tuple[str, bool]:
    host = adapter(platform)
    lines = [f"ElevenPowers {platform}: configuration checks", f"Python {sys.version.split()[0]}"]
    try:
        path = config_path(platform, root)
        if not path.is_file():
            raise ValueError(f"missing native configuration: {path}")
        value = read_config(path)
        generated = configuration(platform, ["PYTHON", "LAUNCHER"] if platform == "copilot" else "COMMAND")
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
                        any(handler.get(k) != v for k, v in wanted.items() if k not in {"exec", "args"})):
                    errors.append(f"{event}: executable, arguments or timeout differs from generated wiring")
                continue
            if len(handlers) != 1 or not handlers[0].get("command", "").endswith(f" {platform} {event}") or any(
                    handlers[0].get(k) != v for k, v in wanted.items() if k != "command"):
                errors.append(f"{event}: command or timeout differs from generated wiring")
        lines.extend(errors or [f"ok: {len(host.EVENTS)} native event subscriptions"])
        ok = not errors
    except (ValueError, OSError) as exc:
        lines.append(f"failed: {exc}")
        ok = False
    lines.extend(getattr(host, "LIMITS", ()))
    lines += ["Host enablement/trust: review in the host", "Live host session: not verified"]
    return "\n".join(lines), ok
