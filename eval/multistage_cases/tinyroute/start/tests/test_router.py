import pytest

from tinyroute import BuildError, MethodNotAllowed, NotFound, RouteError, Router


def show(request, id):
    return id


def update(request, id):
    return id


def index(request):
    return 'index'


def make_router():
    router = Router()
    router.add('/users/<int:id>', show)
    router.add('/users/<int:id>', update, methods=['put', 'PATCH'])
    router.add('/', index)
    return router


def test_match_returns_route_and_parameters():
    route, params = make_router().match('get', '/users/7')
    assert route.handler is show
    assert params == {'id': 7}


def test_match_picks_the_route_for_the_method():
    route, _ = make_router().match('PATCH', '/users/7')
    assert route.handler is update


def test_unmatched_path_is_not_found():
    with pytest.raises(NotFound, match="no route matches '/nope'"):
        make_router().match('GET', '/nope')


def test_wrong_method_lists_allowed_methods():
    with pytest.raises(MethodNotAllowed) as caught:
        make_router().match('DELETE', '/users/7')
    assert caught.value.allowed == ['GET', 'PATCH', 'PUT']
    assert caught.value.message == "method 'DELETE' not allowed for '/users/7'"


def test_routes_are_tried_in_registration_order():
    router = Router()
    router.add('/users/<name>', show, name='by_name')
    router.add('/users/me', index, name='me')
    assert router.match('GET', '/users/me')[0].name == 'by_name'


def test_names_default_to_the_handler_name():
    router = make_router()
    assert router.url_for('show', id=5) == '/users/5'
    assert router.url_for('index') == '/'


def test_url_for_puts_extra_values_in_the_query_string():
    assert make_router().url_for('show', id=5, tab='posts') == '/users/5?tab=posts'


def test_url_for_unknown_name():
    with pytest.raises(BuildError, match="no route named 'nope'"):
        make_router().url_for('nope')


def test_duplicate_names_are_refused():
    router = make_router()
    with pytest.raises(RouteError, match="duplicate route name 'show'"):
        router.add('/again/<int:id>', show)


def test_lambda_routes_have_no_name():
    router = Router()
    router.add('/a', lambda request: 'a')
    router.add('/b', lambda request: 'b')
    assert [route.name for route in router.routes] == [None, None]


def test_include_mounts_under_a_prefix():
    api = Router()
    api.include('/api', make_router())
    assert api.match('GET', '/api/users/1')[1] == {'id': 1}
    assert api.url_for('show', id=1) == '/api/users/1'
    with pytest.raises(RouteError):
        api.include('api/', Router())
