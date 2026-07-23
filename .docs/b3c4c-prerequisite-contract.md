# B3c4c Public Preflight And Delegation Prerequisite Contract

Status: implemented public exception vocabulary and delegation contract.
B3c4c public transition delegation is now implemented in
`.docs/b3c4c-public-transition-delegation.md`.

This tranche exists because the private B3c4b atomic transition entry can raise
the private B3c3 command-local preflight error before mutation-slot acquisition
or database access. Public `_SQLiteWriterSession.apply_transition()` must not
leak that private type, private reason enum, traceback, or module path.

The public prerequisite adds exactly two package-root exports:

- `TransitionApplyPreflightFailureReason`;
- `TransitionApplyPreflightError`.

It does not change `TransitionApplyOutcome`, does not widen `StateStore`, does
not change `WriterSession` method signatures, does not add SQL or transaction
runtime to the public wrapper, and does not implement public global-stop
persistence.

## Public Vocabulary

`TransitionApplyPreflightFailureReason` is a closed public enum with exactly:

- `INVALID_COMMAND = "transition_apply_invalid_command"`;
- `UNSUPPORTED_COMMAND = "transition_apply_unsupported_command"`.

`TransitionApplyPreflightError` is a safe command-local `RuntimeError`.

The constructor accepts only the exact
`TransitionApplyPreflightFailureReason` type. It must not normalize arbitrary
strings through enum conversion. Invalid constructor input raises exactly:

```text
invalid_field_type:transition_apply_preflight.reason
```

The error retains only the checked enum in `.reason`. `str(error)` and
`error.args` expose only the public reason value. `repr(error)` is exactly:

```text
<TransitionApplyPreflightError>
```

The error has no serializer, no report method, no canonicalization method, no
digest method, no internal-detail property, and no command payload. Normal
construction adds no cause, context, or notes.

This error is command-local and pre-apply. It is not `TransitionConflict`,
`WriterSessionError`, `SQLiteMutationStoreError`, a domain-rejected transition,
a durable event, or a receipt.

## Private-To-Public Mapping

The B3c4c public implementation maps private B3c3 preflight reasons
exactly:

| Private reason | Public reason |
| --- | --- |
| `transition_dry_run_invalid_command` | `TransitionApplyPreflightFailureReason.INVALID_COMMAND` |
| `transition_dry_run_unsupported_command` | `TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND` |

The public method must catch only the exact private preflight error type
for this mapping, exact-gate the private reason, construct the public error from
one of the two exact public enum constants, and raise the public error outside
the active `except` block so no private `__context__` survives.

Any malformed, forged, subclassed, missing, inaccessible, or unrecognized
private preflight error or reason is an internal private-contract integrity
contradiction. Its exact public classification is:

```text
SQLiteMutationStoreError(database_integrity_failure)
```

It must not become a third public preflight reason, must not fall back to
`TransitionApplyPreflightFailureReason.INVALID_COMMAND` or
`TransitionApplyPreflightFailureReason.UNSUPPORTED_COMMAND`, and must not leak
the private error, private reason, inaccessible attribute failure, module path,
or any hostile value. The store error is raised outside every active private
preflight handler and outside any extraction-failure handler, with no cause,
context, notes, or internal detail.

Invalid and unsupported commands occur only after the operation guard succeeds
and before mutation-slot acquisition or database access. They create no
`TransitionConflict`, event, sequence, write, rollback, or COMMIT. They do not
participate in idempotency or retry semantics.

The malformed-private-preflight classification is distinct from import/load
failure before delegate invocation, which remains
`SQLiteMutationStoreError(mutation_failed)`; from valid public preflight errors,
which remain `TransitionApplyPreflightError`; and from delegate-owned
`commit_outcome_unknown`, which passes through unchanged.

`validation_failed` remains reserved for locally valid typed command/context
values whose authoritative persisted bindings fail inside the fenced apply
boundary. It is not the public mapping for command-local preflight failure.

## Delegation And Import Shape

The B3c4c public method shape is:

1. acquire the existing WriterSession operation guard;
2. inside that active guard, perform one bounded function-local import of:
   `_run_atomic_transition_apply` and the exact private preflight error and
   reason types needed for mapping;
3. call the delegate exactly once with the exact operation lease and the exact
   caller command.

The operation guard remains open for the entire delegate call. The returned
operation lease is passed by identity. The caller command is passed by identity
unless an existing private preflight contract returns a checked replacement.
WriterSession itself does not acquire the mutation lease.

Rejected shapes:

- top-level reverse import;
- import-time registration;
- mutable delegate registry;
- injection callback;
- package-root indirection;
- second controller;
- second atomic wrapper;
- second capability path.

Import or delegate-load failure before delegate invocation is classified as:

```text
SQLiteMutationStoreError(mutation_failed)
```

No delegate or COMMIT has begun on that path, so non-commit is definite. The
implementation must sanitize this failure outside the caught exception
context and expose no module path, traceback, private sentinel, SQL, parameter,
digest, command value, path, credential, proof, or endpoint.

## No Generic Delegate Catch-All

The private atomic delegate remains the sole owner of transaction-state-aware
exception classification.

The public wrapper transparently propagates:

- `CommittedTransition`;
- `TransitionConflict`;
- `TransitionApplyPreflightError`;
- `WriterSessionError`;
- `SQLiteMutationStoreError`.

`commit_outcome_unknown` passes through unchanged.

The public wrapper must not wrap delegate execution in a broad
`except Exception -> mutation_failed` block. After delegate invocation begins,
the wrapper cannot know whether COMMIT was attempted or succeeded. Any
unexpected non-contract exception escaping the private atomic delegate is
contract drift requiring implementation or audit failure, not an opportunity
for the public wrapper to invent definite non-commit semantics.

This prohibition does not prevent the narrowly bounded import/load failure
mapping before delegate invocation.

## Session-Local Precedence

Public precedence is:

1. WriterSession operation guard:
   closed session, process mismatch or fork-invalid session, inactive authority,
   closing session, and lifecycle failure;
2. local import/load;
3. private command preflight and public preflight mapping;
4. mutation-slot acquisition and private atomic processing.

Therefore a closed or process-mismatched session with a malformed command
returns the existing `WriterSessionError`. An active session with a malformed
command returns `TransitionApplyPreflightError`. Concurrent active public
mutations use the existing `writer_session_mutation_in_progress` reason. No
command preflight or delegate import occurs if operation-guard acquisition
fails.

## Public Result And Error Matrix

Public outcomes are exactly:

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

No private result, evaluation, context, plan, sequence, capability, controller,
connection, row, writer metadata, command value, canonical digest, proof, or
path may escape.

## Current Runtime Boundary

After B3c4c, `_SQLiteWriterSession.apply_transition()` now enters the existing
operation guard, uses bounded function-local private imports, delegates exactly
once to `_run_atomic_transition_apply`, and maps only the two exact private
preflight reasons to public `TransitionApplyPreflightError`.
`_SQLiteWriterSession.apply_global_stop_update()` still enters the existing
operation guard and raises `writer_session_mutation_unavailable`.

`sqlite_writer_session.py` contains no SQL or transaction grammar and does not
acquire the mutation lease. The private mutation transaction module remains the
sole atomic transaction owner. B4b adds only a private global-stop persistence
entry; B4c remains future for public global-stop delegation.

This tranche proves no production admission, authorization, worker,
orchestration, publication, related-repository authority, executable A2
behavior, schema-ID bump, or migration 0002.
