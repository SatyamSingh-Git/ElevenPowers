from decimal import Decimal

import pytest

from helpers import entry
from payroll.errors import PayrollError
from payroll.model.employee import Allowance, Deduction
from payroll.rules.allowances import allowance_lines
from payroll.rules.deductions import deduction_lines, parse_params
from payroll.rules.overtime import Hours, split_hours
from payroll.rules.tax import annual_tax, period_tax


def test_hours_beyond_the_daily_threshold_are_overtime(settings):
    hours = split_hours([entry("E001", "2026-01-05", "10"), entry("E001", "2026-01-06", "6")], settings)
    assert (hours.ordinary, hours.overtime, hours.shifts) == (Decimal("14"), Decimal("2"), 2)


def test_rows_on_the_same_day_are_added_before_the_threshold(settings):
    hours = split_hours([entry("E001", "2026-01-05", "5"), entry("E001", "2026-01-05", "5")], settings)
    assert (hours.ordinary, hours.overtime, hours.shifts) == (Decimal("8"), Decimal("2"), 1)


def test_public_holiday_hours_are_never_ordinary_or_overtime(settings):
    hours = split_hours([entry("E001", "2026-01-16", "10")], settings)
    assert (hours.ordinary, hours.overtime, hours.holiday) == (0, 0, Decimal("10"))


def test_sick_hours_are_kept_apart(settings):
    hours = split_hours([entry("E001", "2026-01-05", "8"), entry("E001", "2026-01-05", "4", "sick")], settings)
    assert (hours.ordinary, hours.overtime, hours.sick) == (Decimal("8"), 0, Decimal("4"))


def test_tax_bands():
    assert annual_tax(Decimal("12000")) == 0
    assert annual_tax(Decimal("45000")) == Decimal("4950")
    assert annual_tax(Decimal("52650")) == Decimal("7245")


def test_period_tax_spreads_the_annual_tax():
    assert period_tax(Decimal("1012.50"), 52) == Decimal("139.33")
    assert period_tax(Decimal("0"), 52) == 0


def test_deductions_by_kind():
    deductions = [
        Deduction("percent", "Pension", {"rate": Decimal("5")}),
        Deduction("fixed", "Union", {"amount": Decimal("12.00")}),
    ]
    lines = deduction_lines(deductions, Decimal("1000.00"))
    assert [(line.label, line.amount) for line in lines] == [("Pension", Decimal("50.00")), ("Union", Decimal("12.00"))]


def test_deduction_params_are_checked():
    with pytest.raises(PayrollError, match="a percent deduction needs rate"):
        parse_params("percent", {"amount": "5"})
    with pytest.raises(PayrollError, match="unknown deduction kind levy"):
        parse_params("levy", {})


def test_per_shift_allowance_counts_shifts():
    allowances = [Allowance("per_shift", "Meal", Decimal("8.00")), Allowance("fixed", "Phone", Decimal("10.00"))]
    lines = allowance_lines(allowances, Hours(ordinary=Decimal("24"), shifts=3))
    assert [line.amount for line in lines] == [Decimal("24.00"), Decimal("10.00")]
    assert allowance_lines(allowances[:1], Hours()) == []
