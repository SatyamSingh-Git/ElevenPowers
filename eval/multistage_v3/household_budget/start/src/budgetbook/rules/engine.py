"""Choosing a category for a payee from the rules file."""
from .matchers import check_pattern, matcher_for


class RuleBook:
    """Rules in file order; the first rule that matches decides the category."""

    def __init__(self, rules):
        for rule in rules:
            check_pattern(rule.match, rule.pattern)
        self.rules = list(rules)

    def first_match(self, payee, account=""):
        """The 1-based position and rule that would file `payee`, or None."""
        for position, rule in enumerate(self.rules, 1):
            if rule.applies_to(account) and matcher_for(rule.match)(rule.pattern, payee):
                return position, rule
        return None

    def category_for(self, payee, account=""):
        found = self.first_match(payee, account)
        return found[1].category if found else ""
