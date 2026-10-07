# Bounded milestone advice — 2026-10-07

Base `fd88f60`; branch `codex/milestone-advisories`. The design, implementation
plan and six selected upstream reference pairs preceded evaluation. Runtime is
project-independent and adds no completion gate or project command execution.

Observed red/green controls: three missing-evaluator failures then three passes;
13 policy failures then 34 policy/config passes; five worker failures then five
passes; five absent-advice failures then 88 advice/adapter passes. The callback
harness initially mishandled legitimate empty Claude baseline output, corrected
before recording measurements. The complete new control group passed **33 tests**.
Existing declared process capability needed no production change: two controls
include actual baseline/fault/equivalent CLI checks and invalid endpoint rejection.

Larger-project observation runtime `3a3ce38`: six selected required relationships
recovered on three pinned upstream snapshots; four cross-reference leads remain
unknown. Unsupported unrelated labels are explicitly withdrawn with originals
preserved. All static reports are incomplete. Both source seals passed. Eighteen
paired reads added median **947.254 ms**, maximum advised read **1498.692 ms**.
No upstream checks or models ran. See [raw results](../../results/milestone-advisories/README.md).

Launcher observation runtime began at `9e3f618`, with the added measurement
harness: **135 replay processes**, no nonzero exits/duplicate advice, median added
**1282.703 ms**, maximum advised **1799.336 ms**. Forty-four contexts delivered
incomplete coverage, one worker attempt incomplete. Installed Claude **2.1.287**
separately processed one unprompted startup callback, sample **1135.235 ms**.
Neither replay nor startup qualifies installed edit advice. See
[qualified native limits](../../results/milestone-advisories/callbacks.md).

The observations below qualify local review and compatibility. Hosted exact-head
CI and main integration are reported against their actual tested revision.
No default-on or coding-benefit claim is made.

The fresh whole-branch review found one profile/configuration race. Three
regressions were watched failing, then repaired: current off suppresses context
and failure diagnostics, and configuration movement discards pending output.
The affected compatibility group passed **180 tests in 39.57 seconds**. The host
doctor passed and all four independent grader categories matched. All five
architecture views rendered at **127 nodes / 291 edges / 7 planes**.
