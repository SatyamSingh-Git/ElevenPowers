# Maven test runs, counted and named

*2026-11-25. A small change: step 6 of the
[direction review](../../../reports/ElevenPowers%20direction%20review.md)
("Java Surefire/Gradle count parsing and discovery"). The user said "start
the work" under the standing "decide things yourself"; every call below is
mine.*

## Why

Java is the most-used language with the weakest support here. A Maven
build is recognised as a test run and judged by its exit code alone: no
counts, no failing tests named, and no command discovered from `pom.xml`.
So `ep_review` on a Java project can only say pinned or not from the exit
code, and cannot tell a stopped build from a complete one.

## What the real producer prints

Captured 2026-11-25 with Maven 3.9.9, JUnit 5.11.3, on Surefire 3.5.2 and
2.22.2, with and without `-q` and `-B` (no colour codes in a pipe):

```
[ERROR] Tests run: 4, Failures: 1, Errors: 1, Skipped: 1, Time elapsed: 0.07 s <<< FAILURE! -- in demo.CalcTest
...
[ERROR] Failures:
[ERROR]   CalcTest.wrongOnPurpose:16 expected: <4> but was: <3>
[ERROR] Errors:
[ERROR]   CalcTest.throwsOnPurpose:21 IllegalState boom
[ERROR] Tests run: 4, Failures: 1, Errors: 1, Skipped: 1
```

- The per-class line carries `Time elapsed`; each module's total does not.
  A multi-module build prints one total per module.
- The per-test failure line differs by version (`demo.CalcTest.x -- Time
  elapsed` in 3.x, `x  Time elapsed` in 2.x). The `Failures:`/`Errors:`
  block is the same in both.
- `[INFO]   from pom.xml` has the same indent as a failing name, so names
  are read only inside that block.
- A build that stops at a failing module lists the later ones as
  `beta ..... SKIPPED` in the reactor summary. With `-q` there is no
  summary at all.

## Design

- **Parser** (`core/parsers.py`, dispatched for `mvn`/`mvnw` commands
  before the wrapper fallback): passed and failed summed over the module
  totals (failed = failures + errors; skipped counted neither way). A
  failing test record per name in the block, identity `Class.method` as
  printed. No total line: the exit code alone, uncounted, as today.
- **Stopped** (`core/review.py`): a reactor line ending `SKIPPED` means not
  every test ran, so the review cannot clear the change. Under `-q` this
  is invisible; the limit is stated in the guide.
- **Discovery** (`core/config.py`): `pom.xml` gives `tests`: the Maven
  wrapper when the project has one (`mvnw.cmd test` on Windows,
  `./mvnw test` elsewhere), else `mvn test`.

## Approaches

- **Chosen: read the console summary.** It is what every Maven run prints,
  and what the hooks already capture.
- **Read `target/surefire-reports/*.xml`.** Exact, but the files outlive
  the run, so a stale report from an earlier build would be read as this
  one. Rejected for that.
- **Add `-fae` to make stops impossible.** Changes the project's own
  command. Rejected.

## Non-goals

Gradle (next slice; its default output names only failures), mutation
(PIT), per-test coverage, TestMiner for Java.

## Checks

Captured outputs as fixtures, both directions: counts on a failing and a
passing run; names on both Surefire versions; `from pom.xml` never named;
two modules summed; a SKIPPED module read as stopped by the review, and a
complete build not; discovery with and without a wrapper, and on both
platforms' spelling.
