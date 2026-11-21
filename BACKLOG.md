# Product backlog
| Priority | Item | Sprint | Acceptance |
| --- | --- | --- | --- |
| P0 | Verify Compose + alerts + persistence on Mac | 0 | One real container, three synthetic fault scenarios |
| P0 | CI lint/test/Compose validation | 0 | PR checks green |
| P0 | Harden dashboard auth for browsers | 1 | Browser Basic auth implemented; TLS required for customer use |
| P0 | Webhook delivery retries and audit | 1 | Recovery notification and restart-safe retries tested; retention and aggregate metrics implemented; per-job delivery audit and alert age implemented; backups pending |
| P1 | Report export | 1 | Admin-only redacted CSV implemented; printable summary pending |
| P1 | Client runbook | 1 | Recovery and customer handoff checklist documented |
| P1 | Pilot landing page | 2 | Draft $399 scope and exclusions documented; public landing page pending |
| P2 | Kubernetes/EKS templates | Later | No cloud provisioning by default |
| P2 | ECS/ECR templates | Later | Opt-in deployment, no paid resources |
Contributions are triaged as break/fix, active-sprint, or backlog. Do not expand scope without an issue.

- P2: Adopt machine-readable badge conventions from `drakeg/madmallard-repository-standards` when available; do not silently import unverified standards.

- P1: Scheduled encrypted off-host backup after customer hosting/retention requirements are agreed.
