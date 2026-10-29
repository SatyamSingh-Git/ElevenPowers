"""Errors recipebox reports to the user.

The command line prints the message of any of these after `error: ` and exits
with status 1; anything else is a bug.
"""


class RecipeBoxError(Exception):
    """Base class for every error meant for the user."""


class UnitError(RecipeBoxError):
    """A unit that is not known, or a conversion between unrelated units."""


class AmountError(RecipeBoxError):
    """An amount that cannot be read."""


class RecipeError(RecipeBoxError):
    """A recipe that is malformed or breaks a limit."""


class RecipeNotFound(RecipeBoxError):
    def __init__(self, rid):
        super().__init__(f"no recipe with id {rid}")
        self.rid = rid


class DuplicateRecipe(RecipeBoxError):
    def __init__(self, rid):
        super().__init__(f"recipe {rid} already exists")
        self.rid = rid


class PlanError(RecipeBoxError):
    """A meal plan file that cannot be read."""


class PantryError(RecipeBoxError):
    """A pantry file or pantry change that cannot be applied."""


class BundleError(RecipeBoxError):
    """An export bundle that cannot be imported."""
