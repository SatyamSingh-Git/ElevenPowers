"""Stocktake: comparing what a branch's scanners saw with what should be on its shelves.

Every copy belonging to the branch that is neither out on loan nor written off
should turn up in the scan. Anything else the scanners saw is worth a look too:
copies the ledger says are out, copies written off, copies from other branches
and barcodes the catalogue does not know.
"""
from dataclasses import dataclass

MISSING = 'missing'
ON_LOAN = 'scanned but on loan'
FOUND = 'scanned but written off'
VISITING = 'belongs to another branch'
UNKNOWN = 'not in the catalogue'


@dataclass
class Finding:
    barcode: str
    title: str
    finding: str


def stocktake(library, branch, scanned):
    seen = set(scanned)
    findings = []
    for title in library.catalogue.titles():
        for copy in title.copies:
            if copy.branch != branch:
                continue
            expected = copy.barcode not in library.loans and copy.barcode not in library.lost
            if expected and copy.barcode not in seen:
                findings.append(Finding(copy.barcode, title.title, MISSING))
    known = {copy.barcode: title for title in library.catalogue.titles() for copy in title.copies}
    for barcode in scanned:
        title = known.get(barcode)
        if title is None:
            findings.append(Finding(barcode, '', UNKNOWN))
        elif barcode in library.loans:
            findings.append(Finding(barcode, title.title, ON_LOAN))
        elif barcode in library.lost:
            findings.append(Finding(barcode, title.title, FOUND))
        elif library.catalogue.copy(barcode).branch != branch:
            findings.append(Finding(barcode, title.title, VISITING))
    return sorted(findings, key=lambda finding: (finding.finding, finding.barcode))
