# RW0-D1 offline process and capsule spine

Classification: `CURRENT IMPLEMENTED CONTRACT` for the private artificial
offline proof only. This status follows the source implementation. It is not a
standing grant, executable permission, live worker route, or acceptance fact.

The private `run_rw0_d1_offline(...)` entry consumes one exact accepted
`WorkSpecV1` and a closed three-file artificial fixture for
`repository.execution-substrate`. It creates a disposable Coordinator database
through migration 0004, invokes the guarded program-initialization and C2B3D
author-effect writers, closes the writer, runs one separate deterministic fake
planner, constructs the current Section 41 bundle from its bounded content,
and records selection through the guarded Section 41 writer. Only a committed
`selected_for_dispatch_gates` result permits C1 phase establishment. The C1
writer commits before the worker starts. Each writer and its state-authority
lock is closed before a child launch. Uncertain commits use the existing exact
recovery entry under a fresh writer; unresolved recovery stops progression.

The private D1 supervisor is the sole production `subprocess` owner. It uses
an absolute interpreter with `-B -m` for two package-private fake executables,
an allowlisted child environment, separate session/process group, closed
inherited descriptors, bounded stdin/stdout/stderr, a monotonic deadline,
cancellation polling, TERM then bounded KILL, direct-child reap, and final
group-clear observation. Process launch, PID, signals, exit, timeout, and
cleanup are parent facts, never durable progression or semantic acceptance.
The children receive no Coordinator database path, writer session, proof,
state-root custody, standing-policy credential, or parent process state.
These deterministic children are proof machinery, not a same-UID security
sandbox.

The planner D1O1 request/response and worker D1W1 launch are private closed
canonical frames with length checks before allocation. The worker launch
embeds the existing NWPF command frame and actual fences. Worker stdout is
exactly one existing NWPF result frame. The worker edits at most one of the
three authorized regular `100644` files in an isolated temporary workspace:

1. `.docs/system_overview/hybrid_integration_architecture_adr.md`
2. `PLANS.md`
3. `docs_contract_test.go`

The fixture `base_git_oid` is a preassigned WorkSpec coordinate. D1 does not
derive it from the artificial bytes or authenticate a Git object. The parent
enumerates and captures the complete before/after file set with no-follow,
hardlink, mode, count, path, and byte checks. It constructs
`CandidateCapsuleManifestV1` itself and separately reconstructs the candidate
from immutable fixture bytes and captured after-bytes, checks all entries and
bindings, and calls `validate_capsule_manifest_relation(...)`. The worker
does not author the manifest. The mutable workspace is removed before a
successful handback; unproved process or workspace cleanup prevents
`capsule_ready`.

The frozen nonprinting `RW0D1HandbackV1` contains committed lineage receipts,
typed process and Wire observations, captured immutable bytes/modes, the
verified manifest, and a closed status/reason. It contains no raw state path,
workspace path, writer, descriptor, proof, or serializable live-state handle.
The separate nonserializable parent-only `RW0D1OfflineRun` owns the disposable
state location until explicit idempotent `close()`. It retains no open writer
between stages or after return. D2 later consumes this run owner in the same
parent process.

RW0-D1 does not implement validator, independent reviewer, review model,
post-execution proposal family, D2 evidence admission, durable C2 decision,
acceptance or terminal outcome, live provider/credential/supplier, ES route,
Git effect, publication, public API/CLI/service, scheduler, queue, or RW0-E
runtime. RW0-D2 evidence/review/model closure is next for the selected offline
proof; RW0-C2 physical decision persistence follows D2. The generic earlier
C2-before-D source ordering is superseded only for this bounded proof. C2
authority semantics and first-live entry rules remain unchanged.
