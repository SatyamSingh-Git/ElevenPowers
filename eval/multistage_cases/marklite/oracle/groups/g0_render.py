"""Blocks, inline markup, escaping, link safety, errors, and the command matching the library."""
from html.parser import HTMLParser

import pytest

from marklite import MarkliteError, Options, render
from marklite.cli import main


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


def test_blocks():
    html = render("Hello *world*\nagain\n\n- one\n- two\n  - deep\n\n3. x\n4. y\n\n> quoted\n\n---\n")
    assert "<p>Hello <em>world</em>\nagain</p>\n" in html
    assert "<li>two\n<ul>\n<li>deep</li>\n</ul>\n</li>" in html
    assert '<ol start="3">\n<li>x</li>\n<li>y</li>\n</ol>\n' in html
    assert "<blockquote>\n<p>quoted</p>\n</blockquote>\n" in html
    assert html.endswith("<hr />\n")


def test_fenced_code():
    html = render("```python\nif a < b and c & d:\n    pass\n```\n")
    assert html == '<pre><code class="language-python">if a &lt; b and c &amp; d:\n    pass\n</code></pre>\n'
    assert '<code class="lang-sh">' in render("~~~sh\nls\n~~~\n", Options(code_class_prefix="lang-"))


def test_inline_markup():
    html = render("**b** _e_ `x < y` snake_case_name \\*lit\\* &copy; AT&T <https://e.org>\n")
    assert html == ('<p><strong>b</strong> <em>e</em> <code>x &lt; y</code> snake_case_name *lit* '
                    '&copy; AT&amp;T <a href="https://e.org">https://e.org</a></p>\n')


def test_links_and_images():
    html = render('[the *site*](http://x.org "Home") ![a *b*](p.png)\n')
    assert '<a href="http://x.org" title="Home">the <em>site</em></a>' in html
    assert '<img src="p.png" alt="a b" />' in html


def test_unsafe_urls_are_replaced():
    html = render("[x](javascript:alert(1)) ![y](data:text/html,hi) [m](mailto:a@b.org) [r](/a.html)\n")
    assert [attrs["href"] for attrs in tags(html, "a")] == ["#", "mailto:a@b.org", "/a.html"]
    assert tags(html, "img")[0]["src"] == "#"
    kept = render("[x](javascript:go)\n", Options(safe_links=False))
    assert tags(kept, "a")[0]["href"] == "javascript:go"


def test_attribute_values_cannot_be_broken_out_of():
    html = render('[x](http://a.org/?q="1"onmouseover="go" "say \\"hi\\"")\n\n'
                  '![say "hi"](p.png)\n\n'
                  '```py"onclick="alert(1)\ncode\n```\n')
    link = tags(html, "a")[0]
    assert link == {"href": 'http://a.org/?q="1"onmouseover="go"', "title": 'say "hi"'}
    assert tags(html, "img")[0] == {"src": "p.png", "alt": 'say "hi"'}
    assert tags(html, "code")[0] == {"class": 'language-py"onclick="alert(1)'}


def test_hard_breaks():
    assert render("a\nb\n", Options(hard_breaks=True)) == "<p>a<br />\nb</p>\n"


def test_errors():
    with pytest.raises(MarkliteError) as raised:
        Options(toc_max_level=0)
    assert str(raised.value) == "toc_max_level must be between 1 and 6"
    with pytest.raises(MarkliteError) as raised:
        render("a" * 1_000_001)
    assert str(raised.value) == "input exceeds 1000000 characters"
    assert isinstance(raised.value, ValueError)


def test_command_output_matches_render(tmp_path):
    text = "# Top\n\n[TOC]\n\n## Middle\n\n### Low\n\n#### Lower\n\nSee [x](javascript:x).\n"
    source = tmp_path / "in.md"
    source.write_text(text, encoding="utf-8")
    out = tmp_path / "out.html"
    assert main([str(source), "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == render(text)
    assert main([str(source), "--no-ids", "--unsafe-links", "-o", str(out)]) == 0
    assert out.read_text(encoding="utf-8") == render(text, Options(heading_ids=False, safe_links=False))


def test_command_errors(tmp_path, capsys):
    assert main([str(tmp_path / "missing.md")]) == 1
    assert capsys.readouterr().err.strip() == f"error: cannot read {tmp_path / 'missing.md'}"
    big = tmp_path / "big.md"
    big.write_text("a" * 1_000_001, encoding="utf-8")
    assert main([str(big)]) == 1
    assert capsys.readouterr().err.strip() == "error: input exceeds 1000000 characters"
