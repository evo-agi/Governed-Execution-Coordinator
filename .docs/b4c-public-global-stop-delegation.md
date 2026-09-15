# B4c Public Global-Stop Delegation

Status: B4c implements guarded public global-stop delegation. The public
`_SQLiteWriterSession.apply_global_stop_update(global_stop_command,
typed_operator_decision)` method is functional as an adapter only.

## Adapter Boundary

The public method owns only session lifecycle precedence, one operation guard,
bounded function-local private loading, private-to-public preflight mapping,
and result/error propagation. The operation guard succeeds before any private
import, private preflight, mutation-slot acquisition, SQLite open, idempotency
lookup, receipt read, evaluator call, sequence inspection, write plan, rollback,
COMMIT, or uncertainty handling.

Inside the active operation guard the adapter imports exactly:

- `_GlobalStopApplyPreflightError`;
- `_GlobalStopApplyPreflightFailureReason`;
- `_run_atomic_global_stop_apply`.

Import or symbol-load failure before delegate invocation is classified as
`SQLiteMutationStoreError(mutation_failed)`. The delegate is not invoked on
that path, the mutation slot is not acquired, SQLite is not opened, and no
private module name, path, import text, command, decision, or hostile sentinel
is part of the public error payload.

The adapter delegates exactly once to `_run_atomic_global_stop_apply(...)` with
the exact operation lease, exact caller command object, and exact caller typed
decision object. It does not reconstruct, wrap, copy, serialize, digest, or
inspect those objects.

## Public Preflight Mapping

The adapter catches only `_GlobalStopApplyPreflightError` from the private
delegate. It exact-gates the caught private error type before trusting it, reads
`reason` only by direct trusted access, exact-gates the private reason enum, and
maps only:

| Private reason | Public reason |
| --- | --- |
| `_GlobalStopApplyPreflightFailureReason.INVALID_COMMAND` | `GlobalStopApplyPreflightFailureReason.INVALID_COMMAND` |
| `_GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION` | `GlobalStopApplyPreflightFailureReason.INVALID_OPERATOR_DECISION` |

Malformed, subclassed, inaccessible, unrelated, or unrecognized private
preflight objects or reasons are classified as
`SQLiteMutationStoreError(database_integrity_failure)`. Translated public
preflight and store errors are raised outside the caught private exception
context so no private cause, context, notes, traceback payload, command, or
decision data escapes.

## Delegate Ownership

There is no generic delegate catch-all. Delegate-owned committed outcomes,
conflicts, `WriterSessionError`, `SQLiteMutationStoreError`, ordinary
unexpected exceptions, and `commit_outcome_unknown` propagate by identity.
The adapter does not retry, inspect durable state, reinterpret commit
uncertainty, manufacture results, or downgrade private B4b classifications.

Private B4b remains the sole global-stop transaction entry and owns:

- mutation-slot acquisition and release;
- resource-bound SQLite open;
- writer fencing;
- idempotency lookup and replay;
- authoritative current-state reads;
- persisted operator-decision receipt verification;
- evaluator invocation;
- timestamp capture;
- table-local event sequence inspection and allocation;
- event INSERT;
- accepted singleton CAS;
- rollback;
- COMMIT;
- uncertainty and retry semantics.

## Receipt Authority

Persisted operator-decision receipts remain SELECT-only authority. The caller
decision remains comparison material only: the caller
`GlobalStopOperatorDecision` is never receipt authority or fallback authority.
B4c does not insert, provision,
upsert, update, delete, register, import, or manufacture receipts. Receipt
provisioning remains a separately governed reopened seam outside B4a, B4b, and
B4c.

Tests may seed receipt rows only as part of the historical schema-0001 B3/B4
graph hosted in a temporary current-generation-2, terminal-0003 fixture.
Accepted public-path tests prove tests-only receipt verification, public
delegation, and persistence mechanics; they do not prove production
operator-policy authorization or any C2B behavior. The fixture boundary is
owned by `.docs/b3-tests-only-coherent-fixtures.md`.

## Non-Claims

B4c does not change public transition delegation, `StateStore`, `WriterSession`
signatures, package exports, schema identifiers, migration `0001`, or migration
posture. Migration `0002` remains the physical C2B2 Slice-1 extension and
migration `0003` is the current terminal; B4c itself neither adds nor consumes
C2B runtime behavior.

B4c adds no receipt-provisioning integration, CLI, MCP, connector, worker,
service, scheduler, report, admission, authorization verifier, orchestration,
repair, local commit behavior, publication, deployment behavior, or
related-repository caller.

B4c completes the Coordinator durable transition/global-stop apply surface:
B3c4c public transition delegation exists, B4b private global-stop persistence
exists, and B4c guarded public global-stop delegation exists. The Coordinator
durable-state program can freeze pending final audit and snapshot. No worker,
service, scheduler, admission, orchestration, publication, or cross-repository
authority exists.
