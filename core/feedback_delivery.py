"""Privacy-safe observations of declared-check feedback delivery.

Intent, a flushed host context, and a later exact native receipt are separate
facts. This module records the first two as hashed local diagnostics and joins
the third read-only when someone asks for it. It never runs a command or treats
the sequence as proof of model comprehension.
"""
from __future__ import annotations

from contextlib import contextmanager
from contextvars import ContextVar
import hashlib
import json
import time

from .hosts import readiness
from .jobs import Busy, Superseded, ledger_write
from .ledger import DELIVERY, Ledger
from .parsers import DECLARED_KINDS
from .redact import scrub


INTENT = "declared verification feedback intent"
EMITTED = "declared verification feedback emitted"
_PENDING: ContextVar[list | None] = ContextVar("declared_feedback_delivery", default=None)


def _hash(value) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf8")).hexdigest()


def _valid_hash(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and set(value) <= set("0123456789abcdef")


@contextmanager
def collect():
    """Keep candidates through the one launcher response that can flush them."""
    existing = _PENDING.get()
    if existing is not None:
        yield
        return
    token = _PENDING.set([])
    try:
        yield
    finally:
        _PENDING.reset(token)


def intent(root, task, properties, text) -> str:
    """Persist a bounded hash-only feedback intent after the normal reservation."""
    selected = tuple(property for property in properties if property in DECLARED_KINDS)
    if not task or not selected or len(selected) != len(properties) or not text:
        return ""
    context = _hash(text)
    identity = _hash([task, selected, context])
    detail = {"id": identity, "checks": list(selected), "context": context}
    try:
        with ledger_write(root, timeout=.05):
            saved = Ledger.load(root)
            if saved.task != task:
                return ""
            known = [_intent(decision) for decision in saved.decisions]
            if not any(item and item["id"] == identity for item in known):
                if sum(item is not None for item in known) >= 16:
                    return ""
                saved.note(INTENT, json.dumps(detail, sort_keys=True, separators=(",", ":")))
                # The receipt's delivery marker is already committed; this note is not a second delivery.
                token = DELIVERY.set(None)
                try:
                    saved._save_locked(expected_task=task)
                finally:
                    DELIVERY.reset(token)
    except (OSError, ValueError, TypeError, Busy, Superseded):
        return ""
    return identity


def prepare(root, task, identity, properties, text) -> None:
    """Hold an emitted-context candidate only during a real host callback."""
    pending = _PENDING.get()
    observed = readiness.emission_scope()
    if (pending is None or not identity or not text or not observed or not observed.get("session")
            or len(pending) >= 16):
        return
    try:
        from .hosts.provenance import fingerprint
        runtime = fingerprint()
    except (OSError, ValueError):
        return
    pending.append({"root": root, "task": task, "id": identity, "checks": tuple(properties),
                    "text": text, "context": _hash(text), "runtime": runtime, **observed})


def _contexts(response):
    if not isinstance(response, dict):
        return []
    nodes = [response]
    if isinstance(response.get("hookSpecificOutput"), dict):
        nodes.append(response["hookSpecificOutput"])
    return [node[key] for node in nodes for key in ("additionalContext", "additional_context")
            if isinstance(node.get(key), str)]


def emitted(response) -> None:
    """Record only a supported context field that was successfully flushed."""
    if readiness.SOURCE.get() != "host":
        return
    contexts = _contexts(response)
    for candidate in _PENDING.get() or []:
        if not any(candidate["text"] in context for context in contexts):
            continue
        try:
            live = readiness.activation(candidate["host"], candidate["root"])
            if (live.get("generation") != candidate["generation"] or
                    live.get("state") in {"removed", "configuration-changed", "error"}):
                continue
            _record_emission(candidate)
        except (OSError, ValueError, TypeError, Busy, Superseded):
            continue


def _record_emission(candidate) -> None:
    detail = {key: candidate[key] for key in ("id", "host", "generation", "session", "runtime", "context", "event")}
    detail["at"] = time.time()
    with ledger_write(candidate["root"], timeout=.05):
        saved = Ledger.load(candidate["root"])
        if saved.task != candidate["task"]:
            return
        known = [_emission(decision) for decision in saved.decisions]
        if any(item and item["id"] == candidate["id"] for item in known):
            return
        if not any(item and item["id"] == candidate["id"] for item in (_intent(d) for d in saved.decisions)):
            return
        saved.note(EMITTED, json.dumps(detail, sort_keys=True, separators=(",", ":")))
        saved._save_locked(expected_task=candidate["task"])


def _intent(decision):
    if not isinstance(decision, dict) or decision.get("what") != INTENT:
        return None
    try:
        value = json.loads(decision.get("why", ""))
    except (TypeError, ValueError):
        return None
    if not isinstance(value, dict):
        return None
    checks = value.get("checks")
    if (not _valid_hash(value.get("id")) or not _valid_hash(value.get("context"))
            or not isinstance(checks, list) or not 0 < len(checks) <= len(DECLARED_KINDS)
            or any(check not in DECLARED_KINDS for check in checks)):
        return None
    return value


def _emission(decision):
    if not isinstance(decision, dict) or decision.get("what") != EMITTED:
        return None
    try:
        value = json.loads(decision.get("why", ""))
    except (TypeError, ValueError):
        return None
    required = {"id", "host", "generation", "session", "runtime", "context", "event", "at"}
    if not isinstance(value, dict) or set(value) != required or not _valid_hash(value.get("id")):
        return None
    if (not isinstance(value["host"], str) or not isinstance(value["event"], str)
            or not isinstance(value["generation"], str) or len(value["generation"]) != 32
            or set(value["generation"]) - set("0123456789abcdef")
            or any(not _valid_hash(value[key]) for key in ("session", "runtime", "context"))
            or type(value["at"]) not in (int, float) or value["at"] < 0):
        return None
    return value


def _latest(ledger, declaration):
    command = ledger.config.command_for(declaration)
    kind = DECLARED_KINDS[declaration]
    matches = [record for record in ledger.evidence
               if record.declaration == declaration and record.kind is kind
               and record.command_identity == scrub(command)]
    return max(matches, key=lambda record: record.at) if matches else None


def inspect(ledger):
    """Return bounded temporal observations; it never writes or executes."""
    intents = [item for item in (_intent(decision) for decision in ledger.decisions) if item]
    emissions = {item["id"]: item for item in (_emission(decision) for decision in ledger.decisions) if item}
    value = {"state": "unobserved", "intents": len(intents), "emitted": 0, "followups": [],
             "issues": [], "model_consumption": "unproven"}
    if not intents:
        return value
    delivered = [(item, emissions[item["id"]]) for item in intents if item["id"] in emissions]
    if not delivered:
        value["state"] = "intent"
        return value
    value["state"] = "emitted"
    value["emitted"] = len(delivered)
    by_check = {}
    for item, emission in delivered:
        for declaration in item["checks"]:
            if declaration not in by_check or emission["at"] > by_check[declaration][1]["at"]:
                by_check[declaration] = (item, emission)
    from .declared_completion import rows
    current = {row.declaration: row for row in rows(ledger)}
    for declaration, (_, emission) in by_check.items():
        state = "unobserved"
        try:
            active = readiness.activation(emission["host"], ledger.root)
            record = _latest(ledger, declaration)
            links = active.get("receipt_links", []) + active.get("owned_links", [])
            matched = record.at > emission["at"] and any(link.get("key") == readiness.receipt_key(record)
                          and link.get("task") == readiness.identity(ledger.task)
                          and link.get("session") == emission["session"]
                          and link.get("at", 0) > emission["at"] for link in links) if record else False
            if matched and declaration in current:
                state = current[declaration].state.lower()
        except (OSError, ValueError, TypeError, KeyError, AttributeError):
            value["issues"].append("Feedback follow-up observation unavailable.")
        value["followups"].append({"declaration": declaration, "state": state})
    return value


def lines(ledger) -> list[str]:
    """Informational completion text; explicitly does not assert model use."""
    value = inspect(ledger)
    if not value["intents"]:
        return []
    output = ["Feedback delivery (informational; model consumption unproven): "
              f"{value['state']}; intents {value['intents']}, native emissions {value['emitted']}"]
    output.extend(f"  later exact native receipt {row['declaration']}: {row['state']}"
                  for row in value["followups"])
    output.extend("  " + issue for issue in dict.fromkeys(value["issues"]))
    return output
