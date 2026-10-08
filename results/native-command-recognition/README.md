# Literal native invocation controls — 2026-10-08

The installed staged comparison recorded missing exact-command links for
directory-wrapped test invocations. The generalized runtime now qualifies one
literal project-directory prefix and retains its exact configured command
separately from the observed invocation. The original comparison remains unchanged.

**Twenty-four actual local process/replay controls qualified**, using Python
unittest and JavaScript `npm run ci`, through Windows `cmd.exe` and Git Bash.
This is capture capability evidence. No model, fresh installed agent session,
advice-consumption observation or coding-benefit comparison ran.

| Per language and shell | Actual process | Declared milestone result |
|---|---|---|
| Direct success | Exit 0 | CURRENT |
| Qualified literal wrapper | Exit 0 | CURRENT |
| Real assertion failure | Nonzero exit | FAILED |
| Same check in a different directory | Exit 0 | INCOMPLETE |
| Real bounded interruption | No completed exit | INCOMPLETE |
| Failing check followed by `|| echo masked` | Exit 0 | ABSENT; no declared binding |

All four language/shell combinations produced these six outcomes. The wrong
directory contains a valid passing fixture, so rejecting it is not explained by
the command simply failing. Replay launchers explicitly use `--replay`, and none
writes native activation diagnostics. Original invocation and qualified declared
identity are checked independently for every bound receipt.

[summary.json](summary.json) records runtime and producer hashes, Python/platform
metadata, every control's process/callback status, receipt qualifications and
descriptive elapsed time. The final reviewed runtime produced 24/24 qualified
controls; earlier private producer observations are retained separately. Total
recorded control time was 22.719 seconds on this
machine; it mixes command and launcher work and is not a native latency guarantee.
Raw outputs and disposable projects remain private; this bounded report includes
no prompts, transcripts or captured output bodies.

Reproduce with installed Python, Node/npm and Bash:

```sh
python -m eval.command_invocations NEW_DISPOSABLE_DIRECTORY
python -m pytest tests/test_command_invocations.py tests/test_invocation_capture.py tests/test_invocation_producers.py -q
```

Missing tools and failed controls remain explicit and make the exercise
unqualified. Other shell forms remain unsupported automatic equivalences.
See [supported syntax and provenance](../../the-guide/command-capture.md).
