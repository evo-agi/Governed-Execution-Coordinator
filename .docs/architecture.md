# NWP Coordinator Architecture

The canonical component name is NWP Coordinator.

Current repository name: Governed Execution Coordinator. This operational
repository name is provisional. It may change without changing schema, authority, or durable identifiers.
Repository naming must not affect schema, authority, or durable identifiers.

## Scope

A2-P1/P1.1 establishes a local Coordinator skeleton for future A2 coding-work
state. It contains domain models, deterministic identity contracts, a pure
state transition evaluator, command/event and writer-session contracts, and
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

The B3a transition contract flow is:

`TransitionCommand + authoritative current state + internally reconstructed
TransitionContext -> evaluator -> TransitionEvent`

A future active writer session performs mutation through the atomic store
boundary. That boundary performs fencing, idempotency, current-state load,
expected-version comparison, authoritative context reconstruction, evaluator
invocation, and atomic state/event persistence. Proposed state, events, and
caller-supplied transition context are not supplied by callers.
Expected-version mismatch is an apply conflict with no event. Safe writer
metadata is evidence only and cannot authorize mutation.

The B3b reader prerequisite contract is documented in
`.docs/b3b-reader-prerequisite-contract.md`. It is not a reader implementation.
It pins the future read bundle authority: admitted backlog is mandatory
transition authority, `WorkItemRecord` attempt/repair limits are exact copies of
standing-lease limits, scalar current-state budget fields are zero-only reserved
compatibility fields in the first persisted slice, dependency receipts are
READY-only, operational row timestamps remain internal envelope metadata, and
schema 0001 is sufficient for the bounded typed-reader slice.

B3b1 implements the pure internal row-contract subset of that prerequisite. It
converts already-fetched explicit schema-0001 row mappings for lease identity,
authorization, dependency, work items, admitted backlogs, and
`global_stop_current` into validated typed envelopes. It validates exact row
shape, strict SQLite Booleans, canonical JSON/digest/index equality where the
schema provides canonical JSON, normalized current-state columns where it does
not, and exact operational UTC `Z` timestamps. It does not add a SQLite reader,
connection, transaction, row cardinality contract, not-found classification,
fixture insertion helper, combined transition-input loader, transition/global
stop mutation, or package-root export.

B3b2a implements the next internal prerequisite. It defines ordered
schema-0001 row-column tuples as the row-shape source of truth, derives existing
row-key contracts from those tuples, defines six immutable explicit-column
parameterized SELECT specifications, and defines a private future-B3c
transaction capability protocol. B3b2a does not implement a concrete
transaction-bound capability, accept raw SQLite connections as authority,
own connection lifecycle, own transactions, widen public `StateStore`, or
integrate with `WriterSession.apply_transition`.

B3b2b implements the six private SELECT readers over those specs and keeps them
unreachable from production callers. The readers validate lookup refs before
borrowing, borrow only through `_TransitionReadCapability`, execute the
parameterized specs, call `fetchmany(2)`, enforce zero/one/multiple
cardinality, require exact built-in tuples, build private mappings, delegate to
B3b1 row adapters, classify SQLite SELECT errors safely, sanitize unknown
capability borrow exceptions, and close cursors. Tests execute them with a
tests-only capability and in-memory tables. B3b2b does not add a concrete
capability, public read port, fixture program, cross-record assembly, admission,
authorization verification, transaction ownership, or mutation.
`connection.in_transaction` is not transaction identity.

B3c0a freezes the future transition mutation authority and ordering contract in
`.docs/b3c0a-transition-authority-and-order.md`. Future B3c must own one
nominal private capability and one opaque epoch per `BEGIN IMMEDIATE`
transaction, create that capability only inside `_SQLiteWriterSession` transition
apply while one operation lease is active and after writer fencing, treat
operation-lease acquisition as the externally atomic lifecycle/process and
retained-lock gate, share the transition/global-stop pre-SQLite mutation prefix
and one mutation slot, invalidate the capability before commit or rollback,
reject old epochs after
transaction end or restart, fence before idempotency, read current state and
expected version before context rows, capture the transaction timestamp only
after authoritative row binding, and preserve the pinned rollback/commit/close
precedence. B3c0a does not implement the concrete
capability, writer-fencing SELECT, idempotency/replay, event sequence SQL,
context assembly, evaluator invocation, fixtures, or mutation outcome.

Report projections are closed typed models. They expose safe refs, enums,
bounded counters, global-stop status, and a fixed non-authority notice only;
they are not generic sanitized payloads and do not carry private, endpoint,
path, platform, credential, or trust material.

## B0 SQLite Backend Selection

B0 selects SQLite, one private local database, as the future first production
state backend architecture. B1/B1.1 add the migration runner and local
administrative database posture. B2b adds the common state-authority lock for
initialize/migrate administration. B2c adds durable writer issuance and
internal writer-session acquisition. The current runtime still has no
production `StateStore` mutation backend, no coordinator service, and no
executable A2 capability.

The selected first-backend journal posture is rollback journal DELETE mode with
`synchronous=FULL`, `locking_mode=NORMAL`, `foreign_keys=ON`,
`trusted_schema=OFF` where supported, bounded `busy_timeout`, and
`BEGIN IMMEDIATE` mutation transactions. WAL is reserved for a later audit if a
current reader-concurrency requirement justifies its extra `-wal` and `-shm`
filesystem surface.

The B0/B2a authority, schema, threat, and operations contracts are documented
in:

- `.docs/sqlite-state-backend-adr.md`;
- `.docs/sqlite-schema-v1.md`;
- `.docs/sqlite-threat-model.md`;
- `.docs/sqlite-operations-and-recovery.md`;
- `.docs/writer-session-authority.md`.

## B1 SQLite Bootstrap And Migrations

B1/B1.1 implements only explicit operator-local SQLite bootstrap, observation,
validation, and migration infrastructure:

- fixed per-user local state-location policy using the canonical NWP
  Coordinator component name, not the repository display name;
- owner-only filesystem preparation and validation for the state root and
  fixed database filename;
- split standard-library SQLite connection posture verification for
  observational existing-database reads, administrative initialization, and
  managed-write migration;
- packaged, versioned, forward-only migration catalog;
- initial schema installation into an explicitly requested local database;
- non-mutating absent/empty/managed/unknown classification;
- migration-history/catalog equality and application-compatibility validation;
- full live-schema manifest verification derived from packaged migration bytes;
- bootstrap and generic managed current-state invariant checks.

B1.1 inspect/validate do not create missing roots or databases, do not change
persistent journal posture, do not repair or adopt unknown databases, and do
not auto-migrate. Initialize and migrate are explicit operator-local
administrative mutations. B2b initialize/migrate acquire the common
state-authority lock and revalidate while holding it. B1/B2b do not implement a
SQLite `StateStore`, product mutation methods, database-backed product reads,
reports over the database, coordinator service behavior, worker execution,
authorization, scheduling, repair, local commit, publication, or deployment.
B2c implements writer acquisition and `writer_ownership` issuance updates
only, not product mutations.
Normal future runtime must not run migrations concurrently with an active
Coordinator writer.

The B1 bootstrap and migration contract is documented in
`.docs/sqlite-bootstrap-and-migrations.md`.

## B2a Writer-Session Contract

B2a corrects the writer authority contract before implementation:

- standalone reconstructable public writer tokens are not mutation authority;
- `WriterSession` is the opaque future live mutation capability;
- safe writer metadata contains only non-secret issuance evidence and no proof,
  proof digest, lock path, process id, or liveness claim;
- no `current_writer()` read surface exists;
- one common future state-authority advisory lock covers initialize, migrate,
  writer acquisition, and the full active writer-session lifetime.

B2a does not implement writer acquisition, proof generation or verification,
SQLite `writer_ownership` updates, a concrete writer session, a `StateStore`
mutation backend, product reads, reports over SQLite, worker execution,
scheduling, repair, local commit, publication, deployment, or executable
authorization.

## B2b State-Authority Lock

B2b implements one common state-authority advisory lock for macOS and Linux.
The fixed persistent lock file remains named `coordinator-state.migration.lock`
on disk for compatibility, but the authority concept is the state-authority
lock. Initialize and migrate use that lock, including no-op current-schema
administration. Inspect and validate remain observational and do not create or
acquire the lock.

The lock provides live-process exclusion only. It is not writer authority, not
a writer credential, not durable state, and not sufficient for work-item or
global-stop mutation. B2c combines the retained lock with durable generation
issuance and a private in-memory proof inside an internal writer session.

B2b owns a real descriptor through a private resource object. Explicit
context-manager close remains the required release path; a one-shot finalizer
is only a fallback for abandoned lock objects and does not provide timing or
authority evidence. Every opened descriptor is immediately owned by a cleanup
scope until it is explicitly transferred. A parent-side lifecycle/fork gate
serializes descriptor opening, validation, `flock`, registry insertion,
finalizer publication, parent close, and pre-fork snapshot creation. Fork child
cleanup uses the frozen raw-descriptor snapshot, does not acquire inherited
Python locks, closes inherited descriptors without `LOCK_UN`, clears only the
child-side copied registry, and leaves parent authority untouched. Python
continues to warn that multithreaded fork is broadly unsafe, and third-party
forks that bypass Python at-fork hooks remain a limitation.

## B2c Writer Issuance

B2c implements internal SQLite writer acquisition for existing current managed
databases. Acquisition revalidates the managed schema while holding the common
lock, starts `BEGIN IMMEDIATE`, issues a monotonically increasing generation,
generates independent safe writer and issuance refs, stores only the
domain-separated private-proof digest, commits the singleton
`writer_ownership` row, closes the acquisition SQLite connection, and returns
an internal concrete `WriterSession` retaining the common lock.

The SQLite row remains latest issuance evidence only. It is not liveness truth,
not a credential, and not sufficient to mutate work-item or global-stop state.
B2 hardening adds generation-zero semantic rejection, child-side replacement
of inherited session synchronization after fork, and a private
operation-identity guard. Copied child leases no-op safely after fork;
same-thread close fails locally with
`writer_session_close_during_operation`; cross-thread close waits for active
operations; operation leases retain the concrete session wrapper; and
closing and cleaning are distinct so exactly one cleanup owner releases proof
and advisory-lock resources before closed is published. Nonblocking fallback
finalization may defer proof/lock cleanup until the last active operation exits,
and concurrent explicit close callers wait for closed. B2c mutation methods
enter that guard and fail locally with `writer_session_mutation_unavailable`.
B3a defines transition-persistence contracts only: command-only
`WriterSession.apply_transition`, typed lease runtime decisions,
schema-aligned decision/event provenance, canonical event/replay mappings, and
safe mutation-store errors. B3a does not add SQLite transition persistence.
B3b prerequisite contracts add pure/model reader prerequisites only: no
integrated typed SQLite reader, test database fixture insertion,
transition/global-stop mutation, admission, authorization verifier, worker,
scheduler, service, CLI, MCP, connector, repair, commit, publication, migration
0002, or executable A2 behavior. B3b1 adds only pure full-row envelope adapters
for already-fetched rows. B3b2a adds private capability-protocol and query-spec
contracts. B3b2b adds private SELECT readers with tests-only execution and no
production call sites. B3c0a adds contract/static pins only for the future
transition authority boundary and adds no transaction controller, concrete
capability, reader integration, context assembly, exact replay runtime, or
mutation. B3c concrete transaction capability and atomic transition apply, exact
replay, and fault injection remain future. B4 remains future for global-stop
persistence.
