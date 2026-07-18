# NWP Coordinator

Current repository name: Governed Execution Coordinator.

This operational repository name is provisional and may change without changing
schema, authority, or durable identifiers. The canonical component name is
NWP Coordinator.

This repository contains the A2-P1/P1.1 skeleton for the future local
coding-work coordinator. P1/P1.1 provides offline contract primitives and B1
SQLite bootstrap/migration infrastructure only:

- standing lease identity parsing, deterministic canonicalization, and digest
  validation for `governed-execution.nwp-standing-lease.v1`;
- closed-world v1 input parsing that rejects unknown and duplicate fields
  before canonicalization;
- a fail-closed unsupported authorization provider;
- finite backlog parsing and canonical identity;
- a pure work-item state transition evaluator that emits accepted or
  domain-rejected transition events;
- a P1.1 command/event/apply-conflict state-store protocol with no production
  backend;
- operator-owned global-stop command/event models and enforcement checks;
- closed, typed, non-authoritative report projections;
- explicit operator-local SQLite database bootstrap, observational database
  inspection/validation, connection posture, migration catalog,
  migration-history/catalog equality, live-schema manifest verification, and
  schema compatibility checks;
- a B2a writer-session authority contract that replaces reconstructable public
  token-shaped mutation authority with an opaque future `WriterSession`
  protocol and safe non-authoritative writer metadata;
- a B2b common state-authority advisory lock, used by SQLite initialize and
  migrate administration for live-process exclusion only;
- B2c durable writer issuance and internal SQLite `WriterSession` acquisition,
  with private in-memory proof material and no mutation storage;
- B3a canonical persistence and provenance contracts for future work-item
  transition persistence, with no SQLite transition mutation runtime;
- B3b prerequisite authority contracts for future typed SQLite readers, pinning
  admitted-backlog binding, exact lease-copied attempt/repair limits,
  zero-only scalar persisted budget fields, READY-only dependency receipts,
  internal timestamp-envelope posture, and schema-0001 sufficiency for the
  bounded reader slice, with no reader or fixture implementation.
- B3b1 pure internal full-row contracts that wrap already-fetched
  schema-0001 row mappings in operational timestamp envelopes for lease
  identity, authorization, dependency, work-item, admitted-backlog, and
  global-stop-current rows, with no SQLite I/O or reader implementation.
- B3b2a private transaction-capability protocol and immutable SELECT contract
  data:
  ordered row-column tuples, six explicit-column parameterized query specs, and
  capability-first future reader signatures for B3c-managed active
  transactions, with no concrete transaction authority, SQL execution, row
  reconstruction, cardinality, missing-row classification, public read port,
  fixture insertion, or mutation behavior.

P1.1 models expected-version mismatch, stale writer sessions, idempotency key
reuse, and authoritative not-found cases as apply conflicts with no event.
Domain rejections, such as invalid predecessors, global stop, budget failure,
missing evidence, and invariant P1 `stage_not_enabled`, commit exactly one
event. The event is the receipt.
For valid bound commands targeting P1-disabled worker, repair, or local-commit
states, `stage_not_enabled` precedes contextual domain reasons while the event
still retains complete runtime provenance.

P1/B1 does not execute workers, invoke Bridge or Codex, start a scheduler, run
a daemon, consume a queue, create worktrees, implement `StateStore` mutations,
acquire a Coordinator writer, authorize executable work, run validation
sandboxes, repair, commit, publish, push, open pull requests, or contact live
product routes.

The P1 runtime has no supported policy, configuration, callback, or environment
path that enables future worker, repair, or local-commit stages.

B0 selected SQLite, one private local database, as the future first production
state backend architecture. B1/B1.1 implements secure local database bootstrap,
non-mutating inspection/validation for existing databases, live-schema
integrity checks, and forward-only migrations for explicitly requested
operator-local administration. B2a corrects the writer-session contract, and
B2b adds the shared state-authority advisory lock plus initialize/migrate
integration. B2b uses explicit close/context-manager release with a
finalizer-backed cleanup fallback for abandoned lock objects; finalization is
not a timing guarantee. Lock descriptor publication and parent-side cleanup are
serialized by one lifecycle/fork gate; the fork child handler uses the frozen
descriptor snapshot, closes inherited descriptors without `LOCK_UN`, and does
not acquire inherited Python locks. Lock possession alone is not writer
authority.

B2c acquires an internal SQLite writer session only for an existing managed
database. It increments the durable writer generation, stores only a proof
digest in `writer_ownership`, closes the acquisition connection before return,
and retains the common lock for the session lifetime. B2 hardening rejects
present generation-zero writer rows as malformed managed state, replaces
child-side inherited session synchronization after fork, and adds a private
operation-identity guard. Copied child leases no-op safely, same-thread close
fails locally with `writer_session_close_during_operation`, cross-thread close
waits for active operations, operation leases retain the concrete session
wrapper, closing and cleaning are distinct, closed is published only after
proof/lock cleanup completes, and fallback finalization is nonblocking with
deferred proof/lock cleanup by the last operation. Concurrent explicit close
callers wait for closed. The runtime still provides no `StateStore` mutation
backend, transition/global-stop persistence, coordinator service, worker,
scheduler, authorization path, or executable A2 capability. B2c mutation
methods enter that guard and fail locally with
`writer_session_mutation_unavailable`.

B3a is contract-only. `WriterSession.apply_transition` accepts only a
`TransitionCommand`; future transition apply must reconstruct
`TransitionContext` internally from authoritative persisted records. B3a adds
typed lease runtime status, schema-aligned authorization/dependency decisions,
provenance-complete transition events, canonical transition-event and replay
`WorkItemRecord` mappings, event-sequence and transaction-timestamp contracts,
and a safe mutation-store error taxonomy. It does not insert transition events,
update work items, perform idempotency/replay/expected-version runtime logic,
implement admission, verify operator-policy authorization, mutate global stop,
or execute work.

B3b prerequisite contracts are documented in
`.docs/b3b-reader-prerequisite-contract.md`. They are implementation-only
contract pins, not typed SQLite readers. They add no SQLite I/O, no test database
fixture insertion helper, no transition/global-stop mutation, no production
admission or authorization implementation, no executable work, and no migration
0002.

B3b1 is the first implementation under those pins. It adds pure mapping-to-value
contracts for complete explicit row shapes and retains `created_at`,
`admitted_at`, and `updated_at` only inside internal envelopes. It still adds no
SQLite `SELECT`, connection, row cardinality behavior, not-found behavior,
combined transition-input loader, fixture insertion helper, idempotency/replay,
expected-version runtime, event sequence allocation, B3c transition apply, or
B4 global-stop mutation.

B3b2a adds only internal prerequisites for those future readers: ordered
schema-0001 row-column tuples, immutable data-only SELECT specifications, and a
private future-B3c transaction capability protocol. B3b2a does not provide a
concrete production capability, raw-connection scope, reader execution, or
connection lifecycle. `connection.in_transaction` is not transaction identity.
Future B3c must own one opaque epoch per `BEGIN IMMEDIATE` transaction,
invalidate it before commit or rollback, reject old epochs after transaction end
or restart on the same connection, and remain responsible for operation-guard,
writer-fencing, idempotency, expected-version, reader ordering, context
assembly, evaluator invocation, and mutation outcome. B3b2b readers will accept
only the private capability protocol.

See `.docs/` for the authority boundary and A2-P1 contract.
