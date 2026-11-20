# Sprint plan

## Sprint 0 — Foundation (implemented; PR #1 merged)
- [x] Independent repository, MIT license and contributor documentation
- [x] Python/SQLite monitor; output validation; isolated LAN-accessible Compose
- [x] CI tests and initial demo
- [x] Actual container failure, restart persistence and valid-output recovery

## Sprint 1 — Pilot readiness (active)
- [x] #7 / PR #9: independent Healthchecks lab and Vercel simulation; runtime verified
- [x] #10 / PR #9: verified badges, idempotent generator and CI validation
- [x] PR #6: browser Basic/Bearer auth and synthetic integration tests (integrated into PR #9 for review)
- [x] #11: selected central standards adoption, security boundaries and pilot checklist
- [x] #11: transactional persistent notification queue, bounded retries and admin audit
- [ ] #11: complete live Docker verification of new queue and audit
- [ ] Operator-friendly protected configuration UI
- [x] #12: authenticated redacted JSON proof report and dashboard download link
- [ ] SMTP/provider adapters and notification retention
- [ ] Verify external receiver delivery before customer deployment

Definition of done: tests and CI green; real local smoke evidence; docs current;
reviewable PR; no claim of production readiness or real customer validation.
Code checked above is implemented on the review branch, not a claim of PR merge.

## Sprint 2 — Commercial validation
- [x] Draft narrowly scoped $399 hypothesis and qualification/owner checklist (PILOT.md)
- [ ] Single-page pilot offer
- [ ] Identify five qualified prospects (research only; no automated outreach)
- [ ] Record actual feedback and hands-on delivery time
- [ ] Go/no-go based on evidence and written pilot acceptance

## Later backlog
- [ ] Multi-host installation and scheduler-specific adapters
- [ ] Kubernetes/EKS manifests and ECS/ECR templates (no cloud provisioning)

Continue ready backlog tasks within each authorized session. Do not stop for
routine Sprint transitions; required PR reviews and cost/data boundaries remain.
