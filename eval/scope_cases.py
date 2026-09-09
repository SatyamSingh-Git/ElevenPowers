"""Cases for the scope guard, written before it was implemented.

The guard's failure mode is not missing a wandering edit. It is questioning a
legitimate one, because a guard that interrupts correct work gets switched off
and then catches nothing at all. So the cases below are weighted heavily toward
edits that look unrelated and are perfectly fine: new files, manifests, tests
for the code being changed, imports in callers.

`ask` here means the host shows the user a prompt. Nothing is ever denied
outright, because the guard is a suspicion and the user is the judge.
"""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class ScopeCase:
    name: str
    request: str
    seen: list[str]            # files read or edited so far, in order
    target: str                # the file about to be edited
    exists: bool               # whether the target is already in the repository
    should_ask: bool
    why: str
    repo: list[str] = field(default_factory=list)   # other files present
    tags: list[str] = field(default_factory=list)


TREE = [
    "src/auth/session.py",
    "src/auth/tokens.py",
    "src/auth/__init__.py",
    "src/billing/invoice.py",
    "src/billing/stripe.py",
    "src/util/dates.py",
    "tests/auth/test_session.py",
    "tests/billing/test_invoice.py",
    "package.json",
    "pyproject.toml",
    "poetry.lock",
    "README.md",
]

CASES: list[ScopeCase] = [
    # ---------- must stay silent ----------
    ScopeCase(
        "first_edit_of_the_task", "fix the session refresh bug",
        seen=[], target="src/auth/session.py", exists=True, should_ask=False,
        why="nothing is established yet, so there is nothing to be outside of",
        repo=TREE,
    ),
    ScopeCase(
        "edit_a_file_already_read", "fix the session refresh bug",
        seen=["src/auth/session.py"], target="src/auth/session.py", exists=True,
        should_ask=False, why="reading then editing is the normal path", repo=TREE,
    ),
    ScopeCase(
        "sibling_in_the_same_module", "fix the session refresh bug",
        seen=["src/auth/session.py"], target="src/auth/tokens.py", exists=True,
        should_ask=False, why="same module as the work already underway", repo=TREE,
    ),
    ScopeCase(
        "package_init_for_a_new_export", "fix the session refresh bug",
        seen=["src/auth/session.py"], target="src/auth/__init__.py", exists=True,
        should_ask=False, why="exporting from the module being changed", repo=TREE,
    ),
    ScopeCase(
        "test_for_the_code_being_changed", "fix the session refresh bug",
        seen=["src/auth/session.py"], target="tests/auth/test_session.py", exists=True,
        should_ask=False, why="the test that covers the change", repo=TREE, tags=["test"],
    ),
    ScopeCase(
        "brand_new_file", "add a rate limiter to auth",
        seen=["src/auth/session.py"], target="src/auth/limiter.py", exists=False,
        should_ask=False, why="creating a file is not wandering", repo=TREE, tags=["create"],
    ),
    ScopeCase(
        "brand_new_test_file", "add a rate limiter to auth",
        seen=["src/auth/session.py"], target="tests/auth/test_limiter.py", exists=False,
        should_ask=False, why="new tests are expected work", repo=TREE, tags=["create"],
    ),
    ScopeCase(
        "manifest_after_adding_a_dependency", "add a rate limiter to auth",
        seen=["src/auth/session.py"], target="pyproject.toml", exists=True,
        should_ask=False, why="manifests change as a consequence of real work",
        repo=TREE, tags=["manifest"],
    ),
    ScopeCase(
        "lockfile", "upgrade the requests dependency",
        seen=["pyproject.toml"], target="poetry.lock", exists=True, should_ask=False,
        why="lockfiles are generated, not wandered into", repo=TREE, tags=["manifest"],
    ),
    ScopeCase(
        "file_named_in_the_request", "fix the invoice total in billing",
        seen=["src/auth/session.py"], target="src/billing/invoice.py", exists=True,
        should_ask=False, why="the request names this area", repo=TREE, tags=["named"],
    ),
    ScopeCase(
        "readme_alongside_a_change", "add a rate limiter to auth",
        seen=["src/auth/session.py"], target="README.md", exists=True, should_ask=False,
        why="documenting the change is not drift", repo=TREE, tags=["docs"],
    ),
    ScopeCase(
        "shared_utility_that_was_read", "fix the session refresh bug",
        seen=["src/auth/session.py", "src/util/dates.py"], target="src/util/dates.py",
        exists=True, should_ask=False, why="read first, so it was a deliberate visit",
        repo=TREE,
    ),

    # ---------- must speak up ----------
    ScopeCase(
        "unrelated_module_never_read", "fix the session refresh bug",
        seen=["src/auth/session.py", "tests/auth/test_session.py"],
        target="src/billing/stripe.py", exists=True, should_ask=True,
        why="a different area of the codebase, never read, unrelated to the request",
        repo=TREE, tags=["drift"],
    ),
    ScopeCase(
        "unrelated_test_never_read", "fix the session refresh bug",
        seen=["src/auth/session.py"], target="tests/billing/test_invoice.py",
        exists=True, should_ask=True,
        why="a test for something else entirely", repo=TREE, tags=["drift"],
    ),
    ScopeCase(
        "wandering_into_a_utility_never_read", "fix the invoice total in billing",
        seen=["src/billing/invoice.py"], target="src/util/dates.py", exists=True,
        should_ask=True,
        why="shared code changed without ever being looked at is how regressions start",
        repo=TREE, tags=["drift"],
    ),

    # ---------- written after the first version passed all of the above ----------
    # Three of these failed on the first run, which is why they are kept.
    ScopeCase(
        "monorepo_other_package", "fix the api handler",
        seen=["packages/api/src/handler.ts"], target="packages/web/src/app.tsx",
        exists=True, should_ask=True,
        why="a different package; the shared word 'packages' says nothing about relatedness",
        tags=["heldout", "drift"],
    ),
    ScopeCase(
        "monorepo_same_package", "fix the api handler",
        seen=["packages/api/src/handler.ts"], target="packages/api/src/router.ts",
        exists=True, should_ask=False, why="same package", tags=["heldout"],
    ),
    ScopeCase(
        "flat_repo_other_file", "fix the parser",
        seen=["parser.py"], target="printer.py", exists=True, should_ask=True,
        why="no directories to compare, so name and request are all there is",
        tags=["heldout", "drift"],
    ),
    ScopeCase(
        "deeply_nested_same_subtree", "fix the encoder",
        seen=["src/media/audio/codec/encoder.py"], target="src/media/audio/codec/frame.py",
        exists=True, should_ask=False, why="same subtree, several levels down", tags=["heldout"],
    ),
    ScopeCase(
        "generic_filename_in_another_module", "fix the session refresh",
        seen=["src/auth/config.py"], target="src/billing/config.py", exists=True,
        should_ask=True,
        why="every module has a config; sharing that name proves nothing",
        tags=["heldout", "drift"],
    ),
    ScopeCase(
        "plural_in_the_request", "refactor the date helpers",
        seen=["src/auth/session.py"], target="src/util/dates.py", exists=True,
        should_ask=False, why="the request names it, in the plural", tags=["heldout"],
    ),
    ScopeCase(
        "request_names_the_module_only", "fix billing",
        seen=["src/auth/session.py"], target="src/billing/invoice.py", exists=True,
        should_ask=False, why="the request names the area if not the file", tags=["heldout"],
    ),
    ScopeCase(
        "workflow_file_never_touched", "fix the session refresh",
        seen=["src/auth/session.py"], target=".github/workflows/ci.yml", exists=True,
        should_ask=True, why="continuous integration config is not part of this task",
        tags=["heldout", "drift"],
    ),
    ScopeCase(
        "camel_case_named_in_request", "fix the userProfile page",
        seen=["src/pages/home.tsx"], target="src/components/UserProfile.tsx", exists=True,
        should_ask=False, why="camel case in the request matches the file name",
        tags=["heldout"],
    ),
    ScopeCase(
        "migration_the_request_asked_for", "add a sessions table migration",
        seen=["src/auth/session.py"], target="migrations/0004_sessions.py", exists=True,
        should_ask=False, why="the request asked for exactly this", tags=["heldout"],
    ),
]
