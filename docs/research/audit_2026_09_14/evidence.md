# Evidence for the next-stage review

Analysis of the recorded paired chunks, begun at revision `51d3165`, inspected 14 September 2026. These calculations read preserved artifacts; they do not re-grade candidates or execute agent commands. `eval/live.py` and `tests/test_audit_probes.py` already had uncommitted changes when the review began; those changes were committed externally as `fd4e8ec` during the review. That commit was inspected separately for the containment findings in §5.7 of the report. This review edited neither file and launched no paid runs.

## Recorded results

Inputs: [chunk1.json](E:/ElevenPowers/results/chunks/chunk1.json) and [chunk2.json](E:/ElevenPowers/results/chunks/chunk2.json). Each JSON object holds its observations under `runs`.

| Arm | Runs | Resolved | Stop-block events | Runs with a Stop block | Recorded cost sum |
|---|---:|---:|---:|---:|---:|
| vanilla | 50 | 46 | 0 | 0 | $47.50 |
| gate | 50 | 49 | 6 | 4 | $54.27 |

The cost sum uses rounded row values. A cent difference from a separately summed invoice/summary is not interpreted as a defect.

| Task | Vanilla successes / 2 | Gate successes / 2 | Blocking events in each gated replicate |
|---|---:|---:|---|
| attrs-0f758fe5 | 1 | 1 | 0, 0 |
| attrs-1c962d15 | 2 | 2 | 0, 0 |
| attrs-1e07f468 | 2 | 2 | 0, 2 |
| attrs-3b0378dd | 2 | 2 | 0, 0 |
| attrs-577c782c | 2 | 2 | 1, 0 |
| attrs-62bdbf23 | 2 | 2 | 0, 0 |
| attrs-6fda0a4e | 1 | 2 | 0, 0 |
| attrs-97f8d175 | 2 | 2 | 0, 0 |
| attrs-bde3f58c | 2 | 2 | 0, 0 |
| attrs-e21793e9 | 2 | 2 | 2, 0 |
| click-051bb0f3 | 2 | 2 | 0, 0 |
| click-4f9086bf | 2 | 2 | 0, 1 |
| click-9f9b149e | 2 | 2 | 0, 0 |
| click-b7e5fd4c | 2 | 2 | 0, 0 |
| click-bec59289 | 0 | 2 | 0, 0 |
| click-becbde5c | 2 | 2 | 0, 0 |
| click-c2ed4149 | 2 | 2 | 0, 0 |
| itsdangerous-526b1ea0 | 2 | 2 | 0, 0 |
| itsdangerous-f966a62e | 2 | 2 | 0, 0 |
| jinja2-065334d1 | 2 | 2 | 0, 0 |
| jinja2-2eb4542c | 2 | 2 | 0, 0 |
| jinja2-679af7f8 | 2 | 2 | 0, 0 |
| jinja2-91a972f5 | 2 | 2 | 0, 0 |
| jinja2-d05bd385 | 2 | 2 | 0, 0 |
| jinja2-ee832194 | 2 | 2 | 0, 0 |

- 22 tasks resolved in all four attempts; 23 tasks had equal arm-level success rates. These are different counts.
- `attrs-0f758fe5` resolved once and failed once in each arm; it is concordant in rates, not universally solved.
- Two vanilla candidates contain at least one graded success on 24/25 tasks. All four candidates contain one on 25/25. These are descriptive oracle pool-coverage values, not selected-system scores. Answer exposure below prevents interpreting them as clean generation capability.
- The current task-level sign test gives `mcnemar(2, 0) = 0.5`. At one replicate per arm this test reduces to McNemar; with the present rate comparison it is a sign test.

## Recorded interventions

| Decision type | Events | Runs with event |
|---|---:|---:|
| claim opened by an edit | 16 | 16 |
| gate blocked | 6 | 4 |
| gate gave up | 2 | 2 |
| ran a declared command | 3 | 3 |
| scope question | 5 | 2 |

The ledger is not a complete host-message exposure log. Opening banners and guidance cannot be inferred absent just because no decision row was appended.

## Upstream-diff retrieval screen

All 100 answer session IDs were located in local host transcripts. A read-only screen paired tool calls with their returned results. It flagged calls using `gh pr diff`, `gh pr view`, `gh api`, or GitHub URLs when the corresponding non-error result contained a diff hunk marker (`@@`).

The screen found **54 returned results in 42 runs**. This is a broad screen for successful retrieval of diff-like GitHub content. It does not establish that all 42 runs fetched their exact target fix, nor that the remaining 58 were unexposed. It misses other channels and forms of exposure. Several exact-target cases were checked directly, including attrs PRs #1328 and #1541 and click PR #3582.

Each link below opens the first matching returned result. The commands were read from historical logs, not executed during this review. No credential values are copied into this report.

| Bundle | Matching returned results | First result |
|---|---:|---|
| attrs-0f758fe5--gate--1789335923248 | 2 | [transcript line 53](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpcm6vn5rn/91f5a9d8-f390-421f-9fb0-341a51fedfdf.jsonl:53) |
| attrs-0f758fe5--vanilla--1789335668769 | 1 | [transcript line 33](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpznw0bbtg/46ea752d-0432-465a-8524-57711cf02f3a.jsonl:33) |
| attrs-1e07f468--gate--1789360440544 | 1 | [transcript line 43](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpzjw8fam0/a8155784-f921-4cd0-b9a0-9702106c08df.jsonl:43) |
| attrs-1e07f468--vanilla--1789360266979 | 1 | [transcript line 77](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpdxgv185j/af4c0399-268d-47b4-851f-5082a061e5bc.jsonl:77) |
| attrs-577c782c--gate--1789336932024 | 1 | [transcript line 38](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpfg050a76/f7f1b2fc-3a55-4969-8d10-e8ac5726e26b.jsonl:38) |
| attrs-577c782c--gate--1789337180941 | 1 | [transcript line 42](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpz8fy24pl/b45dee4e-3535-4f2f-8314-ca4f4aad36c0.jsonl:42) |
| attrs-577c782c--vanilla--1789336452632 | 1 | [transcript line 30](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp1jvacn6n/ca322db4-2649-431f-b876-f121b7d5908d.jsonl:30) |
| attrs-577c782c--vanilla--1789336542801 | 1 | [transcript line 37](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpz1pc4lrm/6bc01957-64fd-44ac-bb85-99ffe4b91fcb.jsonl:37) |
| attrs-62bdbf23--gate--1789338250134 | 2 | [transcript line 41](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpzeopyh36/2321b0fb-2d84-45ad-9b2a-940ed5fc2291.jsonl:41) |
| attrs-6fda0a4e--gate--1789363061623 | 1 | [transcript line 62](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpc4l9xgo5/a67419ce-0a47-4030-b969-d4dbd32d00eb.jsonl:62) |
| attrs-6fda0a4e--gate--1789363303080 | 1 | [transcript line 35](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp88loj5gg/0e6f7f66-cb41-476d-8c04-937351c40846.jsonl:35) |
| attrs-6fda0a4e--vanilla--1789362390237 | 1 | [transcript line 62](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmphkoxrbtf/1bb19983-2557-425c-85e2-1e33643ca201.jsonl:62) |
| attrs-97f8d175--gate--1789359219325 | 1 | [transcript line 99](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpfmmr-3b3/2c9fd395-644d-46b5-bef7-a8af432e3ec4.jsonl:99) |
| attrs-97f8d175--vanilla--1789358597849 | 1 | [transcript line 51](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpb4tp8iem/4605c773-3cbb-4550-b18b-48dfafab7a1d.jsonl:51) |
| attrs-bde3f58c--gate--1789339861213 | 1 | [transcript line 90](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp16g2qj9q/d1ceb5d9-b0ad-4e89-a461-c96fbbd15077.jsonl:90) |
| attrs-bde3f58c--gate--1789340302687 | 1 | [transcript line 47](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpp19r8qpk/63d7bd5d-d17e-40c9-b542-b3cdd7236e58.jsonl:47) |
| attrs-e21793e9--vanilla--1789362111581 | 1 | [transcript line 64](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpxed09msr/9a7c585f-ab0f-4d10-aa35-569270ac408d.jsonl:64) |
| click-4f9086bf--gate--1789342808042 | 4 | [transcript line 37](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpfyvmryke/5633b74f-d64e-4961-be60-1be7b29872ec.jsonl:37) |
| click-4f9086bf--gate--1789343006762 | 1 | [transcript line 32](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp3t3sn2xa/b8a1a996-9cec-456e-bae6-45e203fbe1b2.jsonl:32) |
| click-4f9086bf--vanilla--1789343135595 | 1 | [transcript line 34](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpxm0o3jy5/ff70df21-86a3-4a98-817f-d956241402ad.jsonl:34) |
| click-4f9086bf--vanilla--1789343266283 | 2 | [transcript line 48](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpwg3uckqb/8df249c2-4bd9-4866-82d6-a5214c3e480a.jsonl:48) |
| click-9f9b149e--gate--1789364586633 | 1 | [transcript line 53](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp2vrqfyxl/ddb61d25-31cc-4512-99ed-859577bb12d7.jsonl:53) |
| click-9f9b149e--vanilla--1789364155853 | 1 | [transcript line 49](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpxtdwjjxc/23989829-9554-42df-8e7c-9f31511d98c8.jsonl:49) |
| click-9f9b149e--vanilla--1789364276518 | 1 | [transcript line 53](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp-s4k39ri/c67bdf5b-e490-46cd-a2f8-db2aae9dc68e.jsonl:53) |
| click-b7e5fd4c--gate--1789341841646 | 1 | [transcript line 54](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp69xzztmq/f0d7b1bd-65e4-46ac-9c76-fcc78b8b9cd6.jsonl:54) |
| click-b7e5fd4c--gate--1789342052409 | 2 | [transcript line 50](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpxlgpdiwa/c9dc18dd-cbb4-49f3-b6f3-4d13ea6b353e.jsonl:50) |
| click-b7e5fd4c--vanilla--1789342525102 | 3 | [transcript line 114](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpirg-ulfs/62267600-1691-4b31-a745-71fe0d0d7e0e.jsonl:114) |
| click-b7e5fd4c--vanilla--1789342678077 | 2 | [transcript line 51](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpynx7gn1z/b9290265-3fc3-4c46-ad54-713a2f1de42c.jsonl:51) |
| click-bec59289--gate--1789341614289 | 2 | [transcript line 37](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpmsxu0bb0/13e7973c-53a9-4f82-964d-ef0d1c051337.jsonl:37) |
| click-becbde5c--gate--1789366631670 | 1 | [transcript line 56](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp9u4uvemc/43df919a-0c13-4e31-b17f-ad89db8eeadd.jsonl:56) |
| click-becbde5c--vanilla--1789366351100 | 1 | [transcript line 102](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpb0s-cq3r/be2f2bc4-e831-4d37-9130-ed523968e6d2.jsonl:102) |
| click-c2ed4149--gate--1789363562099 | 1 | [transcript line 32](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpx9knua49/3d52dcf8-9396-401b-b40f-61a958d827d6.jsonl:32) |
| click-c2ed4149--gate--1789363654206 | 1 | [transcript line 36](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmput2q5g1n/6135c25e-4514-418e-a5b7-2442c1074d80.jsonl:36) |
| itsdangerous-f966a62e--gate--1789343977988 | 2 | [transcript line 65](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmppqrh6v7m/3a75ba45-b417-4bfb-9f26-afeb0015fe6d.jsonl:65) |
| itsdangerous-f966a62e--vanilla--1789343564068 | 1 | [transcript line 52](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpa7ezu10k/41e22a7f-8ac1-4c5a-81a3-bdbf860d5273.jsonl:52) |
| jinja2-065334d1--gate--1789344486368 | 1 | [transcript line 39](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmprz2h4viu/ff6525d6-5874-4e8b-9f72-31a0314e1b8f.jsonl:39) |
| jinja2-065334d1--vanilla--1789344622173 | 1 | [transcript line 81](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpzk-i7bff/e98f742c-ee7c-49ef-af24-a8333d4fab27.jsonl:81) |
| jinja2-679af7f8--gate--1789345770698 | 1 | [transcript line 66](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmps2npjrum/578d4350-7a9c-4344-88f7-751a683411b1.jsonl:66) |
| jinja2-91a972f5--gate--1789368394961 | 1 | [transcript line 49](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp3s1k5eiy/0c3d9fbc-5689-47a4-9992-b716ea65751a.jsonl:49) |
| jinja2-91a972f5--gate--1789368818915 | 1 | [transcript line 92](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp6f7ah2xb/0fd6944f-432e-4b27-ae80-97e465e72167.jsonl:92) |
| jinja2-91a972f5--vanilla--1789368964513 | 1 | [transcript line 51](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmp1b214zj-/32020665-2aac-449b-bed3-a5edc7beb74c.jsonl:51) |
| jinja2-91a972f5--vanilla--1789369655095 | 1 | [transcript line 204](C:/Users/Satyam/.claude/projects/C--Users-Satyam-AppData-Local-Temp-tmpe0oaao9i/8c61cd6f-4b82-4dc0-864c-323700c76213.jsonl:204) |

## Exact-target examples

| Case | Historical action and observed result |
|---|---|
| `attrs-6fda0a4e--gate--1789363303080` | `gh pr diff 1328 --repo python-attrs/attrs`; returned hunks include `src/attr/_make.py` and the callable converter adapter. Transcript call line 34, result line 35. |
| `attrs-6fda0a4e--gate--1789363061623` | The same PR diff returned in call/result lines 61/62. |
| `attrs-6fda0a4e--vanilla--1789362390237` | The same PR diff returned in call/result lines 61/62. |
| `click-bec59289--gate--1789341614289` | `gh api repos/pallets/click/pulls/3582/files`; returned file URLs identify exact target commit `bec59289d8cf9b9b4010642b2fee483e5f8eeefc`, with source/test patches. Call/result lines 36/37 and 40/41. |

The last click bundle also records four `scope question` decisions and four host permission denials despite zero Stop blocks. Its [ledger](E:/ElevenPowers/results/chunks/bundles-chunk1/click-bec59289--gate--1789341614289/ledger.json) and [answer](E:/ElevenPowers/results/chunks/bundles-chunk1/click-bec59289--gate--1789341614289/answer.json) contradict the assertion that this run received no intervention.

## Arithmetic checks

For a two-sided exact binomial/sign test with null win probability 0.5, the probability of rejecting at 0.05 when the alternative win probability is 0.75 is calculated by summing binomial mass over the rejection set. No normal approximation is needed.

| Number of discordant units | Exact power at a 75% treatment win probability |
|---:|---:|
| 6 | 0.1782 |
| 25 | 0.7265 |
| 31 | 0.7710 |
| 32 | 0.7367 |
| 33 | 0.8190 |
| 34 | 0.7894 |
| 35 | 0.8579 |
| 40 | 0.8968 |

- Six discordant units all favoring treatment give `p = 0.03125`; 31 is not a universal minimum needed for any result.
- The current approximation gives 31 for a particular power assumption; exact conditional power there is 0.771. Power depends on the alternative and test, and is discrete.
- At an assumed independent per-run eligibility probability of 0.08, two repeats give `1 - 0.92**2 = 0.1536` chance of at least one eligible run. Thirteen tasks then yield 1.9968 eligible tasks **in expectation**, not as a hard maximum. Repeated attempts within tasks need not be independent.
- Exact conditional power given a fixed number of discordances is not a complete total-sample power calculation. The latter must also model how many discordances occur and the chosen randomization/clustering.

## Provenance

- `results/chunks/chunk1.json` SHA-256: `48962a07bc140eac47d31ec826879c01122c5669ef555ad70b78f09d72224ce5`.
- `results/chunks/chunk2.json` SHA-256: `fdc0e206188d0ca0b9dbe6a357c6ba12a7a02788e26c95bec7e7c888ff450cd7`.

The following standard-library calculation reproduces the aggregate outcome, block and pool counts and exact conditional power. It reads the saved JSON only; run it from `E:/ElevenPowers`. It does not establish correctness independently of the saved grader, and does not reproduce the transcript exposure screen.

```python
import json
from collections import defaultdict
from math import comb
from pathlib import Path

rows = [r for n in (1, 2)
        for r in json.loads(Path(f"results/chunks/chunk{n}.json")
                            .read_text(encoding="utf-8"))["runs"]]
assert len(rows) == 100
tasks = defaultdict(list)
for row in rows:
    tasks[row["task"]].append(row)
for arm in ("vanilla", "gate"):
    group = [r for r in rows if r["arm"] == arm]
    print(arm, "runs", len(group), "resolved", sum(r["resolved"] for r in group),
          "events", sum(r["blocks"] for r in group),
          "blocked_runs", sum(r["blocks"] > 0 for r in group))
print("all_four_successful", sum(all(r["resolved"] for r in g)
                                 for g in tasks.values()))
for arms in ({"vanilla"}, {"vanilla", "gate"}):
    print("pool", sorted(arms), sum(any(r["resolved"] and r["arm"] in arms
                                      for r in g) for g in tasks.values()))

def exact_p(k, n):
    return min(1.0, 2 * sum(comb(n, j) for j in range(min(k, n-k) + 1)) / 2**n)

print("observed_sign_p", exact_p(2, 2))
for n in (6, 25, 31, 32, 33, 34, 35, 40):
    power = sum(comb(n, k) * 0.75**k * 0.25**(n-k)
                for k in range(n+1) if exact_p(k, n) <= 0.05)
    print(n, round(power, 4))
```
