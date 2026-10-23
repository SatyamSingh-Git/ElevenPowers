from warden import Evaluator, Request, User, explain, lint, parse_policy

TEXT = """\
role viewer
role auditor
role editor inherits viewer
allow viewer,auditor read reports/**
allow editor write reports/*
"""


def test_explanation_shows_the_rule_as_written():
    policy = parse_policy(TEXT)
    decision = Evaluator(policy).decide(Request(User("carol", ("auditor",)), "read", "reports/q1"))
    assert explain(decision) == (
        "ALLOW carol read reports/q1: allowed by rule 1\n"
        "  rule 1 (line 4): allow viewer,auditor read reports/**")


def test_lint_counts_every_listed_role_as_used():
    assert [(finding.code, finding.message) for finding in lint(parse_policy(TEXT))] == []
    findings = lint(parse_policy("role viewer\nrole auditor\nrole guest\nallow viewer,auditor read **\n"))
    assert [(finding.code, finding.message) for finding in findings] == [("unused-role", "role guest is never used")]
