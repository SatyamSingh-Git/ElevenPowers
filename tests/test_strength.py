"""Positive and adversarial controls for optional changed-code test strength."""
from pathlib import Path
import pytest


def test_observations_are_informational_and_count_all_states():
    from core.strength.model import Observation, summary
    items = [Observation(str(i), 'src/a.py', 2, 'operator', status)
             for i, status in enumerate(('detected', 'undetected', 'invalid', 'timed_out', 'error', 'not_run'))]
    value = summary(items)
    assert value['detected'] == value['undetected'] == 1
    assert value['incomplete'] == 3 and value['invalid'] == 1
    assert 'score' not in value and 'verdict' not in value


def test_observation_rejects_unknown_or_unsafe_metadata():
    from core.strength.model import Observation
    for path, status in [('../a.py', 'detected'), ('/a.py', 'detected'), ('a.py', 'pass')]:
        with pytest.raises(ValueError):
            Observation('1', path, 1, 'operator', status)
