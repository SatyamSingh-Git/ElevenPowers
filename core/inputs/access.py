"""Open verified targets before consuming bytes; never follow POSIX parents."""
import os
from pathlib import Path


def opened(path,flags):
    path = Path(path).absolute()
    if os.name == 'nt':
        descriptor = os.open(path,flags)
        try:
            _windows_target(descriptor,path)
            return descriptor
        except BaseException:
            os.close(descriptor)
            raise
    if os.open not in os.supports_dir_fd or not hasattr(os,'O_NOFOLLOW'):
        raise OSError('anchored input access unavailable')
    directories = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    parent = os.open(path.anchor,directories)
    try:
        for component in path.parts[1:-1]:
            child = os.open(component,directories,dir_fd=parent)
            os.close(parent)
            parent = child
        return os.open(path.name,flags|os.O_NOFOLLOW,dir_fd=parent)
    finally:
        os.close(parent)


def _windows_target(descriptor,expected):
    import ctypes
    import msvcrt
    api = ctypes.WinDLL('kernel32',use_last_error=True).GetFinalPathNameByHandleW
    api.argtypes = [ctypes.c_void_p,ctypes.c_wchar_p,ctypes.c_uint32,ctypes.c_uint32]
    api.restype = ctypes.c_uint32
    buffer = ctypes.create_unicode_buffer(32768)
    size = api(msvcrt.get_osfhandle(descriptor),buffer,len(buffer),0)
    if not size or size >= len(buffer):
        raise OSError('opened input target unavailable')
    name = buffer.value
    if name.startswith('\\\\?\\UNC\\'):
        name = '\\\\'+name[8:]
    elif name.startswith('\\\\?\\'):
        name = name[4:]
    if Path(name) != expected:
        raise ValueError('opened input target differs from approved path')
