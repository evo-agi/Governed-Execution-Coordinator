# NWP Coordinator Architecture

The canonical component name is NWP Coordinator.

Current repository name: Governed Execution Coordinator. This operational
repository name is provisional. It may change without changing schema, authority, or durable identifiers.
Repository naming must not affect schema, authority, or durable identifiers.

## Scope

A2-P1/P1.1 establishes a local Coordinator skeleton for future A2 coding-work
state. It contains domain models, deterministic identity contracts, a pure
state transition evaluator, command/event state-store contracts, and
non-authoritative report projections.

P1 versioned inputs are closed-world contracts. Unknown keys, duplicate JSON
object keys, misspelled keys, and unversioned extension bags fail before
canonicalization or digest verification.

P1/P1.1 is not an executable coordinator slice. It has no worker invocation path,
no scheduler, no daemon, no queue consumer, no `StateStore` mutation backend,
no sandbox, no repair executor, no local commit behavior, and no publication
behavior. It also has no production future-stage enablement policy or
configuration.

## Authorities

The future NWP Coordinator owns only future A2 coding-work durable state.
Bridge remains a guarded worker/evidence adapter. Codex remains a worker only.
Control Plane remains product workflow authority. Execution Substrate remains
product admission/runtime authority. Maintenance Agent remains maintenance
authority. Infrastructure Manager remains readiness, provenance, and
diagnostics authority.

Operator/repo policy owns lease issuance and global stop. The Coordinator
observes and enforces those decisions but cannot issue them, clear them,
weaken them, reinterpret them, or self-authorize.

ChatGPT, connector state, API request/session context, Symphony, reports,
Bridge ledgers, Bridge reports, and local runner evidence remain adapters or
projections. They are not durable A2 state.

## P1 Package

The implementation namespace is `ge_nwp_coordinator`. That package name is an
implementation detail, not a durable identity and not a promise about the
repository display name.

Runtime code uses only the Python standard library. Test-only fakes live under
`tests/`; production code provides only fail-closed default authorization,
typed contract objects, pure evaluators, and state-store protocols.

The P1.1 transition flow is:

`TransitionCommand + typed context + authoritative current state -> evaluator
-> TransitionEvent`

A future atomic store boundary performs fencing, idempotency, current-state
load, expected-version comparison, evaluator invocation, and atomic
state/event persistence. Proposed state and events are not supplied by callers.
Expected-version mismatch is an apply conflict with no event.

Report projections are closed typed models. They expose safe refs, enums,
bounded counters, global-stop status, and a fixed non-authority notice only;
they are not generic sanitized payloads and do not carry private, endpoint,
path, platform, credential, or trust material.

## B0 SQLite Backend Selection

B0 selects SQLite, one private local database, as the future first production
state backend architecture. This is a documentation, schema-fixture, and static
test tranche only. The current runtime still has no production store, no
database file, no migration runner, no writer acquisition, no coordinator
service, and no executable A2 capability.

The selected first-backend journal posture is rollback journal DELETE mode with
`synchronous=FULL`, `locking_mode=NORMAL`, `foreign_keys=ON`,
`trusted_schema=OFF` where supported, bounded `busy_timeout`, and
`BEGIN IMMEDIATE` mutation transactions. WAL is reserved for a later audit if a
current reader-concurrency requirement justifies its extra `-wal` and `-shm`
filesystem surface.

The B0 authority, schema, threat, and operations contracts are documented in:

- `.docs/sqlite-state-backend-adr.md`;
- `.docs/sqlite-schema-v1.md`;
- `.docs/sqlite-threat-model.md`;
- `.docs/sqlite-operations-and-recovery.md`.

## B1 SQLite Bootstrap And Migrations

B1 implements only explicit operator-local SQLite bootstrap and migration
infrastructure:

- fixed per-user local state-location policy using the canonical NWP
  Coordinator component name, not the repository display name;
- owner-only filesystem preparation and validation for the state root and
  fixed database filename;
- standard-library SQLite connection posture verification;
- packaged, versioned, forward-only migration catalog;
- initial schema installation into an explicitly requested local database;
- migration-history checksum and application-compatibility validation.

B1 does not implement a SQLite `StateStore`, product mutation methods,
database-backed product reads, reports over the database, writer acquisition,
advisory writer locking, coordinator service behavior, worker execution,
authorization, scheduling, repair, local commit, publication, or deployment.
Normal future runtime must not run migrations concurrently with an active
Coordinator writer.

The B1 bootstrap and migration contract is documented in
`.docs/sqlite-bootstrap-and-migrations.md`.
