"""Install pinned Linux test binaries locally; verify publisher GitHub asset SHA-256.

No sudo or PATH changes. Run from any directory with Python 3.12+.
"""
import hashlib
from pathlib import Path
import tarfile
import urllib.request

ROOT = Path(__file__).resolve().parents[1] / '.tools'
TOOLS = [
    ('powershell', 'https://github.com/PowerShell/PowerShell/releases/download/v7.7.0/powershell-7.7.0-linux-x64.tar.gz',
     'c89d9c682d2c403dfe726f3df948e359675235a5bd6fab535776de69729ca0cb'),
    ('kopia', 'https://github.com/kopia/kopia/releases/download/v0.23.1/kopia-0.23.1-linux-x64.tar.gz',
     '416d0f84a3dbb321a8b2d8f0997b1a0a6e915babe79ee76fa6e4d2bd1e1c5178'),
]

if __name__ == '__main__':
    ROOT.mkdir(exist_ok=True)
    for name, url, expected in TOOLS:
        target = ROOT / name
        if target.exists():
            raise SystemExit(f'{target} already exists; use existing tools or move it aside to reinstall.')
        archive = ROOT / (name + '.tar.gz')
        urllib.request.urlretrieve(url, archive)
        if hashlib.sha256(archive.read_bytes()).hexdigest() != expected:
            raise SystemExit(f'Checksum mismatch for {name}; nothing extracted.')
        target.mkdir()
        with tarfile.open(archive) as package:
            package.extractall(target, filter='data')
        if name == 'powershell':
            (target / 'pwsh').chmod(0o755)
        archive.unlink()
        print(f'{name}: verified and installed locally')
