"""Quotes stay &quot; inside attribute values while the text around them shows plain quotes."""
from html.parser import HTMLParser
import re

from marklite import Options, render


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []

    def handle_starttag(self, tag, attrs):
        self.tags.append((tag, dict(attrs)))

    handle_startendtag = handle_starttag


def tags(html, name):
    parser = Tags()
    parser.feed(html)
    parser.close()
    return [attrs for tag, attrs in parser.tags if tag == name]


def test_link_attributes_escaped_link_text_plain():
    html = render('[say "hi"](http://x.org/"q" "the \\"t\\"")\n')
    assert 'href="http://x.org/&quot;q&quot;"' in html
    assert 'title="the &quot;t&quot;"' in html
    assert '>say "hi"</a>' in html
    assert tags(html, "a") == [{"href": 'http://x.org/"q"', "title": 'the "t"'}]


def test_image_alt_escaped():
    html = render('![say "hi"](p".png)\n')
    assert 'alt="say &quot;hi&quot;"' in html
    assert 'src="p&quot;.png"' in html
    assert tags(html, "img") == [{"src": 'p".png', "alt": 'say "hi"'}]


def test_code_class_escaped_code_text_plain():
    html = render('```a"b\nx = "1"\n```\n')
    assert 'class="language-a&quot;b"' in html
    assert '>x = "1"\n</code>' in html
    assert tags(html, "code") == [{"class": 'language-a"b'}]


def test_toc_titles_plain_and_ids_intact():
    html = render('[TOC]\n\n# The "best" way\n')
    assert re.search(r'<a href="#[^"]*">The "best" way</a>', html)
    assert re.search(r'<h1 id="[^"]*">The "best" way</h1>', html)


def test_code_class_prefix_with_quote_escaped():
    html = render("```js\nx\n```\n", Options(code_class_prefix='x"y-'))
    assert tags(html, "code") == [{"class": 'x"y-js'}]
    assert 'class="x&quot;y-js"' in html
