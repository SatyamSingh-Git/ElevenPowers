"""Middleware that ships with tinyroute. Each factory returns ``middleware(request, call_next)``."""
from itertools import count

from .http import Response

CORS_METHODS = ('GET', 'POST', 'PUT', 'PATCH', 'DELETE')
CORS_MAX_AGE = 600
REQUEST_ID_HEADER = 'X-Request-Id'
ACCESS_LOG_FORMAT = '{method} {path} {status}'


def cors(origins, methods=CORS_METHODS, max_age=CORS_MAX_AGE):
    """Allow cross-origin calls from ``origins`` (``'*'`` allows any origin).

    A preflight ``OPTIONS`` request from an allowed origin is answered here
    with 204 and never reaches the router.
    """
    allowed = set(origins)

    def middleware(request, call_next):
        origin = request.header('Origin')
        permitted = origin is not None and ('*' in allowed or origin in allowed)
        if permitted and request.method == 'OPTIONS' and request.header('Access-Control-Request-Method'):
            response = Response(status=204)
            response.headers['Access-Control-Allow-Methods'] = ', '.join(methods)
            response.headers['Access-Control-Max-Age'] = str(max_age)
        else:
            response = call_next(request)
        if permitted:
            response.headers['Access-Control-Allow-Origin'] = origin
            response.headers['Vary'] = 'Origin'
        return response

    return middleware


def request_id(header=REQUEST_ID_HEADER, start=1):
    """Tag each request with an id: the caller's own if it sent one, else the next number."""
    numbers = count(start)

    def middleware(request, call_next):
        value = request.header(header) or str(next(numbers))
        request.id = value
        response = call_next(request)
        response.headers[header] = value
        return response

    return middleware


def access_log(write, line=ACCESS_LOG_FORMAT):
    """Call ``write`` with one formatted line per request once its response is ready."""
    def middleware(request, call_next):
        response = call_next(request)
        write(line.format(method=request.method, path=request.path, status=response.status))
        return response

    return middleware
