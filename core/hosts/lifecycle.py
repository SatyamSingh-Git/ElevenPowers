"""Bounded delivery deduplication and one-shot host continuation recognition."""
import hashlib
import json
from contextlib import contextmanager

from ..jobs import ledger_write
from ..ledger import _keep_out_of_git
from .setup import _write


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


@contextmanager
def state(root):
    directory = root / ".elevenpowers"
    directory.mkdir(exist_ok=True)
    _keep_out_of_git(directory)
    path = directory / "hosts.json"
    with ledger_write(root):
        value = json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(value, dict):
            raise ValueError("invalid host lifecycle state")
        yield value
        _write(path, value)


def scope(platform, payload):
    return digest([platform, payload.get("session_id", "")])


def before(platform, event) -> bool:
    payload = event.payload
    key = scope(platform, payload)
    if event.phase == "UserPromptSubmit":
        with state(event.root) as value:
            expected = value.setdefault("continuations", {}).pop(key, None)
            if expected and expected == digest(payload.get("prompt", "")):
                return False
    identity = receipt_identity(platform, event)
    if identity:
        from ..ledger import Ledger
        if identity in Ledger.load(event.root).completed_tools:
            return False
    return True


def receipt_identity(platform, event):
    payload = event.payload
    if event.phase in {"PostToolUse", "PostToolUseFailure"} and payload.get("tool_use_id"):
        raw = payload.get("tool_response", {})
        if isinstance(raw, dict) and type(raw.get("exit_code")) is int:
            return digest([scope(platform, payload), payload["tool_use_id"]])
    return None


@contextmanager
def delivery(platform, event):
    from ..ledger import DELIVERY
    token = DELIVERY.set(receipt_identity(platform, event))
    try:
        yield
    finally:
        DELIVERY.reset(token)


def after(platform, event, code, error):
    if event.phase == "Stop" and code == 2 and error:
        with state(event.root) as value:
            pending = value.setdefault("continuations", {})
            pending[scope(platform, event.payload)] = digest(error)
            while len(pending) > 100:
                pending.pop(next(iter(pending)))
