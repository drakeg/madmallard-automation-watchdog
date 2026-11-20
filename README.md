# Mad Mallard Automation Watchdog

[![Python 3.13](https://img.shields.io/badge/Python-3.13-3776AB?logo=python&logoColor=white)](Dockerfile)
[![SQLite](https://img.shields.io/badge/SQLite-database-003B57?logo=sqlite&logoColor=white)](watchdog.py)
[![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker&logoColor=white)](compose.yml)

[![CI](https://github.com/drakeg/madmallard-automation-watchdog/actions/workflows/ci.yml/badge.svg)](https://github.com/drakeg/madmallard-automation-watchdog/actions/workflows/ci.yml)
[![License](https://img.shields.io/github/license/drakeg/madmallard-automation-watchdog)](LICENSE)
[![Issues](https://img.shields.io/github/issues/drakeg/madmallard-automation-watchdog)](https://github.com/drakeg/madmallard-automation-watchdog/issues)
[![Pull Requests](https://img.shields.io/github/issues-pr/drakeg/madmallard-automation-watchdog)](https://github.com/drakeg/madmallard-automation-watchdog/pulls)


Standalone, open-source MVP for the **Five-Job Automation Watchdog Setup** service. Detects **missed completions**, explicit job failures, and business-output failures. Designed for isolated customer-owned Docker/Linux installs; **not affiliated with Healthchecks.io**.

## Quick start (local test only)

```bash
cp .env.example .env
# Replace all three placeholder tokens with strong random values (e.g. python3 -c 'import secrets; print(secrets.token_urlsafe(36))').
cp jobs.example.json jobs.json
docker compose up --build -d
bash scripts/demo.sh
docker compose ps
```

Browser dashboard: `http://<LAN_HOST_IP>:18765/` — sign in when prompted using username `admin` and password equal to `ADMIN_TOKEN` from the local, ignored `.env` file. API: `/api/status` accepts `Authorization: Bearer <ADMIN_TOKEN>`; Basic authentication also works for the dashboard. Browser Basic credentials are **not encrypted over HTTP**; use only on a trusted lab network, and place the application behind TLS and access controls before customer use. This is intentionally **not** a public website. LAN binding is configurable via WATCHDOG_BIND (default 0.0.0.0). Do not forward this port to the internet; use TLS plus access control for any remote production access.

Compose uses the existing Docker bridge network, avoiding address-pool allocation on crowded test hosts. The monitor runs with its own SQLite volume and read-only access to synthetic outputs. No shared databases, cross-app authentication, or dependencies on other Mad Mallard projects.

### API

- `POST /api/{job-id}/start` — job started, informational only
- `POST /api/{job-id}/success` — validates configured file and records completion only if valid (422 otherwise)
- `POST /api/{job-id}/failure` — immediately raises an alert
- `GET /api/status` — admin-only JSON snapshot

Each POST uses `Authorization: Bearer <job-specific-token>`. GET uses separate `ADMIN_TOKEN`. The server checks schedule interval + grace against last output-validated success. An active alert clears only after a valid success; recovery also sends a webhook message when configured. Webhook failures are stored in the local SQLite notification queue and retried with exponential backoff (5–300 seconds) across service restarts; delivery is at-least-once, so webhook receivers should tolerate duplicates. Webhook provider compatibility must be tested. HTTPS is required for external webhook URLs (HTTP loopback is permitted for synthetic tests). Alerts persist in SQLite across restarts; reboot resets the first-run timer for never-completed jobs. A webhook can receive JSON alert objects with job ID/reason only. Both alerts and recoveries are queued when a webhook is configured. Webhook provider compatibility and TLS must be checked before customer use.

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

### Safe test protocol

1. Ensure `.env` and `jobs.json` remain untracked. Run `docker compose up --build -d`.
2. Run `bash scripts/demo.sh` to create synthetic output and show two valid completions.
3. Open the browser dashboard using `admin` and the local `ADMIN_TOKEN` credential.
4. For failures and recovery run `python3 -m unittest discover -s tests -v` (the integration suite creates isolated temporary databases and a loopback webhook listener; it does not affect live monitoring jobs).
5. Check container health with `docker compose ps`; avoid `docker compose down -v` because it erases alert history.

The initial dashboard is deliberately simple: no public session cookies, no signup, no multi-user management. Do not put the admin token in URLs or logs.

### Delivery and availability limitations

The outbox retains delivered records for auditing until a retention policy is implemented. A disconnected or misconfigured webhook will continue retrying, so investigate logs if notifications are not arriving. Monitoring is still co-located with the jobs in this demo; for customer production monitoring, move this service to a separate host and configure TLS. No outbound network traffic occurs when WEBHOOK_URL is unset.
