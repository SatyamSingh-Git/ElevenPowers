import pytest

from unitconv import UnitError, parse_quantity
from unitconv.mixed import format_mixed, split_quantity


def test_feet_and_inches():
    parts = split_quantity(parse_quantity('1.8 m'), ['ft', 'in'])
    assert format_mixed(parts) == '5 ft 10.866142 in'


def test_rounding_carries_into_the_larger_unit():
    parts = split_quantity(parse_quantity('1.82879 m'), ['ft', 'in'], precision=2)
    assert format_mixed(parts) == '6 ft 0 in'


def test_names():
    parts = split_quantity(parse_quantity('100 min'), ['h', 'min'])
    assert format_mixed(parts, style='name') == '1 hour 40 minutes'


@pytest.mark.parametrize('text, targets, message', [
    ('1 m', ['ft'], 'at least two units'),
    ('-1 m', ['ft', 'in'], 'zero or more'),
    ('1 K', ['degC', 'K'], "offset unit 'degC'"),
])
def test_refused(text, targets, message):
    with pytest.raises(UnitError, match=message):
        split_quantity(parse_quantity(text), targets)
