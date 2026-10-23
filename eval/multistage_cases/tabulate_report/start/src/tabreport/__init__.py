"""Turn CSV exports into grouped, totalled reports."""
from ._generated import VERSION as __version__
from .aggregate import Measure, aggregate, parse_measure
from .dialect import Dialect
from .errors import ReportError
from .filters import Filter, parse_filter
from .money import format_money
from .numbers import format_number, parse_amount
from .profile import profile
from .reader import read_csv
from .report import Report, build_report, render_report
from .table import render_table

__all__ = [
    "Dialect",
    "Filter",
    "Measure",
    "Report",
    "ReportError",
    "__version__",
    "aggregate",
    "build_report",
    "format_money",
    "format_number",
    "parse_amount",
    "parse_filter",
    "parse_measure",
    "profile",
    "read_csv",
    "render_report",
    "render_table",
]
