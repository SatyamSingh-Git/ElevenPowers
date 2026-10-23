"""The policy text format.

    # comments start with a hash
    role viewer
    role editor inherits viewer
    default deny
    allow viewer read,list reports/**
    deny editor delete reports/archive/**
    allow editor write reports/* when user.dept == resource.dept
"""
from .actions import canonical_action
from .conditions import Condition
from .errors import PolicyError, PolicySyntaxError, RoleError
from .model import Policy, Rule
from .patterns import Pattern
from .roles import RoleGraph

EFFECTS = ("allow", "deny")
ROLE_SHAPE = "role <name> [inherits <parent>]"
RULE_SHAPE = "<effect> <role> <actions> <pattern> [when <condition>]"


def make_rule(number, effect, role, actions, pattern, when=None, line=None):
    if effect not in EFFECTS:
        raise PolicyError(f"unknown effect: {effect}")
    canonical = tuple(dict.fromkeys(canonical_action(action) for action in actions))
    if not canonical:
        raise PolicyError("rule has no actions")
    condition = Condition(when) if when else None
    return Rule(number, effect, role, canonical, Pattern(pattern), condition, line)


def finish(graph, rules, default):
    """Check what can only be checked once every role and rule is known."""
    if default not in EFFECTS:
        raise PolicyError(f"unknown effect: {default}")
    graph.check()
    for rule in rules:
        if rule.role not in graph:
            message = f"unknown role: {rule.role}"
            if rule.line is not None:
                raise PolicySyntaxError(rule.line, message)
            raise RoleError(f"rule {rule.number}: {message}")
    return Policy(graph, tuple(rules), default)


def _role_line(graph, words):
    if len(words) == 2:
        graph.add(words[1])
    elif len(words) == 4 and words[2] == "inherits":
        graph.add(words[1], words[3])
    else:
        raise PolicyError(f"expected: {ROLE_SHAPE}")


def _rule_line(number, text, line):
    head, _, when = text.partition(" when ")
    fields = head.split()
    if len(fields) != 4:
        raise PolicyError(f"expected: {RULE_SHAPE}")
    effect, role, actions, pattern = fields
    return make_rule(number, effect, role, actions.split(","), pattern, when.strip(), line)


def parse_policy(text):
    graph, rules, default = RoleGraph(), [], "deny"
    for line, raw in enumerate(text.splitlines(), 1):
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            continue
        words = stripped.split()
        try:
            if words[0] == "role":
                _role_line(graph, words)
            elif words[0] == "default":
                if len(words) != 2:
                    raise PolicyError("expected: default <effect>")
                default = words[1]
            else:
                rules.append(_rule_line(len(rules) + 1, stripped, line))
        except PolicyError as error:
            raise PolicySyntaxError(line, str(error)) from None
    return finish(graph, rules, default)
