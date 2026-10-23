import pytest

from tinyroute import App, Client, ClientError, Response, redirect
from tinyroute.middleware import access_log, cors, request_id


def make_app():
    app = App()

    @app.route('/ping', methods=['GET', 'POST'])
    def ping(request):
        return getattr(request, 'id', 'pong')

    @app.route('/forbidden')
    def forbidden(request):
        return Response('keep out', status=403)

    @app.route('/old')
    def old(request):
        return redirect('/ping')

    @app.route('/cookie')
    def cookie(request):
        response = Response('ok')
        response.set_cookie('session', 'abc', max_age=60)
        return response

    return app


def test_client_error_reads_the_message_of_an_error_response():
    client = Client(make_app(), raise_for_status=True)
    with pytest.raises(ClientError) as caught:
        client.get('/nope')
    assert caught.value.status == 404
    assert caught.value.message == "no route matches '/nope'"
    assert str(caught.value) == "404 Not Found: no route matches '/nope'"


def test_client_error_for_wrong_method():
    with pytest.raises(ClientError) as caught:
        Client(make_app()).delete('/ping', raise_for_status=True)
    assert caught.value.message == "method 'DELETE' not allowed for '/ping'"
    assert str(caught.value).startswith('405 Method Not Allowed: ')


def test_client_error_from_a_plain_text_response():
    with pytest.raises(ClientError) as caught:
        Client(make_app()).get('/forbidden', raise_for_status=True)
    assert caught.value.message == 'keep out'
    assert str(caught.value) == '403 Forbidden: keep out'


def test_client_follows_redirects_when_asked():
    client = Client(make_app())
    assert client.get('/old').status == 302
    assert client.get('/old', follow_redirects=True).text == 'pong'


def test_cookie_header():
    response = Client(make_app()).get('/cookie')
    assert response.header('set-cookie') == 'session=abc; Path=/; Max-Age=60; HttpOnly'


def test_cors_allows_listed_origin_only():
    app = make_app()
    app.use(cors(['https://a.example']))
    client = Client(app)
    allowed = client.get('/ping', headers={'Origin': 'https://a.example'})
    assert allowed.header('Access-Control-Allow-Origin') == 'https://a.example'
    assert allowed.header('Vary') == 'Origin'
    other = client.get('/ping', headers={'Origin': 'https://b.example'})
    assert other.header('Access-Control-Allow-Origin') is None
    assert other.text == 'pong'


def test_cors_answers_preflight():
    app = make_app()
    app.use(cors(['*'], methods=['GET', 'POST'], max_age=60))
    response = Client(app).options('/ping', headers={
        'Origin': 'https://b.example', 'Access-Control-Request-Method': 'POST'})
    assert response.status == 204
    assert response.header('Access-Control-Allow-Methods') == 'GET, POST'
    assert response.header('Access-Control-Max-Age') == '60'
    assert response.header('Access-Control-Allow-Origin') == 'https://b.example'


def test_request_id_numbers_requests_and_echoes_given_ids():
    app = make_app()
    app.use(request_id(start=7))
    client = Client(app)
    first = client.get('/ping')
    assert (first.text, first.header('X-Request-Id')) == ('7', '7')
    assert client.get('/ping').header('x-request-id') == '8'
    given = client.get('/ping', headers={'X-Request-Id': 'abc'})
    assert (given.text, given.header('X-Request-Id')) == ('abc', 'abc')


def test_access_log_writes_one_line_per_request():
    lines = []
    app = make_app()
    app.use(access_log(lines.append))
    client = Client(app)
    client.get('/ping')
    client.get('/missing')
    assert lines == ['GET /ping 200', 'GET /missing 404']
