# ElevenPowers internal state: what is built, measured, withdrawn and open (as of 2026-11-22)

All sources are local files in the repository (read 2026-11-22, HEAD `553a25c`). Links are file paths, not URLs. A private acceptance project used for real-project setup checks is referred to only as "a private acceptance project". Numbers are copied as the sources state them; where two sources disagree, both are given.

Abbreviations used by the sources: **VACUOUS** = the repository's own tests stay green with the change's non-test source reverted (the change is not pinned by any test); **v3** = the multi-stage v3 benchmark (12 synthetic Python cases × 8 stages each, "quiet dependents"); **arms**: *ordinary/superpowers* vs *assisted/+ElevenPowers*.

---

## Q1. What components are shipped, and what each does for whom

### Takeaway
ElevenPowers ships a large, heavily tested evidence layer (ledger + computed verification states, discrimination check, reviewer report `ep_review`, TestMiner, changed-region mutation strength, PatchProof bundles, declared rules/milestones, ImpactGraph, test-command discovery, onboarding, five host adapters). Almost every component is labelled by its own records as a *capability* result, with coding benefit explicitly unestablished; the only component-level effects measured as significant are the vacuity reduction (plain Claude Code only) and declared-rule notes being acted on.

### Cited Findings
**Core evidence layer (for the agent and the person accepting its work)**
- Ledger + gate: watches commands the agent already runs, turns output into evidence bound to file fingerprints, and computes `VERIFIED` / `UNVERIFIED` / `STALE` / `CONTRADICTED` when the agent claims done; reporting or completion gating chosen by profile (`off`/`guide`/`strict`). — [README.md](e:/ElevenPowers/README.md) lines 21-27, 52-120
- Fingerprint qualification: PLAN §10 states "Evidence is bound to exact file contents" is "False of the implementation: size and mtime with a `vcs_state` tie-breaker." — [PLAN.md §10](e:/ElevenPowers/PLAN.md)
- "Pre-existing" failures now need proof (2026-11-06): a failure is excused only if shown red on the tree the task opened (recorded with `git stash create`, run at Stop via `stress.already_failing`) or seen red before the first edit. Previously an agent that broke a test then ran the suite twice got VERIFIED. 24 new tests, 22 mutants killed; first version had 8 defects found by independent review. Three older defects found by the same review are recorded as **not fixed yet** (setup/teardown `ERROR` marks whole file red; `-x`/`--maxfail` kept on base run; subfolder test names with backslashes on Windows). — [docs/status.md](e:/ElevenPowers/docs/status.md) 2026-11-06 entry
- Claim inference is regex-only (no model call); measured over 3,557 real turns: 21% over-claim, 25% missed work; obligations attach to 21% of turns that changed nothing (down from 51%). — [README.md "What claims cost" and status table](e:/ElevenPowers/README.md)

**Discrimination / vacuity (`core/stress.py`)** — asks whether anything in the evidence could have failed (a test red on the base tree and green now); `stress.confirm` runs base-red tests against the current tree. PLAN states it does **not** say a change is well tested ("One test that was red on the base tree and is green now satisfies it, however much of the change goes unexercised"). — [PLAN.md §10](e:/ElevenPowers/PLAN.md)

**Reviewer's report `ep_review` (for the person deciding whether to accept an agent's change; built 2026-11-01)** — for any commit pair, runs declared tests in a private head worktree three times (head, change undone, head again) and says PINNED / NOT PINNED / UNKNOWN; `--strength` lists changed lines no test noticed; `--max-mutants/--mutation-seconds` state the budget; 65 tests, 61+40 mutants killed; independent review found 11 defects (7 gave wrong/misleading verdicts), all fixed. Test counts in two commit messages (22, 24) were corrected to 20 and 20. — [docs/status.md 2026-11-01](e:/ElevenPowers/docs/status.md)
- `ep_review --functions` (2026-11-22): runs TestMiner on the head worktree for touched Python functions; lists `partly checked`, `reached, not checked`, `not reached`. Python only, opt-in. — [docs/status.md 2026-11-22](e:/ElevenPowers/docs/status.md)

**TestMiner `ep_testminer.py` (for a developer/reviewer asking "do the tests check this function?")** — slice 1 (2026-11-13): for named Python functions, runs the project's pytest/unittest under coverage.py with per-test contexts, empties the body (extreme mutation, borrowed from Descartes/PIT); verdict `not reached` / `reached, not checked` / `checked` / `unknown` with reason. Slice 2 (2026-11-21): `record -- python -m app ARGS` keeps executed lines + file sha256 (never arguments); `--observed`; multiple extreme values per return type; `partly checked`; survivors confirmed with the whole command. 71 tests. Bounds: detection only, no suggested tests "until independent oracles exist"; Python only; equivalent values give false candidates. — [docs/status.md 2026-11-13, 2026-11-21](e:/ElevenPowers/docs/status.md); [results/testminer/README.md](e:/ElevenPowers/results/testminer/README.md)

**Changed-region test strength (`core/strength/`, for the reviewer)** — optional Cosmic Ray/Stryker mutation of Git hunks/function targets; informational, never alters verdicts. Since 2026-11-11 `strength.at_stop` defaults to false (it was the largest Stop phase, 18.3 s, ended incomplete in 110 of 119 held-out runs, and the agent never sees it); since 2026-11-22 positions inside argument/return annotations are skipped (434f47f). — [docs/status.md](e:/ElevenPowers/docs/status.md) table + 2026-11-11, 2026-11-22 entries

**PatchProof (for reviewers/CI)** — v1 (2026-10-11) identifies a committed patch and exports qualified receipt associations, missing checks, unobserved paths; then OpenAPI contract observations via pinned oasdiff, ImpactGraph integration, explicit `--verify` execution, GitHub Actions summary/artifact export (2026-10-13), external input witnesses v1/v2, remote observations v1 (2026-10-31, never probes; "a remote is never fresh"). Reports are read-only and unsigned. — [README.md "Where this actually is"](e:/ElevenPowers/README.md); [PLAN.md top entries](e:/ElevenPowers/PLAN.md)

**Declared rules / milestones (for the agent, so coupled files stay in step)**
- Milestone verification: optional `elevenpowers.milestones.json` declares earlier-behaviour checks; cross-task receipts; CURRENT/FAILED/STALE/INCOMPLETE/ABSENT view; `ep_check --all` owned runner; declared-check closure (2026-10-19). — [README.md](e:/ElevenPowers/README.md); [docs/status.md table](e:/ElevenPowers/docs/status.md)
- Rule groups (2026-11-04, after NVIDIA Auto-Ontology discover/certify/ground): `ep_milestones --propose` lists file pairs sharing rare words; a person certifies; certified rules produce a pre-edit note naming the other files (and, since repair, a post-shell note for shell writes) and an end-report line when a rule changed in only some files. Proposer now writes each description as an instruction ("`A` and `B` must stay consistent: change both in the same task"). `--add-rule A B` (2026-11-10). — [PLAN.md §13 B](e:/ElevenPowers/PLAN.md); [docs/status.md 2026-11-04/09/10](e:/ElevenPowers/docs/status.md)
- Rules marked in code (2026-11-05): Google IfThisThenThat `LINT.IfChange`/`LINT.ThenChange`, read as ifttt-lint (MIT) reads them; same note + end report. "Not measured: whether agents act on a marked rule." 39 tests, 41 mutants; independent review found 9 defects in first commit, hosted CI a tenth. — [docs/status.md 2026-11-05](e:/ElevenPowers/docs/status.md)
- Other agents' rules (2026-11-10, `core/milestones/scoped.py`): reads Claude `.claude/rules`, Cursor `.cursor/rules`, Copilot `.github/instructions`, subfolder `AGENTS.md`; delivers at most two per file, cut to 600 chars. Bound: Cursor/Copilot assumed from docs to load their own formats; only Claude Code probed. — [docs/status.md 2026-11-10](e:/ElevenPowers/docs/status.md)
- Rule gate (`"rule_gate": true` under `strict`), opt-in, **off by default** after measurement (Q2). — [docs/status.md 2026-11-09](e:/ElevenPowers/docs/status.md)

**ImpactGraph** — Python literal imports/calls/pytest fixtures; optional JS/TS grammar; focused/fallback/support tests. Evidence boundary: "11/12 new valid test refs, 6/12 focused; corrected authored-fault detection 3/3 versus 0/3 old. Partial oracle… no safe exclusion or automatic integration." — [docs/status.md "Shipped and exercised"](e:/ElevenPowers/docs/status.md)

**Declared test-command discovery (`core/test_command.py`, 2026-11-13)** — when no manifest names a test command, borrows the line from `tox.ini`/`Makefile`/CI workflow, reduced to `python -m pytest PATHS` or `python -m unittest`. 5 of 6 held-out projects lacking a command now get one and all 5 pass; 7 already-configured held-out projects unchanged; 22 tests, 13/13 mutants. Python runners only. — [docs/status.md 2026-11-13](e:/ElevenPowers/docs/status.md)

**Onboarding (`ep_setup`, `ep_ready`, `ep_doctor`)** — setup now ends with ~a dozen plain lines (mode, checks found, other agents' rules, declared rules, real problems with fix commands, next step) instead of a 40-line view that read "attention" on a healthy install; `--tests "COMMAND"`. Discovery itself unchanged; guessing pytest from a `tests/` folder was decided against. — [docs/status.md 2026-11-12](e:/ElevenPowers/docs/status.md); [journey/102](e:/ElevenPowers/journey/102-a-healthy-install-that-read-as-broken.md)

**Five host adapters** — Claude Code, Codex, Gemini CLI, Cursor Agent, GitHub Copilot CLI. 2026-11-10 fix: Cursor/Copilot adapters dropped `additionalContext` on `preToolUse` and Codex's `apply_patch` never asked for a brief, so "the measured rule note reached only Claude Code and Gemini" until then. Installed-host acceptance: "full installed acceptance is 1/10 (claude/python, 2026-10-11)" per status table; live sessions on Codex, Gemini CLI, Cursor Agent, Copilot CLI "remain open". — [docs/status.md](e:/ElevenPowers/docs/status.md) 2026-11-10 and "Remaining readiness limits"; contrast architecture card saying "2/10 successes remain historical" — [architecture/index.html](e:/ElevenPowers/architecture/index.html) card `installed-host-acceptance`

**Other built pieces** — ratchet (green state at Stop kept as a private ref; contribution unmeasured); `core/atlas.py` (reports modules missing from architecture maps); `core/assumptions.py` (reports regex patterns that never matched real output); portable report `ep_report`. — [journey/README.md "Where it stands"](e:/ElevenPowers/journey/README.md); [CLAUDE.md](e:/ElevenPowers/CLAUDE.md)

### Inferences
- The shipped surface is broad relative to the measured benefit: the README's ten-item "What it can do today" list presents capabilities, while status.md's evidence column repeatedly says "no coding benefit claimed".
- Two parallel consumer stories coexist in the code: author-side (notes/gates to the agent) and reviewer-side (`ep_review`, PatchProof, TestMiner).

### Gaps
- No single file inventories every `plugin/bin/ep_*.py` command with its status; the list above is assembled from status.md, README and PLAN.
- Installed acceptance count conflicts slightly (status: 1/10; architecture card: 2/10 historical, Claude/Python and Claude/JavaScript).

---

## Q2. Every measured outcome, with numbers and qualifications

### Takeaway
One large, pre-registered, significant effect exists: plain Claude Code's resolved patches were VACUOUS 84% vs 37% with ElevenPowers (p = 0.00016), driven by whether a test is written at all — but with superpowers installed there is nothing to reduce (1 of 475 vs 0 of 472). Declared rule notes are acted on (35/50 → 4/50 lost with perfect certification; 31/50 → 15/50 with a model reviewer's certification), while the coding-helper comparison against superpowers (v3) showed no benefit with point estimates leaning against ElevenPowers, the reviewer study showed no measurable gain (18/21 vs 20/21, p = 0.5), and a rule gate converted 0 of 7.

### Cited Findings

**Held-out vacuity sweep (2026-10-22/23) — the "one measured effect"**
- 40 tasks, 12 permissive pure-Python repos; 40 × 2 arms × 3 = 240 runs, Sonnet 5.5 medium, 900 s cap, closed book, sealed, never retried; analysis committed before any run. — [results/heldout/sweep-2026-10-22/README.md](e:/ElevenPowers/results/heldout/sweep-2026-10-22/README.md)
- Graded runs 120 vs 118; resolved 88 vs 89; VACUOUS among resolved **74 (84%) ordinary vs 33 (37%) assisted**. Primary per-task Wilcoxon signed-rank **p = 0.00016** over 18 tasks whose arms differ: assisted lower on 17, ordinary on 1 (uvicorn-31e3e00f), 13 tied, 9 dropped. — same
- Resolve rates did not differ (assisted better on 3, ordinary 1, 36 tied; sign test p = 0.625). Cost $7.80 vs $11.11 (1.4×). — same
- Mechanism (descriptive): 106 of 107 VACUOUS patches contained no test file; 69 of 70 non-VACUOUS did; resolved ordinary patches added a test in 14 of 88 runs, assisted 56 of 89. — same
- Bounds stated: one model, one host (Claude Code), Python only, 12 repos, small fixes (median 10 changed lines), "Not a population estimate"; ordinary arm is plain Claude Code — no superpowers in either arm; both arms carried the operator's own `~/.claude/CLAUDE.md`; "VACUOUS… is not correctness"; frame exclusions listed; 2 of 240 ungraded (one closed-book breach excluded, against the assisted arm); the pre-registered analysis was accidentally run once early on 232 of 240, nothing changed in response. — same
- Time: sweep table reports "mean model-process seconds 27.3 vs 85.2" (≈3.1×); the overhead read says that is **wall time**: wall 25.3 s vs 83.6 s, model 23.9 s vs 31.5 s (≈1.3×), 52.1 s of the assisted run outside the model; Stop's test-strength phase averaged 18.3 s. — [results/heldout/overhead/README.md](e:/ElevenPowers/results/heldout/overhead/README.md). PLAN's 2026-10-23 top entry still says "about 3.1x the model time" — [PLAN.md](e:/ElevenPowers/PLAN.md) (inconsistent with the corrected overhead record).
- Post-hoc (not pre-registered): oracle gap +6.7 ordinary / +4.2 assisted (resolved), from 3-5 disagreeing tasks, "still unsettled"; best-of-3 ordinary covers 17.5% of tasks with a resolved-and-tested candidate vs 47.5% for a blind assisted pick; edit-by-edit replay found 1 of 85 runs with a better earlier state (148 of 238 replayable; 90 edited through the shell). — [results/heldout/sweep-2026-10-22/README.md](e:/ElevenPowers/results/heldout/sweep-2026-10-22/README.md); [docs/status.md 2026-10-23](e:/ElevenPowers/docs/status.md)

**Vacuity with superpowers in both arms (v3 snapshots, 2026-11-01, $0, pre-registered)**
- Superpowers alone left **1 VACUOUS stage of 475 resolved**, vs **0 of 472** with ElevenPowers; 11 of 12 cases tied, **p = 1.0**; forward check 130/130, adversarial control 24/24. Bound: "pinned" is the coarse bar (at least one test fails with the whole change undone), not every line. — [PLAN.md §13 A](e:/ElevenPowers/PLAN.md); [docs/status.md 2026-11-01](e:/ElevenPowers/docs/status.md); [results/multistage-v3/vacuity/README.md](e:/ElevenPowers/results/multistage-v3/vacuity/README.md)

**Multi-stage v2 (2026-10-28 pilot)** — 4 conversations, $3.39; neither arm lost earlier behaviour; all five stale facts were oracle defects; "Sonnet 5.5 with superpowers alone found its dependents and kept the docs current on both cases" → no headroom. Harness faults found first: Skill tool missing from launcher (superpowers could not load); operator's CLAUDE.md carried in every subscription run. — [PLAN.md 2026-10-28](e:/ElevenPowers/PLAN.md)

**Multi-stage v3 pilot (2026-10-28)** — $4.09, 32/32 stages qualified; superpowers alone broke earlier behaviour on both cases; no docs fact went stale in any arm. — [results/multistage-v3/README.md](e:/ElevenPowers/results/multistage-v3/README.md)

**Multi-stage v3 full run (2026-10-30)** — 12 cases × 2 arms × 5 replicates, 120/120 comparable, superpowers 7.0.0 both arms, Sonnet 5.5 medium:
- Earlier groups lost **29 (superpowers) vs 35 (+ElevenPowers)**; cases better/worse/tied 3/6/3; p 0.43, **Holm 0.50**.
- Stale documented facts (stage-summed) **43 vs 79**; 1/5/6; p 0.25, **Holm 0.50**.
- Cost $1.22 vs $1.12 per conversation; wall 10.8 vs 6.5 min (corrected from "model time"; model time per stage 36.2 s vs 34.3 s); total $153.40.
- Qualifications: measured superpowers loss rate 0.48 per conversation, about a third of the pilot's 1.5, so less power than planned; "a small benefit cannot be excluded. A large one is not supported: the point estimate is a 21% increase." Stale facts summed over stages (one fact can count up to 8 times). — [results/multistage-v3/README.md](e:/ElevenPowers/results/multistage-v3/README.md); [PLAN.md §10](e:/ElevenPowers/PLAN.md)

**v3 diagnosis of the 31 ElevenPowers-arm losses ($0, 2026-11-01)**
- 27 not detected (22 dependents import no edited file; 5 behind the brief's four-name "+N more" cutoff); 4 detected, delivered and not acted on; agent edited the dependent in 0 losses. — [results/multistage-v3/README.md](e:/ElevenPowers/results/multistage-v3/README.md)
- Delivery probe ($0.46): model quoted the PreToolUse brief word for word; with hook silent answered NONE. — same
- Behaviour-diff spike would have caught 1 of 31 ("30 dependents were left behind with unchanged behaviour"). — same; [PLAN.md §13 B](e:/ElevenPowers/PLAN.md)
- False startup FAIL in 391 of 621 stages (63%) from `parsers.claims_to_run_tests` matching "tests" anywhere (e.g. `sed -n 1,12p tests/test_x.py`); repaired (`d07a9d8`); replay over 2,022 Bash commands now files none. — [results/multistage-v3/README.md](e:/ElevenPowers/results/multistage-v3/README.md)

**Coding-helper $0 spikes on v3 (2026-11-02 to 11-05)** — all from [PLAN.md §13 B](e:/ElevenPowers/PLAN.md):
- Shared rare tokens: broken dependent in top 3 in 17 of 31 losses (control 5 of 31); held out 4 of 17 (control 0); as a standing warning it "is noise": warns on 73–88% of self-contained stages; ~1 named file in 60 is a declared dependent.
- Co-readers: held out 5 of 17 top-3 (control 0); in-sample 11 of 31 under pre-set bar 14; not built. Same state: 0 of 17; not built. Data flow: 4 of 51 vs 17 needed; not built. On 51 never-read dependents shared tokens 16 in top 3 (control 6, random 3.1).
- Rule-group proposals: 50 per project cover 20 of 51 never-read dependents (control 11, random 3.9; pre-set bar 17). Rules outside functions: 20 of 51 either way, under bar 23; reverted.
- Real history (pre-registered, $0): 160 quiet co-changes from click/attrs/rich/pytest; proposals at K=50 covered 60, same as control; co-change history 93 vs control 90; "Proposals are therefore not shown to find undeclared rules in real code."
- Real projects: protocol-method pairs head lists (44% of click's top 50, 84% of rich's vs 6% on v3).
- Brief cutoff re-ranking: tracks file size; another stage's edit does as well (7 of 12 vs 5 of 12).

**Rule notes acted on (PLAN §13 B open problem 2)**
- Perfect (simulated) certification, 2026-11-04: dependent lost **35 of 50 control vs 4 of 50 rules**, 100 one-stage runs on five stages where v3 lost most, exact one-sided stratified **p = 8.6 × 10⁻¹³**; no other group lost; cost +8.5%, model time +8%; $16.39. Bounded: "certification was simulated as perfect, on stages chosen for their known losses." Pilot ($1.63) found 3 of 6 rules-arm runs wrote through Bash and never saw the note; repaired before sealing. — [docs/status.md 2026-11-04](e:/ElevenPowers/docs/status.md); [results/rule-groups-acted-on/README.md](e:/ElevenPowers/results/rule-groups-acted-on/README.md)
- No-harm follow-up: 53 other stages once per arm, 106 runs, $15.52: 0 of 53 other groups lost each; 0 of 28 needless declared-file edits each; covered dependent lost 2 of 20 in each arm; "rules out a harm of about 20 points, not a small one"; cost +3%; shell note hook +66 ms per shell command. — [docs/status.md 2026-11-04](e:/ElevenPowers/docs/status.md)
- Model-reviewer certification (2026-11-05): blind tool-free Sonnet 5.5 kept 16 of 27 pairs that matter ($1.44); rerun 100 runs $16.35: **31 of 50 vs 15 of 50**, **p = 7.3 × 10⁻⁵**; 10 of 15 rules-arm losses are `parcelpost` 5 (pair dropped, no note); on the four covered stages 5 of 40 vs 22 of 40; cost +8%. Bounded: "a model reviewer, not a person who knows the project." — [docs/status.md 2026-11-05](e:/ElevenPowers/docs/status.md)
- Instruction wording ("change both"): first run 2 of 20 vs 6 of 20 lost, one-sided p = 0.12, $6.76, treated as null; confirmation (fresh, sealed, not pooled) on `household_budget` 7, 60 per arm: **5 of 60 vs 23 of 60**, one-sided **p = 8.3 × 10⁻⁵**, $18.68; bounds "one stage, one model, one generated sentence". Harm check on 45 stages: 3 vs 3 lost a group (p = 0.75), 2 vs 2 needless edits, $13.21. On `claude-sonnet-5`, 40 per arm: 0 of 40 vs 0 of 40 lost ($31.73), so benefit "stated for Sonnet 5.5 only". — [docs/status.md 2026-11-09/10](e:/ElevenPowers/docs/status.md)
- Other agents' rules probe: a real Claude Code session quoted a Cursor rule it never opened; control said NONE ($0.13). — [results/scoped-rules/README.md](e:/ElevenPowers/results/scoped-rules/README.md)

**README's "~90% vs ~30%" instruction-following claim** — README item 10: "in tests, a rule shown this way was followed about 90% of the time, against about 30% when there was no rule." — [README.md line 38](e:/ElevenPowers/README.md). The README line itself does not carry the bounds (simulated perfect certification, stages selected for known losses, Sonnet 5.5, superpowers in both arms).

**Rule gate (2026-11-09, 98 runs, $18.36)** — gate sent back 7 runs that had left the dependent; **0 of 7 converted** (all explained a scope choice and stopped). Primary `household_budget` 7: 7 of 25 (gate) vs 10 of 25 (note), one-sided p = 0.28; the gap is runs that had already changed the file before first stop. Harm stages 1 of 24 vs 0 of 24 (p = 0.5). Cost about a tenth more, ~15 s more per run. $0 replay on 153 saved runs: file-level finding fired on all 9 covered losses and on 21 of 132 correct runs (16%); function-level would fire on 6 of 132 but miss all three `parcelpost` losses. Stays off by default. Untested: "A gate with no way out." — [results/rule-gate/README.md](e:/ElevenPowers/results/rule-gate/README.md); [docs/status.md 2026-11-09](e:/ElevenPowers/docs/status.md); [journey/100](e:/ElevenPowers/journey/100-told-twice-and-chose-the-same.md)

**Reviewer-benefit study (PLAN §13 A.3, 2026-11-02, $5.23, pre-registered)** — 21 W (wrong: one Cosmic Ray mutation on a changed line the tests miss), 11 C (control), 11 U (tests removed) seeds; 86 calls; reviewer Claude Sonnet 5.5 medium, no tools; report = `ep_review --strength` at 32 mutations/300 s. W caught **18 of 21 diff alone vs 20 of 21 with report**, discordant 2/0, exact sign **p = 0.5**; U caught 9 of 9 both; C false alarm 9 of 10 both. Cost $2.49 vs $2.74. Exploratory: diff arm at ceiling (86%); grading not specific (control's own report lists the seeded spot as unpinned in 11 of 11; reviewer named it in 2 of 9 diff vs 6 of 9 report control replies); report is acted on (mean problems 4.4 vs 3.1), so "read and ignored" falsifier does not fire; reviewer requested changes on 9 of 10 correct controls in both arms. Bounds: model not person; mutation-shaped seeds favour the report; one call per seed per arm, twelve v3 projects. At default budget 8, seeded line surfaced 6 of 11; at 32, 11 of 11 first-round (20 of 21 per PLAN). — [results/reviewer-benefit/README.md](e:/ElevenPowers/results/reviewer-benefit/README.md)

**Mutation survivors B7 / B8 (2026-09-24)**
- B7: on the rehearsed corpus with gold patch applied, 27 of 98 diff-scoped mutants survived on 9 of 16 tasks; reverting the gold patch killed on 16 of 16 (so discrimination says DISCRIMINATES everywhere) yet 9 of 16 carry a surviving mutant; two blind reviewers called 20 of 27 MEANINGFUL, exactly 1 unanimously equivalent. Agent vs gold on 15 tasks: 28 of 89 vs 27 of 91 survive (all gate-arm patches, 12 Opus 5). — [PLAN.md §10, §12](e:/ElevenPowers/PLAN.md)
- B8: 36 agent runs, `claude-opus-5-5` effort high, at least $22.14 (two timeouts returned no cost); told exactly which mutants survived, Opus 5.5 killed all 54, partly by tests on private internals, message text, internal argument types, and "killed" the unanimously equivalent mutant by asserting which slice expression the source uses. Conditions: runs carried the user's plugins (superpowers) because `--bare` needs an API key. Conclusion: raw mutants are never agent instructions; consumer is a reviewer. — [results/b8-feedback/findings.md](e:/ElevenPowers/results/b8-feedback/findings.md); [PLAN.md §10, §12](e:/ElevenPowers/PLAN.md)
- B9: paired chunks sweep, 10 of 46 resolved vanilla patches VACUOUS (22%) vs 4 of 49 gate (8%); per task fewer under gate on 5, more on 0, tied 19, p = 0.062; all 14 vacuous contained no test file. — [PLAN.md §10](e:/ElevenPowers/PLAN.md)

**Overhead measurements**
- Held-out: see above (wall 25.3 vs 83.6 s; model 23.9 vs 31.5 s; strength 18.3 s/Stop; removed by `at_stop=false`, "an estimate from those records; no new sweep was run"). — [results/heldout/overhead/README.md](e:/ElevenPowers/results/heldout/overhead/README.md)
- v3: ~33 s per stage outside the model; real Stop runs median 5.3 s (test strength 0.6 s); transcript clocks put the 34.9 s per-stage gap as 18.4 s tool calls, median 10 s after last event (Stop), 1.4 s startup. Edit hook timing stated as "An Edit took 2.31 s against 0.03 s" in PLAN §13 B but "3.17 s against 0.03 s" in status.md 2026-11-03 (sources disagree). Cuts: hooks no longer wrapped in PowerShell (0.17–0.26 s per call saved; `407d749`), `ep_check --all` 3.44 s → 2.13 s (`97db162`). Paid check $0.62: Edit 0.63 s vs 0.96 s with order controlled; a larger first-pair gap not claimed. — [PLAN.md §13 B item 4](e:/ElevenPowers/PLAN.md); [docs/status.md 2026-11-03](e:/ElevenPowers/docs/status.md)
- Rule notes: +8.5% / +8% / +3% cost in the three runs above; rule gate ~+10% spend, ~15 s per run.

**TestMiner rehearsals ($0)**
- Slice 1: cachetools + more-itertools, 10 functions each (18 functions in all per README limits); in their own environments every function `unknown` (no coverage.py installed — "the usual case"); with coverage.py all checked except cachetools `_HashedTuple.__getstate__` (false candidate, equivalent mutant); `take` a real detection via timeout. Found: main parser read pytest 9 `366 passed, 8 subtests passed` as 0 passed in every hook (fixed 575d24e). Final review: 1 Critical + 7 Important findings, all but one fixed. — [results/testminer/README.md](e:/ElevenPowers/results/testminer/README.md)
- Slice 2: charset_normalizer at 3985662; `record` kept 1308 executed lines in 12 files; 88 functions observed, 12 examined; first run gave false `partly checked` on `unicode_range_languages` (lru_cache filled by an earlier test) — fixed by whole-command confirmation (d3f4f89); second run: no candidates in 12. "an illustration… not a rate." — same

**Review-functions rehearsals ($0, 2026-11-22)**
- Six charset_normalizer maintainer fixes: all PINNED; functions section no false alarms; found no unchecked function. Two faults fixed first (TestMiner kept 15 s per-run default → 2 of 6 `baseline timed_out`; Git Bash `/e/...` interpreter misreported as missing coverage.py). — [results/review-functions/README.md](e:/ElevenPowers/results/review-functions/README.md)
- Agent changes from held-out sweep: 13 runs (corrected from 14); verdict NOT PINNED 11, PINNED 1, UNKNOWN 1; functions section measured on 9 (corrected from 10); one function listed (`multi_byte_usage`, real); 8 of 9 measured were NOT PINNED. Function-level extreme mutation "does not find an untested edit inside a tested [function]". — same
- `--strength` on same changes: first run found annotations mutated (`key: str | bytes` → `str + bytes`) under `from __future__ import annotations`, survivors 8 of 20 and 11 of 20 on two pyjwt changes → 2 of 20 and 1 of 14 after fix. On eight NOT PINNED changes: line mutation named unpinned lines in the agent's work on 2, functions section on 1; "The review's own verdict, the coarsest of the three, is the only one that flagged all eight." — same

**In-the-wild follow-up fixes (2026-11-06, $0, pre-registered)** — merged agent PRs changing code without touching a test vs touching one: Mantel–Haenszel within repository OR **0.91 (95% CI 0.54–1.54)** over 2,253 PRs in 165 repos; permutation p = 0.70; pooled 5.3% vs 3.9% (Fisher p = 0.16); by agent 1.28 (0.86–1.90); logistic with size 1.46 (0.98–2.18); power 39% at OR 1.5; "inconclusive". Note the exposure is "touched a test", not the vacuity probe. — [results/wild-followup/README.md](e:/ElevenPowers/results/wild-followup/README.md)

**Earlier gate-era measurements (Sept 2026)**
- Gate as classifier 1/28 complete cases falsely blocked (3.6%), 0/18 incomplete missed (46 scenarios). Live blocking 75% → 12% of runs (16 runs); later 8% (6 events across 4 of 50). Gate graded at block: fired 4 times across 19 runs, changed no outcome; cost 1.3× vanilla over 50 vs 50 runs; "benefit is unmeasured after $195"; 80% of first proposals already correct. 42% (123 of 295) preserved passing suite records were wrong (`pytest | tail`). Pinned baseline 68.9% / 73.3%, $67.42. — [README.md table](e:/ElevenPowers/README.md); [PLAN.md §10](e:/ElevenPowers/PLAN.md)
- Matched four-stage comparison (2026-10-17): both pairs tied 10/10 groups; assisted model-process time 2.34× Python, 1.90× JavaScript; JavaScript owned-runner adoption 0/4. — [README.md](e:/ElevenPowers/README.md)
- Field report (2026-10-23): three developers, "Recorded as told, not measured": docs kept current ~95% with superpowers+ElevenPowers; dependent-breaking fixes met once or twice with superpowers, not with ElevenPowers. — [docs/status.md](e:/ElevenPowers/docs/status.md)

### Inferences
- The README's "about 90% vs about 30%" matches the perfect-certification acted-on run (4 of 50 lost ≈ 92% kept; 35 of 50 lost = 30% kept). It does not match the confirmation run (5/60 vs 23/60 lost ≈ 92% vs 62% kept). If that is its source, the README line drops the bounds that run carries (simulated perfect certification, stages chosen for their known losses, one model) and rounds them away. Worth flagging in a direction review.
- The held-out benefit and the v3 null are consistent rather than contradictory. Superpowers already makes the agent write tests (1 VACUOUS in 475), so the vacuity effect is a substitute for practice that superpowers users already have.
- In the reviewer study, the coarse whole-change verdict caught all eight NOT PINNED agent changes. The finer instruments caught 1-2. So the cheapest signal may be the one that carries the most value.

### Gaps
- No measurement with human reviewers exists. The 2026-11-05 synthesis says it needs at least 60 developers and recruitment.
- Nothing has been measured on hosts other than Claude Code, on languages other than Python (for the benefit studies), or with models other than Sonnet 5.5/Sonnet 5/Opus 5.5.
- The marked-rules (`LINT.IfChange`) and other-agents'-rules features have not been measured with agents (beyond a $0.13 one-turn probe).
- The composition baseline (`eval/stack.py`) "has never been run".

---

## Q3. PLAN.md §13: the two directions and the order of next steps

### Takeaway
§13 (2026-11-01) makes **reviewer evidence** (A) the current focus because "it has the one measured effect", and **coding helper** (B) "next after A, open to contributors meanwhile", with its failures written down. A's three steps are: design the reviewer view, then measure against superpowers, then measure reviewer benefit. All three are recorded as done/run, and the reviewer-benefit result was null. Maintainers take up B "once A's three steps are done".

### Cited Findings
- "Both stay in scope. The order follows the evidence: build first where a benefit has been measured, and keep the other open with its failures written down." — [PLAN.md §13](e:/ElevenPowers/PLAN.md)
- **A. Reviewer evidence.** For whom: "the person deciding whether to accept a change an agent made." What it says: whether the change is pinned by tests that would fail without it, the lines that could be altered without anything noticing, and receipts. Already built: PatchProof receipts/bundles, `core/stress.py`, `core/strength/`, end report, GitHub presentation. — same
- A next steps, in order: (1) design the reviewer's view (pinned or not, unpinned lines, what was run on which tree, what is unknown), with spec first. *Built 2026-11-01 as `ep_review`.* (2) Measure against superpowers, $0 first. *Done 2026-11-01:* nothing to reduce, "the reviewer value for superpowers users is the report". (3) Measure benefit to a reviewer by seeding known unpinned/wrong lines. *Run 2026-11-02: no measured benefit for a model reviewer.* "The next test needs defects the diff does not show, or human reviewers on large changes, where reading is the cost." — same
- **B. Coding helper.** Goal: "fewer earlier behaviours broken and fewer docs left stale while an agent works. Status: no measured benefit. Do not claim one (§10). Owner: the maintainers take this up once A's three steps are done." Open problems: (1) left-behind dependents, (2) getting a delivered warning acted on, (3) brief cutoff, (4) overhead. Gate for any claim: "a no-model replay on the kept v3 snapshots first, then a paired run with superpowers in both arms, under the same sealing and pre-registration as v3." — same
- Still open under B2: "what people who know the project certify"; whether wording that declares files "coupled as a whole" does better (untested); "the 31 never-read dependents that no proposal covers." — same
- A later research synthesis (2026-11-05) recommends "**from advice to gates, and from the reviewer to the author**". Keep the vacuity check, declared rules and hash-bound evidence. Stop briefs whose information the model can find itself, automatic rule discovery, leading with PatchProof for human reviewers, LSP/memory/planning layers, and resolve rate as the outcome. Directions considered: (1) gates in the agent's loop (recommended first); (2) a CI check for agent PRs sold to teams ("no one was found checking discrimination against the base"); (3) weaker models; (4) "Park the project. An honest option: the generic layer now ships with the host." — [docs/research/audit_2026_11_05/README.md](e:/ElevenPowers/docs/research/audit_2026_11_05/README.md)
- Its cheapest tests and their outcomes: (1) does non-discrimination matter in the wild? Inconclusive (OR 0.91). (2) A pre-existing-failure check: found already there and wrong, now fixed. (3) Declared-rule gate vs note: the gate did not beat the note (0 of 7). (4) The human-reviewer study is "only if test 1 holds" and is not run. The synthesis says: "the test-discrimination and pre-existing gates are a different case. They answer a factual question the agent can be wrong about." — same
- Work after the synthesis follows a "build list" (journey 101 = item 3, making the "fix comes with a real test" check cheaper; journey 102 = item 4, two-minute onboarding). Then came test-command discovery, TestMiner slices 1-2, and `ep_review --functions`. — [journey/101](e:/ElevenPowers/journey/101-the-agent-waited-for-a-report-it-never-read.md); [journey/102](e:/ElevenPowers/journey/102-a-healthy-install-that-read-as-broken.md); [docs/status.md](e:/ElevenPowers/docs/status.md)

### Inferences
- PLAN §13's sequence for A is finished on paper. Its stated continuation (defects the diff does not show, or human reviewers) has no dated plan in PLAN. Recent work (TestMiner, `--functions`) extends the reviewer report's instruments rather than running that next benefit test.
- The 2026-11-05 synthesis partly redirects §13: author-side gates instead of reviewer-side reports. PLAN's dated top entries stop at 2026-11-01, so PLAN has not been updated to reconcile §13 with the synthesis, the rule-gate null or the build list.
- Under the synthesis, an untested candidate remains: a *vacuity/test-discrimination gate* at Stop. It asks a factual question, which the synthesis distinguishes from the rule gate that failed.

### Gaps
- The "build list" (items 1-4+) referenced in journeys 101/102 is not found in any tracked markdown file. Its full content and remaining items could not be read.
- PLAN.md has no dated entry after 2026-11-01. The latest state lives in docs/status.md (through 2026-11-22).

---

## Q4. What is withdrawn or refuted (PLAN §10) and the falsifiers in §12

### Takeaway
§10 is a long, dated ledger of withdrawn and qualified claims. The most direction-relevant are four. "ElevenPowers keeps earlier work and docs intact for a superpowers user" is not supported. "The gate improves the patch" has no support. "The discrimination check tells you the change is well tested" is false. "Killing a mutant means the test pins behaviour" is false. Of §12's falsifiers: "almost none of our evidence is vacuous" has **fired for superpowers users** (474 of 475 stages discriminate). "No better intermediate state" is nearly fired (1 of 85). "Mutant feedback produces implementation-pinning tests" fired (B8). "Surfacing changes nothing" / "reviewer does not act on unpinned lines" did not fire, but no gain was shown.

### Cited Findings
**Selected §10 entries (all [PLAN.md §10](e:/ElevenPowers/PLAN.md))**
- "ElevenPowers keeps earlier work and docs intact for a superpowers user." **Not supported, 2026-10-30** (29 vs 35 groups lost, 43 vs 79 stale facts, Holm p 0.50). It stays open only as §13's coding-helper direction.
- "A person's description of the rule would not point at the filename" (parcelpost lead). Withdrawn 2026-11-05: a blind describer named the same filename rule, and the stage breaks a different coupling (`groupby` relies on line order).
- "10.8 minutes of model time against 6.5" (v3). Corrected 2026-11-03: it is wall time; model 36.2 s vs 34.3 s per stage.
- "The Stop hook's mutation step is most of the gap, 16 s of a 21 s Stop." Withdrawn the same day: the replays committed each stage's start, while the real runs did not. Real Stop median 5.3 s, strength 0.6 s.
- "The low vacuity rate shows agents rarely finish on evidence that could not have failed." Reopened 2026-09-24, then settled by the held-out sweep: "The low rate was the mechanism's effect, not the phenomenon's absence" (84% vs 37%).
- "Agents routinely finish on evidence that could not have failed." Qualified 2026-09-17 (1 in 22). Restored for the held-out method only: "Restored for that method, that corpus and Sonnet 5.5 medium only."
- "An agent's own tests pin its change less than a maintainer's." Withdrawn 2026-09-24 (28/89 vs 27/91).
- "Killing a mutant means the test pins behaviour." False (B8).
- "The discrimination check tells you the change is well tested." Stated as false 2026-09-23. Reverting gold killed 16 of 16, yet 9 of 16 carry surviving mutants.
- "This system improves the logic, the edge cases, or the bugs." "Never true… Nothing shipped generates a test, infers a property, searches for an edge case, or evaluates whether code is correct."
- "Targeted reproductions went from 0 of 16 to 6 of 16." Withdrawn: wrong in both directions (shell metacharacters in node ids; missing `PYTHONPATH=src`); the true figure is 16 of 16.
- "The gate improves the patch." No support: 4 firings in 19 graded runs changed no outcome; cost 1.3×; "benefit is unmeasured after $195".
- "A gate that detects a real defect will improve the outcome." Withdrawn 2026-09-15: detection and prevention are separate.
- "The neighbourhood brief fires on 47% of files a real commit touched." Qualified: the delivered rate "close to zero" before the 2026-09-19 fix.
- "A plain agent resolves 92 percent of the selected corpus." Withdrawn: 24 of 100 runs named their own fix commit sha.
- "Denying the answer tools makes a run closed-book." Withdrawn: pip cloned git URLs internally.
- "None of the surveyed systems computes completion from evidence" is "no longer a description of the field". At least two shipping projects arrived at no-evidence-no-close with stale-on-edit. The remaining structural advantage is "discrimination and the ratchet".
- External-figure corrections: 6.2 → 6.4 points benchmark inflation; the ORACLE-SWE "+28pp" is qualified (only the ranking survives); the critic collapse (AUROC 0.936, the 26-point collapse is HotPotQA, non-coding); the rule of three misapplied (exact bound 19.81%/22.84%).

**§12 falsifiers and their state (all [PLAN.md §12](e:/ElevenPowers/PLAN.md))**
- "Almost none of our recorded evidence is vacuous" ("the single most falsifying measurement… costs $0"). *2026-11-01: for superpowers users it has fired*: in 474 of 475 resolved v3 stages a test failed on the reverted tree. Plain Claude Code remains at 84% VACUOUS.
- "No better intermediate state ever exists." Not marked in §12. The held-out replay found 1 of 85 runs with a better earlier state: "a ratchet back to the best earlier state has almost nothing to recover" — [results/heldout/sweep-2026-10-22/README.md](e:/ElevenPowers/results/heldout/sweep-2026-10-22/README.md)
- "The oracle gap is under four points." Held-out +6.7 / +4.2, unsettled (3-5 disagreeing tasks).
- "Derived reproduction tests are wrong often enough to cost more than they buy." No derived-test generator is built, so this is untested.
- "A best-of-breed stack already does this" (Superpowers + ECC + gstack + Aider). "`eval/stack.py` exists; it has never been run." Partially informed by v3 (superpowers alone leaves almost no VACUOUS changes and found its dependents in v2).
- "Surfacing changes nothing either." The reviewer study found the report is acted on (more problems raised) but without a gain.
- "Diff-scoped mutants almost never survive." *Did not fire*: 27 of 98 survived on 9 of 16 tasks.
- "The survivors are equivalent mutants." *Did not fire*: 20 of 27 meaningful, 1 unanimously equivalent.
- "Mutant feedback to an agent produces tests that pin the implementation." *Fired* (B8). So raw mutants are never agent targets, and the consumer is a reviewer.
- "A reviewer does not act on a list of unpinned lines." Not fired literally (20 vs 18, "no more" condition not met), but p = 0.5 and no benefit shown — [results/reviewer-benefit/README.md](e:/ElevenPowers/results/reviewer-benefit/README.md)

### Inferences
- The falsifier that fired for superpowers users removes the agent-side vacuity benefit for that population. What remains is the report, and its measured benefit is null with a model reviewer.
- The un-run composition baseline is the falsifier PLAN itself calls "the comparison that matters". v3 is effectively a partial version of it (superpowers only), and it came out null-to-negative.

### Gaps
- §12 has not been updated to mark the "no better intermediate state" falsifier against the held-out 1-of-85 result. Whether the authors regard it as fired is not stated.

---

## Q5. Roadmap cards in architecture/index.html (Planned tab)

### Takeaway
The roadmap (meta updated 2026-11-22) lists 7 "Open milestone" cards. They cover coding intervention, installed-host acceptance, ordinary-session overhead, ImpactGraph, PatchProof, TestMiner and cross-milestone verification. It also lists 17 "Planned research" cards, mostly search/selection/repair-loop research from PLAN phases C–E, plus "Proposed" and "Conditional" cards. Some card summaries lag the latest results.

### Cited Findings (all from [architecture/index.html](e:/ElevenPowers/architecture/index.html), roadmap data ~lines 7330-8200; `"updated": "2026-11-22"` at line 306)
**Open milestone**
- `held-out-benefit`, "Demonstrate a useful coding intervention": "Completed multi-stage comparison: two correctness ties, higher assisted process time and mixed owned adoption. A useful coding intervention remains unproved."
- `installed-host-acceptance`: "Complete real Python and JavaScript exercises across all five supported coding hosts". 2/10 successes (Claude Code 2.1.292, Sonnet 5.5 medium) "remain historical until requalified; eight other cells remain open."
- `ordinary-session-overhead`: "Measure callback, evidence-read and verification costs during normal development on unrelated projects."
- `impact-graph`: qualify remaining subprocess/framework relationships, recommendation noise and native-session cost (11/12 valid refs; 3/3 vs 0/3 authored faults).
- `patch-proof`: extend with further qualified adapters; "Reviewers also need the connection between a patch, affected contracts, applicable checks and the properties those checks establish."
- `test-miner`: "Two slices built… Suggested tests remain."
- `cross-milestone-verification`: two correctness ties, current Python and stale exact JavaScript milestones.

**Planned research**: evaluation-boundary (contained evaluation environment / OS boundary); composition-baseline ("eval/stack.py has not supplied that result"); edit-checkpoints; checkpoint-contribution (ratchet value unmeasured); independent-oracles; candidate-pools; candidate-selection; reproduction-synthesis; diagnosis-branching; localisation-expansion; fresh-context-repair; complementary-workers; lock-in-monitor; allocation-policy; blocking-ablation; correct-candidate-survival.

**Proposed**: open-code-map, ci-evidence-import, contributor-exercise-kit. **Conditional**: static-test-impact, dynamic-invalidation, workflow-compiler, context-budgets, cross-session-memory, model-routing, additional-critics, expanded-harness.

### Inferences
- The `held-out-benefit` card's summary cites the matched four-stage comparison (2026-10-17). It does not mention the held-out vacuity sweep's significant result, the v3 null, the reviewer-benefit null or the rule-note results, so the card is stale against PLAN §13 and status.md.
- `edit-checkpoints` ("Discover whether a useful verified intermediate state is lost") appears to be partly answered by the held-out replay (1 of 85), yet it is still listed as planned.
- No roadmap card exists for either §13 direction as framed (a reviewer-benefit study with humans, or left-behind dependent detection / rule groups).

### Gaps
- The exact count of 17 Planned research cards comes from the grep of `"status": "Planned research"` lines (7676-8010). The card bodies beyond title/summary/why were not read.

---

## Q6. Recurring failure patterns recorded in journey/ and status

### Takeaway
The project's dominant recurring failure pattern is a claim about external or harness behaviour written before running the real producer. It is found within hours by a real run, and appears as false positives, parser misreads, harness faults and withdrawn numbers. A second pattern is that independent reviews regularly find 8–11 defects in each "done" first version. Third, the agent's losses are often judgements, not oversights.

### Cited Findings
- CLAUDE.md "Run the producer before you write the pattern": on 2026-09-17 "seven defects shipped in a day and every one was of this kind… all seven surfaced the instant the real producer was run." The rule is enforced by `core/assumptions.py`. — [CLAUDE.md](e:/ElevenPowers/CLAUDE.md)
- The rehearsal that cost nothing corrected two published figures (shell metacharacters in node ids; missing `PYTHONPATH`). These were "not caught by reading, by the test suite, or by an external audit that reproduced fourteen other probes." — [PLAN.md §10](e:/ElevenPowers/PLAN.md); [CLAUDE.md](e:/ElevenPowers/CLAUDE.md)
- False positives found only by real runs:
  - `claims_to_run_tests` matched "tests" anywhere, causing a false startup FAIL in 63% of v3 stages ([results/multistage-v3/README.md](e:/ElevenPowers/results/multistage-v3/README.md));
  - `pip install pytest` was read as a test run ([journey/103](e:/ElevenPowers/journey/103-the-command-was-already-written-down.md));
  - the pytest 9 "N subtests passed" summary was read as 0 passed in every hook ([journey/104](e:/ElevenPowers/journey/104-reached-is-not-checked.md));
  - an lru_cache-hidden test produced a false `partly checked` ([journey/105](e:/ElevenPowers/journey/105-the-test-that-was-served-from-a-cache.md));
  - mutated type annotations were reported as unpinned lines, shipped since `--strength` was built ([journey/106](e:/ElevenPowers/journey/106-the-signature-that-never-runs.md));
  - a parametrised test id was cut at its first space ([docs/status.md 2026-11-03](e:/ElevenPowers/docs/status.md));
  - a nonexistent unittest name exited as FAILED and would read as `checked` ([journey/104](e:/ElevenPowers/journey/104-reached-is-not-checked.md)).
- Journey 105 found "Five things, each found by executing something real", including "The attempt cap the spec scaled was never in force". — [journey/105](e:/ElevenPowers/journey/105-the-test-that-was-served-from-a-cache.md)
- Harness faults caught by a one-cent or one-turn check before paid runs:
  - the Skill tool was missing (superpowers could not load);
  - the operator's CLAUDE.md leaked into every subscription run, the held-out sweep included;
  - `--bare` needs an API key;
  - a shared zip cache raced between arms.

  Sources: [CLAUDE.md](e:/ElevenPowers/CLAUDE.md); [PLAN.md 2026-10-28](e:/ElevenPowers/PLAN.md)
- Withdrawn same-day overhead claims came from replays whose conditions differed from the real runs: the "mutation step is most of the gap" claim, and a buffered-output misreading of a 9.5-minute wait. — [PLAN.md §10](e:/ElevenPowers/PLAN.md); [journey/101](e:/ElevenPowers/journey/101-the-agent-waited-for-a-report-it-never-read.md)
- Independent reviews find many defects in "done" first versions:
  - 11 defects in `ep_review`;
  - 8 in the pre-existing check ("All eight came from asking the base commit, so the design changed");
  - 9 in marked rules plus a tenth by hosted CI;
  - 1 Critical and 7 Important in TestMiner slice 1.

  Sources: [docs/status.md](e:/ElevenPowers/docs/status.md); [results/testminer/README.md](e:/ElevenPowers/results/testminer/README.md)
- Count errors corrected after publication: `ep_review` mutant counts (22/24 → 20/20); review-functions run counts (14/10/12/3 → 13/9/11/2). — [docs/status.md 2026-11-01](e:/ElevenPowers/docs/status.md); [results/review-functions/README.md](e:/ElevenPowers/results/review-functions/README.md)
- CI breakages:
  - new modules were pushed before being drawn on the architecture map, which turned CI red on all four configurations from `35a3447` to `d4f1706`;
  - several recorded hosted-Windows intermittents (one root-caused to a 21.5 MB tree-sitter grammar download inside a parse);
  - three intermittent process tests are retained unexplained.

  Source: [docs/status.md 2026-11-01, 2026-11-05](e:/ElevenPowers/docs/status.md)
- Oracle/benchmark defects: all five v2 stale facts were oracle defects that "two reviews and the rehearsal missed"; ten v3 findings "would have graded correct work as wrong" and were fixed before freezing. — [PLAN.md 2026-10-28, 2026-10-29](e:/ElevenPowers/PLAN.md)
- Agent behaviour pattern: "The losses the note leaves are disagreements, not oversights"; "A reminder that offers a way out ('or say why') gets the same choice back." — [results/rule-gate/README.md](e:/ElevenPowers/results/rule-gate/README.md); [journey/100](e:/ElevenPowers/journey/100-told-twice-and-chose-the-same.md)
- `journey/mistakes.md` includes, among its later entries:
  - "Numbers written from memory into a document about not doing that";
  - "Probes that could not observe their own fix";
  - "A successful exit code that meant nothing, again";
  - "The headline number was the one the audit warned against";
  - "An experiment sized on the wrong number";
  - "Asking the base commit what only the opened tree knows".

  Source: [journey/mistakes.md](e:/ElevenPowers/journey/mistakes.md)

### Inferences
- The project's measurement discipline is strong and self-correcting, but it consumes much of the effort. A large share of recent journey entries is about fixing the instrument rather than producing user value.
- The recurring "judgement, not oversight" finding (rule gate 0/7; agents explain scope choices) suggests that remaining coding-helper losses may not be fixable by any delivery mechanism. They may only be resolvable by asking the user.

### Gaps
- Only journeys 100-106 and selected mistakes.md headings were read in full or part. Earlier journey entries (1-99) were consulted only through PLAN/status summaries.
