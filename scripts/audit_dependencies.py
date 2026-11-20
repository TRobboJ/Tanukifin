"""Query OSV for public dependency coordinates; an outage never means a clean scan."""
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
import tomllib
import urllib.request


def declared(source):
    catalog = tomllib.loads((source / 'gradle/libs.versions.toml').read_text())
    packages = set()
    for item in catalog['libraries'].values():
        name = item.get('module') or item['group'] + ':' + item['name']
        selected = item.get('version')
        version = catalog['versions'][selected['ref']] if isinstance(selected, dict) else selected
        packages.add((name, version))
    # Compiler/plugin runtime components are build inputs, not all APK contents.
    packages.add(('org.jetbrains.kotlin:kotlin-stdlib', catalog['versions']['kotlin']))
    return packages


def audit(source, output, resolved=None):
    packages = declared(source)
    if resolved:
        packages.update((item['name'], item['version']) for item in json.loads(resolved.read_text()))
    packages = sorted(packages)
    for name, version in packages:
        if not version or version.endswith('+') or any(mark in version.lower() for mark in ['snapshot', 'latest', '[', '(', '*']):
            raise ValueError(f'Unpinned dependency: {name}@{version}')
    request = urllib.request.Request('https://api.osv.dev/v1/querybatch',
        data=json.dumps({'queries': [{'package': {'ecosystem': 'Maven', 'name': name}, 'version': version}
                                    for name, version in packages]}).encode(),
        headers={'Content-Type': 'application/json'}, method='POST')
    with urllib.request.urlopen(request, timeout=90) as response:
        results = json.load(response)['results']
    if len(results) != len(packages) or any(result.get('next_page_token') or result.get('error') for result in results):
        raise ValueError('Incomplete advisory response; review before releasing')
    findings = []
    for (name, version), result in zip(packages, results):
        if result.get('vulns'):
            findings.append({'name': name, 'version': version, 'advisories': result['vulns']})
    report = {'checkedAt': datetime.now(timezone.utc).isoformat(), 'source': 'https://api.osv.dev/v1/querybatch',
              'scope': 'declared catalog plus resolved Maven components' if resolved else 'declared catalog only',
              'packages': [{'name': name, 'version': version} for name, version in packages],
              'findings': findings,
              'limits': 'Known-advisory matching is not malware detection. WebView/OS, native internals and undisclosed flaws require separate review.'}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(f'OSV: checked {len(packages)} Maven coordinates; {len(findings)} packages with advisory matches')
    if findings:
        for finding in findings:
            print(finding['name'], finding['version'], ', '.join(v['id'] for v in finding['advisories']))
        raise SystemExit('Dependency advisories require review and remediation before release')


if __name__ == '__main__':
    audit(Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3]) if len(sys.argv) > 3 else None)
