"""Fail closed on API errors; never replace an existing tag, release or asset."""
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import urllib.error
import urllib.request

ROOT = Path(__file__).resolve().parents[1]


def version():
    expected = (ROOT / 'VERSION').read_text().strip()
    requested = os.environ['REQUESTED_VERSION']
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', requested) or requested != expected:
        raise ValueError('Requested version must exactly match VERSION')
    if os.environ.get('GITHUB_REF') != 'refs/heads/main' or not os.environ.get('GITHUB_SHA'):
        raise ValueError('Releases are only allowed from main')
    return requested


def assert_missing(path):
    request = urllib.request.Request('https://api.github.com/' + path, headers={
        'Authorization': 'Bearer ' + os.environ['GH_TOKEN'],
        'Accept': 'application/vnd.github+json',
        'X-GitHub-Api-Version': '2022-11-28',
    })
    try:
        with urllib.request.urlopen(request, timeout=30):
            raise ValueError('Release/tag already exists: ' + path)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise


def check():
    selected = version()
    repo = os.environ['GITHUB_REPOSITORY']
    for path in [f'repos/{repo}/git/ref/tags/v{selected}', f'repos/{repo}/releases/tags/v{selected}']:
        assert_missing(path)
    return selected


def publish():
    selected = check()  # Recheck after building; concurrency also serializes manual runs.
    repo = os.environ['GITHUB_REPOSITORY']
    source = os.environ['GITHUB_SHA']
    metadata = json.loads((ROOT / 'out/build-info.json').read_text())
    if not metadata['signed'] or metadata['sourceCommit'] != source:
        raise ValueError('Artifact does not match the release source')
    notes = ROOT / 'out/release-notes.md'
    notes.write_text(
        f'Tanukifin {selected}\n\nSource commit: {source}\n\n'
        f'Pinned Jellyfin Android commit: {metadata["upstream"]["commit"]}\n\n'
        'Install Tanukifin.apk. SHA256SUMS and build-info.json identify this build.\n'
        'Hashes provide artifact integrity, not an independent reproducible-build guarantee.\n'
    )
    # Draft first: partially uploaded artifacts never become the public latest release.
    subprocess.run(['gh', 'release', 'create', f'v{selected}', '--repo', repo,
                    '--target', source, '--title', f'Tanukifin {selected}', '--draft',
                    '--notes-file', str(notes), str(ROOT / 'out/Tanukifin.apk'),
                    str(ROOT / 'out/SHA256SUMS'), str(ROOT / 'out/build-info.json'),
                    str(ROOT / 'out/dependencies.json'), str(ROOT / 'out/dependency-audit.json')], check=True)
    subprocess.run(['gh', 'release', 'edit', f'v{selected}', '--repo', repo, '--draft=false', '--latest'], check=True)


if __name__ == '__main__':
    if sys.argv[1] == 'check':
        check()
    elif sys.argv[1] == 'publish':
        publish()
    else:
        raise ValueError('Expected check or publish')
