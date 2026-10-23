from tinyroute import App, Client, Request


def test_repeated_names_keep_every_value_in_order():
    request = Request.from_url('GET', '/search?tag=a&q=x&tag=b&tag=c')
    assert request.query == {'tag': ['a', 'b', 'c'], 'q': ['x']}


def test_names_without_values():
    request = Request.from_url('GET', '/search?flag&empty=&q=1')
    assert request.query == {'flag': [''], 'empty': [''], 'q': ['1']}


def test_no_query_string():
    assert Request.from_url('GET', '/search').query == {}


def test_handlers_see_the_lists():
    app = App()

    @app.route('/search')
    def search(request):
        return request.query

    assert Client(app).get('/search?tag=a&tag=b').json() == {'tag': ['a', 'b']}
