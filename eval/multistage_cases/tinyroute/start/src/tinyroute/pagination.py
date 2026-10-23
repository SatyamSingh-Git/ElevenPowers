"""Page through a list inside a handler, with links to the neighbouring pages."""
import re

from .errors import BadRequest

PER_PAGE = 10
MAX_PER_PAGE = 100
PAGE_PARAM = 'page'
PER_PAGE_PARAM = 'per_page'


def _positive(request, name, default):
    text = request.query.get(name)
    if text is None:
        return default
    if not re.fullmatch('[0-9]+', text) or int(text) < 1:
        raise BadRequest(f'{name} must be a positive integer')
    return int(text)


def _link(request, page, size, default_size):
    query = {PAGE_PARAM: page}
    if size != default_size:
        query[PER_PAGE_PARAM] = size
    return request.app.url_for(request.route.name, **request.params, **query)


def paginate(request, items, per_page=PER_PAGE):
    """One page of ``items`` chosen by the request's ``page`` and ``per_page`` query values.

    ``next`` and ``prev`` are URLs of the same route with the same path
    parameters, or None at either end. The route must have a name.
    """
    page = _positive(request, PAGE_PARAM, 1)
    size = min(_positive(request, PER_PAGE_PARAM, per_page), MAX_PER_PAGE)
    start = (page - 1) * size
    last = max(1, -(-len(items) // size))
    return {
        'items': list(items[start:start + size]),
        'page': page,
        'per_page': size,
        'total': len(items),
        'next': _link(request, page + 1, size, per_page) if page < last else None,
        'prev': _link(request, page - 1, size, per_page) if page > 1 else None,
    }
