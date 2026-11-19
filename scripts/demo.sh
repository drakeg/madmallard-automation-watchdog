#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/.."
set -a; source .env; set +a
mkdir -p demo-outputs
printf 'sku,quantity\nSKU-001,7\n' > demo-outputs/inventory.csv
printf 'Synthetic report created at %s\n' "$(date -u)" > demo-outputs/report.txt
base="http://127.0.0.1:${WATCHDOG_PORT:-18765}"
curl -fsS -X POST -H "Authorization: Bearer ${JOB_INVENTORY_TOKEN}" "$base/api/inventory-feed/success"; echo
curl -fsS -X POST -H "Authorization: Bearer ${JOB_REPORT_TOKEN}" "$base/api/report-export/success"; echo
curl -fsS -H "Authorization: Bearer ${ADMIN_TOKEN}" "$base/api/status"; echo
echo "To test failure: curl -X POST -H 'Authorization: Bearer <job-token>' $base/api/inventory-feed/failure"
echo "To test a missed run, do not post success for longer than interval + grace."
