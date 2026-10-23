import io

import pytest

from stockroom import Inventory, new_document
from stockroom.cli import main


@pytest.fixture
def inventory():
    inventory = Inventory(new_document())
    inventory.add_location('A1')
    inventory.add_location('B2', kind='bin')
    inventory.add_item('BOLT-M6', 'M6 bolt', reorder_point=20, cost='0.12')
    inventory.add_item('NUT-M6', 'M6 nut', cost='0.05')
    return inventory


@pytest.fixture
def run(tmp_path):
    path = tmp_path / 'stock.json'

    def run(*argv):
        out, err = io.StringIO(), io.StringIO()
        status = main(['--file', str(path), *argv], stdout=out, stderr=err)
        return status, out.getvalue(), err.getvalue()

    run.path = path
    return run
