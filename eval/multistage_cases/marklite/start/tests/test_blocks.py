from marklite import parse, render
from marklite.blocks import CodeBlock, Heading, ListBlock, Paragraph, Quote, Rule


def test_paragraphs_are_separated_by_blank_lines():
    assert render("one\ntwo\n\nthree\n") == "<p>one\ntwo</p>\n<p>three</p>\n"


def test_heading_levels_and_closing_hashes():
    document = parse("# One #\n###### Six\n####### seven\n#nospace\n")
    assert [type(node) for node in document.children] == [Heading, Heading, Paragraph]
    assert (document.children[0].level, document.children[0].text) == (1, "One")
    assert document.children[1].level == 6
    assert document.children[2].text == "####### seven\n#nospace"


def test_heading_keeps_trailing_hash_that_is_part_of_a_word():
    assert parse("## C#\n").children[0].text == "C#"


def test_fenced_code_keeps_content_verbatim():
    html = render("```python\nif a < b:\n    pass\n```\n")
    assert html == '<pre><code class="language-python">if a &lt; b:\n    pass\n</code></pre>\n'


def test_unclosed_fence_runs_to_the_end():
    document = parse("~~~\ncode\n")
    assert document.children == [CodeBlock("", "code\n", 1)]


def test_code_class_prefix_option():
    from marklite import Options

    html = render("```js\nx\n```\n", Options(code_class_prefix="lang-"))
    assert '<code class="lang-js">' in html


def test_blockquote_with_lazy_continuation():
    document = parse("> a\nb\n\nc\n")
    quote = document.children[0]
    assert isinstance(quote, Quote)
    assert quote.children == [Paragraph("a\nb", 1)]
    assert document.children[1] == Paragraph("c", 4)


def test_nested_lists():
    html = render("- a\n  - b\n- c\n")
    assert html == "<ul>\n<li>a\n<ul>\n<li>b</li>\n</ul>\n</li>\n<li>c</li>\n</ul>\n"


def test_ordered_list_start():
    document = parse("7. x\n8. y\n")
    assert isinstance(document.children[0], ListBlock)
    assert render("7. x\n8. y\n") == '<ol start="7">\n<li>x</li>\n<li>y</li>\n</ol>\n'


def test_list_items_separated_by_blank_lines_stay_in_one_list():
    document = parse("- a\n\n- b\n")
    assert len(document.children) == 1
    assert len(document.children[0].items) == 2


def test_rules():
    assert [type(node) for node in parse("***\n- - -\n___\n").children] == [Rule, Rule, Rule]


def test_line_numbers_are_one_based():
    document = parse("\n# Title\n\ntext\n")
    assert [node.line for node in document.children] == [2, 4]
