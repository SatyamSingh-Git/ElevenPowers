"""A prep list for a batch-cooking session: the chopping, grating and so on that a plan calls for.

Tasks come from ingredient notes, so `2 onions, chopped` in two planned
recipes becomes one task: chop 4 onion.
"""
from dataclasses import dataclass, field

from .scaling import scale_recipe

# Note word -> the verb the prep list uses.
TASKS = {
    "beaten": "beat",
    "chopped": "chop",
    "crushed": "crush",
    "diced": "dice",
    "grated": "grate",
    "melted": "melt",
    "minced": "mince",
    "peeled": "peel",
    "sliced": "slice",
    "softened": "soften",
    "zested": "zest",
}


@dataclass
class PrepTask:
    verb: str
    name: str
    quantities: list = field(default_factory=list)
    recipes: list = field(default_factory=list)

    @property
    def totals(self):
        """The quantities added up per unit, in the order the units first appear."""
        sums = {}
        for quantity in self.quantities:
            sums[quantity.unit] = sums.get(quantity.unit, 0) + quantity.amount
        return list(sums.items())


def task_verb(note):
    """The prep verb a note asks for, or None; the first word that names one wins."""
    for word in note.lower().replace(",", " ").split():
        if word in TASKS:
            return TASKS[word]
    return None


def prep_list(plan):
    """One task per verb and ingredient across the plan, by verb and then ingredient."""
    tasks = {}
    for entry in plan.entries:
        recipe = entry.recipe if entry.servings is None else scale_recipe(entry.recipe, entry.servings)
        for ingredient in recipe.ingredients:
            verb = task_verb(ingredient.note)
            if verb is None:
                continue
            task = tasks.setdefault((verb, ingredient.name), PrepTask(verb, ingredient.name))
            if ingredient.quantity is not None:
                task.quantities.append(ingredient.quantity)
            if recipe.title not in task.recipes:
                task.recipes.append(recipe.title)
    return [tasks[key] for key in sorted(tasks)]
