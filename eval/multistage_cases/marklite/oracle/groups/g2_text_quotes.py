"""Double quotes in text content come out as plain quotes; & < > are still escaped."""
from marklite import render


def test_paragraph_quotes():
    assert render('She said "hi"\n') == '<p>She said "hi"</p>\n'


def test_other_characters_still_escaped():
    assert render('a < b & c > d "e"\n') == '<p>a &lt; b &amp; c &gt; d "e"</p>\n'


def test_heading_and_list_quotes():
    html = render('# The "best" way\n\n- say "yes"\n\n> "quoted"\n')
    assert '>The "best" way</h1>' in html
    assert '<li>say "yes"</li>' in html
    assert '<p>"quoted"</p>' in html
    assert "&quot;" not in html


def test_code_quotes():
    assert render('`a="b"`\n') == '<p><code>a="b"</code></p>\n'
    assert render('```\nprint("x" < 1)\n```\n') == '<pre><code>print("x" &lt; 1)\n</code></pre>\n'


def test_emphasis_and_link_text_quotes():
    html = render('*"a"* **"b"** ["c"](/x)\n')
    assert html == '<p><em>"a"</em> <strong>"b"</strong> <a href="/x">"c"</a></p>\n'
