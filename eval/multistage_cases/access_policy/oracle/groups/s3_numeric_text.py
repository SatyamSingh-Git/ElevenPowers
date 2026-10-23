from warden import Evaluator, Request, User, explain, parse_policy

POLICY = """\
role staff
allow staff read payroll/** when user.clearance >= 9
allow staff read names/* when user.name < "m"
"""


def decide(user_attrs, resource="payroll/may"):
    return Evaluator(parse_policy(POLICY)).decide(Request(User("alice", ("staff",), user_attrs), "read", resource))


def test_text_still_compares_as_text():
    assert decide({"name": "alice"}, "names/list").allowed is True
    assert decide({"name": "zed"}, "names/list").allowed is False


def test_explanations_follow_numeric_comparison():
    assert explain(decide({"clearance": 10})) == (
        "ALLOW alice read payroll/may: allowed by rule 1\n"
        "  rule 1 (line 2): allow staff read payroll/** when user.clearance >= 9")
    assert explain(decide({"clearance": 2})) == (
        "DENY alice read payroll/may: no rule matched; default is deny\n"
        "  rule 1 not applied: user.clearance >= 9")
