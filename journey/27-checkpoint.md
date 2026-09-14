# 27. Recording what was on the table when the gate said no

Two audits and two hundred paid runs later, the thing this project had never
done was look at the patch the agent was proposing **at the moment the gate
refused it**.

Everything was measured at the end. The gate's whole mechanism is a refusal at a
particular instant, and what it refused was gone by the time anybody graded
anything. P2 — *does the gate block work that was already correct* — has been in
the plan since Phase A with a note admitting the figure came from a weaker
proxy, because grading the block properly needs the candidate as it stood, and
nothing kept it.

## A recorder that cannot change what it records

`eval/checkpoint.py` is a `Stop` hook. It exports the patch as it stands, writes
it to the workspace, and exits zero. It is installed in **both** arms.

Both, because an instrument present on one side and absent on the other is the
difference between the sides. That is E4 said about the measuring apparatus
rather than the treatment, and this project has paid for that sentence twice
already. In the gated arm it runs after the gate's own hook, so a refused stop
is recorded too: the question is what was proposed, not what was permitted.

Two details it was worth getting right:

- **It always allows.** A recorder at a decision point is not neutral if it can
  change the decision, so it writes a file and returns zero whatever happens.
- **It takes the diff before opening its own journal.** Opening creates the
  file, and the next thing it does is `git add -A`, so the recorder appeared
  inside the candidate it was recording. The workspace excludes `.elevenpowers/`
  anyway; a recorder that depends on that to stay out of its own measurement is
  one configuration change away from corrupting it.

## The first four runs

Four runs, two tasks, both arms, $2.63.

| run | proposals | blocks | turns | cost |
|---|---|---|---|---|
| attrs-1c962d15 gate | **2** | **2** | 55 | $1.73 |
| attrs-1c962d15 vanilla | 1 | 0 | 12 | $0.26 |
| attrs-3b0378dd gate | 1 | 0 | 13 | $0.38 |
| attrs-3b0378dd vanilla | 1 | 0 | 10 | $0.26 |

All four first proposals graded `resolved`. Which means that on
`attrs-1c962d15`, the gate **refused a candidate that was already correct**, did
it twice, and the agent spent forty-three more turns and six and a half times
the money arriving at a patch that was also correct.

That is a false block, **graded at the block**, which is the thing PLAN §212
says the P2 figure never did. One run, on an easy task, and it is one data point
rather than a rate. But it is the first one of its kind this project has ever
had, and the apparatus produced it within four runs of existing.

## What it changes about the next experiment

The checkpoint design was chosen because it does not need hard tasks: a task an
agent eventually solves can still have a wrong candidate at turn fifteen, and
that is where the gate acts. The first measurement says the opposite may hold
here — four first proposals, four already correct — and if that survives a real
sample then there is nothing at the stop to repair, and the intervention can
only cost turns.

Which would be a finding, not a failure. "The gate blocks correct work and buys
nothing" is an answer to P2, and P2 has been open since Phase A with only a
proxy behind it.

The honest summary is that **the instrument for the next experiment now exists
and has never been pointed at a real sample.** Four runs on two of the easiest
tasks in the corpus is a demonstration that the wiring works. The measurement
worth having is the same thing across the forty-nine, and it is cheap, because
it rides along on runs that were going to happen anyway.
