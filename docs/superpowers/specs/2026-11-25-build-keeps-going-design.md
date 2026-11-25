# The review's builds keep going past a failing module

2026-11-25. Follows the Maven and Gradle slices
([maven](2026-11-25-maven-tests-design.md), [gradle](2026-11-25-gradle-tests-design.md)).

## Why

A multi-module build stops at its first failing module by default: Maven skips the rest of
the reactor, Gradle runs no further test task. A project with one module that already fails
(a flaky or known-broken test) therefore gives `ep_review` a stopped run on every tree, and a
stopped run can clear nothing: the review answered **unknown** for a change that a later
module's test pins. Captured on 2026-11-25 against two scratch builds (alpha fails on
purpose, beta's test pins the change): `gradle test` and `mvn test` both gave
*"a run stopped before every test had run"*.

## Approaches

- **Read the JUnit XML reports** both tools write. Rejected: Gradle 8.10.2's XML names a
  parameterised case by its display name only (`[2] 2`, no method), so two parameterised
  methods in one class collide, and the names cannot be matched against the console names
  the other runs produce. It also needs a freshness rule for reports a skipped task left behind.
- **Detect the stop and say so** (what shipped first). Kept, but it only explains the
  unknown; it does not avoid it.
- **Ask the build not to stop** (chosen). The review already adjusts the command it runs:
  pytest gets `-rA` so passes are named. Gradle gets `--continue`, Maven `-fae`, placed
  straight after the executable so a pipe or a later `&&` step is untouched.

## What changes

- `core/stress._with_outcomes` (shared by the review and the old-tree check) inserts
  `--continue` after a `gradle`/`gradlew` invocation and `-fae` after an `mvn`/`mvnw` one,
  unless the command already chooses: Gradle `--continue`/`--no-continue`, Maven
  `-fae`/`--fail-at-end`/`-ff`/`--fail-fast`/`-fn`/`--fail-never`. An explicit choice is the
  project's, and the stop rules still read the result.
- `core/review._stopped`'s multi-project rule now fires only for a command that chose
  `--no-continue`; a test pins that it still does.
- The report's run lines show the command as run, flag included.

## Bounds

- A module that depends on a failed one is still not built: Maven lists it `SKIPPED` under
  `-fae` (checked), which the stop rule reads. Gradle under `--continue` skips the tasks that
  depend on a failed task without a summary line; not detected.
- `-q` still hides Gradle's failing names and Maven's reactor summary.
