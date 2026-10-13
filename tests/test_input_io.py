"""A redirected parent must be refused before external contents are read."""
import os
from pathlib import Path

import pytest


def test_parent_redirection_is_refused_before_content_read(tmp_path,monkeypatch):
    from core.inputs.definition import raw
    parent = tmp_path/'approved'; parent.mkdir()
    outside = tmp_path/'outside'; outside.mkdir()
    target = parent/'state'
    target.write_bytes(b'approved')
    (outside/'state').write_bytes(b'private outside material')
    check = tmp_path/'link-check'
    try:
        check.symlink_to(outside,target_is_directory=True); check.unlink()
    except OSError:
        pytest.skip('directory links unavailable')
    original_stat,original_open = Path.stat,os.fdopen
    swapped = False
    reads = 0
    def changing(path,*args,**kwargs):
        nonlocal swapped
        if path == target and kwargs.get('follow_symlinks',True) and not swapped:
            swapped = True
            parent.rename(tmp_path/'old-approved')
            parent.symlink_to(outside,target_is_directory=True)
        return original_stat(path,*args,**kwargs)
    class Stream:
        def __init__(self,inner): self.inner=inner
        def __enter__(self): self.inner.__enter__(); return self
        def __exit__(self,*args): return self.inner.__exit__(*args)
        def __getattr__(self,name): return getattr(self.inner,name)
        def read(self,*args):
            nonlocal reads
            reads += 1
            return self.inner.read(*args)
    monkeypatch.setattr(Path,'stat',changing)
    monkeypatch.setattr(os,'fdopen',lambda *a,**k:Stream(original_open(*a,**k)))
    with pytest.raises((OSError,ValueError)):
        raw(target)
    assert reads == 0, 'outside bytes were consumed before the path was refused'
