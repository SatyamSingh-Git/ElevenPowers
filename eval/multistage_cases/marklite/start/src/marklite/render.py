"""HTML rendering of a parsed document, and the public entry points."""
from .blocks import CodeBlock, Heading, ListBlock, Paragraph, Quote, parse_blocks
from .errors import MarkliteError
from .escape import escape
from .inline import parse_inline, plain_text, render_inline
from .options import Options
from .outline import TOC_MARKER, build_toc, render_toc
from .slug import Slugger

MAX_INPUT_CHARS = 1_000_000


def parse(text):
    if len(text) > MAX_INPUT_CHARS:
        raise MarkliteError(f"input exceeds {MAX_INPUT_CHARS} characters")
    return parse_blocks(text)


def render(text, options=None):
    return _Renderer(parse(text), options or Options()).render()


def toc(text, options=None):
    return build_toc(parse(text), options or Options())


class _Renderer:
    def __init__(self, document, options):
        self.document = document
        self.options = options
        self.slugger = Slugger()

    def render(self):
        return "".join(self.block(node, top=True) for node in self.document.children)

    def blocks(self, nodes):
        return "".join(self.block(node) for node in nodes)

    def block(self, node, top=False):
        if isinstance(node, Heading):
            return self.heading(node, top)
        if isinstance(node, Paragraph):
            if top and node.text == TOC_MARKER:
                return render_toc(build_toc(self.document, self.options)) + "\n"
            return f"<p>{self.inline(node.text)}</p>\n"
        if isinstance(node, CodeBlock):
            return self.code(node)
        if isinstance(node, Quote):
            return f"<blockquote>\n{self.blocks(node.children)}</blockquote>\n"
        if isinstance(node, ListBlock):
            return self.list(node)
        return "<hr />\n"

    def inline(self, text):
        return render_inline(parse_inline(text), self.options)

    def heading(self, node, top):
        content = parse_inline(node.text)
        attributes = ""
        # Only top-level headings get ids; they are the ones the table of contents can list.
        if top and self.options.heading_ids:
            attributes = f' id="{escape(self.slugger.slug(plain_text(content)))}"'
        return f"<h{node.level}{attributes}>{render_inline(content, self.options)}</h{node.level}>\n"

    def code(self, node):
        language = node.info.split()[0] if node.info else ""
        attributes = f' class="{escape(self.options.code_class_prefix + language)}"' if language else ""
        return f"<pre><code{attributes}>{escape(node.code)}</code></pre>\n"

    def list(self, node):
        tag = "ol" if node.ordered else "ul"
        start = f' start="{node.start}"' if node.ordered and node.start != 1 else ""
        return f"<{tag}{start}>\n{''.join(self.item(blocks) for blocks in node.items)}</{tag}>\n"

    def item(self, blocks):
        if not blocks:
            return "<li></li>\n"
        if isinstance(blocks[0], Paragraph):
            rest = blocks[1:]
            nested = f"\n{self.blocks(rest)}" if rest else ""
            return f"<li>{self.inline(blocks[0].text)}{nested}</li>\n"
        return f"<li>\n{self.blocks(blocks)}</li>\n"
