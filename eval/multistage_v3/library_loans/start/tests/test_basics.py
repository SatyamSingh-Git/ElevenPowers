from datetime import date

import pytest

from lending.config import Settings, load_settings
from lending.errors import LendingError
from lending.model.calendar import Calendar
from lending.model.dates import parse_date
from lending.model.money import format_money, parse_money, plain_amount
from lending.storage.holidays_store import load_holidays


@pytest.mark.parametrize('text, pence', [('2', 200), ('2.5', 250), ('2.50', 250), ('£0.05', 5), (' 12.99 ', 1299)])
def test_parse_money(text, pence):
    assert parse_money(text) == pence


@pytest.mark.parametrize('text', ['', '2.505', '-1', 'two pounds', '£'])
def test_parse_money_refuses_nonsense(text):
    with pytest.raises(LendingError) as raised:
        parse_money(text)
    assert raised.value.code == 'bad_amount'


def test_money_is_shown_in_pounds():
    assert format_money(1299) == '£12.99'
    assert format_money(-50) == '-£0.50'
    assert plain_amount(5) == '0.05'


def test_bad_date():
    with pytest.raises(LendingError) as raised:
        parse_date('2 March')
    assert raised.value.message == 'not a date: 2 March'


def test_calendar_skips_closed_days():
    calendar = Calendar(closed_weekdays=('sun',), holidays={date(2026, 4, 6)})
    assert calendar.next_open_day(date(2026, 3, 7)) == date(2026, 3, 7)
    assert calendar.next_open_day(date(2026, 4, 5)) == date(2026, 4, 7)


def test_holidays_file(tmp_path):
    (tmp_path / 'holidays.txt').write_text('# Easter\n2026-04-03  # Good Friday\n\n2026-04-06\n', encoding='utf-8')
    assert load_holidays(tmp_path) == {date(2026, 4, 3), date(2026, 4, 6)}


def test_defaults_without_a_settings_file(tmp_path):
    assert load_settings(tmp_path) == Settings()


def test_settings_file_overrides(tmp_path):
    (tmp_path / 'lending.ini').write_text(
        '[lending]\nloan_days.DVD = 14\nfine_per_day.BK = 0.30\nnotice_days = 21, 7, 35\nclosed_days = Sun, mon\n',
        encoding='utf-8')
    settings = load_settings(tmp_path)
    assert settings.loan_days['DVD'] == 14
    assert settings.loan_days['BK'] == 21
    assert settings.fine_per_day['BK'] == 30
    assert settings.notice_days == (7, 21, 35)
    assert settings.closed_days == ('sun', 'mon')


@pytest.mark.parametrize('line, problem', [
    ('loan_days = 7', 'unknown option'),
    ('max_renewals.BK = 1', 'unknown option'),
    ('loan_days.CD = 7', 'unknown material CD'),
    ('max_holds = lots', "cannot read 'lots'"),
])
def test_bad_settings(tmp_path, line, problem):
    (tmp_path / 'lending.ini').write_text(f'[lending]\n{line}\n', encoding='utf-8')
    with pytest.raises(LendingError) as raised:
        load_settings(tmp_path)
    assert raised.value.code == 'bad_setting'
    assert raised.value.message.endswith(problem)
