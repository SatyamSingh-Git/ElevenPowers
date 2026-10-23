import json

from warden import Evaluator, Request, User, explain, format_summary, parse_policy, read_log, summarize_file, write_log

POLICY = """\
role viewer
role editor inherits viewer
allow viewer read reports/**
deny editor delete reports/archive/**
allow editor write reports/* when user.dept == resource.dept
"""


def decide(name, roles, action, resource, user_attrs=None, resource_attrs=None):
    request = Request(User(name, tuple(roles), user_attrs or {}), action, resource, resource_attrs or {})
    return Evaluator(parse_policy(POLICY)).decide(request)


def test_explain_allow():
    assert explain(decide("alice", ["viewer"], "read", "reports/q1")) == (
        "ALLOW alice read reports/q1: allowed by rule 1\n"
        "  rule 1 (line 3): allow viewer read reports/**")


def test_explain_default_with_near_miss():
    decision = decide("bob", ["editor"], "write", "reports/q1", {"dept": "ops"}, {"dept": "hr"})
    assert explain(decision) == (
        "DENY bob write reports/q1: no rule matched; default is deny\n"
        "  rule 3 not applied: user.dept == resource.dept")


def test_log_round_trip(tmp_path):
    log = tmp_path / "audit.jsonl"
    write_log([decide("alice", ["viewer"], "read", "/reports//q1")], log)
    write_log([decide("bob", ["editor"], "delete", "reports/archive/old")], log)
    records = read_log(log)
    assert records[0] == {"action": "read", "allowed": True, "reason": "allowed by rule 1",
                          "resource": "reports/q1", "rule": 1, "user": "alice"}
    assert records[1]["rule"] == 2 and records[1]["allowed"] is False
    assert list(json.loads(log.read_text(encoding="utf-8").splitlines()[0])) == sorted(records[0])


def test_summary(tmp_path):
    log = tmp_path / "audit.jsonl"
    write_log([
        decide("alice", ["viewer"], "read", "reports/q1"),
        decide("alice", ["viewer"], "write", "reports/q1"),
        decide("bob", ["editor"], "delete", "reports/archive/old"),
        decide("bob", ["editor"], "delete", "reports/archive/old"),
    ], log)
    summary = summarize_file(log)
    assert (summary.total, summary.allowed, summary.denied) == (4, 1, 3)
    assert summary.users == {"alice": (1, 1), "bob": (0, 2)}
    assert format_summary(summary) == (
        "4 decisions: 1 allowed, 3 denied\n"
        "by user:\n"
        "  alice  1 allowed  1 denied\n"
        "  bob    0 allowed  2 denied\n"
        "most denied:\n"
        "  reports/archive/old  2\n"
        "  reports/q1  1")
