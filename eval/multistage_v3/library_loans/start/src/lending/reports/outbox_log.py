"""What went out in the mail runs: notices per day and kind, and who had no email."""
from collections import Counter

from ..storage.outbox import read_outbox

COLUMNS = ('date', 'kind', 'emailed', 'posted')


def outbox_rows(library, since=None):
    """Counts per day and kind; members without an email address get a letter instead."""
    emailed, posted = Counter(), Counter()
    for record in read_outbox(library.directory):
        if since is not None and record['date'] < since.isoformat():
            continue
        key = (record['date'], record['kind'])
        if record['email']:
            emailed[key] += 1
        else:
            posted[key] += 1
    return [{'date': day, 'kind': kind, 'emailed': emailed[(day, kind)], 'posted': posted[(day, kind)]}
            for day, kind in sorted(set(emailed) | set(posted))]
