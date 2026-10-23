import json

import pytest

from stockroom import Inventory, StockError, load, new_document, save
from stockroom.store import default_path


def test_missing_file_is_an_empty_document(tmp_path):
    assert load(tmp_path / 'none.json') == new_document()


def test_save_and_load_round_trip(tmp_path, inventory):
    inventory.receive('BOLT-M6', 3, 'A1')
    path = tmp_path / 'stock.json'
    save(path, inventory.doc)
    assert load(path) == inventory.doc
    assert json.loads(path.read_text(encoding='utf-8'))['version'] == 1
    assert not (tmp_path / 'stock.json.tmp').exists()


def test_unknown_versions_are_refused(tmp_path):
    path = tmp_path / 'stock.json'
    path.write_text(json.dumps({**new_document(), 'version': 99}), encoding='utf-8')
    with pytest.raises(StockError, match='unsupported data file version: 99'):
        load(path)


def test_broken_json_is_reported(tmp_path):
    path = tmp_path / 'stock.json'
    path.write_text('{"version": 1,', encoding='utf-8')
    with pytest.raises(StockError, match='not valid JSON'):
        load(path)


def test_default_path_follows_the_environment():
    assert str(default_path({})) == 'stockroom.json'
    assert str(default_path({'STOCKROOM_FILE': 'x.json'})) == 'x.json'


def test_loaded_document_works_with_inventory(tmp_path, inventory):
    path = tmp_path / 'stock.json'
    save(path, inventory.doc)
    again = Inventory(load(path))
    again.receive('NUT-M6', 2, 'B2')
    assert again.at('NUT-M6', 'B2') == 2
