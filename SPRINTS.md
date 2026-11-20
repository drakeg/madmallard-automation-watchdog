# Sprint plan

## Sprint 0 — Foundation (in progress, 2026-11-19)
- [x] Independent public repository, license, contribution process
- [x] Python standard-library HTTP service and durable SQLite events
- [x] Isolated Docker Compose configuration and configurable LAN port
- [x] Missed run, explicit failure, output freshness and nonempty CSV checks
- [x] Synthetic demo, baseline unit tests, README and initial release policy
- [x] Build and start Docker container; confirm two output-validated synthetic success pings
- [ ] Verify restart persistence and failure/missed-run notifications on connected host
- [ ] Add CI pipeline and review first PR

**Definition of done:** clean tests, Docker smoke tests, no real customer data, documented threat model, reviewable PR.

## Sprint 1 — Pilot readiness
- [x] Issue #10: verified README badges, generator, maintenance convention and CI check (PR #9)
- [x] Issue #7: standalone Healthchecks Compose configuration and Vercel simulation
- [ ] Issue #7: confirm Docker runtime after host daemon recovers (blocked 2026-11-19)
- [ ] Secure browser dashboard auth and operator-friendly configuration
- [ ] Support generic webhook formats / SMTP alert routing with retries
- [ ] End-to-end missed/failure/recovery simulations and integration tests
- [ ] Audit/retention policy, metrics and exportable proof report
- [ ] Customer onboarding and recovery checklist

## Sprint 2 — Commercial validation
- [ ] Single-page $399 offer; scope and qualification worksheet
- [ ] Five evidence-based prospects (no automated outreach)
- [ ] Feedback and time-to-delivery tracking
- [ ] Go/no-go decision based on written pilot acceptance

## Later backlog
- [ ] Multi-host installation
- [ ] Scheduler-specific adapters (cron, systemd timers, container jobs)
- [ ] Kubernetes deployment manifests, ECS task definition and ECR publishing workflow
