from dataclasses import dataclass, field
from typing import Mapping, Optional

from .conditions import Condition
from .patterns import Pattern
from .roles import RoleGraph


@dataclass(frozen=True)
class User:
    name: str
    roles: tuple = ()
    attrs: Mapping = field(default_factory=dict)


@dataclass(frozen=True)
class Request:
    user: User
    action: str
    resource: str
    resource_attrs: Mapping = field(default_factory=dict)


@dataclass(frozen=True)
class Rule:
    number: int
    effect: str
    role: str
    actions: tuple
    pattern: Pattern
    condition: Optional[Condition] = None
    line: Optional[int] = None


@dataclass
class Policy:
    roles: RoleGraph
    rules: tuple
    default: str = "deny"


@dataclass(frozen=True)
class Decision:
    request: Request
    allowed: bool
    reason: str
    rule: Optional[Rule] = None
    # Rules that matched role, action and resource but whose condition did not hold.
    near_misses: tuple = ()
    roles: frozenset = frozenset()
