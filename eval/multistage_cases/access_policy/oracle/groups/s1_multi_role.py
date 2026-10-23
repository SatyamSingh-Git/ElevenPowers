import pytest

from warden import Evaluator, PolicySyntaxError, Request, User, parse_policy

TEXT = """\
role viewer
role auditor
role editor inherits viewer
role guest
allow viewer,auditor read reports/**
deny auditor,guest write **
allow editor,guest write reports/*
"""


def decide(roles, action, resource):
    return Evaluator(parse_policy(TEXT)).decide(Request(User("alice", tuple(roles)), action, resource))


def test_any_listed_role_is_enough():
    for roles in (["viewer"], ["auditor"], ["editor"]):
        decision = decide(roles, "read", "reports/2024/q1")
        assert decision.allowed is True
        assert decision.reason == "allowed by rule 1"
    assert decide(["guest"], "read", "reports/q1").allowed is False


def test_several_roles_on_deny():
    assert decide(["editor"], "write", "reports/q1").reason == "allowed by rule 3"
    assert decide(["guest"], "write", "reports/q1").reason == "denied by rule 2"
    assert decide(["editor", "auditor"], "write", "reports/q1").reason == "denied by rule 2"


def test_every_listed_role_must_be_defined():
    with pytest.raises(PolicySyntaxError) as caught:
        parse_policy("role viewer\nallow viewer,ghost read x\n")
    assert str(caught.value) == "line 2: unknown role: ghost"
