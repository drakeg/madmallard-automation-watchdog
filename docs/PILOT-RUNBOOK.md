# Five-Job Automation Watchdog — Customer Pilot Runbook

**Service:** fixed-scope monitoring for up to five existing jobs on one Linux/Docker environment. Alerts are not automatic repairs.

## Onboarding
Record customer owner, backup contact, escalation channel, job ID, expected completion schedule/grace window, business-output check, and agreed response responsibility. Do not record tokens in this worksheet. Obtain approval to test only synthetic jobs.

## Safe acceptance drills
Demonstrate valid completion, missing/stale/empty output, explicit failure, and a missed completion. Verify that an agreed human receives the alert. Inspect retry counters using the authenticated status API; prove recovery is sent only after output-validated success.

## Responding to alerts
1. Identify job, UTC timestamp, type, business impact, and owner.
2. Missed completion: inspect scheduler and application logs; do not forge a success ping.
3. Explicit job failure: review exit code and logs; underlying script fixes are out of scope.
4. Output failure: validate file freshness, records and completeness; escalate reconciliation to the owner.
5. Notification failure: inspect the monitor container and delivery counters. Verify webhook connectivity/TLS without exposing tokens.
6. Confirm the real business result, then allow a successful completion signal; verify recovered status and notification.
7. Document incident, response, owner and follow-up. Export redacted evidence using the admin-only CSV endpoint.

## Host outage
The watchdog cannot reliably detect its own host outage. Production deployments should monitor from a separate host. Preserve the Docker named volume; never use Docker Compose down with volume deletion to troubleshoot.

## Handoff checklist
- [ ] Up to five job owners and schedules agreed
- [ ] Business output check for each job demonstrated
- [ ] Synthetic missed/failure/recovery drills completed
- [ ] Alert channel and escalation contact verified
- [ ] Browser/API access protected using TLS in customer environment
- [ ] Delivery counters and evidence export demonstrated
- [ ] Configuration correction window and exclusions agreed

## Security and service exclusions
No customer records or secrets in heartbeat payloads. Limit dashboard access to a trusted network. Default retention is 90 days for delivered records and events; unresolved notifications are retained. The setup does not include job repair, hosting, 24/7 response, guaranteed loss prevention or paid infrastructure. The $399 pilot price remains an unvalidated hypothesis.
