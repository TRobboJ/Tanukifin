"""Build the prepared source; signing is opt-in and keys never enter the checkout."""
import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(signed=False):
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('VERSION must be a stable numeric x.y.z version')
    env = dict(os.environ, JELLYFIN_VERSION=version)
    # Unsigned validation must never accidentally inherit signing settings.
    for name in ['KEYSTORE_FILE', 'SIGNING_KEY_ALIAS', 'SIGNING_KEY_PASSWORD']:
        env.pop(name, None)
    source = ROOT / 'upstream'
    with tempfile.TemporaryDirectory(prefix='tanukifin-signing-') as directory:
        if signed:
            password = env.get('KEYSTORE_PASSWORD')
            if not password or not env.get('KEYSTORE_BASE64'):
                raise ValueError('Both signing secrets are required')
            key = Path(directory) / 'signing.p12'
            key.write_bytes(base64.b64decode(env['KEYSTORE_BASE64'], validate=True))
            key.chmod(0o600)
            details = subprocess.check_output([
                'keytool', '-J-Duser.language=en', '-list', '-v', '-keystore', str(key),
                '-storepass:env', 'KEYSTORE_PASSWORD',
            ], env=env, text=True, stderr=subprocess.STDOUT)
            aliases = []
            for block in details.split('Alias name: ')[1:]:
                if 'Entry type: PrivateKeyEntry' in block:
                    aliases.append(block.splitlines()[0].strip())
            if len(aliases) != 1:
                raise ValueError('Signing keystore must contain exactly one private key')
            env.update(KEYSTORE_FILE=str(key), SIGNING_KEY_ALIAS=aliases[0], SIGNING_KEY_PASSWORD=password)
        env.pop('KEYSTORE_BASE64', None)
        subprocess.run(['bash', './gradlew', '--no-daemon', 'assembleLibreRelease'], cwd=source, env=env, check=True)
    apks = list((source / 'app/build/outputs/apk/libre/release').glob('*.apk'))
    if len(apks) != 1:
        raise ValueError('Expected exactly one release APK')
    output = ROOT / 'out'
    output.mkdir(exist_ok=True)
    apk = output / ('Tanukifin.apk' if signed else 'Tanukifin-unsigned.apk')
    shutil.copyfile(apks[0], apk)
    if signed:
        sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
        signers = sorted((sdk / 'build-tools').glob('*/apksigner'))
        if not signers:
            raise ValueError('Android apksigner is required')
        subprocess.run([str(signers[-1]), 'verify', '--verbose', str(apk)], check=True)
    source_info = json.loads((ROOT / 'upstream.json').read_text())
    metadata = {
        'version': version,
        'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'upstream': source_info,
        'patchSha256': digest(ROOT / 'tanukifin.patch'),
        'apkSha256': digest(apk),
        'signed': signed,
        'workflowRun': os.environ.get('GITHUB_RUN_ID'),
        'javaVersion': subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT, text=True),
        'gradleWrapperPropertiesSha256': digest(source / 'gradle/wrapper/gradle-wrapper.properties'),
    }
    (output / 'build-info.json').write_text(json.dumps(metadata, indent=2) + '\n')
    (output / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in [apk, output / 'build-info.json']))


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--signed', action='store_true')
    build(parser.parse_args().signed)
