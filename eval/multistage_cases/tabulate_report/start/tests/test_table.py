import pytest

from tabreport import ReportError, render_table


def test_plain_table():
    text = render_table(["name", "total"], [["ab", "$1.00"], ["c", "$10.00"]], totals=["TOTAL", "$11.00"])
    assert text == (
        "name    total\n"
        "-----  ------\n"
        "ab      $1.00\n"
        "c      $10.00\n"
        "-----  ------\n"
        "TOTAL  $11.00\n"
    )


def test_markdown_table_escapes_pipes():
    text = render_table(["a", "b"], [["x|y", "1"]], "markdown", align=["l", "r"])
    assert text == (
        "| a    |   b |\n"
        "| ---- | --: |\n"
        "| x\\|y |   1 |\n"
    )


def test_explicit_alignment():
    text = render_table(["a", "b"], [["1", "x"]], align=["l", "r"])
    assert text.splitlines()[2] == "1  x"


def test_none_is_an_empty_cell():
    assert render_table(["a", "b"], [[None, "x"]]).splitlines()[2] == "   x"


@pytest.mark.parametrize("kwargs, message", [
    ({"fmt": "html"}, "unknown format: html"),
    ({"align": ["l"]}, "align needs 'l' or 'r' for each of 2 columns"),
    ({"align": ["l", "c"]}, "align needs 'l' or 'r' for each of 2 columns"),
])
def test_refuses(kwargs, message):
    with pytest.raises(ReportError, match=f"^{message}$"):
        render_table(["a", "b"], [["1", "2"]], **kwargs)


def test_ragged_row():
    with pytest.raises(ReportError, match="^row has 1 cells but the table has 2 columns$"):
        render_table(["a", "b"], [["1"]])
