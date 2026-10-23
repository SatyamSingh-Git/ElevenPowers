import pytest

from warden import Evaluator, Request, RoleError, User, load_dict, parse_policy

TEXT = """\
role viewer
role auditor
role editor inherits viewer
role lead inherits editor, auditor
allow viewer read reports/**
allow auditor list logs/**
allow editor write reports/*
"""

DATA = {
    "roles": {"viewer": None, "auditor": None, "editor": "viewer", "lead": ["editor", "auditor"]},
    "rules": [
        {"effect": "allow", "role": "viewer", "actions": ["read"], "resource": "reports/**"},
        {"effect": "allow", "role": "auditor", "actions": ["list"], "resource": "logs/**"},
        {"effect": "allow", "role": "editor", "actions": ["write"], "resource": "reports/*"},
    ],
}


def decide(policy, roles, action, resource):
    return Evaluator(policy).decide(Request(User("lee", tuple(roles)), action, resource))


@pytest.fixture(params=["text", "data"])
def policy(request):
    return parse_policy(TEXT) if request.param == "text" else load_dict(DATA)


def test_role_holds_everything_each_parent_holds(policy):
    assert decide(policy, ["lead"], "read", "reports/q1").reason == "allowed by rule 1"
    assert decide(policy, ["lead"], "list", "logs/2024").reason == "allowed by rule 2"
    assert decide(policy, ["lead"], "write", "reports/q1").reason == "allowed by rule 3"
    assert decide(policy, ["editor"], "list", "logs/2024").allowed is False
    assert decide(policy, ["auditor"], "write", "reports/q1").allowed is False


def test_cycle_through_a_second_parent_is_refused():
    with pytest.raises(RoleError) as caught:
        parse_policy("role a\nrole b inherits a, c\nrole c inherits b\n")
    assert str(caught.value).startswith("role cycle: ")
    with pytest.raises(RoleError) as caught:
        load_dict({"roles": {"a": None, "b": ["a", "c"], "c": "b"}})
    assert str(caught.value).startswith("role cycle: ")
