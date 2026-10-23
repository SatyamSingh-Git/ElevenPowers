import pytest

from unitconv import convert, parse_quantity, parse_unit
from unitconv.cli import main


def message(call, *args):
    with pytest.raises(ValueError) as caught:
        call(*args)
    return str(caught.value)


def test_case_only_matches_are_refused_with_a_hint():
    assert message(parse_quantity, '3 MM') == "unknown unit: 'MM' (did you mean 'Mm' or 'mm'?)"
    assert message(parse_unit, 'KM') == "unknown unit: 'KM' (did you mean 'km'?)"
    assert message(convert, parse_quantity('1 bar'), 'PA') == "unknown unit: 'PA' (did you mean 'Pa'?)"
    assert message(parse_quantity, '20 DEGC') == "unknown unit: 'DEGC' (did you mean 'degC'?)"


def test_unknown_units_without_a_near_match_are_unchanged():
    assert message(parse_quantity, '2 xyz') == "unknown unit: 'xyz'"


def test_command_line_reports_the_hint(capsys):
    assert main(['convert', '3 MM', 'km']) == 1
    captured = capsys.readouterr()
    assert (captured.out, captured.err) == ('', "error: unknown unit: 'MM' (did you mean 'Mm' or 'mm'?)\n")
