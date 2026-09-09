# cline

- Repo: https://github.com/cline/cline
- Commit: b18de0904f66e6235e59c55cad047478108e4bfa (2026-09-08T21:24:58-07:00, shallow clone)
- License: Apache-2.0 (`LICENSE`)
- Language: TypeScript (2311 `.ts` + 692 `.tsx` of 3920 tracked files; Bun 1.3.13 toolchain, Node >= 22 per `AGENTS.md`)
- Layout note: the historical `src/core` tree no longer exists at this commit. Cline is now a monorepo: `sdk/packages/{shared,llms,agents,core,sdk,ui}` hold the engine; `apps/vscode`, `apps/cli`, `apps/cline-hub` are hosts. The VS Code extension is a thin host over the SDK (`apps/vscode/src/sdk/*`). `sdk/ARCHITECTURE.md` is the layering doc.

Cline is a tool-calling coding agent whose loop lives in `sdk/packages/agents/src/agent-runtime.ts` and whose stateful orchestration (sessions, persistence, compaction, checkpoints, hooks, MCP, plugins, hub daemon, cron) lives in `sdk/packages/core`. It runs identically inside VS Code, a terminal CLI/TUI, an ACP server, or a detached "hub" daemon. Its distinguishing pieces are a git-native checkpoint system that snapshots the user's own repo into private refs, a Plan/Act mode split enforced by tool presets plus a shell-command blacklist, per-tool approval policies, and an LLM-driven ("agentic") context compaction pipeline with a deterministic fallback for overflow recovery.

## Request flow (cite files)

1. CLI entry: `apps/cli/src/main.ts` parses args (`apps/cli/src/commands/program.ts`), builds a `Config`, and calls `runAgent` (`apps/cli/src/runtime/run-agent.ts`) for one-shot, `runInteractive` (`apps/cli/src/runtime/run-interactive.ts`) for the TUI, or `acpAgent.ts` for ACP. VS Code entry: `apps/vscode/src/sdk/cline-session-factory.ts` builds the session config and prompt; `apps/vscode/src/sdk/SdkController.ts` owns the session.
2. Both hosts go through `@cline/core` `RuntimeHost` (`sdk/packages/core/src/runtime/host/runtime-host.ts`) which picks `LocalRuntimeHost` (`runtime/host/local-runtime-host.ts`) or a hub-backed host (`hub/runtime-host/hub-runtime-host.ts`).
3. `local-runtime-bootstrap.ts` merges hooks (checkpoint hooks at line 504 if `checkpoint.enabled`), tool policies, and executors; `runtime/orchestration/runtime-builder.ts` assembles tools by preset, MCP tools (line 281-300), skills, and the plan-mode command guard (line 552-560).
4. Each user turn: `LocalRuntimeHost.prepareTurnInput` (`local-runtime-host.ts:2105`) normalizes the text, enriches `@path` mentions (`services/workspace/mention-enricher.ts`), and wraps it as `<user_input mode="act|plan|yolo">` (`sdk/packages/shared/src/prompt/format.ts`).
5. `SessionRuntimeOrchestrator.composeSystemPrompt` (`runtime/orchestration/session-runtime-orchestrator.ts:707`) appends registered rule contributions to the base prompt; `createRuntimePrepareTurn` (line 898) installs compaction as the runtime's `prepareTurn`.
6. `AgentRuntime.execute` (`agent-runtime.ts:690-940`): loop until no tool calls or a `completesRun` tool fires; per iteration `generateAssistantMessageWithOverflowRecovery` (line 961), `beforeModel` hooks (line 1074), then `executeToolCalls` with `beforeTool` hooks, policy resolution, approval (line 1709-1762), and results appended as tool messages. Hook-injected context becomes a hidden `displayRole: "system"` user message (line 826-845).
7. Persistence after each turn via `session/services/persistence-service.ts` into `~/.cline/data/sessions` (`sdk/packages/shared/src/storage/paths.ts:192`).

## What goes into the model (always-loaded vs on-demand, with token estimates)

Token estimates use the repo's own heuristic, `CHARS_PER_TOKEN = 3` (`sdk/packages/shared/src/llms/tokens.ts:8`).

Always loaded (read from source):
- Base system prompt `DEFAULT_CLINE_SYSTEM_PROMPT` (`sdk/packages/shared/src/prompt/system.ts`): ~3.6k chars, ~1.2k tokens. `YOLO_CLINE_SYSTEM_PROMPT`: ~2.9k chars, ~1k tokens. Contains an `<env>` block (platform, date, IDE, cwd) and strong parallel-tool-call instructions. Selection and templating in `sdk/packages/shared/src/prompt/cline.ts` `buildClineSystemPrompt`.
- `MODE_TAG_INSTRUCTIONS` (~0.7k chars) always; `PLAN_MODE_INSTRUCTIONS` (~1.9k chars, ~0.6k tokens) in plan mode (`prompt/cline.ts`).
- Rules: enabled rule files rendered as `# Rules` / `## <name>` (`sdk/packages/core/src/runtime/safety/rules.ts:10`), registered as a contribution by `extensions/config/user-instruction-plugin.ts:256` and merged at `composeSystemPrompt`. Size is user-controlled; unbounded.
- Workspace metadata JSON (root path, hint, redacted remotes, latest commit, branch) only when the provider is Cline's own gateway (`prompt/cline.ts` `buildWorkspaceMetadata`, `isClineProvider`).
- Tool definitions: 9 built-ins in `sdk/packages/core/src/extensions/tools/definitions.ts` (file is 30.8k chars including code; descriptions plus zod-derived JSON schemas are inferred to be ~2-4k tokens). MCP tools add one definition each (`extensions/mcp/tools.ts`). The `skills` tool description is dynamically extended with the skill list (`definitions.ts:~790`).
- Preferred-language suffix in VS Code (`cline-session-factory.ts:~940`).

Not loaded per turn (inferred from absence): there is no `environment_details` block, no per-turn file listing, no open-tabs/terminal dump, and no repo map. I found no builder for any of these in `sdk/packages/core/src/runtime` or `local-runtime-host.ts`. Context arrives only through tool results and `@` mentions.

On demand: `read_files` (max 2000 lines / 48k chars per read), `search_codebase` (48k chars, middle-truncated), `run_commands` (48k chars, middle-truncated) — all in `extensions/tools/executors/output-limits.ts`. `skills` returns SKILL.md bodies. `fetch_web_content` uses native fetch with a 5MB cap (`executors/web-fetch.ts`).

## Tools

Built-ins (`extensions/tools/definitions.ts`, names in `constants.ts`): `read_files`, `search_codebase` (regex, multi-query), `run_commands` (shell, batched, description re-derived per request for shell kind), `fetch_web_content`, `apply_patch` (disabled in every preset in `presets.ts`), `editor` (create / replace `old_text` / insert at line), `skills`, `ask_question` (one question, 2-5 options), `submit_and_exit` (`lifecycle.completesRun: true`; yolo only). Extras: MCP tools named `server__tool` (`extensions/mcp/tools.ts`, `name-transform.ts`); `spawn_agent` (`extensions/tools/team/spawn-agent-tool.ts`); a large team tool family (`team/team-tools.ts`, `team/multi-agent.ts`, 1943 lines); agenda/todo task tool (`tasks/agenda-task-tool.ts`); `switch_to_act_mode` in the CLI only (`apps/cli/src/runtime/interactive/mode.ts`). Tools declare `timeoutMs`, `retryable`, `maxRetries` (`sdk/packages/shared/src/tools/create.ts`). Model-side routing rules can enable/disable tools by provider/model id substrings (`extensions/tools/model-tool-routing.ts`).

## Plan and Act modes

- Presets (`extensions/tools/presets.ts`): `plan` removes `editor` but keeps `run_commands`, `read_files`, `search_codebase`, `fetch_web_content`, `skills`, `ask_question`, spawn/team. `act` adds `editor`. `yolo` drops search/web/skills/ask/spawn, adds `submit_and_exit`, and auto-approves everything (`createToolPoliciesWithPreset`).
- Prompt contract (`prompt/cline.ts`): plan mode text forbids edits and state-changing commands; CLI variant tells the model to call `switch_to_act_mode` only after explicit user approval; VS Code variant (`planModeSwitchTool: false`, `cline-session-factory.ts:931`) tells it to ask the user to "toggle to Act mode".
- Hard backstop: `extensions/tools/command-guard.ts` masks quotes/heredocs/comments, splits on shell separators, and rejects a blacklist of file-mutating commands, mutating `git`/npm/pip/cargo subcommands, and file redirections, returning a tool error. The header comment admits it is a blacklist, not an interpreter (e.g. `python -c` writes pass).
- Mode switches are recorded in the transcript: `<user_input mode=...>` on every user message, `<mode_notice>` on the first message after a UI toggle (`prompt/format.ts` `formatModeSwitchNotice`, `createModeSwitchNoticeTracker`). System prompt swaps between modes are therefore explained to the model rather than silent.

## Checkpoints (detailed mechanism)

The old "shadow git" (separate `.git` dir) is gone at this commit; `grep -ri "shadow git|CheckpointTracker"` finds nothing. The replacement operates on the user's own repository and never touches the working tree or the real index when snapshotting.

Snapshot (`sdk/packages/core/src/hooks/checkpoint-hooks.ts`):
- Registered as `AgentHooks` (`beforeRun` records message count; `beforeModel` fires only for the root agent at `iteration === 1`). A checkpoint is taken once per new user run, keyed by `runCount = countUserRunMessages(messages)` (`session/user-run-messages.ts`), which is span-aware so numbering survives compaction. Resumed runs that were already checkpointed are skipped so the pre-run snapshot is not overwritten by a mutated workspace.
- `createWorktreeStashCommit`: runs `git stash create <msg>` (tracked changes, no worktree mutation), then `createUntrackedParentCommit`: `git ls-files --others --exclude-standard -z`, `git add --force --pathspec-from-file` into a persistent private index (`GIT_INDEX_FILE` under `~/.cline/data/checkpoint-scratch/<sha256(cwd+sessionId)[:32]>/index`, mode 0700), purges stale entries with `update-index --force-remove --stdin`, `write-tree`, `commit-tree`. The persistent index exists so git's stat cache avoids re-hashing unchanged untracked files each turn; `core.ignorestat=false` and `core.splitIndex=false` are pinned because they would break it. A corrupt index or stale lock is deleted and rebuilt once.
- The final object is a 3-parent commit (`commit-tree <stash tree> -p HEAD -p <index commit> -p <untracked commit>`), mirroring `git stash create --include-untracked`. Clean tree with untracked files synthesizes an index parent; clean tree with nothing untracked falls back to a `kind: "commit"` HEAD entry.
- Stored under `refs/cline/checkpoints/<sessionId>/<runCount>` via `update-ref` so it is GC-safe but invisible in `git stash list`. Entry `{ref, createdAt, runCount, kind}` is written into session metadata (`checkpoint.latest`, `checkpoint.history`). Telemetry event `checkpoint.snapshot` records outcome and duration only.
- Scratch dirs older than 14 days are reaped; `deleteCheckpointRefs` removes refs and scratch on session delete.

Restore (`sdk/packages/core/src/session/checkpoint-restore.ts`), invoked from `session/session-versioning-service.ts:279-284`:
- `beginWorktreeRestoreTransaction`: `git stash push --include-untracked`, move the resulting `refs/stash` to `refs/cline/restore-transactions/<uuid>`, `stash drop` so the user's list is untouched; `rollback()` does `reset --hard <originalHead>`, `clean -fd`, `stash apply --index`.
- `applyCheckpointToWorktree`: verifies the ref, derives `restoreBase` (`ref^1` for stash kind), and refuses if `HEAD != restoreBase` (commits made after the checkpoint, rebase, branch switch) with an explanatory error rather than knocking commits off the branch. Then a compare-and-swap `git update-ref HEAD <base> <currentHead>`, `git reset --hard`, `git clean -fd` only if the snapshot has a `^3` untracked parent (older 2-parent snapshots leave untracked files alone to avoid unrecoverable loss), then `git stash apply <ref>`.
- Messages are trimmed to the run (`trimMessagesToCheckpoint`); forking before a run folded into a compaction summary is refused.
- Diff view (`session/checkpoint-diff.ts`) reads `ref:path` and falls back to `ref^3:path` for previously-untracked files.
- Defaults: core leaves checkpoints off (`local-runtime-bootstrap.ts:504`); CLI turns them on (`apps/cli/src/runtime/defaults.ts`). The VS Code host maps chat messages to run counts in `apps/vscode/src/sdk/sdk-checkpoints.ts`.

## Context window management

- `extensions/context/compaction.ts` runs as `prepareTurn` before every model call. Usable budget = `min(maxInputTokens, contextWindow)` or `0.9 * contextWindow`; default 128k (`compaction-shared.ts:13-18`). Compaction triggers when estimated request tokens (system prompt + tools + messages) >= 0.9 of the budget; target is 0.7; the last ~20k tokens are preserved.
- Strategy default is `"agentic"` (`compaction.ts:286`): `agentic-compaction.ts` serializes the conversation and asks the same provider (`createHandlerAsync`) to "Summarize the provided coding session into a concise continuation note with detailed next steps", inserting a summary message carrying `userRunSpan` so checkpoint numbering survives. `basic-compaction.ts` is deterministic: drops old assistant/tool turns, keeps the last 3 assistant texts verbatim, strips file/image attachments from older user messages, and inserts `<SYSTEM_NOTICE>` summaries of dropped tool activity (`TOOL_RESULT_CHAR_LIMIT = 2000`). CLI exposes `--compaction agentic|basic|off` (`apps/cli/src/utils/compaction-mode.ts`).
- Overflow recovery (`agent-runtime.ts:961-1003`): when the provider reports `context_window_exceeded` and the errored turn had no tool calls, the runtime emits a status notice, forces one compaction with `overflowRecovery: true` (which pins the basic strategy so recovery does not depend on another LLM call, per `compaction.ts` doc comment), retries once, then fails with a terminal message.
- Per-tool output caps (48k chars, middle-truncated) are the only other truncation; there is no per-file-read dedup or "already read" pruning that I found (inferred).

## Task understanding and planning

No explicit planning artifact in act mode. The prompt asks the model to "present your plan at the start of your response along with tool calls" (`prompt/system.ts`). Plan mode is the planning mechanism (above). `ask_question` is the only clarification tool. Loop detection (`runtime/safety/loop-detection.ts`, CLI thresholds soft 3 / hard 5 in `apps/cli/src/runtime/defaults.ts`) and a consecutive-mistake limit (`ConsecutiveMistakeLimitContext` imported in `run-agent.ts`) guard against stuck runs. The agenda task tool (`tasks/agenda-task-tool.ts`) is a SQLite-backed todo/handoff list, not a plan.

## Context selection and repository understanding

Entirely model-driven through `search_codebase` (regex) and `read_files`. `prewarmFileIndex` (`services/workspace/file-indexer.ts`) is started in the CLI for `@` mention completion. There is no AST/repo-map, no embedding index, and no `list_code_definition_names` in the SDK tool set (the name survives only in the VS Code policy mapping `apps/vscode/src/sdk/sdk-tool-policies.ts`). Rules search paths (`sdk/packages/shared/src/storage/paths.ts:522-545`): workspace `AGENTS.md`, `.clinerules/`, `.cline/rules/`, `~/.agents/AGENTS.md`, `~/.cline/rules/`, `~/Cline/Rules`, `~/Documents/Cline/Rules`. Rule files support frontmatter (`user-instruction-config-loader.ts`; VS Code adds path-conditional rules in `apps/vscode/src/core/context/instructions/user-instructions/rule-conditionals.ts`).

## Memory across sessions

Sessions persist to `~/.cline/data/sessions` with a manifest store and message artifacts (`session/stores/*`, `session/services/persistence-service.ts`) and can be resumed (`--id`) or forked (`apps/cli/src/runtime/interactive/fork/`). I found no automatic cross-session memory (no memory file, no learned-facts store); "memory" hits in core are all unrelated (in-memory MCP manager etc.). Cross-session knowledge is manual: rules, skills (`SKILL.md`), workflows, agenda tasks, and cron routines (`sdk/packages/core/src/cron/`).

## Verification: what counts as done (browser tool)

- Act mode: a run ends when the model replies with no tool calls (`agent-runtime.ts:791`). Verification is prompt-only ("Always verify the files you have edited... Always validate your answer with checking the code and running it if possible").
- Yolo mode: `submit_and_exit` is required; the runtime nags with a reminder message if the model stops without it (`getCompletionToolReminderMessage`, `agent-runtime.ts:660-680`) and the YOLO prompt demands the relevant test suite pass first.
- Browser: `apps/vscode/src/services/browser/BrowserSession.ts` (puppeteer-core, chrome-launcher, bundled Chromium or remote CDP on port 9222, screenshots as webp) still exists but is referenced only by controller RPCs (`core/controller/browser/*`) and settings. No tool named `browser_action` is registered in the SDK toolset (`presets.ts`, `definitions.ts`, `apps/vscode/src/sdk/vscode-runtime-builder.ts` only adds MCP tools). Inferred: at this commit the model cannot drive a browser; `fetch_web_content` is plain HTTP.

## Multi-agent / roles

`spawn_agent` delegates a task with a caller-supplied system prompt and returns text + usage (`team/spawn-agent-tool.ts`, `team/delegated-agent.ts`); sub-agent prompts wrap through `buildClineSystemPrompt` only for the Cline provider (`team/subagent-prompts.ts`). Teams add mailboxes, outcomes, run tasks, broadcasts, and shutdown (`team/team-tools.ts`, `team/multi-agent.ts`), persisted in SQLite (`services/storage/sqlite-team-store.ts`). Configured agents load from `.cline/agents` (`team/configured-agent-config.ts`). Hub sessions report root-only vs aggregate usage (`sdk/ARCHITECTURE.md`).

## Model routing

All providers go through an AI-SDK-backed gateway in `sdk/packages/llms/src/providers/` (`gateway.ts`, `ai-sdk.ts`, generated `providers.generated.ts`). Plan and act can use different models in VS Code (`resolveCommittedRuntimeModel(providerId, mode, modelId)` in `cline-session-factory.ts`). Tool availability can be conditioned on model/provider id (`model-tool-routing.ts`). Compaction summaries reuse the session's provider. No automatic cheap/expensive routing.

## Security posture (approvals, auto-approve, destructive commands)

- Policy model: `ToolPolicy { enabled, autoApprove }` per tool name with `"*"` wildcard (`agent-runtime.ts:170`, `:1746-1762`). Unlisted tools default to auto-approved (comment in `apps/vscode/src/sdk/sdk-tool-policies.ts`). If `autoApprove === false` the runtime calls `config.requestToolApproval`; absence of a callback denies. Rejections return a tool error with `TOOL_REJECTION_SUFFIX`.
- CLI: auto-approve is on by default for one-shot runs ("Tool calls are auto-approved by default", `apps/cli/README.md:312`; `--auto-approve false` to review; `-y/--yolo` also enables `submit_and_exit`). Zen/hub sessions run fully auto-approved. Interactive TUI has an approval controller (`apps/cli/src/runtime/interactive/approvals`).
- VS Code: `buildToolPolicies` forces `autoApprove: false` on read/edit/command/web/MCP tools and re-evaluates the AutoApprove bar live (`sdk-tool-policies.ts`); MCP has one global toggle, no per-tool opt-in.
- Destructive commands: the only command classifier is the plan-mode blacklist (`command-guard.ts`); in act mode I found no dangerous-command detection (inferred). Shell runs unsandboxed in the user's environment (`executors/bash.ts`); `runtime/tools/subprocess-sandbox.ts` is an IPC helper for plugins, not a security sandbox.
- User hooks (`hooks/hook-file-hooks.ts`, events in `sdk/packages/shared/src/hooks/events.ts`: `tool_call`, `tool_result`, `prompt_submit`, `pre_compact`, ...) can cancel a tool or inject context. Desktop approvals use file-polling IPC with a 5-minute timeout (`runtime/tools/tool-approval.ts`). Agent plugins are auto-discovered only from the home directory so a repo cannot activate MCP servers (`paths.ts` `resolveAgentPluginSearchPaths`).

## Host coupling / headless capability

Headless is first-class. `cline "prompt"` one-shot, `--json` NDJSON stream, `--yolo`, piped stdin, `--acp` (Agent Client Protocol server in `apps/cli/src/acp/acpAgent.ts`), `-z` background sessions on a detached hub daemon (`sdk/packages/core/src/hub/daemon/index.ts`, dashboard in `apps/cline-hub`), cron routines, and a programmatic SDK (`sdk/packages/sdk/src/index.ts` re-exports `@cline/core`). The VS Code extension is a client of the same core; file reads/terminal are host executors (`apps/vscode/src/sdk/vscode-file-read-executor.ts`, `vscode-run-commands-tool.ts`).

## Observability

PostHog telemetry (`services/feature-flags/posthog.ts`, `services/telemetry/core-events.ts`) plus an OpenTelemetry provider (`services/telemetry/OpenTelemetryProvider.ts`); events include compaction executed/skipped, checkpoint snapshots, tool usage, task lifecycle. Model request diagnostics logged per iteration (`agent-runtime.ts:~1094`). CLI `--verbose` prints time, tokens, cache hits, cost, iterations (`run-agent.ts` `printRunStats`). Hook subprocess logs under `~/.cline`.

## Trace: trivial task (border radius)

Act mode, CLI (read from prompt/tool code; the model's choices are inferred). Turn 1 request: base prompt (~1.2k tokens) + mode-tag section (~0.25k) + rules (0 if none) + 8 tool schemas (~2-4k) + `<user_input mode="act">change the button's border radius</user_input>`. Before the first model call, `beforeModel` takes a checkpoint (`git stash create` + untracked index add; sub-second on a small repo, costly on large untracked trees the first time). The model is told to batch: expected `search_codebase` for `border-radius|borderRadius|Button` in one call, then `read_files` for the hit, then one `editor` call with `old_text`/`new_text`, then a final text reply. With CLI defaults every tool auto-approves; in VS Code each of search/read/edit prompts unless the AutoApprove toggles are on. No diagnostics or build feedback is injected, so "verification" is whatever the model chooses to run. Estimated overhead: 3-4 model round trips, ~5-8k input tokens total. Plan mode would add: `editor` removed, ~0.6k more prompt tokens, the model reads and proposes the change and ends its turn; the user must reply "go" and (CLI) the model calls `switch_to_act_mode`, or (VS Code) the user toggles, adding a `<mode_notice>`; then the act path repeats the read. Net: at least one extra round trip and a second read.

## Trace: hard task (auth race)

Act mode: the model has no repo map, so it must discover structure via regex search (`search_codebase`, 48k cap per query) and paged reads (2000 lines). It can run tests or reproduce with `run_commands` (48k middle-truncated output; long-running processes can be detached via `run.proceed_while_running`, `sdk/ARCHITECTURE.md`). Intermittent failures require repeated runs; loop detection only fires on identical tool signatures, so varied runs are fine. As reads accumulate past 0.9 of the budget, agentic compaction summarizes older turns with an extra LLM call; the summary preserves file lists (`ensureFilesSection`) but drops tool output beyond 2000 chars, so earlier evidence of the race may be lost. A user hook could inject test results. `spawn_agent` could parallelize investigation but each sub-agent starts with no context except its prompt. Plan mode adds structured read-only investigation (git log/diff allowed, `git checkout` blocked by the guard) and `ask_question` for clarifying the auth flow before edits; the guard cannot stop `python -c` writes, so the read-only guarantee is soft. No browser means an OAuth redirect flow cannot be exercised end-to-end.

## Strengths (ranked, concrete, cited)

1. Checkpoints that are correct and cheap: 3-parent stash commits in private refs with a persistent stat-cached index, CAS-guarded restore, and refusal when HEAD moved (`hooks/checkpoint-hooks.ts`, `session/checkpoint-restore.ts`).
2. Host-agnostic core with real headless surfaces: CLI/JSON/ACP/hub daemon/SDK share one loop (`sdk/ARCHITECTURE.md`, `apps/cli/src/main.ts`).
3. Overflow recovery that does not depend on another LLM call (`agent-runtime.ts:961`, `compaction.ts` overflowRecovery path).
4. Mode semantics made explicit in the transcript (`<user_input mode>`, `<mode_notice>`, `prompt/format.ts`) instead of silent system-prompt swaps.
5. Plan-mode enforcement with two layers, prompt plus command blacklist (`command-guard.ts`), and honest documentation of its limits.
6. Uniform hook/extension seams (`hook-file-hooks.ts`, `user-instruction-plugin.ts` `registerRule/registerTool/registerCommand`).

## Weaknesses (ranked, concrete, cited)

1. No repository understanding beyond regex and reads; no repo map, definitions listing, or diagnostics feed (absence in `extensions/tools/definitions.ts`; inferred).
2. Auto-approve on by default in the CLI and no destructive-command detection in act mode (`apps/cli/README.md:312`, only `command-guard.ts` exists and is plan-only).
3. Browser tool is effectively gone from the model's toolset while the puppeteer service lingers (`BrowserSession.ts` vs `presets.ts`); UI verification is impossible.
4. Agentic compaction spends a full model call and truncates tool evidence to 2000 chars (`compaction-shared.ts:21`), which is lossy for debugging tasks.
5. Token estimation is chars/3 (`tokens.ts:8`), so the 0.9 trigger can be badly off for code/JSON-heavy contexts; overflow recovery exists precisely because of this.
6. Very large surface: `local-runtime-host.ts` 2.7k lines, `hub-runtime-host.ts` 2.3k, `multi-agent.ts` 1.9k; hub/team/cron machinery dwarfs the agent loop.

## Genuinely innovative vs mostly prompt engineering

Innovative: the git-native checkpoint design (untracked third parent, persistent private index, CAS restore); span-aware run counting that survives compaction (`user-run-messages.ts`); hub-brokered sessions that multiple clients can attach to. Mostly prompt engineering: the parallel-tool-call exhortations, "show your plan" and "verify at the end" instructions, plan-mode contract text, completion-tool reminders.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Team/multi-agent and hub layers add thousands of lines and many tool schemas when enabled (`presets.ts` enables spawn/team in act by default), inflating per-turn tool tokens.
- Command guard is a regex blacklist (`command-guard.ts`); brittle by design.
- `read_files` re-reads are never deduplicated across turns; nothing prevents the model from re-reading 48k-char files repeatedly (inferred).
- Checkpointing every user turn on repos with huge untracked trees pays a first-turn full hash and a stat pass each turn (`checkpoint-hooks.ts` comments acknowledge this).
- Desktop approval via polling files every 200ms (`tool-approval.ts`).

## Reusable pieces (specific files or ideas, and the license terms for reuse)

Apache-2.0 permits reuse with attribution and a NOTICE if present. Candidates: `sdk/packages/core/src/hooks/checkpoint-hooks.ts` + `session/checkpoint-restore.ts` + `checkpoint-diff.ts` (self-contained, only node + git); `extensions/tools/command-guard.ts` (plan-mode shell blacklist with masking); `extensions/context/basic-compaction.ts` (deterministic compaction with dropped-work summaries); `prompt/format.ts` mode-tag helpers; `runtime/safety/loop-detection.ts`; `extensions/mcp/*` (manager, name transform, oauth); `extensions/tools/executors/output-limits.ts` truncation policy.

## Must not copy

Cline branding, the "You are Cline" prompts, Cline-provider-specific workspace metadata injection (`prompt/cline.ts`), PostHog/feature-flag wiring, and the Cline account/auth code (`core/src/auth/*`). The VS Code webview UI was out of scope and should not be lifted.

## Transferable abstractions (name each, one line)

- Run-count checkpoints: snapshot before the first model call of each user run, key snapshots by user-run index, keep the index stable across compaction.
- Private-ref stash snapshots: `git stash create` + synthetic untracked parent stored under `refs/<tool>/...` so nothing appears in the user's stash or history.
- CAS restore guard: refuse workspace restore when HEAD moved; separate "chat only" restore.
- Tool policy triple: `{enabled, autoApprove}` per tool with wildcard, resolved after `beforeTool` hooks can override.
- Mode tags in transcript: annotate each user message with the interaction mode and mark switches explicitly.
- Two-tier compaction: LLM summary by default, deterministic strategy forced on provider overflow, single retry.
- Completion tool with `completesRun` lifecycle plus reminder nag for unattended runs.
- Rule/skill/workflow contribution registry with file watchers, rendered into the prompt lazily at compose time.

## Open questions that need a probe run to answer

- Actual per-turn token cost of the 8-9 built-in tool schemas plus team tools in act mode.
- How often agentic compaction fires on a 200k-window model during a 50-file investigation, and how much evidence the 2000-char tool truncation loses.
- Checkpoint snapshot latency on a repo with 50k untracked files (node_modules ignored vs not).
- Whether the model reliably batches tool calls as instructed, or serializes anyway.
- Whether any host at this commit still surfaces a working `browser_action`, or whether the puppeteer service is dead code.
- Plan-mode escape rate: how often models bypass the command guard via interpreters.
