"""Ingredient lines such as `1 1/2 cup flour, sifted`, and canonical ingredient names.

Two lines name the same ingredient when their canonical names match, which is
what lets a shopping list add up `2 eggs` and `1 egg`.
"""
from dataclasses import dataclass

from ..errors import RecipeError
from . import units
from .quantity import Quantity, display_quantity, format_amount, is_amount, parse_amount

# Words whose plural is not made by adding s or es.
IRREGULAR = {
    "berries": "berry",
    "cherries": "cherry",
    "halves": "half",
    "leaves": "leaf",
    "loaves": "loaf",
}

# Words that end in s but are not plurals, or are only ever used as plurals.
UNCHANGED = frozenset({
    "asparagus", "chickpeas", "couscous", "grits", "hummus", "lentils", "molasses", "oats", "peas",
})

# Other names for the same ingredient, after singularising.
SYNONYMS = {
    "all-purpose flour": "flour",
    "plain flour": "flour",
    "caster sugar": "sugar",
    "granulated sugar": "sugar",
    "whole milk": "milk",
    "salted butter": "butter",
    "unsalted butter": "butter",
    "cheddar cheese": "cheddar",
    "parmesan cheese": "parmesan",
    "extra virgin olive oil": "olive oil",
    "spring onion": "green onion",
    "scallion": "green onion",
    "elbow macaroni": "macaroni",
    "chicken breast fillet": "chicken breast",
}


def _singular(word):
    if word in UNCHANGED:
        return word
    if word in IRREGULAR:
        return IRREGULAR[word]
    if word.endswith("oes"):
        return word[:-2]
    if word.endswith("ies") and len(word) > 4:
        return word[:-3] + "y"
    if word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def canonical_name(text):
    """`Cherry Tomatoes` -> `cherry tomato`; `plain flour` -> `flour`."""
    words = text.lower().split()
    if not words:
        return ""
    words[-1] = _singular(words[-1])
    name = " ".join(words)
    return SYNONYMS.get(name, name)


@dataclass(frozen=True)
class Ingredient:
    name: str
    quantity: Quantity | None = None
    note: str = ""


def parse_ingredient(line):
    """Read `<amount> [<unit>] <name>[, <note>]`; the amount and unit may be left out."""
    body, _, note = line.strip().removeprefix("- ").partition(",")
    tokens = body.split()
    amount_tokens = []
    while tokens and is_amount(tokens[0]) and len(amount_tokens) < 2:
        amount_tokens.append(tokens.pop(0))
    quantity = None
    if amount_tokens:
        symbol = ""
        # `2 cans` with nothing after it is two of something called cans, not a unit.
        if len(tokens) > 1 and units.lookup(tokens[0]) is not None:
            symbol = units.lookup(tokens.pop(0)).symbol
        quantity = Quantity(parse_amount(" ".join(amount_tokens)), symbol)
    name = canonical_name(" ".join(tokens))
    if not name:
        raise RecipeError(f"ingredient has no name: {line.strip()}")
    return Ingredient(name, quantity, note.strip())


def format_ingredient(ingredient):
    """The exact line `parse_ingredient` reads back to the same ingredient."""
    parts = []
    if ingredient.quantity is not None:
        parts.append(format_amount(ingredient.quantity.amount))
        if ingredient.quantity.unit:
            parts.append(ingredient.quantity.unit)
    parts.append(ingredient.name)
    text = " ".join(parts)
    return f"{text}, {ingredient.note}" if ingredient.note else text


def describe_ingredient(ingredient):
    """The line a cook reads, with the amount rounded for measuring."""
    text = ingredient.name
    if ingredient.quantity is not None:
        text = f"{display_quantity(ingredient.quantity)} {ingredient.name}"
    return f"{text}, {ingredient.note}" if ingredient.note else text
