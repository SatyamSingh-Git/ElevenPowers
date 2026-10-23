import pytest

from tinyroute import BadRequest, MethodNotAllowed, NotFound, Request, Response, json_response, redirect
from tinyroute.http import error_response, to_response


def test_request_from_url_splits_query():
    request = Request.from_url('get', '/search?q=tiny&page=2&flag=')
    assert request.method == 'GET'
    assert request.path == '/search'
    assert request.query == {'q': 'tiny', 'page': '2', 'flag': ''}


def test_repeated_query_value_keeps_the_last():
    assert Request.from_url('GET', '/s?tag=a&tag=b').query == {'tag': 'b'}


def test_request_headers_are_case_insensitive():
    request = Request('GET', '/', headers={'X-Token': 'abc'})
    assert request.header('x-token') == 'abc'
    assert request.header('missing', 'none') == 'none'


def test_request_json_and_bad_json():
    assert Request('POST', '/', body='{"a": 1}').json() == {'a': 1}
    with pytest.raises(BadRequest, match='invalid JSON body'):
        Request('POST', '/', body='{').json()


def test_response_defaults():
    response = Response('hi')
    assert response.status_line == '200 OK'
    assert response.content_type == 'text/plain; charset=utf-8'
    assert response.text == 'hi'


def test_response_header_lookup_ignores_case():
    response = Response(headers={'X-Thing': '1'})
    assert response.header('x-thing') == '1'
    assert response.header('nope') is None


def test_set_cookie():
    response = Response()
    response.set_cookie('session', 'abc', max_age=60)
    assert response.header('Set-Cookie') == 'session=abc; Path=/; Max-Age=60; HttpOnly'
    response.delete_cookie('session')
    assert response.header('Set-Cookie') == 'session=; Path=/; Max-Age=0; HttpOnly'


def test_json_response_and_redirect():
    assert json_response({'a': 1}, 201).json() == {'a': 1}
    assert json_response([]).content_type == 'application/json'
    assert redirect('/next').header('Location') == '/next'
    assert redirect('/next').status == 302


def test_error_response_body_and_allow_header():
    response = error_response(MethodNotAllowed('POST', '/x', {'GET', 'HEAD'}))
    assert response.status == 405
    assert response.json() == {'error': "method 'POST' not allowed for '/x'", 'status': 405}
    assert response.header('Allow') == 'GET, HEAD'
    assert error_response(NotFound('/y')).json()['error'] == "no route matches '/y'"


def test_to_response():
    assert to_response(None).status == 204
    assert to_response({'a': 1}).json() == {'a': 1}
    assert to_response(b'raw').text == 'raw'
    with pytest.raises(TypeError):
        to_response(3)
