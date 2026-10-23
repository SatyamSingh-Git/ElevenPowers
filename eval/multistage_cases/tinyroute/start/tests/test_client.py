import pytest

from tinyroute import App, Client, ClientError, Response, TooManyRedirects, redirect


def make_app():
    app = App()

    @app.route('/echo', methods=['POST', 'PUT'])
    def echo(request):
        return {'body': request.json(), 'type': request.header('Content-Type')}

    @app.route('/old')
    def old(request):
        return redirect('/new')

    @app.route('/new')
    def new(request):
        return 'new'

    @app.route('/loop')
    def loop(request):
        return redirect('/loop')

    @app.route('/forbidden')
    def forbidden(request):
        return Response('keep out', status=403)

    return app


def test_json_body_is_sent_with_content_type():
    response = Client(make_app()).post('/echo', json_body={'a': 1})
    assert response.json() == {'body': {'a': 1}, 'type': 'application/json'}


def test_redirects_are_followed_only_when_asked():
    client = Client(make_app())
    assert client.get('/old').status == 302
    assert client.get('/old', follow_redirects=True).text == 'new'


def test_redirect_loop_stops():
    with pytest.raises(TooManyRedirects, match="more than 5 redirects from '/loop'"):
        Client(make_app()).get('/loop', follow_redirects=True)


def test_client_error_reads_the_error_message():
    with pytest.raises(ClientError) as caught:
        Client(make_app(), raise_for_status=True).get('/missing')
    assert caught.value.status == 404
    assert caught.value.message == "no route matches '/missing'"
    assert str(caught.value) == "404 Not Found: no route matches '/missing'"


def test_client_error_from_plain_text_response():
    with pytest.raises(ClientError, match='403 Forbidden: keep out'):
        Client(make_app()).get('/forbidden', raise_for_status=True)


def test_errors_do_not_raise_by_default():
    assert Client(make_app()).get('/missing').status == 404
