"""Remove credentials from output before the ledger writes it down.

`Ledger.saw_output` keeps a bounded amount of what each command printed, so
`core/assumptions.py` can ask whether a pattern this task introduced ever
matched anything real. That is a genuine widening of what sits on disk: before
it, only the last three lines of a result were kept. A command that prints a
token now prints it into a file.

**Prefixes, not entropy.** The tempting implementation is a Shannon-entropy
threshold, and it is the wrong one: high entropy is the property of a git sha, a
UUID, a content hash, a base64 asset and a long identifier, all of which this
project's own outputs are full of. Entropy on this corpus is a false-positive
generator, and a redactor that eats test output would break the very check the
output is kept for. The industry converges on prefix matching for the same
reason - a token that announces itself is one you can remove exactly.

Prefixes taken from two sources that agree, rather than from memory:
Semgrep, *Secrets Story: The Prefixed Secrets That Tried to Get Away* (2025),
and apikeys.guide, *Key Formats & Prefixes*. Both are documentation of issuer
formats; no issuer was called, and that limit is worth stating in a repository
whose rule is to run the producer first.

This is defence in depth, not the defence. The state directory ignores itself
(`Ledger._keep_out_of_git`), which is what actually keeps the file out of a
commit. This is what is left if somebody copies one out by hand.
"""

from __future__ import annotations

import re

MARK = "REDACTED"
"""Deliberately a bare word, not `[redacted]` or `<redacted>`.

The redactor runs over the same text `assumptions.unverified` searches. A
replacement containing non-word characters would break a pattern like
`token=\\w+` that had in fact been confirmed, and reporting a verified pattern as
unverified is the one error that check must never make.
"""

# Tokens that announce their issuer. The trailing length requirement is what
# separates a credential from the prefix appearing in prose.
PREFIXED = re.compile(
    r"\b("
    r"gh[pousr]_"                 # GitHub classic, oauth, user, server, refresh
    r"|github_pat_"               # GitHub fine-grained
    r"|glpat-"                    # GitLab
    r"|xox[baprs]-|xapp-"         # Slack
    r"|[sr]k_(?:live|test)_"      # Stripe and friends
    r"|sk-ant-|sk-proj-|gsk_|nvapi-"
    r"|npm_|pypi-"
    r"|AKIA|ASIA"                 # AWS access key ids
    r"|AIza"                      # Google
    r")[A-Za-z0-9_\-]{10,}"
)

# A value is a secret because of what it is called, not what it looks like.
# `AWS_SECRET_ACCESS_KEY` has no prefix on its value at all.
# The quote before the separator is not decoration: without it this read
# `KEY=value` and walked straight past `"refresh_token": "1//0e..."`, which is
# how every JSON and YAML config on earth spells it. Found by running it.
NAMED = re.compile(
    r"(?i)\b(?P<name>[A-Za-z0-9_.\-]*"
    r"(?:secret|token|password|passwd|api[_\-]?key|access[_\-]?key|private[_\-]?key|credential)"
    r"[A-Za-z0-9_.\-]*)"
    r"(?P<gap>[\"']?\s*[=:]\s*[\"']?)"
    r"(?P<value>[^\s\"',;]{6,})"
)

# The value class matches NAMED's rather than `\S`, which was greedy enough to
# swallow the quote and comma after a token inside a JSON string - found by
# scrubbing a real serialized ledger and watching it stop parsing. In plain
# output it had the same bug more quietly, eating the closing quote of
# `Authorization: Bearer xyz"`.
BEARER = re.compile(r"(?i)\b(authorization\s*[:=]\s*(?:bearer|basic|token)\s+)([^\s\"',;]{6,})")

JWT = re.compile(r"\beyJ[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{8,}\.[A-Za-z0-9_\-]{6,}")

PEM = re.compile(
    r"-----BEGIN[A-Z ]*PRIVATE KEY-----.*?-----END[A-Z ]*PRIVATE KEY-----",
    re.DOTALL)


def _looks_issued(value: str) -> bool:
    """Does this value look like a credential rather than an English word?

    Without this, `Error: token: invalid` loses the word `invalid`. Real secrets
    carry a digit or mixed case almost without exception; a lowercase word does
    not.
    """
    return any(c.isdigit() for c in value) or (
        any(c.isupper() for c in value) and any(c.islower() for c in value))


def _named(match: re.Match) -> str:
    value = match.group("value")
    if not _looks_issued(value) or value.upper() == MARK:
        return match.group(0)
    return match.group("name") + match.group("gap") + MARK


def scrub_values(value):
    """Scrub every string inside a nested structure, leaving the shape alone.

    The alternative was scrubbing the serialized JSON, which is the same idea
    with one extra assumption: that no pattern here can run past a string
    boundary. That assumption was written down confidently and was false —
    `BEARER` matched `\\S` and ate the closing quote, and the ledger stopped
    parsing. Walking the structure needs no such assumption, so it cannot be
    wrong in that way at all.

    Keys are left alone: they are field names chosen in this repository, not
    text arriving from a command.
    """
    if isinstance(value, str):
        return scrub(value)
    if isinstance(value, dict):
        return {k: scrub_values(v) for k, v in value.items()}
    if isinstance(value, list):
        return [scrub_values(v) for v in value]
    return value


def scrub(text: str) -> str:
    """Replace credentials, keeping enough shape to say what was removed."""
    text = PEM.sub(f"-----BEGIN PRIVATE KEY-----{MARK}-----END PRIVATE KEY-----", text)
    text = JWT.sub(f"eyJ{MARK}", text)
    text = PREFIXED.sub(lambda m: m.group(1) + MARK, text)
    text = BEARER.sub(lambda m: m.group(1) + MARK, text)
    return NAMED.sub(_named, text)
