# cronish

Parse, explain and plan cron-style schedules, with nothing outside the
standard library.

```
$ cronish next "30 9 * * mon-fri" --now 2024-03-06T10:17 -n 2
2024-03-07 09:30 Thu
2024-03-08 09:30 Fri
$ cronish describe "0 0 13 * fri"
at 00:00, on day 13 of the month or on Friday
$ cronish check "61 * * * *"
minute: value 61 out of range 0-59
```

From Python:

```python
from datetime import datetime
from cronish import parse, next_runs, describe

schedule = parse("@weekly")
next_runs(schedule, datetime(2024, 3, 6, 10, 17), 2)
describe(schedule)
```

Every option, default and message is listed in `docs/reference.md`.
