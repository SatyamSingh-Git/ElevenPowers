# 93 — a dependent the search does not find

The v2 pilot showed Sonnet 5.5 with superpowers finding every dependent, because
every dependent named what changed and one `grep` reached it. v3 asked the
harder question honestly: what if the code at risk does not name the change?
On its first pilot, superpowers alone broke earlier behaviour in both cases.

## What was built, at $0

- **A case profile.** v3 cases have eight stages, at least five cross-cutting,
  and a bug fix. Each cross-cutting stage declares a **quiet dependent** with
  its own diff, kind and failing groups. Nothing is fixed at six stages any more.
- **`eval/multistage_quiet.py`.** It takes a stage's changed names from the
  reference diff, using `ast` and `tokenize`:
  - definitions whose body the diff changes;
  - module names it reassigns;
  - names it removes from every touched file.

  The rehearsal then proves three things for each quiet dependent: leaving it
  behind fails exactly its groups, the public suite stays green, and its file
  names nothing that changed.
- **An oracle rule.** Placeholder names are not graded, which closes one of the
  v2 defect kinds for every case.
- **A runner for any case set.** It also refuses a batch placed inside a folder
  the agent must not see.

## Found on the way, by running it

- **Appended functions counted as changes.** A function added below another
  marked the one above as changed, because the added lines' insertion point
  was the old function's last line. A test caught it. A run of added lines now
  belongs wherever its first non-blank line starts.
- **"Net removed" swept in common names.** As first specified, it meant "on a
  removed line and on no added line", which counted `items` and `list` still
  used elsewhere in the file. It now means gone from every touched file, and
  builtins never count.
- **Three mutants survived the first rounds, and 30 were killed.** The
  survivors were a removal-only change, a method added inside a class after a
  blank line, and a quiet diff declaring the wrong group. Each got a test, and
  all 35 mutants in the final rounds were killed.
- **Two docs facts were a wording choice.** The independent review of
  `parcelpost` found them. A row whose old value named a unit (`integer pence`)
  could be correctly replaced in several words, and `booking order` appeared
  only as prose. The author fixed both.
- **The blind packet nearly leaked the arm.** The first diffs carried git's
  quoted Windows paths, which included the slot name. A scan caught it before
  any classifier ran.

## The pilot

$4.09, four conversations, all 32 stages qualified.
- **Superpowers alone:**
  - `gradebook` stage 4 raised the default precision and left the grades
    export at `.1f`, so the posted percent no longer matched the course grade.
  - `parcelpost` stage 5 put the manifest in booking order. Billing grouped
    adjacent rows by account, so each account got two invoices with the same
    number, and the second file overwrote the first.
- **The verdict:** a blind classifier, told nothing about the arms, called
  both genuine.
- **What did not break:**
  - Docs stayed current in every arm.
  - Changelog, protected file and bug-fix tests were kept everywhere.
- **The ElevenPowers arm** made the same gradebook miss and avoided the
  parcelpost one. Two cases at one replicate say nothing about the arms; the
  pilot is excluded by design.

## What it means so far

The field report's dependent-breakage claim now has something to show itself
against. Its docs claim still does not: across two pilots and eight
conversations, no docs fact went stale through the agent's fault. At the
pilot's miss rate, twelve cases give roughly half the power the design wants,
so the full run needs more replicates or a descriptive label, decided before it
runs.

*Reproduce: `python -m eval.multistage_rehearse --cases eval/multistage_v3 --out
<file>`; `python -m eval.multistage_run collect --batch <batch> --out <file>
--regrade`.*
