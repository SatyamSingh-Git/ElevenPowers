import pytest

from tabreport import ReportError, read_csv


def _write(tmp_path, text):
    path = tmp_path / "data.csv"
    path.write_bytes(text.encode("utf-8"))
    return path


def test_rows_before_a_bad_line_are_handed_out_first(tmp_path):
    rows = read_csv(_write(tmp_path, "a,b\n1,2\n3,4\n\n5\n6,7\n"))
    assert next(rows) == {"a": "1", "b": "2"}
    assert next(rows) == {"a": "3", "b": "4"}
    with pytest.raises(ReportError, match=r"^line 5: expected 2 fields, got 1$"):
        next(rows)


def test_result_is_a_one_pass_iterator(tmp_path):
    rows = read_csv(_write(tmp_path, "a\n1\n2\n3\n"))
    assert iter(rows) is rows
    assert [row["a"] for row in rows] == ["1", "2", "3"]
    assert list(rows) == []


def test_bad_line_late_in_a_file_does_not_stop_early_rows(tmp_path):
    lines = "".join(f"{i},{i}\n" for i in range(1, 50))
    rows = read_csv(_write(tmp_path, f"k,v\n{lines}oops\n"))
    seen = [next(rows) for _ in range(49)]
    assert seen[-1] == {"k": "49", "v": "49"}
    with pytest.raises(ReportError, match=r"^line 51: expected 2 fields, got 1$"):
        next(rows)
