from warden import Evaluator, Request, User, parse_policy

POLICY = """\
role staff
allow staff read payroll/** when env.network == "office"
allow staff write payroll/* when user.team == "finance" and env.network == "office"
"""


def decide(action, user_attrs=None, **kwargs):
    request = Request(User("erin", ("staff",), user_attrs or {}), action, "payroll/may", **kwargs)
    return Evaluator(parse_policy(POLICY)).decide(request)


def test_env_values_decide():
    assert decide("read", env={"network": "office"}).reason == "allowed by rule 1"
    assert decide("read", env={"network": "home"}).allowed is False


def test_missing_env_value_means_the_rule_does_not_apply():
    decision = decide("read")
    assert decision.allowed is False
    assert decision.reason == "no rule matched; default is deny"
    assert [rule.number for rule in decision.near_misses] == [1]


def test_env_with_user_attributes():
    assert decide("write", {"team": "finance"}, env={"network": "office"}).reason == "allowed by rule 2"
    assert decide("write", {"team": "sales"}, env={"network": "office"}).allowed is False
    assert decide("write", {"team": "finance"}, env={"network": "cafe"}).allowed is False
