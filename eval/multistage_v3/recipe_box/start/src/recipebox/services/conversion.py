"""Converting an ingredient between units, across mass and volume when its density is known."""
from fractions import Fraction

from .. import _generated
from ..core import units
from ..core.quantity import Quantity
from ..errors import UnitError


def density(name):
    """Grams per millilitre of `name` as an exact Fraction, or None when it is not known."""
    value = _generated.DENSITY_G_PER_ML.get(name)
    return None if value is None else Fraction(str(value))


def convert_ingredient(name, quantity, target):
    """`quantity` of `name` in the unit `target`.

    Mass and volume convert into each other through the ingredient's density;
    counts convert to mass or volume through the weight of one item.
    """
    source, goal = units.unit(quantity.unit), units.unit(target)
    if units.convertible(source.symbol, goal.symbol):
        return quantity.to(goal.symbol)
    grams = _to_grams(name, quantity, source)
    if goal.dimension == units.MASS:
        return Quantity(grams / goal.factor, goal.symbol)
    if goal.dimension == units.VOLUME:
        per_ml = density(name)
        if per_ml is None:
            raise UnitError(f"the density of {name} is not known")
        return Quantity(grams / per_ml / goal.factor, goal.symbol)
    each = _generated.GRAMS_EACH.get(name)
    if each is None or goal.symbol != "":
        raise UnitError(f"cannot convert {source.symbol or 'each'} to {goal.symbol or 'each'}")
    return Quantity(grams / each, "")


def _to_grams(name, quantity, source):
    if source.dimension == units.MASS:
        return quantity.amount * source.factor
    if source.dimension == units.VOLUME:
        per_ml = density(name)
        if per_ml is None:
            raise UnitError(f"the density of {name} is not known")
        return quantity.amount * source.factor * per_ml
    each = _generated.GRAMS_EACH.get(name)
    if each is None or source.symbol != "":
        raise UnitError(f"the weight of one {name} is not known")
    return quantity.amount * each
