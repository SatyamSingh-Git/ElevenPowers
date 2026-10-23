"""Attribute conditions such as `user.dept == resource.dept and user.level >= 2`."""
import operator
import re

from .errors import ConditionError

NAMESPACES = ("user", "resource")
OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    "<=": operator.le,
    ">=": operator.ge,
    "<": operator.lt,
    ">": operator.gt,
}
JOIN = "and"

_TOKEN = re.compile(r'\s*(?:(?P<string>"[^"]*")|(?P<op>==|!=|<=|>=|<|>)|(?P<word>[^\s"<>=!]+))')
_NUMBER = re.compile(r"-?\d+(\.\d+)?")
MISSING = object()


class Attribute:
    def __init__(self, namespace, name):
        self.namespace = namespace
        self.name = name

    def value(self, scope):
        return scope[self.namespace].get(self.name, MISSING)


class Literal:
    def __init__(self, constant):
        self.constant = constant

    def value(self, scope):
        return self.constant


class Clause:
    def __init__(self, left, op, right, text):
        self.left = left
        self.op = op
        self.right = right
        self.text = text

    def holds(self, scope):
        left, right = self.left.value(scope), self.right.value(scope)
        if left is MISSING or right is MISSING:
            return False
        return OPERATORS[self.op](_text(left), _text(right))


def _text(value):
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _tokens(text):
    position, tokens = 0, []
    while position < len(text):
        if not text[position:].strip():
            break
        match = _TOKEN.match(text, position)
        if not match or match.end() == position:
            raise ConditionError(f"bad condition: {text}")
        kind = match.lastgroup
        tokens.append((kind, match.group(kind)))
        position = match.end()
    return tokens


def _operand(kind, token):
    if kind == "string":
        return Literal(token[1:-1])
    if token in ("true", "false"):
        return Literal(token == "true")
    if _NUMBER.fullmatch(token):
        return Literal(float(token) if "." in token else int(token))
    namespace, dot, name = token.partition(".")
    if not dot or not name:
        raise ConditionError(f"bad operand: {token}")
    if namespace not in NAMESPACES:
        raise ConditionError(f"unknown attribute namespace: {namespace}")
    return Attribute(namespace, name)


def _parse(text):
    clauses, current = [], []
    for kind, token in _tokens(text) + [("word", JOIN)]:
        if kind == "word" and token == JOIN:
            if len(current) != 3 or current[1][0] != "op" or "op" in (current[0][0], current[2][0]):
                raise ConditionError(f"bad condition: {text}")
            (lk, left), (_, op), (rk, right) = current
            clauses.append(Clause(_operand(lk, left), op, _operand(rk, right), f"{left} {op} {right}"))
            current = []
        else:
            current.append((kind, token))
    return clauses


class Condition:
    def __init__(self, text):
        self.text = text.strip()
        self.clauses = _parse(self.text)

    def evaluate(self, user, resource):
        return all(clause.holds({"user": user, "resource": resource}) for clause in self.clauses)

    def failing(self, user, resource):
        """The clauses that do not hold, as written."""
        scope = {"user": user, "resource": resource}
        return [clause.text for clause in self.clauses if not clause.holds(scope)]
