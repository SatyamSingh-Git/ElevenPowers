"""Export bundles: recipes written out to share with another recipebox.

A bundle holds its recipes in the same form as `library.json`, under a
`recipebox` marker that gives the bundle version.
"""
import json
from pathlib import Path

from .library import recipe_to_dict

BUNDLE_VERSION = 1


def write_bundle(recipes, path):
    recipes = list(recipes)
    data = {"recipebox": BUNDLE_VERSION, "recipes": [recipe_to_dict(recipe) for recipe in recipes]}
    Path(path).write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return len(recipes)
