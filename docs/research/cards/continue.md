# continue

- Repo: https://github.com/continuedev/continue
- Commit: 5522c6f44ca0ac3528b37244818fbfa39b5af470 (2026-07-20T21:00:09-07:00, shallow clone)
- License: Apache-2.0 (`LICENSE`; also `extensions/cli/package.json` "license": "Apache-2.0")
- Primary language: TypeScript (1429 .ts + 345 .tsx of 3058 tracked files; 86 Kotlin for the JetBrains host)
- Files: 3058 tracked (`git ls-files | wc -l`)
- All paths below are relative to the repo root. "Read" = seen in source; "Inferred" = my deduction.

Continue is an IDE-first (VS Code, JetBrains) AI coding assistant with a shared TypeScript `core/`
that owns config loading, context providers, codebase indexing, tools and LLM adapters; a React
`gui/` that assembles the actual prompt each turn; and a separate headless/TUI CLI package
`extensions/cli/` (binary `cn`) that reimplements the agent loop with its own tools, permission
system, compaction, hooks and subagents. Retrieval (`@codebase`) is a hybrid of SQLite FTS5
trigram search, LanceDB embeddings, recently-edited files and an LLM-driven repo-map file
selection, optionally reranked. Configuration is `config.yaml` with hub "blocks", plus markdown
rules, `AGENTS.md`, and `.claude/skills`.

## Request flow (cite files)
1. GUI builds the message list: `gui/src/redux/util/constructMessages.ts` walks `ChatHistoryItem[]`, prepends context-item text to user messages, re-inserts `tool` messages from `toolCallStates`, computes the system message via `core/llm/rules/getSystemMessageWithRules.ts`, and appends any `conversationSummary` to the system message.
2. Base system message chosen per mode in `gui/src/redux/util/getBaseSystemMessage.ts` from `core/llm/defaultSystemMessages.ts` (chat / plan / agent; model may override with `baseAgentSystemMessage` etc.).
3. GUI calls `llm/compileChat` (`core/core.ts:589`) which runs `compileChatMessages` in `core/llm/countTokens.ts:426` to prune history; then `llm/streamChat` (`core/core.ts:563` -> `core/llm/streamChat.ts:llmStreamChat` -> `model.streamChat`).
4. Tool calls come back; `gui/src/redux/thunks/streamNormalInput.ts:318-400` evaluates policies via `tools/evaluatePolicy` (`core/core.ts:1051`), auto-runs `allowedWithoutPermission` calls and built-in readonly calls, pauses for `allowedWithPermission`. Execution is `tools/call` -> `core/tools/callTool.ts:callTool` (edit tools run client-side: `core/tools/builtIn.ts:CLIENT_TOOLS_IMPLS`).
5. Context providers (`@file`, `@codebase`...) are resolved before send via `context/getContextItems` (`core/core.ts:1373`), which passes `ContextProviderExtras` (config, llm, embeddingsProvider, reranker, fullInput, ide, selectedCode, isInAgentMode).
- CLI flow is separate: `extensions/cli/src/stream/streamChatResponse.ts:423` `while(true)` loop; system message from `extensions/cli/src/systemMessage.ts:constructSystemMessage`; tools from `extensions/cli/src/tools/allBuiltIns.ts`; permissions from `extensions/cli/src/permissions/`.

## What goes into the model (always-loaded vs on-demand, with token estimates)
Always-loaded (IDE agent mode), per turn:
- `DEFAULT_AGENT_SYSTEM_MESSAGE` (`core/llm/defaultSystemMessages.ts`): ~120 tokens (read; short). Chat mode message includes `EDIT_CODE_INSTRUCTIONS`, ~350 tokens (inferred from length).
- Rules that pass `shouldApplyRule` (`core/llm/rules/getSystemMessageWithRules.ts`): global rules (alwaysApply or root-level with no globs) every turn; glob/regex rules only when a matching file path appears in the last user/tool message or its context items. `AGENTS.md`/`AGENT.md`/`CLAUDE.md` at workspace root loaded as an always-apply rule (`core/config/markdown/loadMarkdownRules.ts:10-55`). Size unbounded.
- Tool schemas: base 9 tools (`core/tools/index.ts:getBaseToolDefinitions`) + request_rule, read_skill, search_web, grep_search, and multi_edit or (edit_existing_file + single_find_and_replace) depending on `isRecommendedAgentModel` (`core/llm/toolSupport.ts:490`). `multiEditTool` description alone is ~450 tokens (`core/tools/definitions/multiEdit.ts`). Inferred total ~2.5-4k tokens. `read_skill` description embeds every skill name+description (`core/tools/definitions/readSkill.ts`). Experimental tools (`view_repo_map`, `view_subdirectory`, `codebase`, `read_file_range`) only when `enableExperimentalTools`.
- Conversation summary if compaction was triggered (manual, see Memory).
On-demand:
- `@codebase`: up to `nFinal = min(25, contextLength/512/2)` snippets (`core/context/retrieval/retrieval.ts:39-43`), each chunk <=500 tokens (`core/llm/constants.ts:14`), so up to ~12.5k tokens, plus whole files returned by repo-map selection (5-10 files, unbounded; `core/context/retrieval/repoMapRequest.ts`).
- `read_file` refuses files over half the context window (`core/tools/implementations/readFileLimit.ts`).
- Pruning: `compileChatMessages` reserves `min(1000, 2% ctx)` safety buffer + `min(1000, maxTokens)` output, keeps system+tools+last tool sequence, drops oldest messages first (`core/llm/countTokens.ts:368-545`). Default pruning length 128k if context length unknown (`core/llm/constants.ts:4`).
CLI: base message with cwd, git repo flag, platform, date, and full `git status --porcelain` snapshot (`extensions/cli/src/systemMessage.ts:43-60`), plus AGENTS.md/AGENT.md/CLAUDE.md/CODEX.md, `--rule` values, config.yaml rules, `.continue/rules/*.md` and `~/.continue/rules/*.md` (always-apply only) in a `<context name="userRules">` block. Headless adds "Provide ONLY your final answer".

## Context provider abstraction (interface and built-in providers)
- Interface: `IContextProvider` / `BaseContextProvider` (`core/context/index.ts`): static `description: ContextProviderDescription` (title, displayTitle, type normal|submenu|query, `dependsOnIndexing?: ContextIndexingType[]`), `getContextItems(query, extras): Promise<ContextItem[]>`, `loadSubmenuItems(args)`. `ContextProviderExtras` at `core/index.d.ts:199`.
- Registry: `core/context/providers/index.ts` lists 30 providers: file, diff, tree (file tree), issue (GitHub), google, terminal, debugger locals, open files, http (custom server), search (ripgrep), os, problems, folder, docs, gitlab-mr, jira, postgres, database, codebase, code (single symbol), currentFile, url, repo-map, discord, greptile, web, mcp, commit, clipboard, rules.
- Defaults always present: file, currentFile, diff, terminal, problems, rules (`core/config/loadContextProviders.ts:33-40`); MCP provider added when servers expose resources; others via `context:` in config.yaml.
- `dependsOnIndexing` drives which indexes get built: `CodebaseContextProvider` declares `["embeddings","fullTextSearch","chunk"]` (`core/context/providers/CodebaseContextProvider.ts`); `CodebaseIndexer.getIndexesToBuild` unions these across configured providers (`core/indexing/CodebaseIndexer.ts:146-208`). No embed model configured => no indexes built at all (line 153).
- MCP: `MCPContextProvider` is a submenu provider over MCP resources/prompts (`core/context/providers/MCPContextProvider.ts`).

## Codebase indexing and retrieval pipeline (detailed)
Indexing (`core/indexing/README.md`, read): content-addressed by file hash ("cacheKey") with per-(directory,branch,artifactId) tags in SQLite so branch switches only add/remove tags, not recompute. `refreshIndex.ts` produces four lists (compute, del, addTag, removeTag) per `CodebaseIndex` implementation; `CodebaseIndexer.ts` batches 200 files at a time (`filesPerBatch`, line 54), pausable, abortable.
Indexes (`core/indexing/CodebaseIndexer.ts:174-192`):
- `ChunkCodebaseIndex` (`core/indexing/chunk/ChunkCodebaseIndex.ts`): `chunks` + `chunk_tags` SQLite tables. `shouldChunk` skips files >1M chars or without an extension (`chunk/chunk.ts:107`).
- Chunker (`core/indexing/chunk/chunk.ts`): tree-sitter `codeChunker` for supported languages except css/html/json/toml/yaml; else line-based `basicChunker`. `code.ts` yields a node whole if under `maxChunkSize`, otherwise emits a "collapsed" class/function form (bodies replaced by `{ ... }`) and recurses into children; methods in classes get the class header prepended. Max chunk 500 tokens (`core/llm/constants.ts:14`; `maxEmbeddingChunkSize` per model). Chunks over the limit are dropped, not split (`chunk.ts:64-70`).
- `FullTextSearchCodebaseIndex` (`core/indexing/FullTextSearchCodebaseIndex.ts`): SQLite FTS5 virtual table with `tokenize='trigram'`, ranked by `bm25(fts, 10.0)` (path column weight 10), filtered by `rank <= -2.5` (`core/util/parameters.ts:RETRIEVAL_PARAMS.bm25Threshold`).
- `LanceDbIndex` (`core/indexing/LanceDbIndex.ts`): one LanceDB table per tag (`tableNameForTag`, line 84), vectors from `embeddingsProvider.embed` in batches (`maxEmbeddingBatchSize`, default 64), metadata cached in SQLite `lance_db_cache`. Retrieval embeds only the first chunk of the query (line 439-457), searches each tag table, sorts by `_distance`. Directory filter uses `path LIKE 'dir%'` with limit 300 then slices (line 420-425).
- `CodeSnippetsCodebaseIndex` (`core/indexing/CodeSnippetsIndex.ts`): tree-sitter tag queries (`core/tag-qry/`) -> `code_snippets` table with title/signature; feeds the repo map.
- Default embedder: `TransformersJsEmbeddingsProvider` auto-added in VS Code (`core/config/yaml/loadYaml.ts:345-354`). Storage: `~/.continue/index/index.sqlite`, `~/.continue/index/lancedb` (`core/util/paths.ts:326-332`).
- Ignore: `.gitignore`, `.continueignore`, plus hard-coded security ignores for env files, keys, certs, db files, config.json/yaml, `.aws/` etc. (`core/indexing/ignore.ts:8-80`).
Retrieval (`core/context/retrieval/retrieval.ts` -> `pipelines/`):
- `nFinal = min(25, ctx/512/2)`, `nRetrieve = 2*nFinal` if reranker present (`retrieval.ts:39-43`).
- `BaseRetrievalPipeline.ts`: FTS query = stem, stopword-remove, dedupe tokens with wink-nlp, then trigram n-grams joined with OR (`getCleanedTrigrams`); embeddings query; recently-edited files (`openedFilesLruCache` + open tabs) re-chunked live; repo-map request.
- `repoMapRequest.ts`: builds a repo map (file list only, `includeSignatures:false`), asks the LLM to pick 5-10 files with `<reasoning>`/`<results>` tags, reads whole files. Only for model titles matching claude-3, llama3.1/3.2, gemini-2.5, gpt-4 (`SUPPORTED_MODEL_TITLE_FAMILIES`, line 8) or a configured `repoMapFileSelection` role. Repo map capped at 50% of context (`core/util/generateRepoMap.ts:29`).
- `NoRerankerRetrievalPipeline.ts`: 1/4 recently-edited, 1/4 FTS, 1/2 embeddings, plus repo-map chunks; dedupe by (path,start,end).
- `RerankerRetrievalPipeline.ts`: gathers nRetrieve from each source, calls `rerank.rerank(query, chunks)`, sorts, slices nFinal. Threshold filtering is commented out (line 108-114); embedding expansion and second rerank are commented out (line 157-165).
- Experimental `codebaseToolCallingOnly`: one LLM call picks among glob/grep/ls/read/repo-map tools and executes them (`BaseRetrievalPipeline.ts:retrieveWithTools`).
- Output: an instruction item plus one item per chunk, sorted by path, rendered as fenced code with relative path (`retrieval.ts:100-135`). In agent mode with no results, returns "No results were found. Try using other tools."

## Tools
IDE core (`core/tools/builtIn.ts`, definitions in `core/tools/definitions/`, impls in `core/tools/implementations/`): read_file, read_file_range, edit_existing_file (lazy-diff "changes" applied client side), single_find_and_replace, multi_edit (atomic old/new list), read_currently_open_file, create_new_file, run_terminal_command (2 min timeout, `waitForCompletion:false` for background; `runTerminalCommand.ts:7`), grep_search (ripgrep, not on remote), file_glob_search, search_web, view_diff, ls, create_rule_block, request_rule (agent-requested rules, default disabled), fetch_url_content, codebase, read_skill, view_repo_map, view_subdirectory. `Tool` interface (`core/index.d.ts:1132`) carries `readonly`, `defaultToolPolicy`, `systemMessageDescription` for non-native-tool models (`core/tools/systemMessageTools/buildToolsSystemMessage.ts`), `preprocessArgs`, `evaluateToolCallPolicy`. HTTP and MCP tools dispatched by `uri` (`core/tools/callTool.ts:callToolFromUri`).
CLI (`extensions/cli/src/tools/allBuiltIns.ts`): AskQuestion, Edit, Exit, Fetch, List, MultiEdit, Read, ReportFailure, Bash, Search (ripgrep/grep/findstr, `searchCode.ts`), Status, Subagent, Skills, UploadArtifact, Diff, Checklist, Write. No embeddings-based search in the CLI; `FileIndexService.ts` is an fzf file-name index for the TUI `@` picker.

## Headless CLI
- Binary `cn` (`extensions/cli/package.json` "bin"). `cn [prompt]` interactive TUI by default; `-p/--print` headless, `--format json`, `--silent`, `--resume`, `--fork <id>` (`extensions/cli/src/index.ts:183-195`). Stdin piped in as `<stdin>...</stdin>` (line 263-272).
- Shared flags (`extensions/cli/src/shared-options.ts`): `--config <path|hub slug>`, `--org`, `--readonly` (plan), `--auto`, `--rule` (file/slug/string, repeatable), `--mcp <slug>`, `--model <slug>`, `--prompt`, `--allow/--ask/--exclude <tool>`, `--agent <slug>`.
- Subcommands: `ls` sessions, hidden `serve [prompt] --port` (Express HTTP agent server, `commands/serve.ts`), `checks`, `review --base --fix --review-agents` (runs agents in git worktrees and captures diffs, `commands/review/reviewWorker.ts`).
- Permissions: first-match policy list; headless default allows Bash and `*` (MCP) without asking (`extensions/cli/src/permissions/defaultPolicies.ts:29-35`); TUI asks. Plan mode excludes Edit/MultiEdit/Write but allows Bash (line 46-52, TODO acknowledged).
- Output in headless mode is the final assistant text only (`streamChatResponse.ts:590`).

## Task understanding and planning
- No planner. IDE "plan mode" is a system message plus read-only tool filtering (`core/llm/defaultSystemMessages.ts:DEFAULT_PLAN_SYSTEM_MESSAGE`). CLI has a `Checklist` tool for markdown `- [ ]` lists the model maintains (`extensions/cli/src/tools/writeChecklist.ts`). Inferred: task decomposition is entirely model-driven.

## Memory across sessions
- IDE sessions persisted as JSON under `~/.continue/sessions/` (`core/util/paths.ts:78-107`; `core/util/history.ts`). CLI sessions under `~/.continue/sessions/` too with `--resume`/`--fork` (`extensions/cli/src/session.ts`).
- Compaction: IDE is manual (button in `gui/src/components/mainInput/ContextStatus.tsx:69` -> `core/util/conversationCompaction.ts`), stores `conversationSummary` on a history item and `constructMessages` drops everything before it. CLI auto-compacts when input tokens >= `ctx - maxTokens - min(max(maxTokens, 0.2*(ctx-maxTokens)), 15000)` (`extensions/cli/src/compaction.ts:266-298`), then auto-injects a user message "continue" (`streamChatResponse.ts:95-115`).
- No cross-session learned memory. Rules can be written by the agent via `create_rule_block` (persisted to `.continue/rules`). Inferred: that is the only agent-writable durable memory.

## Verification: what counts as done
- IDE: loop ends when the model returns no tool calls (`streamNormalInput.ts:333` `setInactive`). No test-running, lint, or diff-check step.
- CLI: same; `Exit` tool (exit code 1) and `ReportFailure` exist for headless failure signalling (`extensions/cli/src/tools/exit.ts`). Hooks (`extensions/cli/src/hooks/types.ts`) allow user-supplied PreToolUse/PostToolUse/Stop/TaskCompleted commands, matching Claude Code hook schemas verbatim (comment at line 1-6).

## Multi-agent / roles
- CLI only: `Subagent` tool dispatches to models in config.yaml with `roles: [subagent]` and a `chatOptions.baseSystemMessage` (`extensions/cli/src/services/ModelService.ts:309-317`; `subagent/get-agents.ts`). `cn review --review-agents` runs several agents in isolated worktrees. IDE has none.

## Model routing
- `selectedModelByRole` with roles chat, edit, apply, embed, rerank, autocomplete, summarize, plus experimental `repoMapFileSelection` (`core/config/util.ts:getModelByRole`, `repoMapRequest.ts:44`). Tool set varies by model: `isRecommendedAgentModel` regex list (`core/llm/toolSupport.ts:490-512`) selects multi_edit vs lazy edit tool; models without native tools get a system-message tool protocol (`core/tools/systemMessageTools/`).

## Failure recovery / checkpoints
- Tool errors are returned to the model as error context items rather than thrown (`core/tools/callTool.ts:callTool` catch). Canceled tool calls get a placeholder message (`core/tools/constants.ts`). MCP connections have a 20s timeout (`core/context/mcp/MCPConnection.ts:36`). Indexing marks per-file completion so interrupted indexing resumes (`core/indexing/README.md` step 5). No file-level checkpoints or undo beyond the IDE's own edit-diff accept/reject (GUI, not studied).

## Security posture
- Tool policies: `allowedWithPermission | allowedWithoutPermission | disabled` (`packages/terminal-security/src/types.ts`). Per-call escalation: files outside the workspace always require permission (`core/tools/policies/fileAccess.ts`); terminal commands parsed with shell-quote and checked for privilege escalation, sensitive paths, chaining (`packages/terminal-security/src/evaluateTerminalCommandSecurity.ts`).
- Indexing skips secret-like files by pattern (`core/indexing/ignore.ts`). CLI headless mode auto-allows Bash and all MCP tools by default (`defaultPolicies.ts:31-32`), so `-p` without `--ask Bash` is fully autonomous.

## Host coupling
- `core/` depends on an `IDE` interface (`core/index.d.ts`) for file IO, workspace dirs, branch, open files, terminal; implemented by VS Code and JetBrains. Prompt assembly lives in the GUI (`gui/src/redux/util/constructMessages.ts`), so the IDE agent cannot be driven without the webview. The CLI does not reuse this loop; it has its own (`extensions/cli/src/stream/`).

## Observability
- Dev-data event logging with versioned schemas: autocomplete, chatInteraction, chatFeedback, editInteraction, editOutcome, tokensGenerated, toolUsage, quickEdit, nextEdit (`packages/config-yaml/src/schemas/data/`, writer `core/data/log.ts`), written to `~/.continue/dev_data`. CLI logs to `~/.continue/logs/cn.log` (`extensions/cli/package.json` watch:logs). Context-usage percentage surfaced to the GUI (`streamNormalInput.ts:190-194`).

## Trace: trivial task (border radius)
Read: user types "change the Save button's border radius to 8px" in agent mode with no `@` provider. System message = agent message + global rules (~200-400 tokens) + tool schemas (~3k). No retrieval happens automatically; only the default providers exist and none is auto-attached. The model must call `grep_search` (auto-approved, readonly) for "Save" or a class name, then `read_file`, then `multi_edit` (pauses for permission unless the user set it to auto). Three model calls minimum. If the user adds `@codebase`, retrieval runs FTS trigram on the stemmed query, embeddings, recently edited files, and (for claude-3/gpt-4-titled models) a repo-map LLM call listing every file path (up to 50% of context) to pick 5-10 files, which are then inserted whole. Inferred overhead: the repo-map call alone can cost tens of thousands of tokens on a mid-size repo for a one-line CSS change, and `.css` files are chunked line-wise (`chunk.ts:NON_CODE_EXTENSIONS`), so the CSS match relies on FTS.

## Trace: hard task (auth race)
Read: "fix an intermittent auth race condition" with `@codebase`. FTS trigrams over "intermitt auth race condit" (stemmed) will match files containing those literal substrings; embeddings retrieve semantically similar chunks (<=500 tokens each, class bodies collapsed to `{ ... }` so method bodies are separate chunks); repo-map selection returns whole files whose names suggest auth. With a reranker: 50 candidates -> 25 kept, no score threshold. Without: 6 recent, 6 FTS, 13 embedding chunks. The agent then reads/greps further via tools. Nothing in the system runs tests, reproduces the race, or verifies a fix; "done" is the model stopping. Inferred: chunk-level retrieval fragments control flow across async boundaries, and the pipeline has no call-graph expansion (expansion code is commented out in `RerankerRetrievalPipeline.ts`), so cross-file race reasoning depends on the model's own tool use.

## Strengths (ranked, concrete, cited)
1. Content-addressed, branch-tagged incremental indexing with resumable progress (`core/indexing/README.md`, `core/indexing/refreshIndex.ts`) — cheap branch switches, no re-embedding of unchanged files.
2. Tree-sitter "collapsed" chunker that emits class skeletons plus full children (`core/indexing/chunk/code.ts`) — chunks stay under budget while keeping structure.
3. Clean context-provider plugin surface with declarative index dependencies (`core/context/index.ts`, `dependsOnIndexing`), 30 providers, MCP resources as a provider.
4. Rule applicability engine: globs, negative globs, content regex, directory-colocated `rules.md`, agent-requestable rules (`core/llm/rules/getSystemMessageWithRules.ts`, `core/config/markdown/loadCodebaseRules.ts`).
5. Per-call policy escalation (workspace boundary, shell parsing) rather than static allowlists (`core/tools/policies/fileAccess.ts`, `packages/terminal-security/`).
6. CLI auto-compaction with explicit threshold formula and auto-continue (`extensions/cli/src/compaction.ts`), Claude-Code-compatible hooks (`extensions/cli/src/hooks/types.ts`).

## Weaknesses (ranked, concrete, cited)
1. Two divergent agent loops (GUI Redux thunks vs CLI `streamChatResponse.ts`) with different tool sets and prompts; `core/` is not an agent runtime.
2. `@codebase` repo-map selection dumps the whole file list (up to 50% of context) into an extra LLM call and returns whole files, gated by fragile model-title substring matching (`repoMapRequest.ts:8-14`).
3. Reranker threshold and expansion disabled by comments (`RerankerRetrievalPipeline.ts:108-114,157-165`); FTS ignores branch tags in its own table (`core/indexing/README.md` "Known problems").
4. Oversized chunks are dropped, not split (`chunk.ts:64-70`), so long functions vanish from the vector index.
5. No verification: no test/lint step, done = no tool calls (`streamNormalInput.ts`).
6. Headless CLI auto-allows Bash and all MCP tools (`defaultPolicies.ts:31-32`); plan mode still allows Bash (line 46-49).
7. IDE compaction is manual only (`ContextStatus.tsx:69`).

## Genuinely innovative vs mostly prompt engineering
- Innovative: tag-based content-addressed multi-artifact indexing; collapsed-AST chunking; rule matching by content regex and directory colocation; system-message tool protocol for models without native tool calling (`core/tools/systemMessageTools/`).
- Prompt engineering: mode system messages, lazy-diff edit format (`EDIT_CODE_INSTRUCTIONS`), repo-map file selection, tool-based retrieval (`retrieveWithTools`), CLI headless/JSON instructions.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior
- Repo-map file selection call per `@codebase` query (`repoMapRequest.ts`), whole-file injection, 5-10 files unbounded.
- `read_skill` and `request_rule` inline every skill/rule description into tool schemas each turn (`readSkill.ts`, `requestRule.ts`).
- LanceDB directory filter does `LIKE` post-filter with limit 300 (`LanceDbIndex.ts:420-425`) — recall collapses in large dirs.
- `retrieveWithTools` parses raw JSON from an unconstrained chat completion (`BaseRetrievalPipeline.ts`).
- `isSupportedModel` / `isRecommendedAgentModel` regex-on-name gating (`repoMapRequest.ts`, `toolSupport.ts`).
- `retrieval.ts` ignores `options.nFinal` default from docs (docs say 5, code says 25).

## Reusable pieces (specific files or ideas, and the license terms for reuse)
Apache-2.0: reuse permitted with attribution and NOTICE preservation; patent grant included.
- `core/indexing/refreshIndex.ts` + `CodebaseIndexer.ts` + `README.md`: the tag/cacheKey incremental index framework.
- `core/indexing/chunk/code.ts`: collapsed tree-sitter chunker (depends on `web-tree-sitter` and the `.wasm` grammars under `core/vendor`).
- `core/indexing/FullTextSearchCodebaseIndex.ts`: FTS5 trigram + bm25 with path weighting.
- `core/llm/rules/getSystemMessageWithRules.ts`: rule applicability logic.
- `core/llm/countTokens.ts:compileChatMessages`: history pruning that keeps tool sequences intact.
- `packages/terminal-security/`: shell command policy evaluator (standalone npm package).
- `extensions/cli/src/compaction.ts`: threshold formula and summary prompt.
- `core/indexing/ignore.ts`: security ignore list.

## Must not copy
- Model-name regex gating (`toolSupport.ts:490`, `repoMapRequest.ts:8`).
- Headless default of Bash + `*` allow (`defaultPolicies.ts:29-35`).
- Commented-out but shipped retrieval stages (`RerankerRetrievalPipeline.ts`).
- Duplicated agent loops across GUI and CLI.
- Trademarks/branding ("Continue", hub slugs, commit signature text in `systemMessage.ts:227-232`).

## Transferable abstractions (name each, one line)
- ContextProvider with `dependsOnIndexing`: retrieval plugins declare which indexes they need; the indexer builds the union.
- CodebaseIndex artifact with tag/cacheKey: any derived artifact (embeddings, FTS, symbols) shares one incremental refresh loop.
- Collapsed-AST chunk: emit a structural skeleton plus full children so both overview and detail are retrievable.
- Hybrid retrieval quota: fixed fractions per source (recent/FTS/embeddings) when no reranker.
- Rule applicability predicate: globs + content regex + directory colocation + policy override, evaluated on last message's file paths.
- Per-call policy escalation: `evaluateToolCallPolicy(basePolicy, args)` tightens permission based on arguments.
- Tool sequence-preserving pruning: never orphan a tool result when trimming history.
- Compaction threshold = ctx - maxOut - min(max(maxOut, 20% of remaining), cap).
- Model-role registry: chat/edit/apply/embed/rerank/summarize/subagent roles resolved from one config.

## Open questions that need a probe run to answer
- Actual token cost of a `@codebase` query on a 5k-file repo with repo-map selection enabled (map size vs 50% cap).
- Quality of FTS trigram queries built from stemmed tokens (stemmed forms may not appear verbatim in code).
- How often `chunkDocument` drops over-limit chunks in real TypeScript/Python repos.
- Whether `isRecommendedAgentModel` misclassifies current Claude/GPT model ids and silently degrades to the lazy-edit tool.
- Rerank latency and hit rate with the default Transformers.js embedder versus a hosted embedder.
- CLI auto-compaction fidelity across long tool-heavy sessions (summary loses file paths?).
- Effect of `LIKE`-based directory filter on `@folder`-scoped retrieval recall.
