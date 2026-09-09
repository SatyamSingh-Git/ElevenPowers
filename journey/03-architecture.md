# 3. Two rewrites, and the pivot

## v0.2: grounded, but still a laboratory

With the research done, the plan was rewritten. v0.2 opened with a table of what
changed from v0.1 and why, so the reasoning could be audited rather than trusted.
The substantive changes:

- The benchmark suite moved off SWE-bench Verified.
- "False success" was renamed the submit-resolve gap and given the published
  definition, and abstention tasks were added where the correct answer is to
  stop.
- Portability dropped from a five-week milestone to a two-day spike.
- The repository model changed from "build a knowledge graph" to "wrap Aider's
  map and measure whether the missing edges are worth adding".
- Sixteen task categories became eight, because sixteen at three tasks each
  cannot support a per-category claim.
- Statistics were reordered: measure the noise floor, publish the minimum
  detectable effect, then size the suite. v0.1 had written decision rules its
  sample size could not deliver.
- Two new metrics: prediction calibration, and stability contracts for flaky
  bugs.

It was a much better document. It was still shaped wrong: three weeks of harness
before any code touched a repository, eight arms times 48 tasks times three runs,
and no metric at all for whether a developer would tolerate the result.

## The critique

An external review made seven points. The ones that landed:

- This is a research laboratory, not a product. Nothing would be usable in month
  one.
- The evaluation design creates over a thousand agent runs per sweep.
- Friction is not a hypothesis anywhere, and a technically superior system people
  disable has still lost.
- The novelty claims are unbounded. "The only system" and "no prior art" need
  evidence that was not gathered.
- A milestone is referenced that the roadmap never defines.
- The name reads as derivative of one of the studied projects.

And one suggestion that was more interesting than the criticisms: that the
workflow should perhaps be derived backwards from what would prove the work.

```
intent -> claims -> proof obligations -> required observations -> workflow
```

rather than

```
intent -> task category -> workflow template -> verification appended
```

## Testing the pivot rather than adopting it

The proposal was attacked before it was accepted, because a good-sounding
architecture is exactly the kind of thing that should be attacked.

**Where it fails, honestly:**

1. Claims still have to be inferred from intent, so it is a classifier by another
   name. The counter is that it is a better-conditioned one: eight claim types
   rather than an open set of processes, several claims can apply to one request,
   and a wrong claim is visible in one line of output and correctable, while a
   wrong category is invisible.
2. Not all work has obligations. "Explain this module" has no completion
   criterion. Under classification it would still get a workflow; under
   obligations it correctly gets nothing.
3. Obligations underdetermine order. "Applies, preserves data, rolls back" does
   not say to write the migration first. Sequencing needs procedural knowledge,
   though far less than a template library, and for a first version none at all:
   obligations can be discharged in any order and only the end state is checked.

**Why it wins anyway, and not for the reason offered.** The argument given was
that obligations are more concrete. The stronger argument is about invariants:
obligations are stable while plans are contingent. When evidence contradicts the
plan halfway through a hard bug, the obligation does not change, only the route
to it. That makes replanning ordinary instead of a special case, and it deletes
an entire subsystem: v0.2 needed explicit recompile triggers to simulate what
this gets for free.

It also collapses two components into one and removes the workflow compiler from
the first version entirely. The more ambitious idea turned out to be the smaller
one, which is usually a sign it is right.

## Bounding the novelty claims

The critique's demand for evidence was acted on rather than accepted in
principle. Searching found three 2026 papers the earlier plans did not know
about:

- **AgentLTL** specifies procedural rules in temporal logic over agent traces,
  scores compliance without a judge, and enforces at runtime by blocking actions.
  That is runtime-enforced process compliance, so v0.2's claim to it was
  withdrawn. It verifies procedure, not whether work is done and still valid.
- **Proof-carrying certificates for LLM pipelines** issue kernel-checked
  certificates bound to per-call artifacts, with an explicit residue for
  abstention.
- **Proof of execution** enforces authorization and path compliance over a causal
  event stream with attestation.

And one industrial practice that mattered more than all three: **Test Impact
Analysis**, deployed at Datadog, Microsoft and Google, builds a test-to-source
dependency map and reruns only affected tests, with a documented rule to fall
back to running everything when the map goes stale. That is exactly the
invalidation mathematics this design needs, already proven at scale.

So the claim became bounded and, being bounded, stronger: the mechanism is
standard practice, and only its application to agent completion was not found
among the fourteen systems surveyed or the papers read. Borrowing a proven
mechanism is a lower-risk kind of novelty than inventing one.

## What the thing actually is

Reasoning from first principles rather than picking a category name.

It is not a framework: it prescribes no process to learn. Not an agent: it never
acts. Not a harness: it does not own the loop. It watches an agent work, decides
what would constitute proof, collects that proof from commands the agent already
runs, tracks which proof is still valid as the code changes, and computes a
completion state the agent cannot assert its way past.

The closest true analogue is not any coding-agent project. It is `make`.

`make` does not build software. It knows what depends on what, notices when
something is stale, and refuses to call a target up to date when its inputs
changed. It turns "is this built?" from an opinion into a computation. This does
the same for correctness claims.

**The thesis, in one sentence:** completion should be computed from
dependency-tracked evidence, not asserted by the model.

## Cutting to the core

Every subsystem was then tested against one question: if this vanished, would a
developer notice their agent got worse?

Seven survived: evidence capture, provenance and staleness, claim inference,
obligation contracts, the completion gate, the scope guard, and a repeat runner
for flaky work. Everything else was postponed with a written trigger in
`docs/postponed.md`, so postponement is a decision with a condition rather than a
quiet drop.

The workflow compiler, the repository model, the context engine, memory, model
routing, critics and extra adapters all went into that file. The estimate for
what remained was about 1,400 lines.
