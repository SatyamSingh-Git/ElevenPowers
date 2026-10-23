from tinyroute import Response


def test_constructor_takes_a_mapping_or_pairs():
    from_mapping = Response(headers={'X-One': '1'})
    assert from_mapping.header('x-one') == '1'
    from_pairs = Response(headers=[('Link', '<a>'), ('Link', '<b>')])
    assert from_pairs.header_values('link') == ['<a>', '<b>']
    assert from_pairs.header('LINK') == '<a>'


def test_set_header_replaces_every_value():
    response = Response(headers=[('Link', '<a>'), ('Link', '<b>')])
    response.set_header('link', '<c>')
    assert response.header_values('Link') == ['<c>']
    assert response.header('Link') == '<c>'


def test_missing_header():
    response = Response()
    assert response.header('X-Nothing') is None
    assert response.header_values('X-Nothing') == []


def test_add_header_keeps_earlier_values():
    response = Response()
    response.add_header('Vary', 'Accept')
    response.add_header('vary', 'Origin')
    assert response.header_values('VARY') == ['Accept', 'Origin']
