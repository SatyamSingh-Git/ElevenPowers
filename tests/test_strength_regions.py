"""Forward and adversarial controls for changed-region strength analysis."""
import sys
import time
from pathlib import Path
import pytest


def test_scope_records_current_line_hunks_new_files_and_deletion_anchors(tmp_path):
    from core.strength.scope import select
    from test_strength import repository
    base = repository(tmp_path)
    (tmp_path/'a.py').write_text('value = 2\n')
    (tmp_path/'new.py').write_text('def new():\n    return 4\n')
    value = select(tmp_path,base,time.monotonic()+15)
    assert value.regions == {'a.py': [[1,1]], 'new.py': [[1,2]]}
    assert value.deletions == {}
    assert set(value.source_hashes) == {'a.py','new.py'}

    # Pure deletions have no new line; retain their adjacent current-line context.
    import subprocess
    subprocess.run(['git','-c',f'safe.directory={tmp_path.as_posix()}','add','.'],cwd=tmp_path,check=True,capture_output=True)
    subprocess.run(['git','-c',f'safe.directory={tmp_path.as_posix()}','commit','-m','second'],cwd=tmp_path,check=True,capture_output=True)
    second = subprocess.check_output(['git','-c',f'safe.directory={tmp_path.as_posix()}','rev-parse','HEAD'],cwd=tmp_path,text=True).strip()
    (tmp_path/'new.py').write_text('def new():\n    pass\n')
    (tmp_path/'a.py').write_text('')
    value = select(tmp_path,second,time.monotonic()+15)
    assert value.regions['new.py'] == [[2,2]]
    assert value.regions['a.py'] == []
    assert value.deletions == {'a.py': [1]}
