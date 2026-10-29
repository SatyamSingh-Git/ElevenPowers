"""outbox.jsonl: notices waiting for the mail run, one JSON object per line.

The mailer picks the file up overnight; members without an email address are
sent a printed letter instead.
"""
import json

from ..model.dates import format_date

FILE = 'outbox.jsonl'


def append_notices(directory, notices):
    with (directory / FILE).open('a', encoding='utf-8', newline='\n') as out:
        for notice in notices:
            out.write(json.dumps({'date': format_date(notice.date), 'card': notice.card, 'email': notice.email,
                                  'kind': notice.kind, 'subject': notice.subject, 'body': notice.body}) + '\n')


def read_outbox(directory):
    path = directory / FILE
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding='utf-8').splitlines() if line.strip()]
