"""Categories: the built-in list plus any the household adds in its settings."""
from .._generated import CATEGORY_GROUPS, DEFAULT_CATEGORIES
from ..errors import NotFound, ValidationError

INCOME_GROUPS = frozenset({"income"})
IGNORED_GROUPS = frozenset({"transfers"})
UNCATEGORISED = "Uncategorised"


class Catalog:
    def __init__(self, extra=None):
        self.groups = dict(DEFAULT_CATEGORIES)
        for name, group in (extra or {}).items():
            if group not in CATEGORY_GROUPS:
                raise ValidationError(f"unknown category group for {name}: {group}")
            self.groups[name] = group

    @classmethod
    def for_workspace(cls, workspace):
        return cls(workspace.settings()["extra_categories"])

    def require(self, name):
        if name not in self.groups:
            raise NotFound(f"unknown category: {name}")
        return name

    def group_of(self, name):
        return self.groups.get(name, "")

    def is_income(self, name):
        return self.group_of(name) in INCOME_GROUPS

    def is_spending(self, name):
        """Whether money in `name` is spending. Uncategorised money is, until someone files it."""
        return not name or self.group_of(name) not in INCOME_GROUPS | IGNORED_GROUPS

    def by_group(self):
        """(group, [category names]) in the generated group order."""
        return [(group, sorted(name for name, of in self.groups.items() if of == group))
                for group in CATEGORY_GROUPS]
