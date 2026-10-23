from urllib.parse import parse_qs, urlsplit

from tinyroute import App


def make_app():
    app = App()

    @app.route('/users/<int:id>')
    def user(request, id):
        return 'user'

    @app.route('/search')
    def search(request):
        return 'search'

    return app


def test_query_mapping_is_appended():
    assert make_app().url_for('user', id=3, _query={'tab': 'posts'}) == '/users/3?tab=posts'


def test_list_values_repeat_the_name():
    url = make_app().url_for('search', _query={'tag': ['a', 'b'], 'q': 'x y'})
    parts = urlsplit(url)
    assert parts.path == '/search'
    assert parse_qs(parts.query) == {'tag': ['a', 'b'], 'q': ['x y']}
    assert parts.query.count('tag=') == 2


def test_empty_query_adds_nothing():
    app = make_app()
    assert app.url_for('search', _query={}) == '/search'
    assert app.url_for('user', id=1) == '/users/1'
