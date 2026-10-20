"""Commit sampling is a pure function of the frozen rule; mining gains a cutoff and an interpreter."""
import os
import subprocess
import sys

import pytest


def test_order_is_a_pure_function_of_seed_and_ids():
    from eval.heldout_sample import order
    items = [("repo", f"{i:040x}") for i in range(20)]
    assert order(items, "s") == order(list(reversed(items)), "s")
    assert order(items, "s") != order(items, "t")


def _sample(per_repo, keep=lambda repo, sha: True, want=40, cap=4):
    from eval.heldout_sample import sample
    return sample(list(per_repo), lambda repo: per_repo[repo],
                  lambda repo, sha: ({"name": f"{repo}-{sha}"}, "kept") if keep(repo, sha) else (None, "rejected for test"),
                  seed="s", want=want, cap=cap)


def test_a_repository_contributes_at_most_cap_tasks_in_ranking_order():
    kept, _ = _sample({"a": [f"a{i}" for i in range(9)], "b": [f"b{i}" for i in range(9)]}, want=6)
    assert [k["name"].split("-")[0] for k in kept] == ["a"] * 4 + ["b"] * 2


def test_rejected_candidates_and_unusable_repositories_are_retained_with_reasons():
    kept, rejections = _sample({"a": None, "b": ["b1", "b2"]}, keep=lambda repo, sha: sha == "b2")
    assert [k["name"] for k in kept] == ["b-b2"]
    assert {"repo": "a", "sha": "", "reason": "repository unusable"} in rejections
    assert {"repo": "b", "sha": "b1", "reason": "rejected for test"} in rejections


def test_sampling_stops_at_want():
    kept, _ = _sample({"a": ["a1", "a2"], "b": ["b1", "b2"], "c": ["c1"]}, want=3)
    assert len(kept) == 3


def _repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    run = lambda *a, date=None: subprocess.run(["git", "-C", str(repo), *a], check=True, capture_output=True,
                                               env={**os.environ, **({"GIT_AUTHOR_DATE": date, "GIT_COMMITTER_DATE": date} if date else {})})
    run("init", "-q")
    for name, date in (("old", "2026-01-01T00:00:00"), ("new", "2026-07-01T00:00:00")):
        (repo / "src").mkdir(exist_ok=True)
        (repo / "tests").mkdir(exist_ok=True)
        (repo / "src" / f"{name}.py").write_text("x = 1\n")
        (repo / "tests" / f"test_{name}.py").write_text("def test_x():\n    pass\n")
        run("add", ".")
        run("-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", f"fix {name}", date=date)
    return repo


def test_candidates_since_excludes_commits_before_the_cutoff(tmp_path):
    from eval.mine import candidates
    repo = _repo(tmp_path)
    everything = candidates(repo, 50, "src/", "tests/")
    recent = candidates(repo, 50, "src/", "tests/", since="2026-06-01")
    assert len(everything) == 2 and len(recent) == 1


def test_run_tests_uses_the_given_interpreter(tmp_path):
    from eval.mine import run_tests
    assert run_tests(tmp_path, [], {}, python=sys.executable)[0] in (0, 4, 5)
    with pytest.raises(OSError):
        run_tests(tmp_path, [], {}, python=str(tmp_path / "no-such-python"))


def test_progress_is_reported_after_every_repository():
    from eval.heldout_sample import sample
    seen = []
    sample(["a", "b"], {"a": ["a1"], "b": None}.get, lambda repo, sha: ({"name": sha}, "kept"),
           seed="s", want=40, cap=4, progress=lambda kept, rejections: seen.append((len(kept), len(rejections))))
    assert seen == [(1, 0), (1, 1)]


def test_no_further_repository_is_prepared_once_want_is_reached():
    from eval.heldout_sample import sample
    prepared = []

    def candidates_for(repo):
        prepared.append(repo)
        return [repo + "1"]

    sample(["a", "b", "c"], candidates_for, lambda repo, sha: ({"name": sha}, "kept"), seed="s", want=1, cap=4)
    assert prepared == ["a"]


def test_a_suite_timeout_rejects_the_rest_of_that_repository_and_moves_on():
    from eval.heldout_sample import sample
    calls = []

    def check(repo, sha):
        calls.append(sha)
        if repo == "slow":
            raise subprocess.TimeoutExpired(["pytest"], 120)
        return {"name": sha}, "kept"

    kept, rejections = sample(["slow", "fast"], {"slow": ["s1", "s2", "s3"], "fast": ["f1"]}.get, check,
                              seed="s", want=40, cap=4)
    assert [k["name"] for k in kept] == ["f1"]
    assert len([c for c in calls if c.startswith("s")]) == 1
    assert {"repo": "slow", "sha": calls[0], "reason": "suite exceeded the mining timeout; repository skipped"} in rejections


def test_a_repository_whose_preparation_times_out_is_recorded_and_skipped():
    from eval.heldout_sample import sample

    def candidates_for(repo):
        if repo == "slow":
            raise subprocess.TimeoutExpired(["pip"], 900)
        return ["f1"]

    kept, rejections = sample(["slow", "fast"], candidates_for, lambda repo, sha: ({"name": sha}, "kept"),
                              seed="s", want=40, cap=4)
    assert [k["name"] for k in kept] == ["f1"]
    assert {"repo": "slow", "sha": "", "reason": "repository preparation timed out"} in rejections
