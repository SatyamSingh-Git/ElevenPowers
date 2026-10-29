import pytest

from budgetbook.errors import ValidationError
from budgetbook.model.records import Rule
from budgetbook.rules.engine import RuleBook
from budgetbook.rules.matchers import check_pattern, matcher_for


@pytest.mark.parametrize("kind, pattern, payee, expected", [
    ("contains", "tesco", "CARD PAYMENT TESCO STORES", True),
    ("contains", "TES", "TESCO STORES", True),
    ("contains", "ASDA", "TESCO STORES", False),
    ("prefix", "tesco", "TESCO STORES", True),
    ("prefix", "STORES", "TESCO STORES", False),
    ("exact", "tesco stores", "TESCO STORES", True),
    ("exact", "TESCO", "TESCO STORES", False),
    ("regex", r"^shell\b", "SHELL 4021", True),
    ("regex", r"^shell\b", "SHELLFISH BAR", False),
])
def test_matchers(kind, pattern, payee, expected):
    assert matcher_for(kind)(pattern, payee) is expected


def test_first_matching_rule_wins():
    book = RuleBook([
        Rule("contains", "TESCO PETROL", "Fuel"),
        Rule("contains", "TESCO", "Groceries"),
    ])
    assert book.category_for("TESCO PETROL 22") == "Fuel"
    assert book.category_for("TESCO STORES") == "Groceries"
    assert book.category_for("ASDA") == ""


def test_rule_limited_to_an_account():
    book = RuleBook([Rule("contains", "AMAZON", "Subscriptions", account="Card"),
                     Rule("contains", "AMAZON", "Gifts")])
    assert book.category_for("AMAZON PRIME", "Card") == "Subscriptions"
    assert book.category_for("AMAZON PRIME", "Current") == "Gifts"
    assert book.first_match("AMAZON PRIME", "Current")[0] == 2


def test_unknown_match_kind():
    with pytest.raises(ValidationError, match="unknown match kind: fuzzy"):
        RuleBook([Rule("fuzzy", "X", "Gifts")])


def test_bad_regex_is_refused():
    with pytest.raises(ValidationError, match="invalid regular expression"):
        check_pattern("regex", "(")
