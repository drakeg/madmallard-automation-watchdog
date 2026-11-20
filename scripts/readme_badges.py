"""Generate this project's verified README badges, or check them without network access."""
import argparse
import json
from pathlib import Path
import re
from urllib.parse import quote

ROOT = Path(__file__).resolve().parents[1]
REPO = 'drakeg/madmallard-automation-watchdog'
URL = 'https://github.com/' + REPO
START = '<!-- badges:start -->'
END = '<!-- badges:end -->'


def badge(label, message, color, logo, link):
    # Shields static badge path uses doubled hyphens/underscores for literals.
    def escape(value):
        return quote(value.replace('-', '--').replace('_', '__'), safe='')
    image = f'https://img.shields.io/badge/{escape(label)}-{escape(message)}-{color}?style=flat&logo={logo}'
    return f'[![{label} {message}]({image})]({link})'


def generate():
    stack, deployment, activity = [], [], []
    dockerfile = (ROOT / 'Dockerfile').read_text()
    python = re.search(r'^FROM python:([\d.]+)', dockerfile, re.M)
    if python:
        stack.append(badge('Python', python[1], '3776AB', 'python', URL + '/blob/HEAD/Dockerfile'))
    if list((ROOT / 'web').glob('*.js')):
        stack.append(badge('JavaScript', 'browser', 'F7DF1E', 'javascript', URL + '/tree/HEAD/web'))
    if re.search(r'^import sqlite3\b', (ROOT / 'watchdog.py').read_text(), re.M):
        stack.append(badge('SQLite', 'storage', '003B57', 'sqlite', URL + '/blob/HEAD/watchdog.py'))
    deployment.append(badge('Docker', 'supported', '2496ED', 'docker', URL + '/blob/HEAD/Dockerfile'))
    if (ROOT / 'compose.yml').is_file():
        deployment.append(badge('Docker Compose', 'local lab', '2496ED', 'docker', URL + '/blob/HEAD/compose.yml'))
    if (ROOT / 'vercel.json').is_file():
        config = json.loads((ROOT / 'vercel.json').read_text())
        if (ROOT / config['outputDirectory'] / 'index.html').is_file():
            deployment.append(badge('Vercel', 'simulation', '000000', 'vercel', URL + '/blob/HEAD/TESTING.md'))
    for workflow in sorted((ROOT / '.github/workflows').glob('*')):
        if workflow.suffix not in ('.yml', '.yaml'):
            continue
        match = re.search(r'^name:\s*(.+?)\s*$', workflow.read_text(), re.M)
        name = match[1].strip('\"\'') if match else workflow.stem
        activity.append(f'[![{name}]({URL}/actions/workflows/{workflow.name}/badge.svg)]({URL}/actions/workflows/{workflow.name})')
    if (ROOT / 'LICENSE').is_file():
        activity.append(f'[![License](https://img.shields.io/github/license/{REPO}?style=flat)]({URL}/blob/HEAD/LICENSE)')
    activity.extend([
        f'[![Open issues](https://img.shields.io/github/issues/{REPO}?style=flat)]({URL}/issues)',
        f'[![Pull requests](https://img.shields.io/github/issues-pr/{REPO}?style=flat)]({URL}/pulls)',
    ])
    if (ROOT / 'CONTRIBUTING.md').is_file():
        activity.append(badge('Contributions', 'welcome', '2EA44F', 'github', URL + '/blob/HEAD/CONTRIBUTING.md'))
    return START + '\n' + '\n\n'.join(' '.join(row) for row in (stack, deployment, activity)) + '\n' + END


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    path = ROOT / 'README.md'
    content = path.read_text()
    title, separator, rest = content.partition('\n')
    if not title.startswith('# ') or not separator:
        raise SystemExit('README must start with its project title')
    if content.count(START) != content.count(END) or content.count(START) > 1:
        raise SystemExit('Malformed or duplicate badge markers')
    if START in rest:
        rest = re.sub(re.escape(START) + r'.*?' + re.escape(END), '', rest, flags=re.S)
    expected = title + '\n\n' + generate() + '\n\n' + rest.lstrip('\n')
    if args.check:
        if expected != content:
            raise SystemExit('README badges stale: run python3 scripts/readme_badges.py')
        print('README badges match repository configuration')
    else:
        if expected != content:
            path.write_text(expected)
        print('README badges generated')


if __name__ == '__main__':
    main()
