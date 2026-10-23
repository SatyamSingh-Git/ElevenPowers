"""Warnings about policies that load fine but probably do not say what was meant."""
from dataclasses import dataclass
from typing import Optional

from .actions import ANY_ACTION


@dataclass(frozen=True)
class Finding:
    code: str
    message: str
    rule: Optional[int] = None

    def __str__(self):
        return f"{self.code}: {self.message}"


def _key(rule):
    return (rule.effect, rule.role, frozenset(rule.actions), rule.pattern,
            rule.condition.text if rule.condition else None)


def _shadows(graph, deny, allow):
    """Whether `deny` refuses everything `allow` could ever grant."""
    return (deny.effect == "deny" and deny.condition is None
            and deny.role in graph.ancestors(allow.role)
            and (ANY_ACTION in deny.actions or set(allow.actions) <= set(deny.actions))
            and deny.pattern.covers(allow.pattern))


def _role_findings(policy):
    graph = policy.roles
    named = {rule.role for rule in policy.rules}
    inherited = {graph.parent_of(name) for name in graph}
    for name in graph:
        if name in named:
            continue
        parent = graph.parent_of(name)
        if parent is not None:
            yield Finding("redundant-role", f"role {name} adds nothing to {parent}")
        elif name not in inherited:
            yield Finding("unused-role", f"role {name} is never used")


def _rule_findings(policy):
    seen = {}
    for rule in policy.rules:
        key = _key(rule)
        if key in seen:
            yield Finding("duplicate-rule", f"rule {rule.number} repeats rule {seen[key]}", rule.number)
            continue
        seen[key] = rule.number
        if rule.effect != "allow":
            continue
        for other in policy.rules:
            if _shadows(policy.roles, other, rule):
                yield Finding("shadowed-rule", f"rule {rule.number} can never apply: rule {other.number} denies it",
                              rule.number)
                break


def lint(policy):
    return [*_role_findings(policy), *_rule_findings(policy)]
