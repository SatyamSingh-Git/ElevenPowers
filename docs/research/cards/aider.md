# aider

- Repo: https://github.com/Aider-AI/aider (short name: aider)
- Commit: 5dc9490bb35f9729ef2c95d00a19ccd30c26339c, dated 2026-05-22T07:02:20-07:00 (shallow clone, HEAD of default branch)
- License: Apache-2.0 (`LICENSE.txt`)
- Primary language: Python (147 `.py` files of 691 tracked files; 58 tree-sitter `.scm` query files; the rest is website/markdown/media)
- Studied from source in `aider/` and `benchmark/`; website and `aider/gui.py` skipped. Nothing was executed.

Aider is a terminal pair-programming chat loop, not an autonomous agent. Each user message is sent once to one LLM together with a fixed system prompt, a PageRank-ranked "repo map" of symbol signatures, the full text of files the user explicitly added to the chat, and (optionally summarized) chat history. The model replies in an edit format (default SEARCH/REPLACE blocks) that aider parses and applies to disk, then auto-commits with an LLM-written message, lints the edited files, and re-prompts the model with lint/test errors up to three times. There is no tool-calling loop, no planner, and no autonomous file reading: the model can only ask the user to add files, which aider detects by filename matching in the reply and turns into a y/n prompt. Everything described below was read from source unless marked "inferred".

## Request flow (cite files)

1. `aider/main.py:451-1180` parses args, builds `Model` (`aider/models.py:329-369`), `GitRepo`, `InputOutput`, then `Coder.create(...)` at `main.py:973-1007`. `map_tokens` defaults to `main_model.get_repo_map_tokens()` = `max_input_tokens/8` clamped to [1024, 4096] (`main.py:964-967`, `models.py:782-789`).
2. `Coder.run()` (`aider/coders/base_coder.py:876-892`) loops on `io.get_input()`; `run_one()` (`base_coder.py:924-944`) calls `preproc_user_input` (slash commands, file-mention prompts, URL scraping; `base_coder.py:912-922`) and then `send_message()` repeatedly while `self.reflected_message` is set, capped at `max_reflections = 3` (`base_coder.py:101, 939-944`).
3. `send_message()` (`base_coder.py:1419-1623`): appends the user turn to `cur_messages`, builds the prompt via `format_messages()` (`base_coder.py:1333-1338`), checks total tokens against `max_input_tokens` (`base_coder.py:1396-1417`), streams the completion via litellm (`send()` at `base_coder.py:1783-1834`, `models.py:985-1037`), then in order: file-mention detection in the reply → reflect (`1560-1567`); `apply_updates()` (`1585`); `auto_commit()` (`1589`); auto-lint → reflect on errors after a confirm (`1599-1607`); run model-suggested shell commands after a confirm (`1609-1614`); auto-test → reflect on failures (`1616-1623`).
4. Edit parsing/applying is per-format subclass: `EditBlockCoder.get_edits/apply_edits` (`aider/coders/editblock_coder.py:21-124`), `UnifiedDiffCoder` (`udiff_coder.py:46-120`), `PatchCoder` (`patch_coder.py:210+`), `WholeFileCoder`. Format is chosen per model from `aider/resources/model-settings.yml` (357 entries) via `ModelSettings.edit_format` (`models.py:128-158`).
5. Retry: exponential backoff on retryable litellm exceptions (`base_coder.py:1461-1488`); on `FinishReasonLength` it continues the reply with assistant prefill if the model supports it (`1492-1505`).

## What goes into the model (always-loaded vs on-demand, with token estimates)

Message order is fixed by `ChatChunks.all_messages()` (`aider/coders/chat_chunks.py:16-26`): `system + examples + readonly_files + repo + done + chat_files + cur + reminder`. Built in `format_chat_chunks()` (`base_coder.py:1226-1331`).

Always loaded:
- System prompt: `main_system` + `system_reminder` for the edit format (`editblock_prompts.py:8-30, 120-159`), with `{final_reminders}` (lazy/overeager nudges, `base_prompts.py:12-20`), platform block (OS, shell, date, lint/test commands; `base_coder.py:1127-1172`), and shell-command instructions (`aider/coders/shell.py`). The whole `editblock_prompts.py` is ~820 words; with `shell.py` text and the reminder repeated as a trailing system/user message (`base_coder.py:1285-1329`) the fixed overhead is roughly 1.5-2k tokens (inferred from word counts; not measured).
- Two few-shot example exchanges (`editblock_prompts.py:31-118`) followed by a synthetic "I switched to a new code base" pair (`base_coder.py:1249-1259`), or inlined into the system prompt for models with `examples_as_sys_msg` (`1233-1240`).
- Repo map as a user/assistant pair (`base_coder.py:750-761`): budget 1024-4096 tokens by default (`models.py:782-789`), inflated by `map_mul_no_files` (CLI default 2, `args.py:262-267`) when no files are in chat (`repomap.py:122-132`).
- Chat files: full contents of every `/add`ed file, prefixed by `files_content_prefix` (`base_prompts.py:24-28`, `base_coder.py:789-806`). Aider warns once when 4+ files exceed 20k tokens (`base_coder.py:2244-2267`) but never trims.
- Read-only files (`/read-only`, `--read`): full contents (`base_coder.py:763-787`).
- Done messages: prior turns, summarized when over `max_chat_history_tokens` = `max_input_tokens/16` clamped to [1024, 8192] (`models.py:355-358`, `history.py:15-18`).

On demand / conditional: image/PDF attachments when the model supports vision (`base_coder.py:817-857`); scraped URL text appended to the user message after a confirm (`base_coder.py:964-984`); `/run` or `/test` output (`commands.py:1013-1053`); the `AI!` comment context from `--watch-files` (`aider/watch.py:181-255`). Prompt-caching markers are set on system/examples, repo map, and chat files (`chat_chunks.py:28-41`), and a background thread pings the cache every ~5 minutes when `--cache-keepalive-pings` is set (`base_coder.py:1340-1394`).

## Repository map algorithm (detailed)

Entry: `Coder.get_repo_map()` (`base_coder.py:709-748`) → `RepoMap.get_repo_map()` (`aider/repomap.py:103-167`).

Inputs. `chat_files` = added files plus read-only files that are inside the repo; `other_files` = all git-tracked files minus chat files (`base_coder.py:719-722`; tracked list from `GitRepo.get_tracked_files`, `aider/repo.py:433-488`, filtered by `.aiderignore`). `mentioned_fnames` = filenames found in the current user turn(s) via `get_file_mentions` (`base_coder.py:1714-1759`, exact rel-path match or unique basename containing `.`/`_`/`-`/`/`) plus files whose stem (>=5 chars, lowercased) equals any word in the message (`base_coder.py:684-707`). `mentioned_idents` = every `\W+`-split word of the current turn text (`base_coder.py:678-682`); no stemming, no stop-word filter.

Extraction (`repomap.py:279-363`). For each file: `filename_to_lang` picks a tree-sitter grammar (via `grep_ast`), the matching `aider/queries/tree-sitter-language-pack/<lang>-tags.scm` (32 languages; 28 more under `tree-sitter-languages/`) is run as a query, and captures named `name.definition.*` become `Tag(kind="def")`, `name.reference.*` become `Tag(kind="ref")`, each with the 0-based line (`repomap.py:318-336`). Example: `python-tags.scm` captures class/function/constant definitions and call references. If a grammar yields defs but no refs (C++ queries do this), Pygments lexer `Token.Name` tokens are used as refs with `line=-1` (`repomap.py:338-363`).

Cache (`repomap.py:177-264`). Tags are cached in a `diskcache.Cache` at `<root>/.aider.tags.cache.v3` (or `.v4` with the language pack), keyed by absolute path and validated by mtime; SQLite errors fall back to an in-memory dict. Files never change the graph unless their mtime changes. The initial scan shows a tqdm bar when >100 files are uncached (`repomap.py:391-398`).

Graph construction (`repomap.py:365-514`). A `networkx.MultiDiGraph` whose nodes are relative filenames. For every identifier defined in >=1 file and referenced in >=1 file, an edge `referencer -> definer` is added per (referencer, definer) pair with weight `mul * sqrt(num_refs_in_referencer)` and attribute `ident`. `mul` starts at 1.0 and is scaled: ×10 if the ident is in `mentioned_idents`; ×10 if it is snake/kebab/camelCase with length >= 8; ×0.1 if it starts with `_`; ×0.1 if defined in more than 5 files; and ×50 more if the referencer is a chat file (`repomap.py:487-514`). Definitions with zero references get a 0.1-weight self-edge so they still appear (`475-479`). If there are no references at all, defines are reused as references (`465-466`).

Ranking (`repomap.py:519-574`). Personalized PageRank (`nx.pagerank(G, weight="weight", personalization=..., dangling=...)`) where each chat file, each mentioned file, and each file whose path component/basename matches a mentioned ident receives `100/len(all_files)` (chat + mentioned-fname are max'd, not summed; a path-ident match adds another increment; `repomap.py:381-445`). If no personalization, plain weighted PageRank. Each node's rank is then redistributed across its out-edges proportional to edge weight, accumulating into `ranked_definitions[(definer_file, ident)]` (`533-545`). These are sorted descending; definitions inside chat files are skipped (they are already in full); remaining files with no ranked tags are appended as bare filename entries in PageRank order, then any leftover files (`547-572`). Special root files (README, package.json, pyproject.toml, etc. from `aider/special.py:ROOT_IMPORTANT_FILES`) are prepended as filename-only entries (`repomap.py:656-662`).

Budget (`repomap.py:666-706`). A binary search over the prefix length of the ranked tag list: start at `max_map_tokens // 25` tags, render, count tokens (sampled estimate for texts >200 chars, `repomap.py:89-101`), accept the largest render at or under budget, stop early when within 15% of target. Rendering (`to_tree`, `748-784`) groups tags by file and uses `grep_ast.TreeContext` to print only the lines of interest plus their enclosing scope headers (`render_tree`, `710-746`); each output line is truncated to 100 chars. Chat files are excluded from rendering.

Refresh strategy (`repomap.py:576-627`). The rendered map is memoized in-process keyed by (chat files, other files, budget) and, in `auto` mode, also by mentioned files/idents. Modes: `always` recompute; `files` reuse when the file sets match; `manual` reuse `last_map` until `/map-refresh`; `auto` (default) reuse only if the last build took >1s. Note that in `files`/`manual` modes edits to a file do not invalidate the memo even though the tag cache sees the new mtime (read; consequence inferred). `get_repo_map` retries without chat files, then without hints, if the map is empty (`base_coder.py:732-746`), and disables the map for the session on `RecursionError` (`repomap.py:143-146`). `ContextCoder` forces `always` and multiplies the budget (`context_coder.py:11-19`).

## Task understanding and planning

None beyond the prompt. The edit-format system prompt instructs the model to "think step-by-step and explain the needed changes in a few short sentences" before emitting blocks and to ask for files it needs (`editblock_prompts.py:15-25`). There is no task decomposition, no todo list, and no structured plan object; `/architect` (`architect_prompts.py:7-16`) asks a model to "describe how to modify the code" in prose and hands that prose verbatim to an editor model (`architect_coder.py:23-48`). `/context` (`context_coder.py`) is a single-purpose "which files need editing" call that iterates up to `max_reflections-1` times by re-adding the files the model named (`context_coder.py:21-50`). `/ask` is read-only Q&A (`ask_prompts.py`).

## Context selection

Manual first: the user `/add`s files, `--read`s references, or lets `--watch-files` add any file containing an `AI` comment (`watch.py:181-200`). Automatic: (a) filename mentions in the user's message or the model's reply trigger a y/n "Add file to the chat?" prompt (`base_coder.py:1761-1781`), and a "yes" re-sends the same request with the file included (reflection, `1560-1567`); (b) the repo map is biased by mentioned filenames and identifiers as described above; (c) an edit to a file not in chat prompts "Allow edits to file that has not been added to the chat?" (`base_coder.py:2226-2231`). Aider never reads a file on its own initiative and never greps.

## Memory across sessions

- `.aider.chat.history.md` in the git root: every user input and assistant reply is appended as markdown (`io.py:775-795, 1117-1136`). With `--restore-chat-history` it is parsed back into `done_messages` and summarized at startup (`base_coder.py:519-523`, `args.py:289-294`, default off).
- `.aider.input.history`: prompt_toolkit input history (`io.py:736-752`).
- `.aider.tags.cache.v*/`: the tree-sitter tag cache (`repomap.py:43, 217-222`).
- `.aider.llm.history` when `--llm-history-file` is set: raw prompts and responses (`io.py:754-765`).
- No project notes, no learned preferences, no vector store. `.aider.conf.yml` and `.aiderignore` are static config (`args.py:422-431`).

## Verification: what counts as done

Done is "the reply parsed and applied, and no lint/test errors were reported that the user asked to fix". After each successful edit: `auto_commit` (`base_coder.py:2375-2395`), then `lint_edited` (`1681-1696`). The default linter is aider's own (`aider/linter.py`): tree-sitter parse errors (`basic_lint`, `linter.py:192-222`), `compile()` for Python (`168-189`), and `flake8 --select=E9,F821,F823,F831,F406,F407,F701,F702,F704,F706` (`127-159`) — fatal errors only, formatted with `TreeContext` and marked lines (`225-247`). User lint commands via `--lint-cmd lang: cmd` (`main.py:278-303`). Lint failures become the next user message after confirm (`base_coder.py:1603-1607`). Tests run only with `--auto-test` (default off, `args.py:553-558`) or `/test`, and only the output on non-zero exit is fed back (`commands.py:993-1053`). The whole fix loop is bounded by `max_reflections = 3`. No reproduction, no assertion of behavior, no diff review by a second model.

## Multi-agent / roles (architect/editor)

Two roles, sequential, same process. `ArchitectCoder.reply_completed` (`architect_coder.py:10-48`) takes the architect reply, optionally confirms "Edit the files?", then creates an editor `Coder` with `main_model.editor_model` and `editor_edit_format`, `map_tokens=0`, no shell suggestions, no cache, empty history, and runs it with the architect text as the user message (`preproc=False`). The editor's commit hashes and cost are copied back and the architect's history gets an "I made those changes to the files." pair (`architect_coder.py:39-48`). Editor model and format come from `models.py:625-645` (defaults to the main model with `editor-diff`/`editor-whole` prompts that strip the "ask questions" language: `editor_editblock_prompts.py`). `/lint` uses a cloned coder with empty history per file (`commands.py:396-406`). No parallelism, no critic/reviewer role.

## Model routing

Three slots: main, weak, editor (`models.py:339-369`). The weak model writes commit messages (`models.py:622-623`, `repo.py:326-373`) and chat summaries (`base_coder.py:510-513`, `history.py:109-121` tries weak then main). Everything else goes to the main model. Per-model settings (edit format, `use_repo_map`, `lazy`, `overeager`, `reminder` placement, `examples_as_sys_msg`, cache control, reasoning tags) are static YAML (`aider/resources/model-settings.yml`) plus heuristics in `configure_model_settings` (`models.py:385-598`). Temperature defaults to 0 unless the model disables it (`models.py:997-1004`). No dynamic routing by task difficulty.

## Failure recovery / checkpoints (git behavior)

- Dirty-commit before editing a file with uncommitted user changes so `/undo` has a base (`base_coder.py:2175-2189, 2411-2423`; `--dirty-commits` default on).
- After edits, `GitRepo.commit(fnames=edited, aider_edits=True)` stages only edited files and commits with an LLM message generated from the chat context plus diff (`repo.py:131-318`, prompt `aider/prompts.py:8-22`); attribution defaults to author/committer name suffixed "(aider)" or a `Co-authored-by:` trailer depending on flags (`repo.py:242-267`). `--git-commit-verify` defaults to False (`args.py:491-496`), so aider commits with `--no-verify` and skips pre-commit hooks unless the user opts in (`repo.py:278-279`).
- `/undo` (`commands.py:560-655`) only reverts a HEAD commit whose hash aider made this session, refuses if pushed to `origin/<branch>`, restores files with `git checkout HEAD~1 -- file` and `git reset --soft HEAD~1`.
- Malformed edit blocks raise `ValueError` whose message (with "did you mean" nearby lines, `editblock_coder.py:84-124, 602-628`) becomes the reflected message (`base_coder.py:2305-2316`). Successful blocks in the same reply are still applied.
- `--dry-run` disables writes and commits (`base_coder.py:2331, 2376`).

## Security posture

- Shell commands suggested by the model in ```bash blocks (`editblock_coder.py:452-485`) run only after an explicit-yes confirm and via `subprocess.Popen(shell=True)` / pexpect with the repo root as cwd (`base_coder.py:2450-2485`, `aider/run_cmd.py:11-73`). `--yes-always` answers "n" to `explicit_yes_required` prompts, so it does not auto-run shell commands (`io.py:866-867`), but does auto-approve file creation, edits to files outside the chat, and URL fetches.
- No sandbox, no path allowlist beyond gitignore/aiderignore checks in `allowed_to_edit` (`base_coder.py:2191-2240`).
- URL detection in user input offers to scrape with Playwright/httpx and inject the page text (`base_coder.py:964-984`, `aider/scrape.py`).
- Analytics: PostHog opt-in asked of a random 10% of installs (`analytics.py:15, 119-135`), model names redacted if not in the litellm DB (`195-204`).
- API keys from env/.env (`main.py:361-389`).

## Host coupling

CLI/terminal only (prompt_toolkit + rich). Git is optional but most behavior assumes it (`--no-git`). Litellm for all providers (`models.py:1036`). tree-sitter grammars via `grep_ast`/`tree-sitter-language-pack`. No IDE protocol; `--watch-files` (`watch.py`) is the IDE-integration substitute. A Streamlit GUI exists (`gui.py`, not studied).

## Observability

Per-message token and cost report (`base_coder.py:1994-2126`), `/tokens` breakdown by system/history/map/files (`commands.py:445-551`), `/map` prints the map (`commands.py:1418-1424`), `--verbose` dumps full messages (`base_coder.py:1435-1436`), `--llm-history-file` logs raw prompts (`io.py:754-765`), `--show-prompts` prints the assembled prompt and exits (`main.py:1044-1051`). Each request's kwargs are SHA1-hashed for benchmark reproducibility (`models.py:1015-1019`). No tracing spans, no per-turn structured log.

## Trace: trivial task (border radius)

User types "change the submit button border radius to 8px" with no files added. `preproc_user_input` finds no filenames (`base_coder.py:1714-1759`). Repo map: idents {change, the, submit, button, border, radius, to, 8px} get ×10 on any matching symbol, so a `SubmitButton`/`button.css` symbol ranks up if it exists; the map budget is doubled because no chat files (`repomap.py:131-132`). The model, following `files_no_full_files_with_repo_map` (`base_prompts.py:34-38`), must reply with the file path and stop. Aider detects that filename in the reply, asks "Add file to the chat?" (`base_coder.py:1770-1776`), and re-sends the original request with the file included (reflection 1 of 3). Second reply emits one SEARCH/REPLACE block; `apply_edits` matches exactly or with whitespace tolerance (`editblock_coder.py:134-187`), writes the file, a weak-model commit message is generated (one extra LLM call, `repo.py:326-373`), lint runs (CSS has no linter unless configured; `linter.py:44-72` returns None for unknown languages), done. Overhead: 2 main-model calls with ~2k tokens of fixed prompt plus map each, 1 weak-model call, one map build (cached tags after first run). Not done: no screenshot, no check the selector is right, no search for other buttons.

## Trace: hard task (auth race)

User types "fix the intermittent race in auth token refresh". Same start: no plan, no reproduction. Idents {intermittent, race, auth, token, refresh} bias the map; a symbol like `refresh_token` (snake_case, >=8 chars) gets ×100 combined and its definer file surfaces. The model can only guess which files matter from signature lines; it asks for files, user approves, one more reflection. The model then must produce the fix in a single reply from static reading, with no ability to run tests, add logging, or read callers not in chat (it can ask for more files, costing another reflection each; after 3 aider stops with "Only 3 reflections allowed", `base_coder.py:939-941`). If `--auto-test` were configured, a failing test suite would be fed back, but an intermittent race would likely pass, so aider reports success. Auto-commit lands whatever was written. Overhead is the same fixed prompt; the missing capability is the whole investigation loop. This is read from `run_one`/`send_message`; the outcome is inferred.

## Strengths (ranked, concrete, cited)

1. The repo map: static, language-agnostic, sub-second after warm cache, and steered by chat files and by the words in the current request (`repomap.py:365-574`). It gives a large repo a usable "table of contents" in 1-4k tokens without letting the model read files.
2. Edit-format engineering and robust application: whitespace-tolerant and `...`-tolerant SEARCH/REPLACE matching (`editblock_coder.py:134-240`), cross-file fallback (`41-65`), and reflective error messages that show the nearest actual lines (`84-124, 602-628`); formats are chosen per model from a 357-entry table.
3. Cheap, well-bounded loop: one call per turn, at most 3 reflections, auto-commit per edit with `/undo` (`commands.py:560-655`), dirty-commit safety, and an honest lint gate that only reports fatal errors (`linter.py:127-159`).
4. Prompt cache discipline: chunk ordering is fixed so the stable prefix (system, examples, map, files) is cacheable, with keep-alive pings (`chat_chunks.py`, `base_coder.py:1340-1394`).
5. A reproducible benchmark harness (`benchmark/benchmark.py:679-978`): per-exercise Docker runs, request hashes, replay mode, counts of malformed responses, lazy comments, syntax errors.

## Weaknesses (ranked, concrete, cited)

1. No investigation loop: the model cannot read, grep, or run anything; every extra file costs a human confirm and a full re-send (`base_coder.py:1560-1567`), capped at 3 (`939-941`). Hard tasks degrade to "guess from signatures".
2. Ident mentions are raw words with no filtering: "the", "to", "fix" all get ×10 if they happen to be identifiers (`base_coder.py:678-682`, `repomap.py:492-493`); mention-driven personalization is not applied in `files`/`manual` refresh modes (`repomap.py:592-596`).
3. The repo map is defs-only signatures; no docstrings, no types beyond what tree-sitter's header line shows, and lines truncated at 100 chars (`repomap.py:782`). Pygments fallback refs have `line=-1` and are never rendered.
4. Chat files are always sent in full; there is no partial-file or chunk selection, only a one-time warning (`base_coder.py:2244-2267`).
5. History summarization is lossy, prompt-based, and blocks on a thread join at prompt-build time (`base_coder.py:1278`, `history.py:27-123`).
6. Fuzzy edit-distance matching exists but is dead code behind a bare `return` (`editblock_coder.py:183-187`), so near-miss blocks always bounce back to the model.
7. Commit message generation is an unconditional extra LLM call on every edit (`repo.py:326-373`).

## Genuinely innovative vs mostly prompt engineering

Innovative: the tree-sitter-tags → file-graph → personalized PageRank → token-budgeted binary search pipeline (`repomap.py`), and the empirical mapping of model → edit format with a benchmark that measures malformed-response rates. Mostly prompt engineering: the SEARCH/REPLACE system prompts and few-shot examples, the "add files to the chat" protocol, architect/editor split (two prompts, one handoff), `lazy`/`overeager` reminders, and the AI-comment watcher prompts (`watch_prompts.py`).

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Seven edit formats plus function-calling variants (`aider/coders/*_coder.py`) with mostly duplicated prompt classes; `patch_coder.py` alone is 706 lines.
- The tag graph is rebuilt from cached tags for every map request with new hints; `auto` mode only memoizes once a build exceeds 1s (`repomap.py:609`), so mid-size repos recompute PageRank every turn.
- PageRank over a `MultiDiGraph` with an edge per (referencer, definer, ident) grows with references × definers; ident defined in >5 files is only down-weighted, not pruned (`repomap.py:498-499`). `RecursionError` disables the map entirely (`143-146`).
- The system reminder is sent twice (in the system prompt and again as a trailing message, `base_coder.py:1261-1262, 1285-1329`).
- `check_added_files` warns once and never again (`base_coder.py:2242-2267`).
- Windows-specific hacks: `powershell -Command` wrapping (`run_cmd.py:51-54`), cross-drive relpath fallback (`repomap.py:169-175`).

## Reusable pieces (specific files or ideas, and the license terms for reuse)

Apache-2.0: reuse permitted with attribution and license notice; NOTICE obligations apply if a NOTICE file exists (none seen).
- `aider/repomap.py` (867 lines) with `aider/queries/**/*-tags.scm`: the full repo-map pipeline; depends on `grep_ast`, `networkx`, `diskcache`, tree-sitter.
- `aider/linter.py`: tree-sitter ERROR-node linter and `TreeContext`-based error excerpting (`225-247`), language-independent.
- `aider/coders/editblock_coder.py:127-335, 439-628`: SEARCH/REPLACE parsing and tolerant application with diagnostic messages.
- `aider/history.py`: head/tail split summarizer with recursive fallback.
- `aider/coders/chat_chunks.py`: stable-prefix message ordering and cache-control placement.
- `aider/repo.py:131-318`: scoped auto-commit with attribution modes and `/undo` safety checks in `commands.py:560-655`.
- `benchmark/benchmark.py`: harness pattern (per-exercise dirs, tries, replay, request hashes).

## Must not copy

- The ident-mention heuristic as-is (`base_coder.py:678-682`): unfiltered word bag.
- Dead fuzzy matcher (`editblock_coder.py:183-187, 296-329`) — either wire it or drop it.
- The confirm-everything UX for context acquisition (`base_coder.py:1761-1781`) if the goal is autonomy.
- Analytics opt-in lottery (`analytics.py:15, 119-135`) and `--no-verify` default for commits (`repo.py:278-279`) are policy choices, not technical ones.
- Hard-coded model quirks in `configure_model_settings` (`models.py:437-598`).

## Transferable abstractions (name each, one line)

- Symbol-graph PageRank repo map: files as nodes, ident references as weighted edges, personalization from the task, budgeted rendering.
- Hint-biased ranking: multiply edge weights by task-mentioned identifiers and by "in-focus" files (×50) instead of rebuilding indices.
- Token-budgeted binary search over a ranked list, accepting within 15% of target.
- mtime-keyed on-disk tag cache decoupled from the ranking step.
- Stable-prefix prompt layout for cache hits (system → examples → references → map → history → files → current).
- Reflection with a hard cap: parse failure, lint output, or test output becomes the next user message, max N times.
- Edit-format-as-model-capability: choose the output grammar per model from an empirical table.
- Scoped auto-commit + dirty-commit + session-scoped undo.
- Architect/editor handoff: reasoning model writes prose, cheaper model translates to edits with `map_tokens=0`.
- Fatal-only lint gate: parse errors and undefined names, not style.

## Open questions that need a probe run to answer

- Actual token size of the fixed prompt per edit format and model (word counts suggest 1.5-2k; not measured).
- Map build latency and PageRank cost on a 10k-file repo; how often `auto` mode hits its memo.
- How much the ×10 mention multiplier actually changes which files surface versus plain PageRank, on real requests.
- Frequency of SEARCH/REPLACE mismatches per model and whether enabling `replace_closest_edit_distance` would help or corrupt files.
- Whether the 3-reflection cap is the binding constraint on hard tasks in practice.
- Behavior of `files`/`manual` refresh modes when a chat file is edited mid-session (memo staleness).
- Quality of weak-model summaries after several recursive summarizations (`history.py:96`).
