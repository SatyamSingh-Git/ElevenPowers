# Contributing to ElevenPowers

ElevenPowers is a runtime for AI coding agents (Claude Code, Codex, Gemini CLI,
Cursor Agent, Copilot CLI) that records what was actually checked: which tests
ran, against which tree, and whether they would have failed without the change.
This page is for anyone who wants to help. It covers what we need, how to set
up, and the rules a change has to meet before it is merged.

## Where help is wanted

The plan has two directions, in [`PLAN.md` §13](PLAN.md#13-two-directions-reviewer-evidence-and-coding-helper).

1. **Reviewer evidence: the current focus.** This is a report that tells the
   person accepting an agent's change whether tests pin it, and which lines
   could be altered without anything noticing. It is the one direction with a
   measured effect, and the maintainers are building it now. Help with
   design, real-project trials and reviewer studies is welcome.
2. **Coding helper: next, and open now.** The aim is fewer broken earlier
   behaviours and fewer stale docs while an agent works. It has **no measured
   benefit yet**, and the reasons are written down: what was tried, and how
   each attempt failed. §13 lists four open problems, each with a ready
   benchmark of twelve projects and kept before/after snapshots. You can
   start on one without repeating what failed. Read the
   [diagnosis](results/multistage-v3/README.md#why-elevenpowers-did-not-help-diagnosis-of-its-31-losses-0)
   first.

Smaller entry points:
- **The live architecture graph.** Its
  [planned tab](https://satyamsingh-git.github.io/ElevenPowers/architecture/#planned)
  holds contributor cards with acceptance criteria.
- **The PatchProof brief:** [`docs/design/patchproof-contributor-brief.md`](docs/design/patchproof-contributor-brief.md).
- **Anything in [`docs/status.md`](docs/status.md) marked open or unexplained**,
  such as the recorded intermittent CI tests.

If you are not sure where something fits, open an issue first.

## Setup

- **Python 3.11 or newer.** The runtime itself uses only the standard library.
- `python -m pip install -r requirements-dev.txt` gives you pytest.
- **Node 20 or newer, optional.** It is needed only for the JavaScript and
  TypeScript tests, which skip without it.
- **Optional engines** (Cosmic Ray, Stryker, TypeScript) are described in
  [`the-guide/installation.md`](the-guide/installation.md).

```bash
python -m pytest -q tests/test_the_file_you_changed.py   # fast loop
python -m pytest -q                                       # full suite, about an hour on Windows
python -m pytest tests/test_audit_probes.py -q            # every reproduced defect
python architecture/check.py --render                     # the map is true and still draws
```

Do not pass a `--basetemp` inside the repository: fixtures that are not Git
repositories inherit its work tree and fail.

## The rules a change must meet

These come from mistakes this project made and paid for. [`CLAUDE.md`](CLAUDE.md)
and [`journey/`](journey/README.md) give the history behind each one.

1. **Work for any project.** No special case, hardcoded path or command for a
   named repository. Discover a project's conventions, honour explicit
   overrides, and report ambiguity rather than guessing.
2. **Test both directions.** Every check needs a forward case, where
   legitimate input is accepted and the rule still fires. It also needs an
   adversarial case, where something tries to defeat it. A check that
   refuses everything passes the second and is still useless.
3. **Watch the test fail first.** A regression test is evidence only once you
   have seen it fail without your fix and pass with it. Say in the pull
   request that you did.
4. **Mutation-check your tests.** Break each part of your change on purpose,
   one at a time. If no test fails, add the case that would, or delete the
   part.
5. **Run the real thing before writing a pattern.** For any claim about the
   shape of something external (a tool's output, a command line, a file
   format), run it and read what came back first. Most defects found here
   were patterns written from memory.
6. **Borrow first.** Start from the best existing implementation. Name it,
   its licence and its limit, then state in one sentence what you add
   ([`docs/research/build-on.md`](docs/research/build-on.md)).
7. **Every number carries its limit.** Publish a figure with the qualification
   that bounds it. A claim that turns out wrong is listed in `PLAN.md` §10,
   not deleted.
8. **Keep the map current.** If you change architecture, data flow or
   workflow, update [`architecture/index.html`](architecture/index.html) and
   run `python architecture/check.py --render`.

## Pull requests

- **Fork and open a pull request against `main`.** Keep each commit
  reviewable on its own, with a message that says what changed and why.
- **CI runs on four cells:** Ubuntu and Windows, Python 3.11 and 3.13. For a
  fork, a maintainer approves the run after reading the change.
- **In the description, say what you verified:** the commands you ran, what
  failed before your fix and passed after, and which mutants you killed.
- **For a significant change, add a dated record:**
  [`docs/validation/`](docs/validation/README.md) for checks, and
  [`journey/`](journey/README.md) for what was tried and what was wrong.

[PR #3](https://github.com/SatyamSingh-Git/ElevenPowers/pull/3) is a good
example of all of the above.

## Model runs and money

You do not need to spend anything to contribute. Every evaluation here starts
with a no-model rehearsal or replay, and the kept snapshots of past runs let
you test a detector or a fix for $0. Paid model runs are sized, sealed and
pre-registered, and they are run by the maintainers. If your idea needs one,
show the $0 replay and propose the run in an issue.

## Contact and licence

Open an issue, or write to **[satyambcnrk@gmail.com](mailto:satyambcnrk@gmail.com)**.
Contributions are accepted under the licence the README states (Apache-2.0).
