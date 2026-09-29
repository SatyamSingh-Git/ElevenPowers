"""Explicitly selected adapter dispatch; never infer a host from user payload."""
from importlib import import_module

from .transport import collect

PLATFORMS = ("codex", "gemini", "cursor")


def adapter(platform: str):
    if platform not in PLATFORMS:
        raise ValueError(f"unsupported platform: {platform}")
    return import_module(f"core.hosts.{platform}")


def run(platform: str, event: str, payload: dict) -> tuple[dict, int]:
    from .. import hook
    host = adapter(platform)
    normalized = host.normalize(event, payload)
    normalized.payload["_ep_platform"] = platform
    from . import lifecycle
    if not lifecycle.before(platform, normalized):
        return {}, 0
    with collect() as messages:
        code = hook.dispatch(normalized.phase, normalized.payload)
    error = "\n".join(m["error"] for m in messages if "error" in m)
    lifecycle.after(platform, normalized, code, error)
    return host.render(event, messages, code, error), 0
