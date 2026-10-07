# Explained rechecks: frozen authored controls

2026-10-07. Runtime origin **4e5a994**. [Provenance](provenance.v1.json) and
[observations](observations.v1.json) retain corpus and runtime identities. These
six authored small projects are not representative large repositories, installed
host sessions or an agent comparison. No model or paid run was launched.

| Case | Partition | Required references found | Labelled unrelated leads | Behavioral control |
|---|---|---:|---:|---|
| Python package/transitive consumer | Development | 2/2 | 0/1 | Two checks reject the provider fault |
| Literal dynamic plugin | Development | 1/1 | 0/1 | Dispatch rejects the plugin fault |
| Node ESM service | Development | 1/1 | 0/1 | Service rejects the boundary fault |
| Configuration input | Held out | 1/1 | 0/1 | Direct input; retry rejects changed configuration |
| Subprocess worker | Held out | 0/1 | 0/1 | Missed relationship; retained fallback rejects the CLI fault |
| Unrelated source edit | Held out | No required reference | 0/1 | Checks pass; broad native receipts still become stale |

Known required recovery is **5/6** (development 4/4, held out 1/2). No leads reach
the **six labelled negative references**; this is not a precision estimate for
unlabelled projects. Fallback is not credited as a recovered dependency. The
subprocess miss is preserved; no adapter was tuned after the held-out result.
Every declared command remains in the report.

All phases total **36 actual command runs: 30 qualified passes and six qualified
assertion failures**. Six failures come from five seeded faulty changes (the
Python chain fails two commands). Correct/equivalent code passes, assertions stay
byte-identical, and the unrelated edit does not fail. Existing pytest/Node receipt
parsing and execution are reused.

**54 paired read samples / 108 report operations**, three repeats per phase per
case with alternating ordering, give local medians **94.59 ms plain**, **177.54 ms
advised**, and **82.05 ms paired added time**. Maximum advised read: **256.66 ms**.
Projects have only **4–9 selected files / 597–1,996 bytes**. Warming effects are
included. These do not establish large-project/native cost or speedup. Ledger
bytes remain unchanged in all 54 samples; unit controls check all project bytes.

```bash
python -m eval.milestone_rechecks --output NEW_DISPOSABLE_DIR
```

Use a new directory and the recorded runtime/corpus. Python/pytest is required;
missing Node leaves an explicit incomplete case. [Frozen inputs](frozen-corpus.json)
include assertions and labels. Ordinary inspection runs no checks; this explicit
exercise executes local pytest/Node controls. Published output substitutes root
and interpreter paths and redacts XML hostnames. Original and public byte digests
remain separate across **78 artifacts**. Partial attempts remain visible.

This is capability and limited relevance evidence, **not incremental agent coding
improvement**. Broader independent projects, native cost, producer-supported narrow
attribution and a matched end-to-end comparison remain open before automatic integration.

The subsequent review correction grades milestone-specific witnesses when commands
are shared and atomically saves reads, completed attempts and pending identities.
A regression regrade confirms every original six-case grade is unchanged. These
fixes do not replace the published producer origin or timing observations.
