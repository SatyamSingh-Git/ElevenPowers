"""The architecture graph must draw every module; a listed data folder covers its contents."""
import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("architecture_check", ROOT / "architecture" / "check.py")
check = importlib.util.module_from_spec(spec)
spec.loader.exec_module(check)


def test_the_graph_draws_every_module_and_listed_data_folder():
    assert check.uncovered(check.graph()) == []


def test_without_its_node_the_multistage_code_and_cases_are_reported():
    g = check.graph()
    g = {**g, "nodes": [n for n in g["nodes"] if n["id"] != "eval-multistage"]}
    missing = check.uncovered(g)
    assert "eval/multistage_oracles.py is not on the graph" in missing
    assert any(m.startswith("eval/multistage_cases/tinyroute/") for m in missing)


def test_a_folder_listed_without_its_slash_does_not_cover_its_contents():
    g = check.graph()
    nodes = [dict(n, files=[f.rstrip("/") for f in n["files"]]) for n in g["nodes"]]
    assert any(m.startswith("eval/multistage_cases/") for m in check.uncovered({**g, "nodes": nodes}))
