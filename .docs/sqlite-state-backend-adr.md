# SQLite State Backend ADR

Status: accepted architecture; C2B1 implements the current bounded
administrative migration framework over the earlier B1/B1.1/B2b bootstrap,
observational inspection/validation, and common state-authority advisory
lock for initialize/migrate administration. B2a corrects the writer-session
authority contract. B2c implements durable writer issuance and internal
writer-session acquisition for managed SQLite databases. B3a implements
canonical persistence and provenance contracts only. B3b2a implements private
non-executing capability-protocol and immutable query-contract prerequisites
only. B3b2b implements private SELECT readers with no production integration.
B3c0a pins transition authority, ordering, fencing, and failure precedence as a
contract/static prerequisite only. B3c0b adds pure/static transition-event row,
replay, idempotency, and sequence contracts only. B3 tests-only coherent
fixtures add temporary managed graphs under `tests/` only, with no production
admission or runtime authority. B3c1 adds prerequisite contract pins for the
production-unintegrated rollback-only controller posture, single private
controller construction path, mutation slot, operation-lease interfaces,
resource-owned state-database filesystem binding, writer-row query ownership, fencing
taxonomy, nominal capability epoch, cleanup precedence, and B3c1a/B3c1b split.
B3c1a private WriterSession authority plumbing is documented in
`.docs/b3c1a-writer-session-authority.md`. B3c2 adds only private
transaction-internal transition-event readers plus shared SELECT lifecycle
support; it has no production caller, no mutation, no commit, and no migration
0002. B3c3 adds only a private rollback-only transition dry run for preflight,
stale-writer conversion, idempotency read/match, current/expected checks,
context-reader ordering, authority binding, timestamp placement,
lease-runtime/context construction, evaluator invocation, and cleanup/result
precedence; it has no durable mutation, public caller, commit, or migration
0002. B3c4c adds public operation-guarded transition delegation to the B3c4b
private atomic entry plus exact public preflight mapping; it adds no public
SQLite ownership, global-stop persistence, executable A2 behavior, schema-ID
bump, or migration 0002.

B0 selects one private local SQLite database as the first production state
backend architecture for the future NWP Coordinator. B1/B1.1 implements
explicit operator-local database bootstrap, observational validation, and
migrations. B2a replaces standalone reconstructable public mutation authority
with an opaque future `WriterSession` contract and safe writer metadata. B2b
adds the common state-authority lock and uses it for initialize/migrate. B2c
adds internal writer acquisition, a private operation guard, and
session-local mutation-unavailable behavior. B2c does not implement a
production `StateStore`, start a
coordinator service, or enable executable A2 behavior. B3a adds no SQLite
transition mutation runtime. B3b2a adds no executing reader, production read
port, transition mutation, or transaction ownership. B3b2b adds executing
private SELECT readers only; they are not production read ports and add no
concrete transaction capability, transition mutation, production fixture program, or
transaction ownership. B3c0a adds no concrete transaction capability,
transaction controller, writer-fencing SELECT, fixture, context assembly,
evaluator integration, or mutation.
B3c0b adds no SQL execution, idempotency/event/sequence reader, fixture,
concrete transaction capability, writer fencing, context assembly, evaluator
integration, event insertion, current-state update, or mutation.
B3c1a adds only private WriterSession mutation-slot and operation-lease
verification plumbing plus a retained private root/lock/database filesystem
binding. B3c1b adds only private rollback-only writer fencing/capability
mechanics: one private controller, one fresh managed read/write connection
opened only through that binding, `BEGIN IMMEDIATE`, post-begin binding
revalidation, managed validation, one bounded writer-row query using the
existing parser, one nominal capability with one opaque epoch, permanent
invalidation, rollback, close, and private `_WriterIssuanceMatch` return.
B3c1 adds no B3b2 reader integration, context
assembly, evaluator integration, event insertion, current-state update, public
mutation-method behavior change, commit, or migration 0002.
B3c2 adds private event/idempotency and observed maximum-sequence readers only.
It consumes the B3c0b immutable query specs through the B3c1b nominal
capability seam in tests, does not call the pure matcher or allocator in
production source, and does not insert events or mutate current state.
B3c3 adds the private rollback-only dry-run controller entry point, clock
implementation, idempotency reader call, pure matcher integration,
current-state loading, expected-version comparison, context-reader ordering,
`TransitionContext` construction, and evaluator invocation. It does not add
sequence read or allocation, event insertion, state update, CAS, commit, public
API, or migration 0002.

## Decision

The first backend will use one SQLite database behind the `StateStore` port.
All transition and global-stop mutations must occur inside one SQLite
transaction that owns writer fencing, idempotency inspection, authoritative
current-state loading, decision-context verification, expected-version
comparison, pure evaluator invocation, event insertion, current-state update,
and exact replay.

Rejected first-backend alternatives:

- A bespoke append-only journal. It would need custom locking, compare-and-set,
  idempotency indexes, current-state materialization, torn-write recovery,
  migrations, backup, restore, corruption handling, and global-stop reads.
- A journal plus separate materialized-state store. It creates dual durable
  truth unless another atomic authority is invented.
- An external service. The first backend must be local, deterministic, and not
  require an external service.

## B0 Scope

B0 may contain:

- architecture documents;
- a non-production SQL schema fixture;
- static tests;
- tests that execute the fixture against `sqlite3.connect(":memory:")`.

B0 must not contain:

- production SQLite connection code;
- `sqlite3` imports under `src/`;
- persistent `.db`, `.sqlite`, journal, WAL, or SHM files;
- a migration runner;
- writer acquisition;
- a coordinator loop, worker, scheduler, daemon, queue, repair, sandbox,
  local commit, publication, or deployment behavior.

## B1 Scope

B1/B1.1 may contain:

- production SQLite connection/bootstrap code using the Python standard
  library;
- fixed local state-location and filesystem-permission validation;
- packaged migration resources loaded from the installed Coordinator package;
- observational existing-database inspection/validation that does not create or
  mutate files or persistent journal posture;
- forward-only migration execution for explicit administrative initialize and
  migrate operations;
- migration-history/catalog equality and schema/application compatibility
  validation;
- cumulative live-schema manifest verification derived from exact packaged SQL
  through the selected terminal migration;
- bootstrap and generic managed current-state invariant validation.

B1/B2b must not contain:

- a SQLite `StateStore` implementation;
- `StateStore.apply_transition` or `StateStore.apply_global_stop_update`
  implementation;
- writer acquisition, writer issuance, proof generation, or
  `writer_ownership` mutation;
- product reads or report generation over the database;
- work-item, decision receipt, transition event, global-stop event, or
  global-stop current-state mutation APIs outside schema bootstrap;
- executable authorization, scheduling, worker execution, repair, commit,
  publication, service, daemon, or deployment behavior.

B2c may contain only internal writer acquisition, proof generation/digest
verification, `writer_ownership` issuance updates, private operation guarding,
and a concrete internal `WriterSession` whose mutation methods fail locally.
B2c must not contain a SQLite `StateStore`, event persistence, work-item
mutation, global-stop mutation, reports over writer issuance, service
behavior, worker execution, or executable A2 behavior.

## Backend Responsibility Matrix

Coordinator transition service:

- validates external command shape before invoking writer apply;
- calls backend-created `WriterSession.apply_transition(command)` with no
  caller-supplied `TransitionContext`;
- does not write SQLite directly once the production store exists;
- does not call Bridge, Codex, workers, reports, remotes, or authorization
  providers inside the mutation transaction.

SQLite transition transaction:

- is entered only through a backend-created active `WriterSession`;
- validates writer ownership before idempotency disclosure;
- performs internal idempotency lookup from event rows;
- loads authoritative current work-item or global-stop state;
- compares expected version;
- loads or verifies persisted decision receipts in the B3c0a-pinned order;
- invokes the pure evaluator with no external I/O;
- writes one event, the replay snapshot, and any current-state change
  atomically;
- returns either an apply conflict or an authoritative committed outcome.

Pure evaluator:

- owns domain rules only;
- constructs accepted or domain-rejected events;
- does not perform persistence, writer fencing, idempotency lookup, reports, or
  external authorization.

Reports:

- Reports are projections only.
- are projections only;
- are never database input;
- are never current-state authority;
- cannot expose raw rows or canonical JSON as public payloads.

Bridge, Control Plane, Execution Substrate, Maintenance Agent, and
Infrastructure Manager:

- have no database handle;
- have no state-write authority;
- remain external authorities, adapters, evidence sources, or projections
  according to their existing boundaries.

## Journal Mode Decision

The first implementation posture is:

- `journal_mode=DELETE`;
- `synchronous=FULL`;
- `locking_mode=NORMAL`;
- `BEGIN IMMEDIATE` for mutation transactions;
- `foreign_keys=ON`;
- `trusted_schema=OFF` where supported;
- bounded `busy_timeout`.

Rollback journal / DELETE mode is selected for B0 because the first backend has
one local writer, short in-process reads, simpler containment, fewer persistent
auxiliary files, and simpler offline/online backup posture.

WAL remains a future option. WAL improves reader concurrency, but it introduces
persistent `-wal` and `-shm` files, checkpoint policy, and a broader filesystem
surface. Selecting WAL requires a current source-backed concurrent-reader need
and a focused operations/recovery audit.

Journal mode is an implementation posture, not durable contract identity.
Changing it later requires an operations and recovery audit.

## Writer Ownership Model

The first local writer model is:

- one common state-authority lock file in the same secured state directory;
- an exclusive OS advisory lock for live-process exclusion;
- a durable singleton `writer_ownership` row;
- monotonically increasing generation;
- independently generated safe writer and issuance refs;
- a private random opaque 256-bit issuance proof held only in an active
  `WriterSession`;
- only a domain-separated issuance proof digest stored in the database;
- every mutation compares writer ref, generation, and issuance proof;
- new acquisition increments generation atomically;
- process crash releases the OS lock;
- no TTL, heartbeat, or automatic failover in the first backend;
- hung-writer recovery requires explicit operator action.

The OS lock is live-process exclusion. The durable generation and private
issuance proof are fencing authority. Neither is sufficient alone. The durable
row is latest issuance evidence, not liveness truth. Safe writer metadata is
not a credential. Process-local lifecycle synchronization and the private
operation guard are necessary session controls but are not sufficient
authority. Workers, Bridge, reports, readers, and adapters never receive writer
sessions or private writer credentials.

B2b implements the lock-file creation, validation, nonblocking exclusive
`fcntl.flock` acquisition, release, fork/exec descriptor hygiene, same-process
exclusion, cross-process exclusion, crash release behavior, and initialize/
migrate integration for that common lock. B2c implements writer issuance
generation, proof generation and verification, `writer_ownership` acquisition
updates, and the internal concrete writer session. It still implements no
mutation backend. The detailed writer-session contract lives in
`.docs/writer-session-authority.md`.
B2b descriptor hygiene includes immediate cleanup ownership after `os.open`,
a parent lifecycle/fork gate for publication and pre-fork snapshot creation,
and child cleanup that closes inherited descriptors without acquiring
inherited Python locks or issuing `LOCK_UN`.

## Event-Owned Idempotency

The first schema uses event-owned idempotency:

- `transition_events` owns unique `(work_item_id, idempotency_key)`;
- `global_stop_events` owns unique `idempotency_key`;
- no separate idempotency tables exist in the first schema;
- if the key and command digest match, replay returns the stored event plus the
  stored replay snapshot;
- if the key matches but digest differs, the store returns an apply conflict
  and creates no event;
- if no event exists, no idempotency record exists.

Exact replay snapshots do not become current-state truth. They are authoritative
only for replaying the original command outcome.

B3c0b implements the pure transition-event half of that contract for already
fetched rows. `transition_event_record_envelope_from_row(...)` reconstructs the
canonical event and replay `WorkItemRecord`, validates exact JSON/digest/index
equality, created-at/runtime equality, and bounded zero-budget replay posture.
`match_transition_event_idempotency(...)` returns miss, exact replay,
`idempotency_key_reuse_conflict`, or `database_integrity_failure` without
reading SQLite. The future idempotency lookup remains a data-only query spec:
`SELECT <all transition event row columns> FROM transition_events WHERE
work_item_id = ? AND idempotency_key = ? LIMIT 2`.
B3c2's private idempotency reader consumes that spec only after both lookup
inputs are exact built-in `str` values and have passed the existing contract-ref
grammar. That exact-type gate is local to B3c2 and does not alter repo-wide
string validation, B3b2 inputs, or command construction.

## Transaction Order

Transition mutation transaction:

B3c0a is the source of truth for the exact future transition apply order. The
summary order is:

1. acquire the operation lease; acquisition performs owner-process and
   active-session validation and returns only after the retained authority lock
   is confirmed active;
2. perform exact `TransitionCommand` checks and bounded persisted-slice local
   checks;
3. acquire the shared per-session mutation slot;
4. derive the resource-owned root/lock/database binding from the active
   operation lease;
5. open one existing managed read/write connection through that binding;
6. execute `BEGIN IMMEDIATE`;
7. revalidate the retained binding and validate managed schema/posture inside
   the transaction;
8. load and parse `writer_ownership`;
9. verify writer generation, refs, and private issuance proof;
10. create the nominal capability only after fencing;
11. look up `transition_events` by event-owned idempotency;
12. replay exact command digests or return idempotency conflict before changed
    context is read;
13. load authoritative `work_items`;
14. compare command expected version;
15. load context rows in B3c0a order: lease identity, admitted backlog,
    authorization, READY dependency only when required, then
    `global_stop_current`;
16. apply all cross-record binding and authorization-support checks;
17. capture one transaction UTC timestamp only after successful binding;
18. derive `LeaseRuntimeDecision`;
19. Reconstruct `TransitionContext` exclusively from persisted receipts and
    transaction-derived lease runtime status;
20. invoke the pure evaluator with no external I/O exactly once;
21. allocate event sequence;
22. insert exactly one transition event and replay snapshot;
23. on acceptance, compare-and-set update `work_items`;
24. on domain rejection, leave `work_items` unchanged;
25. invalidate the capability before commit or rollback;
26. commit or roll back, close the connection, and return only after transaction
    resolution.

Exact replay happens after writer-session fencing and idempotency match, before
changed decision or global-stop context is re-evaluated.
No timestamp is generated for replay, idempotency conflict, work-item not found,
expected-version conflict, or validation conflict.
B3c0b defines only pure sequence allocation and immutable maximum-sequence SQL
text. It does not run the maximum-sequence query and does not allocate from
SQLite.
B3c2 runs the maximum-sequence query only as a private transaction-internal
observed-maximum reader. It returns no next sequence and makes no reservation,
allocation, consumption, or uniqueness claim; B3c4b owns private allocator and
insert integration after fresh evaluation.
B3c2's shared SELECT support treats cursor-close failure after successful fetch
as operational cleanup failure only. Earlier execute/fetch failure remains
primary if cleanup also fails.
B3c3 is limited to the rollback-only subset of this order through evaluator dry
run and cleanup. Fresh evaluator output is non-durable and
non-receipt. B3c3 performs no maximum-sequence read, allocator call, insert,
CAS, or commit; B3c4b is the first private persistence/commit tranche.

B4a freezes prerequisite global-stop contracts in
`.docs/b4a-global-stop-prerequisite-contracts.md`: public global-stop
preflight vocabulary, private no-I/O preflight, persisted receipt and
event/replay row contracts, transaction-internal readers, table-local sequence
allocation, receipt-binding taxonomy, and pure/static write grammar. It does not
provision receipts or itself make `apply_global_stop_update()` functional.

`.docs/b4b-private-atomic-global-stop-persistence.md`: private atomic
global-stop persistence through the same neutral mutation controller, read
capability, mutation slot, bound-open path, and commit-resolution graph as
transition persistence. It verifies only already-persisted operator-decision
receipts, persists accepted or domain-rejected events atomically, updates the
singleton only by accepted CAS, preserves commit uncertainty/retry semantics,
and keeps transaction ownership private. B4c later makes public
`apply_global_stop_update()` a guarded adapter to this private entry.

The private B4b global-stop mutation transaction shares the same pre-SQLite
authority prefix as transition mutation:

1. acquire the operation lease; acquisition performs owner-process and active-session validation and returns only after the retained authority lock is confirmed active;
2. perform existing global-stop typed command/operator-decision local checks;
3. acquire the shared per-session mutation slot;
4. derive the resource-owned root/lock/database binding from the active operation lease;
5. open one existing managed read/write connection through that binding;
6. execute `BEGIN IMMEDIATE`;
7. revalidate the retained binding and validate managed schema/posture inside the transaction;
8. load and parse `writer_ownership`;
9. verify writer fencing;
10. look up `global_stop_events` by idempotency key;
11. if command digest matches, return stored event and replay snapshot;
12. if command digest differs, return `idempotency_key_reuse_conflict`;
13. load authoritative `global_stop_current`;
14. compare command expected version;
15. load the operator decision receipt;
16. verify command and typed operator decision against the persisted receipt;
17. invoke the pure global-stop evaluator with no external I/O;
18. capture one normalized transaction timestamp only after a fresh evaluation;
19. read the table-local maximum global-stop event sequence;
20. allocate the next table-local sequence;
21. insert exactly one global-stop event and replay snapshot;
22. on acceptance, update `global_stop_current` by singleton CAS;
23. on domain rejection, leave `global_stop_current` unchanged;
24. resolve commit, rollback, and close through the neutral mutation
    commit-resolution graph;
25. return the committed event and resulting global-stop state only after resolution.

## Context Provenance

New commands must use authoritative decision and global-stop records loaded or
verified inside the transaction:

- lease identity decision ref must exist and bind to the same lease;
- authorization decision ref must exist and bind to the same lease;
- dependency decision ref must exist when required by the target state and a
  READY transition must bind that dependency receipt to the same work item;
- global stop is loaded from `global_stop_current`;
- command global-stop ref and version must agree with the authoritative
  snapshot;
- persisted schema ids and canonical digests must validate before evaluator
  use;
- externally supplied typed decisions are never trusted solely by shape;
- caller-supplied `TransitionContext` is not part of
  `WriterSession.apply_transition`.

This backend does not solve executable authorization. Until a separate
authorization architecture is accepted, current production truth remains
fail-closed and unsupported.

If the P1.1 conflict vocabulary is too coarse for a context-provenance mismatch,
B3 must add an explicit contract extension instead of inventing hidden backend
behavior.

## Migration Architecture

C2B1 separates three authorities. `schema_migrations` is authoritative
installed-migration evidence. The exact cumulative code-owned packaged SQL
sequence is authoritative expected schema. The bounded live-schema manifest is
an independently verified observation. History alone never proves schema, and
live schema never self-proves its migration history.

Migration IDs are ordered and checksummed. A row persists sequence, migration
ID, checksum, `applied_at`, and compatibility bounds. Exact equality of
sequence/ID/checksum/bounds resolves one packaged definition; `destructive` is
catalog-only and is not a history column. A selected destructive definition is
rejected before the common lock or writable activity. Migrations are
forward-only; automatic downgrade is unsupported and restore is the recovery
path for a separately authorized destructive change.

Ordinary open admits only the exact complete current terminal and applies
application-generation compatibility only to that installed terminal. A
supported older prefix remains public `UNKNOWN` and is eligible only for
explicit migration. Complete initialization and a complete contiguous suffix
each use one administrative `BEGIN IMMEDIATE`, one planned timestamp, and one
commit attempt. Before commit begins, failure attempts rollback and close. Once
commit begins, rollback is forbidden: a raised commit or unprovable cleanup is
resolved under the retained common lock by filesystem-bound readback as
`COMMITTED_EXACT`, `DEFINITELY_NOT_COMMITTED`, or `UNRESOLVED`. Unresolved
evidence raises `migration_outcome_unresolved` and permits no automatic retry
or remainder append.

`PRAGMA user_version`, if used later, is only a checked convenience mirror.

C2B1 implements the lasting migration catalog and runner. At C2B2 Slice 1
tranche completion, that runner used application generation 2 with terminal tip
`0002_development_program_and_effect_state` and exactly two production SQL
resources. That is historical tranche status. The current repository retains
application generation 2, contains four production SQL resources, and has
current packaged tip `0004_rw0_c1_durable_evidence`. Migrations 0002 and 0003
remain unchanged historical prefixes; the current production SQL resource
count is `4`. C2B2 did not implement or acquire ownership of migration 0003,
migration 0004, or Section 41. Migration SQL is
loaded only from code-owned package resources and never from arbitrary
filesystem paths. Connection PRAGMAs are set and verified by bootstrap code and
are not part of migration identity. Observational B1.1 inspection/validation
uses a separate create-disabled connection path and queries persistent journal
posture instead of changing it. Administrative initialize remains the
create-capable path. Administrative migrate requires managed observational
preflight before opening read/write. Initialize and migrate acquire the same
state-authority lock after observational preflight, revalidate while holding
it, and use the filesystem-bound database seam for mutation and recovery. B2c writer acquisition requires an existing managed
database, revalidates while holding that same lock, validates again inside
`BEGIN IMMEDIATE`, updates only `writer_ownership`, commits, closes the
acquisition connection, and retains the lock in the returned internal session.
B1.1 and B2c treat a missing writer row as the valid pre-first-acquisition
state and a present generation `0` row as malformed managed writer state. B2c
mutation-unavailable methods enter and exit the private operation guard so
future B3/B4 transactions can retain proof and advisory-lock authority across
the full operation. B3b2a's private capability protocol and B3b2b's private
reader execution do not prove that guard, transaction identity, or writer
fencing by themselves; future B3c must create one concrete opaque epoch only
through the private rollback-only transaction controller after operation-lease
acquisition, mutation-specific local checks, shared mutation-slot acquisition,
resource-owned bound-database derivation, `BEGIN IMMEDIATE`, managed
validation, and fencing gates, and must invalidate it before commit or
rollback. The B3c1b controller accepts only the active operation lease and
opens the WriterSession resource-owned binding, which contains the exact
CoordinatorStateLocation, state-root identity, authority-lock-file identity,
and single-link database-file identity captured while the retained common
authority lock was held; a matching writer row in a cloned database is not
authority. Replaced root/lock/database paths and hard-linked active database
aliases fail closed. Future production invocation of that controller may occur
only from `_SQLiteWriterSession.apply_transition()`; B3c1 gives the controller
no production caller and public mutation methods remain unavailable.
If bound-open admission fails after SQLite open, the helper preserves the
primary structural or operational classification even if best-effort close of
the rejected connection also fails, returns no connection, and does not retain
raw cleanup detail. After a connection has been admitted into the rollback-only
controller, transaction-resolution close failure remains an independent
`mutation_failed` cleanup result.
B3c2 transaction-internal reader tests exercise the nominal capability through a
deadline-bounded fork proof that always reaps children and observes
`process_mismatch` before inherited connection use.
B3c4b private transition persistence exists, B3c4c guarded public transition
delegation exists, B4b private global-stop persistence exists, and B4c guarded
public global-stop delegation exists. Operator-decision receipt provisioning
remains a separate reopened seam, and no schema-ID bump, migration 0002,
production authorization, or orchestration claim is added.

Migration `0001_initial` creates the first schema and seeds only a canonical
clear `global_stop_current` singleton at version 0. B1.1 validates that
bootstrap seed immediately after initialize, then validates later managed
databases with generic current-state shape rules rather than forcing permanent
version-0 clear state. The migration does not seed a writer, work items,
backlogs, lease identity records, authorization receipts, decision receipts,
transition events, global-stop events, active global stop, or executable
authorization.

## Non-Goals

B3a does not implement transition persistence, global-stop persistence,
idempotency lookup, expected-version checks, crash recovery orchestration,
production read ports, a `StateStore` mutation backend, worker execution,
scheduling, authorization, sandboxing, repair, local commit, publication, or
deployment. B3b2a does not change that persistence boundary; it adds private
query-spec and capability-protocol contracts. B3b2b adds private, unreachable
SELECT readers for tests only. B3b2b still does not add a production read port,
production fixture program, concrete transaction capability, context assembly, mutation,
or executable A2 behavior. B3c0b adds pure/static transition-event row,
replay, idempotency-match, and sequence/query-spec contracts only; it still
does not add a production read port, idempotency reader, event reader, sequence
reader, production fixture program, concrete transaction capability, writer fencing,
context assembly, evaluator integration, mutation, or executable A2 behavior.
B3c1a adds only private WriterSession authority plumbing, including the
resource-owned bound-database accessor and atomic mutation-slot publication
plus lease-construction unwind. B3c1b adds only private operation-lease-only
rollback-only writer fencing/capability mechanics and still does not add
reader integration, context assembly, evaluator integration, state mutation,
commit, public mutation behavior, or executable A2 behavior.
B3c3 adds only private rollback-only transaction integration, reader calls,
matcher calls from transaction code, clock runtime, context assembly runtime,
and evaluator integration. It still does not add sequence read, sequence
allocation, state mutation, commit, public mutation behavior, or executable A2
behavior.
B3c4a adds only private pure/static transition write specs, value builders,
planned-write and commit-resolution contracts, SQLite classification, retry,
proof, and public-boundary pins. It still does not add a production read port,
mutation execution, private atomic apply, public apply delegation, global-stop
persistence, executable A2 behavior, schema-ID bump, or migration 0002.
B3c4b adds private atomic transition apply through the existing controller:
maximum-sequence read, pure sequence allocation, frozen write-plan consumption,
transition-event insert, accepted-current CAS, capability invalidation before
commit, one commit attempt, commit uncertainty classification, and cleanup. It
still does not add a production read port, public global-stop persistence,
executable A2 behavior, schema-ID bump, or migration 0002.
B4b adds private atomic global-stop apply through the same neutral controller:
idempotency lookup, current-row read, persisted receipt verification, evaluator
invocation, table-local sequence allocation, global-stop event insert, accepted
singleton CAS, capability invalidation before commit, one commit attempt, commit
uncertainty classification, and cleanup. It still does not add receipt
provisioning, executable A2 behavior, schema-ID bump, or migration 0002.
B4c adds only public operation-guarded global-stop delegation to the B4b
private atomic entry. The public wrapper owns bounded local import,
private-to-public preflight mapping, and pre-delegate import/load failure
classification only; it adds no SQL, receipt verification, evaluator, sequence,
event insert, singleton CAS, rollback, COMMIT, or uncertainty ownership.
B3c4c adds only public operation-guarded transition delegation to the B3c4b
private atomic entry. The public wrapper owns bounded local import,
private-to-public preflight mapping, and pre-delegate import/load failure
classification only; it adds no SQL, transaction, sequence, event, CAS,
write-plan behavior, global-stop persistence, executable A2 behavior, schema-ID
bump, or migration 0002.

The tests-only coherent fixture graph initializes a temporary managed database,
directly seeds synthetic authoritative rows through a test transaction,
validates them through existing contracts, acquires real writer issuance as
temporary test evidence, and optionally persists a domain-rejected event/replay
row. It is not product state initialization, not admission, not authorization,
not a concrete capability, not fencing, not context assembly, not mutation, and
not a migration.

<!-- RW0_C1_CURRENT_STATUS_BEGIN -->
**Current catalog after RW0-C1.**

The current generation-2 terminal migration is
`0004_rw0_c1_durable_evidence`; the current production SQL resource count is
`4`. Migration 0002 remains an unchanged historical prefix. C2B2 did not
implement or acquire ownership of migration 0003 or migration 0004. C1 uses
the existing local database, common lock, internal writer issuance, operation
guard, nominal capability, and sole Coordinator transaction controller. It
adds no second backend, connection path, lock, writer, transaction authority,
or public API.
<!-- RW0_C1_CURRENT_STATUS_END -->

### Section 41 catalog succession

The current packaged generation-2 SQLite tip is additive `0005_section41_post_execution_proposal_family`, superseding only previous current-tip references to 0004; the current production SQL resource count is `5`. The new resource adds two immutable STRICT tables and four guards, with no explicit indexes or seeds, for cumulative 64/114/5 table/trigger/explicit-index counts. The four earlier migration bytes and owners are unchanged. An exact older 0004 database needs explicit administrative migration. The existing filesystem binding, writer authority, observational validation, transaction uncertainty and recovery architecture remain in force; Section 41 A uses the existing controller and C1 B remains a separate owner transaction.

### RW0-C2 physical catalog succession in the uncommitted workspace

The current packaged generation-2 workspace tip is
`0007_rw0_c2_progression_decision`; the current production SQL resource count
is `7`. Migration 0006 adds four private program-independent P0 admission
tables and eight immutable guards. Migration 0007 adds six private P1
progression supplemental tables and twelve immutable guards. The exact
cumulative schema has 74 user tables, 134 triggers, and five explicit indexes;
0001–0005 schema objects are unchanged. Exact older prefixes require explicit
administrative migration. The earlier 0005 current-tip statement records the
Section 41 predecessor, while P0/P1 remain an artificial-offline uncommitted
candidate under the existing filesystem, writer, and transaction boundaries.

<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_BEGIN -->
### RW0-C2 locally committed catalog status

The preceding uncommitted-workspace catalog paragraph records its candidate
checkpoint. Independently accepted tree `161ed4b544baf970cc26428b9805a106ea0f3edf` was locally committed as
`8704e6c7988250598809f3a0daf88c3e11493488`. The current packaged source catalog remains generation 2 through
0007 with seven resources, 74 tables, 134 triggers, and five explicit indexes;
0006 P0 and 0007 P1 stay distinct additive families. Existing filesystem,
writer, transaction, explicit migration, and recovery boundaries remain.
This local source status grants no live supplier, product permission, terminal
outcome, or publication.
<!-- RW0_C2_P0_P1_LOCAL_COMMIT_STATUS_SUCCESSOR_END -->
