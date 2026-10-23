"""marklite: a small markdown subset rendered to HTML."""
from ._generated import VERSION
from .errors import MarkliteError
from .options import Options
from .outline import TocEntry
from .render import parse, render, toc
from .slug import slugify

__version__ = VERSION
__all__ = ["MarkliteError", "Options", "TocEntry", "parse", "render", "slugify", "toc"]
