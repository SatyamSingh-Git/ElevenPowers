import json

import pytest

from warden import (Evaluator, PolicyError, PolicySyntaxError, Request, RoleError, User, load_dict,
                    load_file, parse_policy)

POLICY = """\
# reports
role viewer
role editor inherits viewer
role admin inherits editor

allow viewer read,list reports/**
deny editor delete reports/archive/**
allow editor write,delete reports/*
allow admin * **
allow editor share reports/* when user.dept == resource.dept
"""

AS_DATA = {
    "schema": 3,
    "roles": {"viewer": None, "editor": "viewer", "admin": "editor"},
    "rules": [
        {"effect": "allow", "role": "viewer", "actions": ["read", "list"], "resource": "reports/**"},
        {"effect": "deny", "role": "editor", "actions": "delete", "resource": "reports/archive/**"},
        {"effect": "allow", "role": "editor", "actions": ["write", "delete"], "resource": "reports/*"},
        {"effect": "allow", "role": "admin", "actions": ["*"], "resource": "**"},
        {"effect": "allow", "role": "editor", "actions": ["share"], "resource": "reports/*",
         "when": "user.dept == resource.dept"},
    ],
}


def decide(policy, roles, action, resource, user_attrs=None, resource_attrs=None):
    user = User("alice", tuple(roles), user_attrs or {})
    return Evaluator(policy).decide(Request(user, action, resource, resource_attrs or {}))


@pytest.fixture(params=["text", "data"])
def policy(request):
    return parse_policy(POLICY) if request.param == "text" else load_dict(AS_DATA)


def test_inherited_allow(policy):
    decision = decide(policy, ["editor"], "view", "reports/2024/q1")
    assert decision.allowed and decision.reason == "allowed by rule 1"
    assert decision.roles == {"editor", "viewer"}


def test_deny_beats_allow(policy):
    decision = decide(policy, ["admin"], "rm", "reports/archive/2019")
    assert not decision.allowed
    assert decision.reason == "denied by rule 2"


def test_default(policy):
    decision = decide(policy, ["intern"], "read", "reports/q1")
    assert not decision.allowed
    assert decision.reason == "no rule matched; default is deny"
    assert decision.rule is None


def test_condition_and_near_miss(policy):
    assert decide(policy, ["editor"], "share", "reports/q1", {"dept": "ops"}, {"dept": "ops"}).allowed
    refused = decide(policy, ["editor"], "share", "reports/q1", {"dept": "ops"}, {"dept": "hr"})
    assert not refused.allowed
    assert [rule.number for rule in refused.near_misses] == [5]


def test_default_allow():
    policy = parse_policy("role viewer\ndefault allow\ndeny viewer write **\n")
    assert decide(policy, ["viewer"], "read", "x").reason == "no rule matched; default is allow"
    assert not decide(policy, ["viewer"], "write", "x").allowed


def test_allows_shortcut():
    evaluator = Evaluator(parse_policy(POLICY))
    assert evaluator.allows(User("bob", ("editor",), {"dept": "ops"}), "share", "reports/q1", dept="ops")


@pytest.mark.parametrize("text, message", [
    ("role viewer\nallow ghost read x\n", "line 2: unknown role: ghost"),
    ("role viewer\nallow viewer fly x\n", "line 2: unknown action: fly"),
    ("role viewer\npermit viewer read x\n", "line 2: unknown effect: permit"),
    ("role viewer\nallow viewer read\n", "line 2: expected: "),
    ("role viewer\nrole viewer\n", "line 2: role viewer is defined twice"),
    ("role viewer is cool\n", "line 1: expected: role <name> [inherits <parent>]"),
    ("role viewer\nallow viewer read x when user.dept\n", "line 2: bad condition"),
])
def test_syntax_errors(text, message):
    with pytest.raises(PolicySyntaxError) as caught:
        parse_policy(text)
    assert str(caught.value).startswith(message)


def test_role_cycle():
    with pytest.raises(RoleError, match="role cycle: a -> b -> a"):
        parse_policy("role a inherits b\nrole b inherits a\n")


def test_data_errors():
    with pytest.raises(PolicyError, match="unsupported schema: 2"):
        load_dict({"schema": 2})
    with pytest.raises(PolicyError, match="rule 1: missing field: resource"):
        load_dict({"roles": {"viewer": None}, "rules": [{"effect": "allow", "role": "viewer", "actions": "read"}]})
    with pytest.raises(PolicyError, match="rule 1: unknown role: ghost"):
        load_dict({"rules": [{"effect": "allow", "role": "ghost", "actions": "read", "resource": "x"}]})


def test_load_file(tmp_path):
    (tmp_path / "p.policy").write_text(POLICY, encoding="utf-8")
    (tmp_path / "p.json").write_text(json.dumps(AS_DATA), encoding="utf-8")
    for name in ("p.policy", "p.json"):
        assert decide(load_file(tmp_path / name), ["viewer"], "list", "reports").allowed
