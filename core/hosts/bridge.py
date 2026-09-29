"""Explicitly selected adapter dispatch; never infer a host from user payload."""
from importlib import import_module

from .transport import collect

PLATFORMS = ("codex",)


def adapter(platform: str):
    if platform not in PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")
    return import_module(f"core.hosts.{platform}")


def run(platform: str, event: str, payload: dict) -> tuple[dict, int]:
    from .. import hook
    host = adapter(platform)
    normalized = host.normalize(event, payload)
    with collect() as messages:
        code = hook.dispatch(normalized.phase, normalized.payload)
    error = "\n".join(m["error"] for m in messages if "error" in m)
    return host.render(event, messages, code, error), 0
