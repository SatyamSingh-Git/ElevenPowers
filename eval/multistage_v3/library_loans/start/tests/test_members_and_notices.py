from datetime import date
import json

import pytest

from lending.errors import LendingError
from lending.services import membership, notices
from lending.services.circulation import checkout
from lending.services.holds import place_hold
from lending.storage.outbox import read_outbox


def test_join(at, home):
    member = membership.add_member(at(), 'm3001', 'Grace Hopper', 'grace@example.org', 'adult', date(1970, 12, 9))
    assert member.card == 'M3001'
    assert member.joined == date(2026, 3, 2)
    saved = json.loads((home / 'members.json').read_text(encoding='utf-8'))
    assert [record['card'] for record in saved] == ['C2001', 'M1001', 'M1002', 'M3001']


@pytest.mark.parametrize('card, kind, code', [
    ('M1001', 'adult', 'duplicate_member'),
    ('X12', 'adult', 'invalid_member'),
    ('M3001', 'senior', 'invalid_member'),
])
def test_join_refusals(at, card, kind, code):
    with pytest.raises(LendingError) as raised:
        membership.add_member(at(), card, 'Someone', '', kind, date(1970, 1, 1))
    assert raised.value.code == code


def test_import(at, tmp_path):
    source = tmp_path / 'signups.csv'
    source.write_text('card,name,email,type,born,joined,branch\n'
                      'm3001,Grace Hopper,grace@example.org,Adult,1970-12-09,2026-02-27,CEN\n'
                      'C3002,Bobby Tables,,child,2016-01-31,2026-02-28,RIV\n', encoding='utf-8')
    assert membership.import_members(at(), source) == 2
    library = at()
    assert library.members['M3001'].kind == 'adult'
    assert library.members['C3002'].born == date(2016, 1, 31)


@pytest.mark.parametrize('rows, message', [
    ('card,name\nM3001,Grace\n', 'row 1: missing columns email, type, born, joined'),
    ('card,name,email,type,born,joined\nM3001,Grace,,adult,9 Dec 1970,2026-02-27\n', 'row 2: not a date: 9 Dec 1970'),
    ('card,name,email,type,born,joined\nM3001,,,adult,1970-12-09,2026-02-27\n', 'row 2: name is empty'),
])
def test_import_refuses_bad_rows(at, tmp_path, rows, message):
    source = tmp_path / 'signups.csv'
    source.write_text(rows, encoding='utf-8')
    with pytest.raises(LendingError) as raised:
        membership.import_members(at(), source)
    assert raised.value.message == message


def test_export(at, tmp_path):
    target = tmp_path / 'members.csv'
    assert membership.export_members(at(), target) == 3
    lines = target.read_text(encoding='utf-8').splitlines()
    assert lines[0] == 'card,name,email,type,born,joined'
    assert lines[2] == 'M1001,Ada Lovelace,ada@example.org,adult,1990-04-02,2020-01-15'


def test_children_become_adults_at_eighteen(at):
    membership.add_member(at(), 'C3003', 'Young Person', '', 'child', date(2008, 3, 3))
    assert membership.promote_adults(at(date(2026, 3, 2))) == []
    assert membership.promote_adults(at(date(2026, 3, 3))) == ['C3003']


def test_cannot_leave_with_loans(at):
    checkout(at(), 'M1001', '31000001')
    with pytest.raises(LendingError) as raised:
        membership.leave(at(), 'M1001')
    assert raised.value.message == 'M1001 cannot leave: items are still on loan'


def test_overdue_reminders_on_notice_days(at):
    library = at()
    checkout(library, 'M1001', '31000001')
    checkout(library, 'M1001', '31000003')
    assert notices.overdue_notices(at(date(2026, 3, 29))) == []
    [notice] = notices.overdue_notices(at(date(2026, 3, 30)))
    assert notice.subject == 'Overdue: 2 item(s)'
    assert 'Dune (due 2026-03-23)' in notice.body


def test_notices_are_written_once_a_day(at, home):
    place_hold(at(), 'M1002', 'T0002')
    assert [notice.kind for notice in notices.send_notices(at())] == ['hold_ready']
    assert notices.send_notices(at()) == []
    [record] = read_outbox(home)
    assert record['subject'] == 'Ready to collect: Dune'
    assert 'collect it by 2026-03-09' in record['body']


def test_courtesy_reminder(at):
    checkout(at(), 'M1001', '31000004')
    [notice] = notices.courtesy_notices(at(date(2026, 3, 7)))
    assert notice.subject == 'Due soon: 1 item(s)'
