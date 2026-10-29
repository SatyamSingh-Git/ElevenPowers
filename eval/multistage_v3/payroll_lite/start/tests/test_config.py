from datetime import date
from decimal import Decimal

import pytest

from payroll.config import load_settings
from payroll.errors import PayrollError


def test_defaults_apply_without_a_settings_file(tmp_path):
    settings = load_settings(tmp_path)
    assert settings.company_name == "Example Co"
    assert settings.pay_frequency == "weekly"
    assert settings.first_period_start == date(2026, 1, 5)
    assert settings.daily_threshold == Decimal("8")
    assert settings.overtime_multiplier == Decimal("1.5")
    assert settings.max_hours_per_day == Decimal("24")


def test_file_overrides_defaults(tmp_path):
    (tmp_path / "payroll.ini").write_text("[overtime]\ndaily_threshold = 7.5\n", encoding="utf-8")
    assert load_settings(tmp_path).daily_threshold == Decimal("7.5")


@pytest.mark.parametrize("text, message", [
    ("[overtime]\nmultiplier = 0.5\n", "bad setting overtime.multiplier: 0.5"),
    ("[company]\npay_delay_days = soon\n", "bad setting company.pay_delay_days: soon"),
    ("[company]\nfirst_period_start = 5/1/2026\n", "bad setting company.first_period_start: 5/1/2026"),
    ("[overtime]\nweekend_multiplier = 2\n", "unknown setting overtime.weekend_multiplier"),
    ("[bonus]\nrate = 1\n", r"unknown setting section \[bonus\]"),
    ("[company]\npay_frequency = daily\n", "unknown pay frequency daily"),
])
def test_bad_settings_are_reported(tmp_path, text, message):
    (tmp_path / "payroll.ini").write_text(text, encoding="utf-8")
    with pytest.raises(PayrollError, match=message):
        load_settings(tmp_path)
