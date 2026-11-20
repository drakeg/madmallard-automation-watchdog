# Mad Mallard Automation Watchdog

<!-- badges:start -->
[![Python 3.15](https://img.shields.io/badge/Python-3.15-3776AB?style=flat&logo=python)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/Dockerfile) [![JavaScript browser](https://img.shields.io/badge/JavaScript-browser-F7DF1E?style=flat&logo=javascript)](https://github.com/drakeg/madmallard-automation-watchdog/tree/HEAD/web) [![SQLite storage](https://img.shields.io/badge/SQLite-storage-003B57?style=flat&logo=sqlite)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/watchdog.py)

[![Docker supported](https://img.shields.io/badge/Docker-supported-2496ED?style=flat&logo=docker)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/Dockerfile) [![Docker Compose local lab](https://img.shields.io/badge/Docker%20Compose-local%20lab-2496ED?style=flat&logo=docker)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/compose.yml) [![Vercel simulation](https://img.shields.io/badge/Vercel-simulation-000000?style=flat&logo=vercel)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/TESTING.md)

[![CI](https://github.com/drakeg/madmallard-automation-watchdog/actions/workflows/ci.yml/badge.svg)](https://github.com/drakeg/madmallard-automation-watchdog/actions/workflows/ci.yml) [![License](https://img.shields.io/github/license/drakeg/madmallard-automation-watchdog?style=flat)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/LICENSE) [![Open issues](https://img.shields.io/github/issues/drakeg/madmallard-automation-watchdog?style=flat)](https://github.com/drakeg/madmallard-automation-watchdog/issues) [![Pull requests](https://img.shields.io/github/issues-pr/drakeg/madmallard-automation-watchdog?style=flat)](https://github.com/drakeg/madmallard-automation-watchdog/pulls) [![Contributions welcome](https://img.shields.io/badge/Contributions-welcome-2EA44F?style=flat&logo=github)](https://github.com/drakeg/madmallard-automation-watchdog/blob/HEAD/CONTRIBUTING.md)
<!-- badges:end -->

Standalone, open-source MVP for the **Five-Job Automation Watchdog Setup** service. Detects **missed completions**, explicit job failures, and business-output failures. Designed for isolated customer-owned Docker/Linux installs; **not affiliated with Healthchecks.io**.

See [TESTING.md](TESTING.md) for the optional upstream Healthchecks Docker lab (port 18080), the custom Watchdog (port 18765), and the Vercel browser-only simulation. Vercel does not host the live monitor or its SQLite database.

## Quick start (local test only)

```bash
cp .env.example .env
# Replace all three placeholder tokens with strong random values (e.g. python3 -c 'import secrets; print(secrets.token_urlsafe(36))').
cp jobs.example.json jobs.json
docker compose up --build -d
bash scripts/demo.sh
docker compose ps
```

Dashboard/API: `http://<LAN_HOST_IP>:18765/api/status` with `Authorization: Bearer <ADMIN_TOKEN>`. For browser login use username `admin` and the local `ADMIN_TOKEN` as password. Basic authentication is unencrypted over HTTP; this is for a trusted lab network only. This is intentionally **not** a public website. LAN binding is configurable via WATCHDOG_BIND (default 0.0.0.0). Do not forward this port to the internet; use TLS plus access control for any remote production access.

Compose uses the existing Docker bridge network, avoiding address-pool allocation on crowded test hosts. The monitor runs with its own SQLite volume and read-only access to synthetic outputs. No shared databases, cross-app authentication, or dependencies on other Mad Mallard projects.

### API

- `POST /api/{job-id}/start` — job started, informational only
- `POST /api/{job-id}/success` — validates configured file and records completion only if valid (422 otherwise)
- `POST /api/{job-id}/failure` — immediately raises an alert
- `GET /api/status` — admin-only JSON snapshot

Each POST uses `Authorization: Bearer <job-specific-token>`. GET uses separate `ADMIN_TOKEN`. The server checks schedule interval + grace against last output-validated success. An active alert clears only after a valid success. Alerts and the notification queue persist in SQLite across restarts; reboot resets the first-run timer for never-completed jobs. An opt-in webhook receives JSON with fixed reason and job ID only. Both alert and recovery are queued transactionally, retried up to five times with exponential delays starting at 30 seconds, and audited at admin-only `GET /api/notifications`. Delivery is at-least-once, may duplicate after a crash, and can be exhausted. Pending messages use the currently configured destination after restart. This is single-instance only. Webhook provider compatibility and TLS must be checked before customer use.

### Instrument a scheduled job

Run your actual task first, then POST `success` **only when its business output is complete**. POST `failure` if it errors. Configure interval/grace to the real completion cadence. For output checks, mount a designated output folder read-only and choose `type: csv` (requires a header and at least one record) or `type: file` (nonempty). Each check rejects stale files beyond `max_age_seconds`. This checks existence, freshness and rows; it does not prove contents are semantically correct.

### Demo and testing

```bash
python3 -m unittest discover -s tests -v
docker compose config
bash scripts/demo.sh
```

To show a synthetic failed job, POST `failure`; to show a missed run, omit the success ping past the configured interval + grace. Reconfigure intervals for a longer production cadence and do not trigger alarms on real workloads during demos. Use `docker compose down` without `-v` to retain alert history.

### Constraints

At most five jobs on one host per pilot. No automatic job repair, incident response, outbound customer data, guaranteed uptime or production failover. For independent outage detection, deploy the monitor on a separate host from the jobs in production. An HTTP heartbeat without an output check is **not** sufficient proof of business success.

See [SPRINTS.md](SPRINTS.md), [BACKLOG.md](BACKLOG.md), [RELEASES.md](RELEASES.md), [CONTRIBUTING.md](CONTRIBUTING.md), and [AGENTS.md](AGENTS.md). Licensing: MIT; third-party base image and dependency terms require review for releases.

## Pilot and standards

See [PILOT.md](PILOT.md) for the SMB buyer hypothesis, $399 price hypothesis, scope and owner checklist; [STANDARDS.md](STANDARDS.md) for selected central adoption; and [SECURITY.md](SECURITY.md) for threat model and customer deployment limitations. No demand, revenue or external notification provider delivery is claimed as validated.

Admin-only `GET /api/report` downloads a JSON proof report containing observed job status, event counts and notification states, without raw output, tokens, webhook URLs or file paths. Browser users can use the dashboard download link. Run `python3 scripts/smoke_delivery.py` for an isolated real-HTTP retry/recovery check; it uses a temporary database and loopback receiver only.
