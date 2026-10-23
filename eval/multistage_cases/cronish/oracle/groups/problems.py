from cronish import validate


def test_usable_expressions():
    assert validate("*/5 9-17 * * mon-fri") == []
    assert validate("@daily") == []
    assert validate("0 0 29 2 *") == []


def test_one_problem_as_a_pair():
    assert validate("61 * * * *") == [("minute", "value 61 out of range 0-59")]
    assert validate("* * * foo *") == [("month", "unknown name 'foo'")]
    assert validate("*/0 * * * *") == [("minute", "step must be at least 1")]


def test_whole_expression_problems():
    assert validate("* * *") == [("expression", "expected 5 fields, got 3")]
    assert validate("@often") == [("expression", "unknown shortcut '@often'")]


def test_impossible_day():
    assert validate("0 0 30 2 *") == [("day", "no selected month has a day 30")]
