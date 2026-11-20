# Product backlog
| Priority | Item | Sprint | Acceptance |
| --- | --- | --- | --- |
| P1 | #10 README badge maintenance | 1 | Generated from actual config; CI checks drift; documented convention |
| P0 | #7 Docker lab runtime verification | 1 | Both labs healthy; custom failure/restart/recovery passed; upstream LAN HTTP 200 |
| P1 | #7 Vercel simulation | 1 | Browser-only demo; no real monitoring or secrets; deployment verified |
| P0 | Verify Compose + alerts + persistence on Mac | 0 | One real container, three synthetic fault scenarios |
| P0 | CI lint/test/Compose validation | 0 | PR checks green |
| P0 | Harden dashboard auth for browsers | 1 | Browser Basic auth implemented; TLS required for customer use |
| P0 | Webhook delivery retries and audit | 1 | Recovery notification tested; retry/audit pending |
| P1 | Report export | 1 | Redacted evidence document |
| P1 | Client runbook | 1 | Owner can follow recovery steps |
| P1 | Pilot landing page | 2 | $399 offer and exclusions |
| P2 | Kubernetes/EKS templates | Later | No cloud provisioning by default |
| P2 | ECS/ECR templates | Later | Opt-in deployment, no paid resources |
Contributions are triaged as break/fix, active-sprint, or backlog. Do not expand scope without an issue.

- P2: Adopt machine-readable badge conventions from `drakeg/madmallard-repository-standards` when available; do not silently import unverified standards.

## Next ready priorities

1. #11: deploy queue migration and verify retry/recovery with a loopback synthetic receiver.
2. Protected operator configuration UI and output-check validation.
3. Redacted proof report and explicit retention controls.
4. External receiver acceptance test with customer-approved destination.

Central adoption: STANDARDS.md. No real customer validation or outreach completed.
