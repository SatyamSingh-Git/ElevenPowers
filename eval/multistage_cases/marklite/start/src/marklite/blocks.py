"""Block structure: headings, paragraphs, fenced code, quotes, lists and rules."""
from dataclasses import dataclass
import re
from typing import NamedTuple

_HEADING = re.compile(r"^ {0,3}(#{1,6})(?=[ \t]|$)(.*)$")
_CLOSING_HASHES = re.compile(r"(?:^|[ \t]+)#+[ \t]*$")
_FENCE = re.compile(r"^( {0,3})(`{3,}|~{3,})[ \t]*(.*?)[ \t]*$")
_RULE = re.compile(r"^ {0,3}(?:(?:\*[ \t]*){3,}|(?:-[ \t]*){3,}|(?:_[ \t]*){3,})$")
_QUOTE = re.compile(r"^ {0,3}> ?")
_BULLET = re.compile(r"^( {0,3})([-+*])( +|$)")
_ORDERED = re.compile(r"^( {0,3})(\d{1,9})([.)])( +|$)")


@dataclass
class Heading:
    level: int
    text: str
    line: int


@dataclass
class Paragraph:
    text: str
    line: int


@dataclass
class CodeBlock:
    info: str
    code: str
    line: int


@dataclass
class Quote:
    children: list
    line: int


@dataclass
class ListBlock:
    ordered: bool
    start: int
    items: list
    line: int


@dataclass
class Rule:
    line: int


@dataclass
class Document:
    children: list


class _Marker(NamedTuple):
    ordered: bool
    delimiter: str
    number: int
    width: int


def parse_blocks(text):
    text = text.replace("\r\n", "\n").replace("\r", "\n").expandtabs(4)
    lines = text.removesuffix("\n").split("\n")
    return Document(_BlockParser(lines, 1).blocks())


def _marker(line):
    match = _BULLET.match(line)
    if match:
        return _Marker(False, match.group(2), 1, _width(match, 3))
    match = _ORDERED.match(line)
    if match:
        return _Marker(True, match.group(3), int(match.group(2)), _width(match, 4))
    return None


def _width(match, spaces):
    """Column where a list item's content starts."""
    before = match.start(spaces)
    gap = len(match.group(spaces))
    return before + 1 if gap == 0 or gap > 4 else before + gap


def _indent(line):
    return len(line) - len(line.lstrip(" "))


def _starts_block(line):
    return bool(_FENCE.match(line) or _HEADING.match(line) or _RULE.match(line)
                or _QUOTE.match(line) or _marker(line))


def _heading_text(raw):
    return _CLOSING_HASHES.sub("", raw.strip())


class _BlockParser:
    def __init__(self, lines, first_line):
        self.lines = lines
        self.first_line = first_line
        self.i = 0

    def blocks(self):
        blocks = []
        while self.i < len(self.lines):
            if self.lines[self.i].strip():
                blocks.append(self.block(self.lines[self.i]))
            else:
                self.i += 1
        return blocks

    def block(self, line):
        start = self.first_line + self.i
        fence = _FENCE.match(line)
        if fence and not (fence.group(2)[0] == "`" and "`" in fence.group(3)):
            return self.fence(fence, start)
        heading = _HEADING.match(line)
        if heading:
            self.i += 1
            return Heading(len(heading.group(1)), _heading_text(heading.group(2)), start)
        if _RULE.match(line):
            self.i += 1
            return Rule(start)
        if _QUOTE.match(line):
            return self.quote(start)
        marker = _marker(line)
        if marker:
            return self.list(marker, start)
        return self.paragraph(start)

    def fence(self, match, start):
        indent, marker, info = len(match.group(1)), match.group(2), match.group(3)
        self.i += 1
        code = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            self.i += 1
            stripped = line.strip()
            if _indent(line) < 4 and stripped.startswith(marker) and set(stripped) == {marker[0]}:
                break
            code.append(line[min(indent, _indent(line)):])
        return CodeBlock(info, "".join(f"{line}\n" for line in code), start)

    def quote(self, start):
        inner = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            match = _QUOTE.match(line)
            if match:
                inner.append(line[match.end():])
            elif line.strip() and inner and inner[-1].strip() and not _starts_block(line):
                inner.append(line)
            else:
                break
            self.i += 1
        return Quote(_BlockParser(inner, start).blocks(), start)

    def list(self, first, start):
        items = []
        while self.i < len(self.lines):
            marker = _marker(self.lines[self.i])
            if not marker or (marker.ordered, marker.delimiter) != (first.ordered, first.delimiter):
                break
            items.append(self.item(marker))
            following = self.i
            while following < len(self.lines) and not self.lines[following].strip():
                following += 1
            if following < len(self.lines) and _marker(self.lines[following]):
                self.i = following
        return ListBlock(first.ordered, first.number, items, start)

    def item(self, marker):
        start = self.first_line + self.i
        content = [self.lines[self.i][marker.width:]]
        self.i += 1
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if not line.strip():
                following = self.i
                while following < len(self.lines) and not self.lines[following].strip():
                    following += 1
                if following == len(self.lines) or _indent(self.lines[following]) < marker.width:
                    break
                content.extend([""] * (following - self.i))
                self.i = following
                continue
            if _indent(line) >= marker.width:
                content.append(line[marker.width:])
            elif content[-1].strip() and not _starts_block(line):
                content.append(line.strip())
            else:
                break
            self.i += 1
        return _BlockParser(content, start).blocks()

    def paragraph(self, start):
        lines = []
        while self.i < len(self.lines):
            line = self.lines[self.i]
            if not line.strip() or (lines and _starts_block(line)):
                break
            lines.append(line.strip())
            self.i += 1
        return Paragraph("\n".join(lines), start)
