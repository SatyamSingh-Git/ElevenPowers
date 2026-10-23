import pytest

from warden import Evaluator, PolicyError, PolicySyntaxError, Request, RoleError, User, load_dict, parse_policy

TEXT = """\
role viewer
role editor inherits viewer
role admin inherits editor
allow viewer read,list reports/**
deny editor delete reports/archive/**
allow editor write,delete reports/*
allow admin * **
allow editor share reports/* when user.team == resource.team
"""

DATA = {
    "schema": 3,
    "roles": {"viewer": None, "editor": "viewer", "admin": "editor"},
    "rules": [
        {"effect": "allow", "role": "viewer", "actions": ["read", "list"], "resource": "reports/**"},
        {"effect": "deny", "role": "editor", "actions": ["delete"], "resource": "reports/archive/**"},
        {"effect": "allow", "role": "editor", "actions": ["write", "delete"], "resource": "reports/*"},
        {"effect": "allow", "role": "admin", "actions": ["*"], "resource": "**"},
        {"effect": "allow", "role": "editor", "actions": ["share"], "resource": "reports/*",
         "when": "user.team == resource.team"},
    ],
}


def decide(policy, roles, action, resource, user_attrs=None, resource_attrs=None):
    user = User("alice", tuple(roles), user_attrs or {})
    return Evaluator(policy).decide(Request(user, action, resource, resource_attrs or {}))


@pytest.fixture(params=["text", "data"])
def policy(request):
    return parse_policy(TEXT) if request.param == "text" else load_dict(DATA)


def test_inherited_allow_and_alias(policy):
    decision = decide(policy, ["editor"], "view", "reports/2024/q1")
    assert decision.allowed is True
    assert decision.reason == "allowed by rule 1"
    assert decision.rule.number == 1


def test_deny_overrides_allow(policy):
    decision = decide(policy, ["admin"], "delete", "reports/archive/2019")
    assert decision.allowed is False
    assert decision.reason == "denied by rule 2"
    assert decide(policy, ["editor"], "rm", "reports/q1").reason == "allowed by rule 3"


def test_single_segment_wildcard_and_default(policy):
    decision = decide(policy, ["editor"], "write", "reports/2024/q1")
    assert decision.allowed is False
    assert decision.rule is None
    assert decision.reason == "no rule matched; default is deny"
    assert decide(policy, ["admin"], "write", "/anything//at/all/").reason == "allowed by rule 4"


def test_undefined_user_roles_are_ignored(policy):
    assert decide(policy, ["intern"], "read", "reports/q1").reason == "no rule matched; default is deny"


def test_condition_and_near_miss(policy):
    granted = decide(policy, ["editor"], "share", "reports/q1", {"team": "ops"}, {"team": "ops"})
    assert granted.allowed and granted.reason == "allowed by rule 5"
    refused = decide(policy, ["editor"], "share", "reports/q1", {"team": "ops"}, {"team": "hr"})
    assert refused.allowed is False
    assert [rule.number for rule in refused.near_misses] == [5]
    assert decide(policy, ["editor"], "share", "reports/q1", {}, {"team": "hr"}).allowed is False


def test_default_allow():
    policy = parse_policy("role viewer\ndefault allow\ndeny viewer write **\n")
    assert decide(policy, ["viewer"], "read", "x").reason == "no rule matched; default is allow"
    assert decide(policy, ["viewer"], "read", "x").allowed is True
    assert decide(policy, ["viewer"], "write", "x").allowed is False


def test_text_errors():
    with pytest.raises(PolicySyntaxError) as caught:
        parse_policy("role viewer\nallow ghost read x\n")
    assert str(caught.value) == "line 2: unknown role: ghost"
    with pytest.raises(PolicySyntaxError) as caught:
        parse_policy("role viewer\n\nallow viewer fly x\n")
    assert str(caught.value) == "line 3: unknown action: fly"
    with pytest.raises(RoleError) as caught:
        parse_policy("role a inherits b\nrole b inherits a\n")
    assert str(caught.value) == "role cycle: a -> b -> a"


def test_data_errors():
    with pytest.raises(PolicyError) as caught:
        load_dict({"roles": {"viewer": None},
                   "rules": [{"effect": "allow", "role": "ghost", "actions": ["read"], "resource": "x"}]})
    assert str(caught.value) == "rule 1: unknown role: ghost"
    with pytest.raises(PolicyError) as caught:
        load_dict({"schema": 2})
    assert str(caught.value) == "unsupported schema: 2"
