from tinyroute import App, BadRequest, Client


def make_app():
    app = App()

    @app.route('/users/<int:id>', methods=['GET', 'PUT'])
    def user(request, id):
        return {'id': id}

    @app.route('/refuse')
    def refuse(request):
        raise BadRequest('no thanks')

    @app.route('/echo', methods=['POST'])
    def echo(request):
        return request.json()

    @app.route('/boom')
    def boom(request):
        raise RuntimeError('broken')

    return app


def test_not_found_body():
    response = Client(make_app()).get('/nope')
    assert response.status == 404
    assert response.json() == {'error': {'code': 'not_found', 'message': "no route matches '/nope'"},
                               'status': 404}


def test_method_not_allowed_body():
    response = Client(make_app()).delete('/users/1')
    assert response.status == 405
    assert response.json() == {
        'error': {'code': 'method_not_allowed', 'message': "method 'DELETE' not allowed for '/users/1'"},
        'status': 405}
    assert response.header('Allow') == 'GET, PUT'


def test_bad_request_body():
    client = Client(make_app())
    assert client.get('/refuse').json() == {'error': {'code': 'bad_request', 'message': 'no thanks'},
                                            'status': 400}
    assert client.post('/echo', body='{').json() == {
        'error': {'code': 'bad_request', 'message': 'invalid JSON body'}, 'status': 400}


def test_unexpected_exception_body():
    response = Client(make_app()).get('/boom')
    assert response.status == 500
    assert response.json() == {'error': {'code': 'internal_error', 'message': 'internal server error'},
                               'status': 500}


def test_successful_responses_are_untouched():
    assert Client(make_app()).get('/users/3').json() == {'id': 3}
