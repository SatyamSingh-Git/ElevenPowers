"""Action names: the generated table plus the aliases people actually type."""
from ._generated import ACTIONS, ALIASES
from .errors import PolicyError

ANY_ACTION = "*"


def canonical_action(name):
    word = name.strip().lower()
    word = ALIASES.get(word, word)
    if word != ANY_ACTION and word not in ACTIONS:
        raise PolicyError(f"unknown action: {name}")
    return word
