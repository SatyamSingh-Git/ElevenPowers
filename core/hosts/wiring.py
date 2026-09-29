"""Generate native subscriptions from the adapter's handled event set."""
from .bridge import adapter


def configuration(platform: str, command: str) -> dict:
    host = adapter(platform)
    hooks = {}
    for native, phase in host.EVENTS.items():
        timeout = 600 if phase == "Stop" else 120 if phase in {
            "SessionStart", "PostToolUse", "PostToolUseFailure"} else 20
        hooks[native] = [{"hooks": [{"type": "command", "command": f"{command} {platform} {native}",
                                    "timeout": timeout}]}]
    return {"hooks": hooks}
