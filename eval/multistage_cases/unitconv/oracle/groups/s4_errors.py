from unitconv.cli import main


def run(capsys, *argv):
    try:
        code = main(list(argv))
    except SystemExit as exit:
        code = exit.code
    out, err = capsys.readouterr()
    return code, out, err


def test_page_past_the_end(capsys):
    code, out, err = run(capsys, 'list', '--page', '3')
    assert (code, out) == (2, '')
    assert err.strip().endswith('page 3 out of range (1-2)')


def test_page_below_one(capsys):
    code, _, err = run(capsys, 'list', '--page', '0')
    assert code == 2
    assert err.strip().endswith('page 0 out of range (1-2)')


def test_page_past_the_end_of_a_filtered_listing(capsys):
    code, _, err = run(capsys, 'list', '--dimension', 'mass', '--page', '2')
    assert code == 2
    assert err.strip().endswith('page 2 out of range (1-1)')
