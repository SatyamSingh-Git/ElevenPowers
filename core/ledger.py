"""The task ledger and the completion state computed from it.

The ledger is the external task state: which claims are open, what evidence has
been captured, and which files the task is allowed to touch. It lives on disk so
it survives compaction, resumption and a change of host.
"""

from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

from .claims import opens_new_task
from .config import Config, load as load_config
from .evidence import Evidence, Freshness, Kind, Result
from .intent import is_abstention, is_question
from .obligations import Claim, Obligation, Risk, _demonstrated_fix, obligations_for, risk_of
from .redact import scrub
from .repeat import MAX_RUNS, MIN_RUNS, rules_out, runs_needed
from .scope import is_manifest, is_prose, normalise
from .surface import TEST_NAME, Surface, declares_a_test, detect

STATE_DIR = ".elevenpowers"

# Said on a reproduction established only at suite grain. Measured on the B3
# sweep: 7 of 7 reproductions came this way and 0 from a named test, because the
# targeted path needs a *passing* record carrying a node id and `pytest -q`
# prints passes as dots. Left unsaid, the report shows two obligations
# discharged where one base-tree run established a single fact.
SUITE_GRAIN = ("suite-level: the declared check failed on the base tree and passes now. "
               "No individual test was seen red there and green here, so this is the "
               "same run that decided discrimination, not a second finding")


class Status(str, Enum):
    VERIFIED = "VERIFIED"
    UNVERIFIED = "UNVERIFIED"
    CONTRADICTED = "CONTRADICTED"
    STALE = "STALE"


def _keep_out_of_git(state: Path) -> None:
    """Make the state directory ignore itself.

    This directory holds the user's prompt, every command string, and - since
    the assumption check - a bounded amount of what those commands printed. A
    repository that has never heard of this plugin does not ignore it, and
    `git add -A` would commit the lot.

    A `.gitignore` containing `*` inside the directory ignores everything in it
    whatever the repository's own ignore file says. It needs no edit to a file
    the user owns, protects the whole directory rather than the one field that
    prompted the question, and leaves the uninstall story intact: the directory
    is still the only thing to delete.
    """
    marker = state / ".gitignore"
    if marker.exists():
        return
    try:
        marker.write_text("*\n", encoding="utf-8")
    except OSError:
        pass                      # never fail a save over housekeeping


def _appended(disk: list, mine: list, key) -> list:
    """Everything on disk, plus whatever of mine is not already there."""
    out = list(disk)
    known = {key(item) for item in disk}
    for item in mine:
        if key(item) not in known:
            known.add(key(item))
            out.append(item)
    return out


@dataclass
class Check:
    obligation: Obligation
    met: bool
    evidence: Evidence | None = None
    freshness: Freshness | None = None
    caveat: str = ""


@dataclass
class Verdict:
    claim: Claim
    risk: Risk
    status: Status
    checks: list[Check]

    @property
    def missing(self) -> list[Check]:
        return [c for c in self.checks if not c.met]

    @property
    def stale(self) -> list[Check]:
        """Met, but no longer speaking for the repository as it is now.

        `GONE` belongs here as much as `STALE` does. Rejecting only `STALE` left
        a claim verified by a test result whose files had been deleted — the
        strongest possible form of out of date.
        """
        return [c for c in self.checks
                if c.met and c.freshness in (Freshness.STALE, Freshness.GONE)]


@dataclass
class Ledger:
    root: Path
    task: str = ""
    request: str = ""
    claims: list[Claim] = field(default_factory=list)
    risk: Risk = Risk.LOW
    domains: list[str] = field(default_factory=list)
    touched: list[str] = field(default_factory=list)
    seen: list[str] = field(default_factory=list)
    evidence: list[Evidence] = field(default_factory=list)
    decisions: list[dict] = field(default_factory=list)
    blocks: int = 0
    guided: bool = False
    created: float = field(default_factory=time.time)
    base: str = ""
    """The commit this task started from, captured before anything was edited.

    Recorded at task open rather than read on demand, because an agent that
    commits mid-task would otherwise move the thing its own work is compared
    against, and `core/stress.py` would be asking whether the change
    discriminates from itself.
    """
    outputs: list = field(default_factory=list)
    """A bounded record of what commands actually printed, head and tail.

    Kept so that `core/assumptions.py` can ask whether a pattern this task
    introduced ever matched anything the task really saw. `Evidence.detail`
    holds only the last three lines, which is a summary rather than the text a
    pattern would have to match.

    Bounded on purpose: twelve commands, eight thousand characters each, split
    between the start and the end because a runner's summary is at the bottom
    and its header at the top. It never leaves the machine.
    """
    opened_dirty: list[str] = field(default_factory=list)
    """Paths already modified when this task opened, so they are not its work.

    A real repository is never clean. Without this, every uncommitted file a
    developer already had in flight is attributed to whatever they ask next: it
    raises the risk tier, it demands obligations for code the task never
    touched, and it feeds `core/radius.py` a blast radius computed from
    somebody else's half-finished work. Measured on a probe, a task that edited
    one file was credited with four.
    """
    failed_before: list = field(default_factory=list)
    """Test identities that were already red on the tree this task started from.

    A test failing there and passing now is a **reproduction**, and this is what
    lets the runtime establish that by computation rather than by hoping the
    agent ran the test before it wrote the fix. Writing the test afterwards is
    ordinary practice and was previously an obligation nobody could discharge.
    """
    briefed: list[str] = field(default_factory=list)
    """Files whose architecture brief has actually been emitted.

    Delivery, not observation. The brief was gated on `seen`, which records
    reads as well as edits - so the ordinary Read-then-Edit workflow marked the
    file seen first and the note intended for the edit never appeared. An audit
    measured it: emitted on a direct edit, silent after a read. The feature was
    suppressed by the most common way anyone works.
    """
    passed_before: list = field(default_factory=list)
    """Test identities observed **passing** on the tree this task started from.

    Kept because absence of a failure is not a pass. `vacuous_tests` used to
    report any new test that was missing from `failed_before`, and a test can be
    missing from that list for reasons that say nothing at all: it was skipped,
    deselected, never reached under fail-fast, or the run died before it. An
    audit reported a test as vacuous on exactly that inference. Accusing correct
    work is the one thing these checks must not do, so the claim now needs the
    positive observation rather than the absent negative one.
    """
    discrimination: dict = field(default_factory=dict)
    """Per declared need: did that check pass before the change, or not?

    Cached because the base does not move while a task runs, so a declared
    command is run against the old tree once rather than at every stop.
    """
    discrimination_inputs: dict = field(default_factory=dict)
    """Per declared need: a fingerprint of everything that answer depended on.

    The base commit does not move, which is what the cache above was justified
    by - but the *tests carried onto* that base do, and they are the other half
    of the question. An audit cached a non-discriminating verdict, then changed
    the implementation and the test, and a fresh control run on the old tree
    failed while the cached answer still said the check could not fail.

    So the key is the base, the command and the content of the carried test
    files. Unchanged inputs reuse the answer; an edited test asks again.
    """
    _surface: Surface | None = None
    _config: Config | None = None

    @property
    def config(self) -> Config:
        if self._config is None:
            self._config = load_config(self.root)
        return self._config

    @property
    def surface(self) -> Surface:
        """What this project can prove, from a file scan plus what has been seen.

        Evidence outranks the scan: if a test command has actually produced a
        record, the project has tests whatever the layout looks like. Without
        this, an unusual directory structure silently makes every obligation
        unreachable.
        """
        if self._surface is None:
            found = detect(self.root)
            kinds = {e.kind for e in self.evidence}
            declared = self.config
            self._surface = Surface(
                tests=found.tests or bool(kinds & {Kind.TEST, Kind.SUITE}) or declared.declares("tests"),
                typecheck=found.typecheck or Kind.TYPECHECK in kinds or declared.declares("typecheck"),
                build=found.build or Kind.BUILD in kinds or declared.declares("build"),
                benchmark=found.benchmark or Kind.BENCHMARK in kinds or declared.declares("benchmark"),
            )
        return self._surface

    @property
    def path(self) -> Path:
        return self.root / STATE_DIR / "ledger.json"

    @classmethod
    def load(cls, root: Path) -> "Ledger":
        path = root / STATE_DIR / "ledger.json"
        if not path.exists():
            return cls(root=root)
        raw = json.loads(path.read_text(encoding="utf-8"))
        return cls(
            root=root,
            task=raw.get("task", ""),
            request=raw.get("request", ""),
            claims=[Claim(c) for c in raw.get("claims", [])],
            risk=Risk(raw.get("risk", "low")),
            domains=raw.get("domains", []),
            touched=raw.get("touched", []),
            seen=raw.get("seen", []),
            evidence=[Evidence.from_dict(e) for e in raw.get("evidence", [])],
            decisions=raw.get("decisions", []),
            blocks=raw.get("blocks", 0),
            guided=raw.get("guided", False),
            created=raw.get("created", time.time()),
            base=raw.get("base", ""),
            outputs=raw.get("outputs", []) or [],
            opened_dirty=raw.get("opened_dirty", []) or [],
            failed_before=raw.get("failed_before", []) or [],
            passed_before=raw.get("passed_before", []) or [],
            briefed=raw.get("briefed", []) or [],
            discrimination_inputs=raw.get("discrimination_inputs", {}) or {},
            discrimination=raw.get("discrimination", {}) or {},
        )

    def save(self) -> None:
        """Write the ledger, keeping anything another writer appended meanwhile.

        Atomic replacement stops a half-written file. It does not make
        read-modify-write transactional, and two handlers for the same session
        do exactly that: both load, both append, and the second write drops the
        first one's work silently. The append-only fields are merged against
        whatever is on disk at the moment of writing, which is the cheap half of
        what a real transaction would buy and covers the case that actually
        happens here.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        _keep_out_of_git(self.path.parent)
        self._keep_concurrent_appends()
        payload = {
            "task": self.task,
            "request": self.request,
            "claims": [c.value for c in self.claims],
            "risk": self.risk.value,
            "domains": self.domains,
            "touched": self.touched,
            "seen": self.seen,
            "evidence": [e.to_dict() for e in self.evidence],
            "decisions": self.decisions,
            "blocks": self.blocks,
            "guided": self.guided,
            "created": self.created,
            "base": self.base,
            "outputs": self.outputs,
            "opened_dirty": self.opened_dirty,
            "failed_before": self.failed_before,
            "passed_before": self.passed_before,
            "briefed": self.briefed,
            "discrimination_inputs": self.discrimination_inputs,
            "discrimination": self.discrimination,
            # Written for diagnosis, never read back. `stress` declines when a
            # project declares no command, and on the B3 sweep that gate could
            # not be told apart from the others afterwards, because the config
            # lived only on disk in a workspace that no longer exists. A bundle
            # that cannot say which gate closed cannot explain its own result.
            # Deliberately not restored by `load`: the config on disk is the
            # truth about a repository now, and a snapshot of what it said
            # yesterday must never quietly override it.
            "config": {"profile": self.config.profile,
                       "commands": dict(self.config.commands)},
        }
        # Named per process: a shared temporary file is its own race, where two
        # writers interleave into one buffer and the winner replaces with a
        # mixture of both.
        tmp = self.path.with_suffix(f".{os.getpid()}.tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _keep_concurrent_appends(self) -> None:
        if not self.path.exists():
            return
        try:
            disk = Ledger.load(self.root)
        except (json.JSONDecodeError, OSError, ValueError):
            return          # unreadable: this write is the repair
        if disk.task != self.task:
            return          # a different task; its history is not ours to carry
        self.decisions = _appended(disk.decisions, self.decisions,
                                   lambda d: json.dumps(d, sort_keys=True))
        self.evidence = _appended(disk.evidence, self.evidence,
                                  lambda e: json.dumps(e.to_dict(), sort_keys=True))
        self.seen = sorted(set(disk.seen) | set(self.seen))
        self.touched = sorted(set(disk.touched) | set(self.touched))
        self.blocks = max(disk.blocks, self.blocks)

    def add(self, records: list[Evidence]) -> None:
        self.evidence.extend(records)
        self._surface = None

    def saw(self, path: str) -> None:
        """Record that the task has looked at or changed a file."""
        rel = normalise(path, self.root)
        if rel and rel not in self.seen:
            self.seen.append(rel)

    def observe_edit(self, path: str) -> None:
        """Record an edit, and open a claim if the task never stated one.

        Deriving the claim from what a task does rather than only from what was
        asked is the same move the scope guard makes, for the same reason: one
        real prompt in five is four words or fewer, and the intent for those
        lives in the conversation. A prompt that explicitly asked for something
        other than a change is left alone, so answering a question does not
        become a claim because a note was edited along the way.
        """
        rel = normalise(path, self.root)
        self.saw(rel)
        # An edit is a fact about the task whatever claim is already open.
        # Recording it only on the path that opens one meant every later edit
        # was invisible: a task that started on a README and then reached into
        # `src/auth/` kept the risk the README earned it.
        self.touched = sorted(set(self.touched) | {rel})
        self.risk, self.domains = risk_of(self.touched, self.request)
        if self.claims or not self.request or opens_new_task(self.request):
            return
        if is_manifest(rel) or is_prose(rel):
            return
        self.claims = [Claim.FEATURE_ADDED]
        self.note("claim opened by an edit", f"{rel} changed with no claim stated")

    def saw_output(self, command: str, text: str) -> None:
        """Remember enough of what a command printed to check a claim about it.

        Head and tail, because a runner puts its header at the top and its
        summary at the bottom, and the middle is the part nobody writes a
        pattern for.

        Credentials are removed first. This is the only place output enters the
        file, so it is the only place that has to do it.
        """
        keep = 4000
        if len(text) <= keep * 2:
            body = text
        else:
            body = text[:keep] + "\n[...]\n" + text[-keep:]
        body = scrub(body)
        self.outputs = (self.outputs + [{"command": scrub(command[:200]), "text": body}])[-12:]

    def note(self, what: str, why: str) -> None:
        self.decisions.append({"what": what, "why": why, "at": time.time()})

    def settle(self, last_message: str = "") -> Status:
        """The completion state, given what the agent just said.

        Two readings of the final message change the answer. A question is not a
        completion claim, so gating it would force the agent to guess rather
        than wait. A stated blocker converts the task to an abstention, whose
        obligation is the reason itself, because a system with no way to accept
        "this cannot be done as asked" pushes the agent into inventing a result.
        """
        if is_question(last_message):
            return Status.VERIFIED
        if last_message and is_abstention(last_message) and self.claims:
            if self.claims != [Claim.CANNOT_COMPLETE]:
                self.claims = [Claim.CANNOT_COMPLETE]
                self.add([Evidence(
                    kind=Kind.DIFF, identity="stated-blocker", result=Result.PASS,
                    observed=[], tree="", detail=last_message.strip()[:400], at=time.time(),
                )])
        return self.status()

    def verdicts(self) -> list[Verdict]:
        return [self._verdict(claim) for claim in self.claims]

    def status(self) -> Status:
        verdicts = self.verdicts()
        if not verdicts:
            return Status.VERIFIED
        order = [Status.CONTRADICTED, Status.UNVERIFIED, Status.STALE, Status.VERIFIED]
        return min((v.status for v in verdicts), key=order.index)

    def _verdict(self, claim: Claim) -> Verdict:
        checks: list[Check] = []
        for obligation in obligations_for(claim, self.risk, self.surface, self.request):
            checks.append(self._check(obligation))

        if self._contradictions():
            status = Status.CONTRADICTED
        elif any(not c.met for c in checks):
            status = Status.UNVERIFIED
        elif any(c.freshness in (Freshness.STALE, Freshness.GONE) for c in checks):
            status = Status.STALE
        else:
            status = Status.VERIFIED
        return Verdict(claim=claim, risk=self.risk, status=status, checks=checks)

    def _contradictions(self) -> list[Evidence]:
        """Evidence that is failing now and was not already failing at the start.

        Two rules, both learned by measurement. Only the most recent record for
        an identity counts, so a test that failed and was then fixed reads as
        reproduction rather than contradiction. And an identity whose first
        observation in this task was already failing is pre-existing breakage:
        plenty of real repositories have a red test on the main branch, and
        blaming the agent for it blocks every task on such a repository.
        """
        first: dict[tuple, Evidence] = {}
        latest: dict[tuple, Evidence] = {}
        for e in self.evidence:
            key = (e.kind, e.identity)
            if key not in first or e.at < first[key].at:
                first[key] = e
            if key not in latest or e.at >= latest[key].at:
                latest[key] = e
        return [
            e for key, e in latest.items()
            if e.result is not Result.PASS
            and first[key].result is Result.PASS
            and e.freshness(self.root) is Freshness.FRESH
        ]

    def pre_existing(self) -> list[Evidence]:
        """Failures that were already there when the task started.

        Stability measurements are excluded: a repeat run that found the bug is
        the reproduction the task exists to fix, not somebody else's breakage.
        """
        first: dict[tuple, Evidence] = {}
        for e in self.evidence:
            if e.kind is Kind.STABILITY:
                continue
            key = (e.kind, e.identity)
            if key not in first or e.at < first[key].at:
                first[key] = e
        return [e for e in first.values() if e.result is not Result.PASS]

    def _check(self, obligation: Obligation) -> Check:
        if obligation.require_prior_failure:
            relevant = [e for e in self.evidence if obligation.matches(e)]
            failed = [e for e in relevant if e.result is Result.FAIL]
            passed = [e for e in relevant if e.result is Result.PASS]
            if failed and passed and min(f.at for f in failed) < max(p.at for p in passed):
                return Check(obligation=obligation, met=True, evidence=failed[0])
            # Where tests only run through an opaque wrapper there is no scoped
            # record to point at, but a target going from red to green is the
            # reproduction by any other name.
            shown = _demonstrated_fix(self.evidence)
            grain = ""
            if shown is None:
                # The agent did not happen to run it red first, so ask the old
                # tree directly. A test that was failing there and passes now is
                # a reproduction however the work was ordered, and demanding the
                # ordering blocked agents who wrote the test after the fix -
                # which is ordinary practice, not a mistake.
                shown, grain = self._reproduction()
            return Check(obligation=obligation, met=shown is not None, evidence=shown,
                         caveat=grain)

        if obligation.kind is Kind.STABILITY:
            return self._check_stability(obligation)

        found = obligation.satisfied_by(self.evidence)
        if found is not None:
            return Check(obligation=obligation, met=True, evidence=found,
                         freshness=found.freshness(self.root))

        written = self._test_written_and_suite_green(obligation)
        if written is not None:
            return Check(obligation=obligation, met=True, evidence=written,
                         freshness=written.freshness(self.root),
                         caveat="a test was written and the suite that runs it passed")

        tolerated = self._no_new_failures(obligation)
        if tolerated is not None:
            return Check(obligation=obligation, met=True, evidence=tolerated,
                         freshness=tolerated.freshness(self.root), caveat="no new failures")
        return Check(obligation=obligation, met=False)

    def required_runs(self) -> int:
        """How many clean runs would justify calling an intermittent bug fixed.

        Derived from the worst failure rate this task actually observed, so the
        answer is arithmetic rather than a guess. With nothing observed, fall
        back to the floor and say so.
        """
        rates = [
            e.failed / e.runs
            for e in self.evidence
            if e.kind is Kind.STABILITY and e.runs and e.failed
        ]
        return runs_needed(max(rates)) if rates else MIN_RUNS

    def _reproduced_on_base(self) -> Evidence | None:
        return self._reproduction()[0]

    def _reproduction(self) -> tuple[Evidence | None, str]:
        """A now-passing check that was already failing before this task began,
        and **how coarsely** that was established.

        The grain matters, and measuring it is what showed why. Across the eight
        B3 runs where the base tree was asked, **seven of seven** reproductions
        came from the suite path below and **zero** from the targeted one. The
        targeted path needs a *passing* record carrying a node id, and `pytest
        -q` prints passes as dots - the parsers hold 1,256 failing node records
        against four passing ones - so it is starved by construction.

        The consequence is worth stating plainly rather than leaving implied: on
        real runs this obligation is currently satisfied by the same single
        base-tree run that decides §5.10, so `reproduced` and `discriminates`
        are one fact reported twice. Saying so in the caveat is honest;
        presenting them as two independently discharged obligations is not.

        **Suites count, and they are the common case.** The parsers record
        individual nodes mainly when they *fail* — across every preserved
        ledger there are 1,256 failing test records and four passing ones,
        because `pytest -q` lists failures by name and passes as dots. A version
        matching only node identities engaged on 1.4% of saved runs, which
        `_demonstrated_fix` would have warned about: it has always accepted
        `Kind.SUITE` as well, for exactly this reason.

        For a suite the identity is the command's scope rather than a node, so
        it cannot be matched against node ids. It does not need to be: §5.10
        already asked whether that declared check passed on the old tree, and
        `DISCRIMINATES` means it did not. A suite red back there and green now
        is the same proof at coarser grain.
        """
        from .stress import DISCRIMINATES

        # Targeted FIRST. A named test that was red on the base tree and passes
        # here is strictly better evidence than "the suite did not pass back
        # there", and asking the suite first meant `stress.confirm`'s records
        # were computed and then never reached - all sixteen rehearsed tasks
        # still reported suite grain with the targeted records sitting in the
        # ledger unread.
        red = set(self.failed_before)
        if red:
            # A whole file that would not collect back there has no node id, so
            # a node now passing inside it counts. `tests/test_new.py` against
            # `tests/test_new.py::test_mul` is the ordinary shape of a fix that
            # introduces the thing the test imports.
            files = {p for p in red if p.endswith(".py")}

            def was_red(identity: str) -> bool:
                here = identity.replace("\\", "/")
                return identity in red or any(here.startswith(f) for f in files)

            passing = [e for e in self.evidence
                       if e.kind is Kind.TEST and e.result is Result.PASS
                       and was_red(e.identity)
                       and e.freshness(self.root) is Freshness.FRESH]
            if passing:
                return passing[-1], ""

        # Otherwise the coarse reading, which is still a true one. Not
        # `e.command == the declared string`: that is the same exact-match
        # mistake `stress._passing` made, and wrong here for the same reason -
        # agents run their own invocation, so no record carries the declared
        # text. What `DISCRIMINATES` establishes is that the project's suite did
        # *not* pass on the old tree; a fresh passing suite record is the claim
        # that it passes now. Together those are red-then-green, at suite grain.
        #
        # The *tests* check, not any check. `discrimination` is keyed by kind,
        # and reading it with `in .values()` let a discriminating **typecheck**
        # pair with a passing **test suite** and be reported as one red-then-
        # green fact. An audit built exactly that: two observations of two
        # different things, joined because both were true. A reproduction is a
        # claim about one check, so both halves have to be about that check.
        if self.discrimination.get("tests") == DISCRIMINATES:
            suites = [e for e in self.evidence
                      if e.kind is Kind.SUITE and e.result is Result.PASS
                      and e.freshness(self.root) is Freshness.FRESH]
            if suites:
                return suites[-1], SUITE_GRAIN
        return None, ""

    def _check_stability(self, obligation: Obligation) -> Check:
        """Stability needs enough clean repeats, not one lucky run.

        A single successful execution is indistinguishable from a hundred of
        them unless something counted, so this is the one obligation that
        requires its own tool.
        """
        records = [e for e in self.evidence if e.kind is Kind.STABILITY]
        if not records:
            return Check(obligation=obligation, met=False)

        # Bound to what actually failed here. Any stability record would do
        # before, so three hundred clean repeats of `python -c pass` certified a
        # flaky test: nothing asked what had been repeated. The match is by name
        # because the record carries the command it repeated and not the target
        # it was aimed at, which is the sharper fix and a larger one.
        failed_here = {e.identity for e in self.evidence if e.result is not Result.PASS}
        records = [e for e in records
                   if any(t and (t in e.identity or t in e.command) for t in failed_here)]
        if not records:
            return Check(obligation=obligation, met=False,
                         caveat="no repeated run names a target that failed here")

        needed = self.required_runs()
        if needed > MAX_RUNS:
            # Insufficient evidence, not a smaller sample. A budget that cannot
            # buy the confidence says so.
            return Check(
                obligation=obligation, met=False,
                evidence=max(records, key=lambda e: e.runs),
                caveat=(f"{needed} clean runs needed at the rate observed, past the "
                        f"{MAX_RUNS}-run budget; {MAX_RUNS} clean runs rule out only "
                        f"{rules_out(MAX_RUNS):.2%}"),
            )
        clean = [e for e in records if e.failed == 0 and e.runs >= needed]
        if clean:
            best = max(clean, key=lambda e: e.runs)
            return Check(obligation=obligation, met=True, evidence=best,
                         freshness=best.freshness(self.root))

        best = max(records, key=lambda e: (e.failed == 0, e.runs))
        short = best.failed == 0 and best.runs < needed
        return Check(
            obligation=obligation, met=False, evidence=best,
            caveat=(f"{best.runs} clean runs, {needed} needed" if short
                    else f"still failed {best.failed} of {best.runs}"),
        )

    def _test_written_and_suite_green(self, obligation: Obligation) -> Evidence | None:
        """This task wrote a test, and the suite that contains it passed.

        A whole-suite run produces no per-test record, so an agent that writes a
        covering test and then runs everything cannot discharge a scoped
        obligation. That described three quarters of the runs the gate blocked
        in live measurement, in every one of which a test file had been edited.

        Watching the task write a test and the suite go green is the same proof
        by a different route, which is the argument that already admits a
        red-to-green transition. It is weaker than a named passing test, so it
        is reported with the caveat rather than silently.
        """
        if not obligation.scoped or obligation.kind is not Kind.TEST:
            return None
        # Written, not read. `seen` includes files the agent merely opened, so
        # reading an existing test and running a green suite satisfied "a test
        # covering the change passes" — with a caveat that said a test had been
        # written. Nuisance blocking is not a reason to upgrade weaker evidence
        # into a stronger claim.
        #
        # The file must also still declare a test. Emptying one is how a suite
        # goes green without the bug being fixed, and the held-out scenarios
        # caught exactly that the first time this rule was written without it.
        if not any(TEST_NAME.search(p) and declares_a_test(self.root / p)
                   for p in self.touched):
            return None
        green = [
            e for e in self.evidence
            if e.kind is Kind.SUITE and e.result is Result.PASS and e.ran_tests
            and not Obligation._is_scoped(e)
        ]
        return green[-1] if green else None

    def _no_new_failures(self, obligation: Obligation) -> Evidence | None:
        """A suite that was already red and is no redder than before.

        Some repositories are red on their main branch. Demanding a green suite
        there makes every task impossible, so the standard becomes the one the
        agent can actually meet: introduce no new failures. This mirrors the
        way linters are applied to agent edits, counting only errors the change
        itself added.
        """
        if not obligation.broad:
            return None
        runs = [e for e in self.evidence if obligation.matches(e)]
        if len(runs) < 2:
            return None
        runs.sort(key=lambda e: e.at)
        first, last = runs[0], runs[-1]
        if first.result is Result.PASS or last.result is Result.PASS:
            return None
        # Which tests failed, not how many. A suite that swapped an old failure
        # for a new one keeps its count and has regressed, and counting alone
        # cannot tell those apart. Where the runner reported no per-test detail
        # there is nothing to compare, and the concession is refused rather than
        # granted on a number that cannot support it.
        was, now = self._failing_tests(first.at), self._failing_tests(last.at)
        if not was or not now or now - was:
            return None
        return last if last.failed <= first.failed else None

    def _failing_tests(self, when: float) -> set[str]:
        """The tests a single suite run reported failing, by name.

        Per-test records share the timestamp of the run that produced them,
        which is what ties them to one invocation rather than to the task.
        """
        return {e.identity for e in self.evidence
                if e.kind is Kind.TEST and e.result is not Result.PASS and e.at == when}
