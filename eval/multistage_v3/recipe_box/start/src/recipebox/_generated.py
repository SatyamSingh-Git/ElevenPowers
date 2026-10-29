"""Food composition tables.

Generated from the team's food composition sheet (values per 100 g of the
edible portion). Regenerate from the sheet instead of editing this file.
"""

NUTRIENT_COLUMNS = ("energy_kcal", "protein", "fat", "carbohydrate", "fibre", "sugars", "sodium_mg")

NUTRIENTS_PER_100G = {
    "baking powder": (53, 0.0, 0.0, 27.7, 0.2, 0.0, 10600),
    "banana": (89, 1.1, 0.3, 22.8, 2.6, 12.2, 1),
    "black pepper": (251, 10.4, 3.3, 64.0, 25.3, 0.6, 20),
    "bread": (265, 9.0, 3.2, 49.0, 2.7, 5.0, 491),
    "butter": (717, 0.9, 81.1, 0.1, 0.0, 0.1, 11),
    "carrot": (41, 0.9, 0.2, 9.6, 2.8, 4.7, 69),
    "cheddar": (403, 24.9, 33.1, 1.3, 0.0, 0.5, 621),
    "chicken breast": (165, 31.0, 3.6, 0.0, 0.0, 0.0, 74),
    "cream": (340, 2.8, 36.0, 2.7, 0.0, 2.9, 38),
    "egg": (143, 12.6, 9.5, 0.7, 0.0, 0.4, 142),
    "flour": (364, 10.3, 1.0, 76.3, 2.7, 0.3, 2),
    "frozen peas": (81, 5.4, 0.4, 14.5, 5.1, 5.7, 5),
    "garlic": (149, 6.4, 0.5, 33.1, 2.1, 1.0, 17),
    "honey": (304, 0.3, 0.0, 82.4, 0.2, 82.1, 4),
    "lemon": (29, 1.1, 0.3, 9.3, 2.8, 2.5, 2),
    "lentils": (352, 24.6, 1.1, 63.4, 10.7, 2.0, 6),
    "macaroni": (371, 13.0, 1.5, 74.7, 3.2, 2.7, 6),
    "milk": (61, 3.2, 3.3, 4.8, 0.0, 5.1, 43),
    "oats": (389, 16.9, 6.9, 66.3, 10.6, 0.0, 2),
    "olive oil": (884, 0.0, 100.0, 0.0, 0.0, 0.0, 2),
    "onion": (40, 1.1, 0.1, 9.3, 1.7, 4.2, 4),
    "parmesan": (431, 38.0, 29.0, 4.1, 0.0, 0.9, 1529),
    "potato": (77, 2.0, 0.1, 17.5, 2.2, 0.8, 6),
    "rice": (365, 7.1, 0.7, 80.0, 1.3, 0.1, 5),
    "salt": (0, 0.0, 0.0, 0.0, 0.0, 0.0, 38758),
    "spinach": (23, 2.9, 0.4, 3.6, 2.2, 0.4, 79),
    "sugar": (387, 0.0, 0.0, 100.0, 0.0, 100.0, 1),
    "tomato": (18, 0.9, 0.2, 3.9, 1.2, 2.6, 5),
    "vegetable stock": (5, 0.3, 0.1, 0.9, 0.0, 0.4, 300),
    "yogurt": (61, 3.5, 3.3, 4.7, 0.0, 4.7, 46),
}

DENSITY_G_PER_ML = {
    "baking powder": 0.9,
    "black pepper": 0.5,
    "butter": 0.91,
    "cheddar": 0.45,
    "cream": 1.0,
    "flour": 0.53,
    "frozen peas": 0.6,
    "honey": 1.42,
    "lentils": 0.8,
    "macaroni": 0.45,
    "milk": 1.03,
    "oats": 0.41,
    "olive oil": 0.91,
    "parmesan": 0.4,
    "rice": 0.85,
    "salt": 1.2,
    "sugar": 0.85,
    "vegetable stock": 1.0,
    "yogurt": 1.03,
}

GRAMS_EACH = {
    "banana": 120,
    "bread": 30,
    "carrot": 60,
    "chicken breast": 170,
    "egg": 50,
    "garlic": 5,
    "lemon": 100,
    "onion": 150,
    "potato": 170,
    "tomato": 120,
}
