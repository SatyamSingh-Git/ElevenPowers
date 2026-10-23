"""Stock levels, locations and movements kept in one JSON file."""
from ._generated import VERSION
from .inventory import Inventory
from .models import StockError
from .store import load, new_document, save

__version__ = VERSION
__all__ = ['Inventory', 'StockError', 'load', 'new_document', 'save']
