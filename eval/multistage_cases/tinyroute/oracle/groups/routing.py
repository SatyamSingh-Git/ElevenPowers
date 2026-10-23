from urllib.parse import parse_qs, urlsplit

import pytest

from tinyroute import App, BuildError, Client, paginate


def make_app():
    app = App()

    @app.route('/users/<int:id>')
    def user(request, id):
        return {'id': id, 'type': type(id).__name__}

    @app.route('/posts/<slug:slug>', methods=['GET', 'PUT'])
    def post(request, slug):
        return slug

    @app.route('/files/<path:filename>')
    def file(request, filename):
        return filename

    @app.route('/items')
    def items(request):
        return paginate(request, list(range(25)))

    @app.route('/tags/<slug:tag>/items')
    def tagged(request, tag):
        return paginate(request, [tag] * 12, per_page=5)

    return app


def link(url):
    parts = urlsplit(url)
    return parts.path, parse_qs(parts.query)


def test_int_parameter_is_converted():
    assert Client(make_app()).get('/users/42').json() == {'id': 42, 'type': 'int'}


def test_typed_parameters_refuse_other_text():
    client = Client(make_app())
    assert client.get('/users/abc').status == 404
    assert client.get('/posts/Hello').status == 404
    assert client.get('/posts/hello-world').text == 'hello-world'


def test_path_parameter_spans_slashes_and_is_decoded():
    assert Client(make_app()).get('/files/a/b%20c.txt').text == 'a/b c.txt'


def test_unknown_path_is_404():
    response = Client(make_app()).get('/nowhere')
    assert response.status == 404
    assert "no route matches '/nowhere'" in response.text


def test_wrong_method_is_405_with_allow_header():
    response = Client(make_app()).delete('/posts/hello')
    assert response.status == 405
    assert response.header('Allow') == 'GET, PUT'
    assert "method 'DELETE' not allowed for '/posts/hello'" in response.text


def test_url_for_builds_paths():
    app = make_app()
    assert app.url_for('user', id=7) == '/users/7'
    assert app.url_for('file', filename='a/b c.txt') == '/files/a/b%20c.txt'
    assert app.url_for('items') == '/items'


def test_url_for_refuses_missing_and_invalid_values():
    app = make_app()
    with pytest.raises(BuildError, match="missing parameter 'id' for route 'user'"):
        app.url_for('user')
    with pytest.raises(BuildError):
        app.url_for('user', id='abc')
    with pytest.raises(BuildError, match="no route named 'nobody'"):
        app.url_for('nobody')


def test_pagination_reads_the_page_and_links_neighbours():
    page = Client(make_app()).get('/items?page=2').json()
    assert page['items'] == list(range(10, 20))
    assert (page['page'], page['per_page'], page['total']) == (2, 10, 25)
    assert link(page['next']) == ('/items', {'page': ['3']})
    assert link(page['prev']) == ('/items', {'page': ['1']})


def test_pagination_first_and_last_pages():
    client = Client(make_app())
    first = client.get('/items').json()
    assert first['prev'] is None
    assert link(first['next']) == ('/items', {'page': ['2']})
    last = client.get('/items?page=3').json()
    assert last['items'] == list(range(20, 25))
    assert last['next'] is None


def test_pagination_keeps_per_page_and_path_parameters():
    client = Client(make_app())
    page = client.get('/items?per_page=4&page=2').json()
    assert page['items'] == [4, 5, 6, 7]
    assert link(page['next']) == ('/items', {'page': ['3'], 'per_page': ['4']})
    tagged = client.get('/tags/red/items?page=2').json()
    assert tagged['items'] == ['red'] * 5
    assert link(tagged['next']) == ('/tags/red/items', {'page': ['3']})


def test_pagination_refuses_bad_numbers():
    client = Client(make_app())
    for query in ('page=0', 'page=x', 'per_page=-1'):
        response = client.get(f'/items?{query}')
        assert response.status == 400
        assert 'must be a positive integer' in response.text
