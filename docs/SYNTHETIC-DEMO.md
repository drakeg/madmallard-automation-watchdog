# Synthetic customer demo — under 15 minutes

## Setup
Use the isolated Docker Compose stack with the sample `jobs.json` and private `.env` secrets. No customer imports, secrets or personal records. Keep the service accessible only on a trusted LAN. Sign in as the configured admin.

## Demo sequence
1. Show two synthetic monitored jobs and their expected completion intervals.
2. Run `bash scripts/demo.sh` to generate sample outputs and validated success signals.
3. Use the existing test endpoint to submit an explicit failure for a synthetic job, using its scoped token. Verify the alert in the dashboard.
4. Remove or invalidate only the **synthetic** sample CSV, submit a success signal and show that validation fails rather than clearing the alert.
5. Restore the sample CSV, submit valid success and verify recovery.
6. Demonstrate the admin-only per-job delivery audit and CSV evidence export.
7. Explain the difference between job success and business-result correctness. Show the recovery runbook and the proposed $399 scope.

## Acceptance evidence
Capture timestamps, endpoint status, and nonsecret screenshots. Do not expose real tokens or URLs containing credentials.

## Limitations
Live webhook delivery requires a customer-provided HTTPS endpoint and should be tested only with approval. This demo proves the local technical workflow, not demand, customer revenue or guaranteed detection under a total-host outage.
