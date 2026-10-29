"""One function per `lend` subcommand. Each prints its result and returns the exit status."""
from dataclasses import fields
from pathlib import Path

from ..config import CONVERTERS
from ..model.dates import format_date, parse_date
from ..model.money import format_money, parse_money, plain_amount
from ..reports import activity, due, finance, holdshelf, loans, members, outbox_log, overdue, search, stock
from ..reports import demand as demand_report
from ..reports.day_sheet import day_sheet
from ..reports.render import render
from ..services import (accounts, audit, cataloguing, circulation, fines, history, holds, membership, notes,
                        notices, transit)
from ..services.stocktake import stocktake as compare_scans
from ..storage.backup import restore_backup, write_backup
from ..storage.scans import read_scans


def checkout(library, args, out):
    """Lend each copy in turn; a refusal stops the rest, and the ones already lent stay lent."""
    for barcode in args.barcodes:
        loan = circulation.checkout(library, args.card, barcode)
        print(f'{loan.barcode} due {format_date(loan.due)}', file=out)
    return 0


def renew(library, args, out):
    loan = circulation.renew(library, args.barcode)
    print(f'{loan.barcode} due {format_date(loan.due)}', file=out)
    return 0


def checkin(library, args, out):
    result = circulation.checkin(library, args.barcode)
    line = f'{result.loan.barcode} returned'
    if result.fine:
        line += f', fine {format_money(result.fine)}'
    if result.hold is not None:
        line += f'; hold shelf for {result.hold.card}'
    elif result.in_transit:
        line += f'; send to {library.copy(result.loan.barcode).branch}'
    print(line, file=out)
    return 0


def lost(library, args, out):
    charged = circulation.write_off(library, args.barcode)
    print(f'{args.barcode.strip()} written off, charged {format_money(charged)}', file=out)
    return 0


def hold(library, args, out):
    placed = holds.place_hold(library, args.card, args.title)
    where = holds.position(library, placed)
    state = 'ready to collect' if where == 0 else f'position {where}'
    print(f'hold on {placed.title_id} for {placed.card}: {state}', file=out)
    return 0


def queue(library, args, out):
    out.write(render(holdshelf.queue_rows(library, args.title), holdshelf.QUEUE_COLUMNS, args.format))
    return 0


def shelf(library, args, out):
    out.write(render(holdshelf.shelf_rows(library), holdshelf.SHELF_COLUMNS, args.format))
    return 0


def expire(library, args, out):
    lapsed = holds.expire_holds(library)
    print(f'{len(lapsed)} holds lapsed', file=out)
    return 0


def pay(library, args, out):
    paid = parse_money(args.amount)
    owed = fines.pay(library, args.card, paid)
    print(f'paid {format_money(paid)}; balance {format_money(owed)}', file=out)
    return 0


def balance(library, args, out):
    member = library.member(args.card)
    print(f'{member.card} owes {format_money(fines.balance(library, member.card))}', file=out)
    return 0


def statement(library, args, out):
    rows = [{'date': format_date(line.date), 'description': line.description,
             'amount': format_money(line.amount), 'owed': format_money(line.owed)}
            for line in fines.statement(library, args.card)]
    out.write(render(rows, ('date', 'description', 'amount', 'owed'), args.format))
    return 0


def status(library, args, out):
    found = accounts.summary(library, args.card)
    lines = [
        f'card: {found.card}',
        f'name: {found.name}',
        f'type: {found.kind}',
        f'on loan: {found.on_loan}',
        f'overdue: {found.overdue}',
        f'holds waiting: {found.holds_waiting}',
        f'holds ready: {found.holds_ready}',
        f'owes: {format_money(found.owed)}',
        f'can borrow: {found.can_borrow}',
    ]
    print('\n'.join(lines), file=out)
    return 0


def member_loans(library, args, out):
    out.write(render(loans.member_loans(library, args.card), loans.COLUMNS, args.format))
    return 0


def overdue_report(library, args, out):
    out.write(render(overdue.overdue_rows(library), overdue.COLUMNS, args.format))
    return 0


def activity_report(library, args, out):
    rows = activity.activity_rows(library.ledger.entries(), args.year)
    out.write(render(rows, activity.COLUMNS, args.format))
    return 0


def find(library, args, out):
    out.write(render(search.search_rows(library, ' '.join(args.words)), search.COLUMNS, args.format))
    return 0


def send_notices(library, args, out):
    sent = notices.send_notices(library)
    print(f'{len(sent)} notices written', file=out)
    return 0


def join(library, args, out):
    member = membership.add_member(library, args.card, args.name, args.email, args.type, parse_date(args.born))
    print(f'joined {member.card}', file=out)
    return 0


def import_members(library, args, out):
    count = membership.import_members(library, args.file)
    print(f'imported {count} members', file=out)
    return 0


def export_members(library, args, out):
    count = membership.export_members(library, args.file)
    print(f'exported {count} members', file=out)
    return 0


def member_history(library, args, out):
    rows = members.history_rows(library, history.member_history(library, args.card))
    out.write(render(rows, members.HISTORY_COLUMNS, args.format))
    return 0


def copy_history(library, args, out):
    rows = members.history_rows(library, history.copy_history(library, args.barcode))
    out.write(render(rows, members.HISTORY_COLUMNS, args.format))
    return 0


def debtors(library, args, out):
    rows = members.debtor_rows(library, parse_money(args.at_least))
    out.write(render(rows, members.DEBTOR_COLUMNS, args.format))
    return 0


def member_profile(library, args, out):
    since = parse_date(args.active_since) if args.active_since else library.today().replace(year=library.today().year - 1)
    out.write(render(members.profile_rows(library, since), members.PROFILE_COLUMNS, args.format))
    return 0


def collection(library, args, out):
    out.write(render(stock.collection_rows(library), stock.COLLECTION_COLUMNS, args.format))
    return 0


def popular(library, args, out):
    rows = stock.popular_rows(library, parse_date(args.since), parse_date(args.until), args.top)
    out.write(render(rows, stock.POPULAR_COLUMNS, args.format))
    return 0


def idle(library, args, out):
    out.write(render(stock.idle_rows(library, parse_date(args.since)), stock.IDLE_COLUMNS, args.format))
    return 0


def take_stock(library, args, out):
    findings = compare_scans(library, args.branch.upper(), read_scans(Path(args.scans)))
    rows = [{'barcode': found.barcode, 'title': found.title, 'finding': found.finding} for found in findings]
    out.write(render(rows, ('barcode', 'title', 'finding'), args.format))
    return 0


def waive(library, args, out):
    owed = fines.waive(library, args.card, parse_money(args.amount))
    print(f'waived {format_money(parse_money(args.amount))}; balance {format_money(owed)}', file=out)
    return 0


def takings(library, args, out):
    rows = finance.daily_rows(library, parse_date(args.since), parse_date(args.until))
    out.write(render(rows, finance.COLUMNS, args.format))
    return 0


def check(library, args, out):
    problems = audit.check_library(library)
    for problem in problems:
        print(problem, file=out)
    print(f'{len(problems)} problems found', file=out)
    return 1 if problems else 0


def backup(library, args, out):
    archive, saved = write_backup(library.directory, Path(args.target), library.today())
    print(f'{archive.name}: {len(saved)} files', file=out)
    return 0


def restore(library, args, out):
    restored = restore_backup(Path(args.archive), library.directory)
    print(f"restored {', '.join(restored)}", file=out)
    return 0


def update_member(library, args, out):
    member = membership.update_member(library, args.card, args.name, args.email)
    print(f'updated {member.card}', file=out)
    return 0


def leave(library, args, out):
    member = membership.leave(library, args.card)
    print(f'{member.card} has left', file=out)
    return 0


def promote(library, args, out):
    cards = membership.promote_adults(library)
    print(f"{len(cards)} members now adult{': ' + ', '.join(cards) if cards else ''}", file=out)
    return 0


def show_settings(library, args, out):
    """Print the settings in force, written the way lending.ini takes them."""
    for field in fields(library.settings):
        value = getattr(library.settings, field.name)
        written = plain_amount if CONVERTERS[field.name] is parse_money else str
        if isinstance(value, dict):
            for material, number in sorted(value.items()):
                print(f'{field.name}.{material} = {written(number)}', file=out)
        elif isinstance(value, tuple):
            print(f"{field.name} = {','.join(written(part) for part in value)}", file=out)
        else:
            print(f'{field.name} = {written(value)}', file=out)
    return 0


def add_title(library, args, out):
    title = cataloguing.add_title(library, args.title, args.author, args.material, args.isbn)
    print(f'added {title.id}', file=out)
    return 0


def add_copy(library, args, out):
    copy = cataloguing.add_copy(library, args.title, args.barcode, args.branch, parse_money(args.price))
    print(f'added {copy.barcode} to {copy.title_id}', file=out)
    return 0


def withdraw(library, args, out):
    copy = cataloguing.withdraw(library, args.barcode)
    print(f'withdrew {copy.barcode}', file=out)
    return 0


def outbox(library, args, out):
    rows = outbox_log.outbox_rows(library, parse_date(args.since) if args.since else None)
    out.write(render(rows, outbox_log.COLUMNS, args.format))
    return 0


def receive(library, args, out):
    copy = transit.receive(library, args.barcode)
    print(f'{copy.barcode} back at {copy.branch}', file=out)
    return 0


def in_transit(library, args, out):
    out.write(render(transit.transit_rows(library), transit.COLUMNS, args.format))
    return 0


def note(library, args, out):
    count = notes.add_note(library, args.card, ' '.join(args.text))
    print(f'{library.member(args.card).card} has {count} notes', file=out)
    return 0


def show_notes(library, args, out):
    for day, text in notes.notes_for(library, args.card):
        print(f'{format_date(day)}  {text}', file=out)
    return 0


def due_on(library, args, out):
    day = parse_date(args.day) if args.day else library.today()
    out.write(render(due.due_rows(library, day), due.DUE_COLUMNS, args.format))
    return 0


def print_slip(library, args, out):
    out.write(due.slip(library, args.card))
    return 0


def amnesty(library, args, out):
    waived = fines.amnesty(library, parse_date(args.before))
    total = sum(waived.values())
    print(f'waived {format_money(total)} for {len(waived)} members', file=out)
    return 0


def lapsed(library, args, out):
    out.write(render(members.lapsed_rows(library, parse_date(args.since)), members.LAPSED_COLUMNS, args.format))
    return 0


def lateness(library, args, out):
    rows = stock.lateness_rows(library, parse_date(args.since), parse_date(args.until))
    out.write(render(rows, stock.LATENESS_COLUMNS, args.format))
    return 0


def clear_notes(library, args, out):
    removed = notes.clear_notes(library, args.card)
    print(f'removed {removed} notes', file=out)
    return 0


def demand(library, args, out):
    out.write(render(demand_report.demand_rows(library, args.at_least), demand_report.COLUMNS, args.format))
    return 0


def print_day_sheet(library, args, out):
    out.write(day_sheet(library, parse_date(args.day) if args.day else library.today()))
    return 0
