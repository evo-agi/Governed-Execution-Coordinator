# B3c3 Prerequisite Contract

Status: contract-only / pure-static prerequisite; no B3c3 transaction
implementation; no public caller; no mutation.

B3c3 pins the private rollback-only transition dry-run boundary that a later
runtime tranche may execute inside the existing B3c1b controller lifecycle. This
tranche adds only documentation, private pure result/preflight/binding
contracts, and tests. It does not modify the live B3c1b controller, acquire a
mutation slot, open SQLite, execute `BEGIN IMMEDIATE`, call B3b2 or B3c2
readers, call the idempotency matcher from transaction code, capture the real
clock, derive lease runtime, construct `TransitionContext`, invoke
`evaluate_transition`, read maximum sequence, allocate sequence, insert or
update durable state, commit, change public `WriterSession` methods, widen
`StateStore`, export package-root symbols, or add migration 0002.

## Controller Ownership

B3c3 preserves one controller class and one capability-construction path. The
single private controller remains `_RollbackOnlyTransitionTransactionController`
in `src/ge_nwp_coordinator/sqlite_transition_transaction.py`; the single
nominal read capability remains constructed only by that controller's existing
private helper and construction key.

The unchanged fencing-only entry point remains:

```python
_run_rollback_only_writer_fencing(
    *,
    operation_lease: _WriterSessionOperationLease,
) -> _WriterIssuanceMatch
```

The future B3c3 dry-run entry point is pinned as:

```python
_run_rollback_only_transition_dry_run(
    *,
    operation_lease: _WriterSessionOperationLease,
    transition_command: TransitionCommand,
) -> _RollbackOnlyTransitionDryRunResult
```

The future dry-run entry point is not implemented in this tranche. When it is
implemented, it must extend the same private controller lifecycle rather than
introducing a second transaction controller, second nominal capability
constructor, callback, observer, raw `sqlite3.Connection` parameter, generic
callable hook, generic mode, caller-supplied `TransitionContext`,
caller-supplied `LeaseRuntimeDecision`, or caller-supplied timestamp.
In short: no callback, observer, raw connection, second controller, second
capability, or generic mode.

## Command Preflight

Future B3c3 performs command-local checks before mutation-slot acquisition.
The order is:

1. operation lease acquisition;
2. exact `TransitionCommand` type and canonical command digest validation;
3. bounded-slice local checks;
4. mutation-slot acquisition;
5. bound managed database open.

The private pure helper is:

```python
_validate_transition_dry_run_preflight(
    command: TransitionCommand,
) -> TransitionCommand
```

It accepts only the exact `TransitionCommand` type, requires digest
recomputation to succeed and equal `canonical_command_digest`, requires every
non-READY command to have `dependency_decision_ref is None`, and requires
`budget_cost == 0` for the bounded persisted slice. Invalid type or digest is
`transition_dry_run_invalid_command`. Unsupported non-READY dependency refs or
nonzero budget cost are `transition_dry_run_unsupported_command`.
The private preflight error constructor accepts only the exact private reason
enum. Arbitrary strings or hostile objects are rejected with one constant safe
constructor error; rejected values are not normalized through enum conversion,
rendered, chained, or retained.

Local invalid input contacts no SQLite, creates no transaction timestamp,
invokes no reader, invokes no evaluator, returns no event, constructs no
`TransitionConflict`, raises no `SQLiteMutationStoreError`, and raises no
`WriterSessionError`.

## Dry-Run Ordering

After preflight, future B3c3 uses the B3c1b controller lifecycle:

1. acquire the mutation slot;
2. open the resource-owned managed read/write connection;
3. execute `BEGIN IMMEDIATE`;
4. revalidate the retained binding and managed posture;
5. read and verify writer fencing;
6. create the nominal read capability only for a matching writer;
7. call `_read_transition_event_for_idempotency(...)`;
8. call `match_transition_event_idempotency(existing, command)` exactly once;
9. on miss, read current work item;
10. compare expected version;
11. read context rows in the pinned order;
12. bind authoritative rows;
13. capture one transaction timestamp;
14. derive lease runtime;
15. construct `TransitionContext`;
16. call `evaluate_transition(current_record, command, context)` exactly once;
17. invalidate capability;
18. roll back;
19. close;
20. release the mutation lease;
21. return a private dry-run result only after cleanup succeeds.

Stale writer precedes idempotency disclosure; stale writer before idempotency
disclosure is a hard ordering boundary. Future B3c3 is the first private
owner that converts `_WriterIssuanceMatch.STALE_WRITER` into
`_RollbackOnlyTransitionDryRunResult(kind=APPLY_CONFLICT,
conflict=TransitionConflict("stale_writer_token"))`. That conversion result is
returned only after rollback and close succeed, and no idempotency reader is
called for a stale writer.

Exact replay and idempotency-key reuse conflict both skip B3b2 context readers,
current-state reading, timestamp capture, lease-runtime derivation,
`TransitionContext` construction, evaluator invocation, maximum-sequence read,
sequence allocation, event insertion, state update, CAS, and commit. Exact
replay may carry only the existing already-committed
`CommittedTransition(replayed=True)`. Key reuse conflict may carry only
`TransitionConflict("idempotency_key_reuse_conflict")`.

## Current And Context Reads

After idempotency miss, future B3c3 reads the current work item before any
context row. Zero current rows are `TransitionConflict("work_item_not_found")`.
Exactly one valid row continues. Expected-version mismatch is
`TransitionConflict("expected_version_conflict")`. No timestamp or evaluator
call occurs for work-item absence or expected-version mismatch.

Only after expected-version match may B3c3 read context rows. The exact context
reader order is:

1. lease identity;
2. admitted backlog;
3. authorization receipt;
4. dependency receipt only when the target is READY;
5. global-stop singleton.

Missing lease identity, authorization receipt, or READY dependency receipt is
`TransitionConflict("validation_failed")`. Missing admitted backlog after the
current work item references it is `database_integrity_failure`. Missing
`global_stop_current` singleton is `database_integrity_failure`.

For non-READY targets, command preflight has already required
`dependency_decision_ref is None`; the dependency reader is not called; the
assembler uses exactly neutral `DependencyDecision()` as evaluator shape; no
synthetic persisted dependency receipt is invented.

## Cross-Record Binding

The pure binding helper is:

```python
_bind_b3c3_transition_authority(
    *,
    command: TransitionCommand,
    current_record: WorkItemRecord,
    standing_lease: StandingLease,
    admitted_backlog: FiniteBacklog,
    lease_identity: LeaseIdentityValidation,
    authorization: AuthorizationDecision,
    dependency: DependencyDecision,
    global_stop: GlobalStopState,
) -> _BoundTransitionAuthority | TransitionConflict
```

It performs no SQLite I/O, accepts no row envelopes, retains no operational
timestamps, retains no canonical JSON, constructs no `TransitionContext`,
derives no lease runtime, invokes no evaluator, returns no event, and returns
no dry-run result. It returns `_BoundTransitionAuthority` only with exact model
types for current record, standing lease, lease identity, authorization,
dependency, and global stop.

B3c3 reuses `validate_b3_work_item_authority_binding(...)`,
`classify_authorization_model_for_b3(...)`, existing lease-identity
reconstruction semantics, exact command/ref checks, and existing model
constructors. It validates lease/backlog/current binding, exact backlog digest,
exact single current work item in canonical backlog, backlog size within lease
maximum, exact attempt/repair limit copies, counters within limits, zero scalar
current-state budget fields, and static multidimensional budget policy.
Exact type alone is not authority for this private boundary. The binding helper
first exact-gates and then reconstructs command and persisted model inputs
through model-owned pure validation before retaining or comparing them. Forged
exact shells, missing fields, hostile nested values, and malformed private
payloads collapse to `SQLiteMutationStoreError(database_integrity_failure)`
without raw `AttributeError`, raw `ValueError`, field values, causes, contexts,
or notes.

Candidate validation and serialization methods are never dispatched through the
candidate instance. The private B3c3 reconstructors exact-gate required fields
and nested models first, read known dataclass fields directly, and then invoke
trusted class-owned constructors or class-owned serialization on already-safe
replacement models only. Instance-level method shadowing, including a forged
`to_dict` that returns synthetic canonical data, cannot substitute clean data
for malformed real fields and cannot override valid real fields with conflicting
shadow output. Retained models are reconstructed from validated real fields
only; malformed result or authority payloads remain
`database_integrity_failure`. This hardening still adds no runtime authority.

Candidate instance dictionaries are untrusted containers. For exact
dictionary-backed models, B3c3 snapshots the raw instance dictionary only by
enumerating built-in `dict.items(...)`; it performs no lookup, membership,
hashing, comparison, sorting, formatting, rendering, or mapping conversion with
raw candidate keys first. Every raw key must be an exact built-in `str` before a
trusted local state mapping is constructed. Required-field lookup then occurs
only against that newly created exact-string-keyed mapping. Non-string keys and
`str` subclasses fail closed as `database_integrity_failure` without exposing
the key or payload. Extra exact-string attributes, including shadowed
serialization or digest method names, are ignored and cannot become validation,
serialization, canonicalization, digest, or retention authority. This dictionary
snapshot rule is pure prerequisite hardening only and implements no B3c3
runtime authority.

Lease identity binding requires the exact command decision ref, the persisted
decision ref, lease ref, identity validity, digest, and issue tuple to agree
with `StandingLease.validate_identity()`. A coherent invalid lease identity is
valid evaluator input and is not automatically a pre-evaluator conflict.

Authorization binding requires the exact command authorization decision ref,
authorization lease ref equal to the current and standing lease, authorization
lease-identity ref and validity equal to the lease-identity receipt, and a
persisted decision coherent under the existing model constructor.
`authorization_model=unsupported` remains a valid fail-closed evaluator input.
`authorization_model=operator_policy` is not trusted by B3c3 and becomes
`TransitionConflict("validation_failed")`.

READY dependency binding requires the command dependency decision ref to equal
the persisted decision ref and the dependency work-item binding to equal the
current work item. A false READY dependency remains evaluator-domain input.
Non-READY targets require null command dependency ref and exact neutral
`DependencyDecision()`.

Global-stop binding requires the command global-stop ref and version to equal
the authoritative singleton. Mismatch is
`TransitionConflict("validation_failed")`.

Command/reference mismatch against otherwise valid authoritative models is
`TransitionConflict("validation_failed")`. Contradiction among authoritative
persisted models is `SQLiteMutationStoreError(database_integrity_failure)`.
Persisted-model coherence is checked before command-address mismatch, so a
simultaneous persisted contradiction and command mismatch is an integrity
failure, not a validation conflict.

## Timestamp, Runtime, And Evaluator

Future B3c3 owns exactly this private timestamp source in
`src/ge_nwp_coordinator/sqlite_transition_transaction.py`:

```python
_utc_transaction_timestamp() -> str
```

This function is not implemented in the prerequisite tranche. When implemented,
it has zero arguments, is module-private, returns exact whole-second UTC
`YYYY-MM-DDTHH:MM:SSZ`, and may be monkeypatched by tests only at that bounded
module-private seam. It is called exactly once only after all rows are loaded
and cross-record binding succeeds, before lease-runtime derivation,
`TransitionContext` construction, and evaluator invocation. It is not called
for stale writer, exact replay, idempotency conflict, work-item not found,
expected-version conflict, validation conflict, or integrity failure before
binding. It uses `normalize_transaction_timestamp(...)` and
`require_utc_timestamp(...)` rather than duplicating timestamp grammar. Clock
failure is `SQLiteMutationStoreError(mutation_failed)`, calls no evaluator,
fabricates no event/result, retains no raw clock exception, and still requires
rollback and close.

After timestamp capture, future B3c3 derives exactly one
`derive_lease_runtime_decision(standing_lease, timestamp)`, constructs exactly
one `TransitionContext` from the persisted lease identity, persisted
authorization decision, derived lease runtime, authoritative global stop, and
persisted READY dependency or exact neutral non-READY default, then invokes
`evaluate_transition(current_record, command, context)` exactly once.

No external I/O may occur while the transaction is active. No reader, clock,
authorization provider, report, worker, Bridge, network, filesystem,
subprocess, related repo, or callback call may occur after evaluator begins.
`PRE_APPLY_INVALID` after successful B3c3 binding is
`database_integrity_failure`.

## Private Result Algebra

The dry-run result is one private frozen slots-only repr-safe wrapper:

```python
_RollbackOnlyTransitionDryRunResult
```

Its closed kind enum is:

- `EXACT_REPLAY = "exact_replay"`;
- `APPLY_CONFLICT = "apply_conflict"`;
- `ACCEPTED_EVALUATION_NOT_PERSISTED =
  "accepted_evaluation_not_persisted"`;
- `DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED =
  "domain_rejected_evaluation_not_persisted"`.

The only payload fields are:

- `replayed_transition: CommittedTransition | None`;
- `conflict: TransitionConflict | None`;
- `evaluation: TransitionEvaluation | None`.

Exactly one matching payload is required. `EXACT_REPLAY` requires exact
`CommittedTransition`, `replayed is True`, and exact nested `WorkItemRecord`
and `TransitionEvent`. `APPLY_CONFLICT` requires exact `TransitionConflict`
with one of `stale_writer_token`, `idempotency_key_reuse_conflict`,
`work_item_not_found`, `expected_version_conflict`, or `validation_failed`.
`ACCEPTED_EVALUATION_NOT_PERSISTED` requires exact `TransitionEvaluation`, kind
`ACCEPTED`, and exact non-null `TransitionEvent`.
`DOMAIN_REJECTED_EVALUATION_NOT_PERSISTED` requires exact
`TransitionEvaluation`, kind `DOMAIN_REJECTED`, and exact non-null
`TransitionEvent`.
Result payloads are reconstructed through model-owned pure validation before the
wrapper retains them, using trusted class-owned reconstruction rather than
candidate instance method dispatch. The wrapper never retains forged exact
shells, instance-shadowed serializer output, or hostile nested model values.
Malformed result payloads, including forged
`CommittedTransition`, `TransitionConflict`, `TransitionEvaluation`,
`WorkItemRecord`, `TransitionEvent`, or `PRE_APPLY_INVALID` evaluator output,
are `database_integrity_failure` with no raw payload leakage.

Fresh evaluator output is non-durable; fresh evaluator output is non-durable
and non-receipt in B3c3. A newly evaluated accepted or
domain-rejected event must never be represented as `CommittedTransition`, must
never be called committed, and is not a receipt until future B3c4 inserts and
commits it. `PRE_APPLY_INVALID` is not a dry-run result and becomes
`database_integrity_failure`.

The wrapper has no serializer, canonical mapping, digest, report method,
package-root export, public API, or durable receipt claim. Result reprs and
errors expose no private material.

No result retains a capability, connection, controller, operation lease,
mutation lease, epoch, credential, proof, filesystem binding, raw row,
`TransitionContext`, canonical JSON, digest, path, or evaluator internals.

## Cleanup And Persistence Boundary

B3c3 remains rollback-only. For replay, conflict, accepted evaluation,
domain-rejected evaluation, and definite safe errors, cleanup order is:

1. invalidate capability;
2. roll back;
3. close connection;
4. release mutation lease;
5. return or raise only after cleanup.

A result may be constructed internally before cleanup but is never returned
before cleanup. Rollback failure supersedes replay, conflict, or evaluation
with `SQLiteMutationStoreError(mutation_failed)` and no result. Close failure
after rollback also supersedes replay, conflict, or evaluation with
`SQLiteMutationStoreError(mutation_failed)` and no result. The mutation lease is
released after the close attempt. B3c3 never returns
`commit_outcome_unknown`.

No sequence read or allocation occurs in B3c3. No writes, CAS, or COMMIT occur
in B3c3. B3c4 remains the first persistence/commit tranche and owns observed
maximum-sequence use, allocator call, event insertion, current-state CAS,
rollback-or-commit resolution, commit uncertainty, and durable receipts.

## Production Boundary

B3c3 prerequisite contracts are private and production-unintegrated. Public
transition and global-stop mutation methods continue to return
`writer_session_mutation_unavailable` and contact no SQLite database. B3c3 adds
no `StateStore` method, package-root export, CLI, MCP, connector, report,
service, worker, scheduler, production admission, production authorization
provider, related-repo consumer, schema-ID bump, migration edit, or migration
0002.
