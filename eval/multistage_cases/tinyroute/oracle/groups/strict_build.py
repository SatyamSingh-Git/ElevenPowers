import pytest

from tinyroute import App, BuildError


def make_app():
    app = App()

    @app.route('/users/<int:id>')
    def user(request, id):
        return 'user'

    @app.route('/items')
    def items(request):
        return 'items'

    return app


def test_unknown_keyword_is_refused():
    with pytest.raises(BuildError) as caught:
        make_app().url_for('user', id=3, tba='posts')
    assert str(caught.value) == "unknown parameter 'tba' for route 'user'"


def test_unknown_keyword_on_a_route_without_parameters():
    with pytest.raises(BuildError) as caught:
        make_app().url_for('items', pgae=2)
    assert str(caught.value) == "unknown parameter 'pgae' for route 'items'"


def test_path_parameters_alone_still_build():
    assert make_app().url_for('user', id=3) == '/users/3'
    assert make_app().url_for('items') == '/items'
