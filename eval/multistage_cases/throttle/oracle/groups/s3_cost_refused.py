import pytest

from throttle import ManualClock, Throttle


@pytest.mark.parametrize('policy, cost, limit', [
    ('10/minute', 11, 10),
    ('10/minute; algorithm=sliding', 15, 10),
    ('5/second; algorithm=bucket; burst=8', 9, 8),
])
def test_hit_costing_more_than_the_limit_is_refused(policy, cost, limit):
    throttle = Throttle(ManualClock(), default=policy)
    with pytest.raises(ValueError) as caught:
        throttle.hit('k', cost)
    assert str(caught.value) == f'cost must be between 1 and {limit}: {cost}'


@pytest.mark.parametrize('policy, limit', [
    ('10/minute', 10),
    ('10/minute; algorithm=sliding', 10),
    ('5/second; algorithm=bucket; burst=8', 8),
])
def test_cost_equal_to_the_limit_is_still_allowed(policy, limit):
    throttle = Throttle(ManualClock(), default=policy)
    with pytest.raises(ValueError):
        throttle.hit('k', limit + 1)
    assert throttle.hit('k', limit).allowed
