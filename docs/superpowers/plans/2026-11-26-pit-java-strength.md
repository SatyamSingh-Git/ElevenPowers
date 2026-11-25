# Java Test Strength Through PIT Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `ep_strength` and `ep_review --strength` report which mutants on a change's Java lines no test noticed, in Maven and Gradle projects, by running PIT.

**Architecture:** A new `core/strength/pit.py` builds the PIT invocation for the project's own build tool, runs it in the strength trial copy, and maps `mutations.xml` onto the existing `Observation` records. `core/strength/runner.py` gains a third adapter whose producer returns observations instead of source candidates. `.java` joins the strength scope's suffixes.

**Tech Stack:** Python 3.11+, `xml.etree.ElementTree`; PIT 1.30.2, pitest-junit5-plugin 1.2.3, gradle-pitest-plugin 1.19.0 (resolved by the user's build tool).

**Spec:** [docs/superpowers/specs/2026-11-26-pit-java-strength-design.md](../specs/2026-11-26-pit-java-strength-design.md)

## Global Constraints

- No new Python dependency. No edit to the project's pom or build script, in the user's tree or the copy.
- Versions pinned in one place: `PIT = '1.30.2'`, `JUNIT5 = '1.2.3'`, `GRADLE_PLUGIN = '1.19.0'`.
- Every observation PIT yields: relevance `changed_lines`, context `Class.method`, operator PIT's `<description>`.
- Every Java record carries the limitation: "Java mutants are run by PIT against the tests it selects from the build's test classpath, not by the recorded test command."
- Python 3.11 floor; Windows and POSIX. Fixtures are real captured output, private paths replaced.
- No local full suite; targeted tests, `py -3.11`, hosted CI after push.

## Review Focus

1. A stale `mutations.xml` already in the copied tree (a user who ran PIT) must not be read: delete before the run. Test in Task 1 (`run` deletes then reads only fresh).
2. Two selected files with the same name in different packages (`a/Util.java`, `b/Util.java`): mutants attach to the right one by package. Test in Task 1.
3. A mutant on an unchanged line of a changed class is dropped, not reported. Test in Task 1.
4. The test command is `make test` (or anything not Maven/Gradle) while a `.java` file changed: an issue, no crash, other languages still examined. Test in Task 2.
5. PIT exits non-zero or times out (offline plugin resolution, a TestNG project): issue `PIT did not complete (...)`, no observations, state incomplete. Test in Task 2.

---

### Task 1: `core/strength/pit.py` — targets, invocation, report mapping

**Files:**
- Create: `core/strength/pit.py`
- Create: `tests/fixtures/pit/` (captured `mutations.xml` files)
- Test: `tests/test_strength_pit.py`

**Interfaces:**
- Produces:
  - `tool(command: str) -> str | None` — the first Maven/Gradle executable token in a shell command (`'./gradlew'`, `'mvnw.cmd'`, `'mvn'`), via `core.stress.BUILD_TOOL`.
  - `targets(root: Path, paths: list[str]) -> list[str]` — `'<package>.<Stem>*'`, or `'<Stem>*'` with no package, deduplicated, sorted.
  - `invocation(executable: str, targets: list[str], scratch: Path) -> list[str]` — the argument list after the resolved executable; writes `scratch/pit.gradle` for Gradle.
  - `observations(root: Path, paths: list[str], regions: dict[str, list[list[int]]]) -> list[Observation]` — reads every report under `root`, maps and filters, sorted by (path, line, PIT index).
  - `run(root: Path, paths, regions, command: str, budget: Budget, maximum: int) -> tuple[list[Observation], list[str], bool]` — (observations kept, issues, more).

- [ ] **Step 1: Capture the producer.** In the scratchpad, a Maven project whose changed class has a killed mutant, a survived boundary mutant (`n > 10` tested only at 20 and 0), an untested method (NO_COVERAGE), a nested class, and a second `Util.java` in another package; run the spec's Maven invocation and a Gradle copy through the init script. Copy both `mutations.xml` into `tests/fixtures/pit/maven-mixed.xml` and `gradle-mixed.xml`; record which statuses actually appeared.
- [ ] **Step 2: Write the failing tests** in `tests/test_strength_pit.py`:
  - `test_the_tool_is_the_one_the_tests_use`: `tool('./gradlew test | tail') == './gradlew'`, `tool('cd x && mvnw.cmd -q test') == 'mvnw.cmd'`, `tool('make test') is None`, `tool('cd gradle && npm test') is None`.
  - `test_targets_cover_nested_classes_and_the_default_package`: files with `package demo;`, `package a.b;` and none → `['Bare*', 'a.b.Util*', 'demo.Calc*']`.
  - `test_maven_invocation_carries_the_junit5_plugin_and_never_fails_on_no_mutations` and `test_gradle_invocation_applies_the_plugin_per_project`: exact lists, the init script text contains `project.pluginManager.apply`, `'1.19.0'`, `'1.30.2'`, `'1.2.3'`.
  - `test_reports_map_to_changed_lines_with_pit_statuses`: on the fixtures, statuses map KILLED→detected, SURVIVED→undetected, NO_COVERAGE→undetected; an unchanged-line mutant absent; operator is the description; context `Shapes.big`.
  - `test_same_file_name_in_two_packages`: each `Util.java` gets only its own mutants.
  - `test_a_stale_report_is_not_read`: `run` with an executor stub that writes nothing, a stale report present beforehand → no observations, issue names "no report".
  - `test_the_limit_keeps_the_first_mutants_and_says_more`: maximum 1 → one observation, `more` True.
- [ ] **Step 3: Run them; expect import failure.** `python -m pytest tests/test_strength_pit.py -q` → FAIL (`No module named core.strength.pit`).
- [ ] **Step 4: Implement `core/strength/pit.py`** per spec steps 2–7. Resolve the executable: a file of that name in `root` (absolute path), else `shutil.which`; none → issue. `execute(..., shell=False)` with the remaining deadline. Status map exactly as the spec's step 5; unknown status → `error`.
- [ ] **Step 5: Tests pass**, then mutation-check the module with `flip.py` (status map, line filter, package match, stale deletion, limit).
- [ ] **Step 6: Commit** `strength: PIT reads Java mutants on changed lines` (code, tests, fixtures).

### Task 2: the runner and scope take Java

**Files:**
- Modify: `core/strength/scope.py:13` (`SUFFIXES` gains `.java`)
- Modify: `core/strength/runner.py` (adapter selection, versions, the producer loop, limitation)
- Test: `tests/test_strength_pit.py` (integration tests through `analyze` with `pit.run` stubbed)

**Interfaces:**
- Consumes: `pit.run`, `pit.tool`, `pit.PIT` from Task 1.

- [ ] **Step 1: Failing tests:**
  - `test_a_changed_java_file_is_selected`: `scope.select` on a git fixture with `src/main/java/demo/Calc.java` changed and `src/test/java/demo/CalcTest.java` changed → paths `['src/main/java/demo/Calc.java']`.
  - `test_java_needs_a_maven_or_gradle_command`: `analyze` with command `make test` and a changed `.java` → issue `Java mutation needs a Maven or Gradle test command; "make test" is neither`.
  - `test_pit_observations_enter_the_record`: `pit.run` monkeypatched to return two observations → record has them, `engine_versions == {'pit': '1.30.2'}`, the Java limitation present, `attempts == 2`.
  - `test_pit_failure_is_an_issue`: `pit.run` returns `([], ['PIT did not complete (exit 1)'], False)` → state `incomplete`, issue present.
- [ ] **Step 2: Run; expect FAIL** (Java not selected / no pit adapter).
- [ ] **Step 3: Implement.** `.java` in `SUFFIXES`; in `analyze` split `java` paths from `js` (`js` = neither `.py` nor `.java`); add `('pit', java, None, tool)` when `pit.tool(value['command'])`, else the issue; version `PIT` for it; in the producer loop, for `pit` run `pit.run` inside `with trial(...) as test_root` with the share as `maximum`, count each kept observation with `budget.attempt()` (a `TimeoutError` turns the rest into `not_run`), extend issues, `more` → the existing issue; append the limitation when a `pit` adapter was chosen.
- [ ] **Step 4: Pass**, plus `tests/test_strength*.py` and `py -3.11` for the new file; mutation-check the runner branch.
- [ ] **Step 5: Commit** `strength: Java files go to PIT, its mutants into the same record`.

### Task 3: real runs, docs, map

**Files:**
- Create: `docs/validation/2026-11-26-pit-java-strength.md`
- Modify: `the-guide/commands.md` (ep_strength engines), `docs/status.md`, `architecture/index.html` (+ `graph-data.js` via render)

- [ ] **Step 1:** Real `ep_review --strength` on the scratch Maven and Gradle repos (`multirev-*`, with a survivable change), and on a checkout of the code before Task 2 (Java not selected) — watch the flip. Record commands, outcomes, seconds.
- [ ] **Step 2:** Docs: engines table/prose names PIT, versions, the build-tool rule, the limitation, the bounds (no method expansion, TestNG, Kotlin, offline). Status entry. Map: a `pit` engine node or the strength node's text, changelog line; `python architecture/check.py --render`.
- [ ] **Step 3:** Final review of the whole change (one reviewer), fix Critical/Important with RED→GREEN.
- [ ] **Step 4:** Commit and push; read hosted CI.
