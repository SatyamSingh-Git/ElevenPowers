"""Collect engine intent without making the engine speak a new host protocol."""
from contextlib import contextmanager
from contextvars import ContextVar
import json
import sys

_sink: ContextVar[list | None] = ContextVar("host_response", default=None)


def emit(event: str, fields: dict) -> None:
    sink = _sink.get()
    if sink is None:
        response = {"hookSpecificOutput": {"hookEventName": event, **fields}}
        print(json.dumps(response), flush=True)
        from ..milestones.delivery import emitted
        emitted(response)
    else:
        sink.append({"event": event, **fields})


def block(message: str) -> int:
    sink = _sink.get()
    if sink is None:
        print(message, file=sys.stderr)
    else:
        sink.append({"error": message})
    return 2


@contextmanager
def collect():
    messages = []
    token = _sink.set(messages)
    try:
        yield messages
    finally:
        _sink.reset(token)


def fields_of(messages: list[dict]) -> dict:
    """Combine context rather than dropping earlier messages from a handler."""
    result = {}
    for message in messages:
        for key, value in message.items():
            if key in {"event", "error"}:
                continue
            if key in {"additionalContext", "systemMessage"} and key in result:
                result[key] += "\n" + value
            else:
                result[key] = value
    return result
