# Sprint plan

## Sprint 0 — Foundation (merged 2026-11-19, PR #1)
- [x] Independent public repository, license, contribution process
- [x] Python standard-library HTTP service and durable SQLite events
- [x] Isolated Docker Compose configuration and configurable LAN port
- [x] Missed run, explicit failure, output freshness and nonempty CSV checks
- [x] Synthetic demo, baseline unit tests, README and initial release policy
- [x] Build and start Docker container; confirm two output-validated synthetic success pings
- [x] Verify restart persistence and failure/missed-run notifications on connected host
- [x] Add CI pipeline and review first PR

**Definition of done:** clean tests, Docker smoke tests, no real customer data, documented threat model, reviewable PR.

## Sprint 1 — Pilot readiness (active, 2026-11-20)
- [x] Adopt complete Mad Mallard development, delivery, commercial and GitHub standards in AGENTS.md and CONTRIBUTING.md
- [x] Audit stack and add verified, dynamic README badges (PR #6)
- [x] Document badge maintenance and add automated CI validation
- [x] Browser Basic authentication without embedding credentials in URLs
- [x] Authenticated per-job interval/grace editor with persisted, validated changes
- [x] Recovery webhook and HTTPS-only external webhook destination checks
- [x] Persist webhook notifications and retry transient delivery failures with bounded backoff
- [ ] Support generic webhook formats / SMTP alert routing
- [x] Synthetic missed/failure/recovery, output-failure and loopback webhook integration tests
- [x] Live container restart, authorized dashboard/API, and persisted job-event verification
- [x] Admin-only, redacted CSV event-evidence export
- [x] Configurable retention with pending-alert preservation and delivery status metrics
- [x] Per-job delivery history and alert aging endpoint
- [x] Safe SQLite online backup and isolated restore verification
- [ ] Additional delivery channels (SMTP/provider adapters)
- [x] Customer onboarding and recovery checklist

## Sprint 2 — Commercial validation (materials in progress, 2026-11-21)
- [x] Draft $399 pilot offer, scope and qualification worksheet (PR #18)
- [x] Synthetic customer demonstration script (PR #18)
- [ ] Five evidence-based prospects (no automated outreach)
- [ ] Feedback and time-to-delivery tracking
- [ ] Go/no-go decision based on written pilot acceptance

## Later backlog
- [ ] Multi-host installation
- [ ] Scheduler-specific adapters (cron, systemd timers, container jobs)
- [ ] Kubernetes deployment manifests, ECS task definition and ECR publishing workflow
