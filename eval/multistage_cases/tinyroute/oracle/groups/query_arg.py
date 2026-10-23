from tinyroute import App, Client, Request


def test_arg_gives_the_first_value():
    request = Request.from_url('GET', '/search?tag=a&tag=b&q=x')
    assert request.arg('tag') == 'a'
    assert request.arg('q') == 'x'


def test_arg_default_when_absent():
    request = Request.from_url('GET', '/search?flag')
    assert request.arg('missing') is None
    assert request.arg('missing', 'fallback') == 'fallback'
    assert request.arg('flag') == ''
    assert request.arg('flag', 'fallback') == ''


def test_arg_inside_a_handler():
    app = App()

    @app.route('/greet')
    def greet(request):
        return f"hello {request.arg('name', 'world')}"

    client = Client(app)
    assert client.get('/greet?name=ada&name=bob').text == 'hello ada'
    assert client.get('/greet').text == 'hello world'
