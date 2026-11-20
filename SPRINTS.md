# Sprint plan

## Sprint 0 — Foundation (merged 2026-11-19, PR #1)
- [x] Independent public repository, license, contribution process
- [x] Python standard-library HTTP service and durable SQLite events
- [x] Isolated Docker Compose configuration and configurable LAN port
- [x] Missed run, explicit failure, output freshness and nonempty CSV checks
- [x] Synthetic demo, baseline unit tests, README and initial release policy
- [x] Build and start Docker container; confirm two output-validated synthetic success pings
- [ ] Verify restart persistence and failure/missed-run notifications on connected host
- [x] Add CI pipeline and review first PR

**Definition of done:** clean tests, Docker smoke tests, no real customer data, documented threat model, reviewable PR.

## Sprint 1 — Pilot readiness (active, 2026-11-20)
- [x] Adopt complete Mad Mallard development, delivery, commercial and GitHub standards in AGENTS.md and CONTRIBUTING.md
- [x] Audit stack and add verified, dynamic README badges (PR #6)
- [x] Document badge maintenance and add automated CI validation
- [x] Browser Basic authentication without embedding credentials in URLs
- [ ] Operator-friendly configuration UI with protected changes
- [x] Recovery webhook and HTTPS-only external webhook destination checks
- [x] Persist webhook notifications and retry transient delivery failures with bounded backoff
- [ ] Support generic webhook formats / SMTP alert routing
- [x] Synthetic missed/failure/recovery, output-failure and loopback webhook integration tests
- [x] Live container restart, authorized dashboard/API, and persisted job-event verification
- [x] Admin-only, redacted CSV event-evidence export
- [x] Configurable retention with pending-alert preservation and delivery status metrics
- [ ] Per-job delivery audit, alert aging and backup/export policy
- [x] Customer onboarding and recovery checklist

## Sprint 2 — Commercial validation
- [ ] Single-page $399 offer; scope and qualification worksheet
- [ ] Five evidence-based prospects (no automated outreach)
- [ ] Feedback and time-to-delivery tracking
- [ ] Go/no-go decision based on written pilot acceptance

## Later backlog
- [ ] Multi-host installation
- [ ] Scheduler-specific adapters (cron, systemd timers, container jobs)
- [ ] Kubernetes deployment manifests, ECS task definition and ECR publishing workflow
