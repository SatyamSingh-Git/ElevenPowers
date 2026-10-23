"""Policies given as data (a dict, or a JSON file) instead of text.

    {"schema": 3,
     "default": "deny",
     "roles": {"viewer": null, "editor": "viewer"},
     "rules": [{"effect": "allow", "role": "viewer", "actions": ["read"],
                "resource": "reports/**", "when": "user.dept == resource.dept"}]}
"""
import json
from pathlib import Path

from ._generated import SCHEMA_VERSION
from .errors import PolicyError
from .parser import finish, make_rule, parse_policy
from .roles import RoleGraph

REQUIRED = ("effect", "role", "actions", "resource")


def load_dict(data):
    schema = data.get("schema", SCHEMA_VERSION)
    if schema != SCHEMA_VERSION:
        raise PolicyError(f"unsupported schema: {schema}")
    graph = RoleGraph()
    for name, parent in data.get("roles", {}).items():
        graph.add(name, parent)
    rules = []
    for number, item in enumerate(data.get("rules", []), 1):
        missing = [name for name in REQUIRED if name not in item]
        try:
            if missing:
                raise PolicyError(f"missing field: {missing[0]}")
            actions = item["actions"]
            if isinstance(actions, str):
                actions = actions.split(",")
            rules.append(make_rule(number, item["effect"], item["role"], actions,
                                   item["resource"], item.get("when")))
        except PolicyError as error:
            raise PolicyError(f"rule {number}: {error}") from None
    return finish(graph, rules, data.get("default", "deny"))


def load_file(path):
    """A `.json` file is read as data; anything else as policy text."""
    path = Path(path)
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return load_dict(json.loads(text))
    return parse_policy(text)
