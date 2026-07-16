# NWP Coordinator Agent Rules

If `.docs/` exists, always treat `.docs/` as the source of truth.

## Ownership

This repository owns the future A2 coding-work durable state contract only.
Current P1/P1.1 code has no production durable store and no active durable
writer.

Bridge remains the guarded worker/evidence adapter. Control Plane remains
product workflow authority. Execution Substrate remains product admission and
runtime authority. Maintenance Agent remains maintenance authority.
Infrastructure Manager remains readiness, provenance, and diagnostics
authority.

Operator/repo policy owns lease issuance and global stop. The coordinator
cannot self-authorize, cannot mint authorization, and cannot treat a valid
digest as execution permission.

Transition commands, transition events, writer tokens, global-stop commands,
and global-stop events are contract objects only until a future backend
tranche. Reports are projections only. They are not durable state,
authorization, acceptance, publication, or product truth.

B0 may select and document a future backend architecture and non-production
schema fixture, but it must not implement production storage, create database
files, run migrations, acquire writers, or enable executable A2 behavior.

Versioned Coordinator input schemas are closed-world in P1/P1.1. Unknown
fields, misspelled fields, duplicate JSON object keys, and unversioned
extension or metadata bags must fail before canonicalization or digest
comparison.

P1.1 transition persistence uses a command/event/apply-conflict algebra:
`TransitionCommand` contains caller intent, the pure evaluator produces exactly
one durable `TransitionEvent` for accepted or domain-rejected commands, and the
event is the receipt. Caller code must not provide proposed records, proposed
events, or receipts.

Expected-version mismatch is an apply/store conflict, not a durable domain
rejection. Writer fencing, internal idempotency lookup, authoritative current
state loading, expected-version comparison, evaluator invocation, exact replay,
and atomic state/event persistence belong to the atomic store boundary.

Apply conflicts never carry transition events. Exact replay requires a valid
current writer plus the same idempotency key and the same canonical command
digest. Same key with a different digest conflicts. Stale writers receive only
`stale_writer_token` and no replay, key-existence, or conflict detail.

Global-stop updates use the same command/event/apply-conflict/outcome algebra.
The Coordinator cannot manufacture operator authorization and cannot clear,
weaken, or replace global stop without a typed operator decision.

## P1 Prohibitions

P1/P1.1 must not implement worker execution, a scheduling loop, a queue
consumer, a daemon, repair, local commit behavior, publication, production
storage, a validation sandbox, executable lease authorization, signing, keys,
trust roots, writer-token acquisition, or a trusted-local/allow-all production
authorization path.

P1 public state and report models must not include private briefs, raw prompts,
raw logs, credentials, secrets, local absolute paths, endpoints, platform
identifiers, or trust material.

P1 report projections must be closed typed models in `reports.py`. Do not add a
second report-shaped helper or a generic sanitize-and-keep payload boundary.

## Change Rules

Before changing authority-sensitive behavior, identify the governing invariant
in `.docs/` and keep architectural and security boundaries intact.

Do not bypass governance layers. Surface conflicts instead of working around
them.

Docs, tests, and code must change together for authority-sensitive behavior.
After changes, update `.docs/` to reflect reality and ensure there is no drift
between code and documentation.
