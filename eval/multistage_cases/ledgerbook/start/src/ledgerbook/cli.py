"""Command line: ledgerbook JOURNAL COMMAND [ARGS].

Every command replays the journal first, so a command that would leave the
journal unreadable is refused before anything is written.
"""
import argparse
from pathlib import Path
import sys

from .errors import LedgerError
from .journal import JournalWriter
from .money import DEFAULT_CURRENCY, parse_amount
from .replay import load_journal
from .reports import render_statement, render_summary, render_trial_balance
from .transactions import make_transaction, reversal

EXIT_OK = 0
EXIT_ERROR = 1


def _parser():
    parser = argparse.ArgumentParser(prog="ledgerbook", description="Double-entry bookkeeping on a journal file.")
    parser.add_argument("journal", type=Path)
    commands = parser.add_subparsers(dest="command", required=True)

    init = commands.add_parser("init", help="create an empty journal")
    init.add_argument("--currency", default=DEFAULT_CURRENCY)

    opening = commands.add_parser("open", help="open one or more accounts")
    opening.add_argument("accounts", nargs="+")

    post = commands.add_parser("post", help="record a transaction")
    post.add_argument("date")
    post.add_argument("description")
    post.add_argument("postings", nargs="+", metavar="ACCOUNT[=AMOUNT]")

    reverse = commands.add_parser("reverse", help="undo a transaction by posting its opposite")
    reverse.add_argument("number", type=int, help="1-based position of the transaction in the journal")
    reverse.add_argument("date")

    commands.add_parser("balances", help="print the trial balance")
    commands.add_parser("summary", help="print totals by account type")

    statement = commands.add_parser("statement", help="print one account's postings")
    statement.add_argument("account")
    return parser


def parse_postings(texts, currency):
    """Read ACCOUNT=AMOUNT arguments; one ACCOUNT may omit its amount and take the remainder."""
    postings, remainder = [], None
    for text in texts:
        account, has_amount, amount = text.partition("=")
        if has_amount:
            postings.append((account, parse_amount(amount, currency)))
        elif remainder is None:
            remainder = account
        else:
            raise LedgerError("only one posting may omit its amount")
    if remainder is not None:
        postings.append((remainder, -sum(amount for _, amount in postings)))
    return postings


def _run(args):
    if args.command == "init":
        JournalWriter.create(args.journal, args.currency)
        return f"created {args.journal}\n"

    ledger = load_journal(args.journal)
    writer = JournalWriter(args.journal, ledger.currency)
    if args.command == "open":
        for name in args.accounts:
            ledger.open(name)
        for name in args.accounts:
            writer.append_open(name)
        return ""
    if args.command == "post":
        postings = parse_postings(args.postings, ledger.currency)
        writer.append(ledger.post(make_transaction(args.date, args.description, postings)))
        return ""
    if args.command == "reverse":
        if not 1 <= args.number <= len(ledger.transactions):
            raise LedgerError(f"no transaction number {args.number}")
        writer.append(ledger.post(reversal(ledger.transactions[args.number - 1], args.date)))
        return ""
    if args.command == "balances":
        return render_trial_balance(ledger)
    if args.command == "summary":
        return render_summary(ledger)
    return render_statement(ledger, args.account)


def main(argv=None):
    args = _parser().parse_args(argv)
    try:
        output = _run(args)
    except (LedgerError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return EXIT_ERROR
    sys.stdout.write(output)
    return EXIT_OK
