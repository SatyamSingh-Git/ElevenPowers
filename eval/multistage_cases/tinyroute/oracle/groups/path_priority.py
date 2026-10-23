from tinyroute import App, Client


def make_app():
    app = App()

    @app.route('/files/<path:rest>')
    def anything(request, rest):
        return f'any {rest}'

    @app.route('/files/<name>/raw')
    def raw(request, name):
        return f'raw {name}'

    @app.route('/n/<int:id>')
    def number(request, id):
        return f'number {id}'

    @app.route('/n/<word>')
    def word(request, word):
        return f'word {word}'

    return app


def test_parameter_wins_over_an_earlier_path_parameter():
    client = Client(make_app())
    assert client.get('/files/a/raw').text == 'raw a'
    assert client.get('/files/a/b/raw').text == 'any a/b/raw'
    assert client.get('/files/a').text == 'any a'


def test_equally_specific_routes_keep_their_order():
    client = Client(make_app())
    assert client.get('/n/12').text == 'number 12'
    assert client.get('/n/twelve').text == 'word twelve'
