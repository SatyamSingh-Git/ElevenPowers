# ledgerbook

Double-entry bookkeeping in plain Python. Accounts, balanced transactions in
integer minor units, and a journal file that every command replays.

```
python -m ledgerbook books.jsonl init --currency USD
python -m ledgerbook books.jsonl open Assets:Cash Expenses:Food Equity:Opening
python -m ledgerbook books.jsonl post 2026-01-01 "Start" Assets:Cash=100 Equity:Opening
python -m ledgerbook books.jsonl post 2026-01-02 "Lunch" Expenses:Food=12.50 Assets:Cash
python -m ledgerbook books.jsonl balances
python -m ledgerbook books.jsonl statement Assets:Cash
```

From Python:

```python
from ledgerbook import Ledger, write_journal, load_journal, trial_balance

ledger = Ledger("EUR")
ledger.open("Assets:Cash")
ledger.open("Equity:Opening")
ledger.record("2026-01-01", "Start", [("Assets:Cash", 10000), ("Equity:Opening", -10000)])
write_journal("books.jsonl", ledger)
assert load_journal("books.jsonl").balances() == ledger.balances()
```

See `docs/reference.md` for every default, limit, message and file field.
