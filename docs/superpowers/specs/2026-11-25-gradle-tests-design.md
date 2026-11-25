# Gradle test runs, counted and named

*2026-11-25. A small change: the second Java slice of the
[direction review](../../../reports/ElevenPowers%20direction%20review.md)'s
step 6, after [Maven](2026-11-25-maven-tests-design.md). The user said
"continue with gradle" under the standing "decide things yourself"; every
call below is mine.*

## What the real producer prints

Captured 2026-11-25 with Gradle 8.10.2, JUnit 5.11.3, Java 17:

```
> Task :test FAILED

CalcTest > wrongOnPurpose() FAILED
    org.opentest4j.AssertionFailedError at CalcTest.java:16
ShapesTest > positive(int) > [2] 2 FAILED
ShapesTest > Inner > deep() FAILED

7 tests completed, 4 failed, 1 skipped
```

- **A passing run prints no count at all**, only `BUILD SUCCESSFUL`. Counts
  exist only when something fails.
- **A re-run with unchanged inputs prints `> Task :test UP-TO-DATE`** and
  runs nothing. Gradle skips only a test task whose inputs match an earlier
  *passing* run, so it is not a false pass, but it is not a fresh run.
- **`-q` keeps the count line and drops the names.**
- **A multi-project build without `--continue` stops at the first failing
  test task and says nothing about the ones it never ran**
  (`:beta:test` simply does not appear). With `--continue` every one runs.
- Plain console when piped (no colour codes; `--console=plain` gives the
  same lines).

## Design

- **Parser** (`core/parsers.py`, dispatched for `gradle`/`gradlew` commands
  that name a `test`/`check`/`build` task, before the wrapper fallback):
  - counts from every `N tests completed, M failed[, K skipped]` line,
    summed (one per failing test task); passed = N − M − K;
  - a failing test record per `A > B > C FAILED` line, identity the parts
    joined by `.`, with an empty `()` dropped (`CalcTest.wrongOnPurpose`,
    `ShapesTest.Inner.deep`, `ShapesTest.positive(int).[2] 2`);
  - no count line (every passing run): the exit code alone, uncounted.
- **Stopped** (`core/review.py`): a failed Gradle run without `--continue`
  in a build whose `settings.gradle(.kts)` includes subprojects may not
  have reached every test task, so it cannot clear a change.
- **Discovery** (`core/config.py`): `build.gradle(.kts)` or
  `settings.gradle(.kts)` gives `tests`: the wrapper where it runs
  (`gradlew.bat test` on Windows, `./gradlew test` elsewhere), else
  `gradle test`.

## Approaches

- **Chosen: the console lines**, as for Maven.
- **`build/test-results/test/*.xml`**: complete, including passes, but a
  stale file from an earlier build is indistinguishable from this one, and
  an UP-TO-DATE run would re-read the old results as new. Rejected.
- **Adding `--continue` or test logging to the project's command**: changes
  the project's own build. Rejected.

## Bounds stated, not fixed

A passing Gradle run is uncounted; an UP-TO-DATE run counts as the pass
it is from; `-q` names nothing; a single-project build's stop is not
flagged (its one test task runs every test).

## Checks

Captured outputs as fixtures, both directions: counts and names on a
failing run (including nested and parameterised names); a passing run
uncounted; `-q` counted, unnamed; two failing test tasks summed (with
`--continue`); the review's stopped rule on a multi-project build with and
without `--continue`, and never on a single project; discovery with and
without a wrapper, on both platforms.
