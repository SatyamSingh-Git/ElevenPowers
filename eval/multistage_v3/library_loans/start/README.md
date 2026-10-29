# lending

Circulation desk tools for a small public library: lending, renewals, holds,
fines, overdue notices and the loans ledger finance reconciles against.

    pip install -e .
    lend --library /srv/library --today 2026-03-02 checkout M1001 31000001

Everything lives in one directory per library; see `docs/reference.md` for the
files, settings and messages. Run the tests with `python -m pytest`.

Layout:

- `src/lending/model` - plain records: catalogue, members, loans, holds, dates, money
- `src/lending/storage` - reading and writing the library's files
- `src/lending/services` - what the desk does: circulation, holds, fines, notices
- `src/lending/reports` - reports for staff and finance
- `src/lending/cli` - the `lend` command
