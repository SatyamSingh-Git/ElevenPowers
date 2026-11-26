# Java test strength through PIT — validation, 2026-11-26

Design: [spec](../superpowers/specs/2026-11-26-pit-java-strength-design.md),
[plan](../superpowers/plans/2026-11-26-pit-java-strength.md).

## Setup

Windows 11, JDK 17.0.0.1, Maven 3.9.9, Gradle 8.10.2, JUnit Jupiter 5.11.3.
PIT 1.30.2, pitest-junit5-plugin 1.2.3, gradle-pitest-plugin 1.19.0, all resolved
by the build tool from Maven Central and the Gradle plugin portal on first use.

Two scratch repositories with the same sources, one built by Maven and one by
Gradle. The change under review moves a boundary, `n > 5` to `n > 10`, in
`Shapes.big`; the tests call it only at 20 and 0, so a boundary mutant survives.

## Real reviews

`ep_review --base HEAD~1 --command "<mvn|gradle> test" --strength --mutation-seconds 240`

| build | code | strength | mutants | unnoticed line | seconds |
|---|---|---|---|---|---|
| Maven | before (8d23a0f) | not applicable: `.java` not selected | 0 | none | 21 |
| Gradle | before (8d23a0f) | not applicable | 0 | none | 12 |
| Maven | 7ac14f8 | complete | 3, 1 unnoticed | only the counts were read | 32 |
| Gradle | 7ac14f8 | incomplete: *baseline did not report positive passing test counts* | 0 | none | 16 |
| Gradle | e60e033 | complete | 3, 1 unnoticed | `Shapes.java:5 in Shapes.big: changed conditional boundary` | 16 |
| Maven | e60e033 | complete | 3, 1 unnoticed | same | 35 |

Verdict in every row: NOT PINNED (no test fails with the change undone), which is
right: the tests never probe between 5 and 10.

## Found by running it

- **Gradle never reached PIT.** The strength baseline requires a count of passing
  tests, and a passing Gradle run prints none. It is now counted from the JUnit
  XML that run wrote under `build/test-results/`; an UP-TO-DATE re-run left the
  previous file untouched (captured), so reports are deleted before the run.
- **The review cut PIT's descriptions.** It kept the part of an operator after
  its last `/` (right for Cosmic Ray's `core/NumberReplacer`), which turns
  `replaced boolean return with true for demo/Shapes::big` into `Shapes::big`.
- **The review never said PIT ran its own tests.** The record carried the
  limitation; the review's Unknown list did not. It does now.
- **Hosted CI failed on the first two commits**: the architecture map must draw
  every module, and `core/strength/pit.py` was on no node.
- PIT needs `test-compile` first (it found no classes otherwise) and its JUnit 5
  plugin (it found no tests otherwise); a module with no target class only warns
  with `failWhenNoMutations=false`. Gradle refuses the plugin applied from an init
  script's own scope; it is applied to each project.
- A mutant that loops forever is TIMED_OUT and the run still exits 0. PIT writes
  its report out of line order (7, 8, 9, 7, 11).

## Not covered

- PIT runs its own selection of tests from the build's test classpath, not the
  judged command; every Java record and review says so.
- Only mutants on changed lines: PIT names a method but not its lines, so a
  change is not expanded to its enclosing method as it is for Python.
- JUnit 4 and 5 only; no TestNG, Kotlin, Scala, Ant or Bazel.
- The first run needs the network or a build cache that already holds PIT.
- MEMORY_ERROR, NON_VIABLE, NOT_STARTED, STARTED and RUN_ERROR were not produced
  by a real run; their mapping is tested on a real record with the status changed,
  using the names PIT's own summary prints.
