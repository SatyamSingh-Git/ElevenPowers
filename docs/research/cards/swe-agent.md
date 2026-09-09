# swe-agent (and mini-swe-agent)

Paths below are relative to the clone root `C:\Users\Satyam\AppData\Local\Temp\claude\e--ElevenPowers\cf4ea1a0-0d66-483c-af19-d5e4658f485a\scratchpad\repos\`. Everything is from reading source; nothing was executed. Claims marked *(inferred)* are my reading of what the code would do, not something the code states.

- **swe-agent**: https://github.com/SWE-agent/SWE-agent, commit `3ea751c087f32b16e039a2233dd6eefecef325d5` (2026-07-16), MIT (`swe-agent/LICENSE`), Python >=3.11 (`swe-agent/pyproject.toml`), 409 tracked files (100 .py, 69 .md, 51 .yaml, 22 .traj, 17 .sh). Core deps: `litellm`, `swe-rex>=1.4.0` (`pyproject.toml:57,60`).
- **mini-swe-agent**: https://github.com/SWE-agent/mini-swe-agent, commit `04d809ceab9df28f9adaed044884180159172930` (2026-09-03), MIT (`mini-swe-agent/LICENSE.md`), Python >=3.10, version 2.4.6 (`src/minisweagent/__init__.py:11`), 221 tracked files (113 .py). Deps: `litellm`, optional `swe-rex` (`pyproject.toml:38,53`).

**SWE-agent** is a config-driven single-agent loop: a Jinja-templated system + instance prompt, a set of shell "tool bundles" uploaded into a SWE-ReX sandbox, one action per model turn executed in a persistent bash session, pluggable history processors, optional retry/review loops that sample several full attempts and pick one, and a batch harness that writes SWE-bench `preds.json` and can hand it to `sb-cli`. It is a research scaffold for experimenting with agent-computer interfaces (ACIs) (`swe-agent/docs/background/aci.md`).

**mini-swe-agent** is the same team's deliberate reduction: a ~190-line agent (`src/minisweagent/agents/default.py`) with a single `bash` tool, no shell session (every action is a fresh `subprocess.run`/`docker exec`), a completely linear message list that *is* the trajectory, and no history processors, tool bundles, or review loops (`mini-swe-agent/README.md` "More motivation").

## Request flow (cite files)

1. CLI: `sweagent run` -> `sweagent/run/run_single.py:RunSingleConfig` (env, agent, problem_statement, actions) parsed by `sweagent/run/common.py:BasicCLI` (pydantic-settings; supports `--config a.yaml --config b.yaml` merging). Batch: `sweagent/run/run_batch.py:RunBatchConfig`.
2. `RunSingle.run()` (`run_single.py:191`): `env.start()` -> `agent.run(problem_statement, env, output_dir)` -> `save_predictions` -> `env.close()`.
3. `SWEEnv.start()` (`sweagent/environment/swe_env.py:114`): `deployment.start()`, `create_session(startup_source=[/root/.bashrc])`, set `LANG/PAGER` vars, copy repo, run git reset commands (`sweagent/environment/repo.py:_get_git_reset_commands`: `git restore .`, `git reset --hard`, `git checkout <base_commit>`, `git clean -fdq`), then `post_startup_commands`.
4. `DefaultAgent.setup()` (`sweagent/agent/agents.py:565`): `tools.install(env)` uploads each bundle dir to `/root/tools/<name>`, prepends `bin/` to PATH, sources `install.sh`, verifies each command with `which` (`sweagent/tools/tools.py:_install_commands`); writes registry variables to `/root/.swe-agent-env` and `{}` to `/root/state.json` (`tools.py:reset`); then appends system message, demonstrations, and the instance template rendered with the first `state` dict.
5. Loop: `DefaultAgent.run()` -> `step()` -> `forward_with_handling(self.messages)` -> `forward()` -> `model.query(history)` -> `tools.parse_actions` -> `handle_action` -> `env.communicate(action, timeout=execution_timeout)` -> `tools.get_state(env)` (runs every bundle's `state_command`, reads `/root/state.json`) -> `handle_submission` (looks for `<<SWE_AGENT_SUBMISSION>>` in the observation, then reads `/root/model.patch`) (`agents.py:1010-1090, 1231`).
6. Each step appends an assistant entry (content, thought, action, tool_calls, thinking_blocks) and a user/tool observation entry rendered through `next_step_template` / `next_step_no_output_template` / `next_step_truncated_observation_template` (`agents.py:add_step_to_history`).
7. Termination: `step.done` set by submission, the literal `exit` action, `_ExitForfeit`, or any error branch that calls `attempt_autosubmission_after_error` (`agents.py:1094-1216`).

## What goes into the model (always-loaded vs on-demand, with token estimates)

Estimates are chars/4. Character counts were measured from the YAML files.

Default config (`swe-agent/config/default.yaml`, function calling, bundles `registry`, `edit_anthropic`, `review_on_submit_m`):
- System template: 77 chars (~20 tok). Instance template: 1,207 chars (~300 tok) + `{{problem_statement}}` + `{{working_dir}}` (from `_state_anthropic`). Always loaded.
- Tool schemas sent as `tools=` on every call (`sweagent/agent/models.py:_single_query`, `ToolConfig.tools` in `sweagent/tools/tools.py`): `bash` (`sweagent/tools/commands.py:BASH_COMMAND`), `str_replace_editor` (docstring 988 chars + arg descriptions 963 chars, ~500 tok; `tools/edit_anthropic/config.yaml`), `submit` (~20 tok). Roughly 600 tok of tool schema per call, always.
- Per-turn observation: raw command output up to `max_observation_length` = 100,000 chars (~25k tok) before the truncation template kicks in (`agents.py:TemplateConfig`). `str_replace_editor view` self-caps at `MAX_RESPONSE_LEN` = 16,000 chars (~4k tok) and, for `.py` files over that with `USE_FILEMAP`, prints a tree-sitter "filemap" that elides function bodies >= 5 lines (`tools/edit_anthropic/bin/str_replace_editor:27-28,192-230,493-508`; `tools/filemap/bin/filemap`).
- On first `submit`: the review message (827 chars, ~200 tok) plus the full `git diff` is injected as the observation (`tools/review_on_submit_m/bin/submit`).
- No demonstrations, no `command_docs` in the prompt (function calling carries them), no history elision; only `cache_control` on the last 2 user/tool messages. History grows linearly until `ContextWindowExceededError` (`models.py:_single_query` compares `litellm.token_counter` against `max_input_tokens`).

Paper-era config (`swe-agent/config/sweagent_0_7/07.yaml`, thought/action text parsing): system template 1,814 chars that embeds `{{command_docs}}` (auto-generated by `sweagent/tools/utils.py:generate_command_docs`; ~1,900 chars for windowed+search+edit, ~500 tok); instance template 3,148 chars (~800 tok) with `{{open_file}}`/`{{working_dir}}` state; a demonstration trajectory added as one user message (`trajectories/demonstrations/replay__marshmallow-code__marshmallow-1867__default_sys-env_window100__.../*.traj`, 19,117 chars of history content, ~5k tok, 23 entries); `last_n_observations: n=5` so older observations collapse to "Old environment output: (N lines omitted)". Every observation ends with the pseudo-prompt `(Open file: ...) (Current directory: ...) bash-$`.

## Tool bundles and guardrails (detailed)

Bundle format: a directory with `config.yaml` (`tools:` map of name -> signature/docstring/arguments/end_name, optional `state_command`), `bin/` executables, optional `install.sh` and `lib/` (`sweagent/tools/bundle.py`). Duplicate tool names across bundles raise at config time (`tools.py:ToolConfig.commands`). Multi-line commands (those with `end_name`) are wrapped in a heredoc automatically (`sweagent/tools/utils.py:_guard_multiline_input`).

- **registry** (`tools/registry`): no tools. `lib/registry.py` is a JSON key/value file at `/root/.swe-agent-env` used by all other bundles to persist state between subprocess tool invocations (window position, current file, submit stage). `_read_env`/`_write_env` CLI helpers.
- **windowed** (`tools/windowed`): `open <path> [line]`, `goto <line>`, `scroll_up`, `scroll_down`, `create <file>`. `lib/windowed_file.py:WindowedFile` shows `WINDOW` (default 100) lines with `OVERLAP` 2, prints `[File: path (N lines total)]`, `(k more lines above/below)`, numbered lines; `goto` positions the target 1/6 of the window from the top (`offset_multiplier`). Guardrails: refuses directories, clamps line numbers, `create` refuses existing files. `_state` writes `open_file` and `working_dir` to `/root/state.json`.
- **windowed_edit_linting** (`tools/windowed_edit_linting/bin/edit`): `edit <start>:<end>\n<text>\nend_of_edit` replaces a line range in the open file. Guardrail: runs `flake8 --isolated --select=F821,F822,F831,E111,E112,E113,E999,E902` before and after (`tools/windowed/lib/flake8_utils.py:flake8`), maps pre-existing errors through the edit window (`_update_previous_errors`), and if *new* errors appear it **reverts the edit** (`wf.undo_edit()`), prints the errors, the would-be window and the original window, and says "DO NOT re-run the same failed edit command". Only `.py` files are linted (`flake8()` returns "" otherwise). This is the paper's "linter that refuses syntactically broken edits" (`docs/background/aci.md`).
- **windowed_edit_replace** (`tools/windowed_edit_replace`): `edit <search> <replace> [replace-all]` and `insert <text> [line]` scoped to the *displayed window*. Guardrails: distinct messages for not-found-anywhere, found-elsewhere-in-file (lists line numbers, suggests `goto`), multiple occurrences in window, no-op edit; same flake8 revert path; can emit `###SWE-AGENT-RETRY-WITH-OUTPUT###` so the agent requeries without committing the step to history (`agents.py:RETRY_WITH_OUTPUT_TOKEN`, `_RetryWithOutput`).
- **windowed_edit_rewrite**: `edit <text>` replaces the whole displayed window.
- **search** (`tools/search/bin`): `search_dir <term> [dir]` (grep across files, prints per-file match counts, refuses if >100 files match: "Please narrow your search"), `find_file <name> [dir]`, `search_file <term> [file]`. The deliberate design is "list each file with >=1 match, not the matches" (`docs/background/aci.md`).
- **edit_anthropic** (`tools/edit_anthropic/bin/str_replace_editor`, 712 lines): one `str_replace_editor` tool with `view|create|str_replace|insert|undo_edit`. Guardrails: `str_replace` requires `old_str` to occur exactly once (exit 15 if absent, exit 16 with line numbers if multiple), refuses no-op replacements, keeps per-file undo history, shows a snippet expanded to enclosing function/class boundaries via `WindowExpander`; `view` on directories runs `find -maxdepth 2`; `view_range` is validated; long outputs are clipped at 16,000 chars with a note to `grep -n` first. Lint: unlike the windowed editor, edits are **applied** and the flake8 diff is appended as a warning ("Your edits have been applied, but the linter has found syntax errors"); controlled by `USE_LINTER`/`LINT_COMMAND` registry vars. `install.sh` pip-installs `tree-sitter` for the filemap.
- **filemap** (`tools/filemap/bin/filemap`): standalone tree-sitter view of a Python file eliding function bodies >= 5 lines.
- **submit** (`tools/submit/bin/submit`): reverse-applies `/root/test.patch` if present, `git add -A && git diff --cached > /root/model.patch`, prints `<<SWE_AGENT_SUBMISSION>>`.
- **review_on_submit_m** (`tools/review_on_submit_m/bin/submit`): staged submit. On stage k < len(`SUBMIT_REVIEW_MESSAGES`) it prints the k-th message with `{{diff}}` and `{{problem_statement}}` substituted and bumps `SUBMIT_STAGE` in the registry; only after all stages (or `-f`, used by autosubmit) does it emit the real submission marker.
- **diff_state** (`tools/diff_state`): a `state_command` only; after every step writes the current `git diff` into `state["diff"]`, which templates can render (`config/benchmarks/250212_sweagent_heavy_sbl.yaml` "+state" variant) and which autosubmit falls back to when the container is dead (`agents.py:attempt_autosubmission_after_error`).
- **forfeit** (`tools/forfeit`): `exit_forfeit` prints `###SWE-AGENT-EXIT-FORFEIT###`, ending the run with `exit_forfeit` status.
- Others present but not studied in depth: `image_tools`, `web_browser`, `multilingual_setup`.
- Agent-side guardrails independent of bundles (`sweagent/tools/tools.py:ToolFilterConfig`): blocklist prefixes (`vim`, `vi`, `emacs`, `nano`, `nohup`, `gdb`, `less`, `tail -f`, `python -m venv`, `make`), standalone blocks (`python`, `python3`, `ipython`, `bash`, `sh`, `su`, ...), regex-gated tools. A blocked action raises `_BlockedActionError` -> requery with `blocklist_error_template`. Bash syntax errors (`BashIncorrectSyntaxError` from SWE-ReX) -> requery with `shell_check_error_template`. Function-calling parser requires exactly one tool call per turn (`sweagent/tools/parsing.py:444-450`, error codes `missing`/`multiple`). `max_requeries` = 3 for format/blocklist/syntax errors, then `exit_format` autosubmit (`agents.py:DefaultAgentConfig`, `forward_with_handling`).

## History processors and context management

`DefaultAgent.messages` filters history to this agent's entries and chains the configured processors on every query (`agents.py:messages`). All in `sweagent/agent/history_processors.py`:
- `last_n_observations` (n, polling, tag overrides): replaces all but the last n non-demo observations with "Old environment output: (N lines omitted)"; never removes the first (instance) observation; `polling` batches removals so caches survive several steps. Docstring notes it breaks prompt caching.
- `closed_window`: keeps only the most recent window per file (regex on `[File: ... (N lines total)]` and `N:` line prefixes), replacing older ones with "Outdated window with N lines omitted".
- `tag_tool_call_observations`: tags actions by function name so `last_n_observations` can `keep_output`/`remove_output` selectively.
- `cache_control` (last_n_messages, offset, roles): sets Anthropic `cache_control: ephemeral` on the last n user/tool messages and clears it elsewhere.
- `remove_regex` (patterns, keep_last): strips e.g. `<diff>.*</diff>` from all but the last k messages; used with `diff_state` so the cumulative diff is only shown recently.
- `image_parsing`: converts base64 markdown images into multimodal content parts.
- Observation truncation is separate: `max_observation_length` 100,000 chars with an instructive `<NOTE>` (`agents.py:TemplateConfig`).
- There is no summarisation, no compaction, and no automatic recovery once the window is exceeded: `ContextWindowExceededError` -> `exit_context` autosubmit (`agents.py:1188`).

## Retries, review, candidate selection

Three distinct mechanisms, all in `sweagent/agent/`:
- **Requery** (step-level, default on): format/blocklist/syntax errors add a temporary assistant+user pair and requery up to `max_requeries`=3; the failed attempt goes to the trajectory but not the history (`agents.py:get_model_requery_history`, `forward_with_handling`).
- **RetryAgent + retry loops** (`agents.py:RetryAgent`, `reviewer.py`): `type: retry` config with `agent_configs` (round-robin per attempt) and `retry_loop`. Each attempt runs a fresh `DefaultAgent` after `env.hard_reset()` (container restart). `ScoreRetryLoop`: a `Reviewer` LM scores each trajectory (`n_sample` samples, mean minus `reduce_by_std`*std, penalty for non-`submitted` exits), stops at `accept_score`/`max_accepts`/`max_attempts`/`cost_limit`, picks max score, ties broken by fewest API calls. `ChooserRetryLoop`: after all attempts a `Chooser` LM sees the problem statement plus each patch (`submission_template`, e.g. patch + `edited_files30` context) and returns an index; optional `Preselector` narrows candidates first; only `submitted` attempts are considered when >=2 exist. Used in `config/benchmarks/250212_sweagent_heavy_sbl.yaml` (3 config variants, up to 10 attempts, $6 cap, `o1` chooser at `reasoning_effort: high`).
- **Action samplers** (`action_sampler.py`, per-step): `ask_colleagues` samples n completions, concatenates them as "Your colleagues had the following ideas", and asks for a final action; `binary_trajectory_comparison` samples 4-10 completions (more if any is an edit), dedups, and runs a tournament of pairwise LM comparisons ("first"/"second"). Off by default.
- **Review-on-submit** is prompt-level (see bundle above), not an LM reviewer.
- API retries: tenacity with configurable attempts/min/max wait (`models.py:RetryConfig`, `LiteLLMModel.query`).

## Environment and sandbox

`SWEEnv` wraps a SWE-ReX `AbstractDeployment` (`swe_env.py`). Deployment configs come from the external `swerex` package; `Docker` (default image `python:3.11`, `python_standalone_dir=/root`), `Local`, `Dummy` are imported in `sweagent/run/batch_instances.py:11-15`; `modal` is referenced in `run_single.py` docstring. *(inferred: fargate/daytona exist in swe-rex but were not verified here.)* One persistent bash session (`CreateBashSessionRequest`); `communicate()` sends `BashAction(command, timeout, check)` and returns output; `interrupt_session()` sends `BashInterruptAction` after a timeout; `read_file`/`write_file`/`upload` go through the runtime API, not the shell. Repo sources: `github` (clone), `local` (upload; refuses dirty working trees), `preexisting` (SWE-bench images have `/testbed`), `swesmith` (`repo.py`). Tools run as root inside the container; `propagate_env_variables` can forward host secrets and the docstring warns they appear in debug logs (`tools.py:ToolConfig`).

## Batch harness and evaluation

`sweagent run-batch` (`sweagent/run/run_batch.py`): instance sources `swe_bench` (HF datasets `lite|verified|full|multimodal|multilingual`, image `docker.io/swebench/sweb.eval.x86_64.<id with __ -> _1776_>`), `huggingface`, `file`, `expert_file`, `swesmith`, each with regex `filter`, python-style `slice`, seeded `shuffle` (`batch_instances.py`). `ThreadPoolExecutor(num_workers)` with a random startup delay; per-instance output dir with `.traj`, `.pred` (`{model_name_or_path, instance_id, model_patch}`, `run/common.py:save_predictions`), `.patch` (`run/hooks/apply_patch.py`), `trace/debug/info` logs, and a replayable `<id>.config.yaml`. Existing trajectories with an exit status are skipped unless `redo_existing`. `merge_predictions` builds `preds.json`. With `--instances.evaluate=True`, `run/hooks/swe_bench_evaluate.py` shells out to `sb-cli submit swe-bench_lite|verified|-m <split> --predictions_path ...` every 30 s incrementally and once at the end, moving the report to `results.json`; evaluation itself is remote (SWE-bench cloud), not in-repo. `total_cost_limit` aborts the whole batch (`TotalCostLimitExceededError` -> `_BreakLoop`). `run_replay.py` re-executes a trajectory's actions to regenerate demos; `run_traj_to_demo.py`, `compare_runs.py`, `quick_stats.py` support analysis.

## mini-swe-agent: loop, config, what it omits, and why it matters

Loop (`src/minisweagent/agents/default.py`): `run(task)` renders `system_template` and `instance_template` (Jinja, `StrictUndefined`) into two messages, then `while True: step()`. `step()` = `query()` (checks `step_limit`, `cost_limit`, `wall_time_limit_seconds`, then `model.query(messages)`) + `execute_actions()` (`env.execute(action)` per parsed action, then `model.format_observation_messages`). Control flow is by exceptions carrying messages: `Submitted`, `LimitsExceeded`, `TimeExceeded`, `UserInterruption`, `FormatError` all subclass `InterruptAgentFlow(*messages)` (`src/minisweagent/exceptions.py`); the loop appends those messages and exits when the last role is `exit`. `max_consecutive_format_errors`=3. The trajectory is saved after every step (`save()`), format `mini-swe-agent-1.1`, and is literally `self.messages` plus an `info` block.

Model (`src/minisweagent/models/litellm_model.py`): one tool, `BASH_TOOL` (`models/utils/actions_toolcall.py`); parser rejects zero tool calls or non-`bash` names with a templated error that distinguishes `finish_reason == length` truncation; multiple tool calls per turn are allowed (`swebench.yaml` sets `parallel_tool_calls: true`). Cost from `litellm.completion_cost`; a zero/unknown cost raises unless `cost_tracking: ignore_errors`. tenacity retry, 10 attempts, 4-60 s exponential (`models/utils/retry.py`); `ContextWindowExceededError` is an abort exception. Anthropic models get `cache_control` on the last message automatically (`models/__init__.py:get_model`, `models/utils/cache_control.py`). A text-based variant parses one ```` ```mswea_bash_command ```` block (`models/utils/actions_text.py`, `config/mini_textbased.yaml`).

Environment (`environments/local.py`, `docker.py`, `singularity.py`, `extra/{bubblewrap,contree,swerex_docker,swerex_modal}.py`): `execute()` is `subprocess.Popen(shell=True, start_new_session)` with a timeout that kills the process group, or `docker exec -w cwd <id> bash -lc <cmd>` against a container started with `sleep 2h`. Submission is detected by the first output line being `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT` with return code 0; the rest of stdout is the submission (`_check_finished`).

Config (`src/minisweagent/config/mini.yaml`): system 63 chars; instance 3,007 chars (~750 tok) containing the workflow, the "every action is a new subshell" rule, and sed/heredoc/`nl -ba` examples; `cost_limit: 3`, `step_limit: 0`, `mode: confirm`. Observation template: JSON with returncode + output, or head/tail 5,000 chars each when output > 10,000 chars. `config/benchmarks/swebench.yaml`: instance 4,500 chars (~1.1k tok) adds boundaries (do not modify tests/config), a three-step patch submission protocol (`git diff -- files > patch.txt`, verify, `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat patch.txt`), `step_limit: 250`, docker with `cwd: /testbed`, `BASH_ENV: /root/.bashrc`, model `anthropic/claude-sonnet-4-5-20250929`.

Batch (`src/minisweagent/run/benchmarks/swebench.py`): same dataset mapping plus `rebench`/`smith`, thread pool, `preds.json` updated under a lock after each instance, exit-status YAML; no in-repo evaluation (docs point to `sb-cli`, `docs/usage/swebench.md:110-122`). `InteractiveAgent` (`agents/interactive.py`) adds `human|confirm|yolo` modes, a regex whitelist, and Ctrl-C interruption that injects a user message.

Deliberately omitted (README "More motivation", `docs/faq.md` "Why no shell session"): no tools other than bash, no file viewer/editor/search/lint tools, no persistent shell (so no `cd`/`export` persistence, but no hung-session detection either), no history processors, no demonstrations, no retry/review/chooser loops, no state commands, no patch extraction on the agent side. Why it matters: the authors report >74% on SWE-bench Verified with this design and argue the ACI machinery of 2024 is no longer needed for frontier models; it is also the "bash-only" leaderboard baseline and is preferred for RL/fine-tuning because messages == trajectory.

## Task understanding and planning

No planner, decomposition, or task classification in either system. Planning is entirely the prompt's numbered workflow (find code, reproduce, edit, rerun, edge cases) in `config/default.yaml` and `config/mini.yaml`. SWE-agent's `strategy_template` slot exists but is unused in shipped configs (`agents.py:TemplateConfig`). Problem statements are plain text, file, GitHub issue (title + body), or SWE-bench multimodal with images (`sweagent/agent/problem_statement.py`).

## Memory across sessions

None in either. SWE-agent's only cross-run artefact is demonstrations (static trajectories chosen in config) and the per-instance `replay_config` for reproducibility. mini-swe-agent stores a global `.env` for keys/model name (`__init__.py:global_config_file`) and `last_mini_run.traj.json`.

## Verification: what counts as done

SWE-agent: done == the `submit` tool emitted `<<SWE_AGENT_SUBMISSION>>` and `/root/model.patch` was readable (`agents.py:handle_submission`); the patch content is the deliverable regardless of test results. Autosubmit on any error yields `submitted (exit_cost)` etc., and `run/common.py:_is_promising_patch` treats only a clean `submitted` as trustworthy (used by `SaveApplyPatchHook`). No test execution is enforced; the prompt asks the model to reproduce and rerun. `review_on_submit_m` forces one extra self-review turn. mini-swe-agent: done == the model prints the sentinel; the submission is whatever text follows it. Correctness is judged only externally by SWE-bench.

## Multi-agent / roles

No concurrent agents. `RetryAgent` runs sequential attempts and a separate reviewer/chooser LM; `ask_colleagues` and `binary_trajectory_comparison` are sample-and-judge with the same model (`action_sampler.py`). mini-swe-agent has none.

## Model routing

Both go through litellm with a single configured model. SWE-agent: `api_key` may be `$ENV` or `:::`-separated keys chosen per thread (`models.py:choose_api_key`), litellm `fallbacks`, custom model registry for cost tables, forced `max_tokens` for Anthropic. Reviewer/chooser have their own `ModelConfig` (e.g. `o1` chooser vs Sonnet worker in `250212_sweagent_heavy_sbl.yaml`). mini-swe-agent: `model_class` selects litellm/openrouter/portkey/requesty/response-API variants (`models/__init__.py:_MODEL_CLASS_MAPPING`); `models/extra/roulette.py` exists for random model selection.

## Failure recovery

SWE-agent (`agents.py:forward_with_handling`): requery (format, blocklist, bash syntax, content policy) up to 3; command timeout -> `interrupt_session` + templated observation, exit after `max_consecutive_execution_timeouts`=3; `total_execution_timeout`=1800 s; cost/call limits, context window, API `RetryError`, SWE-ReX errors, and unknown exceptions all route to `attempt_autosubmission_after_error`, which runs `git add -A && git diff --cached` itself or falls back to the last `state["diff"]` if the container is dead. `RetryAgent` restarts the container between attempts. mini-swe-agent: format errors re-prompt (3 consecutive max); limits raise `LimitsExceeded` (interactive mode prompts for new limits); any other exception is recorded as an `exit` message with traceback and re-raised (`default.py:handle_uncaught_exception`); the batch runner catches it and writes an empty submission.

## Security posture

SWE-agent: everything runs as root in the container; the blocklist is a UX guard against interactive commands, not a security boundary; `propagate_env_variables` leaks secrets into logs by admission; `OpenPRHook` pushes a fork branch with `GITHUB_TOKEN` in the URL (`run/hooks/open_pr.py:73-76`); `apply_patch_locally` only for clean `submitted` status. mini-swe-agent: `mini` defaults to `LocalEnvironment` on the host with `mode: confirm` (every non-whitelisted command needs a keypress); `-y/--yolo` disables that; docker/bubblewrap/singularity/contree environments are opt-in.

## Host coupling

SWE-agent: Linux container assumptions throughout (`/root/...` paths, `bash`, `flake8`, `git`, `which`), `python_standalone_dir` so tools have a Python even in bare images, `edit_anthropic/install.sh` needs pip network access. `LocalRepoConfig` requires a clean git tree. mini-swe-agent: `LocalEnvironment` works on Windows via `subprocess` without process groups; Darwin-specific sed hint in `mini.yaml`; docker path needs a working `docker` CLI.

## Observability (trajectories)

SWE-agent writes `<id>.traj` JSON after every step with `trajectory` (action, observation, response, thought, execution_time, state, `query` = exact messages sent, `extra_info` such as colleague discussion/comparison logs), `history`, `info` (exit_status, submission, model_stats, `edited_files30/50/70` context strings, versions/hashes, review/chooser outputs), `replay_config`, `environment` (`agents.py:get_trajectory_data`, `docs/usage/trajectories.md`). Plus three log levels per instance, `run_batch_exit_statuses.yaml`, and a web inspector (`sweagent/inspector/`). Hooks (`agent/hooks`, `environment/hooks`, `run/hooks`) expose every lifecycle event. mini-swe-agent: one `.traj.json` = messages with `extra` (cost, raw response, timestamps, returncodes); a Textual inspector (`run/utilities/inspector.py`).

## Trace: trivial task (border radius)

SWE-agent, `sweagent run --config config/default.yaml --env.repo.path <repo> --problem_statement.text "change the primary button border radius to 8px"` (read from `run_single.py`, `swe_env.py`, `tools.py`, `default.yaml`): start a `python:3.11` container, upload the repo (must be clean), `git reset --hard` + `git clean -fdq` inside the container, upload 3 bundles, `pip install tree-sitter` (may fail silently), check `which str_replace_editor submit`. Model receives ~600 tok of tool schema + ~350 tok of prompt. *(inferred)* Turn 1 `bash: grep -rn "border-radius" src`; turn 2 `str_replace_editor view`; turn 3 `str_replace` (no lint for `.css/.tsx`, edit applied, snippet echoed); turn 4 `submit` -> review message with diff asking to rerun reproduction and remove scripts; turn 5 `submit` again -> patch. Minimum 5 model calls; output is a `.patch` file that is only applied to the local repo with `--actions.apply_patch_locally=True`. Overhead: container lifecycle, tool install, Python-centric reproduction instructions, mandatory double submit.

mini-swe-agent, `mini -t "..."` (read from `run/mini.py`, `agents/interactive.py`, `mini.yaml`): no setup; runs in the cwd as the user. Turn 1 `grep -rn border-radius`; turn 2 `sed -i 's/border-radius: 4px/border-radius: 8px/' path` (the prompt explicitly teaches this); turn 3 `echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`; in `confirm` mode the user presses enter for each command; `confirm_exit` asks once more. The edit is already in the working tree; no patch. Three calls, ~800 tok static prompt. *(inferred)* A sed pattern that matches zero lines succeeds silently, so a wrong guess is only caught if the model re-reads the file.

## Trace: hard task (auth race)

SWE-agent (default config): the instance template pushes "create a script to reproduce" and rerun it; with `execution_timeout` 30 s (`ToolConfig` default; `default.yaml` does not raise it, the benchmark configs set 300) a stress loop that runs long is interrupted and the model is told to use a faster command; three consecutive timeouts end the run with an autosubmitted partial diff. Each iteration keeps full observations in history (no elision in `default.yaml`), so long test logs (up to 100k chars each) can exhaust the window and trigger `exit_context` autosubmit of whatever is on disk. There is no test-runner integration or flakiness detection; the reviewer/chooser loops are available only via a `type: retry` config (`250212_sweagent_heavy_sbl.yaml`), which would sample several complete attempts and let an `o1` chooser pick by reading patches, not by running tests. The `str_replace` uniqueness rule helps when editing near-duplicate lock/refresh code; the `python` standalone blocklist forbids a REPL but not scripts. Realistic budget: `per_instance_cost_limit` $3 default (`models.py:73`), then `exit_cost` autosubmit.

mini-swe-agent: same reproduction-driven prompt, but every command is a fresh subprocess with a 30 s timeout (`LocalEnvironmentConfig.timeout`; 60 s in `swebench.yaml`), so a long-running race reproducer must be backgrounded or shortened, and no `cd`/venv activation persists. Parallel tool calls let it run several probes per turn. No history trimming at all; a context overflow is a hard abort (`abort_exceptions`) that ends the run with an exception exit status and empty submission. `cost_limit` $3 and unlimited steps by default; no review, no retry. *(inferred)* Both systems are equally blind to intermittency: neither reruns tests N times or diffs behaviour across runs unless the model decides to.

## Strengths (ranked, concrete, cited)

1. Tool bundles are self-contained directories with YAML schemas, install scripts, and a state command; the same bundle works for function calling and text parsing, and docs are generated from the schema (`sweagent/tools/bundle.py`, `commands.py:get_function_calling_tool`, `utils.py:generate_command_docs`).
2. Edit guardrails that revert on new lint errors, mapping pre-existing errors across the edit window so only *introduced* errors count (`tools/windowed/lib/flake8_utils.py:_update_previous_errors`); `str_replace` uniqueness checks with line-number hints (`str_replace_editor:516-534`).
3. Robust termination: every error path funnels into autosubmission with a diff recovered even from a dead container (`agents.py:attempt_autosubmission_after_error`, `tools/diff_state`).
4. Full `query` capture per step plus `replay_config` makes any run reproducible and replayable (`agents.py:add_step_to_trajectory`, `run_replay.py`).
5. Composable history processors with tag-based exceptions and cache-aware `polling` (`history_processors.py:LastNObservations`).
6. mini-swe-agent: stateless action execution eliminates the hung-session problem and makes sandbox swaps a one-line change (`environments/local.py:_run`, `docker.py:execute`); exception-as-message control flow keeps the loop readable (`agents/default.py:run`).

## Weaknesses (ranked, concrete, cited)

1. Python-only guardrails: flake8 only runs on `.py` (`flake8_utils.py:flake8`), filemap assumes Python (`tools/filemap/bin/filemap`), and the default prompt says "python code repository" (`config/default.yaml`).
2. Default config has no context management beyond truncation; a long run dies with `exit_context` rather than compacting (`agents.py:1188`; `history_processors.py` has no summariser).
3. One tool call per turn enforced by the parser (`parsing.py:444-450`); no parallel reads.
4. Heavy setup per instance: container start, bundle upload, `pip install tree-sitter`, `which` checks (`tools.py:_install_commands`), and a full container restart per retry attempt (`agents.py:RetryAgent._next_attempt`).
5. Review/chooser loops judge patches by reading them, not by running tests (`reviewer.py:Chooser.build_messages`); ties fall back to index 0.
6. Tool state lives in ad-hoc JSON files (`/root/.swe-agent-env`, `/root/state.json`) mutated by subprocesses; the `SUBMIT_STAGE` counter means a second submit always passes even if nothing changed (`review_on_submit_m/bin/submit`).
7. mini-swe-agent: no edit tool means sed/heredoc edits with silent no-match failures; no lint; `LocalEnvironment` runs on the host by default with only a y/n prompt as the guard (`agents/interactive.py`).

## Genuinely innovative vs mostly prompt engineering

Innovative (at the time, and still useful): the ACI framing and its measured ingredients (100-line viewer, revert-on-lint, file-list-only search, explicit empty-output message; `docs/background/aci.md`); the bundle abstraction; the lint-diff windowing; diff-on-every-step state for crash-safe autosubmit; mini's stateless-execution + linear-history design as an RL-friendly baseline. Mostly prompt engineering: the numbered workflow, review-on-submit messages, `ask_colleagues`, chooser/reviewer prompts, mini's sed cheat sheet.

## Unnecessary complexity / scales poorly / wastes tokens / brittle behavior

- Three overlapping ways to express a tool (signature string, `arguments`, `argument_format` Jinja) with validation rules linking them (`commands.py:Command.validate_arguments`, `invoke_format`).
- `last_n_observations` and `remove_regex` deep-copy and rewrite the history every step; `remove_regex` runs regexes over every message each call.
- The `+state` variant re-sends the cumulative diff in each of the last 2 observations (`250212_sweagent_heavy_sbl.yaml:next_step_with_diff`).
- `ScoreRetryLoop` spends `n_sample`=5 reviewer calls per attempt by default (`reviewer.py:ReviewerConfig`).
- Regex-based `ClosedWindowHistoryProcessor` depends on the exact `[File: ...]` banner format.
- Marker strings in stdout (`<<SWE_AGENT_SUBMISSION>>`, `###SWE-AGENT-RETRY-WITH-OUTPUT###`, `COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT`) are the control channel; any program that prints them hijacks the loop.
- `Chooser.choose` sets `response` only inside a `try`; on failure `ChooserOutput(response=response)` references an unbound name *(read from `reviewer.py:330-345`)*.

## Reusable pieces (specific files or ideas, and the license terms for reuse)

Both repos are MIT: reuse with attribution and license notice. Candidates: `tools/windowed/lib/flake8_utils.py` (edit-window error diffing); `tools/edit_anthropic/bin/str_replace_editor` (uniqueness-checked replace, `WindowExpander` to function boundaries, undo stack; docstring credited to OpenHands, also MIT); `tools/registry/lib/registry.py` (tiny cross-process state file); `sweagent/tools/bundle.py` + `commands.py` (YAML tool schema -> OpenAI function schema + text docs); `history_processors.py:CacheControlHistoryProcessor` and mini's `models/utils/cache_control.py`; `agents.py:attempt_autosubmission_after_error` pattern; mini's `environments/local.py:_run` (process-group kill on timeout) and `agents/default.py` exception-driven loop; `models/utils/actions_toolcall.py` finish-reason-aware format errors.

## Must not copy

- Root-in-container and `propagate_env_variables` secret handling (`tools.py:ToolConfig` warns keys land in logs).
- Token-in-URL git push (`run/hooks/open_pr.py:73-76`).
- Stdout sentinel strings as the submission/control protocol.
- Silently swallowed install failures (`edit_anthropic/install.sh` `|| true`) and `diff_state` clearing the diff on any exception.
- The unbound `response` path in `reviewer.py:Chooser.choose`.

## Transferable abstractions (name each, one line)

- **Tool bundle**: directory = schema YAML + executables + install + state command, uploaded into the sandbox and documented automatically.
- **State command**: after each action, tools write a JSON state that templates can render (open file, cwd, diff).
- **Revert-on-new-lint**: lint before/after, shift old errors through the edit window, reject only newly introduced errors.
- **History processor chain**: pure functions over the message list applied at query time, leaving the stored history intact.
- **Autosubmit-on-any-exit**: every failure path still extracts the working-tree diff.
- **Staged submit**: the submit tool returns a review prompt the first k times.
- **Sample-then-judge**: retry loop with reviewer scoring or chooser selection over complete attempts.
- **Stateless action execution**: each command is an independent subprocess/`docker exec`; the prompt teaches `cd ... &&` prefixes.
- **Exception-as-message control flow**: interrupts carry the messages to append, so the loop has one `while True`.

## Open questions that need a probe run to answer

- Actual token volume per turn under `default.yaml` on a mid-size repo (observations vs tool schema vs cached prefix), and how often `exit_context` fires without `last_n_observations`.
- Whether `review_on_submit_m` measurably changes patch quality versus a single submit.
- Chooser accuracy versus test-based selection on the same attempt set.
- Timeout behaviour of SWE-ReX session interrupts on stuck commands, and how often `max_consecutive_execution_timeouts` ends runs.
- mini-swe-agent's effective step count and silent-sed-failure rate on non-Python repos.
- Whether `edit_anthropic/install.sh` pip installs succeed in offline SWE-bench images (filemap silently disabled otherwise).
