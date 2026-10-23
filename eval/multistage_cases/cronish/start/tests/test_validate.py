from cronish import validate


def test_a_usable_expression_has_no_problems():
    assert validate("*/5 9-17 * * mon-fri") == []
    assert validate("@hourly") == []


def test_a_parse_error_is_reported():
    assert validate("61 * * * *") == ["minute: value 61 out of range 0-59"]


def test_only_the_first_problem_is_reported():
    assert validate("61 25 * * *") == ["minute: value 61 out of range 0-59"]


def test_a_day_no_chosen_month_has():
    assert validate("0 0 30 2 *") == ["day: no selected month has a day 30"]
    assert validate("0 0 31 apr,jun *") == ["day: no selected month has a day 31"]


def test_february_29_is_possible():
    assert validate("0 0 29 2 *") == []


def test_a_weekday_can_still_match_when_the_day_cannot():
    assert validate("0 0 30 2 mon") == []
