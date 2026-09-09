"""Hand-labelled prompts, for the judgements behaviour cannot settle.

The behavioural proxy in `eval/prompts.py` scores 3,557 real turns by what they
did, which is the only ground truth available at that scale. It cannot say
whether a particular prompt *should* have carried a claim, only whether work
followed. These cases fill that in.

They are written rather than copied. The corpus is one person's real sessions
across thirty of their own projects, containing resumes, business detail and
server names, and none of that belongs in a public repository. What is taken
from it is the shape of real prompts: how short they are, how often they carry
no subject of their own, and how much of the intent sits in the conversation
rather than in the message.

`should_claim` is about the prompt alone. A prompt that states no subject gets
no claim here and is claimed later by the edit that follows, which is the point
of `Ledger.observe_edit`.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Case:
    name: str
    prompt: str
    should_claim: bool
    claim: str = ""
    why: str = ""


CASES = [
    # --- prompts that plainly ask for work ------------------------------------
    Case("plain_fix", "fix the login redirect loop", True, "bug_fixed",
         "an unambiguous fix request"),
    Case("failing_tests", "the tests are failing on main", True, "bug_fixed",
         "a statement of breakage is a request to fix it"),
    Case("question_shaped_fix", "can you fix the crash on upload?", True, "bug_fixed",
         "a question mark does not make a work request into a question"),
    Case("pasted_error", "TypeError: cannot read property id of undefined at cart.js:44",
         True, "bug_fixed", "a pasted error is a fix request with the detail attached"),
    Case("flaky", "the worker test fails intermittently, sort it out", True, "bug_fixed",
         "intermittency also triggers the stability obligation"),
    Case("feature", "add a retry with backoff to the uploader", True, "feature_added",
         "a plain feature request"),
    Case("implement", "implement pagination on the results endpoint", True, "feature_added", ""),
    Case("refactor", "rename the date helpers and move them into utils", True, "refactor_safe", ""),
    Case("perf", "the export is slow, speed it up", True, "perf_improved", ""),
    Case("migration", "add a migration for the users table", True, "migration_safe",
         "a migration is its own claim even though the word add appears"),
    Case("deps", "bump the express dependency to 5", True, "deps_updated", ""),
    Case("docs", "update the readme with the new install steps", True, "docs_changed",
         "prose work carries no proof obligations, but it is still a claim"),

    # --- prompts that carry no subject of their own ---------------------------
    Case("continue", "continue", False, "",
         "the intent is in the conversation; clearing an open claim here would "
         "switch the gate off mid-task"),
    Case("go_on", "go on", False, "", ""),
    Case("yes_do_it", "yes do it", False, "", ""),
    Case("ok_next", "ok now the other one", False, "", ""),
    Case("see_this", "see this", False, "", "usually precedes a paste"),
    Case("bare_ans", "ans", False, "", "one in five real prompts is four words or fewer"),

    # --- prompts that are explicitly not work ---------------------------------
    Case("what_does", "what does this module do?", False, "", ""),
    Case("why_slow", "why is the dashboard slow?", False, "",
         "asking why something is slow is not claiming to have made it fast"),
    Case("explain", "explain the auth flow", False, "", ""),
    Case("review", "review this file and tell me what you think", False, "", ""),
    Case("investigate", "investigate where the memory goes", False, "",
         "investigation has no completion criterion until it produces a change"),
    Case("compare", "compare these two approaches", False, "", ""),

    # --- statements and context, which the old fallback claimed ---------------
    Case("context_statement", "our team uses pnpm workspaces for this", False, "",
         "context, not a request"),
    Case("deadline", "the client wants this by friday", False, "", ""),
    Case("pasted_config", "here is the current config for reference", False, "", ""),
    Case("apology", "okay start again, sorry about that", False, "",
         "resets the conversation, states no subject"),

    # --- short imperatives that state no subject ------------------------------
    Case("make_it_blue", "make the sidebar collapsible", False, "",
         "no pattern names this, and guessing a claim from any imperative is what "
         "produced a 51 percent over-claim rate; the first edit opens it instead"),
    Case("try_again", "try again", False, "", ""),
    Case("push_it", "now push it", False, "", ""),
]
