"""Explaining decisions to people, and logging them for later."""
import json

from .patterns import normalize

VERDICTS = {True: "ALLOW", False: "DENY"}


def describe(rule):
    """A rule as it would be written in policy text."""
    text = f"{rule.effect} {rule.role} {','.join(rule.actions)} {rule.pattern.text}"
    if rule.condition:
        text += f" when {rule.condition.text}"
    return text


def explain(decision):
    request = decision.request
    lines = [f"{VERDICTS[decision.allowed]} {request.user.name} {request.action} "
             f"{request.resource}: {decision.reason}"]
    rule = decision.rule
    if rule is not None:
        where = f" (line {rule.line})" if rule.line is not None else ""
        lines.append(f"  rule {rule.number}{where}: {describe(rule)}")
    for skipped in decision.near_misses:
        unmet = skipped.condition.failing(request.user.attrs, request.resource_attrs)
        lines.append(f"  rule {skipped.number} not applied: {' and '.join(unmet)}")
    return "\n".join(lines)


def record(decision):
    request = decision.request
    return {
        "user": request.user.name,
        "action": request.action,
        "resource": normalize(request.resource),
        "allowed": decision.allowed,
        "rule": decision.rule.number if decision.rule else None,
        "reason": decision.reason,
    }


def write_log(decisions, path):
    """Append one JSON line per decision."""
    with open(path, "a", encoding="utf-8", newline="\n") as log:
        for decision in decisions:
            log.write(json.dumps(record(decision), sort_keys=True) + "\n")


def read_log(path):
    with open(path, encoding="utf-8") as log:
        return [json.loads(line) for line in log if line.strip()]
