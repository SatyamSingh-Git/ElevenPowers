"""Inline markup: code spans, emphasis, links, images, autolinks and entities."""
from dataclasses import dataclass
import re

from ._generated import NAMED_ENTITIES
from .escape import escape, safe_url

PUNCTUATION = frozenset("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
_ENTITY = re.compile(r"&(?:#([0-9]{1,7})|#[xX]([0-9a-fA-F]{1,6})|([A-Za-z][A-Za-z0-9]{1,31}));")
_AUTOLINK = re.compile(r"<((?:https?|mailto):[^\s<>]+)>")
_ESCAPED = re.compile(r"\\([!-/:-@\[-`{-~])")


@dataclass
class Text:
    value: str


@dataclass
class Code:
    value: str


@dataclass
class Entity:
    raw: str


@dataclass
class Emphasis:
    children: list


@dataclass
class Strong:
    children: list


@dataclass
class Link:
    url: str
    title: str
    children: list


@dataclass
class Image:
    url: str
    title: str
    alt: list


def parse_inline(text):
    return _Scanner(text).parse()


def render_inline(nodes, options):
    return "".join(_render(node, options) for node in nodes)


def plain_text(nodes):
    """The text a reader sees, with markup dropped and entities decoded."""
    parts = []
    for node in nodes:
        if isinstance(node, (Text, Code)):
            parts.append(node.value)
        elif isinstance(node, Entity):
            parts.append(decode_entity(node.raw))
        elif isinstance(node, Image):
            parts.append(plain_text(node.alt))
        else:
            parts.append(plain_text(node.children))
    return "".join(parts)


def decode_entity(raw):
    """The character an entity reference stands for, or None if marklite does not know it."""
    decimal, hexadecimal, name = _ENTITY.fullmatch(raw).groups()
    if name:
        return NAMED_ENTITIES.get(name)
    code = int(decimal) if decimal else int(hexadecimal, 16)
    if code == 0 or code > 0x10FFFF or 0xD800 <= code <= 0xDFFF:
        return None
    return chr(code)


def _render(node, options):
    if isinstance(node, Text):
        html = escape(node.value)
        return html.replace("\n", "<br />\n") if options.hard_breaks else html
    if isinstance(node, Code):
        return f"<code>{escape(node.value)}</code>"
    if isinstance(node, Entity):
        return node.raw
    if isinstance(node, Emphasis):
        return f"<em>{render_inline(node.children, options)}</em>"
    if isinstance(node, Strong):
        return f"<strong>{render_inline(node.children, options)}</strong>"
    if isinstance(node, Link):
        href = escape(safe_url(node.url, options))
        return f'<a href="{href}"{_title(node.title)}>{render_inline(node.children, options)}</a>'
    src = escape(safe_url(node.url, options))
    return f'<img src="{src}" alt="{escape(plain_text(node.alt))}"{_title(node.title)} />'


def _title(title):
    return f' title="{escape(title)}"' if title else ""


class _Scanner:
    def __init__(self, text):
        self.text = text
        self.pos = 0
        self.nodes = []
        self.pending = []

    def parse(self):
        handlers = {"\\": self.backslash, "`": self.code, "&": self.entity, "<": self.autolink,
                    "[": self.link, "!": self.image, "*": self.emphasis, "_": self.emphasis}
        while self.pos < len(self.text):
            handler = handlers.get(self.text[self.pos])
            if handler is None or not handler():
                self.pending.append(self.text[self.pos])
                self.pos += 1
        self.flush()
        return self.nodes

    def flush(self):
        if self.pending:
            self.nodes.append(Text("".join(self.pending)))
            self.pending = []

    def emit(self, node, end):
        self.flush()
        self.nodes.append(node)
        self.pos = end
        return True

    def literal(self, chars):
        self.pending.append(chars)
        self.pos += len(chars)
        return True

    def backslash(self):
        escaped = self.text[self.pos + 1:self.pos + 2]
        if escaped not in PUNCTUATION:
            return False
        self.pending.append(escaped)
        self.pos += 2
        return True

    def code(self):
        run = _run(self.text, self.pos, "`")
        end = _code_span_end(self.text, self.pos)
        if end is None:
            return self.literal("`" * run)
        content = self.text[self.pos + run:end - run].replace("\n", " ")
        if content.startswith(" ") and content.endswith(" ") and content.strip():
            content = content[1:-1]
        return self.emit(Code(content), end)

    def entity(self):
        match = _ENTITY.match(self.text, self.pos)
        if not match or decode_entity(match.group()) is None:
            return False
        return self.emit(Entity(match.group()), match.end())

    def autolink(self):
        match = _AUTOLINK.match(self.text, self.pos)
        if not match:
            return False
        return self.emit(Link(match.group(1), "", [Text(match.group(1))]), match.end())

    def link(self):
        found = _link_at(self.text, self.pos)
        if found is None:
            return False
        label, url, title, end = found
        return self.emit(Link(url, title, parse_inline(label)), end)

    def image(self):
        if self.text[self.pos + 1:self.pos + 2] != "[":
            return False
        found = _link_at(self.text, self.pos + 1)
        if found is None:
            return False
        label, url, title, end = found
        return self.emit(Image(url, title, parse_inline(label)), end)

    def emphasis(self):
        char = self.text[self.pos]
        run = _run(self.text, self.pos, char)
        if run <= 2 and _opens(self.text, self.pos, run, char):
            end = _closing(self.text, self.pos + run, char * run)
            if end is not None:
                kind = Strong if run == 2 else Emphasis
                return self.emit(kind(parse_inline(self.text[self.pos + run:end])), end + run)
        return self.literal(char * run)


def _run(text, pos, char):
    end = pos
    while end < len(text) and text[end] == char:
        end += 1
    return end - pos


def _code_span_end(text, pos):
    """Index just past the backtick run closing the code span opened at pos, or None."""
    run = _run(text, pos, "`")
    search = pos + run
    while (found := text.find("`" * run, search)) != -1:
        length = _run(text, found, "`")
        if length == run:
            return found + run
        search = found + length
    return None


def _skip(text, j):
    """Where scanning resumes after an escape or a code span starting at j, or None."""
    if text[j] == "\\":
        return j + 2
    if text[j] == "`":
        end = _code_span_end(text, j)
        return end if end is not None else j + _run(text, j, "`")
    return None


def _opens(text, pos, run, char):
    after = text[pos + run:pos + run + 1]
    if not after or after.isspace():
        return False
    return not (char == "_" and pos > 0 and text[pos - 1].isalnum())


def _closing(text, start, delim):
    char, j = delim[0], start
    while j < len(text):
        resume = _skip(text, j)
        if resume is not None:
            j = resume
            continue
        if text[j] != char:
            j += 1
            continue
        run = _run(text, j, char)
        if (run == len(delim) and j > start and not text[j - 1].isspace()
                and not (char == "_" and text[j + run:j + run + 1].isalnum())):
            return j
        j += run
    return None


def _matching_bracket(text, pos):
    depth, j = 0, pos
    while j < len(text):
        resume = _skip(text, j)
        if resume is not None:
            j = resume
            continue
        if text[j] == "[":
            depth += 1
        elif text[j] == "]":
            depth -= 1
            if depth == 0:
                return j
        j += 1
    return None


def _link_at(text, pos):
    """(label, url, title, end) for a `[label](url "title")` starting at pos, or None."""
    close = _matching_bracket(text, pos)
    if close is None or text[close + 1:close + 2] != "(":
        return None
    i, n = close + 2, len(text)
    while i < n and text[i].isspace():
        i += 1
    start, depth = i, 0
    while i < n and not text[i].isspace():
        if text[i] == "\\":
            i += 2
            continue
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            if depth == 0:
                break
            depth -= 1
        i += 1
    url = _ESCAPED.sub(r"\1", text[start:i])
    while i < n and text[i].isspace():
        i += 1
    title = ""
    if i < n and text[i] in "\"'":
        end = i + 1
        while end < n and text[end] != text[i]:
            end += 2 if text[end] == "\\" else 1
        if end >= n:
            return None
        title = _ESCAPED.sub(r"\1", text[i + 1:end])
        i = end + 1
        while i < n and text[i].isspace():
            i += 1
    if i >= n or text[i] != ")":
        return None
    return text[pos + 1:close], url, title, i + 1
