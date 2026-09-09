# Complementarity matrix: which strength covers which weakness

Built 2026-09-09 from the ten source-read cards in `cards/` (commits and dates recorded there) and the Claude Code host card in `hosts/`. Every claim below traces to a card, and every card claim traces to a file path. Nothing was executed; behavior claims are inferred from source and are marked as probe questions where the cards say so.

Purpose: the project's first goal is to combine the strengths of these systems so that each one's weakness is covered by another's strength. This document does that mapping explicitly, then isolates the weaknesses that no system covers. Those residual gaps are the only legitimate targets for new architecture.

## 1. Mechanism types

Each strength is tagged by how it is enforced, because that determines whether it survives composition:

- **code**: a script, hook, or runtime check that runs whether or not the model cooperates
- **protocol**: a file or data contract (fixed filenames, JSON lines, exit codes) that code on both sides can rely on
- **prose**: instruction text the model is asked to follow

A prose strength can be adopted at zero engineering cost but adds tokens and can be ignored. A code strength costs integration work and is unignorable. The cards show that nine of ten systems enforce their process mainly through prose, and the ETH study on context files (reading list) shows agents follow prose "too diligently" in some places and not at all in others.

## 2. Strength inventory

| System (license) | Strength | Mechanism | Card citation |
|---|---|---|---|
| Superpowers (MIT) | File handoff between controller and subagents: task brief, review package, report by path | code (3 bash scripts) | `SDD/SKILL.md:231-324`, `scripts/task-brief`, `scripts/review-package` |
| Superpowers | Plan-scoped append-only ledger for compaction recovery with recorded BASE commits | protocol | `SDD/SKILL.md:131-152`, `scripts/sdd-workspace` |
| Superpowers | Bounded fix loop: 5 rounds, model tier escalation at rounds 4 to 5, breaker, rulings log surfaced to the human | prose | `SDD/SKILL.md:354-429` |
| Superpowers | Systematic debugging: reproduce, instrument boundaries, hypotheses, condition-based waiting, 3-fix breaker | prose | `systematic-debugging/SKILL.md:48-212` |
| Superpowers | Skills authored and tested like code: baseline runs without the skill, pressure scenarios | method | `writing-skills/testing-skills-with-subagents.md` |
| Superpowers | Portability: action vocabulary plus per-host tool map, one skill body across 12 hosts | protocol | `docs/porting-to-a-new-harness.md:38-70` |
| Superpowers | Smallest always-on footprint of the process frameworks: about 680 tokens | measured | `hooks/session-start`, `using-superpowers/SKILL.md` |
| ECC (MIT) | Defensive hook runtime: profile gating, pass-through on error, atomic writes, denial dampening | code | `scripts/lib/hook-flags.js`, `run-with-flags.js` |
| ECC | Destructive shell classifier handling heredocs, subshells, `sh -c` bypasses | code | `gateguard-fact-force.js:700-745` |
| ECC | Batched Stop-time formatter and typecheck via an edit accumulator | code | `post-edit-accumulator.js`, `stop-format-typecheck.js` |
| ECC | Hard blocks that are small and exact: no `--no-verify`, no editing lint configs | code | `block-no-verify.js`, `config-protection.js` |
| ECC | Worktree-keyed session recall with a hard cap and a stale-replay marker | code | `session-start.js:275-330, 673-700` |
| ECC | Size-to-ceremony classifier with exactly two human gates | prose | `skills/orch-pipeline/SKILL.md:40-84` |
| ECC | Reviewer prompt engineered against review noise, zero findings allowed | prose | `agents/code-reviewer.md:30-100` |
| Spec Kit (MIT) | One template source rendered to 41 hosts through a small substitution pipeline | code | `integrations/base.py:769-884` |
| Spec Kit | Exit-code prerequisite gates and a feature pointer file that makes stages location-independent | code (shell) | `check-prerequisites.sh:127-145`, `common.sh:163-231` |
| Spec Kit | Machine-parseable task grammar consumed by downstream commands | protocol | `templates/commands/tasks.md:149-180` |
| Spec Kit | Typed gap convergence loop: missing, partial, contradicts, unrequested, append-only task IDs | prose protocol | `converge.md` steps 3 to 7 |
| Spec Kit | Bounded incremental clarification: at most 5, one at a time, recommendation first, write-back per answer | prose protocol | `clarify.md` steps 3 to 9 |
| Spec Kit | The lean preset: same artifact contract with about 5 percent of the prompt text | evidence | `presets/lean/commands/*.md` |
| gstack (MIT) | Evidence sentinel protocol and content-fingerprint evidence ledger graded FRESH, STALE, MISSING | code | `bin/gstack-evidence`, `bin/gstack-wtree`, `scripts/resolvers/aside.ts` |
| gstack | Opt-in Stop hook that blocks the turn until a declared verify command passes, with a trust store and re-entry cap | code | `bin/gstack-verify-gate` |
| gstack | Bundled Playwright browser daemon with ref-based snapshots, stale-ref detection, untrusted-content envelopes | code | `browse/src/snapshot.ts`, `commands.ts`, `server.ts` |
| gstack | Review fan-out with merge logic: JSON findings, fingerprint dedup, confidence gate, quote-before-report, adaptive gating by historical hit rate | code plus prose | `scripts/resolvers/review-army.ts`, `confidence.ts`, `bin/gstack-specialist-stats` |
| gstack | Learnings and decisions as JSONL with confidence decay, latest-wins dedup, trust gate, injection filter, supersede | code | `bin/gstack-learnings-log`, `-search`, `lib/jsonl-store.ts` |
| gstack | Security engineering: nonce-bound instruction blocks, fail-closed freeze hook with trap backstop, hash-chained egress receipts, redaction before git and gh sinks | code | `bin/gstack-skill-start:334-347`, `freeze/bin/check-freeze.sh`, `lib/egress-receipt.ts` |
| gstack | Docs generated from the tool registry, tests that validate every documented command, a CI token ratchet | code, CI | `scripts/gen-skill-docs.ts`, `test/context-budget-ratchet.test.ts` |
| gstack | Diff-scope flags that gate which reviewers run | code | `bin/gstack-diff-scope` |
| BMAD (MIT) | Blind-then-claims review ordering: reviewers see only the diff; the change's own narrative reaches one lens last | prose protocol with JSON contract | `step-04-review.md`, `references/claims-check.md` |
| BMAD | Verdict-then-route triage: every finding verified at the cited line, one verdict, routed to intent_gap, bad_spec, patch, or defer; loopbacks re-derive from an amended spec | prose protocol | `step-04-review.md` |
| BMAD | Route after investigation: investigate silently, then choose oneshot versus full spec on intent gaps, irreversibles, footprint | prose | `step-02-plan.md` |
| BMAD | Frozen intent block that only the human may edit after approval | protocol | `spec-template.md` |
| BMAD | Content-addressed prompt snapshots with SHA manifests; atomic append-only memlog; 477 tests over exactly the code that runs | code | `render_skill.py`, `memlog.py` |
| BMAD | Evidence-admission rules for repository context with a provenance SHA and deletion grounds | prose plus script | `bmad-project-context/references/best-practices.md` |
| BMAD | Numeric token budgets stored inside the artifacts that must respect them | protocol | `spec-template.md`, `compile-epic-context.md` |
| Aider (Apache-2.0) | Repository map: tree-sitter tags, file graph, personalized PageRank biased by request words and chat files, token-budgeted binary-search render, mtime cache | code | `aider/repomap.py:365-706` |
| Aider | Edit-format engineering: tolerant SEARCH/REPLACE application, per-model format table, diagnostic bounce-back | code | `editblock_coder.py:134-240, 602-628` |
| Aider | Bounded reversible loop: dirty-commit, scoped auto-commit, session-scoped undo, fatal-only lint gate, 3 reflections | code | `repo.py:131-318`, `commands.py:560-655`, `linter.py:127-159` |
| Aider | Stable-prefix prompt ordering for cache hits | code | `chat_chunks.py` |
| Aider | Reproducible benchmark harness with request hashes and replay | code | `benchmark/benchmark.py` |
| OpenCode (MIT) | Message list as the state machine: subtasks, compaction, overflow are parts; resume, fork, revert fall out | code | `session/prompt.ts` |
| OpenCode | Permission engine: tree-sitter-parsed bash, arity-based "always allow" patterns, last-match-wins rules, rejection with feedback to the model | code | `tool/shell.ts`, `permission/arity.ts`, `permission/index.ts` |
| OpenCode | Side-gitdir snapshots with per-step patches and revert | code | `snapshot/index.ts`, `session/revert.ts` |
| OpenCode | Compaction: verbatim recent tail, chained summaries in a fixed schema, separate tool-output pruning | code | `session/compaction.ts` |
| OpenCode | Post-edit LSP diagnostics and formatter as a hard signal, about 30 language servers | code | `tool/edit.ts:112, 197-201`, `lsp/` |
| OpenCode | Plugin hooks on every seam: tool before and after, message, system, params, compaction, events | code | `packages/plugin/src/index.ts` |
| OpenCode | Doom-loop detection on identical consecutive tool calls | code | `session/processor.ts` |
| Cline (Apache-2.0) | Git-native checkpoints: 3-parent stash commits in private refs, persistent private index, compare-and-swap restore that refuses when HEAD moved | code | `hooks/checkpoint-hooks.ts`, `session/checkpoint-restore.ts` |
| Cline | Host-agnostic core with real headless surfaces: CLI, NDJSON, ACP, hub daemon, SDK | code | `sdk/ARCHITECTURE.md`, `apps/cli` |
| Cline | Two-tier compaction with a deterministic overflow-recovery path that needs no model call | code | `agent-runtime.ts:961`, `basic-compaction.ts` |
| Cline | Interaction mode stamped on every user message and mode switches announced | code | `prompt/format.ts` |
| Cline | Hooks that copy the Claude Code event schema, so one hook set serves two hosts | code | `hooks/hook-file-hooks.ts` |
| Continue (Apache-2.0) | Content-addressed, branch-tagged incremental index shared by chunks, FTS5, LanceDB, symbol snippets, resumable per file | code | `core/indexing/refreshIndex.ts`, `CodebaseIndexer.ts` |
| Continue | Collapsed-AST chunker: class and function skeletons with bodies elided plus full children, under 500 tokens | code | `core/indexing/chunk/code.ts` |
| Continue | Context provider abstraction with declared index dependencies | code | `core/context/index.ts` |
| Continue | Rule applicability engine: globs, negative globs, content regex, colocated rules, agent-requestable rules | code | `core/llm/rules/getSystemMessageWithRules.ts` |
| Continue | Per-call policy escalation and a standalone terminal-security package | code | `packages/terminal-security/` |
| Continue | History pruning that never orphans a tool result | code | `core/llm/countTokens.ts:368-545` |
| SWE-agent (MIT) | Tool bundle: schema YAML, executables, install script, state command; generates both function schemas and text docs | code | `sweagent/tools/bundle.py`, `commands.py` |
| SWE-agent | Revert-on-new-lint editing that maps pre-existing errors through the edit window; uniqueness-checked replace | code | `tools/windowed/lib/flake8_utils.py`, `str_replace_editor:516-534` |
| SWE-agent | Autosubmit on every failure path, recovering the diff even from a dead container | code | `agents.py:attempt_autosubmission_after_error`, `tools/diff_state` |
| SWE-agent | Full per-step query capture plus replay config | code | `agents.py:add_step_to_trajectory` |
| SWE-agent | Composable history processors applied at query time | code | `history_processors.py` |
| SWE-agent | Sample-then-judge retry loops over complete attempts | code | `reviewer.py` |
| mini-SWE-agent (MIT) | Stateless action execution, exception-as-message control flow, messages equal trajectory; reported over 74 percent on SWE-bench Verified with bash only | code | `agents/default.py`, `environments/local.py` |

## 3. Weakness inventory, grouped into classes

Weakness classes are the rows of the cross-map in Section 4. Each class lists which systems exhibit it, with the card's citation for the strongest instance.

| Class | Weakness | Systems that exhibit it | Strongest evidence |
|---|---|---|---|
| A | Process enforced by prose only; every gate can be skipped | Superpowers, BMAD, Spec Kit, gstack (control flow), ECC (rules) | Superpowers `CLAUDE.md:7-8` admits agents ignore its rules; BMAD `workflow.md` "NEVER load multiple step files" unchecked; Spec Kit hooks executed by the model from `EXECUTE_COMMAND:` text |
| B | No task-size triage; fixed ceremony on trivial work | Spec Kit, Superpowers, gstack (routing), ECC (absolutist rules), BMAD (finding floor) | Spec Kit one-line CSS change produces user stories, success criteria, a 16-item checklist, 5 to 8 files; Superpowers "1 percent chance" rule plus never-scaling approval gate |
| C | Instruction and token volume | ECC (21 to 23k always-on), gstack (12 to 28k per skill, 6.5k repeated preamble), Superpowers (16k per feature), BMAD (6 to 9k per Build), OpenCode (8 to 9k fixed prefix per call including subagents) | Measured word counts in each card |
| D | No repository understanding beyond grep and read | Superpowers, ECC, Spec Kit, gstack (default), BMAD, OpenCode (shipped default), Cline, SWE-agent, mini | Cline card: no repo map, no definitions listing, no diagnostics feed; OpenCode `lsp` tool behind an experimental flag |
| E | Done means the model stopped; no verification gate | OpenCode, Cline, Continue, Aider (tests off by default), SWE-agent (patch is the deliverable), Spec Kit (self-ticked checklist) | OpenCode loop exit is finish-reason only; Spec Kit `specify.md` step 8 ticks its own checklist that `implement.md` step 2 then gates on |
| F | Memory absent, or present but unsafe or inert | Absent: Aider, Cline, Continue, SWE-agent, Spec Kit, Superpowers. Inert: ECC learning v1 (no-op), gstack auto-learning (43 of 44 learnings were explicit) | `evaluate-session.js:88-97`; `generate-completion-status.ts` comment on #2402 |
| G | Long-horizon loss at compaction | SWE-agent (`exit_context` ends the run), Continue IDE (manual only), Cline (2000-char evidence truncation), Superpowers (ledger exists because compaction lost place) | `agents.py:1188`; `compaction-shared.ts:21`; `SDD/SKILL.md:131-134` |
| H | Multi-agent overhead and duplicated work | gstack (`/ship` reruns the review army after `/review`), BMAD (3 to 4 reviewers per change, forced finding floor), ECC (4 to 6 subagent contexts on a bug) | `ship/SKILL.md.tmpl` "Never skip a verification step"; BMAD `customize.toml` Blind Hunter floor |
| I | No tooling for intermittent or concurrency bugs: no repeat runner, no instrumentation harness | All ten | Every card's hard-task trace ends with "the race analysis is left to the model" |
| J | Security gaps: injection unaddressed, headless auto-allow, secrets | Superpowers (none), BMAD (thin, TOML overrides run shell), Spec Kit (headless all tools), Cline CLI (auto-approve, no destructive detection in act), Continue CLI (Bash and MCP auto-allowed), SWE-agent (root, secrets in logs) | `defaultPolicies.ts:29-35`; `apps/cli/README.md:312`; `copilot/__init__.py:55-75` |
| K | Model routing is prose or static | Superpowers (prose tiers), ECC (static frontmatter), Aider (three fixed slots), gstack (baked overlay), Continue (role registry) | Superpowers `SDD/SKILL.md:204-206` "nothing verifies a model was set" |
| L | Self-confirming review: reviewer reads the implementer's narrative or its own checklist | Spec Kit (self-ticked), Superpowers (reviewer reads implementer report, told to distrust it), SWE-agent chooser (reads patches, does not run tests) | `task-reviewer-prompt.md:64-71`; `reviewer.py:Chooser.build_messages` |
| M | Ambiguity handling is either absent or unbounded | Aider, Cline, Continue, OpenCode, SWE-agent (no clarification mechanism); gstack (13-item self-check on every question, over-asking risk) | Cards' trivial traces |
| N | Learning from outcomes does not exist or is a daemon nobody runs | ECC v2 needs a separate daemon; gstack specialist stats is the single working example | `bin/gstack-specialist-stats`; `observe-runner.js` |
| O | Author- or project-specific content leaks into generic process | gstack (`bin/test-lane`, Rails globs, personal preferences), ECC (non-coding domain skills), Spec Kit (ignore-file generation in implement) | `ship/sections/tests.md.tmpl`; `implement.md` step 4 |
| P | Host coupling by copying: parallel renderings kept in sync by scripts | ECC (16 targets, four copies of agents), Superpowers (12 manifests), BMAD (three copies of the build pipeline) | ECC `scripts/build-opencode.js`; BMAD `bmad-build` versus `bmad-build-auto` drift |

## 4. The cross-map: weakness class to covering strength

For each weakness class: which strength from another system covers it, by what mechanism, at what cost, and how much of the class it actually covers. Coverage is rated full, partial, or none.

| Class | Covering strength (system) | Mechanism | Cost or caveat | Coverage |
|---|---|---|---|---|
| A prose enforcement | Pre-tool hooks that deny (ECC hook runtime, gstack freeze and careful, OpenCode permission engine, Cline command guard); Claude Code `PreToolUse`, `Stop`, `PostToolBatch`, `TaskCompleted` hooks (host card) | code | Every existing gate is a tool-level guard (which file, which command). None enforces a process-stage rule such as "reproduce before editing" or "evidence before done". gstack's `verify-gate` is the only Stop-time gate and it checks one declared command | partial |
| B no triage | ECC size-to-ceremony classifier; BMAD route-after-investigation; Superpowers three-path brainstorm; Spec Kit lean preset as proof that ceremony is separable from contract | prose | All three classifiers are prose the model applies to itself. None is calibrated against outcomes. The BMAD and ECC versions are the best-specified and can seed a code classifier | partial |
| C token volume | Claude Code progressive disclosure (descriptions only, 1 percent listing budget); Superpowers 680-token bootstrap; gstack token ratchet in CI and context bill; BMAD numeric budgets in artifacts; Continue rule applicability; ECC path-scoped rules; Spec Kit lean preset | code, CI, protocol | Progressive disclosure fails silently when too many skills are installed (listing truncated by usage) and the listing is not reloaded after compaction (host card). No system budgets per stage of a task | partial |
| D no repo model | Aider repo map (symbol graph, PageRank, budgeted render); Continue index (FTS5, embeddings, collapsed AST, symbol snippets, incremental); OpenCode LSP diagnostics; gstack diff-scope flags; SWE-agent filemap | code | Aider's map is defs-only, hint bag unfiltered, rebuilt each turn on mid-size repos. Continue's repo-map selection spends an extra model call on the whole file list. Neither has test-to-source edges, ownership, or a blast-radius number. Both are portable modules under permissive licenses | partial |
| E no verification gate | gstack evidence ledger, sentinel protocol, verify-gate Stop hook; ECC batched Stop typecheck; OpenCode post-edit LSP diagnostics; SWE-agent revert-on-lint; BMAD diff-based judging and Matrix Test Audit (prose); Superpowers verification-before-completion (prose); Cline yolo `submit_and_exit` nag; Claude Code `Stop` and `TaskCompleted` hooks | code and prose | gstack binds "tests passed" to a working-tree hash, which is the closest thing to an evidence contract in the field. What is missing everywhere: typed claims, evidence requirements that scale with risk, automatic parsing of test output into evidence, and abstention as a valid outcome | partial |
| F memory | gstack learnings and decisions (decay, trust gate, injection filter, supersede); ECC worktree-keyed recall with stale marker; BMAD memlog and provenance-SHA admission rules; Claude Code auto memory (host card) | code | The two systems with real memory code both report that automatic capture does not produce useful records. Retrieval is by scope and recency, never by task profile. No system validates a memory against later outcomes | partial |
| G compaction loss | OpenCode compaction (verbatim tail, chained schema, separate pruning); Cline deterministic overflow recovery; Superpowers ledger and resume rules; Continue CLI threshold formula; Claude Code `PreCompact`, `SessionStart(compact)`, invoked-skill re-injection | code, protocol | Well covered for conversation state. Not covered: task state outside the conversation. Every system reconstructs from the summary; only Superpowers reconstructs from a ledger, and only by prose | partial |
| H multi-agent overhead | gstack adaptive gating by hit rate, confidence gate, fingerprint dedup; BMAD parent-verifies-every-finding; Superpowers no-subagents-for-workers and sequential dispatch; ECC delegation completion contract; Claude Code subagents with fresh context, model, turn cap, worktree | code and prose | gstack's hit-rate gating is the only mechanism that turns overhead down based on evidence. Nobody decides whether to spawn at all from a task profile | partial |
| I intermittent bugs | Superpowers condition-based waiting and instrument-then-trace (prose); BMAD I/O matrix rows and race-aware edge-case lens (prose); gstack investigate 3-strike (prose) | prose | No repeat runner, no stress harness, no instrumentation tooling, no hypothesis ledger in any system | none |
| J security | gstack (nonce-bound instruction blocks, fail-closed hooks, egress receipts, redaction, untrusted envelopes, injection filter on learnings); OpenCode permission engine and lazy nested instruction injection; ECC destructive classifier; Continue terminal-security and per-call escalation; Spec Kit CLI hardening and URL trust policy; Claude Code `--bare` and permission modes | code | Strong coverage for commands, secrets, and browser content. Not covered: trust levels on every context item, memory writes from untrusted origins held for confirmation, tool descriptions as untrusted | partial |
| K model routing | Claude Code subagent `model` field and `CLAUDE_CODE_SUBAGENT_MODEL`; OpenCode per-agent model and small_model; Aider weak and editor slots; Continue role registry; Superpowers tier prose | code (host), prose (policy) | The mechanism to route exists in the hosts. No system has a routing policy driven by task difficulty or evidence | partial |
| L self-confirming review | BMAD blind-then-claims ordering and verdict-then-route; gstack quote-before-report gate and fresh-context adversarial pass; ECC zero-findings-allowed reviewer; Claude Code fresh-context subagents | prose protocol with JSON contract | Well specified. Composable as a critic procedure. Cost: BMAD's forced finding floor guarantees noise on tiny diffs; drop the floor, keep the ordering | full (as procedure) |
| M ambiguity | Spec Kit bounded clarify with write-back; BMAD open-question admission rule ("the request does not say, the code cannot settle, the user would notice"); Superpowers one question per message; gstack decision brief format; Cline and Continue `ask_question` tools | prose protocol | Two good protocols exist (Spec Kit and BMAD). Neither is gated by a measured ambiguity signal; both fire by command or by the model's judgment | partial |
| N learning | gstack specialist stats (skip a reviewer with zero hits in 10 dispatches); Superpowers skill-testing method (baseline without skill, pressure scenarios); ECC instincts with confidence threshold | code (gstack), method (Superpowers) | gstack's is the only closed loop from outcomes to policy, and it is narrow. The Superpowers method is the right shape for validating any proposed instruction change | partial |
| O leakage | BMAD evidence-admission rules for project context; Continue rule applicability; Claude Code path-scoped rules | prose plus script | Covered in principle; the leaking systems simply do not apply it to themselves | partial |
| P host coupling by copying | Spec Kit one-source substitution pipeline; gstack host config as data; Superpowers action vocabulary; Cline SDK-first core; Continue hooks copying Claude Code's schema | code, data | The generation approach (Spec Kit, gstack) beats the copy approach (ECC, BMAD). Continue's decision to adopt Claude Code's hook schema verbatim suggests a de facto standard is forming | full |

## 5. Residual gaps: what no system covers

These are the only places where new architecture is justified. Each is stated with the nearest existing partial cover, so that the new work starts from it rather than from zero.

1. **Process-stage gates enforced by code.** Every gate in the field is tool-level. Nothing can enforce "a failing reproduction exists before an edit is allowed" or "a completion claim needs these evidence records". Nearest cover: gstack `verify-gate` (one command at Stop), Claude Code `Stop`, `PostToolBatch`, `TaskCompleted` hooks, ECC batched Stop check. Target: a ledger-driven gate that reads the compiled workflow's current stage and its exit evidence.
2. **A calibrated task classifier.** Three prose classifiers exist (ECC, BMAD, Superpowers). None is backed by outcomes. Nearest cover: ECC's table (files, dependency, ambiguity) and BMAD's route rule (intent gaps, irreversibles, footprint) as the initial feature set; the evaluation harness as the label source.
3. **Typed claims with risk-scaled evidence contracts and automatic evidence capture.** Nearest cover: gstack's fingerprint-bound evidence ledger and sentinel lines; BMAD's Matrix Test Audit; the submit-resolve gap paper (reading list) for abstention as a valid outcome. Target: claims parsed from tool output by code, contracts compiled per task, UNVERIFIED as a first-class end state.
4. **A task-conditioned repository model with test and dependency edges and a blast-radius number.** Nearest cover: Aider's PageRank map (portable, Apache-2.0) and Continue's incremental index and collapsed chunker (Apache-2.0). Neither has test-to-source edges, ownership, or a computed blast radius. Target: build on Aider's graph, add edges, benchmark each tier.
5. **Externalized task state that survives compaction and host switch.** Nearest cover: Superpowers ledger (prose-driven), BMAD spec status frontmatter, OpenCode message-parts-as-state, Cline run-count checkpoints keyed to survive compaction. Target: a ledger the runtime writes and re-injects, not one the model is asked to maintain.
6. **Tooling for intermittent and concurrency bugs.** No cover at all. Target: repeat runner with variance reporting, instrumentation helpers, hypothesis ledger with discriminating tests; Superpowers' condition-based-waiting note and BMAD's I/O matrix as the procedural seed.
7. **Memory write gating that produces useful records.** Both real implementations report failure of automatic capture. Nearest cover: gstack decay and trust gate, BMAD admission rules with provenance SHA. Target: writes only as proposals from a retrospective, with evidence links, validated by replay before promotion.
8. **Replay-gated learning.** Nearest cover: gstack specialist stats (outcome-driven, narrow), Superpowers' baseline-without-skill test method. Target: every proposed change to a procedure, template, or routing policy is replayed on the relevant task subset before it is promoted.
9. **Composition without dilution.** No system measures what happens when frameworks are stacked. The host card shows the skill listing is budgeted and truncated by usage, so stacking silently loses skills. Target: the composition baseline experiment in Section 6.
10. **Decision-level observability.** Cost accounting exists (Aider, gstack, Cline, OTel). No system records why a stage ran, why a reviewer was spawned, or why a gate blocked. Target: a decision record per task.

## 6. The composition baseline

The user's first goal is to combine strengths. The cleanest test of that goal is a stack of best-of-breed pieces installed together on Claude Code, measured against each piece alone and against vanilla. If the stack does not beat its parts, composition is diluting, and the runtime's first job is to make composition selective.

Recipe (everything MIT or Apache-2.0; attribution in NOTICE):

| Concern | Piece | From | Form |
|---|---|---|---|
| Process procedures | brainstorming three-path triage, systematic debugging, condition-based waiting, verification-before-completion, finishing-a-branch | Superpowers | skills, as-is |
| Subagent handoff | task-brief, review-package, sdd-workspace scripts; implementer and reviewer templates | Superpowers | scripts plus templates |
| Hard blocks | block-no-verify, config-protection, destructive classifier | ECC | PreToolUse hooks only, not the plugin |
| Stop-time checks | edit accumulator plus batched typecheck | ECC | Stop hook |
| Evidence ledger | gstack-evidence, gstack-wtree, verify-gate | gstack | bin scripts plus optional Stop hook |
| Browser evidence | bundled Playwright daemon and `$B` CLI | gstack | standalone binary |
| Command safety | careful and freeze hooks | gstack | hooks, opt-in |
| Repository map | `repomap.py` and tag queries | Aider | wrapped as one MCP tool returning a budgeted map |
| Large-feature artifacts | lean preset commands and the feature pointer | Spec Kit | commands, lean only |
| Review procedure | blind-then-claims ordering, verification-gap lens, verdict-then-route | BMAD | one critic subagent definition, no finding floor |
| Checkpoints | Claude Code worktree subagents; `git stash create` snapshot idea | host; Cline | host feature |
| Model per role | subagent `model` frontmatter | host | host feature |

Exclusions and why: the full ECC catalog (13k tokens of descriptions per turn), full gstack skills (6.5k preamble per invocation, macOS-first browser contract), BMAD skills (uv dependency, triplicated pipeline, finding floor), Continue's index (IDE-bound, retrieval stages disabled), SWE-agent bundles (Python-only, container-bound).

Conflicts the composition must resolve, all observed in the cards:

- Three routing instructions compete for the same request: Superpowers "1 percent chance, invoke the skill", gstack "when in doubt, invoke the skill", ECC "use agent X, no user prompt needed". All three over-route trivial work.
- Two Stop hooks (ECC typecheck, gstack verify-gate) and three reviewer mechanisms (Superpowers task reviewer, gstack review army, ECC auto-spawned code-reviewer) would all fire on one change.
- The Claude Code skill listing budget is 1 percent of the context window and truncates least-used skills; stacking Superpowers (14 skills) with even the lean Spec Kit commands and any gstack skills risks silent loss of discoverability. Measure with `/context` and `/skill-doctor`.
- Superpowers' TDD absolutism and ECC's mandatory coverage rule both fire on CSS and config edits.
- Every piece writes its own state directory: `.superpowers/`, `~/.gstack/`, `~/.claude/sessions/`, `.specify/`.

These conflicts are the first concrete argument for a runtime that selects among the pieces per task instead of loading them all. That is the composition problem, and it is the same problem as the workflow compiler in the plan.

## 7. What this changes in the plan

- Phase A's "competitor architecture map" is now grounded in source at recorded commits (Section 2 and `competitor-map.md`).
- The "reason to exist" test is sharpened: the system must beat the composition baseline of Section 6, not only vanilla and single frameworks.
- The ten residual gaps in Section 5 replace the speculative "unsolved problems" list in v0.1. Architecture components that do not address one of them are removed.
- Several v0.1 ideas have prior art that must be cited and built on rather than reinvented: evidence ledger (gstack), ledger for compaction (Superpowers), blind review ordering (BMAD), bounded clarification (Spec Kit), repo map (Aider), incremental index (Continue), checkpoints (Cline, OpenCode), message-as-state (OpenCode), tool bundles and revert-on-lint (SWE-agent), minimal loop as baseline (mini-SWE-agent).
- Two host facts change the runtime design: Claude Code's `PostToolBatch` and `TaskCompleted` hooks give control points between tool batches and on task completion, and OpenCode has no session-end hook, so the evidence gate must also exist as a final tool the rules file names.
