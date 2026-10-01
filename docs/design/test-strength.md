# Changed-code test strength

Approved delivery: an optional, bounded, host-independent observation of whether
passing tests notice small mutations in the source changed by a task. The runtime
works for any repository; named repositories are acceptance cases only.

The shared runner selects changed production files against a recorded Git base,
creates a private copy, establishes a passing baseline there, asks established
language engines for mutations, and records detected, undetected, invalid and
incomplete observations. It never mutates the user's source. Repository boundaries,
ignores, ambiguous attribution, missing engines, setup failures, interruptions and
budget exhaustion are explicit. A surviving mutant is a possible test gap,
including possibly equivalent behavior, rather than proof of a bug.

Python uses Cosmic Ray; JavaScript and TypeScript use StrykerJS. Dependencies are
optional and installed by the project/user, never downloaded by runtime. Engine
producer probes precede adapters. The standard-library runtime remains importable
without them. Attempts and elapsed time are bounded; completed results may be
reused only for identical inputs. There is no new completion blocker or verdict.

Completion automatically considers this analysis when enabled and an engine is
available, sharing the existing deadline. An explicit CLI supports a focused
command/base override. Automatic operation does not expose individual mutants to
the coding agent: observations are saved for human review in portable reports.
Report export reads saved results and never starts execution.

Isolation is a filesystem working copy, not a security sandbox. Trusted declared
test commands can have external side effects. Commands tied to an original absolute
workspace or missing dependencies cannot be silently called successful isolation.
Copy limits, source changes during execution and incomplete engine output invalidate
the observation. Reports contain bounded metadata, never source/replacements or raw
captured test output. Strength remains informational and independently qualified.

Acceptance: weak tests leave undetected changes; stronger tests detect them on
unrelated Python and JS/TS fixtures; baseline failures and timeouts are incomplete;
original files remain byte-identical. Native Windows and Linux execution are tested
where available, with unsupported environments stated rather than guessed.
