from unitconv.cli import main


def listing(capsys, *argv):
    assert main(['list', *argv]) == 0
    return capsys.readouterr().out.splitlines()


def test_twenty_units_a_page_with_a_footer(capsys):
    first = listing(capsys)
    assert len(first) == 21
    assert first[-1] == 'page 1 of 2'
    assert first[0].split()[0] == 'm'
    second = listing(capsys, '--page', '2')
    assert second[-1] == 'page 2 of 2'
    assert len(second) == 19
    assert second[0].split()[0] == 'L'
    assert second[-2].split()[0] == 'A'


def test_filtered_listing_is_one_page(capsys):
    lines = listing(capsys, '--dimension', 'length')
    assert lines[-1] == 'page 1 of 1'
    assert [line.split()[0] for line in lines[:-1]] == ['m', 'in', 'ft', 'yd', 'mi', 'nmi']
