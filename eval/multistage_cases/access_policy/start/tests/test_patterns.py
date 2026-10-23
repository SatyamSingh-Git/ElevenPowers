import pytest

from warden.errors import PolicyError
from warden.patterns import Pattern, normalize


@pytest.mark.parametrize("pattern, resource, expected", [
    ("reports/q1", "reports/q1", True),
    ("reports/q1", "reports/q2", False),
    ("reports/*", "reports/q1", True),
    ("reports/*", "reports/2024/q1", False),
    ("reports/*.csv", "reports/q1.csv", True),
    ("reports/*.csv", "reports/q1.pdf", False),
    ("reports/**", "reports", True),
    ("reports/**", "reports/2024/q1", True),
    ("**/secret", "a/b/secret", True),
    ("**/secret", "secret", True),
    ("a/**/z", "a/z", True),
    ("a/**/z", "a/b/c/z", True),
    ("a/**/z", "a/b/c", False),
])
def test_matches(pattern, resource, expected):
    assert Pattern(pattern).matches(resource) is expected


def test_resource_paths_are_normalized():
    assert normalize("/reports//q1/") == "reports/q1"
    assert Pattern("reports/q1").matches("/reports//q1/")


@pytest.mark.parametrize("text", ["", "/", "reports/**x"])
def test_bad_patterns(text):
    with pytest.raises(PolicyError, match="bad pattern"):
        Pattern(text)


@pytest.mark.parametrize("wide, narrow, expected", [
    ("reports/**", "reports/2024/*", True),
    ("reports/*", "reports/*.csv", True),
    ("reports/*.csv", "reports/*", False),
    ("reports/*", "reports/**", False),
    ("**", "anything/at/all", True),
    ("reports/q1", "reports/q1", True),
])
def test_covers(wide, narrow, expected):
    assert Pattern(wide).covers(Pattern(narrow)) is expected
