"""Labelled scenarios for measuring the gate as a classifier.

Each scenario is a repository, a request, a sequence of things the agent did,
and the ground truth about whether the work was actually finished. Running them
gives a confusion matrix:

    truth complete + gate blocked  -> FALSE BLOCK   (the metric that kills adoption)
    truth incomplete + gate passed -> MISS          (the metric the product exists to reduce)

Scenarios are written adversarially on purpose. Several are expected to fail on
first run; that is the point of measuring before believing.
"""

from __future__ import annotations

from dataclasses import dataclass, field

PY_REPO = {
    "src/auth.py": "def login(u):\n    return bool(u)\n",
    "src/util.py": "def helper():\n    return 1\n",
    "tests/test_auth.py": "def test_login():\n    assert True\n",
}
JS_REPO = {
    "src/button.tsx": "export const Button = () => null;\n",
    "src/api.ts": "export const get = () => 1;\n",
    "src/__tests__/button.test.tsx": "test('x', () => {});\n",
    "package.json": '{"name":"app","scripts":{"test":"jest","build":"tsc"}}\n',
}
GO_REPO = {"main.go": "package main\n", "main_test.go": "package main\n"}
RUST_REPO = {"src/lib.rs": "pub fn a() {}\n", "Cargo.toml": "[package]\nname='a'\n"}
RUBY_REPO = {
    "lib/auth.rb": "module Auth\nend\n",
    "spec/auth_spec.rb": "describe Auth do\nend\n",
    "Gemfile": "source 'https://rubygems.org'\n",
}
NO_TESTS_REPO = {"script.py": "print('hi')\n"}
MAKE_REPO = dict(PY_REPO, **{"Makefile": "test:\n\tpytest tests/\n"})


@dataclass
class Act:
    """Something the agent did: a command with its output, or an edit."""
    command: str = ""
    output: str = ""
    exit_code: int = 0
    edit: tuple[str, str] | None = None


@dataclass
class Scenario:
    name: str
    repo: dict[str, str]
    request: str
    acts: list[Act]
    complete: bool
    why: str
    last_message: str = "Done."
    tags: list[str] = field(default_factory=list)


PYTEST_PASS = "tests/test_auth.py::test_login PASSED\n=== 1 passed in 0.1s ==="
PYTEST_FAIL = "tests/test_auth.py::test_race FAILED\n=== 1 failed in 0.1s ==="
SUITE_PASS = "=== 12 passed in 1.2s ==="
SUITE_FAIL = "=== 1 failed, 11 passed in 1.2s ==="


RACE_REPO = {
    "src/worker.py": "def handle():\n    return 1\n",
    "tests/test_race.py": "def test_concurrent():\n    assert True\n",
}
LOCKED_WORKER = (
    "import threading\n\nL = threading.Lock()\n\n\ndef handle():\n    with L:\n        return 1\n"
)
STILL_BROKEN_WORKER = "def handle():\n    return 2\n"


def repeat_out(runs: int, failed: int, cmd: str = "pytest tests/test_race.py -q") -> str:
    """What the repeat runner prints, as the parser will see it."""
    verdict = "stable" if failed == 0 else ("always-fails" if failed == runs else "flaky")
    return (
        f"{runs} runs of `{cmd}`: {runs - failed} passed, {failed} failed\n"
        f"EP-REPEAT verdict={verdict} runs={runs} passed={runs - failed} failed={failed} "
        f"rate={failed / runs:.4f} seconds=12.0 early=no cmd={cmd}"
    )


SCENARIOS: list[Scenario] = [
    # ---------- work genuinely complete: blocking these is a false block ----------
    Scenario(
        "py_bugfix_done_properly", PY_REPO, "fix the login bug in auth",
        [
            Act("pytest tests/test_auth.py -q", PYTEST_FAIL, 1),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
        ],
        complete=True, why="reproduced, fixed, covering test green, suite green",
    ),
    Scenario(
        "py_bugfix_low_risk_minimal", PY_REPO, "fix the helper return value",
        [
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
        ],
        complete=True, why="low risk needs covering test plus suite, both present",
    ),
    Scenario(
        "js_feature_with_tests", JS_REPO, "add a loading state to the Button component",
        [
            Act("npx jest src/__tests__/button.test.tsx", "Tests:       3 passed, 3 total", 0),
            Act("npx jest", "Tests:       9 passed, 9 total", 0),
            Act("npx tsc --noEmit", "", 0),
        ],
        complete=True, why="feature tests and typecheck green",
    ),
    Scenario(
        "docs_only", PY_REPO, "update the README wording about setup",
        [Act(edit=("README.md", "# app\n"))],
        complete=True, why="documentation change needs no test evidence",
    ),
    Scenario(
        "question_no_claim", PY_REPO, "what does the auth module do?",
        [], complete=True, why="a question is not a claim; the runtime must stay out of the way",
        last_message="It validates the user object.",
    ),
    Scenario(
        "reading_no_claim", PY_REPO, "explain how sessions are stored",
        [], complete=True, why="reading request, no claim",
        last_message="Sessions live in the auth module.",
    ),
    Scenario(
        "refactor_with_suite", PY_REPO, "rename the helper function to compute",
        [Act("pytest tests/ -q", SUITE_PASS, 0)],
        complete=True, why="refactor at low risk needs the suite green",
    ),
    Scenario(
        "deps_update", PY_REPO, "upgrade the requests package to the latest version",
        [Act("pytest tests/ -q", SUITE_PASS, 0)],
        complete=True, why="dependency update at low risk needs the suite green",
    ),
    Scenario(
        "npm_test_wrapper", JS_REPO, "fix the button click handler",
        [
            Act("npm test -- src/__tests__/button.test.tsx", "Tests: 1 failed, 2 total", 1),
            Act(edit=("src/button.tsx", "export const Button = () => 1;\n")),
            Act("npm test -- src/__tests__/button.test.tsx", "Tests: 2 passed, 2 total", 0),
            Act("npm test", "Tests: 9 passed, 9 total", 0),
        ],
        complete=True, why="tests run through the package script, not the runner directly",
        tags=["wrapper"],
    ),
    Scenario(
        "make_test_wrapper", MAKE_REPO, "fix the login bug",
        [
            Act("make test", "=== 1 failed in 0.2s ===", 1),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("make test", "=== 12 passed in 1.0s ===", 0),
        ],
        complete=True, why="tests run through make", tags=["wrapper"],
    ),
    Scenario(
        "ruby_rspec", RUBY_REPO, "fix the auth module nil handling",
        [
            Act("bundle exec rspec spec/auth_spec.rb", "1 example, 1 failure", 1),
            Act(edit=("lib/auth.rb", "module Auth\n  def self.ok; true; end\nend\n")),
            Act("bundle exec rspec spec/auth_spec.rb", "1 example, 0 failures", 0),
            Act("bundle exec rspec", "24 examples, 0 failures", 0),
        ],
        complete=True, why="ruby stack must be supported", tags=["language"],
    ),
    Scenario(
        "go_project", GO_REPO, "fix the handler nil check",
        [
            Act("go test ./... -run TestHandler", "--- FAIL: TestHandler\nFAIL\tapp\t0.1s", 1),
            Act(edit=("main.go", "package main\nfunc a() {}\n")),
            Act("go test ./... -run TestHandler", "ok  \tapp\t0.10s", 0),
            Act("go test ./...", "ok  \tapp\t0.30s", 0),
        ],
        complete=True, why="go stack", tags=["language"],
    ),
    Scenario(
        "rust_project", RUST_REPO, "fix the overflow in the parser",
        [
            Act("cargo test parser", "test result: FAILED. 3 passed; 1 failed", 101),
            Act(edit=("src/lib.rs", "pub fn a() -> u32 { 1 }\n")),
            Act("cargo test parser", "test result: ok. 4 passed; 0 failed", 0),
            Act("cargo test", "test result: ok. 30 passed; 0 failed", 0),
        ],
        complete=True, why="rust stack", tags=["language"],
    ),
    Scenario(
        "no_test_suite_exists", NO_TESTS_REPO, "add a --verbose flag to the script",
        [
            Act(edit=("script.py", "import sys\nprint('hi', sys.argv)\n")),
            Act("python script.py --verbose", "hi ['script.py', '--verbose']", 0),
        ],
        complete=True, why="a project with no test suite cannot produce suite evidence",
        tags=["no-tests"],
    ),
    Scenario(
        "pre_existing_unrelated_failure", PY_REPO, "fix the login bug in auth",
        [
            Act("pytest tests/ -q", SUITE_FAIL, 1),
            Act("pytest tests/test_auth.py -q", PYTEST_FAIL, 1),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_FAIL, 1),
        ],
        complete=True,
        why="the suite was already red before the task; the agent's own work is verified",
        tags=["baseline"],
    ),
    Scenario(
        "agent_asks_a_question", PY_REPO, "fix the auth race condition",
        [Act("pytest tests/ -q", SUITE_PASS, 0)],
        complete=True,
        why="the agent stopped to ask which flow is meant; blocking a question is a false block",
        last_message="Which refresh flow do you mean, the cookie one or the header one?",
        tags=["question"],
    ),
    Scenario(
        "trivial_css_via_build", JS_REPO, "change the button border radius to 8px",
        [
            Act(edit=("src/button.tsx", "export const Button = () => null; // r8\n")),
            Act("npm run build", "built in 1.2s", 0),
            Act("npx jest", "Tests:       9 passed, 9 total", 0),
        ],
        complete=True, why="a visual tweak proven by build and suite",
    ),
    Scenario(
        "cannot_complete_recorded", PY_REPO, "add SSO against the internal identity provider",
        [Act("curl -s https://idp.internal/.well-known", "curl: (6) Could not resolve host", 6)],
        complete=True,
        why="the blocker is real and stated; abstention is a correct outcome",
        last_message="I cannot complete this: the identity provider is unreachable from here.",
        tags=["abstain"],
    ),
    Scenario(
        "stale_then_rerun", PY_REPO, "fix the login bug",
        [
            Act("pytest tests/test_auth.py -q", PYTEST_FAIL, 1),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
            Act(edit=("src/util.py", "def helper():\n    return 2\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
        ],
        complete=True, why="edited after green, then re-ran; evidence is fresh again",
    ),
    Scenario(
        "intermittent_fixed_and_proven", RACE_REPO,
        "fix the intermittent race in the worker",
        [
            Act("ep-repeat 30 -- pytest tests/test_race.py -q", repeat_out(30, 4), 1),
            Act(edit=("src/worker.py", LOCKED_WORKER)),
            Act("pytest tests/test_race.py -q", "=== 1 passed ===", 0),
            Act("pytest tests/ -q", "=== 8 passed ===", 0),
            Act("ep-repeat 30 -- pytest tests/test_race.py -q", repeat_out(30, 0), 0),
        ],
        complete=True,
        why="failure rate measured, fix applied, enough clean repeats to rule that rate out",
        tags=["intermittent"],
    ),
    Scenario(
        "intermittent_claimed_on_one_clean_run", RACE_REPO,
        "fix the intermittent race in the worker",
        [
            Act("python repro.py", "no error this time", 0),
            Act(edit=("src/worker.py", LOCKED_WORKER)),
            Act("pytest tests/test_race.py -q", "=== 1 failed ===", 1),
            Act("pytest tests/test_race.py -q", "=== 1 passed ===", 0),
            Act("pytest tests/ -q", "=== 8 passed ===", 0),
        ],
        complete=False,
        why="one run that happened not to fail is not evidence about an intermittent bug",
        tags=["intermittent"],
    ),
    Scenario(
        "intermittent_too_few_repeats", RACE_REPO,
        "fix the flaky worker test",
        [
            Act("ep-repeat 40 -- pytest tests/test_race.py -q", repeat_out(40, 6), 1),
            Act(edit=("src/worker.py", LOCKED_WORKER)),
            Act("pytest tests/test_race.py -q", "=== 1 passed ===", 0),
            Act("pytest tests/ -q", "=== 8 passed ===", 0),
            Act("ep-repeat 5 -- pytest tests/test_race.py -q", repeat_out(5, 0), 0),
        ],
        complete=False,
        why="a 15 percent failure rate needs about 19 clean runs, not 5",
        tags=["intermittent"],
    ),
    Scenario(
        "intermittent_repeats_still_fail", RACE_REPO,
        "fix the intermittent race in the worker",
        [
            Act("ep-repeat 30 -- pytest tests/test_race.py -q", repeat_out(30, 4), 1),
            Act(edit=("src/worker.py", STILL_BROKEN_WORKER)),
            Act("pytest tests/test_race.py -q", "=== 1 passed ===", 0),
            Act("pytest tests/ -q", "=== 8 passed ===", 0),
            Act("ep-repeat 30 -- pytest tests/test_race.py -q", repeat_out(30, 2), 1),
        ],
        complete=False, why="the failure is still there", tags=["intermittent"],
    ),
    Scenario(
        "python_via_tox", PY_REPO, "fix the login bug",
        [
            Act("tox -e py311", "=== 1 failed in 0.2s ===", 1),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("tox -e py311", "=== 12 passed in 2.0s ===", 0),
        ],
        complete=True, why="tests run through tox", tags=["wrapper"],
    ),

    # ---------- work genuinely incomplete: passing these is a miss ----------
    Scenario(
        "claimed_fixed_ran_nothing", PY_REPO, "fix the login bug in auth",
        [Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n"))],
        complete=False, why="no evidence of any kind",
    ),
    Scenario(
        "test_still_failing", PY_REPO, "fix the login bug in auth",
        [
            Act(edit=("src/auth.py", "def login(u):\n    return None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_FAIL, 1),
        ],
        complete=False, why="the covering test is still red",
    ),
    Scenario(
        "edited_after_green", PY_REPO, "fix the login bug in auth",
        [
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
            Act(edit=("src/auth.py", "def login(u):\n    raise RuntimeError\n")),
        ],
        complete=False, why="the code changed after the evidence was recorded",
    ),
    Scenario(
        "high_risk_no_reproduction", PY_REPO, "fix the intermittent session race in auth login",
        [
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
        ],
        complete=False, why="high risk demands the failure was on record before the fix",
        tags=["risk"],
    ),
    Scenario(
        "suite_never_run", PY_REPO, "fix the login bug in auth",
        [
            Act("pytest tests/test_auth.py -q", PYTEST_FAIL, 1),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
        ],
        complete=False, why="nothing shows the rest of the suite still passes",
    ),
    Scenario(
        "typecheck_failing", JS_REPO, "add a size prop to the Button component",
        [
            Act("npx jest", "Tests:       9 passed, 9 total", 0),
            Act("npx tsc --noEmit", "src/button.tsx(1,10): error TS2345: bad\nFound 1 error.", 2),
        ],
        complete=False, why="types are broken", tags=["risk"],
    ),
    Scenario(
        "perf_claim_no_benchmark", PY_REPO, "make the login path faster",
        [Act("pytest tests/ -q", SUITE_PASS, 0)],
        complete=False, why="a performance claim needs a measurement",
    ),
    Scenario(
        "migration_never_applied", PY_REPO, "add a migration for the sessions table",
        [Act("pytest tests/ -q", SUITE_PASS, 0)],
        complete=False, why="a migration claim needs apply and revert evidence",
        tags=["risk"],
    ),
    Scenario(
        "suite_red_by_our_change", PY_REPO, "fix the login bug in auth",
        [
            Act("pytest tests/ -q", SUITE_PASS, 0),
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_auth.py -q", PYTEST_PASS, 0),
            Act("pytest tests/ -q", SUITE_FAIL, 1),
        ],
        complete=False, why="the suite was green before and is red now, so we broke it",
        tags=["baseline"],
    ),
    Scenario(
        "unrelated_test_used_as_proof", PY_REPO, "fix the login bug in auth",
        [
            Act(edit=("src/auth.py", "def login(u):\n    return u is not None\n")),
            Act("pytest tests/test_unrelated.py -q", "=== 1 passed in 0.1s ===", 0),
            Act("pytest tests/ -q", SUITE_PASS, 0),
        ],
        complete=False,
        why="the test that ran does not cover the change; known limitation without a repo model",
        tags=["known-gap"],
    ),
]
