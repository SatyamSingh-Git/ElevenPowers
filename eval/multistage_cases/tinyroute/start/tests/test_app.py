import pytest

from tinyroute import App, BadRequest, Client, HTTPError, Response


def make_app(**options):
    app = App(**options)

    @app.route('/users/<int:id>')
    def user(request, id):
        return {'id': id}

    @app.route('/echo', methods=['POST'])
    def echo(request):
        return request.json()

    @app.route('/boom')
    def boom(request):
        raise RuntimeError('broken')

    @app.route('/gone')
    def gone(request):
        class Gone(HTTPError):
            status = 410
        raise Gone()

    @app.route('/refuse')
    def refuse(request):
        raise BadRequest('no thanks')

    return app


def test_handler_gets_converted_parameters():
    response = Client(make_app()).get('/users/12')
    assert response.json() == {'id': 12}


def test_not_found_and_method_not_allowed():
    client = Client(make_app())
    assert client.get('/nope').status == 404
    response = client.delete('/users/1')
    assert response.status == 405
    assert response.header('Allow') == 'GET'


def test_http_errors_become_json_responses():
    client = Client(make_app())
    assert client.get('/refuse').json() == {'error': 'no thanks', 'status': 400}
    assert client.get('/gone').json() == {'error': 'gone', 'status': 410}
    assert client.post('/echo', body='{').json()['error'] == 'invalid JSON body'


def test_unexpected_exception_is_a_500():
    response = Client(make_app()).get('/boom')
    assert response.json() == {'error': 'internal server error', 'status': 500}


def test_debug_mode_lets_exceptions_through():
    with pytest.raises(RuntimeError, match='broken'):
        Client(make_app(debug=True)).get('/boom')


def test_middleware_runs_in_order_added():
    app = make_app()
    calls = []

    def outer(request, call_next):
        calls.append('outer')
        return call_next(request)

    def inner(request, call_next):
        calls.append('inner')
        response = call_next(request)
        return Response(response.text.upper(), response.status)

    app.use(outer)
    app.use(inner)
    response = Client(app).get('/users/3')
    assert calls == ['outer', 'inner']
    assert response.text == '{"ID": 3}'


def test_request_knows_its_route():
    app = App()

    @app.route('/a/<int:n>', name='a')
    def handler(request, n):
        return [request.route.name, request.params, request.app is app]

    assert Client(app).get('/a/1').json() == ['a', {'n': 1}, True]
