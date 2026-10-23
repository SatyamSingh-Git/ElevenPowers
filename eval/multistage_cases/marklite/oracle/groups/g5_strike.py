"""~~text~~ renders as <del>, nests with the other inline styles, and single tildes stay literal."""
from marklite import render


def para(text):
    html = render(text + "\n")
    assert html.startswith("<p>") and html.endswith("</p>\n")
    return html[3:-5]


def test_strikethrough():
    assert para("~~gone~~") == "<del>gone</del>"
    assert para("keep ~~drop this~~ keep") == "keep <del>drop this</del> keep"


def test_nesting_both_ways():
    assert para("~~**old**~~") == "<del><strong>old</strong></del>"
    assert para("**~~old~~**") == "<strong><del>old</del></strong>"
    assert para("~~*a* and `b`~~") == "<del><em>a</em> and <code>b</code></del>"


def test_single_tilde_is_literal():
    assert para("about ~5 km") == "about ~5 km"
    assert para("a ~b~ c") == "a ~b~ c"


def test_unclosed_and_code_are_literal():
    assert para("~~open") == "~~open"
    assert para("`~~x~~`") == "<code>~~x~~</code>"
