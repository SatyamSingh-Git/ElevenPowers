# opencode

- Repo: https://github.com/anomalyco/opencode (cloned fine; no redirect from sst/opencode needed, though the repo history shows the org move — `packages/opencode/src/session/prompt/anthropic.txt` still points bug reports at anomalyco).
- Commit: `830d5eb5354874105cc31599635a80c1662609e8`, 2026-09-09T03:34:25Z, "sync release versions for v1.18.30" (`packages/opencode/package.json` version 1.18.30).
- License: MIT (`LICENSE`, "Copyright (c) 2025 opencode").
- Primary language: TypeScript (2721 `.ts` + 608 `.tsx` of 6621 tracked files; Bun runtime, Effect-TS everywhere). Monorepo of 30 packages; the agent core is `packages/opencode/src` (~41k lines across the files read here), with shared schema/types in `packages/core`, `packages/plugin`, `packages/llm`.
- All paths below are relative to `packages/opencode/src/` unless prefixed.

opencode is a provider-agnostic coding agent that runs as a local HTTP server (`server/`) with a TUI, a headless CLI (`cli/cmd/run.ts`), an ACP server (`cli/cmd/acp.ts`), and an SDK client. The agent loop (`session/prompt.ts`) is a "message list is the state machine" design: every step re-reads the session's messages from SQLite, decides whether to run a subtask, compaction, or an LLM turn, and pushes new messages/parts back. Tools, agents, permissions, and plugin hooks are all Effect services; the LLM path is Vercel AI SDK by default with an opt-in native runtime (`session/llm/AGENTS.md`). Everything read below is from source; items marked (inferred) are my reading of behaviour, not something the code states.

## Request flow (cite files)

1. Entry: CLI `opencode run` (`cli/cmd/run.ts`) or any client calls the server's `session.prompt` route, which lands in `SessionPrompt.prompt` (`session/prompt.ts` ~L1000). ACP (`acp/service.ts`) and TUI go through the same SDK/HTTP surface.
2. `prompt()` → `revert.cleanup` (drops reverted messages) → `createUserMessage` (`session/prompt.ts` ~L620-990): resolves the agent (`agents.get` or `defaultInfo`), model (explicit → agent.model → session's last model → provider default), expands `@file` parts by running the `read` tool inline (with LSP symbol-range lookup for `?start=`), `@agent` parts into a synthetic "call the task tool with subagent X" text, MCP resource parts, then fires plugin `chat.message`, persists message + parts.
3. `loop()` → `SessionRunState.ensureRunning` → `runLoop` (`session/prompt.ts` ~L1030-1330). Each iteration: `MessageV2.filterCompactedEffect` (history after last compaction), `MessageV2.latest` to find last user/assistant/pending tasks; exits when the last assistant finished with a non-tool-call reason and parent is the last user message. Step 1 forks title generation (`agent/prompt/title.txt`) and diff summary.
4. Pending `subtask` part → `handleSubtask` (runs `TaskTool` directly, with `tool.execute.before/after` hooks). Pending `compaction` part → `compaction.process`. Overflow check via `compaction.isOverflow` → creates a compaction part and loops.
5. Otherwise: `SessionReminders.apply` (plan/build synthetic reminders), create assistant message, `SessionProcessor.create` (`session/processor.ts`), `SessionTools.resolve` (`session/tools.ts`) builds the AI-SDK tool map wrapped with permission `ask`, plugin `tool.execute.before/after`, truncation. System prompt assembled from `SystemPrompt.environment/skills/mcp` (`session/system.ts`) + `Instruction.system()` (`session/instruction.ts`), then `handle.process` → `LLM.stream` (`session/llm.ts`) → `LLMRequestPrep.prepare` (`session/llm/request.ts`) builds the final system array, params, headers, tool filtering.
6. `SessionProcessor.handleEvent` consumes the LLMEvent stream: creates reasoning/text/tool parts, snapshots the worktree at `step-start`/`step-finish` (`snapshot/index.ts`), detects doom loops (3 identical consecutive tool calls → `doom_loop` permission ask), applies `SessionRetry.policy` (`session/retry.ts`: 5 retries, exp backoff, honours `retry-after`), returns `"compact" | "stop" | "continue"`.
7. After the loop: `compaction.prune` (forked) clears old tool outputs.

## What goes into the model (always-loaded vs on-demand, with token estimates)

Byte sizes from `wc -c`; token estimates use ~4 chars/token (inferred, not measured).

Always loaded per request (`session/llm/request.ts` `prepare`, order matters, joined into one system string then split back into header + rest for cache stability):
- Provider-specific base prompt selected by model id substring in `session/system.ts` `provider()`: `anthropic.txt` 8.3 KB (~2.1k tok) for claude, `beast.txt` 11.2 KB for gpt-4/o1/o3, `gpt.txt` 9.4 KB, `codex.txt` 7.5 KB, `gpt-astra.txt` 4.1 KB for gpt-6, `gemini.txt` 15.5 KB (~3.9k), `kimi.txt` 8.8 KB, `meta.txt` 9.2 KB, `trinity.txt` 7.8 KB, `default.txt` 8.6 KB. Replaced entirely by `agent.prompt` if the agent defines one (explore/compaction/title/summary/custom agents), so the anthropic prompt is NOT used by subagents that carry their own prompt.
- Environment block (`session/system.ts` `environment`): model id, cwd, worktree, git yes/no, platform, date, plus `<available_references>` when configured. ~100-150 tok.
- Instruction files (`session/instruction.ts` `system()`): global `~/.config/opencode/AGENTS.md` OR `~/.claude/CLAUDE.md` (first found wins, CLAUDE.md gated by `OPENCODE_DISABLE_CLAUDE_CODE_PROMPT`); then project-level walk-up from cwd to worktree for `AGENTS.md` → `CLAUDE.md` → `CONTEXT.md` (first name that matches wins, all ancestor matches for that name included); then `config.instructions` globs and http(s) URLs (fetched, 5 s timeout). Each prefixed "Instructions from: <path>". Size is repo-dependent.
- MCP server `instructions` in `<mcp_instructions>` (`session/system.ts` `mcp`), filtered by permission.
- Skills list (`session/system.ts` `skills` → `Skill.fmt(list, {verbose:true})`): name + description of every discovered SKILL.md; the comment says verbose here, terse in the tool description, deliberately.
- `user.system` (per-message system override from the API) appended last.
- Tool schemas: 16 builtin descriptions total ~16 KB (~4k tok) plus JSON schemas; `task.txt` gets the subagent list appended (`tool/registry.ts` `describeTask`), `shell.txt` is templated per OS/shell/cwd (`tool/shell/prompt.ts`). Edit/Write are swapped for `apply_patch` on GPT-5+ models (`tool/registry.ts` `tools()`). MCP tools are added at the end of the map (`session/tools.ts`), sorted alphabetically (`request.ts`).
- Plan/build reminders (`session/reminders.ts`): `plan.txt` 1.5 KB appended to the last user message every loop step while agent=plan; `build-switch.txt` 238 B once after switching plan→build; under `OPENCODE_EXPERIMENTAL_PLAN_MODE`, `plan-mode.txt` 4.6 KB (~1.2k) is persisted as a part instead. `plan-reminder-anthropic.txt` exists but nothing imports it (grep found no references).
- Structured-output system line when `format.type === "json_schema"` (`session/prompt.ts`).
- Cache breakpoints: first 2 system messages and last 2 non-system messages get `cacheControl: ephemeral` (`provider/transform.ts` `applyCaching`).

On demand:
- Nested `AGENTS.md`/`CLAUDE.md` found while walking up from a file the model reads, injected into the read tool result as `<system-reminder>` once per assistant message (`session/instruction.ts` `resolve`, `tool/read.ts` ~L300, L355).
- Skill bodies via the `skill` tool (`tool/skill.ts`), which also lists up to 10 files in the skill dir.
- MCP resources via `list_mcp_resources`/`read_mcp_resource` tools (`session/tools.ts`), registered only when a connected server advertises resources.
- Tool outputs are capped at 2000 lines / 50 KB (`tool/truncate.ts`), overflow written to a temp file the model may read.
- `MAX_STEPS_PROMPT` (`packages/core/src/session/runner/max-steps.ts`) appended as an assistant message when `agent.steps` is hit.

## Tools (list with one line each)

Builtins registered in `tool/registry.ts` (order as in `builtin[]`):
- `invalid` (`tool/invalid.ts`): sink for malformed tool calls; `experimental_repairToolCall` in `session/llm.ts` rewrites bad calls to it so the model sees the error text.
- `question` (`tool/question.ts`): multi-choice questions to the user; only registered for app/cli/desktop clients or `OPENCODE_ENABLE_QUESTION_TOOL`; denied by default in `opencode run` (`cli/cmd/run.ts` `rules`).
- `bash` (`tool/shell.ts`, id via `ShellID.ToolID`): tree-sitter (bash + powershell wasm) parses the command, extracts every subcommand and path argument, asks `external_directory` for paths outside the worktree and `bash` permission with an "always" pattern built from `permission/arity.ts` prefix table (e.g. `git checkout *`); timeout, `shell.env` plugin hook.
- `read` (`tool/read.ts`): line-numbered read, 2000 lines / 50 KB / 2000-char lines, images and PDFs returned as attachments, `.env` files ask by default, injects nearby AGENTS.md.
- `glob` (`tool/glob.ts`), `grep` (`tool/grep.ts`): ripgrep-backed.
- `edit` (`tool/edit.ts`): exact-string replace with 9 fallback replacers (`SimpleReplacer`, `LineTrimmedReplacer`, `BlockAnchorReplacer`, `WhitespaceNormalizedReplacer`, `IndentationFlexibleReplacer`, `EscapeNormalizedReplacer`, `TrimmedBoundaryReplacer`, `ContextAwareReplacer`, `MultiOccurrenceReplacer`); requires prior read; runs configured formatter (`format/formatter.ts`, ~28 formatters) then LSP diagnostics and appends "LSP errors detected in this file, please fix" (L197-201).
- `write` (`tool/write.ts`): same permission/format/LSP flow, also reports errors in other files.
- `apply_patch` (`tool/apply_patch.ts`): Codex-style patch format, used instead of edit/write for gpt-5+.
- `task` (`tool/task.ts`): spawns a child session with a subagent; `task_id` resumes; `background=true` behind `OPENCODE_EXPERIMENTAL_BACKGROUND_SUBAGENTS`; `subagent_depth` default 1 (no nesting).
- `webfetch`, `websearch` (`tool/webfetch.ts`, `tool/websearch.ts`; websearch only for opencode-hosted providers or Exa/Parallel flags).
- `todowrite` (`tool/todo.ts`): stored in SQLite `TodoTable` per session (`session/todo.ts`); no `todoread` tool exists.
- `skill` (`tool/skill.ts`).
- `lsp` (`tool/lsp.ts`): goToDefinition/findReferences/hover/documentSymbol/workspaceSymbol/goToImplementation/call hierarchy; gated behind `OPENCODE_EXPERIMENTAL_LSP_TOOL`.
- `plan_exit` (`tool/plan.ts`): asks the user via question tool, then injects a synthetic build-agent user message; only under experimental plan mode + cli client.
- `execute` (`tool/code-mode.ts`): experimental "code mode" that exposes MCP tools as a JS catalog.
- Custom tools: `.opencode/tool(s)/*.{ts,js}` and plugin `tool` hooks, Zod args, `tool/registry.ts` `fromPlugin`.

## Agents, modes, subagents

`agent/agent.ts` defines seven natives: `build` (primary, default, all tools, `question`/`plan_enter` allowed), `plan` (primary, `edit` denied except `.opencode/plans/*.md` and the global plans dir, `task: general` denied), `general` (subagent, `todowrite` denied), `explore` (subagent, read-only tool allowlist, own prompt `agent/prompt/explore.txt`), and hidden `compaction`, `title`, `summary` with `*: deny`. Defaults: `*: allow`, `doom_loop: ask`, `external_directory: ask` (temp/skills/references whitelisted), `.env*` read: ask. "Modes" are legacy: `config/agent.ts` `loadMode` reads `.opencode/mode(s)/*.md` and coerces to `mode: "primary"`. Custom agents come from `config.agent` or `.opencode/agent(s)/**/*.md` with YAML frontmatter + body as prompt; options: model, variant, temperature, top_p, steps, permission, hidden, color, mode (`primary|subagent|all`). `Agent.generate` builds an agent config from a description with `agent/generate.txt`. Subagent sessions inherit only the parent's deny rules and `external_directory` rules (`agent/subagent-permissions.ts`), plus `todowrite`/`task` denies unless the subagent explicitly grants them. Slash commands (`command/index.ts`, `.opencode/command(s)/*.md`, `$1`/`$ARGUMENTS`, `!`shell`` and `@file` expansion in `session/prompt.ts` `command`) can target an agent; if that agent is a subagent the command becomes a `subtask` part.

## Plugin hook surface (exact names, arguments, capabilities)

Contract: `packages/plugin/src/index.ts` `Hooks`; dispatch `plugin/index.ts` `trigger` runs every plugin's hook sequentially with `(input, output)`, plugins mutate `output` in place. A plugin is `async ({client, project, directory, worktree, serverUrl, $, experimental_workspace}, options) => Hooks`, loaded from `config.plugin` (npm specs installed on demand, `plugin/loader.ts`) or auto-discovered `.opencode/plugin(s)/*.{ts,js}` (`config/plugin.ts`). Builtin auth plugins for Codex/Copilot/GitLab/Azure/etc. use the same surface.

| Hook | input | output (mutable) | Fired from |
|---|---|---|---|
| `config` | Config | – | `plugin/index.ts` after load |
| `event` | `{event}` (every bus event for this directory) | – | `plugin/index.ts` listener |
| `dispose` | – | – | scope finalizer |
| `tool` | – | map name→ToolDefinition (Zod args, `execute(args, ctx)` with `ctx.ask`) | `tool/registry.ts` |
| `auth`, `provider` | – | provider auth methods / model list | provider layer |
| `chat.message` | `{sessionID, agent?, model?, messageID?, variant?}` | `{message: UserMessage, parts: Part[]}` | `session/prompt.ts` `createUserMessage` |
| `chat.params` | `{sessionID, agent, model, provider, message}` | `{temperature, topP, topK, maxOutputTokens, options}` | `session/llm/request.ts` |
| `chat.headers` | same | `{headers}` | `session/llm/request.ts` |
| `permission.ask` | Permission request | `{status: "ask"\|"deny"\|"allow"}` | declared in types; the `Permission.ask` in `permission/index.ts` does NOT call it — grep found no trigger site in `packages/opencode/src` (inferred: dead or moved to core/v2 path) |
| `command.execute.before` | `{command, sessionID, arguments}` | `{parts}` | `session/prompt.ts` `command` |
| `tool.execute.before` | `{tool, sessionID, callID}` | `{args}` | `session/tools.ts` for builtin, MCP-resource and MCP tools; `session/prompt.ts` for subtasks |
| `tool.execute.after` | `{tool, sessionID, callID, args}` | `{title, output, metadata}` | same sites |
| `tool.definition` | `{toolID}` | `{description, parameters}` | `tool/registry.ts` `tools()` |
| `shell.env` | `{cwd, sessionID?, callID?}` | `{env}` | `tool/shell.ts`, `session/prompt.ts` `shellImpl` |
| `experimental.chat.messages.transform` | `{}` | `{messages: WithParts[]}` | `session/prompt.ts` before each LLM turn and `session/compaction.ts` |
| `experimental.chat.system.transform` | `{sessionID?, model}` | `{system: string[]}` | `session/llm/request.ts`, `agent/agent.ts` generate |
| `experimental.session.compacting` | `{sessionID}` | `{context: string[], prompt?}` | `session/compaction.ts` |
| `experimental.compaction.autocontinue` | `{sessionID, agent, model, provider, message, overflow}` | `{enabled}` | `session/compaction.ts` |
| `experimental.text.complete` | `{sessionID, messageID, partID}` | `{text}` | `session/processor.ts` text-end |
| `experimental.provider.small_model` | `{provider}` | `{model?}` | provider layer |

Capabilities for an adapter:
- Block a tool call: throw inside `tool.execute.before` (`Effect.promise` turns the rejection into a tool error the model sees; documented in `packages/web/src/content/docs/plugins.mdx` L246-256). Can also rewrite `output.args`.
- Inject text into a turn: `chat.message` (add parts to the user message), `experimental.chat.system.transform` (append/replace system strings), `experimental.chat.messages.transform` (edit full history, not persisted), `tool.execute.after` (rewrite tool output), `experimental.text.complete` (rewrite the assistant's final text).
- Block session end / force continuation: no hook. The loop exit condition in `session/prompt.ts` is purely finish-reason based; `experimental.compaction.autocontinue` can only suppress the post-compaction "continue" turn. A plugin could call `client.session.prompt` from an `event` handler on `session.status idle` (inferred workaround, not a hook).
- Observe everything: `event` receives the whole bus (message/part updates, permission asked/replied, session status, todo updates).

## Headless mode

`opencode run [message..]` (`cli/cmd/run.ts`): flags `--command`, `--continue/-c`, `--session/-s`, `--fork`, `--share`, `--model/-m provider/model`, `--agent`, `--format default|json`, `--file/-f`, `--title`, `--attach <url>` (+ `--username/--password`), `--dir`, `--port`, `--variant`, `--thinking`, `--auto` (alias hidden `--yolo`, `--dangerously-skip-permissions`), hidden `--mini/--interactive` split-footer mode. Stdin is appended to the message. Non-interactive sessions are created with `question`, `plan_enter`, `plan_exit` denied. Permissions: with `--auto` every `permission.asked` gets reply `once`; otherwise it is auto-rejected with a printed warning. `--format json` writes one JSON object per line: `{type: "tool_use"|"step_start"|"step_finish"|"text"|"reasoning"|"error", timestamp, sessionID, part|error}`. Exit code 1 on `session.error`. It exits when `session.status` becomes `idle`. Also `opencode serve` (HTTP server), `opencode acp` (Agent Client Protocol over stdio, `acp/*.ts`), and the SDK (`packages/sdk`) for programmatic use; `session.prompt` accepts `format: {type: "json_schema"}` producing a `StructuredOutput` forced tool call (`session/prompt.ts` `createStructuredOutputTool`).

## Task understanding and planning

No explicit planner. `anthropic.txt` and `default.txt` push TodoWrite ("VERY frequently"), Task-tool delegation for exploration, and parallel tool calls. Plan agent = same loop with edit denied and a `<system-reminder>` (`plan.txt`); experimental plan mode adds a 5-phase workflow (explore agents → design agents → review → write plan file → `plan_exit`) via `plan-mode.txt` and a plan file at `.opencode/plans/<slug>.md` (`session/session.ts` `plan()`). Todos live in SQLite per session and are not re-injected into the prompt (only the tool output carries them).

## Context selection and repository understanding (LSP)

No indexing, embeddings, or repo map. Context is what the model pulls via glob/grep/read, plus the `explore` subagent. LSP (`lsp/lsp.ts`, `lsp/server.ts`) auto-spawns ~30 servers by file extension (typescript, deno, vue, eslint, oxlint, biome, gopls, ruby-lsp, ty, pyright, elixir-ls, zls, csharp, razor, fsharp, sourcekit, rust-analyzer, clangd, svelte, astro, jdtls, kotlin, yaml, lua, intelephense, prisma, dart, ocaml, bash, terraform), downloading binaries unless `OPENCODE_DISABLE_LSP_DOWNLOAD`; `cfg.lsp: false` disables all. LSP is used (a) after edit/write to append error diagnostics (max 20 per file, errors only, `lsp/diagnostic.ts`), (b) to resolve `@file?start=N` symbol ranges, and (c) via the experimental `lsp` tool. Nearby AGENTS.md files are surfaced lazily on read.

## Memory across sessions

Sessions, messages, parts, todos, and share state are in SQLite `~/.local/share/opencode/opencode.db` (`packages/core/src/database/database.ts`; Drizzle; channel-suffixed for non-release builds). `--continue`/`--session`/`--fork` resume or fork (`session/session.ts` `fork`). Compaction summaries are persisted as assistant messages with `summary: true` and carried into the next compaction as `<prior-summary>` (`packages/core/src/session/compaction.ts` `buildPrompt`). No cross-session memory beyond AGENTS.md; `/init` command (`command/template/initialize.txt`) writes an AGENTS.md. Sharing (`share/share-next.ts`) pushes session/message/part/diff/model rows to opencode's hosted share API; `share: "auto"|"manual"|"disabled"`, `OPENCODE_DISABLE_SHARE`.

## Verification: what counts as done

Done = the model stops calling tools (`finish` not in `tool-calls|unknown`). Nothing checks tests or builds. Verification pressure is prompt-only: `default.txt` "you MUST run the lint and typecheck commands", `todowrite.txt` "Mark completed only after required verification". Hard signals: LSP error diagnostics injected after every edit/write, formatter run after edits, `edit` refusing to write without a prior read, doom-loop detection after 3 identical tool calls (`session/processor.ts` `DOOM_LOOP_THRESHOLD`), `agent.steps` cap with `MAX_STEPS_PROMPT`.

## Model routing (providers, per-agent models)

Provider catalog from models.dev (`provider/provider.ts`, `OPENCODE_MODELS_URL/PATH`), executed through ~20 `@ai-sdk/*` packages plus gitlab-ai-provider and opencode's own gateway. Per-agent `model` + `variant` (reasoning effort) in `agent/agent.ts`; `small_model` for title/summary via `provider.getSmallModel`; `compaction` agent may use its own model. Per-model prompt selection in `session/system.ts`, per-model option/temperature transforms in `provider/transform.ts`, tool-schema transforms per provider, `strict:false` for OpenAI Responses tools. `session/llm.ts` picks AI SDK vs native runtime per request.

## Failure recovery / checkpoints

Worktree snapshots: a separate git dir under `~/.local/share/opencode/snapshot/<project>/<hash>` tracks the real worktree (`snapshot/index.ts`, files > 2 MB skipped, pruned after 7 days); `step-start`/`step-finish` parts carry snapshot hashes and `patch` parts list changed files. `SessionRevert.revert` (`session/revert.ts`) restores files and truncates messages; `unrevert` restores. LLM retries with `retry-after` awareness (`session/retry.ts`). Aborted tool calls are marked `interrupted` and ignored by the loop-exit check (`session/prompt.ts` `isOrphanedInterruptedTool`). Context overflow → automatic compaction; overflow from oversized media replays the last user turn with media stripped (`session/compaction.ts` `replay`).

## Security posture (permissions)

Rule model: `{permission, pattern, action: allow|ask|deny}` list, last matching rule wins, default `ask` (`permission/index.ts` `evaluate`); merged agent ruleset + session ruleset + runtime "always" approvals. Config `permission` supports per-tool patterns (e.g. `bash: {"git *": "allow"}`), `OPENCODE_PERMISSION` env, managed config / macOS MDM profiles (`config/managed.ts`). Bash gets AST-level parsing with subcommand-prefix "always" patterns and path extraction for `external_directory`. Rejection with a message becomes `PermissionCorrectedError` fed back to the model; a plain reject also rejects all other pending asks in that session. Denials stop the loop unless `experimental.continue_loop_on_deny`. There is no sandbox; tools run as the user. `.env` reads ask by default. Remote config can be pulled from a well-known URL (`config/config.ts` L375-408).

## Host coupling

Runtime: Bun (`Bun.$`, `Bun.stdin`), Node fallback layers exist (`packages/effect-sqlite-node`). Requires git for snapshots (degrades if not a repo), ripgrep bundled, tree-sitter wasm for bash parsing, downloads LSP binaries. Server is a Hono app usable in-process (`Server.Default().app.fetch`) or over HTTP with basic auth. Plugins get an SDK client bound to the same server.

## Observability

Structured `Effect.logInfo/Error` throughout (`loop`, `stream`, `process`, `evaluated`, `asking`), `Tool.execute` spans with session/message/call ids, optional OpenTelemetry for AI SDK calls (`experimental.openTelemetry` in config, `session/llm.ts`), per-message token/cost accounting (`Session.getUsage`), a global event bus every client and plugin can subscribe to (`event-v2-bridge.ts`), `--format json` event stream.

## Trace: trivial task (border radius)

Default (`build`, Claude): system = `anthropic.txt` (~2.1k) + env (~120) + AGENTS.md (repo-dependent) + skills list + ~16 tool schemas (~5-6k with JSON) ≈ 8-9k tokens before the user message (inferred sum). `anthropic.txt` tells the model to use Task for open-ended search but Grep/Read for needle queries, and to use TodoWrite "VERY frequently" — a 3-step todo list is plausible overhead. Expected path: `grep` for the button class → `read` (may inject a nearby AGENTS.md as a system-reminder) → `edit` (permission `edit` is `allow` by default so no prompt; formatter runs; LSP diagnostics appended, likely none for CSS) → stop. 3-4 tool round-trips; snapshots taken at each step boundary via git in the side gitdir. Plan agent: same but `edit` denied → the model would produce a description and the user must switch to build; `plan.txt` (~400 tok) is re-appended each step. Overhead relative to the minimal answer is dominated by the fixed ~8k system+tools prefix (cached after the first call) and TodoWrite calls.

## Trace: hard task (auth race)

Build agent: the prompt pushes delegation to `explore` (read-only subagent with its own 900-byte prompt, no `anthropic.txt`) for "how does auth work"; each explore call is a fresh child session with the full tool set minus write tools, so the ~5k tool-schema prefix is paid again per subagent. The parent then reads files, may use `lsp` findReferences only if the experimental flag is set; otherwise grep. Edits go through `edit` with LSP error feedback (TypeScript/Go/Rust servers spawn automatically). Nothing forces a reproduction or a test run; `default.txt` asks for lint/typecheck but `anthropic.txt` does not. If the session grows past `context - max(20k, maxOutput)` tokens (`session/overflow.ts`), compaction runs: last ~25 % of usable context (2k-15k tokens) of recent turns kept verbatim, older turns serialized with tool outputs truncated to 2000 chars and summarized into the fixed Objective/Work State/Next Move template, then a synthetic "Continue if you have next steps" user turn. Plan mode (experimental) would run explore agents ×3, a `general` design agent, question tool, write `.opencode/plans/*.md`, then `plan_exit` — several extra full-context LLM calls. Doom-loop detection would catch a model retrying the same failing test command 3×.

## Strengths (ranked, concrete, cited)

1. Message-list-as-state-machine loop (`session/prompt.ts` `runLoop`): subtasks, compaction, and overflow are just parts on messages, so resume/fork/revert are trivial and the loop is restartable from the DB.
2. Permission system with AST-parsed bash and prefix-arity "always" patterns (`tool/shell.ts`, `permission/arity.ts`, `permission/index.ts`): fine-grained, composable, and the corrected-rejection feedback path returns user guidance to the model.
3. Provider-specific system prompts and transforms (`session/system.ts`, `provider/transform.ts`) plus a clean LLM adapter seam (`session/llm/AGENTS.md`).
4. Git-side-repo snapshots with per-step patches and revert (`snapshot/index.ts`, `session/revert.ts`) without touching the user's `.git`.
5. Compaction design (`session/compaction.ts`, `packages/core/src/session/compaction.ts`): keeps a recent-turn tail verbatim, chains prior summaries, prunes old tool outputs separately, and exposes both to plugins.
6. Plugin hooks sit on every seam that matters for an adapter (tool before/after, message, system, params, headers, compaction, events) with an in-process SDK client handed to the plugin.
7. Post-edit LSP diagnostics + formatter (`tool/edit.ts` L112, L197-201) as a cheap hard-signal verifier.

## Weaknesses (ranked, concrete, cited)

1. No verification gate: done = model stopped (`session/prompt.ts` loop exit); tests/builds are prompt suggestions only, and `anthropic.txt` dropped the lint/typecheck instruction that `default.txt` keeps.
2. No session-end hook or "must continue" control for plugins; `permission.ask` is typed in `packages/plugin/src/index.ts` but has no trigger site in `packages/opencode/src` (inferred stale contract).
3. Fixed prefix overhead: 8-15 KB provider prompt + full tool schemas on every call including subagents and the title/summary calls (title uses `system: []` but the compaction call still pays its own agent prompt).
4. Prompt sprawl: 10 provider prompts with divergent instructions (`session/prompt/*.txt`), an unused `plan-reminder-anthropic.txt`, and `anthropic.txt` containing a dangling "- " bullet under "Doing tasks".
5. Retrieval is grep/glob only; `lsp` tool, plan mode, background subagents, code mode, native runtime are all behind `OPENCODE_EXPERIMENTAL_*` flags (`effect/runtime-flags.ts`), so the shipped default is a plain ReAct loop.
6. Subagent depth defaults to 1 and subagents inherit only deny rules (`agent/subagent-permissions.ts`), so a permissive subagent definition widens what the parent could do.
7. Effect-TS everywhere: every service is a Layer with `InstanceState`; readable once learned but heavy for reuse outside the monorepo.

## Genuinely innovative vs mostly prompt engineering

Innovative: tree-sitter bash permission scanning with arity prefixes; the side-gitdir snapshot/patch/revert mechanism; compaction with verbatim tail + chained summary template + separate tool-output pruning; `experimental_repairToolCall` routing malformed calls to an `invalid` tool; nested AGENTS.md injected lazily on read. Mostly prompt engineering: the provider prompts (largely Claude Code-style text), TodoWrite pressure, plan mode phases, explore/general subagent split, doom-loop threshold.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Ten near-duplicate provider prompts selected by substring match on model id (`session/system.ts`); a new model name silently falls to `default.txt`.
- `plan.txt` re-appended in memory every step (`session/reminders.ts` non-experimental path) — small but repeated.
- Tool descriptions carry UI-specific text (ctrl+p, /help) into API/headless use.
- `permission.ask` hook declared but not wired; `plan-reminder-anthropic.txt` dead file.
- Auto-npm-install of `@opencode-ai/plugin` into every `.opencode` dir on config load (`config/config.ts` L452-470) and remote well-known config fetch are surprising side effects.
- LSP servers auto-download and spawn per file type; diagnostics are read after every edit, which can be slow on large TS projects (inferred).

## Reusable pieces (specific files or ideas, and the license terms for reuse)

MIT, attribution required. Directly liftable: `tool/edit.ts` replacer chain (L217-703); `permission/arity.ts` + `permission/index.ts` evaluate/merge/fromConfig; `tool/shell.ts` tree-sitter scan → permission patterns; `snapshot/index.ts` side-gitdir approach; `session/compaction.ts` + `packages/core/src/session/compaction.ts` `buildPrompt` template; `session/retry.ts` retry classification; `session/instruction.ts` walk-up + lazy nested instruction injection; `packages/plugin/src/index.ts` as a reference hook contract; `tool/truncate.ts` spill-to-file truncation; `lsp/diagnostic.ts` report format.

## Must not copy

Anything hosted: share API (`share/share-next.ts`), opencode gateway headers (`session/llm/request.ts` `x-opencode-*`), Go upsell strings in `session/retry.ts`. Provider prompts are MIT but read as derivatives of Claude Code's prompts (inferred); do not ship them verbatim. Auth plugins for Copilot/Codex reverse-engineer third-party OAuth flows — licensing of use is the third party's, not MIT.

## Transferable abstractions (name each, one line)

- Message parts as loop control: `subtask`/`compaction` parts drive the runner, not in-memory flags.
- Permission = (permission, pattern, action) ruleset with last-match-wins and runtime "always" grants.
- Command-arity table to turn shell commands into stable approval patterns.
- Side git repository for cheap worktree checkpoints and per-step patches.
- Tail-preserving compaction with a fixed summary schema and prior-summary chaining.
- Provider-keyed system prompt + per-provider parameter/schema transform layer.
- Lazy instruction injection: attach nearby AGENTS.md when a file under it is read, once per message.
- Hook pairs `(input, mutableOutput)` run sequentially across plugins for deterministic override order.
- Doom-loop detector on identical consecutive tool calls escalating to a permission ask.
- Truncate-to-file for tool output, with the file path whitelisted for later reads.

## Open questions that need a probe run to answer

- Actual token count of the assembled prefix for Claude with builtin tools and no AGENTS.md (estimate ~8-9k).
- Whether `permission.ask` fires anywhere (core v2 path?) or is dead in 1.18.30.
- How often compaction triggers on a 200k model in a realistic 1-hour session, and the quality of the chained summary.
- Latency cost of post-edit LSP diagnostics on a large TypeScript repo.
- Whether `--auto` in `opencode run` also auto-answers `doom_loop` asks (code suggests yes: all `permission.asked` get `once`).
- Behaviour when a plugin throws in `tool.execute.after` (inferred: tool errors after side effects already happened).
- Real-world cost of `explore` subagents paying the full tool-schema prefix per call.
