# Standalone testing environments

Issue #7 / Sprint 1. These environments belong only to this repository.

## Custom Watchdog

Use the existing `compose.yml` and README quick start. Dashboard is port 18765.
Preserve `.env`, `jobs.json`, and the `watchdog-data` volume. Never run `down -v`
unless deliberately discarding history. Browser Basic auth is supported by the
in-progress Sprint 1 build; the merged foundation only accepts bearer headers.

## Upstream Healthchecks comparison lab

This is the actual BSD 3-Clause [Healthchecks project](https://github.com/healthchecks/healthchecks),
not the custom Watchdog. Official image tag v5.0.3 corresponds to upstream commit
`51a503531d845fc11d5ef270d576c59c300e3620`. SQLite and its own named volume keep it
independent. The official image has been pulled and the lab started healthy on the Mac.

```bash
python3 scripts/init-healthchecks.py --url http://YOUR_LAN_IP:18080
docker compose -f compose.healthchecks.yml config -q
docker compose -f compose.healthchecks.yml up -d
# Initial account creation only (password is read inside the container):
bash scripts/healthchecks-admin.sh
docker compose -f compose.healthchecks.yml ps
```

Open the configured LAN URL. Email is `admin@example.invalid`; password is the
`DJANGO_SUPERUSER_PASSWORD` entry in the ignored `.env.healthchecks`. Setup never
overwrites an existing environment file. Stop with `docker compose -f
compose.healthchecks.yml down` (no `-v`). Default LAN binding is configurable.
This HTTP lab is for a trusted network only; don't expose it to the internet.

Create a synthetic check in the UI, set a short period/grace, copy its generated
ping URL, then send a normal ping, a `/fail` ping, and another normal ping to
observe failure/recovery. Omit pings past the deadline to test a missed run.
Use no production jobs or customer data. The upstream heartbeat does not inspect
business outputs; the custom Watchdog handles those separately.

No SMTP provider, paid API or external notification integration is configured.
Status changes can be inspected in the UI; external alert delivery is not yet
an acceptance-tested feature of this comparison lab.

## Vercel simulation

`vercel.json` publishes only `web/` with no install/build step, API, cron, database,
secrets or paid integration. It simulates failure, missed run, stale output,
recovery and reset in the browser. No monitoring occurs while it is closed.
Do not put admin tokens or real job metadata in this static demo.

The current live monitor uses SQLite and a continuous polling process; deploying
that implementation as an ordinary Vercel Function would not preserve those
semantics. A production Vercel backend needs separate durable storage and a
reliable scheduler, which are outside this zero-additional-service lab.

Validate with:

```bash
python3 -m unittest discover -s tests -v
node --test tests/demo.test.cjs
node --check web/app.js
python3 -m http.server 18865 --directory web --bind 127.0.0.1
```

## Initial runtime evidence — 2026-11-19

On Gregs-MacBook-Pro.local, all nine in-progress Python tests passed. Docker API
requests timed out after eight seconds and HTTP to port 18765 timed out. A build
was requested but running/healthy status could not be established. Docker Desktop
was not restarted because doing so could affect other apps. The upstream lab is
configuration-ready, not runtime-verified. No unrelated containers were changed.

## Verified Vercel result

- URL: https://madmallard-watchdog-lab.vercel.app/
- Deployment: dpl_2QAx4H4Fu5GcSmm7zrJNrMfNH6Q6 (READY).
- HTTP 200 and CSP headers verified.
- Live browser: failure, validated recovery, missed run, stale output and reset passed.
- Five Python tests and one Node scenario test passed on the lab branch.
- Healthchecks Compose configuration validation passed on the Mac.
- At initial deployment verification, Docker was blocked by the host daemon; see the subsequent recovery evidence below.

## Subsequent Docker and badge validation

The custom Watchdog container started healthy on the Mac with LAN port 18765.
Authenticated dashboard and status API both returned HTTP 200. Two synthetic
output checks passed; an explicit failure raised ALERT, the alert survived a
container restart, and fresh output completions restored both jobs to OK.
The upstream Healthchecks lab also started healthy and its LAN homepage returned HTTP 200. Initial admin creation completed. External notification delivery remains unconfigured. No other containers were restarted.

Issue #10: README badge generation/check, repeat-run idempotence and stale-version
detection passed. Five Python tests, the Node scenario test and GitHub CI passed.
The central standards repository had only a placeholder README when inspected.
