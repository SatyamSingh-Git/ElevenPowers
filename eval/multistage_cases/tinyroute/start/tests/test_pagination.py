from tinyroute import App, Client, paginate


def make_app():
    app = App()

    @app.route('/items')
    def items(request):
        return paginate(request, list(range(25)))

    @app.route('/tags/<slug:tag>/items')
    def tagged(request, tag):
        return paginate(request, [tag] * 12, per_page=5)

    return app


def test_first_page_by_default():
    page = Client(make_app()).get('/items').json()
    assert page['items'] == list(range(10))
    assert (page['page'], page['per_page'], page['total']) == (1, 10, 25)
    assert page['prev'] is None
    assert page['next'] == '/items?page=2'


def test_middle_and_last_pages():
    client = Client(make_app())
    middle = client.get('/items?page=2').json()
    assert middle['items'] == list(range(10, 20))
    assert (middle['prev'], middle['next']) == ('/items?page=1', '/items?page=3')
    last = client.get('/items?page=3').json()
    assert last['items'] == list(range(20, 25))
    assert last['next'] is None


def test_per_page_from_the_query_is_kept_in_links():
    page = Client(make_app()).get('/items?per_page=4&page=2').json()
    assert page['items'] == [4, 5, 6, 7]
    assert page['next'] == '/items?page=3&per_page=4'


def test_per_page_is_capped():
    assert Client(make_app()).get('/items?per_page=500').json()['per_page'] == 100


def test_links_keep_path_parameters():
    page = Client(make_app()).get('/tags/red/items').json()
    assert page['items'] == ['red'] * 5
    assert page['next'] == '/tags/red/items?page=2'


def test_bad_page_is_a_400():
    client = Client(make_app())
    for query in ('page=0', 'page=x', 'per_page=-1'):
        response = client.get(f'/items?{query}')
        assert response.status == 400
        assert 'must be a positive integer' in response.text
