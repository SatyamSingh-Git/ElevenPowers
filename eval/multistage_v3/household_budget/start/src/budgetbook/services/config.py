"""Changing a workspace's settings and adding categories of its own."""
import re

from .._generated import CATEGORY_GROUPS
from ..errors import ValidationError
from ..reports.render import RENDERERS
from .catalog import Catalog

_CURRENCY = re.compile(r"[A-Z]{3}")


def _currency(text):
    code = text.strip().upper()
    if not _CURRENCY.fullmatch(code):
        raise ValidationError(f"currency must be a three-letter code: {text}")
    return code


def _report_format(text):
    if text not in RENDERERS:
        raise ValidationError(f"report_format must be one of: {', '.join(sorted(RENDERERS))}")
    return text


SETTABLE = {
    "currency": _currency,
    "report_format": _report_format,
}


def set_value(workspace, key, text):
    if key not in SETTABLE:
        raise ValidationError(f"cannot set {key}; settable: {', '.join(sorted(SETTABLE))}")
    settings = workspace.settings()
    settings[key] = SETTABLE[key](text)
    workspace.save_settings(settings)
    return settings[key]


def add_category(workspace, name, group):
    name = name.strip()
    if not name:
        raise ValidationError("category name is empty")
    if group not in CATEGORY_GROUPS:
        raise ValidationError(f"group must be one of: {', '.join(CATEGORY_GROUPS)}")
    if name in Catalog.for_workspace(workspace).groups:
        raise ValidationError(f"category already exists: {name}")
    settings = workspace.settings()
    settings["extra_categories"] = {**settings["extra_categories"], name: group}
    workspace.save_settings(settings)
