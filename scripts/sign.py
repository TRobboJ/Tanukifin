"""Sign an audited unsigned APK on a fresh runner; never execute Gradle here."""
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
from build import android_tool, digest, inspect_apk

ROOT = Path(__file__).resolve().parents[1]


def sign():
    output = ROOT / 'out'
    metadata = json.loads((output / 'build-info.json').read_text())
    if metadata['sourceCommit'] != os.environ['GITHUB_SHA'] or metadata['signed']:
        raise ValueError('Unsigned artifact must match this workflow commit')
    expected_version = (ROOT / 'VERSION').read_text().strip()
    if metadata['version'] != expected_version:
        raise ValueError('Artifact version mismatch')
    # The download is tied to this run's immutable artifact ID. Also verify contents.
    for line in (output / 'SHA256SUMS').read_text().splitlines():
        expected, name = line.split('  ', 1)
        if Path(name).name != name or digest(output / name) != expected:
            raise ValueError('Build artifact checksum mismatch')
    unsigned = output / 'Tanukifin-unsigned.apk'
    if digest(unsigned) != metadata['apkSha256']:
        raise ValueError('Unsigned APK checksum mismatch')
    report = json.loads((output / 'dependency-audit.json').read_text())
    if report['findings'] or not report['packages']:
        raise ValueError('A complete passing dependency audit is required')
    metadata['inspection'] = inspect_apk(unsigned)
    password = os.environ.get('KEYSTORE_PASSWORD')
    encoded = os.environ.get('KEYSTORE_BASE64')
    if not password or not encoded:
        raise ValueError('Both signing secrets are required')
    signing_env = {k: v for k, v in os.environ.items() if k != 'KEYSTORE_BASE64'}
    apk = output / 'Tanukifin.apk'
    with tempfile.TemporaryDirectory(prefix='tanukifin-signing-') as directory:
        key = Path(directory) / 'signing.p12'
        key.write_bytes(base64.b64decode(encoded, validate=True))
        key.chmod(0o600)
        details = subprocess.check_output([
            'keytool', '-J-Duser.language=en', '-list', '-v', '-keystore', str(key),
            '-storepass:env', 'KEYSTORE_PASSWORD',
        ], env=signing_env, text=True, stderr=subprocess.STDOUT)
        aliases = [block.splitlines()[0].strip() for block in details.split('Alias name: ')[1:]
                   if 'Entry type: PrivateKeyEntry' in block]
        if len(aliases) != 1:
            raise ValueError('Signing keystore must contain exactly one private key')
        signer = android_tool('apksigner')
        subprocess.run([signer, 'sign', '--ks', str(key), '--ks-key-alias', aliases[0],
                        '--ks-pass', 'env:KEYSTORE_PASSWORD', '--key-pass', 'env:KEYSTORE_PASSWORD',
                        '--out', str(apk), str(unsigned)], env=signing_env, check=True)
        subprocess.run([signer, 'verify', '--verbose', '--print-certs', str(apk)], check=True)
    metadata.update(signed=True, apkSha256=digest(apk))
    (output / 'build-info.json').write_text(json.dumps(metadata, indent=2) + '\n')
    artifacts = [apk] + [output / name for name in ['build-info.json', 'dependencies.json', 'dependency-audit.json']]
    (output / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in artifacts))


if __name__ == '__main__':
    sign()
