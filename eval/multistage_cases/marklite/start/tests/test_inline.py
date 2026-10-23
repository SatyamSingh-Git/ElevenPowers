from marklite import Options, render


def inline(text, options=None):
    html = render(text, options)
    assert html.startswith("<p>") and html.endswith("</p>\n")
    return html[3:-5]


def test_emphasis_and_strong():
    assert inline("*a* **b** _c_ __d__") == "<em>a</em> <strong>b</strong> <em>c</em> <strong>d</strong>"


def test_nested_emphasis():
    assert inline("**bold *and* more**") == "<strong>bold <em>and</em> more</strong>"


def test_underscores_inside_words_are_literal():
    assert inline("snake_case_name") == "snake_case_name"


def test_unmatched_delimiters_are_literal():
    assert inline("2 * 3 and *open") == "2 * 3 and *open"


def test_code_span_is_escaped_and_not_parsed():
    assert inline("`a < *b*`") == "<code>a &lt; *b*</code>"


def test_double_backtick_code_span():
    assert inline("``a ` b``") == "<code>a ` b</code>"


def test_backslash_escapes():
    assert inline(r"\*not em\*") == "*not em*"


def test_text_is_escaped():
    assert inline("a < b & c > d") == "a &lt; b &amp; c &gt; d"


def test_known_entities_pass_through():
    assert inline("&copy; &#169; &#xA9; &bogus;") == "&copy; &#169; &#xA9; &amp;bogus;"


def test_link_with_title():
    assert inline('[the *site*](http://x.org "Home")') == '<a href="http://x.org" title="Home">the <em>site</em></a>'


def test_link_url_with_parentheses():
    assert inline("[w](http://x.org/a_(b))") == '<a href="http://x.org/a_(b)">w</a>'


def test_image():
    assert inline("![a *b*](p.png)") == '<img src="p.png" alt="a b" />'


def test_autolink():
    assert inline("<https://x.org>") == '<a href="https://x.org">https://x.org</a>'


def test_unsafe_schemes_are_replaced():
    assert inline("[x](javascript:alert(1))") == '<a href="#">x</a>'
    assert inline("[x]( JavaScript:alert(1))") == '<a href="#">x</a>'
    assert inline("![x](data:image/png;base64,AAA)") == '<img src="#" alt="x" />'


def test_safe_and_relative_urls_are_kept():
    assert inline("[a](mailto:me@x.org) [b](/docs/a.html) [c](#top)") == (
        '<a href="mailto:me@x.org">a</a> <a href="/docs/a.html">b</a> <a href="#top">c</a>')


def test_unsafe_links_option_keeps_any_scheme():
    assert inline("[x](javascript:go)", Options(safe_links=False)) == '<a href="javascript:go">x</a>'


def test_hard_breaks_option():
    assert inline("a\nb", Options(hard_breaks=True)) == "a<br />\nb"
    assert inline("a\nb") == "a\nb"
