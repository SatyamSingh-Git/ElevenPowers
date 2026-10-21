"""Commit sampling is a pure function of the frozen rule; mining gains a cutoff and an interpreter."""
import json
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
           seed="s", want=40, cap=4, progress=lambda kept, rejections, processed: seen.append((len(kept), len(rejections))))
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


def test_until_excludes_a_later_commit(tmp_path):
    from eval.mine import candidates
    repo = _repo(tmp_path)
    (repo / "src" / "late.py").write_text("x = 1\n")
    (repo / "tests" / "test_late.py").write_text("def test_x():\n    pass\n")
    late = {**os.environ, "GIT_AUTHOR_DATE": "2026-10-21T12:00:00+00:00", "GIT_COMMITTER_DATE": "2026-10-21T12:00:00+00:00"}
    subprocess.run(["git", "-C", str(repo), "add", "."], check=True, capture_output=True)
    subprocess.run(["git", "-C", str(repo), "-c", "user.name=t", "-c", "user.email=t@example.invalid", "commit", "-qm", "fix late"],
                   check=True, capture_output=True, env=late)
    bounded = candidates(repo, 50, "src/", "tests/", since="2026-06-01", until="2026-10-20T00:00:00+00:00")
    assert len(bounded) == 1
    assert len(candidates(repo, 50, "src/", "tests/", since="2026-06-01")) == 2


def test_every_repository_is_journaled_as_processed_including_a_timed_out_one():
    from eval.heldout_sample import sample
    seen = []

    def candidates_for(repo):
        if repo == "slow":
            raise subprocess.TimeoutExpired(["pip"], 900)
        return ["f1"]

    sample(["slow", "fast"], candidates_for, lambda repo, sha: ({"name": sha}, "kept"), seed="s", want=40, cap=4,
           progress=lambda kept, rejections, processed: seen.append(list(processed)))
    assert seen == [["slow"], ["slow", "fast"]]


def test_resume_skips_processed_repositories_and_keeps_their_tasks():
    from eval.heldout_sample import sample
    prepared = []

    def candidates_for(repo):
        prepared.append(repo)
        return [repo + "1"]

    journal = {"processed": ["a"], "tasks": [{"name": "a-a1", "url": "a"}], "rejections": [{"repo": "a", "sha": "x", "reason": "r"}]}
    kept, rejections = sample(["a", "b"], candidates_for, lambda repo, sha: ({"name": sha, "url": repo}, "kept"),
                              seed="s", want=40, cap=4, resume=journal)
    assert prepared == ["b"]
    assert [k["name"] for k in kept] == ["a-a1", "b1"] and rejections == journal["rejections"]


def test_resume_refuses_changed_rule_values(tmp_path):
    from eval.heldout_sample import resumed
    rule = {"seed": "x", "since": "2026-06-01", "until": "u", "want": 40, "cap": 4, "limit": 400}
    path = tmp_path / "corpus.json"
    assert resumed(path, rule) is None
    path.write_text(json.dumps({**rule, "processed": ["a"], "tasks": [], "rejections": []}), encoding="utf8")
    assert resumed(path, rule)["processed"] == ["a"]
    with pytest.raises(ValueError):
        resumed(path, {**rule, "seed": "y"})


def test_a_failed_journal_write_keeps_the_previous_journal(tmp_path):
    from eval.preservation import _write
    path = tmp_path / "corpus.json"
    _write(path, {"tasks": ["first"]})
    with pytest.raises(ValueError):
        _write(path, {"tasks": [float("nan")]})
    assert json.loads(path.read_text(encoding="utf8")) == {"tasks": ["first"]}


def test_low_disk_stops_before_the_next_repository():
    from eval.heldout_sample import LowDisk, sample
    prepared, seen, room = [], [], iter([True, False])

    def candidates_for(repo):
        prepared.append(repo)
        return [repo + "1"]

    with pytest.raises(LowDisk):
        sample(["a", "b"], candidates_for, lambda repo, sha: ({"name": sha}, "kept"), seed="s", want=40, cap=4,
               progress=lambda kept, rejections, processed: seen.append(list(processed)), room=lambda: next(room))
    assert prepared == ["a"] and seen == [["a"]]


def _dirs(work, *names):
    for name in names:
        for kind in ("repos", "venvs"):
            (work / kind / name).mkdir(parents=True)
            (work / kind / name / "f").write_text("x")


def test_prune_keeps_repositories_with_kept_tasks(tmp_path):
    from eval.heldout_sample import prune
    _dirs(tmp_path, "a", "b", "c")
    removed = prune(tmp_path, ["https://x/a", "https://x/b"], [{"url": "https://x/a"}])
    assert removed == ["b"]
    assert sorted(p.name for p in (tmp_path / "repos").iterdir()) == ["a", "c"]
    assert sorted(p.name for p in (tmp_path / "venvs").iterdir()) == ["a", "c"]


def test_prune_removes_read_only_git_objects(tmp_path):
    import stat
    from eval.heldout_sample import prune
    _dirs(tmp_path, "b")
    locked = tmp_path / "repos" / "b" / "f"
    locked.chmod(stat.S_IREAD)
    assert prune(tmp_path, ["https://x/b"], []) == ["b"]
    assert not (tmp_path / "repos" / "b").exists()


def test_a_partial_clone_is_discarded(tmp_path):
    from eval.heldout_sample import clone
    source = _repo(tmp_path)
    into = tmp_path / "clones" / "repo"
    stale = into.with_name("repo.partial")
    stale.mkdir(parents=True)
    (stale / "junk").write_text("half a clone")
    assert clone(str(source), into)
    assert (into / "src" / "new.py").exists() and not stale.exists()
    assert not clone(str(tmp_path / "missing"), tmp_path / "clones" / "other")
    assert not (tmp_path / "clones" / "other").exists()


def test_a_repository_listed_twice_is_mined_once():
    from eval.heldout_sample import sample
    prepared = []

    def candidates_for(repo):
        prepared.append(repo)
        return [repo + "1"]

    kept, _ = sample(["a", "a", "b"], candidates_for, lambda repo, sha: ({"name": sha}, "kept"), seed="s", want=40, cap=4)
    assert prepared == ["a", "b"] and [k["name"] for k in kept] == ["a1", "b1"]
