import pytest

from recipebox.config import Home
from recipebox.storage.recipe_text import parse_recipe

PANCAKES = """\
title: Fluffy Pancakes
servings: 4
time: 25 min
tags: breakfast, sweet

ingredients:
- 1 1/2 cup flour
- 2 tbsp sugar
- 2 eggs
- 1 1/4 cup milk
- 30 g butter, melted
- salt, to taste

steps:
1. Whisk the flour, sugar and salt.
2. Beat in the eggs, milk and butter.
3. Fry in spoonfuls until golden.
"""

SOUP = """\
title: Tomato Soup
servings: 2
time: 40 min
tags: lunch, vegetarian

ingredients:
- 6 tomatoes, chopped
- 1 onion
- 2 cloves garlic
- 2 tbsp olive oil
- 500 ml vegetable stock
"""


@pytest.fixture
def pancakes():
    return parse_recipe(PANCAKES)


@pytest.fixture
def soup():
    return parse_recipe(SOUP)


@pytest.fixture
def home(tmp_path):
    return Home(tmp_path / "home")


@pytest.fixture
def recipe_files(tmp_path):
    (tmp_path / "pancakes.recipe").write_text(PANCAKES, encoding="utf-8")
    (tmp_path / "soup.recipe").write_text(SOUP, encoding="utf-8")
    return [tmp_path / "pancakes.recipe", tmp_path / "soup.recipe"]
