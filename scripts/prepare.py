"""Checkout the immutable upstream commit and apply our binary-safe patch."""
import json
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]


def prepare(destination):
    spec = json.loads((ROOT / 'upstream.json').read_text())
    if spec['repository'] != 'https://github.com/jellyfin/jellyfin-android.git':
        raise ValueError('Unexpected upstream repository')
    if not re.fullmatch(r'[0-9a-f]{40}', spec['commit']):
        raise ValueError('Upstream must be an immutable commit')
    destination = pathlib.Path(destination).resolve()
    if destination.exists():
        raise ValueError('Destination already exists; choose a fresh directory')
    destination.mkdir(parents=True)

    def git(*args):
        return subprocess.check_output(['git', '-C', str(destination), *args], text=True).strip()

    git('init')
    git('config', 'core.autocrlf', 'false')
    git('remote', 'add', 'origin', spec['repository'])
    git('fetch', '--depth=1', 'origin', spec['commit'])
    git('checkout', '--detach', 'FETCH_HEAD')
    if git('rev-parse', 'HEAD') != spec['commit']:
        raise ValueError('Upstream commit mismatch')
    patch = ROOT / 'tanukifin.patch'
    if b'\r\n' in patch.read_bytes():
        raise ValueError('Patch must retain LF line endings; see .gitattributes')
    git('apply', '--check', str(patch))
    git('apply', str(patch))
    print(f'Prepared {spec["commit"]} in {destination}')


if __name__ == '__main__':
    prepare(sys.argv[1] if len(sys.argv) > 1 else ROOT / 'upstream')
