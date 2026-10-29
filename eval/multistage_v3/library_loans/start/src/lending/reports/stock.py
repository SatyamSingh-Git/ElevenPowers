"""Reports on the collection itself: what each branch holds and what gets borrowed."""
from collections import Counter

from .._generated import BRANCHES, MATERIALS
from ..model.dates import format_date
from ..model.money import format_money
from ..services.history import spells

COLLECTION_COLUMNS = ('branch', 'material', 'copies', 'on_loan', 'lost', 'value')
POPULAR_COLUMNS = ('rank', 'id', 'title', 'issues')
IDLE_COLUMNS = ('barcode', 'title', 'branch', 'last_issued')
LATENESS_COLUMNS = ('material', 'returns', 'late', 'late_share')


def collection_rows(library):
    """Copies by branch and material, with how many are out and what the stock is worth."""
    totals = {}
    for title in library.catalogue.titles():
        for copy in title.copies:
            row = totals.setdefault((copy.branch, title.material), {'copies': 0, 'on_loan': 0, 'lost': 0, 'value': 0})
            row['copies'] += 1
            row['on_loan'] += copy.barcode in library.loans
            row['lost'] += copy.barcode in library.lost
            row['value'] += copy.price
    return [{'branch': BRANCHES[branch], 'material': MATERIALS[material], **counts,
             'value': format_money(counts['value'])}
            for (branch, material), counts in sorted(totals.items())]


def popular_rows(library, since, until, top=10):
    """The most issued titles between two dates, inclusive; ties go to the title first alphabetically."""
    issues = Counter()
    for spell in spells(library.ledger.entries()):
        if since <= spell.issued <= until:
            issues[library.catalogue.copy(spell.barcode).title_id] += 1
    ranked = sorted(issues.items(), key=lambda item: (-item[1], library.catalogue.title(item[0]).title.lower()))
    return [{'rank': rank, 'id': title_id, 'title': library.catalogue.title(title_id).title, 'issues': count}
            for rank, (title_id, count) in enumerate(ranked[:top], 1)]


def idle_rows(library, since):
    """Copies not issued since `since`: candidates for moving to another branch or withdrawing."""
    last = {}
    for spell in spells(library.ledger.entries()):
        last[spell.barcode] = spell.issued
    rows = []
    for title in library.catalogue.titles():
        for copy in title.copies:
            issued = last.get(copy.barcode)
            if copy.barcode not in library.lost and (issued is None or issued < since):
                rows.append({'barcode': copy.barcode, 'title': title.title, 'branch': copy.branch,
                             'last_issued': format_date(issued) if issued else 'never'})
    return sorted(rows, key=lambda row: (row['branch'], row['last_issued'], row['barcode']))


def lateness_rows(library, since, until):
    """How often each material comes back late, between two dates inclusive."""
    counts = {}
    for entry in library.ledger.entries():
        if entry.event != 'return' or not since <= entry.date <= until:
            continue
        material = library.catalogue.material_of(entry.barcode)
        row = counts.setdefault(material, [0, 0])
        row[0] += 1
        row[1] += entry.date > entry.due
    return [{'material': MATERIALS[material], 'returns': returned, 'late': late,
             'late_share': f'{100 * late // returned}%'}
            for material, (returned, late) in sorted(counts.items())]
