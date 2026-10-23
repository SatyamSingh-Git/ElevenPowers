import pytest

from tinyroute import App, Client, ClientError, HTTPError


class Teapot(HTTPError):
    status = 418
    code = 'teapot'


class Gone(HTTPError):
    status = 410


class Locked(HTTPError):
    status = 423


def make_app():
    app = App()

    @app.route('/tea')
    def tea(request):
        raise Teapot('short and stout')

    @app.route('/gone')
    def gone(request):
        raise Gone()

    @app.route('/locked')
    def locked(request):
        raise Locked('try later')

    return app


def test_subclass_with_its_own_code():
    response = Client(make_app()).get('/tea')
    assert response.status == 418
    assert response.json() == {'error': {'code': 'teapot', 'message': 'short and stout'}, 'status': 418}


def test_subclass_without_a_code_gets_http_status():
    client = Client(make_app())
    assert client.get('/gone').json() == {'error': {'code': 'http_410', 'message': 'gone'}, 'status': 410}
    assert client.get('/locked').json() == {'error': {'code': 'http_423', 'message': 'try later'},
                                            'status': 423}


def test_client_error_message_with_a_custom_code():
    with pytest.raises(ClientError) as caught:
        Client(make_app()).get('/tea', raise_for_status=True)
    assert caught.value.status == 418
    assert caught.value.message == 'short and stout'
