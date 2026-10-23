import pytest

from warden import Evaluator, PolicySyntaxError, Request, User, explain, parse_policy

POLICY = 'role staff\nallow staff read payroll/** when env.network == "office" and user.team == "hr"\n'


def explain_for(team, network):
    request = Request(User("erin", ("staff",), {"team": team}), "read", "payroll/may", env={"network": network})
    return explain(Evaluator(parse_policy(POLICY)).decide(request))


def test_explanation_names_the_unmet_env_clause():
    assert explain_for("hr", "home") == (
        "DENY erin read payroll/may: no rule matched; default is deny\n"
        '  rule 1 not applied: env.network == "office"')


def test_env_clause_that_holds_is_not_listed():
    assert explain_for("ops", "office") == (
        "DENY erin read payroll/may: no rule matched; default is deny\n"
        '  rule 1 not applied: user.team == "hr"')


def test_other_namespaces_are_still_refused():
    with pytest.raises(PolicySyntaxError) as caught:
        parse_policy('role staff\nallow staff read x when env.network == "office"\nallow staff read y when host.name == "a"\n')
    assert str(caught.value) == "line 3: unknown attribute namespace: host"
