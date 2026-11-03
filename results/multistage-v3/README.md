# Multi-stage v3: no measured benefit from ElevenPowers

The full run is complete: 12 cases × 2 arms × 5 replicates, and 120 of 120
conversations are comparable. On the pre-registered analysis, ElevenPowers did
not reduce either harm the field report described. Both point estimates lean
the other way, and neither difference is significant
([result](#result-pre-registered-primary-analysis)).

v3 replaces v2's cases after the v2 pilot found nothing to prevent
([journey 92](../../journey/92-the-pilot-found-nothing-to-prevent.md)). Its
projects are bigger, eight requests long, and every request that changes
shared code has a declared **quiet dependent**: code a search for the changed
names does not find and the project's own tests do not catch. The rehearsal
proves that mechanically
([design](../../docs/superpowers/specs/2026-10-28-multistage-v3-harder-cases-design.md),
[journey 93](../../journey/93-a-dependent-the-search-does-not-find.md)).

## Pilot, 2026-10-28

Four sealed conversations on `gradebook` and `parcelpost`, frozen at `ecee720`
([`pilot-manifest.json`](pilot-manifest.json), [`pilot-protocol.json`](pilot-protocol.json)).
After the pilot, a final code review fixed three checks, and [`manifest.json`](manifest.json)
is refrozen with the cases byte-identical:
- format specs in documented values are graded;
- f-strings read the same on every Python version;
- a quiet diff may touch only its declared file.

The pilot regrades identically under the fixed checks.
Superpowers 7.0.0 was in both arms, with Sonnet 5.5 at medium. All 32 stages
completed and qualified, for $4.09.

| | lost earlier groups | stale facts | cost | model time |
|---|---|---|---|---|
| superpowers, `gradebook` | 1 (stage 4) | 0 | $0.98 | 230 s |
| superpowers, `parcelpost` | 2 (stage 5) | 0 | $0.84 | 291 s |
| + ElevenPowers, `gradebook` | 1 (stage 4, the same miss) | 0 | $0.94 | 367 s |
| + ElevenPowers, `parcelpost` | 0 | 0 | $1.33 | 398 s |

A blind classifier saw only the request, the stage diff, the project before
the stage and the failing check, and was not told the arm. It called both
superpowers-arm misses genuine ([`pilot-classified.json`](pilot-classified.json)):
- **gradebook:** raising the default precision left the grades export at one
  decimal place. The posted percent stopped matching the course grade the docs
  promise.
- **parcelpost:** putting the manifest in booking order broke billing, which
  grouped adjacent rows by account. Each account got two invoices with the same
  number, and the second file overwrote the first.

**The gate is met, in substance and not just mechanically.** Every changelog,
protected file and bug-fix test was kept in both arms, and no docs fact went
stale. The docs claim still shows no headroom on these cases.

**What this pilot does not show:**
- **No comparison between arms.** Pilot runs are excluded by design, and two
  cases at one replicate cannot separate the arms. On these four conversations,
  ElevenPowers made the same gradebook miss and avoided the parcelpost one.
  That is a description, not a result.
- **Statistical power.** At the pilot's rate of 1.5 lost groups per
  superpowers-only conversation, twelve cases at three replicates give only
  0.64–0.67 power at ratio 0.5 ([`power.json`](power.json), computed after
  the pilot; an estimate from v2's table had said 0.45–0.6). The full-run
  proposal below therefore adds replicates.

## How the two pilot cases were checked

- **Rehearsal:** both cases rehearse usable from a fresh CRLF clone
  ([`rehearsal.json`](rehearsal.json)). Every quiet dependent fails exactly its
  groups, keeps the public suite green, and names nothing the stage changed.
- **Review:** one independent reviewer per case ([`review.json`](review.json)).
  - `gradebook` had no blocking findings.
  - `parcelpost` had two docs facts whose value was a wording choice. The author
    fixed them, and the case was rehearsed again.
  - 10 of 11 quiet dependents can be reached by searching the request's own
    words, through ordinary comments and docs prose. They were kept: making them
    quieter would mean hiding things, which the design forbids. The gradebook
    miss came from the one dependent its reviewer rated hard to find. The
    parcelpost miss came from one rated only mildly weak: a search for "manifest"
    reaches it among 11 files.
- **Agent's instructions:** the user's own `~/.claude/CLAUDE.md` is excluded, and
  the Skill tool is allowed in both arms.

## Twelve cases, frozen

Ten more fresh authors wrote the remaining cases from the same brief, with
domains: clinic booking, recipes, library loans, fleet maintenance, payroll,
theatre tickets, greenhouse monitoring, surveys, household budgets and a
hotel desk. The two pilot cases are unchanged.
- **Review:** each case had one fresh reviewer. Their 10 blocking findings,
  all correct work that would have been graded wrong, went back to the authors
  and were fixed. Typical ones:
  - a fact whose old value named a unit;
  - a field list an agent could accurately extend;
  - a check that only one of two reasonable designs passes.
- **Disclosed:** 55 of 68 quiet dependents can be reached by searching the
  request's own words ([`review.json`](review.json)).
- **Rehearsal:** all twelve rehearse usable from a fresh CRLF clone
  ([`rehearsal.json`](rehearsal.json)).
- **Freeze:** [`manifest.json`](manifest.json) was taken at `8c3d7b1`, with
  1,220 case files. [`pilot-manifest.json`](pilot-manifest.json) keeps the
  pilot's freeze.
- **Published:** the cases are in the `v3/` folder of
  <https://github.com/SatyamSingh-Git/elevenpowers-multistage-cases>.

## Result: pre-registered primary analysis

[`full-analysis.json`](full-analysis.json) is batch b's 53 complete
conversations plus batch c's 67 reruns, graded by the frozen oracles. All 120
are comparable and none is missing. A case's difference is its mean without
ElevenPowers minus its mean with it, so positive favours ElevenPowers. The
cases enter an exact two-sided signed-rank test, with Holm across the two
co-primaries.

| outcome | superpowers | + ElevenPowers | cases better / worse / tied | p | Holm |
|---|---|---|---|---|---|
| earlier groups lost | 29 | 35 | 3 / 6 / 3 | 0.43 | 0.50 |
| stale documented facts (stage-summed) | 43 | 79 | 1 / 5 / 6 | 0.25 | 0.50 |

Per conversation, ElevenPowers cost $1.22 against $1.12, and took 10.8 minutes
of wall time against 6.5 (corrected 2026-11-03 from "model time": the model's
own time is nearly equal; see [overhead](overhead/README.md)).

**What this does and does not show:**
- **No reduction is shown.** The power target assumed ElevenPowers halves
  the lost-group rate at the pilot's rate of 1.5. The measured superpowers rate
  was 0.48 (29 in 60 conversations), about a third of the pilot's. So the run
  had less power than planned, and a small benefit cannot be excluded. A large
  one is not supported: the point estimate is a 21% increase.
- **The docs claim has the wrong sign so far.** ElevenPowers was worse on five
  cases and better on one. Stale facts are summed over stages, so one fact
  that goes stale early counts up to eight times. The separator sensitivity
  analysis and the blind review below decide how much of the 79 is real.
- **Batch provenance.** Batches b and c share every sealed field except the
  session ids and the preparation time, and batch c's slots are exactly the
  ones batch b did not complete. Batch a ran under the earlier network check
  and is excluded.
- **Total spent:** $153.40, made up of $8.93 for batch a, $65.35 for b and
  $79.12 for c, plus about $0.30 of probes.

## Why ElevenPowers did not help: diagnosis of its 31 losses ($0)

This takes every stage where the ElevenPowers arm lost an earlier group (31
of them) and asks where prevention failed. Was the dependent that broke
detected? Was the warning delivered? Was it ignored? It was computed from the
kept snapshots and transcripts by [`diagnose_losses.py`](diagnose_losses.py).
For detection, ElevenPowers' own `atlas.neighbourhood` brief is replayed on
the pre-stage tree for each file the agent edited. Per-loss rows are in
[`diagnosis-elevenpowers-losses.json`](diagnosis-elevenpowers-losses.json).

| where it failed | losses |
|---|---|
| **not detected**: no brief for an edited file names the dependent | 27 |
| of those, the dependent imports an edited file but sits behind the brief's four-name cutoff ("+N more") | 5 |
| of those, the dependent does not import any edited file at all | 22 |
| **detected**: a brief names the dependent, delivered (see probe) and not acted on | 4 |
| the agent edited the dependent, in any loss | 0 |

- **A behaviour diff does not fix it either.** It would have caught only 1 of
  31, because 30 dependents were left behind with unchanged behaviour
  ([behaviour spike](behaviour-spike/README.md)).
- **Detection is the main failure.** 22 of 31 dependents are not reachable
  through imports at all. They depend on behaviour, such as a file format, a
  row order or a precision, not on a name. No import graph can find them, so
  a detector that watches behaviour is needed. The other 5 were reachable but
  cut off by the four-name limit.
- **Delivery works; the transcripts just do not show it.** The PreToolUse
  brief is emitted: 13 of 95 final ledgers list briefed files. Its text
  appears in none of the stream-json transcripts. A probe on 2026-11-01
  ([`delivery-probe.json`](delivery-probe.json), $0.46) emitted ElevenPowers'
  exact output shape with a token. The model quoted it word for word, and with
  the hook silent it answered NONE. So the 4 detected losses were delivered
  and not acted on, not undelivered.
- **The agent was told a false FAIL in 391 of 621 stages (63%).** The startup
  health check fails on any "unreadable test output" record.
  `parsers.claims_to_run_tests` matches the word `tests` anywhere in a
  command, so reading a test file (`sed -n 1,12p tests/test_x.py`) is
  recorded as a test run nobody could read. It is the same defect class as
  the `gh` false breach: a word matched anywhere, not where a command starts.

**Repair, replayed on this run.** A command now claims to run tests only when
one of its pieces, split at `;`, `&&`, pipes and newlines outside quotes, is a
non-reader command that runs them. That means a known wrapper or TAP harness,
matched on the program's name even when it is called by path, a named runner,
or a bare `test`/`tests` argument rather than a path. Of the 884 "unreadable
test output" records the ElevenPowers arm wrote, 82 still claim, and in every
one the claiming piece is `python -m pytest tests -q 2>&1`. The other 802 were:
- reads of test files (`cd … && sed`, `cat`, `grep`, `git diff`);
- `grep` patterns holding a quoted `\|`;
- Python heredocs editing a test file.

The 82 were not unreadable either. Every one ran the agent's pytest and then
`ep_check.py --all`, as ElevenPowers' startup message advises. `parse` defers
such a command to the receipt `ep_check` writes, by design, and the hook then
filed the empty result as unreadable. Of the 2,022 Bash commands in the arm's
transcripts, 282 pytest commands produced no records, and all 282 were owned
checks. With the hook repaired (`d07a9d8`), none of the 2,022 is filed, so this
run's data would have produced no false FAIL at all. A first version of this repair split inside quotes and was caught by this
replay. A second matched TAP harnesses on the raw text, missing
`"C:\Program Files\nodejs\node.exe" --test`. A third did not count a `--test`
flag, missing `node --experimental-strip-types --test`, so TAP output from that
run was never parsed. The full suite caught both.

## The full run, started 2026-10-30

The user said go on five replicates. 120 slots were sealed in
`E:/ep-runs/multistage-v3-full-2026-10-30` (outside the repository), run four
at a time and never retried. The first stage of all four lanes qualified:
superpowers loaded in both arms, ElevenPowers' marker only in its own, and no
closed-book breaches. A one-turn probe first confirmed authentication and
Sonnet 5.5 on `claude` 2.1.292, for $0.15.

Before sealing, two frozen modules (`eval/multistage_quiet.py`,
`eval/multistage_run.py`) hashed differently from [`manifest.json`](manifest.json).
The cause was newline conversion: `core.autocrlf` is true on this machine and
the working copies had been rewritten with CRLF after the freeze hashed them.
All ten frozen modules equal the blobs at `8c3d7b1` byte for byte, and equal
the working copies once CRLF is read as LF. The run uses the frozen code.

### Batch a stopped on a false breach; batch b restarted

About 30 minutes in, `greenhouse_monitor--elevenpowers--0` was ended at stage 1
as a closed-book breach. The agent had grepped its own test data:
`grep -n "timestamp,zone\|T..:..:00,gh" tests/test_ingest.py`. The network
pattern matched the word `gh` anywhere, inside a grep pattern included, and the
multi-stage runner also searched the tool call's description. The household
and library cases' files say `pip install`, so grepping those would have
ended a conversation too.

- **Stopped.** The pattern is part of the seal, so it could not be fixed in a
  running batch. Batch a (`E:/ep-runs/multistage-v3-full-2026-10-30`) holds
  7 complete conversations, 1 ended by the false breach and 4 interrupted,
  for at least $8.93. It is kept, and excluded: it ran under a different seal.
- **Repaired** (`2daad59`). A network command now counts only where a command
  starts, and only the Bash command is read. The tests run both ways, and
  all 10 mutants of the pattern are killed. `eval/multistage_run.py` therefore
  differs from its hash in [`manifest.json`](manifest.json), and that change
  is the whole difference. The cases and the analysis are unchanged.
- **Qualified with no model.** The old and new patterns were replayed over
  1,046 real Bash commands from both v3 batches, both pilots and the held-out
  sweep. Only the greenhouse verdict changes. No held-out breach verdict
  changes, so that published result stands.
- **Restarted.** All 120 slots were sealed again as batch b
  (`E:/ep-runs/multistage-v3-full-2026-10-30-b`). The whole batch is rerun,
  not just the failed slot, so no slot is chosen by its outcome.

### Batch b: 53 complete, 67 lost to the environment

Batch b ran normally for about three hours. Then two things went wrong, and
neither was in the harness or the agents:
- **A network outage, 16:00–16:04 local time.** Every API call got
  `SELF_SIGNED_CERT_IN_CHAIN`: something on the machine or network began
  intercepting HTTPS. Each conversation then failed in about 250 ms, so the
  four lanes ran through their whole remaining queues. 65 slots failed this
  way: 61 at stage 1 with $0 spent, and 4 mid-conversation. A probe at
  16:44 reached the model normally. The cause is unknown.
- **A file lock, at 15:00.** Two conversations crashed between stages:
  Windows refused to swap in an updated `result.json`
  (`PermissionError: [WinError 5]`). The likely cause is the operator's
  progress watcher, which read every `result.json` every 20 seconds. On
  Windows, a file that is open blocks the replace. Later watchers read only
  the lane logs.

Batch b spent $65.35. Its 53 complete conversations stand. The 67 failures
were set by the clock and the file lock, not by any outcome. So they run
again, under the same harness and seal contents, as a continuation batch, and
every batch b slot that did not complete is rerun.
- **Change to the operator's lane script, not the harness:** a lane now stops
  when a slot ends incomplete having spent nothing. One outage then costs one
  slot per lane, not the queue.

### A docs-oracle defect seen in batch a, handled as fixed before batch b is read

Batch a's `gradebook--superpowers--0` had one stale fact, `grades.columns`,
counted at all eight stages. Stage 1 changes the grades file's delimiter to
`;`, and the agent rewrote the documented header as
`student_id;name;course;credits;percent;letter`. That is the header the file
now actually has, but the oracle expects the comma spelling. It is correct
work graded wrong.

The oracle is part of batch b's seal, so it cannot change during the run.
This rule was written down before any batch b result was read:
- **Primary:** the frozen oracle's grade, exactly as pre-registered.
- **Sensitivity:** the same analysis after a general fix: a documented list
  that differs only by a separator the project itself declares is not stale.
  The kept snapshots are regraded.
- **Both are reported.** Any difference between them is attributed to this
  defect. The blind classifier still rates every stale fact.

### As proposed

[`power.json`](power.json) covers twelve cases at the pilot rate of 1.5 lost
groups per superpowers-only conversation, ratio 0.5. With no effect, the test
rejects falsely 1.5–2.3% of the time.

| layout | conversations | power | estimated cost | wall time, four at a time |
|---|---|---|---|---|
| 12 × 2 arms × 4 replicates | 96 | 0.78–0.79 | about $98 | about 2.5–3 h |
| 12 × 2 arms × 5 replicates | 120 | 0.88 | about $123 | about 3–3.5 h |

The cost rests on the pilot's $0.91 per conversation without ElevenPowers and
$1.14 with it, at about 5.4 minutes of model time each. The frozen layout rule
takes the largest affordable layout with power of at least 0.8, which is five
replicates.
