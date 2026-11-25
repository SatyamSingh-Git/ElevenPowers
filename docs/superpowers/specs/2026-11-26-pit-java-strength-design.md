# Java test strength through PIT

2026-11-26. Java support step after Maven and Gradle test runs
([maven](2026-11-25-maven-tests-design.md), [gradle](2026-11-25-gradle-tests-design.md),
[builds keep going](2026-11-25-build-keeps-going-design.md)). User: "start the PIT work";
standing "decide things yourself, just let me know at the end".

## Intent

`ep_strength` and `ep_review --strength` mutate the lines a change touched and say which
mutations no test noticed. They do this for Python (Cosmic Ray) and JavaScript/TypeScript
(Stryker's instrumenter). A changed `.java` file is not even selected today
(`core/strength/scope.py` `SUFFIXES`). The goal is the same answer for Java changes in Maven
and Gradle projects, borrowed from **PIT** (pitest, Apache-2.0), the standard Java mutation
tester.

**The borrow.** PIT 1.30.2 (Maven Central, 2026-11-05), its JUnit 5 plugin 1.2.3, and for
Gradle the gradle-pitest-plugin 1.19.0 (Apache-2.0). PIT chooses the mutations, compiles
nothing (it mutates bytecode), picks the tests that cover each mutant and runs them.
**What we add:** running it without touching the project's build files, keeping only the
mutants on the changed lines, and reporting them through the same observation records,
store, reuse rule and review section the other engines use.

## Goals

- A changed main-source `.java` file in a Maven or Gradle project is selected and examined.
- Each PIT mutant on a changed line becomes one observation: detected, undetected, invalid,
  error or not run, with PIT's own description of the change as the operator.
- Works on the unchanged project: no pom or build script edit, in the user's tree or the copy.
- Absent PIT (offline, no build tool, a test command that is not Maven or Gradle) is an
  issue in the record, never a crash, exactly like an absent Cosmic Ray.

## Non-goals

- Kotlin, Scala, Groovy sources; TestNG (PIT needs a separate plugin); Ant; Bazel.
- PIT's incremental history, its HTML report, arcmutate's commercial git integration.
- Expanding a changed line to its enclosing method (Cosmic Ray's `changed_function`): PIT
  reports a method name but no method span. Only mutants on changed lines are reported.

## Anti-goals

- Reporting a mutant PIT ran outside the change as if the change were unpinned.
- Reading a report the run did not write (a `mutations.xml` left in the copied tree).
- Claiming the declared test command noticed a mutant: PIT runs its own selection of tests
  from the build's test classpath. This is stated as a limitation on every Java record.

## How it works (decided)

Captured on 2026-11-26 against Maven 3.9.9 and Gradle 8.10.2, JDK 17, JUnit 5.11.3.

1. **Selection.** `.java` joins `SUFFIXES`. Test files are already excluded by
   `surface.TEST_NAME` (`src/test/java/...` matches its `test/` directory rule).
2. **Which build.** The strength command (the project's declared tests command) names the
   build tool; the first `mvn`/`mvnw`/`gradle`/`gradlew` invocation in it (the same
   `BUILD_TOOL` pattern `core/stress.py` uses) is the executable PIT runs with, so PIT uses
   the wrapper the tests use. A command that names neither: issue
   `Java mutation needs a Maven or Gradle test command; "<command>" is neither`.
3. **Which classes.** For each selected file, its `package` declaration plus the file stem,
   with a trailing `*` so nested classes (`Calc$Inner`) are included: `demo.Calc*`. A file
   with no package declaration gives `Calc*`. Over-inclusion (`demo.Calculator`) only costs
   time; step 5 drops what is not in a selected file.
4. **The run**, in the trial copy after the baseline passed, through `strength.execution.execute`
   with an argument list (no shell, so `*` and `$` reach the tool unchanged), within the
   remaining strength deadline:
   - Maven: `<mvn> -B dependency:copy -Dartifact=org.pitest:pitest-junit5-plugin:1.2.3
     -DoutputDirectory=<tmp> test-compile org.pitest:pitest-maven:1.30.2:mutationCoverage
     -DtargetClasses=<list> -DoutputFormats=XML -DtimestampedReports=false
     -DfailWhenNoMutations=false -DadditionalClasspathElements=<tmp>/pitest-junit5-plugin-1.2.3.jar`.
     Without the plugin jar PIT finds no JUnit 5 tests (captured: "JUnit 5 is on the
     classpath but the pitest junit 5 plugin is not installed"); without `test-compile` it
     finds no classes. `failWhenNoMutations=false` keeps a module with no target class from
     failing the build (captured: a warning only).
   - Gradle: `<gradle> --init-script <tmp>/pit.gradle --continue pitest -PepPitTargets=<list>`.
     The init script puts gradle-pitest-plugin 1.19.0 on its classpath and applies it to
     every project with the `java` plugin, through `project.pluginManager.apply` (applying
     it from the script's own scope is refused: "must be applied in a build script").
   - Reports: every `target/pit-reports/mutations.xml` (Maven) or
     `build/reports/pitest/mutations.xml` (Gradle) under the copy, all deleted before the run.
5. **Mapping.** Each `<mutation>` is matched to a selected file by package (of
   `mutatedClass`, nested part dropped) and `sourceFile`; kept only when `lineNumber` lies
   in one of that file's changed ranges. Status from PIT's own classification: `detected='true'`
   (KILLED, TIMED_OUT, MEMORY_ERROR) is detected; SURVIVED and NO_COVERAGE undetected;
   NON_VIABLE invalid; NOT_STARTED and STARTED not run; RUN_ERROR and anything else error.
   Relevance `changed_lines`, context `Class.method`, operator PIT's `<description>`.
6. **Budget.** Kept mutants are sorted by file, line and PIT's index; at most the engine's
   share of `max_mutants` are recorded, each counted as an attempt, and more than that
   records the existing "additional candidates were not examined" issue. PIT has no
   line filter, so it runs every mutant in the targeted classes; the time limit is what bounds it.
7. **Failure.** A run that times out, exits non-zero or writes no report: issue
   `PIT did not complete (<reason>)` with the last error line, no observations from it.
8. **Version and reuse.** `engine_versions['pit'] = '1.30.2'`; the reuse rule already keys on it.

## What a reader sees

`ep_review --strength` on a Java change lists unpinned lines as it does for Python, e.g.
`Calc.java:5 — Replaced integer addition with subtraction`, under the Java limitation line.

## Constraints

- No new Python dependency; `xml.etree.ElementTree` reads the report.
- Python 3.11 floor; Windows and POSIX (wrapper names `mvnw.cmd`/`gradlew.bat` vs `./mvnw`).
- The hosted CI has no network-independent PIT, so tests read captured `mutations.xml`
  fixtures and check the built commands; the end-to-end runs are local and recorded.

## Left to the builder

File layout inside `core/strength/` (a `pit.py` beside `engines.py` is expected), the init
script text, and how the runner's per-candidate loop branches for an engine that reports
observations itself.
