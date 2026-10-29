"""Where ingredients are found in the shop.

Aisle codes are listed in the order the shop is walked; an ingredient the
catalog does not know is in `other`.
"""

AISLE_ORDER = ("produce", "bakery", "dairy", "meat", "pantry", "frozen", "other")

INGREDIENT_AISLES = {
    "produce": (
        "banana", "carrot", "garlic", "green onion", "lemon", "onion", "potato", "spinach", "tomato",
    ),
    "bakery": ("bread",),
    "dairy": ("butter", "cheddar", "cream", "egg", "milk", "parmesan", "yogurt"),
    "meat": ("bacon", "chicken breast", "minced beef"),
    "pantry": (
        "baking powder", "black pepper", "flour", "honey", "lentils", "macaroni", "oats",
        "olive oil", "rice", "salt", "sugar", "vegetable stock",
    ),
    "frozen": ("frozen peas",),
}

_AISLE_OF = {name: aisle for aisle, names in INGREDIENT_AISLES.items() for name in names}


def aisle_for(name):
    return _AISLE_OF.get(name, "other")
