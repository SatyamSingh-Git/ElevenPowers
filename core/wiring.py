"""Which events the runtime needs, and the hook configuration that delivers them.

The scope guard shipped inert because `hooks.json` subscribed `PostToolUse` to
Bash alone, so no file tool ever reached the handler that records what the task
has read. The handler was right, its tests passed, and it was never called.

Unit tests cannot catch that: they invoke the handler directly, which is
precisely the step the host was not performing. So the subscription is
generated from the same constants the handlers branch on, and a test asserts
that the checked-in file still matches. Divergence becomes impossible rather
than merely unlikely.
"""

from __future__ import annotations

import json

# Tools whose use the guard may question before it happens.
EDIT_TOOLS = ("Edit", "Write", "NotebookEdit")
# Tools whose use tells the task what it has looked at.
FILE_TOOLS = ("Read", "Edit", "Write", "NotebookEdit", "NotebookRead")
# Tools that produce evidence. `PowerShell` is a separate tool name, used on
# Windows where Git Bash is not installed — so on those machines the runtime was
# subscribed to a shell that never ran and saw no commands at all.
COMMAND_TOOLS = ("Bash", "PowerShell")

GUARDED = COMMAND_TOOLS + EDIT_TOOLS
RECORDED = COMMAND_TOOLS + FILE_TOOLS

# A failing tool call raises PostToolUseFailure instead of PostToolUse, so a
# runtime subscribed only to the latter sees successes and never failures. That
# is the exact opposite of what a verification layer needs.
EVENTS: dict[str, str] = {
    "SessionStart": "startup|resume|compact",
    "UserPromptSubmit": "",
    "PreToolUse": "|".join(GUARDED),
    "PostToolUse": "|".join(RECORDED),
    "PostToolUseFailure": "|".join(COMMAND_TOOLS),
    "Stop": "",
}

# Reading a payload and appending to the ledger is fast, and a hook that hangs
# is worse than one that gives up. Stop is the exception: it may run the
# project's whole test suite to compute the evidence rather than demand it, and
# a callback killed at twenty seconds loses its output and makes no decision at
# all. The host's documented default for a command hook is 600 seconds, and this
# has to outlast `core.verify.TIMEOUT` or self-discharge cannot finish.
TIMEOUT = 20
STOP_TIMEOUT = 600


def hooks_json(command: str = 'python "${CLAUDE_PLUGIN_ROOT}/bin/ep_hook.py"') -> dict:
    """The plugin's hook configuration, derived rather than maintained."""
    hooks = {}
    for event, matcher in EVENTS.items():
        entry: dict = {}
        if matcher:
            entry["matcher"] = matcher
        entry["hooks"] = [{
            "type": "command",
            "command": f"{command} {event}",
            "timeout": STOP_TIMEOUT if event == "Stop" else TIMEOUT,
        }]
        hooks[event] = [entry]
    return {"hooks": hooks}


def rendered() -> str:
    return json.dumps(hooks_json(), indent=2) + "\n"


if __name__ == "__main__":
    from pathlib import Path

    target = Path(__file__).resolve().parents[1] / "plugin" / "hooks" / "hooks.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(rendered(), encoding="utf-8")
    print(f"wrote {target}")
