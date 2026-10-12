"""Explicit developer/CI setup of checksum-pinned official oasdiff binaries."""
import argparse
import hashlib
import io
from pathlib import Path
import platform
import tarfile
from urllib.request import urlopen

ASSETS = {
    'Windows': ('windows_amd64', 'oasdiff.exe', '22f98c7247075f8a446e783595802d6d38637de1760df264f3d4b3309f766c5b'),
    'Linux': ('linux_amd64', 'oasdiff', '43a4e328e2d13ba1552d760aa68d2485c75c5621f309f6ff64ae895188345247'),
}


def install(directory):
    if platform.machine().lower() not in ('amd64', 'x86_64') or platform.system() not in ASSETS:
        raise ValueError('pinned installer supports Windows/Linux x86_64; install manually elsewhere')
    asset, name, checksum = ASSETS[platform.system()]
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    with urlopen(f'https://github.com/oasdiff/oasdiff/releases/download/v1.33.0/oasdiff_1.33.0_{asset}.tar.gz', timeout=60) as stream:
        raw = stream.read(64 * 1024 * 1024 + 1)
    if len(raw) > 64 * 1024 * 1024 or hashlib.sha256(raw).hexdigest() != checksum:
        raise ValueError('official checker archive checksum/size mismatch')
    with tarfile.open(fileobj=io.BytesIO(raw), mode='r:gz') as archive:
        entries = [entry for entry in archive.getmembers() if entry.name == name]
        if len(entries) != 1 or not entries[0].isfile() or entries[0].size > 128 * 1024 * 1024:
            raise ValueError('invalid checker archive member')
        data = archive.extractfile(entries[0]).read()
    path = directory / name
    path.write_bytes(data)
    path.chmod(0o755)
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', required=True, help='new directory for pinned optional checker')
    args = parser.parse_args()
    print(install(args.directory))


if __name__ == '__main__':
    main()
