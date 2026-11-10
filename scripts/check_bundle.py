"""Verify the published HTML and PDF were built from the current content.json."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def check_bundle(root=ROOT):
    root = Path(root)
    manifest = json.loads((root / 'build/site/build.json').read_text())
    digest = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
    if manifest['content_sha256'] != digest(root / 'content.json'):
        raise ValueError('content.json changed after the last build; rebuild the website and PDF together.')
    for name, expected in manifest['files'].items():
        if digest(root / 'build/site' / name) != expected:
            raise ValueError(f'Generated file changed after build: {name}. Rebuild from content.json.')
    print('Bundle is current: HTML and PDF match content.json.')


if __name__ == '__main__':
    check_bundle()
