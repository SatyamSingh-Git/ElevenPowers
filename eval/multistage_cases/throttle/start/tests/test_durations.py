import pytest

from throttle import format_duration, parse_duration


@pytest.mark.parametrize('text, seconds', [
    ('30', 30.0), ('30s', 30.0), ('minute', 60.0), ('5m', 300.0),
    ('1.5h', 5400.0), ('250ms', 0.25), (' 2 day ', 172800.0),
])
def test_parse_duration(text, seconds):
    assert parse_duration(text) == seconds


@pytest.mark.parametrize('text, message', [
    ('', 'invalid duration: '), ('soon', 'unknown unit: soon'), ('0s', 'invalid duration: 0s'),
    ('-5s', 'invalid duration: -5s'),
])
def test_parse_duration_rejects(text, message):
    with pytest.raises(ValueError) as caught:
        parse_duration(text)
    assert str(caught.value) == message


@pytest.mark.parametrize('seconds, text', [
    (0.25, '250ms'), (1, '1s'), (1.5, '1.5s'), (60, '1m'), (90, '1m30s'), (3600, '1h'), (3725, '1h2m5s'),
])
def test_format_duration(seconds, text):
    assert format_duration(seconds) == text
