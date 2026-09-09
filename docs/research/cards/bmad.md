# bmad (BMAD-METHOD)

- Repo: https://github.com/bmad-code-org/BMAD-METHOD (clone: `--depth 1`, branch `main`)
- Commit: `abe4eb1bce919c9d22cd18b3519353d5824c4b75`, 2026-09-05 21:52 -0600 ("chore(review): point CodeRabbit at dev...")
- Version on disk: `6.13.0-next` (`skills/bmad/module-manifest.toml`); latest tagged release in `CHANGELOG.md` is v6.12.0 (2026-09-03)
- License: MIT (`LICENSE`, "Copyright (c) 2025 BMad Code, LLC"); trademark restrictions on the names BMad / BMAD-METHOD in `TRADEMARK.md`
- Primary language: Markdown prompt text (390 of 573 tracked files, ~40.7k lines); Python 3.11+ tooling (43 files, ~17.2k lines incl. tests); `git ls-files | wc -l` = 573
- Repo-level `AGENTS.md`: "Skills, workflows, tasks, and agent definitions are prompt text that an agent reads in full on every run."

BMAD is a process framework, not a runtime: 29 folders under `skills/`, each a `SKILL.md` per the Agent Skills spec, installed into a coding tool's skills directory (`.claude/skills/`, `.agents/skills/`, etc. per `docs/reference/skills-and-agents.md`) and executed by that host's model. It targets solo developers and small teams who want plan-first, document-driven delivery ("Agile AI Driven Development", `README.md`) on Claude Code, Codex, Cursor, Windsurf, Cline and similar. The user problem it addresses is agents that "turn unstated assumptions into code" (`README.md`); the fix is a chain of persisted documents (spec, PRD, architecture spine, stories, per-change spec) plus a fixed implement-then-adversarial-review loop. The only code BMAD itself runs is a set of `uv run` Python scripts for config merging, snapshot rendering, an append-only memlog, sprint-status parsing, and lint (`skills/bmad/scripts/`, `skills/*/scripts/`).

## Request flow (cite files)

1. Entry is the host's skill trigger: the user types a skill name or the host matches a `description:` frontmatter (`skills/bmad-build/SKILL.md` lines 1-4). No BMAD code sees the request first.
2. Most skills then run two shell commands from prose: `resolve_customization.py --key workflow|agent` (3-layer TOML merge, `skills/bmad/scripts/config_utils.py::load_customization`) and `resolve_config.py` (`_bmad/config.toml` + `_bmad/custom/config.toml` + `_bmad/custom/config.user.toml`, `config_utils.py::load_central_config`). Every skill carries a fallback instructing the model to do the merge itself if the script fails (e.g. `skills/bmad-agent-dev/SKILL.md` "If the script fails").
3. The two Build skills are different: `skills/bmad-build/SKILL.md` (184 words) contains only an instruction to run `_bmad/scripts/render_skill.py`, which substitutes `{{.key}}`, `{{config.key}}`, `{workflow.key}` and `[[bmad-snapshot:file.md]]` tokens into every non-SKILL `.md` in the skill and publishes a content-addressed immutable copy under `_bmad/render/<skill>/<slug-hash>/<gen-hash>/` with a `manifest.json` of source/output SHA-256s (`skills/bmad/scripts/render_skill.py::render`, `_publish`, `_verify_existing`). The model is told to "read and follow" the printed absolute `workflow.md` path.
4. Build's control flow is a step-file chain: `workflow.md` -> `step-01-clarify-and-route.md` -> `step-02-plan.md` -> (`step-oneshot.md` | `step-03-implement.md` -> `step-04-review.md` -> `step-05-present.md`), each ending in "Read fully and follow `[[bmad-snapshot:next]]`". Rules forbid loading more than one step at a time (`skills/bmad-build/workflow.md` "Critical Rules").
5. Routing between skills is done by the `bmad` hub skill reading `module-manifest.toml` files and the knowledge document they name (`skills/bmad/SKILL.md`, `skills/bmad/references/help.md`). The hub is explicitly read-only and may not start the recommended skill in the same context.
6. Cross-skill invocation in prose is validated to use "Invoke the `x` skill" wording (`tools/skill-validator.md` REF-03); there is no programmatic dispatcher.

## What goes into the model (always-loaded vs on-demand, with token estimates)

Nothing is always loaded by BMAD itself; each skill loads what its `SKILL.md` names. Estimates use tokens ~= words x 1.35 (inferred rule of thumb; counts are `wc -w`).

- Persona activation (`bmad-agent-dev`): `SKILL.md` 626 w + `customize.toml` 495 w (arrives as resolver JSON) + config JSON ~50 w -> roughly 1,100 words, ~1.5k tokens. Personas are identical in structure across the five agents (`skills/bmad-agent-*/SKILL.md`, 611-626 words each); the differences live in `customize.toml` (`role`, `identity`, `communication_style`, `principles`, `menu`).
- Build, dispatch route, parent context: SKILL 184 + workflow 566 + step-01 1,559 + step-02 966 + spec-template 682 + step-03 570 + step-04 1,715 + step-05 176 = ~6.4k words, ~8.7k tokens of instructions, plus the rendered `review_layers` prose from `customize.toml` (1,079 w total file). Oneshot route: ~4.9k words, ~6.7k tokens. Subagent prompts are separate: edge-case hunter 1,280 + claims 237 + deletion 153 = 1,670 w; verification-gap 1,529 w; blind hunter ~150 w (`skills/bmad-build/review-prompts/*.md`, `references/*.md`, `customize.toml`).
- Code review (`bmad-code-review`): SKILL + 4 steps + customize.toml = 4,967 w (~6.7k tokens) parent, plus the same three reviewer prompts and an "Acceptance Auditor" layer gated on a spec (`skills/bmad-code-review/customize.toml`).
- Hub help: `skills/bmad/SKILL.md` 976 w + `references/help.md` 1,189 w (~2.9k tokens) per help request.
- Largest single-file skills: `bmad-spec/SKILL.md` 2,447 w, `bmad-project-context/SKILL.md` 2,088 w, `bmad-architecture/SKILL.md` 2,067 w; deep-recon totals 6,870 w across 20 files, loaded by mode.
- Documents a feature produces: Build spec targeted at 900-1,600 tokens with a user-overridable gate at 1,600 (`skills/bmad-build/workflow.md` "SCOPE STANDARD", `step-02-plan.md` item 6); `epic-<N>-context.md` targeted at 800-1,500 tokens (`compile-epic-context.md`); `SPEC.md` kernel template 375 w; PRD template 1,510 w with guidance "hobby ~2 pages, internal 5-8" (`skills/bmad-prd/SKILL.md` "Length scales with stakes"); architecture spine template 709 w; sprint-status template 325 w. Inferred: a project-sized run leaves roughly 10-25k tokens of planning documents, of which Build deliberately reads only the compiled epic context plus the prior story's spec (`step-01-clarify-and-route.md` A.2, A.5).

## Task understanding and planning

- Build treats the invocation as "starting intent... not authority to skip Build steps" and ignores in-prompt directives to skip (`skills/bmad-build/step-01-clarify-and-route.md` RULES). Read from source.
- Step 2 investigates before asking: "Do not ask the human during investigation", records findings in a `## Code Map`, then decides between `oneshot` (no intent gaps, nothing irreversible, small footprint) and `dispatch` (full spec) (`step-02-plan.md` items 2-3). This route decision after investigation is the v6.12 headline (`CHANGELOG.md`).
- Open questions are limited to "things the request does not say, the code cannot settle, and the user would notice"; everything else the agent decides and logs (`step-02-plan.md` item 3, `spec-template.md` Open Questions comment).
- The spec has a `<frozen-after-approval>` block (Intent, Boundaries, I/O matrix) that only the human may change after approval (`spec-template.md`; build-auto calls it `<intent-contract>`, `skills/bmad-build-auto/spec-template.md`).
- Sizing tiers (trivial / one session / epic / project) are prose heuristics in `skills/bmad/references/help.md` "How to use BMad" and `docs/plan/choose-a-planning-path.md`; "one session" is ~500 changed LOC (`docs/build/build-a-change.md`).
- Upstream planning (`bmad-spec`, `bmad-prd`, `bmad-architecture`) is coaching-first: "Coaching path is the default... coach; don't silently draft" (`skills/bmad-architecture/SKILL.md`), "Elicitation, not direction" (`skills/bmad-prd/SKILL.md`).

## Context selection and repository understanding

- No index, embeddings, or code map tool. Build's Code Map is produced by the model, optionally via subagents told to "return short summaries only" (`step-02-plan.md` item 2).
- Epic context caching: `epic-<N>-context.md` is valid only if it exists, starts with the right heading, and no planning artifact is newer; otherwise a subagent recompiles it from PRD/architecture/UX "by purpose, not by source", 800-1,500 tokens (`skills/bmad-build/compile-epic-context.md`).
- Freeform route scans `{{.planning_artifacts}}` by filename globs (`*prd*`, `*architecture*`, `*ux*`, `*epic*`, `*brief*`) and loads selectively (`step-01-clarify-and-route.md` B).
- Brownfield: `bmad-project-context` writes one verified `<!-- bmad:context -->` block into `AGENTS.md` with a provenance SHA; admission rules exclude anything derivable from source and require observed evidence for pitfalls (`skills/bmad-project-context/SKILL.md`, `references/best-practices.md`, `references/template.md`). Refresh diffs `git log --diff-filter=DR` since the recorded SHA. The rationale doc cites studies that repo overview files add cost without success gains (`docs/existing-codebases/theory-of-project-context.md`). The older scan-and-document skills were retired for this reason (`CHANGELOG.md` v6.11.0, `removals.txt`).
- `persistent_facts` (file globs loaded on activation) ships empty since 6.12; project-context auto-load was removed (`CHANGELOG.md` Breaking).
- Implementation subagents are told to read the spec and its `context:` list themselves; the parent must not paste files into the dispatch (`step-03-implement.md`).

## Memory across sessions

- All memory is files on disk under `{project-root}/_bmad-output/` (`skills/bmad/assets/config.template.toml`): `planning-artifacts/`, `implementation-artifacts/`, `specs/spec-<slug>/`.
- Per-change spec frontmatter `status` (draft / ready-for-dev / in-progress / in-review / done, plus `blocked` for auto) is the resume state; Build routes on it at step 1 (`step-01-clarify-and-route.md` "Intent check").
- `.memlog.md`: an append-only, one-line-per-entry log written only through `skills/bmad/scripts/memlog.py` (atomic temp+fsync+rename, no edit/delete subcommand). `bmad-spec`, `bmad-prd`, `bmad-architecture`, `bmad-brainstorming` and party-mode derive their deliverables from it and resume by reading it (`skills/bmad-spec/SKILL.md` "Memory and derivation", `skills/bmad-party-mode/references/party-memory.md`).
- `sprint-status.yaml` tracks epic/story status; `sync-sprint-status.md` updates it from Build; `bmad-sprint-planning/scripts/sprint_plan.py` owns generate/status/validate with preserve-never-downgrade merging (`skills/bmad-sprint-planning/SKILL.md`).
- `deferred-work.md` collects review findings not owned by the current story (`step-04-review.md` defer; `bmad-code-review/steps/step-04-present.md`).
- Stable IDs across documents: `CAP-N` in specs, `AD-n` in spines, `FR-N`/`UJ-N` in PRDs, never renumbered (`skills/bmad-spec/SKILL.md` Spec Law 6, `skills/bmad-architecture/SKILL.md` Update).

## Verification: what counts as done

- Build step 3: capture `baseline_commit`, write the unified diff to a temp file and "judge against the diff, not against the implementation subagent's report"; mark every task and AC; "Matrix Test Audit" requires each I/O matrix row to have a test that ran and passed, and forbids editing expectations to match code (`skills/bmad-build/step-03-implement.md`).
- Build step 4: three parallel context-free reviewer subagents at "the same model capability" (blind hunter with a mandatory finding floor `N = min(floor(sqrt(kB)+1), 10)`; edge-case path tracer with deletion and claims passes; verification-gap "if this broke, would a test fail") (`skills/bmad-build/customize.toml`, `review-prompts/*.md`). The parent verifies each finding at the cited line, assigns one verdict (high/medium/low/false/maybe-false), groups by root cause, routes to intent_gap (revert, ask human), bad_spec (revert, amend spec, re-derive), patch (re-engage the same implementation subagent), or defer; loops capped at 5 (`step-04-review.md`).
- Every finding gets a row in the spec's `## Review Triage Log`; "never drop, merge, or silently skip one" (`step-04-review.md`; v6.12 changelog).
- The spec's claims are handed only to the edge-case layer and only after its tracing, so the change's own narrative cannot steer review (`references/claims-check.md`; `step-04-review.md` "Stage the Diff").
- Done = spec `status: done`, local commit, no push (`step-05-present.md`). `help.md` adds: complete "when the intent is satisfied, its chosen checks pass, and no chosen review leaves material unresolved findings".
- Upstream gates: `bmad-sprint-planning` readiness gate PASS/CONCERNS/FAIL (`references/readiness-gate.md`); architecture `lint_spine.py` deterministic checks plus rubric subagents (`skills/bmad-architecture/scripts/lint_spine.py`, `references/reviewer-gate.md`); `bmad-retrospective` requires a source reference on every finding and rejects epics with unfinished stories (`skills/bmad-retrospective/SKILL.md`).
- The framework itself: 21 `test_*.py` files, 477 test functions over the Python scripts only; `AGENTS.md` forbids tests on LLM output or static prompt text. `tools/validate_skills.py` enforces 10 structural rules; 10 more are LLM-judged (`tools/skill-validator.md`).

## Multi-agent / roles

- Five named personas (Mary analyst, John PM, Sally UX, Winston architect, Amelia dev) are optional wrappers: "No path above needs them; the flow skills already do this work" (`skills/bmad/references/help.md`). Each is a menu that dispatches to workflow skills (`skills/bmad-agent-dev/customize.toml` `[[agent.menu]]`). Name/title are hardcoded; role, style, principles, facts, hooks and menu are customizable (`docs/customize/customize-bmad.md`).
- Real multi-agent work is subagent fan-out inside workflows: implementation subagent (`step-03-implement.md`), 3-4 reviewer subagents (`step-04-review.md`), epic-context compiler, PRD research/extraction subagents that return only digests (`skills/bmad-prd/SKILL.md` "Extract, don't ingest").
- `bmad-party-mode` runs personas as standing subagents or a Claude Code agent team, with a lead that "weaves" replies and per-party memlogs (`skills/bmad-party-mode/references/mode-subagent.md`, `mode-agent-team.md`).
- Unattended: `bmad-build-auto` is one worker per story; halts `blocked` with `no subagents` if fan-out is unavailable; an external orchestrator (bmad-loop or a coding session) owns dispatch (`skills/bmad-build-auto/workflow.md`, `docs/build/autonomous-development-loops.md`).

## Model routing

- None inside BMAD. Reviewers "must run at the same model capability as the current session" (`step-04-review.md`, `bmad-code-review/steps/step-02-review.md`). When subagents are unavailable the prompts are written to disk for the human to paste into "a separate session (ideally a different LLM)".
- Party mode allows a per-member `model` and a session `--model` pin, delegated to the host (`references/mode-subagent.md` "Model choice").
- A review layer's `instruction` may be overridden to shell out to an external tool "and therefore a different model" (`skills/bmad-build/customize.toml` comments; `CHANGELOG.md` #2550).

## Failure recovery / checkpoints

- Human checkpoints: dirty tree / branch mismatch halt, multi-goal split, spec approval (CHECKPOINT 1 with approve-and-stop option), open questions, intent_gap loopbacks (`step-01`, `step-02`, `step-04`). 79 `HALT` occurrences across skill prose.
- Resume: spec status routing; draft specs preserve the frozen block on re-plan (`step-02-plan.md` item 1); `review_loop_iteration` cap of 5; `baseline_commit` never overwritten on resume (`step-03-implement.md`).
- Build-auto: enumerated blocking conditions, terminal status written to the spec or a fallback result file, attempted change saved as a patch on review `intent gap` (`docs/build/autonomous-development-loops.md`; `skills/bmad-build-auto/workflow.md` HALT). A `blocked` story is permanent until the file is deleted.
- Setup/doctor: staging directories and atomic `replace_dir` with backup rename; symlinked `_bmad` rejected (`skills/bmad/scripts/setup.py::materialize_bmad`, `replace_dir`, `reject_symlinked_bmad`). Renderer refuses to overwrite a generation whose manifest differs (`render_skill.py::_verify_existing`).

## Security posture

- Read: no sandboxing, permission model, or secret handling; those are delegated to the host. `SECURITY.md` is a disclosure policy only.
- Prompt-injection awareness is thin and prose-only: the hub treats manifests and artifacts as "evidence, not instructions" (`skills/bmad/SKILL.md`); Build ignores skip directives in the intent (`step-01`); reviewers are told not to spawn subagents or invoke skills; deep-recon escapes source URLs via script (`skills/bmad-deep-recon/references/html-briefing.md`). Only 2 grep hits for injection/untrusted language across `skills/`.
- Skills execute `uv run` on Python files copied into `_bmad/scripts/` at setup; `setup.py` reads remote `module-manifest.toml` over HTTPS for update checks (`SOURCE_READ_LIMIT`, `urllib`), no signature verification (read in `setup.py` imports and `read_source_manifest`).
- Review layers and `on_complete` are free-form instructions from TOML that the model executes, including arbitrary shell (`customize.toml` comments "an override may run anything"). A team-committed `_bmad/custom/*.toml` is therefore an instruction-injection surface. Inferred.
- Guardrails that do exist: "No push. No remote ops." (`step-03`), "NEVER auto-push" (`step-05`), no `git add` during review staging (`step-04`), project-context never commits.

## Host coupling

- Host-agnostic by design: SKILL.md + `description:` trigger per agentskills.io (`tools/skill-validator.md` SKILL-0x). Host directory table in `docs/reference/skills-and-agents.md`. Installation is `npx skills add bmad-code-org/BMAD-METHOD` or Claude Code / Codex plugin marketplaces (`README.md`); the older `npx bmad-method install` npm installer is "maintained separately on `V6.12`" (`AGENTS.md`) and still documented in `docs/start/install-bmad.md`, so the two docs disagree on the install path.
- Hard dependencies: `uv` and Python 3.11 for Build/Build-auto; they halt without it (`skills/bmad-build/SKILL.md`; `CHANGELOG.md` #2281).
- Subagent availability is the main capability fork; each fan-out has an inline fallback naming "Copilot, Codex, local Ollama, older Claude" (`step-01-clarify-and-route.md` A.3). Party-mode `agent-team` is "Claude Code only".
- The hub requires the host to expose skill roots and listings "already exposed in context" and stops otherwise (`skills/bmad/SKILL.md` "Fresh Discovery").
- `open_spec` override examples for VS Code, Cursor, Windsurf, Zed, IntelliJ, Vim, Emacs (`skills/bmad-build/customize.toml`).
- Web bundles repackage six planning skills for Gemini Gems / Custom GPTs (`web-bundles/README.md`, `bundles.json`, `tools/bundle_web_bundles.py`).

## Observability

- Rendered snapshots with `manifest.json` (renderer hash, source hashes, resolved values, output hashes) make "exactly what ran" inspectable (`render_skill.py`; `CHANGELOG.md` #2601).
- The spec file is the run log: Implementation Notes, Spec Change Log, Review Triage Log, `baseline_commit`, `review_loop_iteration`, and for auto `warnings`, `deferred`, `followup_review_recommended`, `## Auto Run Result` (`spec-template.md`, `skills/bmad-build-auto/spec-template.md`).
- Memlogs echo JSON state on each write and are the audit trail for planning skills (`memlog.py::ack`).
- No token accounting, timing, or telemetry anywhere; time estimates are banned by lint (`tools/validate_skills.py` SEQ-02).

## Trace: trivial task (border radius)

Read from `skills/bmad/references/help.md` and `skills/bmad-build/*`; the outcome below is inferred from those instructions.
1. `help.md` says a trivial, low-risk edit should use "no BMad skill at all". `bmad-build`'s description tells the host not to volunteer for "typo-only, formatting-only" edits. If the user types `/bmad-build change the button border radius to 8px`, the explicit request qualifies.
2. Cost before any code: `render_skill.py` run; `workflow.md` (566 w) + `step-01` (1,559 w): list two artifact directories, decide freeform path, VCS clean-tree check (halts if dirty), multi-goal check, derive slug `spec-button-border-radius.md`.
3. `step-02` (966 w): investigate (find the button component and any design tokens), write three facts; with no intent gaps and a small footprint, write a minimal spec (Intent + Implementation Notes, `route: oneshot`, `status: in-progress`) and exit to `step-oneshot.md` (979 w).
4. Oneshot: implement, then launch the `oneshot_review_layers` (default: one Blind Hunter subagent that must produce at least `min(floor(sqrt(kB)+1),10)` findings, i.e. at least 1-2 for a tiny diff), verify each claim, log verdicts, commit locally, present a two-sentence summary.
5. Overhead: roughly 6.5-7k tokens of instructions in the parent, one `uv` process, one reviewer subagent that is contractually required to find something, a spec file left in `_bmad-output/implementation-artifacts/`, and a local commit. No human checkpoint on this route unless the tree is dirty. Inferred: the forced finding floor is the most likely source of noise on a one-line CSS change.

## Trace: hard task (auth race)

Read from the same files; outcome inferred.
1. `/bmad-build fix intermittent auth race` -> `step-01` freeform path; scans planning artifacts for `*architecture*` etc. and loads any relevant one; VCS check; single goal.
2. `step-02`: investigation via subagents into auth middleware, token refresh, concurrency; Code Map records files/symbols. Facts: likely intent gaps (which behavior wins on concurrent refresh; is a session invalidation acceptable), possibly irreversibles (session store migration). So `route: dispatch`, full spec with `## Open Questions`, I/O & Edge-Case Matrix rows for the interleavings, `## Verification` commands. If over 1,600 tokens the user is asked to split or keep. CHECKPOINT 1 halts for approval; the human may "Approve and stop" and resume later.
3. `step-03`: implementation subagent gets only the spec path; parent stages the diff, checks every AC, and the Matrix Test Audit demands a passing test per matrix row that actually ran. Inferred: for an intermittent race, writing a deterministic covering test is the hard part, and the audit will block until one exists or the human is asked.
4. `step-04`: three reviewers in parallel; the edge-case hunter's method explicitly includes race conditions and "handle lifetime" re-check analysis (`review-prompts/edge-case-hunter.md` Step 2); the verification-gap reviewer must read the tests and search by symbol before claiming a gap. Findings are verified at the cited line; a finding that the fix guards state not shown reachable routes to bad_spec or intent_gap, reverting code and re-deriving. Loop cap 5.
5. Overhead: ~9k tokens of parent instructions, 3-4 subagent runs each reading the diff file and a 1.3-1.5k-word prompt, at least one human halt, a spec of ~1-1.6k tokens with triage log, local commit. The method gives real structure for this class (matrix, claims check, verification-gap) but has no runtime tooling to reproduce a race; that is entirely on the model and the repo's test harness.

## Strengths (ranked, concrete, cited)

1. Reviewer design that resists self-confirmation: reviewers are context-free, read the diff from a file, cannot see the spec except the edge-case layer after tracing, cannot assign severity, and the parent must verify every claim before a verdict (`skills/bmad-build/step-04-review.md`, `references/claims-check.md`). The verification-gap prompt's evidence rules are unusually concrete (`review-prompts/verification-gap.md`).
2. Route-after-investigation with a frozen intent block and explicit intent_gap/bad_spec/patch/defer routing; loopbacks re-derive code from an amended spec rather than patching (`step-02-plan.md`, `step-04-review.md`, `spec-template.md`).
3. Deterministic core where it matters: content-addressed rendered snapshots (`render_skill.py`), atomic memlog (`memlog.py`), sprint-status parser (`sprint_plan.py`), spine linter (`lint_spine.py`), and 477 tests over exactly that code.
4. Evidence-based project context: the admission/deletion rules and provenance SHA in `bmad-project-context` are a defensible answer to AGENTS.md bloat (`references/best-practices.md`, `docs/existing-codebases/theory-of-project-context.md`).
5. Layered TOML customization with shape-based merge semantics and no-removal rule; every skill ships its schema as `customize.toml` (`config_utils.py::structural_merge`, 27 files).
6. Token budgets stated as numbers in the artifacts themselves (900-1,600 spec, 800-1,500 epic context) and a scope gate the user can override.

## Weaknesses (ranked, concrete, cited)

1. Instruction volume: a Build run reads ~6-9k tokens of process text before any code, and `AGENTS.md` admits "length and ambiguity are paid on every run". `step-01` alone is 1,559 words of routing rules.
2. Enforcement is prose: "NEVER load multiple step files", "HALT and wait", "run at the same model capability" are requests to the model; nothing checks compliance (`workflow.md`, `step-04`). Only structural lint runs on skills (`tools/validate_skills.py`).
3. Forced finding floor on the blind hunter guarantees findings on trivial diffs; the parent then spends tokens refuting them (`customize.toml` Blind Hunter).
4. Hard `uv`/Python 3.11 dependency and shell-out for every skill activation, including two resolver processes per persona (`skills/bmad-agent-dev/SKILL.md` Steps 1, 5). Build halts without `uv`.
5. Duplicated sources: `bmad-build` and `bmad-build-auto` carry near-identical copies of steps, templates, and all three review prompts (diff in `step-03` shows small divergences); `bmad-code-review` has a third copy. Drift risk is real and already visible (`baseline_commit` vs `baseline_revision`).
6. Documentation drift: README installs via `npx skills add`; `docs/start/install-bmad.md` documents `npx bmad-method install`; `resolve_config.py` docstring says four layers, code merges three; `skill-validator.md` references `src/core-skills/module.yaml` paths that do not exist in this tree.
7. Filename-glob discovery of planning artifacts in Build's freeform path (`*prd*`, `*architecture*`) coexists with "identify documents by reading what they are" in sprint planning; inconsistent.
8. No security model for the customization surface: TOML overrides are executed as instructions, including shell (`customize.toml` review_layers comments).

## Genuinely innovative vs mostly prompt engineering

- Innovative (in this space): the claims-after-tracing ordering for reviewers; verification-gap as a distinct review lens with evidence rules; frozen-intent block with bad_spec re-derivation instead of patching; content-addressed prompt snapshots with manifests; append-only memlog as the canonical artifact from which documents are re-rendered; the project-context admission/deletion grounds with provenance SHA.
- Mostly prompt engineering: personas and menus (`bmad-agent-*`), step-file "micro-file" discipline and its CRITICAL/FORBIDDEN rule blocks (`skills/bmad-create-epics-and-stories/SKILL.md` still uses emoji rule lists from the v4 lineage), coaching vs fast paths, PRD/spine templates, party mode.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Three copies of the review pipeline (`bmad-build`, `bmad-build-auto`, `bmad-code-review`) plus a fourth generic one in `bmad-review` lenses.
- Every persona activation runs two Python processes and reads ~1.1k words to present a menu of 4-5 items that map to skills the user could invoke directly.
- The hub re-scans all manifests on every help request by design and may not cache (`skills/bmad/SKILL.md` "Fresh Discovery", "Ordinary Help Is Read-Only").
- Brittle: routing depends on the host exposing skill listings and roots in context; subagent semantics ("blocking calls awaited together in this turn", "never `run_in_background`") are host-specific and only described in prose (`skills/bmad-build-auto/workflow.md` Subagents).
- `deferred-work.md` and epic context are appended/regenerated without dedupe by rule ("Do not modify existing entries or look for duplicates").
- Planning documents scale in count (spec folder, companions, memlog, stories.yaml, per-story spec, sprint-status, retro) and the `bmad-correct-course` skill FULL_LOADs PRD, epics, architecture, UX and spec together (`skills/bmad-correct-course/SKILL.md` Input Files).

## Reusable pieces (specific files or ideas, and the license terms for reuse)

MIT permits copying with attribution; `TRADEMARK.md` restricts use of the BMad name.
- `skills/bmad-build/review-prompts/verification-gap.md` and `edge-case-hunter.md` + `references/claims-check.md`, `deletion-check.md`: standalone reviewer prompts with a JSON output contract.
- `skills/bmad-build/step-04-review.md` triage protocol (verify -> single verdict -> group by root cause -> route).
- `skills/bmad/scripts/memlog.py` (229 lines, stdlib only) and `config_utils.py::structural_merge`.
- `skills/bmad/scripts/render_skill.py` snapshot/manifest approach.
- `skills/bmad-project-context/references/best-practices.md` and `template.md` as an AGENTS.md policy.
- `skills/bmad-build/spec-template.md` and `compile-epic-context.md` as compact per-change and per-epic context shapes with numeric budgets.
- `skills/bmad-spec/assets/stories-schema.md` (prefix-free ids, caller-only checkpoint fields).
- `tools/validate_skills.py` + `tools/skill-validator.md` as a skill lint catalog.

## Must not copy

- The BMad/BMAD-METHOD names, wordmark, banner (`TRADEMARK.md`, `Wordmark.png`, `banner-bmad-method.png`).
- Persona names and descriptions (Mary, John, Sally, Winston, Amelia) are product identity; fine legally under MIT but they carry no technical value.
- The CRITICAL/FORBIDDEN/SYSTEM FAILURE rule style in `bmad-create-epics-and-stories/steps/*.md`; the repo's own newer skills have moved away from it.
- The duplicated-copy pattern across build/build-auto/code-review.
- Free-form TOML instructions executed as shell without a permission boundary.

## Transferable abstractions (name each, one line)

- Frozen intent contract: human-owned block in the plan that code derivation may not edit; review routes to it when intent is the root cause.
- Route-after-investigation: investigate first, then pick oneshot vs full spec on intent gaps, irreversibles, footprint.
- Blind-then-claims review ordering: reviewers see the diff only; the change's own narrative arrives last and only to one lens.
- Verification-gap lens: ask "would a test fail" rather than "is this wrong", with mandatory evidence.
- Verdict-then-route triage with a written row per finding and a bounded loopback count.
- Content-addressed prompt snapshots: hash sources + resolved config, publish immutable, reuse or refuse.
- Append-only memlog as canonical, documents as derived renders.
- Evidence-admission rules for repo instructions with provenance SHA and deletion grounds.
- Numeric context budgets stored inside the artifacts that must respect them.
- Shape-based layered config merge (scalar override, table deep-merge, keyed array replace, other arrays append, no removal).
- Terminal-status contract for unattended workers (`status` + enumerated blocking conditions, deferred list in frontmatter).

## Open questions that need a probe run to answer

- Does a host model actually honor "load one step at a time" and "same model capability" rules, and how often does it skip or merge steps?
- Real token cost of a Build run end to end (parent + 4 subagents) on a small and a medium change; how much is process text vs code.
- False-positive rate of the Blind Hunter's finding floor, and how much parent time goes to refuting it.
- Whether the triage protocol's `false`/`maybe-false` verdicts are applied honestly or collapse to "patch everything".
- Does the Matrix Test Audit block on intermittent/race scenarios, and what does the model do when no deterministic test exists?
- Behavior on hosts without subagents (Copilot, Codex CLI): how usable is the "write prompts to disk and paste back" fallback?
- Whether `render_skill.py` generations accumulate unbounded under `_bmad/render/` across config changes.
- How the hub's manifest-driven routing behaves when several modules (method, toolbox, builder, loop) are installed together.
