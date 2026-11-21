# Release policy
Use Semantic Versioning and tag releases only after merged tests and documented notes.
- **Patch** (0.1.1): fixes, dependency/security changes without intentional API changes.
- **Minor** (0.2.0): backward-compatible feature additions (new checks, alerts, UI).
- **Major** (1.0.0, 2.0.0): stable release / breaking configuration, API or data migration.
While pre-1.0, breaking changes may happen between minor versions, explicitly described in changelog.
A release requires: completed Sprint milestone or urgent break/fix; green CI; Docker smoke; security/license review; changelog; rollback/migration steps; tagged commit. No automated production deployment.

## Unreleased
- Add selectable authenticated SMTP-over-TLS notifications (mutually exclusive with webhook), reusing the persistent retry queue; default remains webhook.
- No schema migration, new external Python dependencies or automatic email account provisioning.
