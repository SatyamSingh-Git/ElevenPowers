"""Statement layouts, registered by name."""
from ..errors import StatementError

_LAYOUTS = {}


def register(layout):
    if layout.name in _LAYOUTS:
        raise ValueError(f"layout registered twice: {layout.name}")
    _LAYOUTS[layout.name] = layout
    return layout


def get_layout(name):
    try:
        return _LAYOUTS[name]
    except KeyError:
        raise StatementError(f"unknown layout: {name}") from None


def all_layouts():
    """Every registered layout, in the order they were registered."""
    return list(_LAYOUTS.values())
