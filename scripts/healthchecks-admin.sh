#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
# Credentials are read inside the container, never passed on its command line.
docker compose -f compose.healthchecks.yml exec -T healthchecks ./manage.py shell -c '
import os
from django.contrib.auth import get_user_model
from django.core.management import call_command
email = os.environ["DJANGO_SUPERUSER_EMAIL"]
if get_user_model().objects.filter(email=email).exists():
    print("Existing admin preserved")
else:
    call_command("createsuperuser", email=email, password=os.environ["DJANGO_SUPERUSER_PASSWORD"])
'
