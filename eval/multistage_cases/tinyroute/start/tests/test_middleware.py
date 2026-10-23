from tinyroute import App, Client
from tinyroute.middleware import access_log, cors, request_id


def make_app():
    app = App()

    @app.route('/ping', methods=['GET', 'POST'])
    def ping(request):
        return getattr(request, 'id', 'pong')

    return app


def test_cors_allows_listed_origin():
    app = make_app()
    app.use(cors(['https://a.example']))
    response = Client(app).get('/ping', headers={'Origin': 'https://a.example'})
    assert response.header('Access-Control-Allow-Origin') == 'https://a.example'
    assert response.header('Vary') == 'Origin'


def test_cors_ignores_other_origins():
    app = make_app()
    app.use(cors(['https://a.example']))
    response = Client(app).get('/ping', headers={'Origin': 'https://b.example'})
    assert response.header('Access-Control-Allow-Origin') is None


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
    assert client.get('/ping').header('X-Request-Id') == '8'
    assert client.get('/ping', headers={'X-Request-Id': 'abc'}).text == 'abc'


def test_access_log_writes_one_line_per_request():
    lines = []
    app = make_app()
    app.use(access_log(lines.append))
    client = Client(app)
    client.get('/ping')
    client.get('/missing')
    assert lines == ['GET /ping 200', 'GET /missing 404']
