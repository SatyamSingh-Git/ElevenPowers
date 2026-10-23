import pytest

from warden import Evaluator, PolicySyntaxError, Request, User, explain, parse_policy


def test_explanation_names_the_unmet_env_clause():
    policy = parse_policy('role staff\nallow staff read payroll/** when env.network == "office" and user.team == "hr"\n')
    request = Request(User("erin", ("staff",), {"team": "hr"}), "read", "payroll/may", env={"network": "home"})
    assert explain(Evaluator(policy).decide(request)) == (
        "DENY erin read payroll/may: no rule matched; default is deny\n"
        '  rule 1 not applied: env.network == "office"')


def test_other_namespaces_are_still_refused():
    with pytest.raises(PolicySyntaxError) as caught:
        parse_policy('role staff\nallow staff read x when env.network == "office"\nallow staff read y when host.name == "a"\n')
    assert str(caught.value) == "line 3: unknown attribute namespace: host"
