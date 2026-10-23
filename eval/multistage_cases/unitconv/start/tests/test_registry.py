import pytest

from unitconv import REGISTRY, UnknownUnitError, parse_unit
from unitconv.dimensions import Dimension


def test_base_and_prefixed_units():
    assert REGISTRY.lookup('ft').factor == pytest.approx(0.3048)
    kilometre = REGISTRY.lookup('km')
    assert (kilometre.name, kilometre.plural, kilometre.factor) == ('kilometre', 'kilometres', 1000)
    assert REGISTRY.lookup('kWh').factor == pytest.approx(3.6e6)


def test_exact_spelling_wins_over_prefix():
    assert REGISTRY.lookup('min').name == 'minute'
    assert REGISTRY.lookup('ha').name == 'hectare'


def test_lookup_ignores_case():
    assert REGISTRY.lookup('PA').name == 'pascal'
    assert REGISTRY.lookup('btu').name == 'British thermal unit'


def test_unknown_unit():
    with pytest.raises(UnknownUnitError, match="unknown unit: 'furlong'"):
        REGISTRY.lookup('furlong')


def test_units_by_dimension():
    symbols = [unit.symbol for unit in REGISTRY.units(Dimension.named('volume'))]
    assert symbols == ['L', 'gal', 'qt']


def test_compound_dimension_and_symbol():
    unit = parse_unit('kg*m/s^2')
    assert unit.dimension.name == 'force'
    assert unit.symbol == 'kg*m/s^2'
    assert unit.factor == pytest.approx(1)
    assert parse_unit('W/m^2/K').dimension.formula == 'M/T^3/K'
    assert parse_unit('1/s').dimension.name == 'frequency'


def test_compound_names():
    assert parse_unit('km/h').name(plural=True) == 'kilometres per hour'
    assert parse_unit('m/s^2').name() == 'metre per second squared'
