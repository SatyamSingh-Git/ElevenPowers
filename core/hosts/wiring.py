"""Generate native subscriptions from the adapter's handled event set."""
from .bridge import adapter


def configuration(platform: str, command: str) -> dict:
    host = adapter(platform)
    hooks = {}
    for native, phase in host.EVENTS.items():
        timeout = 600 if phase == "Stop" else 120 if phase in {
            "SessionStart", "PostToolUse", "PostToolUseFailure"} else 20
        if platform == "gemini":
            timeout *= 1000
        if platform == "cursor":
            handler = {"command": f"{command} {platform} {native}", "timeout": timeout}
            if phase == "Stop":
                handler["loop_limit"] = 2
            hooks[native] = [handler]
            continue
        hooks[native] = [{"hooks": [{"type": "command", "command": f"{command} {platform} {native}",
                                    "timeout": timeout}]}]
    return {"version": 1, "hooks": hooks} if platform == "cursor" else {"hooks": hooks}
