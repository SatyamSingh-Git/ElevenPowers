import json


def setup(run):
    run('add-location', 'A1')
    run('add-location', 'B2', '--kind', 'bin')
    run('add-item', 'BOLT-M6', 'M6 bolt', '--reorder', '20', '--cost', '0.12')


def test_movement_messages(run):
    setup(run)
    assert run('receive', 'bolt-m6', '50', 'a1')[1] == 'received 50 BOLT-M6 at A1 (now 50 there)\n'
    assert run('transfer', 'BOLT-M6', '10', 'A1', 'B2')[1] == 'moved 10 BOLT-M6 from A1 to B2 (now 10 at B2)\n'
    assert run('issue', 'BOLT-M6', '30', 'A1')[1] == 'issued 30 BOLT-M6 from A1 (now 10 there)\n'
    assert run('issue', 'BOLT-M6', '1', 'A1')[1] == (
        'issued 1 BOLT-M6 from A1 (now 9 there)\n'
        'warning: BOLT-M6 is below its reorder point (19 < 20)\n'
    )
    status, out, _ = run('adjust', 'BOLT-M6', 'B2', '8')
    assert status == 0 and out.startswith('adjusted BOLT-M6 at B2 to 8 (-2)\n')


def test_refusal_exits_1_and_keeps_the_file(run):
    setup(run)
    before = run.path.read_text(encoding='utf-8')
    status, out, err = run('issue', 'BOLT-M6', '1', 'A1')
    assert (status, out, err) == (1, '', 'error: insufficient stock: BOLT-M6 at A1 has 0, needs 1\n')
    assert run.path.read_text(encoding='utf-8') == before


def test_reports(run):
    setup(run)
    run('receive', 'BOLT-M6', '12', 'A1')
    assert run('low')[1].splitlines()[1].split() == ['BOLT-M6', 'M6', 'bolt', '12', '20', '8']
    assert run('value')[1].splitlines()[-1].split() == ['TOTAL', '$1.44']
    assert 'on hand: 12' in run('show', 'BOLT-M6')[1]


def test_history_and_check(run):
    setup(run)
    run('receive', 'BOLT-M6', '12', 'A1', '--note', 'PO 7')
    run('transfer', 'BOLT-M6', '2', 'A1', 'B2')
    assert run('history', 'BOLT-M6')[1].splitlines() == [
        '#1 BOLT-M6 receive 12 into A1  (PO 7)',
        '#2 BOLT-M6 transfer 2 from A1 to B2',
    ]
    assert run('check') == (0, 'ok: stock matches 2 movements\n', '')
    doc = json.loads(run.path.read_text(encoding='utf-8'))
    doc['stock']['BOLT-M6']['A1'] = 11
    run.path.write_text(json.dumps(doc), encoding='utf-8')
    assert run('check')[:2] == (1, 'mismatch: BOLT-M6 at A1: stock table 11, movements 10\n')
