"""How a rule's pattern is compared with a payee. A rule names its matcher in `match`."""
import re

from ..errors import ValidationError


def _contains(pattern, payee):
    return pattern.casefold() in payee.casefold()


def _prefix(pattern, payee):
    return payee.casefold().startswith(pattern.casefold())


def _exact(pattern, payee):
    return payee.casefold() == pattern.casefold()


def _regex(pattern, payee):
    return re.search(pattern, payee, re.IGNORECASE) is not None


MATCHERS = {
    "contains": _contains,
    "prefix": _prefix,
    "exact": _exact,
    "regex": _regex,
}


def matcher_for(kind):
    try:
        return MATCHERS[kind]
    except KeyError:
        raise ValidationError(f"unknown match kind: {kind}") from None


def check_pattern(kind, pattern):
    """Refuse a rule its matcher could never apply."""
    matcher_for(kind)
    if not pattern.strip():
        raise ValidationError("rule pattern is empty")
    if kind == "regex":
        try:
            re.compile(pattern)
        except re.error as error:
            raise ValidationError(f"invalid regular expression {pattern!r}: {error}") from None
