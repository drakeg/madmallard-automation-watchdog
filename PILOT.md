# Five-job paid pilot

Buyer hypothesis: small web/e-commerce agencies maintaining scheduled imports,
inventory feeds or recurring client reports without reliable completion alerts.
Value: detect missed or invalid business output and give the owner evidence and
a recovery checklist. No customer demand, feedback or revenue is verified yet.

Price hypothesis: $399 once for up to five jobs on one Linux/Docker environment,
one notification destination, one agreed output check per job, safe failure and
recovery demonstrations, and an owner runbook. Include seven days of configuration
corrections. Exclude underlying job repairs, hosting, continuous incident response,
ongoing monitoring service and guaranteed recovery times.

Alternatives include configuring upstream Healthchecks directly, using an agency's
existing monitoring tools, or manual checks. Paid value must come from setup,
business-output validation, proven alert routing and handoff, not exclusive access
to free software. First delivery target: 4–6 hands-on hours, an estimate to measure.

## Owner onboarding and acceptance checklist

1. Identify an important scheduled job and how missed completion is detected now.
   Confirm access authorization, schedule/timezone/grace, expected output, receiver
   and person responsible for recovery.
2. Use synthetic copies or an agreed safe fixture. Never break a live import.
   Verify valid fresh output succeeds; missing/stale output does not clear alerts;
   and a missed run raises an alert.
3. Verify receiver delivery and recovery notification, including retry behavior.
   Mock tests and UI alerts do not prove an external receiver got a message.
4. Restart the container and confirm history survives. Review TLS, independent
   hosting, volume backups, access and retention before customer use.
5. Handoff schedules, output checks, alert routing evidence, escalation contacts
   and exact recovery commands. Record limitations and observed delivery time.

48-hour validation hypothesis: identify five qualified agencies, seek two
substantive confirmations of the problem and one written $399 acceptance. Without
evidence, revise the offer before expanding features. Outreach requires separate
authorization; none has been sent. Record only actual customer responses.
