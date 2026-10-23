"""Roles and the inheritance between them."""
import re

from .errors import RoleError

ROLE_NAME = re.compile(r"[A-Za-z][A-Za-z0-9_-]*")
MAX_CHAIN = 8


class RoleGraph:
    def __init__(self):
        self._parent = {}

    def add(self, name, parent=None):
        if not ROLE_NAME.fullmatch(name):
            raise RoleError(f"bad role name: {name}")
        if name in self._parent:
            raise RoleError(f"role {name} is defined twice")
        self._parent[name] = parent

    def __contains__(self, name):
        return name in self._parent

    def __iter__(self):
        return iter(self._parent)

    def __len__(self):
        return len(self._parent)

    def parent_of(self, name):
        return self._parent[name]

    def ancestors(self, name):
        """`name` and every role it inherits from, nearest first."""
        chain = []
        while name is not None:
            chain.append(name)
            name = self._parent[name]
        return chain

    def expand(self, names):
        """Every role held by someone given `names`. Names the policy does not define are ignored."""
        held = set()
        for name in names:
            if name in self._parent:
                held.update(self.ancestors(name))
        return frozenset(held)

    def check(self):
        for parent in self._parent.values():
            if parent is not None and parent not in self._parent:
                raise RoleError(f"unknown role: {parent}")
        for name in self._parent:
            chain = [name]
            parent = self._parent[name]
            while parent is not None:
                if parent in chain:
                    cycle = chain[chain.index(parent):] + [parent]
                    raise RoleError("role cycle: " + " -> ".join(cycle))
                chain.append(parent)
                parent = self._parent[parent]
            if len(chain) > MAX_CHAIN:
                raise RoleError(f"inheritance chain of {name} is longer than {MAX_CHAIN} roles")
