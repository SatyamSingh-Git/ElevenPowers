import pytest

from throttle import ConfigError, ManualClock, dump_config, load_config

CONFIG = """
# production limits
default = 100/minute
max_keys = 50
limit login:* = 5/minute; algorithm=sliding   # brute force guard
limit upload:* = 20/hour; algorithm=bucket; burst=5
"""


def test_load_config():
    throttle = load_config(CONFIG, ManualClock())
    assert throttle.max_keys == 50
    assert throttle.policy_for('login:ann').algorithm == 'sliding'
    assert throttle.policy_for('upload:x').capacity == 5
    assert throttle.policy_for('other').limit == 100


def test_dump_round_trips():
    clock = ManualClock()
    text = dump_config(load_config(CONFIG, clock))
    assert dump_config(load_config(text, clock)) == text


@pytest.mark.parametrize('text, message', [
    ('default 100/minute', 'config line 1: expected name = value'),
    ('\nspeed = 3', 'config line 2: unknown setting: speed'),
    ('max_keys = lots', 'config line 1: max_keys must be an integer: lots'),
    ('limit a* = 5/fortnight', 'config line 1: unknown unit: fortnight'),
])
def test_config_errors(text, message):
    with pytest.raises(ConfigError) as caught:
        load_config(text, ManualClock())
    assert str(caught.value) == message
