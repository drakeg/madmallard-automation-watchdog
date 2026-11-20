# Release policy
Use Semantic Versioning and tag releases only after merged tests and documented notes.
- **Patch** (0.1.1): fixes, dependency/security changes without intentional API changes.
- **Minor** (0.2.0): backward-compatible feature additions (new checks, alerts, UI).
- **Major** (1.0.0, 2.0.0): stable release / breaking configuration, API or data migration.
While pre-1.0, breaking changes may happen between minor versions, explicitly described in changelog.
A release requires: completed Sprint milestone or urgent break/fix; green CI; Docker smoke; security/license review; changelog; rollback/migration steps; tagged commit. No automated production deployment.

## Unreleased — pilot readiness
- Isolated upstream Healthchecks lab and Vercel browser simulation.
- Browser admin authentication, dynamic README badges and central standards checks.
- Persistent bounded webhook retries, recovery messages and admin delivery audit.
- Authenticated redacted proof-report download with observed status and event counts.

Queue migration: startup adds the notifications table without replacing existing
events/alerts. Stop the app and take a consistent backup of the project-owned
SQLite volume before upgrading a customer environment. For rollback, redeploy the
previous image with the same volume; the older app ignores the additive table,
but cannot process pending retries. Re-upgrading resumes pending work. Never
run `down -v`. No tagged release is published by this change; review and required
checks remain release gates.
