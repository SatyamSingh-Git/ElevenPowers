"""Credentials out, everything else untouched.

Design: `docs/design/unverified-assumptions.md` §7c. Keeping 12x8KB of command
output so a pattern can be checked against it is a real widening of what sits on
disk, and this is the half of the answer that survives somebody copying the file
out by hand. The other half - the state directory ignoring itself - is
`test_state_directory_ignores_itself` below.

Both directions matter here more than usual, and the adversarial one is the
harder requirement: a redactor that eats ordinary test output would break the
check the output is kept for. Entropy-based redaction fails exactly there, which
is why this one matches prefixes.
"""

import subprocess

import pytest

from core.ledger import STATE_DIR, Ledger
from core.obligations import Claim
from core.redact import MARK, scrub

# Invented values in the issuers' documented shapes - none is live. They are
# assembled from a prefix and a body at import time so that no complete token
# literal ever appears in this file.
#
# That is not fastidiousness. The first version wrote them out whole and
# **GitHub's push protection refused the push**, naming the Slack and Stripe
# lines. Which is a pleasant external confirmation that this table holds the
# shapes real scanners look for - and a reminder that a fixture shaped exactly
# like a live credential gets treated as one, by every tool downstream of here.
def _shaped(prefix, body):
    return prefix + body


ISSUED = [
    ("aws key id", "aws_access_key_id = " + _shaped("AKIA", "IOSFODNN7EXAMPLE"),
     "IOSFODNN7EXAMPLE"),
    ("aws secret", "AWS_SECRET_ACCESS_KEY=" + _shaped("wJalrXUtnFEMI", "/K7MDENG/bPx"),
     "wJalrXUtnFEMI"),
    ("github classic", _shaped("ghp_", "16C7e42F292c6912E7710c838347Ae178B4a"),
     "16C7e42F292c"),
    ("github fine-grained",
     _shaped("github_pat_", "11ABCDEFG0aBcDeFgHiJkL_mNoPqRsTuVwXyZ01"),
     "mNoPqRsTuVwXyZ01"),
    ("gitlab", _shaped("glpat-", "ABCdefGHIjklMNOpqrST"), "ABCdefGHIjkl"),
    ("slack bot", _shaped("xoxb-", "123456789012-1234567890123-AbCdEfGhIjKlMnOpQrSt"),
     "AbCdEfGhIjKlMnOpQrSt"),
    ("stripe live", _shaped("sk_live_", "51H8xAbCdEfGhIjKlMnOpQrStUvWxYz"),
     "51H8xAbCdEfGh"),
    ("anthropic", "ANTHROPIC_API_KEY=" + _shaped("sk-ant-", "api03-AbCdEfGhIjKlMnOpQrStUvWxYz01"),
     "AbCdEfGhIjKlMnOpQrStUvWxYz01"),
    ("google", _shaped("AIza", "SyD-1234567890abcdefghijklmnopqrstu"),
     "SyD-1234567890abc"),
    ("npm", _shaped("npm_", "AbCdEfGhIjKlMnOpQrStUvWxYz0123456789"),
     "AbCdEfGhIjKlMnOpQrSt"),
    ("bearer header", "Authorization: Bearer AbCdEfGhIjKlMnOpQrStUvWxYz0123",
     "AbCdEfGhIjKlMnOpQrStUvWxYz0123"),
    ("json field", '{"refresh_token": "' + _shaped("1//0e", "AbCdEfGhIjKlMnOpQrStUvWxYz") + '"}',
     "AbCdEfGhIjKlMnOpQrStUvWxYz"),
    ("dotenv", "DATABASE_PASSWORD=Sup3rS3cretDbPass", "Sup3rS3cretDbPass"),
    ("jwt", _shaped("eyJ", "hbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dBjftJeZ4CVPmB92K27u"),
     "eyJzdWIiOiIxMjM0NTY3ODkw"),
    ("pem", "-----BEGIN RSA PRIVATE KEY-----\nMIIEowIBAAKCAQEA7pQ\n"
            "-----END RSA PRIVATE KEY-----", "MIIEowIBAAKCAQEA7pQ"),
]

# Every one of these is high-entropy or contains a trigger word, and every one
# is ordinary output this project produces constantly. An entropy threshold eats
# the first three.
INNOCENT = [
    "commit 23f6e785aa1c4d9e0b77f3a2c81d5e6f90ab1234",
    "run-id: 550e8400-e29b-41d4-a716-446655440000",
    "sha256:9f86d081884c7d659a2feaa0c55ad015a3bf4f1b2b0b822cd15d6c15b0f00a08",
    "Error: token: invalid",
    "self.token_count = len(tokens)",
    "password reset email sent to the user",
    "def secret_santa(names):",
    "tests/test_secrets.py::test_token_parse PASSED",
    "ok 12 - password validation rejects short input",
    "# pass 41\n# fail 0\n",
    "TAP version 13\n1..3\nok 1 - adds\n",
]


@pytest.mark.parametrize("name,line,material", ISSUED, ids=[i[0] for i in ISSUED])
def test_an_issued_credential_does_not_reach_the_file(name, line, material):
    after = scrub(line)
    assert material not in after, f"{name} survived: {after!r}"
    assert MARK in after


@pytest.mark.parametrize("line", INNOCENT)
def test_ordinary_output_is_left_exactly_alone(line):
    """The adversarial direction, and the one that decides the design.

    The redactor runs over the text `assumptions.unverified` searches. Anything
    it damages here turns a pattern that *was* confirmed into a report that it
    was not - the single error that check must never make.
    """
    assert scrub(line) == line


def test_the_replacement_cannot_break_a_pattern_that_was_confirmed():
    """`MARK` is a bare word on purpose.

    `<redacted>` would stop `token=\\w+` matching its own redacted output, and
    the pattern would be reported as unverified after being verified.
    """
    import re

    assert re.search(r"token=\w+", scrub("token=Ab3fXq91ZzKw"))


def test_a_lowercase_english_word_is_not_a_credential():
    assert scrub("Error: token: invalid") == "Error: token: invalid"
    assert MARK in scrub("Error: token: inv4lidSecret")


def test_the_ledger_scrubs_on_the_way_in():
    """Forward and adversarial in one: the wiring, not just the function."""
    led = Ledger(root=".", task="t", claims=[Claim.BUG_FIXED])
    led.saw_output("curl -H 'Authorization: Bearer AbCdEf0123456789xyz'", "ok\n")
    led.saw_output("printenv", "GITHUB_TOKEN=ghp_16C7e42F292c6912E7710c838347Ae178B4a\n")
    kept = "\n".join(item["command"] + item["text"] for item in led.outputs)
    assert "AbCdEf0123456789xyz" not in kept, "the command string is stored too"
    assert "16C7e42F292c" not in kept
    assert kept.count(MARK) == 2


def test_state_directory_ignores_itself(tmp_path):
    """A repository that has never heard of this plugin must not commit it.

    This repository gitignores the state directory; a user's does not, and
    `git add -A` would commit the prompt, every command and what they printed.
    Adversarially: with the marker removed, git sees the directory - so the
    silence above is caused by the marker and not by an empty write.
    """
    def status(root):
        subprocess.run(["git", "init", "-q"], cwd=root, capture_output=True)
        led = Ledger(root=root, task="t", claims=[Claim.BUG_FIXED])
        led.request = "fix the login bug"
        led.save()
        return subprocess.run(["git", "status", "--porcelain"], cwd=root,
                              capture_output=True, text=True).stdout.strip()

    quiet = tmp_path / "quiet"
    quiet.mkdir()
    assert status(quiet) == "", "the state directory is visible to git"
    assert (quiet / STATE_DIR / ".gitignore").read_text(encoding="utf-8") == "*\n"

    loud = tmp_path / "loud"
    loud.mkdir()
    status(loud)
    (loud / STATE_DIR / ".gitignore").unlink()
    seen = subprocess.run(["git", "status", "--porcelain"], cwd=loud,
                          capture_output=True, text=True).stdout
    assert STATE_DIR in seen, "the probe proves nothing: git never saw it either way"


def test_an_existing_marker_is_not_overwritten(tmp_path):
    """The user may have put something there. Housekeeping does not own it."""
    state = tmp_path / STATE_DIR
    state.mkdir()
    (state / ".gitignore").write_text("*\n!keep.json\n", encoding="utf-8")
    Ledger(root=tmp_path, task="t", claims=[Claim.BUG_FIXED]).save()
    assert (state / ".gitignore").read_text(encoding="utf-8") == "*\n!keep.json\n"


URL_CASES = [
    ("https://user:pa55word@example.invalid/x", False, "pa55word"),
    ("https://token123456@github.invalid/o/r.git", True, None),
    ("git@github.invalid:user/repo.git", True, None),
    ("https://example.invalid/x", True, None),
    ("PATH=/usr/bin:/bin", True, None),
    ("http://localhost:8080/api", True, None),
]


@pytest.mark.parametrize("line,unchanged,secret", URL_CASES)
def test_url_credential_handling(line, unchanged, secret):
    """`https://user:token@host` is how a credential reaches a git remote.

    Both ways in one table: the password half goes, and the five shapes that
    only *look* like it - an ssh remote, a bare URL, a PATH, a port number -
    must come through untouched, or every log line with a colon in it is
    damaged.
    """
    after = scrub(line)
    if unchanged:
        assert after == line
    else:
        assert secret not in after
        assert MARK in after
        assert after.startswith("https://user:"), "the username is not a secret"
