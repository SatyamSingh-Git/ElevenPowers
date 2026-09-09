# Host card: Codex CLI (openai/codex)

Clone: `scratchpad/repos/codex` (paths below are relative to the clone root unless absolute). "Read" = seen in source or in-repo docs; "Docs" = official page at learn.chatgpt.com (developers.openai.com redirects there); "Inferred" = my conclusion from the read material. The hosts were not run.

## Identity

- Commit: `b4d42052cd0fe621cec83dd35582676904ce958c`, 2026-09-09T05:39:52Z (`git log -1`). Commit title: "Publish Python packages after stable CLI releases (#44067)".
- License: Apache-2.0 (`LICENSE`; `codex-cli/package.json` `"license": "Apache-2.0"`).
- Language: Rust (workspace in `codex-rs/Cargo.toml`, toolchain 1.95.0 in `codex-rs/rust-toolchain.toml`). `codex-cli/` is a thin npm launcher (`bin/codex.js`) for the `@openai/codex` package.
- In-repo `docs/*.md` are one-line stubs pointing at the official docs (e.g. `docs/exec.md`, `docs/config.md`), so source is the primary reference here.

## Instruction files

- Discovery (Read, `codex-rs/core/src/agents_md.rs` module doc, lines 1-16): find project root by walking up from cwd to the first `project_root_markers` hit (default `.git`); collect `AGENTS.md` from project root down to cwd inclusive; concatenate in that order; never walk above root.
- Per directory it prefers `AGENTS.override.md`, then `AGENTS.md`, then `project_doc_fallback_filenames` (Read: constants at `agents_md.rs:40-42`, fallback config at `codex-rs/config/src/config_toml.rs:309-314`). Docs (agents-md page): "at most one file per directory".
- Global file: `$CODEX_HOME/AGENTS.override.md` then `$CODEX_HOME/AGENTS.md` (Read, `codex-rs/codex-home/src/instructions/mod.rs:9-24`). Global and project docs are joined with `\n\n--- project-doc ---\n\n` (`agents_md.rs:46`).
- Size cap: `project_doc_max_bytes`, default 32 KiB (`codex-rs/core/src/config/mod.rs:234` comment `// 32 KiB`; `agents_md.rs:65` decrements a `remaining` budget). Docs: discovery stops once the combined content reaches the cap.
- Injected as a `# AGENTS.md instructions` block wrapped in `<INSTRUCTIONS>` (Read, `codex-rs/core/src/context/user_instructions.rs:24`). Loaded once per session (Docs: "once per run"); world-state updates can replace it (`core/src/context/world_state/agents_md.rs:10`).
- Also: `instructions`, `developer_instructions`, `model_instructions_file`, `compact_prompt` keys in `config.toml` (`config_toml.rs:231-256`).

## Hooks and lifecycle events

Present. A full Claude-Code-style hook engine lives in `codex-rs/hooks/` (the engine struct is literally `ClaudeHooksEngine`, `hooks/src/events/stop.rs:128`).

- Events (Read, `codex-rs/config/src/hook_config.rs:36-61`): `PreToolUse`, `PermissionRequest`, `PostToolUse`, `PreCompact`, `PostCompact`, `SessionStart`, `SessionEnd`, `UserPromptSubmit`, `SubagentStart`, `SubagentStop`, `Stop`, `Interrupt`. JSON schemas per event under `codex-rs/hooks/schema/generated/*.schema.json`.
- Config location (Read, `hooks/src/engine/discovery.rs:94-190` and `:339-343`): for each config layer, `<layer folder>/hooks.json` and/or a `[hooks]` table in that layer's `config.toml`. Docs: `~/.codex/hooks.json` or `[hooks]` in `~/.codex/config.toml`; `<repo>/.codex/hooks.json` or `[hooks]` in `<repo>/.codex/config.toml`; plugin `hooks/hooks.json`. Managed hooks come from `requirements.toml` (`ManagedHooksRequirementsToml`, `hook_config.rs:210`); `allow_managed_hooks_only = true` disables user/project hooks (`docs/config.md`).
- Handler types (Read, `hook_config.rs:158-200`): `command` (with `timeout`, `async`, `commandWindows`, `additionalContextLimit`), `mcp_tool` (server + tool + input), `prompt` and `agent` (placeholders, empty structs). Matcher groups: `{ matcher, hooks[] }`; `*` matches all (`discovery.rs` test `pre_tool_use_treats_star_matcher_as_match_all`).
- Feature flag: `features.hooks`, stage Stable, `default_enabled: true` (Read, `codex-rs/features/src/lib.rs:1167-1171`).
- Trust: non-managed hooks must be trusted by hash before they run; state lives in `[hooks.state]` with `enabled` / `trusted_hash` (`hook_config.rs:28-33`, `hooks/src/config_rules.rs`). `--dangerously-bypass-hook-trust` skips this (`codex-rs/utils/cli/src/shared_options.rs:63`).
- BLOCK a tool call: yes. PreToolUse output `decision: "block"` or `hookSpecificOutput.permissionDecision: allow|deny|ask`, plus `updatedInput` to rewrite args; exit code 2 with stderr reason also blocks (`hooks/schema/generated/pre-tool-use.command.output.schema.json`; `hooks/src/events/pre_tool_use.rs:193-275`). Core applies it in `codex-rs/core/src/hook_runtime.rs:184-245` (`run_pre_tool_use_hooks`).
- INJECT text: yes. `hookSpecificOutput.additionalContext` on `SessionStart`, `UserPromptSubmit`, `PreToolUse`, `PostToolUse`; recorded into the turn via `record_additional_contexts` and `inject_hook_context_if_running` (`hook_runtime.rs:169, 217, 763-781`). Plain stdout of a UserPromptSubmit command hook is also treated as context (`user_prompt_submit.rs:218`).
- BLOCK completion: yes. `Stop` (and `SubagentStop`) output `decision: "block"` + `reason` sets `should_block` (`hooks/src/events/stop.rs:100-115, 250-315`); dispatched from `run_turn_stop_hooks` (`hook_runtime.rs:376-430`). Docs: Stop "can force additional processing loops". `continue: false` + `stopReason` halts instead.
- Universal output fields: `continue`, `stopReason`, `suppressOutput`, `systemMessage`, `decision`, `reason` (all generated schemas).
- Legacy `notify = [...]` command still fires on `agent-turn-complete` (`hooks/src/legacy_notify.rs`; `config_toml.rs:228`).

## MCP

- Config: `[mcp_servers.<id>]` in `config.toml` (`config_toml.rs:277`). Fields (Read, `codex-rs/config/src/mcp_types.rs:197-260`): transport (`command`/`args`/`env` stdio or `url` HTTP, `McpServerTransportConfig` at `:533`), `enabled`, `required`, `startup_timeout_sec`, `tool_timeout_sec`, `default_tools_approval_mode`, `enabled_tools`, `disabled_tools`, `oauth`, `scopes`. Also `codex mcp add|list` edit helpers (`config/src/mcp_edit.rs`).
- Tool restriction: yes, `enabled_tools` allowlist then `disabled_tools` denylist (`mcp_types.rs:247-251`). Managed requirements can constrain servers (`config/src/mcp_requirements.rs`).
- Resources: supported. `list_resources`, `list_resource_templates`, `read_resource` in `codex-rs/rmcp-client/src/rmcp_client.rs:735-785`; model-facing tools in `core/src/tools/handlers/mcp_resource/`.
- Prompts: no evidence. No `list_prompts`/`prompts/get` call in `rmcp-client/src/rmcp_client.rs` or `codex-mcp/src` (grep). Inferred: MCP prompts are not surfaced.
- MCP servers can also be hook handlers (`mcp_tool` type above) and elicitation is handled (`core/src/elicitation.rs`).

## Extensions and commands

- Skills: `SKILL.md` directories. Roots (Read, `codex-rs/ext/skills/src/host_roots.rs:24-25, 80-120`): project `.codex/skills` (repo scope), `$CODEX_HOME/skills` (deprecated user), `~/.agents/skills` (user), system cache, admin `/etc/codex/skills`, plus repo `.agents/skills` walking up from cwd (`repo_agents_skill_roots`). Skills are listed in the prompt with name/description and read on demand (`ext/skills/src/catalog_prompt.rs:3-38`). Docs: `$skill` mention invokes explicitly; list capped at ~2% of context.
- Plugins: `.codex-plugin/plugin.json` manifest, bundling `skills/`, `hooks/hooks.json`, `.mcp.json`, `agents/` (Docs; Read: `codex-rs/core-plugins/src/loader.rs:1214`, `store.rs:525`). Marketplaces from `.agents/plugins/marketplace.json` (`loader.rs:475`); `[plugins]` / `[marketplaces]` tables in `config.toml` (`config_toml.rs:471-475`).
- Custom prompts / slash commands: Docs say `~/.codex/prompts`; I found no dedicated loader in `core/src` by name (grep for `custom_prompts` empty), so treat the exact file format as an open question. `docs/slash_commands.md` is a stub.
- Execution policy: `*.rules` files under each config layer's `rules/` dir, default `default.rules` (`codex-rs/core/src/exec_policy.rs:54-56, 665`); `--ignore-rules` skips them.

## Subagents

- Present and on by default: `features.multi_agent` (Docs "stable; on by default"; `Feature::MultiAgentV2` in `features/src/lib.rs:1265`).
- Tools exposed to the model (Read, `codex-rs/core/src/tools/handlers/multi_agents_spec.rs`): `spawn_agent`, `send_input`/`send_message`, `followup_task`, `resume_agent`, `wait_agent`, `list_agents`, `close_agent`, `interrupt_agent`.
- Per-subagent model: yes. `spawn_agent` takes `agent_type`, `model`, `reasoning_effort` (`multi_agents_spec.rs:581-661`), gated by `expose_spawn_agent_model_overrides` (`core/src/config/mod.rs:1293`). Roles are TOML files in `~/.codex/agents/` or `.codex/agents/` requiring `name`, `description`, `developer_instructions` and accepting `model`, `model_reasoning_effort` (Docs; Read: `codex-rs/agent-roles/src/agent_role_config.rs:10-31, 130-147`; `[agents.<name>].config_file` at `core/src/config/mod.rs:901`).
- Limits: `agents.max_concurrent_threads_per_session` / `agent_max_threads`, `agent_max_depth` (`core/src/config/mod.rs:886-898, 3800-3813`). Hooks `SubagentStart`/`SubagentStop` fire for child threads.

## Headless mode

- Command: `codex exec [OPTIONS] [PROMPT]`; prompt from arg, `-`, or piped stdin (Read, `codex-rs/exec/src/cli.rs:11-80`). Subcommands: `exec resume <id|--last> [PROMPT]`, `exec fork <id>`, `exec review --uncommitted|--base|--commit`.
- Output: `--json` emits JSONL events `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.started|updated|completed`, `error` (`exec/src/exec_events.rs:11-37`). Items: `agent_message`, `reasoning`, `command_execution`, `file_change`, `mcp_tool_call`, `collab_tool_call`, `web_search`, `todo_list`, `error` (`:107-132`). So tool calls are reported.
- Token usage: `turn.completed.usage` has `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`, `reasoning_output_tokens` (`exec_events.rs:50-72`).
- Other flags: `-o/--output-last-message FILE`, `--output-schema FILE` (JSON Schema for final answer), `--ephemeral` (no rollout on disk), `--ignore-user-config`, `--ignore-rules`, `--skip-git-repo-check`, `--color`, `--strict-config` (`exec/src/cli.rs`). Shared: `-m/--model`, `-p/--profile` (layers `$CODEX_HOME/<name>.config.toml`), `-s/--sandbox`, `--approve-for-me`, `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`), `-C/--cd`, `--add-dir`, `--worktree`, `--oss`/`--local-provider`, `-c key=value` overrides and `--enable/--disable <feature>` (`utils/cli/src/shared_options.rs`; `cli/src/main.rs:1043-1047`).
- Approval policy in exec: no `-a` flag on exec (only on the TUI, `tui/src/cli.rs:65`); set via `-c approval_policy=never` or config (Inferred from flag lists). `--full-auto` is deprecated per Docs.
- Max turns / budget: none found. No `max_turns`-style option in `exec/src` or `core/src/config/mod.rs` (grep). Only `model_auto_compact_token_limit` and `tool_output_token_limit` exist.
- Exit codes: not documented in-repo; open question.

## Sandbox and approvals

- `sandbox_mode`: `read-only` (default), `workspace-write`, `danger-full-access` (`codex-rs/protocol/src/config_types.rs:104-114`). `SandboxPolicy` adds `network_access` and `sandbox_workspace_write.writable_roots` etc. (`protocol/src/protocol.rs:1074+`; `config_toml.rs:215`).
- `approval_policy`: `untrusted` (ask unless a rule allows), `on-request` (default, alias `on-failure`), `granular { sandbox_approval, rules, skill_approval, request_permissions, mcp_elicitations }`, `never` (`protocol/src/protocol.rs:988-1020`).
- Backends (Read, `codex-rs/sandboxing/src/`): macOS Seatbelt (`seatbelt.rs`, `.sbpl` profiles), Linux Landlock + bubblewrap (`landlock.rs`, `bwrap.rs`), Windows (`windows.rs`, `windows_mxc.rs`, `codex-rs/windows-sandbox-rs`). Network restricted by default (`NetworkAccess::Restricted`, `protocol.rs`).
- Destructive commands: with `on-request` the model requests escalation; `PreToolUse`/`PermissionRequest` hooks and `.rules` execpolicy can pre-decide (`core/src/exec_policy.rs`). `--dangerously-bypass-approvals-and-sandbox` removes both.

## Context management and memory

- Startup context: base model prompt (`codex-rs/core/gpt_5_2_prompt.md`, `gpt-5.2-codex_prompt.md`, etc.; selection by model, Inferred), AGENTS.md chain, skills catalog, permissions/collab instructions (`include_permissions_instructions`, `include_collaboration_mode_instructions`, `include_environment_context` in `config_toml.rs:238-247`), tool specs from `core/src/tools/registry.rs`.
- Compaction: inline auto-compact using `SUMMARIZATION_PROMPT` (`core/src/compact.rs:62, 120-131`), configurable `compact_prompt`, `model_auto_compact_token_limit` (+`_scope`), `model_context_window` (`config_toml.rs:165-172, 256`). Remote compaction variants exist (`compact_remote*.rs`). Hooks `PreCompact`/`PostCompact` fire.
- Memory across sessions: `features.memories` (off by default per Docs); `[memories]` table with `version`, `generate_memories`, `use_memories`, `dedicated_tools` (`config/src/types.rs:294-309`); context fragments in `core/src/context/memory.rs`.
- No repository index. `file-search` crate is on-demand fuzzy search, not an embedding index (Inferred from crate list).

## Telemetry

- Session rollouts: `$CODEX_HOME/sessions/rollout-<timestamp>-<thread_id>.jsonl` (optionally `.jsonl.zst`), `archived_sessions/` (`codex-rs/rollout/src/lib.rs:83-84`, `rollout_file_name.rs:67`, `recorder.rs:82`). Persisted items include `TokenUsageRecord`, `TurnContext`, `Compacted`, `SessionMeta` and `EventMsg::TokenCount` (`rollout/src/policy.rs:10-24, 113-119`), so per-turn token usage is on disk.
- Command history: `~/.codex/history.jsonl`, `history.persistence = save-all|none`, `max_bytes` (`codex-rs/message-history/src/lib.rs:3, 52`; `config/src/types.rs:197-209`).
- SQLite state DB with metrics (`codex-rs/state/src/lib.rs:130-146`); `sqlite_home`, `log_dir` config keys (`config_toml.rs:348-353`). TUI log `log/codex-tui.log` (`tui/src/lib.rs:261`).
- OpenTelemetry: `[otel]` with `exporter`, `trace_exporter`, `metrics_exporter` (`none|otlp-http|otlp-grpc`), `log_user_prompt` default false (`config/src/types.rs:562-634`; crate `codex-rs/otel`).

## Model selection

- `model`, `model_provider` (default `openai`), `model_providers.<id>` table with `wire_api = "responses"` only (chat wire API removed, `codex-rs/model-provider-info/src/lib.rs:61`), `model_reasoning_effort`, `model_verbosity`, `review_model`, profiles (`config_toml.rs:157-162, 306, 336-340, 371-375`).
- Built-in providers: `openai`, `ollama`, `lmstudio` (`model-provider-info/src/lib.rs:42, 566-596`); Bedrock auth helper in `model-provider/src/amazon_bedrock`. `--oss` / `--local-provider` CLI switches.
- No hard-coded default model constant found; the models-manager resolves it from a catalog (`models-manager/src/manager.rs`; `model_catalog_json` override in `config_toml.rs:379`).

## Adapter assessment

- Inject text at turn boundary: PRESENT. `UserPromptSubmit` / `SessionStart` command hook returning `hookSpecificOutput.additionalContext` (or raw stdout for UserPromptSubmit); `PostToolUse` also carries `additionalContext`.
- Intercept tool calls: PRESENT. `PreToolUse` with `permissionDecision: deny|ask|allow`, `decision: block`, `updatedInput`; `PostToolUse` sees results; `PermissionRequest` hook can pre-answer approvals.
- Block completion: PRESENT. `Stop` hook `decision: "block"` + `reason` re-engages the agent; `continue: false` hard-stops.
- Degraded adapter (if hooks are disabled by `allow_managed_hooks_only` or trust is unavailable): drive `codex exec --json`, prepend context to the prompt, enforce policy with `.rules` execpolicy + `approval_policy=untrusted`, and detect completion by consuming `turn.completed` then re-invoking `codex exec resume --last` with follow-up text. Loses in-turn tool interception and in-turn completion blocking.

## Open questions

- Exact JSON shape of `hookSpecificOutput` for `PostToolUse` and `PermissionRequest` was not read (only file names seen); confirm from `hooks/schema/generated/*.output.schema.json` before coding.
- Whether hooks fire identically under `codex exec` vs the TUI (Inferred yes since the engine is in `core`).
- Location and format of custom prompt files (`~/.codex/prompts` per Docs; no loader found in `core/src`).
- Exit codes of `codex exec` and how `turn.failed` maps to process status.
- Whether `Stop` block re-runs with the reason as a user message or as developer context (`hook_runtime.rs:376-430` not fully read).
