import json
import pytest
from eval import benefit_archive


def test_unknown_private_fields_and_oversize_inputs_rejected(tmp_path):
    path=tmp_path/'archive.json'; path.write_text(json.dumps({'secret':'private'}))
    with pytest.raises(ValueError):
        benefit_archive.inspect(path)
    path.write_bytes(b' '*(8*1024*1024+1))
    with pytest.raises(ValueError,match='limit'):
        benefit_archive.inspect(path)


def test_duplicate_keys_and_nonfinite_values_rejected(tmp_path):
    for text in ('{"schema_version":1,"schema_version":2}', '{"schema_version":NaN}'):
        path=tmp_path/'archive.json'; path.write_text(text)
        with pytest.raises(ValueError):
            benefit_archive.inspect(path)


def test_retained_actual_archive_is_qualified_without_claiming_coding_gain(tmp_path):
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'docs/validation/2026-10-02-proof-of-benefit/completion-archive.json'
    result=benefit_archive.inspect(path)
    assert result['summary']['valid_runs']==8
    assert result['summary']['coding_improvement_observed'] is False
    assert len(result['summary']['verification_refreshes'])==3
    value=json.loads(path.read_text())
    value['runs'][0]['record']['final_grade']['passed']=15
    altered=tmp_path/'altered.json';altered.write_text(json.dumps(value))
    with pytest.raises(ValueError,match='result'):
        benefit_archive.inspect(altered)


def test_public_checksums_survive_checkout_newline_conversion(tmp_path):
    from pathlib import Path
    path=Path(__file__).resolve().parents[1]/'docs/validation/2026-10-02-proof-of-benefit/checksums.json'
    assert benefit_archive.verify_checksums(path) is True
    for source in path.parent.glob('*.json'):
        (tmp_path/source.name).write_bytes(source.read_bytes().replace(b'\r\n',b'\n'))
    assert benefit_archive.verify_checksums(tmp_path/path.name) is True
