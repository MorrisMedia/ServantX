# ServantX HIPAA-Safe Data Plan

## Product intent
ServantX is a revenue-integrity and underpayment audit platform for hospitals, surgery centers, and outpatient groups. The system ingests billing/payment exports, compares reimbursement against contract terms and public fee schedules, flags defensible underpayments, and prepares analyst-reviewed recovery workflows.

## Non-negotiable guardrails
1. **No raw PHI to external LLMs**
   - Names, MRNs, DOBs, full addresses, payer member IDs, and other direct identifiers must never be sent to third-party LLM APIs.
2. **Deterministic dollar decisions only**
   - Underpayment findings, coverage logic, expected reimbursement, and appeal recommendations must come from deterministic rules, contract logic, and audited source data.
3. **Minimum necessary access**
   - Only admins and analysts should have access in this version.
4. **Tenant isolation**
   - Every client account must be logically and operationally separated.
5. **Human review before outbound action**
   - No autonomous appeal submission or autonomous payment dispute escalation.

## Data classification
- **PHI / sensitive regulated data**
  - patient identifiers, subscriber/member identifiers, claim identifiers tied to a person, dates that identify a patient, provider-specific attachments where patient context is exposed
- **Restricted operational data**
  - contract terms, payer mappings, locality overrides, batch metadata, claim variance values
- **LLM-safe derived data**
  - tokenized identifiers, salted hashes, aggregate counts, non-identifying reimbursement math, de-identified narratives

## Allowed LLM usage
Allowed only when one of the following is true:
- the input is fully de-identified
- identifiers are irreversibly tokenized for the model call
- the content is aggregate-only and contains no PHI

Permitted LLM tasks:
- summarizing already-approved findings in non-PHI terms
- drafting internal analyst notes from de-identified finding sets
- classifying operational queue issues
- generating admin alerts from counts/statuses only

Prohibited LLM tasks:
- deciding whether a claim was underpaid
- interpreting PHI-rich documents directly in an external model
- generating unsupported reimbursement conclusions
- sending messages/appeals without human approval

## Background audit agent plan
The compliant background agent may:
- monitor ingest/batch status
- flag failed/stalled jobs to admins
- summarize exposure counts by payer, batch, and status
- prepare admin task queues from already-computed findings

The background agent may not:
- access cross-client data
- export raw PHI
- create final reimbursement findings without deterministic engine support
- transmit appeal packets automatically

## Storage and security requirements
- encrypted storage at rest
- encrypted transport in transit
- audit logging for user actions and agent actions
- role-based access control for admin/analyst scopes
- retention and deletion controls by client and batch
- environment separation between smoke/demo and production

## Production hardening still required
- durable Postgres instead of smoke SQLite
- durable object/file storage instead of temp local Vercel storage
- explicit RBAC for admin and analyst roles
- de-identification/tokenization layer before any external AI call
- documented retention schedule and incident response plan
