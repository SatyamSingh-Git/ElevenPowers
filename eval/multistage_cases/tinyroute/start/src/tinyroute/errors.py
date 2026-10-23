"""Errors raised while declaring routes and while answering requests."""
from ._generated import STATUS_REASONS


class RouteError(Exception):
    """A route table that cannot work: bad pattern, unknown type, clashing names."""


class BuildError(RouteError):
    """``url_for`` could not produce a URL from the values it was given."""


class HTTPError(Exception):
    """An error the application answers with a status code instead of crashing.

    Subclasses set ``status``; the message defaults to the status reason in
    lower case, so ``status = 410`` reads ``gone``.
    """

    status = 500

    def __init__(self, message=None, headers=None):
        if message is None:
            message = STATUS_REASONS.get(self.status, 'error').lower()
        self.message = message
        self.headers = dict(headers or {})
        super().__init__(message)


class BadRequest(HTTPError):
    status = 400


class NotFound(HTTPError):
    status = 404

    def __init__(self, path):
        self.path = path
        super().__init__(f"no route matches '{path}'")


class MethodNotAllowed(HTTPError):
    status = 405

    def __init__(self, method, path, allowed):
        self.allowed = sorted(allowed)
        super().__init__(f"method '{method}' not allowed for '{path}'",
                         {'Allow': ', '.join(self.allowed)})


class InternalError(HTTPError):
    status = 500
