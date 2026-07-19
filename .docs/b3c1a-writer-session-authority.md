# B3c1a Writer Session Authority

Status: implemented private WriterSession authority plumbing; no SQLite
transaction/controller/capability/fencing query.

B3c1a implements only the in-memory authority plumbing needed before the future
B3c1b rollback-only transaction controller. It does not make public
transition or global-stop mutation methods operational.
This document is the B3c1a companion to
`.docs/b3c1-prerequisite-contract.md`.

## Slot Owner

`_WriterSessionResource` owns exactly one mutation slot shared by future
transition mutation and future global-stop mutation. The slot is distinct from
`_active_operations` and is acquired only through an active
`_WriterSessionOperationLease`.

The same resource also retains a private state-database filesystem-authority
binding captured for the exact `CoordinatorStateLocation` used to acquire the
common `StateAuthorityLock` and durable writer issuance. The binding contains
the state-root identity, authority-lock-file identity, and active
database-file identity, all hidden from reprs and public errors. The active
database file must have exactly one hard link. B3c1b may open SQLite only
through that retained binding. The operation lease exposes only a private
mutation-authority accessor for the retained binding; callers cannot supply a
different root, database path, alias, lock, descriptor, inode, device, or link
count.

The slot record is private, constant-repr, and retains only:

- operation identity;
- owner process identity;
- owner thread identity;
- resource lifecycle epoch;
- one opaque release token.

It retains no credential, raw proof, proof digest, lock, descriptor, session
metadata, connection, path, endpoint, or public authority object.

## Mutation Lease

`_WriterSessionMutationLease` is the private release handle for the slot. It is
a slots-only context manager with a constant safe repr and no public close
surface. Its private `_close()` is idempotent for the owner thread.

The lease retains the operation lease strongly until owner-thread release. That
retention keeps the B2 operation guard alive while a mutation slot is held. A
wrong-process or wrong-thread close attempt is a no-op against the resource
slot and does not expose identity details.

There is no mutation-lease finalizer. Explicit mutation-lease close is the
primary cleanup path. If a mutation lease is abandoned, operation-finish
cleanup is the fallback.

Publishing the resource mutation slot and constructing
`_WriterSessionMutationLease` are externally atomic. If construction fails
after the slot is published, the resource synchronously releases the exact
just-published slot before re-raising. That unwind uses the owning operation,
lifecycle epoch, owner process, owner thread, and opaque token, so it cannot
clear a newer or unrelated slot.

## Cleanup Rules

Exact resource-side release clears the slot only when operation identity,
lifecycle epoch, owner process, owner thread, and opaque token all match the
current slot. Duplicate, stale, wrong-operation, wrong-thread, and fork-child
releases cannot clear a newer or current slot.

`_WriterSessionResource._finish_operation()` defensively clears a slot owned by
the operation being finished before operation removal and cleanup convergence.
This covers abandoned mutation leases, operation-lease finalizer fallback, and
explicit operation close before mutation-lease close.

Owner cleanup claim, foreign-process cleanup, at-fork child invalidation, and
final resource cleanup all clear the slot. No slot survives a closed or
fork-invalid resource. Foreign-process cleanup also removes the exact inactive
resource from the current process-local active-session registry; the registry
remains non-authoritative and is not a source of writer liveness.

## Process And Thread

Mutation-slot acquisition requires the current owner process, the operation
owner thread, matching lifecycle epoch, `ACTIVE` resource state, credential and
authority-lock presence, active operation registration, exact retained
credential identity, exact retained authority-lock identity, and an empty slot.

Contention fails promptly with
`writer_session_mutation_in_progress` before SQLite. It does not block, open a
connection, create an apply conflict, or emit an event.

Active-mutation-authority validation requires the operation lease to be open,
same-process, same-thread, registered, lifecycle-current, bound to the
resource-owned credential and authority lock, backed by an owned current slot,
protected by an active retained authority lock, and still matched to the
retained root/lock/database filesystem binding. Wrong-thread private calls
fail closed with existing `writer_session_closed`; no new public
`WriterSession` reason is added.

The private resource-owned bound-database accessor calls
active-mutation-authority validation first and then returns the exact retained
private binding. The binding is:

```text
controller database open binding
==
WriterSession resource-owned state-database binding
==
same CoordinatorStateLocation, state-root identity, authority-lock-file
identity, and single-link database-file identity captured while the retained
common authority lock was held
```

A cloned or independently initialized database with a matching
`writer_ownership` row is not authority for the session. Replacing the visible
root, replacing the visible lock file, replacing the visible database file, or
creating a hard-link alias to the active database fails closed without exposing
which identity changed. Removing the alias permits normal operation to resume
only if every retained invariant is again true; the session does not silently
close or reacquire authority.

Fork-child copied leases and release handles fail closed or no-op without
clearing parent authority. B3c1a does not claim arbitrary multithreaded-fork
safety beyond the existing B2 process/fork rules.

## Issuance Verification

`_verify_durable_writer_issuance(...)` accepts only the exact private
`_DurableWriterIssuance` type from `sqlite_writer_state.py`. It validates the
object through the existing writer-row grammar before comparison. Malformed
input raises only a safe private `ValueError("invalid writer input")`.

`_WriterIssuanceMatch` is the only private verification result:

- `MATCH`;
- `STALE_WRITER`.

Credential identity consists of writer ref, generation, issued ref, and the
private proof verified against the persisted proof digest. `acquired_at` is
validated persisted metadata but is not credential identity.

Every well-formed identity or proof mismatch returns only
`_WriterIssuanceMatch.STALE_WRITER`. The caller cannot distinguish writer-ref,
generation, issued-ref, or proof mismatch. The raw proof is never read out,
returned, serialized, logged, or exposed.

## Public Boundary

`_SQLiteWriterSession.apply_transition()` and
`_SQLiteWriterSession.apply_global_stop_update()` continue to enter only the
generic operation guard and raise `writer_session_mutation_unavailable`. They
do not acquire the mutation slot, open SQLite, execute SQL, perform writer
fencing, call B3b2 readers, reconstruct context, invoke evaluators, insert
events, update work items, or update global-stop state.

B3c1b implements the private rollback-only transaction controller, writer-row
query, writer fencing, and nominal transaction capability without production
integration or durable mutation. B3c2-B3c4 remain future for
idempotency/event/sequence readers, context/evaluator integration, and durable
mutation.
