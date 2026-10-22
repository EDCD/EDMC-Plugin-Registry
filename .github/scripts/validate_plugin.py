"""Validate a plugin registry entry and decide whether it can be auto-merged."""
import argparse
import datetime
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import zipfile

REQUIRED:dict = {
    'pluginName': str, 'pluginVer': str, 'autoUpdateEnabled': bool, 'autoInstallEnabled': bool, 'pluginAuthors': list,
    'pluginMainLink': str, 'pluginLastUpdate': str, 'pluginDirName': str, 'pluginCategory': list, 'pluginDesc': str,
    'pluginLastTestedEDMC': str, 'pluginLicense': str,
}
OPTIONAL:dict = {'pluginZip': str, 'pluginHash': str, 'pluginRequirements': list, 'pluginIcon': str, 'pluginVT': str}
CATEGORIES:set = {
    'Exploration', 'Navigation', 'Combat', 'Trading', 'Engineering', 'Anti-Xeno', 'Colonization', 'Colonisation',
    'Utility', 'Lore', 'Social', 'Streaming', 'Other',
}
LICENSES:set = {
    'GPL-2.0-only', 'GPL-2.0-or-later', 'GPL-3.0-only', 'GPL-3.0-or-later', 'LGPL-2.1-only', 'LGPL-2.1-or-later',
    'LGPL-3.0-only', 'LGPL-3.0-or-later', 'MIT', 'BSD-2-Clause', 'BSD-3-Clause', 'Apache-2.0', 'ISC', 'MPL-2.0',
    'Unlicense', '0BSD',
}
IDENTITY:tuple = ('pluginName', 'pluginDirName', 'pluginMainLink', 'pluginAuthors', 'pluginLicense')
MARKER:str = '<!-- plugin-validation -->'
MAX_ZIP:int = 50 * 1024 * 1024
SHA_RE = re.compile(r'[0-9a-f]{64}')
VER_RE = re.compile(r'(v?)(\d+)\.(\d+)\.(\d+)([-+].*)?')
VT_FILE_RE = re.compile(r'virustotal\.com/gui/file/([0-9a-fA-F]{64})')


class Report:
    """Collected errors, warnings and notes for one entry."""

    def __init__(self):
        self.errors:list = []
        self.warnings:list = []
        self.blockers:list = []
        self.notes:list = []
        self.vt_ok:bool = False

    def err(self, msg:str):
        self.errors.append(msg)

    def warn(self, msg:str, block:bool = False):
        self.warnings.append(('🚫 ' if block else '') + msg)
        if block: self.blockers.append(msg)


def parse_ver(ver) -> tuple|None:
    """Numeric (major, minor, patch) of a version string."""
    m = VER_RE.fullmatch(ver) if isinstance(ver, str) else None
    return tuple(int(x) for x in m.group(2, 3, 4)) if m else None


def repo_of(url) -> tuple|None:
    """(host, owner, project path) for a github.com or gitlab.com URL."""
    if not isinstance(url, str): return None

    u = urllib.parse.urlparse(url)
    host:str = u.netloc.lower().removeprefix('www.')
    parts:list = [p for p in u.path.split('/') if p]

    if host == 'github.com' and len(parts) >= 2:
        return host, parts[0].lower(), f'{parts[0]}/{parts[1].removesuffix(".git")}'.lower()

    if host == 'gitlab.com' and len(parts) >= 2:
        proj:list = parts[:parts.index('-')] if '-' in parts else parts
        return host, proj[0].lower(), '/'.join(proj).removesuffix('.git').lower()

    return None


def pick_file(changed:list, rep:Report) -> str|None:
    """The single plugins/*.json path a PR changes."""
    if len(changed) != 1:
        rep.err(f'PR must change exactly one file under `plugins/`, it changes {len(changed)}: '
                + ', '.join(f'`{p}`' for _, p in changed))
        return None

    status, path = changed[0]
    if not re.fullmatch(r'plugins/[^/]+\.json', path):
        rep.err(f'`{path}` is not a plugin entry; only `plugins/<name>.json` may be changed')
        return None

    if status.startswith('D'):
        rep.err(f'`{path}` is deleted; removing a listing needs a maintainer')
        return None

    return path


def check_schema(entry, rep:Report):
    """Field presence, types and formats."""
    if not isinstance(entry, dict):
        rep.err('Entry must be a JSON object')
        return

    for key, typ in REQUIRED.items():
        if key not in entry:
            rep.err(f'Missing required field `{key}`')
        elif not isinstance(entry[key], typ):
            rep.err(f'`{key}` must be a {typ.__name__}')

    for key, typ in OPTIONAL.items():
        if key in entry and not isinstance(entry[key], typ): rep.err(f'`{key}` must be a {typ.__name__}')

    for key in entry.keys() - REQUIRED.keys() - OPTIONAL.keys():
        rep.warn(f'Unknown field `{key}`')

    for key in ('pluginAuthors', 'pluginCategory', 'pluginRequirements'):
        val = entry.get(key)
        if isinstance(val, list) and not all(isinstance(x, str) for x in val): rep.err(f'`{key}` must be a list of strings')

    for key in ('pluginAuthors', 'pluginCategory'):
        if entry.get(key) == []: rep.err(f'`{key}` must not be empty')

    m = VER_RE.fullmatch(entry.get('pluginVer') or '')
    if not m: rep.err(f'`pluginVer` "{entry.get("pluginVer")}" is not a semantic version (Major.Minor.Patch)')
    if m and m.group(1): rep.warn('`pluginVer` should not have a `v` prefix')

    try:
        datetime.date.fromisoformat(entry.get('pluginLastUpdate') or '')
    except (TypeError, ValueError):
        rep.err('`pluginLastUpdate` must be a YYYY-MM-DD date')

    if not str(entry.get('pluginMainLink', '')).startswith('https://'): rep.err('`pluginMainLink` must be an https URL')

    cats = entry.get('pluginCategory')
    for cat in cats if isinstance(cats, list) else []:
        if cat not in CATEGORIES: rep.warn(f'Category "{cat}" is not in the documented list')

    if entry.get('pluginLicense') not in LICENSES:
        rep.warn(f'License "{entry.get("pluginLicense")}" is not a recognised GPL-compatible SPDX identifier')

    if entry.get('autoInstallEnabled') is True: rep.warn('`autoInstallEnabled` should be false until EDMC supports it')

    zip_url, sha = entry.get('pluginZip'), entry.get('pluginHash')
    if zip_url and not str(zip_url).startswith('https://'): rep.err('`pluginZip` must be an https URL')
    if zip_url and not sha: rep.warn('`pluginHash` should be set when `pluginZip` is set')
    if sha and not SHA_RE.fullmatch(str(sha).lower()): rep.err('`pluginHash` must be a 64 character SHA256 hex digest')

    main, zrepo = repo_of(entry.get('pluginMainLink')), repo_of(zip_url)
    if zip_url and (not main or not zrepo or main[:2] != zrepo[:2]):
        rep.warn('`pluginZip` is not hosted by the same GitHub/GitLab owner as `pluginMainLink`', block=True)


def check_vt_link(entry:dict, rep:Report):
    """pluginVT must point at the file whose hash is listed."""
    sha:str = str(entry.get('pluginHash') or '').lower()
    if not sha: return

    want:str = f'https://www.virustotal.com/gui/file/{sha}'
    m = VT_FILE_RE.search(str(entry.get('pluginVT') or ''))

    if m and m.group(1).lower() != sha:
        rep.err(f'`pluginVT` scans a different file than `pluginHash`; expected {want}')
        return

    if not m: rep.warn(f'`pluginVT` should be the file report link: {want}')


def ineligible(entry:dict, base:dict|None, author:str, rep:Report) -> list:
    """Reasons this PR cannot be auto-merged."""
    if not isinstance(base, dict): return ['New plugin listings need a maintainer review']

    why:list = []
    if rep.errors: why.append('Validation errors')
    if rep.blockers: why.append('Blocking warnings (🚫)')

    for key in IDENTITY:
        if entry.get(key) != base.get(key): why.append(f'`{key}` changed')

    new, old = parse_ver(entry.get('pluginVer')), parse_ver(base.get('pluginVer'))
    if not new or not old or new <= old: why.append(f'`pluginVer` not increased from {base.get("pluginVer")}')

    if not entry.get('pluginZip') or not entry.get('pluginHash'): why.append('`pluginZip` and `pluginHash` are required')
    if not rep.vt_ok: why.append('VirusTotal scan not verified clean')

    owner = repo_of(base.get('pluginMainLink'))
    authors:list = [str(a).lower() for a in base.get('pluginAuthors') or []]
    who:str = author.lower()
    if not who or (who != (owner[1] if owner else None) and who not in authors):
        why.append(f'PR author `{author}` is not the repository owner or a listed author')

    return why


def fetch(url:str, headers:dict|None = None, method:str = 'GET', limit:int|None = None) -> tuple:
    """(status, body) for an HTTP request; status 0 on connection failure."""
    req = urllib.request.Request(url, method=method, headers={'User-Agent': 'edmc-plugin-registry-validator', **(headers or {})})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return resp.status, resp.read(limit + 1 if limit else -1)
    except urllib.error.HTTPError as e:
        return e.code, b''
    except (urllib.error.URLError, TimeoutError) as e:
        print(f'{url}: {e}', file=sys.stderr)
        return 0, b''


def check_main_link(entry:dict, rep:Report):
    """pluginMainLink resolves to an existing project."""
    url:str = entry['pluginMainLink']
    repo = repo_of(url)
    token:str = os.environ.get('GITHUB_TOKEN', '')

    if repo and repo[0] == 'github.com':
        status, _ = fetch(f'https://api.github.com/repos/{repo[2]}', {'Authorization': f'Bearer {token}'} if token else None)
    elif repo:
        status, _ = fetch(f'https://gitlab.com/api/v4/projects/{urllib.parse.quote_plus(repo[2])}')
    else:
        status, _ = fetch(url, method='HEAD')

    if status != 200: rep.err(f'`pluginMainLink` {url} did not resolve (HTTP {status})')


def check_zip(entry:dict, rep:Report):
    """pluginZip downloads, is a valid archive and matches pluginHash."""
    status, data = fetch(entry['pluginZip'], limit=MAX_ZIP)
    if status != 200: return rep.err(f'`pluginZip` download failed (HTTP {status})')
    if len(data) > MAX_ZIP: return rep.err(f'`pluginZip` is larger than {MAX_ZIP // 1024 // 1024} MB')

    sha:str = hashlib.sha256(data).hexdigest()
    if sha != str(entry['pluginHash']).lower(): return rep.err(f'`pluginHash` does not match the zip, whose SHA256 is `{sha}`')
    rep.notes.append(f'Zip SHA256 matches `pluginHash` ({len(data):,} bytes)')

    try:
        bad = zipfile.ZipFile(io.BytesIO(data)).testzip()
    except zipfile.BadZipFile:
        return rep.err('`pluginZip` is not a valid zip archive')
    if bad: rep.err(f'`pluginZip` is corrupt at `{bad}`')


def check_vt_scan(entry:dict, key:str, rep:Report):
    """VirusTotal's last analysis of the zip is clean."""
    if not key: return rep.warn('`VT_API_KEY` is not configured, so the VirusTotal scan was not checked', block=True)

    sha:str = str(entry['pluginHash']).lower()
    status, body = fetch(f'https://www.virustotal.com/api/v3/files/{sha}', {'x-apikey': key})
    if status == 404: return rep.warn('VirusTotal has no scan of this zip; upload it at https://www.virustotal.com', block=True)
    if status != 200: return rep.warn(f'VirusTotal lookup failed (HTTP {status}); re-run the check later', block=True)

    stats:dict = json.loads(body).get('data', {}).get('attributes', {}).get('last_analysis_stats') or {}
    if not stats: return rep.warn('VirusTotal has not finished analysing this zip; re-run the check later', block=True)

    bad, sus = stats.get('malicious', 0), stats.get('suspicious', 0)
    rep.notes.append(f'VirusTotal: {bad} malicious, {sus} suspicious, {stats.get("undetected", 0)} undetected '
                     f'([report](https://www.virustotal.com/gui/file/{sha}))')

    if bad: return rep.err(f'VirusTotal reports {bad} malicious detections')
    if sus: return rep.warn(f'VirusTotal reports {sus} suspicious detections', block=True)
    rep.vt_ok = True


def git_show(ref:str, path:str) -> str|None:
    """File contents at a git ref, or None if absent."""
    res = subprocess.run(['git', 'show', f'{ref}:{path}'], capture_output=True, text=True)
    return res.stdout if res.returncode == 0 else None


def main() -> int:
    """Run all checks, write the report and return the exit status."""
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--head', help='PR head commit; validates the files it changes')
    ap.add_argument('--file', help='validate a local entry instead of a PR')
    ap.add_argument('--base-ref', default='HEAD', help='ref holding the approved entries')
    ap.add_argument('--author', default='', help='GitHub login of the PR author')
    ap.add_argument('--report', help='write the markdown report here')
    args = ap.parse_args()
    if bool(args.head) == bool(args.file): ap.error('pass exactly one of --head or --file')

    rep = Report()

    if args.head:
        diff:str = subprocess.run(['git', 'diff', '--name-status', '--no-renames', f'{args.base_ref}...{args.head}'],
                                  capture_output=True, text=True, check=True).stdout
        path = pick_file([tuple(line.split('\t', 1)) for line in diff.splitlines()], rep)
        text = git_show(args.head, path) if path else None
    else:
        path = args.file
        with open(path, encoding='utf-8') as f:
            text = f.read()

    base_text = git_show(args.base_ref, path) if path else None
    base = json.loads(base_text) if base_text else None
    entry = None

    try:
        entry = json.loads(text) if text is not None else None
    except json.JSONDecodeError as e:
        rep.err(f'Invalid JSON: {e}')

    if entry is not None: check_schema(entry, rep)

    if isinstance(entry, dict) and not rep.errors:
        check_main_link(entry, rep)
        check_vt_link(entry, rep)
        if entry.get('pluginZip') and entry.get('pluginHash'): check_zip(entry, rep)
        if entry.get('pluginHash') and not rep.errors: check_vt_scan(entry, os.environ.get('VT_API_KEY', ''), rep)

    why:list = ineligible(entry, base, args.author, rep) if isinstance(entry, dict) else ['Entry could not be read']
    enabled:bool = os.environ.get('AUTO_MERGE', '').lower() == 'true'

    out:list = [MARKER, f'## Plugin validation: {"❌ failed" if rep.errors else "✅ passed"}', '']
    if path: out += [f'Entry: `{path}` ({"update" if base else "new listing"})', '']

    for title, items in (('Errors', rep.errors), ('Warnings', rep.warnings), ('Checks', rep.notes)):
        if items: out += [f'### {title}', *(f'- {i}' for i in items), '']

    if why:
        out += ['### Auto-merge: not eligible', *(f'- {w}' for w in why)]
    else:
        out += ['### Auto-merge: eligible', '- ' + ('Merging now.' if enabled else 'Auto-merge is disabled; a maintainer must merge.')]

    report:str = '\n'.join(out) + '\n'
    print(report)

    if args.report:
        with open(args.report, 'w', encoding='utf-8') as f:
            f.write(report)

    if os.environ.get('GITHUB_OUTPUT'):
        with open(os.environ['GITHUB_OUTPUT'], 'a', encoding='utf-8') as f:
            f.write(f'eligible={"false" if why else "true"}\n')
            f.write('reasons<<EOF\n' + ''.join(f'- {w}\n' for w in why) + 'EOF\n')

    return 1 if rep.errors else 0


if __name__ == '__main__':
    sys.exit(main())
