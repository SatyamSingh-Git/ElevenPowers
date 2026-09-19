"""No credential survives anywhere under the state directory.

Written because choosing *which fields* hold text was tried twice and failed
twice in two days. `Ledger.saw_output` was made to scrub and `Evidence.detail`
was missed. `Evidence.detail` was then covered and `ledger.request`,
`ledger.decisions` and `blindspots.jsonl` were missed - found by an audit's
acceptance criterion, which said *every* persisted representation and meant it.

So this test does not name fields. It drives a credential through every path
that writes text, then reads every file in the directory and greps. A field
added next year by somebody who never opened `redact.py` is covered by
construction, which is the only way this stops recurring.
"""

from __future__ import annotations

import json
import subprocess

import pytest

from core import blindspots, hook
from core.ledger import STATE_DIR, Ledger
from core.redact import MARK

FAKE = "ghp_" + "PROBEONLY1234567890abcdefghijkl"


@pytest.fixture
def repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, capture_output=True)
    return tmp_path


def _drive_a_credential_through_everything(root):
    led = Ledger(root=root, task="t")
    led.request = f"deploy using token {FAKE} please"
    led.saw_output(f"curl -H 'Authorization: Bearer {FAKE}'", "line one\nline two\n")
    led.note("a decision", f"ran with {FAKE}")
    led.save()
    blindspots.record(root, "unreadable test output",
                      f"npm test --token={FAKE} -> exit 1, no runner recognised")
    hook.on_post_tool({"tool_name": "Bash",
                       "tool_input": {"command": f"deploy --key {FAKE}"},
                       "tool_response": {"stdout": f"using {FAKE}\n", "stderr": ""}}, root)


def test_no_credential_survives_anywhere_under_the_state_directory(repo):
    _drive_a_credential_through_everything(repo)
    written = [p for p in sorted((repo / STATE_DIR).rglob("*")) if p.is_file()]
    assert written, "nothing was written, so this proves nothing"
    leaking = [p.name for p in written
               if FAKE in p.read_text(encoding="utf-8", errors="replace")]
    assert leaking == [], f"credential survived in: {leaking}"


def test_the_probe_would_notice(repo):
    """The forward control on the test above.

    A grep that never finds anything is indistinguishable from a grep that
    cannot find anything. This writes the value through a path nothing scrubs,
    so the search is known to work.
    """
    (repo / STATE_DIR).mkdir(parents=True, exist_ok=True)
    (repo / STATE_DIR / "unscrubbed.txt").write_text(FAKE, encoding="utf-8")
    written = [p for p in sorted((repo / STATE_DIR).rglob("*")) if p.is_file()]
    leaking = [p.name for p in written
               if FAKE in p.read_text(encoding="utf-8", errors="replace")]
    assert leaking == ["unscrubbed.txt"]


def test_the_ledger_still_parses_after_scrubbing(repo):
    """Scrubbing the serialized JSON corrupted it, so the shape is asserted.

    `BEARER` matched `\\S`, swallowed the closing quote and comma after a token,
    and `Ledger.load` raised `Invalid control character`. Scrubbing walks the
    structure now; this is the guard that says so.
    """
    _drive_a_credential_through_everything(repo)
    body = (repo / STATE_DIR / "ledger.json").read_text(encoding="utf-8")
    json.loads(body)                    # raises if the structure was damaged

    back = Ledger.load(repo)
    assert back.task == "t"
    assert MARK in back.request, back.request
    assert "deploy using token" in back.request, "the surrounding words were eaten"
    assert back.outputs and "line one" in back.outputs[0]["text"]


def test_a_quote_after_a_bearer_token_is_not_eaten(repo):
    """The plain-text half of the same defect, which was quieter.

    `Authorization: Bearer xyz"` lost its closing quote long before any JSON was
    involved; nothing noticed because nothing parsed the result.
    """
    from core.redact import scrub

    got = scrub(f'curl -H "Authorization: Bearer {FAKE}" https://example.invalid')
    assert FAKE not in got
    assert got.count('"') == 2, got
    assert got.endswith("https://example.invalid"), got
