"""The application: a router, a middleware stack and the dispatch between them."""
from functools import partial

from .errors import HTTPError, InternalError
from .http import error_response, to_response
from .router import DEFAULT_METHODS, Router


class App:
    """Routes requests to handlers through middleware.

    A handler is called as ``handler(request, **params)`` and may return a
    ``Response``, a ``str`` or ``bytes`` body, a ``dict`` or ``list`` for JSON,
    or None for 204. A middleware is called as ``middleware(request, call_next)``
    and returns a ``Response``; the first one added runs outermost.
    """

    def __init__(self, router=None, debug=False):
        self.router = router if router is not None else Router()
        self.middleware = []
        # In debug mode an unexpected exception propagates instead of becoming a 500.
        self.debug = debug

    def route(self, pattern, methods=DEFAULT_METHODS, name=None):
        return self.router.route(pattern, methods, name)

    def add_route(self, pattern, handler, methods=DEFAULT_METHODS, name=None):
        return self.router.add(pattern, handler, methods, name)

    def use(self, middleware):
        self.middleware.append(middleware)
        return middleware

    def url_for(self, name, **values):
        return self.router.url_for(name, **values)

    def handle(self, request):
        request.app = self
        call = self._dispatch
        for middleware in reversed(self.middleware):
            call = partial(middleware, call_next=call)
        return call(request)

    def _dispatch(self, request):
        try:
            route, params = self.router.match(request.method, request.path)
            request.route, request.params = route, params
            return to_response(route.handler(request, **params))
        except HTTPError as error:
            return error_response(error)
        except Exception:
            if self.debug:
                raise
            return error_response(InternalError())
