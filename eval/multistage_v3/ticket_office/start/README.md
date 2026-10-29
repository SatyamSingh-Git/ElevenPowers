# boxoffice

Box-office ticketing for a small theatre: the venue's seat map, performances
and their prices, holds, sales with concessions, refunds and exchanges, and the
reports the box office and finance use every day.

```
python -m boxoffice --data ./season venue hall.txt
python -m boxoffice --data ./season perf add HAM-0412E --title Hamlet --starts 2026-04-12T19:30 --price A=32 --price B=24
python -m boxoffice --data ./season hold HAM-0412E --best 2
python -m boxoffice --data ./season sell H0001 --concession A5=child
python -m boxoffice --data ./season report daily
```

Everything lives in the data directory as plain files: see `docs/reference.md`.
Run the tests with `python -m pytest`.
