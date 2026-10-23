"""The oracle gap read from a held-out sweep's records rather than from bundles."""
import json

from eval.pool import measure, pools, records


def _sweep(tmp_path, rows):
    sweep = tmp_path / "sweep-x"
    sweep.mkdir()
    path = sweep / "collected.json"
    path.write_text(json.dumps([
        {"slot": f"{task}--{arm}--{n}", "task": task, "arm": arm, "state": state, "outcome": outcome,
         "vacuous": vacuous, "host_version": "2.1.292 (Claude Code)"}
        for task, arm, n, state, outcome, vacuous in rows]), encoding="utf8")
    return path


ROWS = [
    ("a", "ordinary", 0, "graded", "resolved", True),
    ("a", "ordinary", 1, "graded", "unfixed", None),
    ("a", "ordinary", 2, "graded", "resolved", False),
    ("b", "ordinary", 0, "graded", "resolved", True),
    ("b", "ordinary", 1, "closed_book_breach", "resolved", None),
    ("b", "ordinary", 2, "running", None, None),
]


def test_only_graded_runs_join_a_pool(tmp_path):
    got = measure(pools(records(_sweep(tmp_path, ROWS))), "sweep-x", "ordinary")
    assert (got["tasks"], got["attempts"], got["mixed"]) == (2, 4, 1)
    assert got["coverage"] == 1.0
    assert got["random_pick"] == (2 / 3 + 1) / 2


def test_a_pinned_pool_counts_a_vacuous_resolution_as_no_success(tmp_path):
    got = measure(pools(records(_sweep(tmp_path, ROWS), pinned=True)), "sweep-x", "ordinary")
    assert got["coverage"] == 0.5
    assert got["random_pick"] == (1 / 3 + 0) / 2


def test_a_records_file_is_reported_without_the_open_book_caveat(tmp_path, capsys):
    from eval.pool import report
    assert report([_sweep(tmp_path, ROWS)]) == 0
    out = capsys.readouterr().out
    assert "4 graded attempts" in out
    assert "answer access" not in out


def test_one_host_version_is_one_condition(tmp_path):
    got = measure(pools(records(_sweep(tmp_path, ROWS))), "sweep-x", "ordinary")
    assert got["conditions"] == 1
