# Security and pilot boundaries

Report vulnerabilities privately through the repository owner's GitHub profile.
Never include live tokens, customer output, or webhook URLs in public issues.
There is no guaranteed response SLA during the pre-release pilot phase.

The lab accepts job-specific bearer credentials and separate admin bearer/Basic
credentials. Basic authentication over plain LAN HTTP is not encrypted. Use only
synthetic data on trusted networks; require TLS and restricted access for customers.
The dashboard and notification audit require admin authentication.

Output mounts are read-only and checks reject paths outside the configured root.
Heartbeat success alone does not prove correct business output. Host filesystem
access, container ownership and independent monitoring infrastructure need review
before customer use. There is no automatic repair or command execution API.

SQLite events, alerts and notification attempts persist in a project-owned volume.
Never erase volumes during upgrades. Restrict host access and ignored environment
files. Audits expose job IDs, fixed reasons, attempts and status, never webhook
addresses or customer output. Use synthetic identifiers for demos.

External webhooks require HTTPS. Delivery is opt-in, bounded and at-least-once:
a crash after receipt but before acknowledgment can duplicate a notification.
Only single-instance operation is supported. After five failures a notification
is exhausted and visible in the audit. This is not a delivery guarantee or 24/7
response service. Pending messages use the currently configured destination;
review pending history before changing recipients.
