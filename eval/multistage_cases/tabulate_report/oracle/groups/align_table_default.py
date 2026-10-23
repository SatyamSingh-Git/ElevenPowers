from tabreport import render_table


def _rule(text):
    return [cell.strip() for cell in text.splitlines()[1].strip().strip("|").split("|")]


def test_plain_numbers_left_aligned_without_align():
    text = render_table(["code", "n"], [["7", "1"], ["0042", "22"], ["123", "$1,000.00"]])
    lines = text.splitlines()
    assert lines[2].startswith("7 ") and lines[2].endswith("  1")
    assert lines[2].index("1") == lines[3].index("22") == lines[4].index("$1,000.00")


def test_markdown_rule_has_no_right_marker_without_align():
    text = render_table(["code", "amount"], [["7", "$1.00"], ["0042", "-$22.50"]], "markdown")
    assert not any(cell.endswith(":") for cell in _rule(text))
    assert "| 7    |" in text


def test_explicit_align_still_right_aligns():
    text = render_table(["code", "n"], [["7", "1"], ["0042", "22"]], "markdown", align=["l", "r"])
    rule = _rule(text)
    assert not rule[0].endswith(":") and rule[1].endswith(":")
    lines = render_table(["code", "n"], [["7", "1"], ["0042", "22"]], align=["l", "r"]).splitlines()
    assert len(lines[2]) == len(lines[3])
