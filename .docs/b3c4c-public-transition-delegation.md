# B3c4c Public Transition Delegation

Status: implemented public transition delegation only. Public global-stop
persistence remains unavailable.

B3c4c makes `_SQLiteWriterSession.apply_transition(command)` functional through
the existing WriterSession operation guard and the existing private B3c4b atomic
transition entry. It does not add a second atomic entry, second transaction
controller, second capability constructor, public `StateStore` mutation method,
schema-ID bump, migration 0002, production admission, authorization verifier,
worker, scheduler, service, CLI, MCP, connector, publication, or related-repo
authority.

## Delegation Shape

The public method:

1. acquires `self._resource.operation_guard(self)` exactly once;
2. keeps the returned operation lease active across local import, private
   preflight, private mutation, cleanup, and result or error propagation;
3. performs one bounded function-local import of
   `_run_atomic_transition_apply`, `_TransitionDryRunPreflightError`, and
   `_TransitionDryRunPreflightFailureReason`;
4. calls `_run_atomic_transition_apply(...)` exactly once with only
   `operation_lease=operation_lease` and
   `transition_command=transition_command`;
5. returns the delegate result directly unless exact private preflight mapping is
   required.

The function-local import avoids the private circular-import seam between
`sqlite_writer_session.py` and `sqlite_transition_transaction.py`. The import is
inside the active operation guard, but before delegate invocation.

## Error Boundary

Session-local failures retain precedence. Closed sessions, fork/process
mismatch, inactive authority locks, closing sessions, lifecycle failures, and
mutation-slot contention remain `WriterSessionError` outcomes from the existing
session resource.

An import or symbol-load failure before delegate invocation is a definite
pre-delegate failure and is exposed only as:

```text
SQLiteMutationStoreError(mutation_failed)
```

The wrapper catches no broad delegate-execution exception. After delegate
invocation begins, B3c4b remains the sole owner of transaction-state-aware error
classification, including `database_integrity_failure`,
`event_sequence_exhausted`, `mutation_failed`, and `commit_outcome_unknown`.
Commit uncertainty passes through unchanged.

Private preflight errors map exactly:

| Private reason | Public reason |
| --- | --- |
| `transition_dry_run_invalid_command` | `TransitionApplyPreflightFailureReason.INVALID_COMMAND` |
| `transition_dry_run_unsupported_command` | `TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND` |

Malformed, missing, inaccessible, subclassed, forged, or unrecognized private
preflight errors or reasons are internal private-contract integrity
contradictions. They are classified exactly as:

```text
SQLiteMutationStoreError(database_integrity_failure)
```

The wrapper exact-gates the caught private error before reading its reason,
extracts the reason through trusted direct access that safely handles ordinary
missing or inaccessible-attribute failures, exact-gates the extracted private
reason before mapping enum members, and raises the final public or store error
only after leaving the active private preflight handler and any extraction
failure handler. These malformed cases do not create a third public preflight
reason, must not become a third public preflight reason, must not fall back to
`TransitionApplyPreflightFailureReason.INVALID_COMMAND` or
`TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND`, and do not leak
private or hostile values. The resulting store error has no cause, context,
notes, or internal detail.

This private-contract integrity classification is distinct from import/load
failure or symbol-load failure before delegate invocation, which remains
`SQLiteMutationStoreError(mutation_failed)`. The wrapper still catches no broad
delegate-execution exception, and commit uncertainty remains owned by the
private atomic delegate.

## Public Outcomes

The public transition result/error matrix is now:

| Case | Public result or error |
| --- | --- |
| fresh accepted transition | `CommittedTransition(replayed=False)` |
| fresh domain rejection | `CommittedTransition(replayed=False)` |
| exact replay | `CommittedTransition(replayed=True)` |
| stale writer | `TransitionConflict` |
| idempotency-key reuse conflict | `TransitionConflict` |
| work item not found | `TransitionConflict` |
| expected-version conflict | `TransitionConflict` |
| fenced validation conflict | `TransitionConflict` |
| invalid local command | `TransitionApplyPreflightError` |
| unsupported local command | `TransitionApplyPreflightError` |
| malformed private preflight object or reason | `SQLiteMutationStoreError(database_integrity_failure)` |
| session lifecycle or slot failure | `WriterSessionError` |
| store, sequence, or commit failure | `SQLiteMutationStoreError` |

`TransitionApplyOutcome` remains `CommittedTransition | TransitionConflict`.
Private events, replay envelopes, contexts, plans, sequence values,
capabilities, controllers, connections, rows, command digests, filesystem paths,
credentials, proofs, and private sentinels are not public payloads.

## Static Boundary

`_SQLiteWriterSession.apply_transition()` contains no SQL, SQLite connection or
cursor handling, `BEGIN`, `COMMIT`, `ROLLBACK`, event insertion, work-item CAS,
sequence read/allocation, `TransitionContext` construction, evaluator call,
capability construction, mutation-lease acquisition, state-root input, mutable
delegate registry, callback injection, package-root indirection, or generic
delegate catch-all.

`_SQLiteWriterSession.apply_global_stop_update()` now enters the operation
guard and, after B4c, delegates once to the B4b private global-stop persistence
entry through its own bounded function-local import and preflight mapping
boundary. Public transition delegation remains unchanged.
