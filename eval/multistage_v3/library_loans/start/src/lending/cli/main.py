"""Argument parsing and dispatch for `lend`.

Refusals are printed as `lend: <code>: <message>` on stderr with exit status 1,
so scripts can match on the code and people can read the message.
"""
import argparse
import sys

from ..errors import LendingError
from ..model.dates import parse_date
from ..reports.render import FORMATS
from ..services.library import Library
from . import commands


def _with_format(parser):
    parser.add_argument('--format', choices=sorted(FORMATS), default='text')
    return parser


def build_parser():
    parser = argparse.ArgumentParser(prog='lend', description='Circulation desk commands.')
    parser.add_argument('--library', default='.', help='library directory (default: the current one)')
    parser.add_argument('--today', required=True, help='the desk date, YYYY-MM-DD')
    parser.add_argument('--branch', help='the branch this desk is at; copies from other branches go into transit')
    sub = parser.add_subparsers(dest='command', required=True, metavar='command')

    def command(name, handler, summary):
        found = sub.add_parser(name, help=summary, description=summary)
        found.set_defaults(handler=handler)
        return found

    found = command('checkout', commands.checkout, 'lend copies to a member')
    found.add_argument('card')
    found.add_argument('barcodes', nargs='+', metavar='barcode')
    command('renew', commands.renew, 'renew a loan').add_argument('barcode')
    command('return', commands.checkin, 'take a copy back').add_argument('barcode')
    command('receive', commands.receive, 'take a copy off the van at its home branch').add_argument('barcode')
    _with_format(command('transit', commands.in_transit, 'list copies travelling between branches'))
    command('lost', commands.lost, 'write off a copy that will not come back').add_argument('barcode')

    found = command('hold', commands.hold, 'place a hold on a title')
    found.add_argument('card')
    found.add_argument('title')
    _with_format(command('queue', commands.queue, 'show the holds on a title')).add_argument('title')
    _with_format(command('shelf', commands.shelf, 'list copies set aside for members'))
    command('expire-holds', commands.expire, 'drop holds not collected in time')

    found = command('pay', commands.pay, 'take a payment towards fines')
    found.add_argument('card')
    found.add_argument('amount')
    found = command('waive', commands.waive, 'write off part of what a member owes')
    found.add_argument('card')
    found.add_argument('amount')
    command('amnesty', commands.amnesty, 'waive fines charged before a date').add_argument('--before', required=True)
    command('balance', commands.balance, 'show what a member owes').add_argument('card')
    _with_format(command('statement', commands.statement, "list a member's charges and payments")).add_argument('card')
    found = command('note', commands.note, "leave a note on a member's account")
    found.add_argument('card')
    found.add_argument('text', nargs='+')
    command('clear-notes', commands.clear_notes, "remove every note on a member's account").add_argument('card')
    command('notes', commands.show_notes, "read the notes on a member's account").add_argument('card')
    command('slip', commands.print_slip, 'print the loans slip for a member').add_argument('card')
    _with_format(command('due', commands.due_on, 'list loans due back on a day')).add_argument('--day')
    command('status', commands.status, "summarise a member's account").add_argument('card')
    _with_format(command('loans', commands.member_loans, "list a member's loans")).add_argument('card')

    _with_format(command('overdue', commands.overdue_report, 'list overdue loans'))
    found = _with_format(command('activity', commands.activity_report, 'count desk activity by month'))
    found.add_argument('--year', type=int)
    _with_format(command('search', commands.find, 'search the catalogue')).add_argument('words', nargs='+')
    command('notices', commands.send_notices, "write today's notices to the outbox")
    _with_format(command('outbox', commands.outbox, 'count notices sent by day and kind')).add_argument('--since')
    _with_format(command('history', commands.member_history, "list a member's past loans")).add_argument('card')
    _with_format(command('copy-history', commands.copy_history, 'list the loans of one copy')).add_argument('barcode')
    found = _with_format(command('debtors', commands.debtors, 'list members who owe money'))
    found.add_argument('--at-least', default='0.01')
    _with_format(command('lapsed', commands.lapsed, 'list members who have not borrowed lately')).add_argument('--since', required=True)
    found = _with_format(command('lateness', commands.lateness, 'share of returns that came back late'))
    found.add_argument('--since', required=True)
    found.add_argument('--until', required=True)
    found = _with_format(command('members', commands.member_profile, 'count members by type'))
    found.add_argument('--active-since')
    _with_format(command('collection', commands.collection, 'count stock by branch and material'))
    found = _with_format(command('popular', commands.popular, 'rank titles by issues'))
    found.add_argument('--since', required=True)
    found.add_argument('--until', required=True)
    found.add_argument('--top', type=int, default=10)
    _with_format(command('idle', commands.idle, 'list copies not issued lately')).add_argument('--since', required=True)
    found = _with_format(command('stocktake', commands.take_stock, 'compare a scan file with the shelves'))
    found.add_argument('branch')
    found.add_argument('scans')
    found = _with_format(command('takings', commands.takings, 'money charged, taken and waived by day'))
    found.add_argument('--since', required=True)
    found.add_argument('--until', required=True)
    command('check', commands.check, 'look for records that contradict each other')
    command('backup', commands.backup, 'zip the library files').add_argument('target')
    command('restore', commands.restore, 'unpack a backup over the library files').add_argument('archive')
    command('settings', commands.show_settings, 'show the settings in force')
    found = _with_format(command('demand', commands.demand, 'titles with the longest hold queues per copy'))
    found.add_argument('--at-least', type=int, default=1)
    command('day-sheet', commands.print_day_sheet, "summarise a day's desk activity").add_argument('--day')

    found = command('add-title', commands.add_title, 'add a title to the catalogue')
    found.add_argument('title')
    found.add_argument('--author', default='')
    found.add_argument('--material', default='BK')
    found.add_argument('--isbn', default='')
    found = command('add-copy', commands.add_copy, 'add a copy of a title to stock')
    found.add_argument('title')
    found.add_argument('barcode')
    found.add_argument('--branch', required=True)
    found.add_argument('--price', required=True)
    command('withdraw', commands.withdraw, 'take a copy out of stock').add_argument('barcode')

    found = command('join', commands.join, 'register a new member')
    found.add_argument('card')
    found.add_argument('name')
    found.add_argument('--type', default='adult')
    found.add_argument('--born', required=True)
    found.add_argument('--email', default='')
    found = command('member', commands.update_member, "change a member's name or email")
    found.add_argument('card')
    found.add_argument('--name')
    found.add_argument('--email')
    command('leave', commands.leave, 'close a membership').add_argument('card')
    command('promote', commands.promote, 'make child members who have turned 18 adults')
    command('import', commands.import_members, 'add members from a CSV file').add_argument('file')
    command('export', commands.export_members, 'write all members to a CSV file').add_argument('file')
    return parser


def main(argv=None, out=None, err=None):
    out = out or sys.stdout
    err = err or sys.stderr
    args = build_parser().parse_args(argv)
    try:
        library = Library.open(args.library, parse_date(args.today), args.branch and args.branch.upper())
        return args.handler(library, args, out)
    except LendingError as error:
        print(f'lend: {error.code}: {error.message}', file=err)
        return 1


if __name__ == '__main__':
    sys.exit(main())
