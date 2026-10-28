# Multi-stage v3 Build Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the $0 machinery and the first two v3 cases (bigger projects with quiet dependents), then run the gated pilot and the blind headroom classifier.

**Architecture:** v3 reuses v2's runner, oracles and rehearsal. Each case declares a `profile` (`v2` default, `v3`), so the loader enforces each profile's own stage rules, and nothing is hard-coded at six stages. A new module, `eval/multistage_quiet.py`, extracts a reference diff's changed names and checks that a declared quiet dependent's file names none of them. The rehearsal adds three checks per quiet dependent.

**Tech Stack:** Python 3.11+ standard library (`ast`, `tokenize`, `re`), pytest, git.

**Spec:** `docs/superpowers/specs/2026-10-28-multistage-v3-harder-cases-design.md`

## Global Constraints

- **Profile v2:** 6 stages, at least 4 cross-cutting, at least 1 self-contained. Unchanged behaviour; every existing v2 test stays green.
- **Profile v3:**
  - 8 stages; at least 5 cross-cutting, at least 1 self-contained, at least 1 `bugfix`.
  - Every cross-cutting stage has at least 1 `quiet` entry.
  - Each entry has `file`, `kind` (one of `key`, `data`, `copy`, `contract`), `path`, `diff`, `fails`. `fails` must be non-empty and name earlier groups still required at that stage.
  - At least 2 distinct kinds per case.
- **Placeholders:** `{anything}` in a documented value compares as `{}`. This applies to both profiles.
- **Changed names** for a stage:
  - every function, method or class whose definition overlaps a changed line of the reference diff (found with `ast` on the stage n-1 tree);
  - module-level names assigned on a changed line;
  - identifiers (via `tokenize`) and string literals of 3+ characters that appear on `-` lines and on no `+` line.

  Hunks in the quiet dependent's own file are excluded. The match is a whole-word regex over the dependent file's raw text in the stage n-1 tree.
- **Quiet suite check:** the public suite (`python -m pytest <test_dir> -q`) passes on the quiet-missed tree.
- **Locations:** v3 cases in `eval/multistage_v3/`, records in `results/multistage-v3/`; `.gitattributes` keeps `eval/multistage_v3/** -text`.
- **Stage turn and model:** 900 s, Sonnet 5.5 medium, the same runner as v2.
- **Python floor:** changed files compile on `py -3.11`.
- **Never heredoc backslashes;** use Write or Edit.

## Review Focus

1. A quiet dependent that is not Python, such as a JSON registry holding the changed name as a string, must count as found. Test in Task 3.
2. A reference diff that adds a file with no stage n-1 version must not crash the name extraction. Test in Task 3.
3. A name renamed in place (on both `-` and `+` lines) is not net-removed, but the definition it sits in still counts. Test in Task 3.
4. Placeholders with format specs (`{rate:.1f}`) normalise like plain ones. Test in Task 1.
5. A quiet diff that does not apply makes the case unusable with the diff named, rather than crashing the rehearsal. Test in Task 3.

---

### Task 1: Placeholder names are not graded

**Files:**
- Modify: `eval/multistage_oracles.py` (`stale`)
- Test: `tests/test_multistage_oracles.py`

**Interfaces:** Produces `stale(case, stage, tree) -> list[str]` with an unchanged signature. Values compare after `re.sub(r'\{[^{}]*\}', '{}', value)` on both sides.

- [ ] **Step 1: Write the failing tests.**
  - `test_a_renamed_placeholder_is_not_stale`: on a stage-2 reference tree, rewrite the `default` row's value to `{n}`. Use a case whose fact value is `{m}`, built by patching `case['facts'][2]['default']` in a copy. Assert `stale(...) == []`.
  - `test_placeholders_with_format_specs_normalise`: `{rate:.1f}` and `{r}` match.
  - `test_placeholder_text_still_has_to_match`: `x {a}` against `y {a}` is stale.
- [ ] **Step 2:** Run `python -m pytest tests/test_multistage_oracles.py -q`. Expected: the first two FAIL.
- [ ] **Step 3:** Implement the normalisation in `stale` for both the documented and the expected values.
- [ ] **Step 4:** Run the tests and check they pass. Mutation-check that removing normalisation on either side turns a test red.
- [ ] **Step 5:** Commit and push: `eval: placeholder names are not graded`.

### Task 2: Profiles, quiet entries and a v3 fixture

**Files:**
- Modify: `eval/multistage_cases.py`, replacing `STAGES`/`CROSS_CUTTING`/`SELF_CONTAINED` with `PROFILES`.
- Modify: `eval/multistage_rehearse.py` and `eval/multistage_run.py`: every `STAGES` use becomes `len(case['stages'])`.
- Modify: `tests/multistage_fixture.py`, adding `make_v3_case(root) -> Path`.
- Test: `tests/test_multistage_cases.py`.

**Interfaces:**
- **Produces:**
  - `PROFILES = {'v2': {'stages': 6, 'cross_cutting': 4, 'self_contained': 1, 'bugfix': 0, 'quiet': False}, 'v3': {'stages': 8, 'cross_cutting': 5, 'self_contained': 1, 'bugfix': 1, 'quiet': True}}`;
  - `load(root)` returns `case` with `case['profile']`;
  - `tree(case, stage, folder, variant='reference', which=0)`, where `variant='quiet'` applies `stage['quiet'][which]['diff']` on the stage reference.
- **The v3 fixture** has 8 stages.
  - **Stages 1–5** are cross-cutting. Each changes `core.SEP`, the separator `core.record(x)` writes between `x` and `DEFAULT`, and `DEFAULT`. The reference updates `parse.py`'s own `SEP_IN`, a second copy, so `parse.read(core.record(3)) == 3`.
  - **Each quiet entry** reverts `parse.py`'s `SEP_IN` to the previous stage's, with `fails: ['roundtrip']`. Kinds: stages 1–3 `copy`, stages 4–5 `data`.
  - **Separators** are `',', ';', '|', ':', '/', '#'` for stages 0–5.
  - **Stage 6** is a self-contained bug fix that adds `extra_v6` and a test. **Stages 7 and 8** are self-contained additions.
  - **Groups:** the base groups are `roundtrip` (0–8) and `generated` (0–8). Each stage adds two groups that are only valid at that stage.
  - **Public tests** never touch `parse`.

- [ ] **Step 1: Write the failing tests.**
  - `test_the_v3_fixture_loads` asserts `profile == 'v3'` and 8 stages.
  - `test_v2_cases_still_load` asserts profile `v2`.
  - `test_each_v3_rule_is_refused` is parametrised. Each case breaks one rule and expects a match on the message:
    - 7 stages;
    - 4 cross-cutting;
    - no bug fix;
    - a cross-cutting stage without `quiet`;
    - an unknown kind;
    - one kind only;
    - `fails` naming a later group;
    - a missing quiet diff.
  - `test_quiet_variant_reverts_only_the_dependent`: the quiet tree differs from the reference only in `src/pkg/parse.py`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement `PROFILES`, the profile rules in `load`, and the `quiet` variant in `tree`. Replace every `STAGES` import.
- [ ] **Step 4:** Run `tests/test_multistage_cases.py`, `test_multistage_oracles.py`, `test_multistage_rehearse.py` and `test_multistage_run.py`. All pass.
- [ ] **Step 5:** Mutation-check: drop each v3 rule in turn; each must turn a test red.
- [ ] **Step 6:** Commit and push: `eval: case profiles, v3 quiet dependents`.

### Task 3: The quiet checks

**Files:**
- Create: `eval/multistage_quiet.py`.
- Modify: `eval/multistage_rehearse.py`.
- Test: `tests/test_multistage_quiet.py` and `tests/test_multistage_rehearse.py`.

**Interfaces:**
- **Produces:**
  - `changed_names(diff: str, before: Path, exclude: str) -> set[str]`, following the rule in Global Constraints;
  - `named(names: set[str], path: Path) -> list[str]`, the names found whole-word in the file's text, sorted;
  - `suite_passes(tree: Path, case) -> bool`, which runs the public suite with `cwd=tree` and 300 s.
- **Rehearsal checks:** for v3 cases, the rehearsal adds per quiet entry `k` of stage n:
  - `quiet_fails[k]`: the earlier groups failing on the quiet tree equal `fails`;
  - `quiet_suite_green[k]`;
  - `quiet_unnamed[k]`: `named(changed_names(reference diff, stage n-1 tree, entry file), stage n-1 tree / entry file) == []`.

  A diff that does not apply records `quiet_fails[k] = False`, with the error in `detail`.

- [ ] **Step 1: Write the failing tests in `test_multistage_quiet.py`.**
  - `test_a_changed_function_is_a_changed_name`: a diff edits the body of `def total`, so `'total'` is in the result.
  - `test_a_renamed_identifier_is_net_removed_only_when_gone` covers `old_name` to `new_name`, and a name on both sides.
  - `test_short_literals_are_ignored_and_long_ones_kept`: `','` is ignored, `'format_money'` is kept.
  - `test_a_module_constant_changed_is_a_changed_name`: `SEP = ','` becomes `SEP = ';'`, so `'SEP'` is in the result.
  - `test_a_new_file_in_the_diff_does_not_crash`.
  - `test_the_dependents_own_hunks_are_excluded`.
  - `test_a_json_registry_naming_it_is_found`: `named({'format_money'}, registry.json)` returns `['format_money']`.
  - `test_whole_words_only`: `SEP` is not found in `SEP_IN = 1`.
- [ ] **Step 2: Write the failing tests in `test_multistage_rehearse.py`.**
  - `test_the_v3_fixture_rehearses_usable`.
  - `test_a_quiet_dependent_the_suite_catches_is_unusable`: add a public test calling `parse.read` at stage 2, so `quiet_suite_green` is False.
  - `test_a_quiet_dependent_that_names_the_change_is_unusable`: make `parse.py` import and use `core.SEP` at stage 3, so `quiet_unnamed` is False.
  - `test_a_quiet_diff_that_does_not_apply_is_unusable`.
- [ ] **Step 3:** Run the tests. Expected: FAIL.
- [ ] **Step 4:** Implement `multistage_quiet.py` and the rehearsal checks.
- [ ] **Step 5:** Run the tests until they pass. Run the 20-mutation style check on the new module: drop each name source, flip whole-word matching, drop the exclusion. Each must be killed.
- [ ] **Step 6:** Commit and push: `eval: rehearsal proves each quiet dependent is quiet`.

### Task 4: The runner takes any case set

**Files:**
- Modify: `eval/multistage_run.py`.
- Test: `tests/test_multistage_run.py`.

**Interfaces:**
- `prepare(...)` records `'manifest': str(Path(manifest).absolute())`.
- `_breaches` withholds the cases root, the manifest's folder and the public repository name.
- `collect` derives the stage count from the loaded case.
- The CLI `prepare` gains `--cases-root` and `--manifest`, defaulting to v2's.

- [ ] **Step 1: Write the failing tests.**
  - `test_a_v3_case_runs_all_eight_stages`, with the reference fake host on `make_v3_case`.
  - `test_reading_the_manifest_folder_is_a_breach`.
- [ ] **Step 2:** Run the tests. Expected: FAIL.
- [ ] **Step 3:** Implement the changes.
- [ ] **Step 4:** Run the tests until they pass, then mutation-check.
- [ ] **Step 5:** Commit and push: `eval: the runner takes any case set`.

### Task 5: The v3 brief and folders

**Files:**
- Create: `eval/multistage_v3/AUTHORING.md`, from v2's brief, carrying the spec's size, eight stages, the quiet-dependent table, the declared entries, both checks, both fairness rules and the anti-goals.
- Create: `eval/multistage_v3/conftest.py`, holding `collect_ignore_glob = ["*"]`.
- Modify: `.gitattributes`, to add `eval/multistage_v3/** -text`.
- Modify: `architecture/index.html`.

- [ ] **Step 1:** Write the brief. It names only the files an author may read: the brief, `eval/multistage_cases.py`, `eval/multistage_oracles.py`, `eval/multistage_quiet.py` and `eval/multistage_rehearse.py`.
- [ ] **Step 2:** Update the graph node to v3, then run `python architecture/check.py --render`. Expected: `OK`.
- [ ] **Step 3:** Commit and push: `eval: v3 authoring brief`.

### Task 6: Two cases

- [ ] **Step 1:** Dispatch two fresh authors in parallel, each with the brief and a distinct domain. One has a persisted format read by another module; one is a domain unlike any v2 case. Each must leave `python -m eval.multistage_rehearse --cases eval/multistage_v3 --case <id> --out <scratch>` exiting 0.
- [ ] **Step 2:** Run one fresh reviewer per case. It gets the three fairness questions, the surface rule, and "is each quiet dependent findable, and by what path?". Blocking findings go back to the author, and the rehearsal is rerun.
- [ ] **Step 3:** Rehearse both from a fresh CRLF clone and write `results/multistage-v3/rehearsal.json` and `review.json`.
- [ ] **Step 4:** Freeze. `results/multistage/freeze.py` gains `--cases-dir` and `--pilot` arguments; v2's output is unchanged when they are omitted. Write `results/multistage-v3/manifest.json` with both cases as the pilot.
- [ ] **Step 5:** Commit and push each step's output.

### Task 7: Pilot and gate (paid, authorized)

- [ ] **Step 1:** Seal the batch:

  ```
  python -m eval.multistage_run prepare --batch E:/ep-runs/multistage-v3-pilot-<date> --cases-root eval/multistage_v3 --manifest results/multistage-v3/manifest.json --cases <a> <b> --replicates 1
  ```

  Then copy the protocol to `results/multistage-v3/` and push.
- [ ] **Step 2:** Execute the four slots, each as its own tracked background task.
- [ ] **Step 3:** Collect into `results/multistage-v3/pilot-collected.json`.
- [ ] **Step 4:** Run the blind classifier: one fresh agent per superpowers-arm miss, seeing the request, the stage diff and either the row plus the expected value, or the group source plus its failure output. Record the verdicts in `results/multistage-v3/pilot-classified.json`.
- [ ] **Step 5:** Decide go or no-go by the spec's rule. Update the results README, `PLAN.md`, the status page and a journey entry, then push.
