# On-Call Escalation Runbook

## Severity levels

SEV1: full outage or data loss - page immediately, incident commander
required. SEV2: degraded service affecting users - page primary on-call.
SEV3: internal-only impact - file a ticket, address in business hours.

## Escalation path

Primary on-call has 15 minutes to acknowledge a page. Unacknowledged pages
escalate to secondary, then to the engineering manager. SEV1 incidents also
notify the director channel immediately.

## Postmortems

Every SEV1 and SEV2 requires a postmortem within 5 business days. Postmortems
are blameless and must include a timeline, root cause, and action items.
