"""Reading a real session transcript back into the events a hook would receive.

Every measurement in this project so far ran on scenarios written by the person
who wrote the code being measured. That is useful for finding logic errors and
useless for finding the assumptions both share. A session transcript is the
opposite: it is a record of what an agent actually did, including the tool
results exactly as the host produced them, which is the part that turned out to
be wrong.

Replaying one costs no inference. A few hundred stored sessions support dozens
of offline experiments, which is what makes evaluating this layer affordable at
all.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

# Text the host injects into the user role that is not a person asking for
# anything. Treating these as prompts would restart the ledger mid-task.
INJECTED = ("<task-notification>", "<system-reminder>", "<local-command",
            "<command-name>", "Caveat:", "[Request interrupted")


@dataclass
class Call:
    name: str
    args: dict
    result: object = None

    @property
    def failed(self) -> bool:
        """How the host itself signals failure: a string instead of an object."""
        return isinstance(self.result, str) and self.result.lstrip().startswith("Error:")

    def payload(self, cwd: str) -> dict:
        return {
            "hook_event_name": "PostToolUseFailure" if self.failed else "PostToolUse",
            "tool_name": self.name,
            "tool_input": self.args,
            "tool_result": self.result,
            "cwd": cwd,
        }


@dataclass
class Turn:
    prompt: str
    cwd: str = ""
    calls: list[Call] = field(default_factory=list)
    last_message: str = ""


def load(path: Path, include_subagents: bool = False) -> list[Turn]:
    """The turns in one transcript, in order."""
    turns: list[Turn] = []
    pending: dict[str, Call] = {}
    current: Turn | None = None
    text: list[str] = []

    for row in _rows(path):
        if row.get("isSidechain") and not include_subagents:
            continue
        kind = row.get("type")
        cwd = row.get("cwd", "")

        if kind == "user":
            content = (row.get("message") or {}).get("content")
            results = [b for b in content or []
                       if isinstance(b, dict) and b.get("type") == "tool_result"]
            for block in results:
                call = pending.pop(block.get("tool_use_id"), None)
                if call is not None:
                    call.result = row.get("toolUseResult", block.get("content"))
            if results:
                continue

            # A person's message is the user role with no tool result in it. It
            # arrives as a plain string in some versions and as text blocks in
            # others, so both are read.
            prompt = (content if isinstance(content, str) else _text(content)).strip()
            if not prompt or prompt.startswith(INJECTED):
                continue
            if current:
                current.last_message = "\n".join(text).strip()
                turns.append(current)
            current, text = Turn(prompt=prompt, cwd=cwd), []
            continue

        if kind != "assistant":
            continue
        for block in (row.get("message") or {}).get("content") or []:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text" and block.get("text"):
                text.append(block["text"])
            elif block.get("type") == "tool_use":
                call = Call(name=block.get("name", ""), args=block.get("input") or {})
                pending[block.get("id")] = call
                if current is None:
                    current = Turn(prompt="", cwd=cwd)
                current.calls.append(call)
                current.cwd = current.cwd or cwd

    if current:
        current.last_message = "\n".join(text).strip()
        turns.append(current)
    return [t for t in turns if t.prompt or t.calls]


def _text(blocks) -> str:
    return "\n".join(
        b["text"] for b in blocks or []
        if isinstance(b, dict) and b.get("type") == "text" and isinstance(b.get("text"), str)
    )


def _rows(path: Path):
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def sessions(directory: Path) -> list[Path]:
    """Transcripts under a directory, newest first."""
    return sorted(directory.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)


def default_dir() -> Path:
    return Path.home() / ".claude" / "projects"
