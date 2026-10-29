"""A recipe as a small, printable HTML page, for `recipebox show --html`."""
from html import escape

from ..core.ingredients import describe_ingredient
from ..storage.recipe_text import format_minutes

STYLE = (
    "body{font-family:Georgia,serif;max-width:36em;margin:2em auto;line-height:1.5}"
    "h1{margin-bottom:.2em}.facts{color:#555}li{margin:.2em 0}"
)


def recipe_html(recipe):
    facts = [f"Serves {recipe.servings}"]
    if recipe.minutes is not None:
        facts.append(format_minutes(recipe.minutes))
    if recipe.tags:
        facts.append(", ".join(recipe.tags))
    out = [
        "<!doctype html>",
        '<html lang="en">',
        f'<head><meta charset="utf-8"><title>{escape(recipe.title)}</title><style>{STYLE}</style></head>',
        "<body>",
        f"<h1>{escape(recipe.title)}</h1>",
        f'<p class="facts">{escape(" · ".join(facts))}</p>',
        "<h2>Ingredients</h2>",
        "<ul>",
    ]
    out += [f"<li>{escape(describe_ingredient(ingredient))}</li>" for ingredient in recipe.ingredients]
    out.append("</ul>")
    if recipe.steps:
        out += ["<h2>Method</h2>", "<ol>"]
        out += [f"<li>{escape(step)}</li>" for step in recipe.steps]
        out.append("</ol>")
    out += ["</body>", "</html>"]
    return "\n".join(out) + "\n"
