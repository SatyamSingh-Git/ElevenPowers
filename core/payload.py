"""Reading what the host actually sends.

Every number this project has produced came from payloads written by hand to
match what the hook contract was assumed to be. Checked against a real session
transcript, the contract differs in three ways, and each one silently disables
the product:

* **There is no exit code.** A Bash result carries `stdout` and `stderr` and
  nothing else. Reading a missing `exit_code` as zero scored every command as
  passing.
* **Failure changes the shape.** A command that exits non-zero comes back as a
  plain string beginning `Error: Exit code 1`, where success is an object.
  Treating the string form as "no structure, assume success" inverted the one
  judgement the whole gate rests on.
* **Failure changes the event.** A failing tool call raises
  `PostToolUseFailure` rather than `PostToolUse`, so a hook subscribed only to
  the latter never sees a failing test at all.

So reading is its own module with its own tests, and those tests run against
payloads captured from a real session rather than invented ones.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

# Hosts have used all three names for the same thing. Accepting each costs
# nothing and makes a rename a non-event rather than a silent outage.
RESULT_KEYS = ("tool_result", "tool_response", "toolUseResult")
OUTPUT_KEYS = ("stdout", "stderr")
TEXT_KEYS = ("output", "content", "result", "text")
CODE_KEYS = ("exit_code", "exitCode", "returncode", "return_code", "code")
ERROR_KEYS = ("is_error", "isError", "error")

EXIT_CODE = re.compile(r"^Error: Exit code (\d+)[ \t]*\r?\n?")

_MISSING = object()


@dataclass(frozen=True)
class ToolResult:
    output: str
    exit_code: int
    readable: bool = True
    skip: str = ""

    @property
    def ok(self) -> bool:
        return self.exit_code == 0


def read_result(payload: dict, event: str = "") -> ToolResult:
    """The output and exit status of a finished tool call.

    `readable` is false when no result field could be found at all, which is
    the symptom of a host contract change. The caller records that rather than
    quietly capturing nothing, because silence is how the last three defects in
    this layer stayed hidden.
    """
    event = event or payload.get("hook_event_name", "")
    failed = event.endswith("Failure")

    raw = next((payload[key] for key in RESULT_KEYS if key in payload), _MISSING)
    if raw is _MISSING or raw is None:
        return ToolResult("", 1 if failed else 0, readable=False)
    if isinstance(raw, str):
        return _from_text(raw, failed)
    if isinstance(raw, list):
        return _from_text(_join(raw), failed)
    if isinstance(raw, dict):
        return _from_object(raw, failed)
    return ToolResult("", 0, readable=False)


def _from_text(text: str, failed: bool) -> ToolResult:
    """A string result means the command failed; the code is in the first line."""
    body = text.lstrip()
    match = EXIT_CODE.match(body)
    if match:
        return ToolResult(body[match.end():], int(match.group(1)) or 1)
    if failed or body.startswith("Error:"):
        return ToolResult(text, 1)
    return ToolResult(text, 0)


def _from_object(raw: dict, failed: bool) -> ToolResult:
    if raw.get("interrupted"):
        # Partial output from a command somebody stopped proves nothing either
        # way, and recording it as a pass would be worse than recording nothing.
        return ToolResult("", 0, skip="interrupted")

    output = "".join(str(raw.get(key) or "") for key in OUTPUT_KEYS)
    if not output:
        for key in TEXT_KEYS:
            value = raw.get(key)
            if isinstance(value, str) and value:
                output = value
                break
            if isinstance(value, list):
                output = _join(value)
                if output:
                    break

    code = next((raw[key] for key in CODE_KEYS if raw.get(key) is not None), None)
    if code is not None:
        return ToolResult(output, int(code))
    if failed or any(raw.get(key) for key in ERROR_KEYS):
        return ToolResult(output or _message(raw), 1)

    known = any(key in raw for key in OUTPUT_KEYS + TEXT_KEYS)
    return ToolResult(output, 0, readable=known)


def _message(raw: dict) -> str:
    for key in ERROR_KEYS:
        value = raw.get(key)
        if isinstance(value, str) and value:
            return value
    return ""


def _join(blocks: list) -> str:
    parts = []
    for block in blocks:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, dict) and isinstance(block.get("text"), str):
            parts.append(block["text"])
    return "\n".join(parts)


def command_of(payload: dict) -> str:
    return str((payload.get("tool_input") or {}).get("command") or "")


def target_file(payload: dict) -> str:
    args = payload.get("tool_input") or {}
    for key in ("file_path", "notebook_path", "path"):
        value = args.get(key)
        if isinstance(value, str) and value:
            return value
    return ""
