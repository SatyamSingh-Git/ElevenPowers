import re
import unicodedata

EMPTY_SLUG = "heading"
_WORD = re.compile(r"[^\W_]+")


def slugify(text):
    """Lowercase words joined by hyphens: "C++ & Rust!" -> "c-rust"."""
    text = unicodedata.normalize("NFKC", text).casefold()
    return "-".join(_WORD.findall(text))


class Slugger:
    """Hands out unique slugs in document order: intro, intro-1, intro-2."""

    def __init__(self):
        self.seen = set()

    def slug(self, text):
        base = slugify(text) or EMPTY_SLUG
        candidate, n = base, 0
        while candidate in self.seen:
            n += 1
            candidate = f"{base}-{n}"
        self.seen.add(candidate)
        return candidate
