# Reverted-tree discrimination and runner provenance — 2026-10-10

Base `b835f97`, on `main`. No model call, no paid run, no new dependency. See
[results](../../results/reverted/README.md).

**Why.** Re-running a saved check on its base tree was the planned $0 answer to
P22. Before building it, the 22 distinct corpus base trees were re-collected
under the installed pytest 9.1.1: 4 collected cleanly. attrs failed 8/8 on a
missing `hypothesis`; click 8/10 and itsdangerous 2/2 failed collection, click's
on `tests/test_basic.py`, a file its saved patch never touches, where the
original run had collected and passed 1,259 tests. Manifests recorded python,
platform, claude and git — never the runner. A selected agent-written test
re-run on its base tree exited 4, `not found`: a naive reversion check would
have counted it as discriminating.

**Provenance (`fafe61a`).** `eval/live.py:environment()` adds `tools` —
pytest/ruff/mypy through the harness interpreter, which workspace venvs inherit,
and node/npm from PATH — in `core/hosts/probes.py`'s state shape, plus
`packages`. Not that module's parser: run against the real producers, it read
node's `v22.17.1` and an absent module as `incomplete`. Witnessed RED (missing
key/attribute) before GREEN. Five mutations caught, including a PATH `pytest`
substituted for the interpreter's, which survived until a decoy `pytest` was put
first on PATH. Live record: 0.63 s and about 1.3 KB per manifest.

**Measurement (`348fa84`).** `eval/reverted.py` composes `materialise`,
`bundle.apply_patch`, the runtime's `parse` and `TEST_NAME`, and stress's
states. Two corrections came from running the producer: the runtime parser
counts pytest's `1 error` as a failed test, so collection errors are read first;
and stress's `COLLECT_ERROR` also matches setup errors (`ERROR x.py::test_a`), so
labelling uses a stricter pattern. 22 controls on real repositories, real
patches and real pytest; sixteen mutations, each caught — the last after adding
the fixture-setup-error control it exposed.

**Sweep (`bac2908`).** 54 ledgers, 2,017 records → 432 passing → 200 test records
that ran tests → 62 re-executable → 44 checks from 28 bundles: 16 discriminate,
7 vacuous, 21 uncheckable, every one of the 21 with a named environment cause.
Six of seven vacuous checks come from patches touching no test.

```sh
python -m pytest tests/test_reverted.py tests/test_audit_probes.py -q
python -m eval.reverted --bundles results --out NEW_DIRECTORY
python architecture/check.py --render
python -m pytest -q
```

Limits: every run is the unrecorded-toolchain stratum; checks cluster by task;
attrs is uncovered because installing `hypothesis` would change the environment
future runs inherit. The runtime is unchanged — this is evaluation tooling.
