"""Barcode scan files from the stocktake scanners: one barcode per line.

The scanners repeat a barcode when a copy is scanned twice and some add a
trailing carriage return; both are harmless and are tidied away here.
"""


def read_scans(path):
    """The barcodes in the order first scanned, each once."""
    lines = (line.strip() for line in path.read_text(encoding='utf-8').splitlines())
    return list(dict.fromkeys(line for line in lines if line))
