import re

from ._generated import ESCAPES

SAFE_SCHEMES = ("http", "https", "mailto")
UNSAFE_URL = "#"

_TABLE = str.maketrans(ESCAPES)
# Browsers drop control characters and spaces before deciding on a scheme.
_SCHEME = re.compile(r"^[\x00-\x20]*([A-Za-z][A-Za-z0-9+.\-]*)[\x00-\x20]*:")


def escape(text):
    return text.translate(_TABLE)


def safe_url(url, options):
    """The URL to emit for a link or image: unsafe schemes become UNSAFE_URL."""
    if not options.safe_links:
        return url
    match = _SCHEME.match(url)
    if match and match.group(1).lower() not in SAFE_SCHEMES:
        return UNSAFE_URL
    return url
