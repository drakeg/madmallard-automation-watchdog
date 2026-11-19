"""Prepare an isolated upstream Healthchecks lab. Never overwrite credentials."""
import argparse
import os
from pathlib import Path
import secrets
from urllib.parse import urlsplit

parser = argparse.ArgumentParser()
parser.add_argument('--url', required=True, help='LAN URL, e.g. http://192.168.0.155:18080')
args = parser.parse_args()
url = urlsplit(args.url)
if (url.scheme not in ('http', 'https') or not url.hostname or url.username
        or url.password or url.path not in ('', '/') or url.query or url.fragment
        or any(c in args.url for c in '\r\n')):
    parser.error('Provide an HTTP(S) origin without credentials, query or path')
target = Path(__file__).resolve().parents[1] / '.env.healthchecks'
content = '\n'.join([
    'DB=sqlite', 'DB_NAME=/data/hc.sqlite', 'DEBUG=False',
    'SECRET_KEY=' + secrets.token_urlsafe(48),
    'SITE_ROOT=' + args.url.rstrip('/'),
    'PING_ENDPOINT=' + args.url.rstrip('/') + '/ping/',
    'ALLOWED_HOSTS=' + url.hostname + ',localhost,127.0.0.1',
    'SITE_NAME=Mad Mallard Healthchecks Lab', 'REGISTRATION_OPEN=False',
    'EMAIL_HOST=', 'DEFAULT_FROM_EMAIL=watchdog@example.invalid',
    'DJANGO_SUPERUSER_EMAIL=admin@example.invalid',
    'DJANGO_SUPERUSER_PASSWORD=' + secrets.token_urlsafe(24),
    'PING_BODY_LIMIT=0', '',
])
try:
    with open(target, 'x', opener=lambda path, flags: os.open(path, flags, 0o600)) as fh:
        fh.write(content)
except FileExistsError:
    print('Existing .env.healthchecks preserved.')
else:
    print('Created .env.healthchecks (mode 0600); credentials stay local.')
