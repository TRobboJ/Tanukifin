"""Resolve, audit and build without signing secrets."""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import zipfile
from audit_dependencies import audit

ROOT = Path(__file__).resolve().parents[1]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def android_tool(name):
    found = shutil.which(name)
    if found:
        return found
    sdk = Path(os.environ.get('ANDROID_HOME') or os.environ['ANDROID_SDK_ROOT'])
    matches = sorted((sdk / 'build-tools').glob('*/' + name)) + sorted((sdk / 'cmdline-tools').glob('*/bin/' + name))
    if not matches:
        raise ValueError(f'Android SDK tool required: {name}')
    return str(matches[-1])


def inspect_apk(apk):
    analyzer = android_tool('apkanalyzer')
    package = subprocess.check_output([analyzer, 'manifest', 'application-id', str(apk)], text=True).strip()
    if package != 'org.tanukifin.tv':
        raise ValueError('Unexpected APK package identity')
    permissions = subprocess.check_output([analyzer, 'manifest', 'permissions', str(apk)], text=True).splitlines()
    allowed = {'android.permission.' + p for p in [
        'BLUETOOTH', 'BLUETOOTH_CONNECT', 'INTERNET', 'ACCESS_WIFI_STATE', 'ACCESS_NETWORK_STATE',
        'WAKE_LOCK', 'RECEIVE_BOOT_COMPLETED', 'POST_NOTIFICATIONS', 'FOREGROUND_SERVICE',
        'FOREGROUND_SERVICE_MEDIA_PLAYBACK', 'FOREGROUND_SERVICE_DATA_SYNC',
    ]} | {'org.tanukifin.tv.DYNAMIC_RECEIVER_NOT_EXPORTED_PERMISSION'}
    if set(permissions) - allowed:
        raise ValueError('New APK permissions require review: ' + str(set(permissions) - allowed))
    with zipfile.ZipFile(apk) as archive:
        native = [name for name in archive.namelist() if name.startswith('lib/') and name.endswith('.so')]
        if any(Path(name).name != 'libandroidx.graphics.path.so' for name in native):
            raise ValueError('New native libraries require review: ' + str(native))
    return {'package': package, 'permissions': sorted(permissions), 'nativeLibraries': native}


def build():
    version = (ROOT / 'VERSION').read_text().strip()
    if not re.fullmatch(r'[0-9]+\.[0-9]+\.[0-9]+', version):
        raise ValueError('VERSION must be a stable numeric x.y.z version')
    env = dict(os.environ, JELLYFIN_VERSION=version)
    # Gradle and downloaded build plugins never receive our signing secrets.
    for name in ['KEYSTORE_BASE64', 'KEYSTORE_PASSWORD', 'KEYSTORE_FILE', 'SIGNING_KEY_ALIAS', 'SIGNING_KEY_PASSWORD']:
        env.pop(name, None)
    source = ROOT / 'upstream'
    output = ROOT / 'out'
    output.mkdir(exist_ok=True)
    env['TANUKIFIN_AUDIT_DIR'] = str(output)
    subprocess.run(['bash', './gradlew', '--no-daemon', '-I', str(ROOT / 'scripts/dependency-report.init.gradle'),
                    ':app:exportTanukifinDependencies'], cwd=source, env=env, check=True)
    audit(source, output / 'dependency-audit.json', output / 'dependencies.json')
    subprocess.run(['bash', './gradlew', '--no-daemon', '--no-build-cache', '--no-configuration-cache',
                    '-I', str(ROOT / 'scripts/dependency-report.init.gradle'), 'assembleLibreRelease'],
                   cwd=source, env=env, check=True)
    apks = list((source / 'app/build/outputs/apk/libre/release').glob('*.apk'))
    if len(apks) != 1:
        raise ValueError('Expected exactly one release APK')
    inspection = inspect_apk(apks[0])
    apk = output / 'Tanukifin-unsigned.apk'
    shutil.copyfile(apks[0], apk)
    metadata = {
        'version': version,
        'sourceCommit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'upstream': json.loads((ROOT / 'upstream.json').read_text()),
        'patchSha256': digest(ROOT / 'tanukifin.patch'), 'apkSha256': digest(apk), 'signed': False,
        'dependencyOverridesSha256': digest(ROOT / 'dependency-versions.json'),
        'inspection': inspection,
        'workflowRun': os.environ.get('GITHUB_RUN_ID'),
        'javaVersion': subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT, text=True),
        'gradleWrapperPropertiesSha256': digest(source / 'gradle/wrapper/gradle-wrapper.properties'),
    }
    (output / 'build-info.json').write_text(json.dumps(metadata, indent=2) + '\n')
    artifacts = [apk] + [output / name for name in ['build-info.json', 'dependencies.json', 'dependency-audit.json']]
    (output / 'SHA256SUMS').write_text(''.join(f'{digest(p)}  {p.name}\n' for p in artifacts))


if __name__ == '__main__':
    build()
