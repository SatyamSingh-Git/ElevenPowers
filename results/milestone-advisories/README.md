# Larger-project milestone advice observations

Runtime at measurement: `3a3ce38`. Source pins and full SHA-256 inventories are
in [the frozen corpus](../../eval/milestone_large_cases.json). Click has 178
sealed files / 1,676,581 bytes, attrs 141 / 2,030,786, and Jinja 108 / 1,177,522;
these include one authored milestone declaration per snapshot. Source is from
the cached upstream commits, with BSD-3-Clause / MIT licenses retained. Selected
whole-file relationships were source-inspected before evaluation. Jinja labels
overlap earlier graph exercises; this is not a blinded test or representative
population. The larger repositories are still small compared with a monorepo.

All six selected required relationships are found. Four of the six queries also
lead to the other declared test behavior. **These are not established false
positives.** The initial label treated distinct behavior as unrelated, but shared
package initialization and transitive dependencies prevent that inference.
Those negative labels are withdrawn and the four leads remain unlabelled.
[Original corpus](original-corpus.json) and
[original observations](original-observations.json) preserve the mistake;
[qualified observations](observations.json) regrade the same command witnesses.
No claim about larger-project precision or zero false leads is supported.

All reports expose incomplete static coverage, including ambiguous/rebound Python
exports. Both pre/post snapshot seals pass. Eighteen sequential paired reads add
median **947.254 ms**, with maximum advised read **1498.692 ms** on this Windows
machine. Commands are declarations only: no upstream tests or model were run.
These measurements do not include host launch, native callbacks or final worker
changes. They support keeping automatic advice opt-in with a timeout; they do
not qualify a universal default or establish coding improvement.

Reproduce by extracting each pinned upstream Git archive into a new disposable
directory and adding the exact `elevenpowers.milestones.json` below. A roots JSON
maps `click`, `attrs`, `jinja2` to those directories. The evaluator verifies every
sealed file and rejects extras before reading advice; hashes in the corpus are
authoritative, including generated declarations.

```sh
python -m eval.milestone_large --corpus eval/milestone_large_cases.json --roots roots.json --output new-observations.json --repeats 3
```

For each project, declaration schema is 1, with two milestones `check-0` and
`check-1`, description `Upstream assertions in TEST_PATH`, inputs `[TEST_PATH]`
and check `{kind: "test_suite", command: "python -m pytest TEST_PATH -q"}`.
Test paths in order: Click `tests/test_parser.py`, `tests/test_formatting.py`;
attrs `tests/test_filters.py`, `tests/test_converters.py`; Jinja
`tests/test_utils.py`, `tests/test_filters.py`. JSON is serialized by
`json.dumps(value, indent=2)` without a trailing newline. The original Windows
declaration has CRLF line endings. Each final corpus project includes its exact
`milestone_declaration` text: write that field with
`Path("elevenpowers.milestones.json").write_bytes(text.encode("utf-8"))` on any OS
to reproduce the original hash. Published observation JSON uses normalized LF;
this changes formatting only, never source seals or measured values. No `.elevenpowers`
directory is needed. Preserve upstream licenses in extracted snapshots.
