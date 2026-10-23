from warden import Evaluator, Request, User, explain, format_summary, lint, parse_policy, summarize_file, write_log

POLICY = """\
role viewer
role editor inherits viewer
allow viewer read reports/**
deny editor delete reports/archive/**
allow editor write reports/* when user.team == resource.team
"""


def decide(name, roles, action, resource, user_attrs=None, resource_attrs=None):
    request = Request(User(name, tuple(roles), user_attrs or {}), action, resource, resource_attrs or {})
    return Evaluator(parse_policy(POLICY)).decide(request)


def test_explain_allow_and_deny():
    assert explain(decide("alice", ["viewer"], "read", "reports/q1")) == (
        "ALLOW alice read reports/q1: allowed by rule 1\n"
        "  rule 1 (line 3): allow viewer read reports/**")
    assert explain(decide("bob", ["editor"], "delete", "reports/archive/old")) == (
        "DENY bob delete reports/archive/old: denied by rule 2\n"
        "  rule 2 (line 4): deny editor delete reports/archive/**")


def test_explain_near_miss():
    decision = decide("bob", ["editor"], "write", "reports/q1", {"team": "ops"}, {"team": "hr"})
    assert explain(decision) == (
        "DENY bob write reports/q1: no rule matched; default is deny\n"
        "  rule 3 not applied: user.team == resource.team")


def test_log_and_summary(tmp_path):
    log = tmp_path / "audit.jsonl"
    write_log([decide("alice", ["viewer"], "read", "reports/q1"),
               decide("alice", ["viewer"], "write", "reports/q1")], log)
    write_log([decide("bob", ["editor"], "delete", "reports/archive/old"),
               decide("bob", ["editor"], "delete", "/reports//archive/old")], log)
    summary = summarize_file(log)
    assert (summary.total, summary.allowed, summary.denied) == (4, 1, 3)
    assert summary.users == {"alice": (1, 1), "bob": (0, 2)}
    assert dict(summary.denied_resources) == {"reports/q1": 1, "reports/archive/old": 2}
    assert format_summary(summary).splitlines()[0] == "4 decisions: 1 allowed, 3 denied"


def findings(text):
    return {(finding.code, finding.message) for finding in lint(parse_policy(text))}


def test_lint_roles():
    text = "role viewer\nrole editor inherits viewer\nrole guest\nallow viewer read **\n"
    assert findings(text) == {
        ("redundant-role", "role editor adds nothing to viewer"),
        ("unused-role", "role guest is never used"),
    }


def test_lint_rules():
    text = ("role viewer\nrole editor inherits viewer\n"
            "deny viewer * reports/**\nallow editor write reports/*.csv\n"
            "allow viewer read docs/**\nallow viewer read docs/**\n")
    assert findings(text) == {
        ("shadowed-rule", "rule 2 can never apply: rule 1 denies it"),
        ("duplicate-rule", "rule 4 repeats rule 3"),
    }
    assert findings("role viewer\nallow viewer read **\n") == set()
