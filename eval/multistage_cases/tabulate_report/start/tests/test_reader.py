import pytest

from tabreport import Dialect, ReportError, read_csv


def test_reads_rows_keyed_by_header(sales):
    rows = read_csv(sales)
    assert len(rows) == 5
    assert rows[0] == {"region": "East", "product": "Widget", "units": "3", "amount": "1200.50"}
    assert rows[3]["amount"] == "1,000.00"


def test_semicolon_dialect_with_quoted_delimiter(write_csv):
    path = write_csv('name;note\n"Smith; J";late\n')
    assert read_csv(path, Dialect(delimiter=";")) == [{"name": "Smith; J", "note": "late"}]


def test_header_and_cells_are_stripped(write_csv):
    path = write_csv(" a , b \n 1 , x \n")
    assert read_csv(path) == [{"a": "1", "b": "x"}]


def test_blank_lines_kept_when_asked(write_csv):
    path = write_csv("a,b\n1,2\n\n3,4\n")
    assert len(read_csv(path)) == 2
    assert read_csv(path, Dialect(skip_blank=False))[1] == {"a": "", "b": ""}


def test_missing_required_column(sales):
    with pytest.raises(ReportError, match="^missing column: price$"):
        read_csv(sales, required=["region", "price"])


def test_wrong_field_count_names_the_line(write_csv):
    path = write_csv("a,b\n1,2\n3\n")
    with pytest.raises(ReportError, match="^wrong field count: line 3 has 1, expected 2$"):
        read_csv(path)


def test_empty_file(write_csv):
    with pytest.raises(ReportError, match="^empty input: no header row$"):
        read_csv(write_csv("\n\n"))


def test_duplicate_column(write_csv):
    with pytest.raises(ReportError, match="^duplicate column: a$"):
        read_csv(write_csv("a,b,a\n1,2,3\n"))


def test_wrong_encoding(write_csv):
    path = write_csv("name\nJosé\n", encoding="latin-1")
    with pytest.raises(ReportError, match="^cannot decode: .* is not utf-8$"):
        read_csv(path)
    assert read_csv(path, Dialect(encoding="latin-1")) == [{"name": "José"}]


def test_dialect_checks_its_characters():
    with pytest.raises(ReportError, match="^delimiter must be one character, got ';;'$"):
        Dialect(delimiter=";;")
    with pytest.raises(ReportError, match="^delimiter and quotechar must differ$"):
        Dialect(delimiter='"')
