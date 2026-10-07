# RW0-C1 durable phase and supplied-evidence state

Status: `CURRENT IMPLEMENTED CONTRACT`. Migration 0004, the private mutation
and recovery paths, permanent tests, and repository status synchronization are
implemented together in this candidate.

RW0-C1 is the Coordinator-owned private durable boundary for establishing one
immutable RW0 phase basis and admitting one typed supplied-evidence member at a
time. It is not a completeness, decision, acceptance, terminality, execution,
custody, source-authenticity, or external-contact authority.

## Authority boundary

C1 owns exactly two private mutation families:

- `establish_rw0_phase`
- `admit_rw0_evidence`

The existing `_CoordinatorMutationTransactionController` remains the only
owner of the mutation lease, SQLite connection, `BEGIN IMMEDIATE`, writer
fencing, nominal read capability, rollback, commit attempt, uncertainty state,
and cleanup. C1 adds no public `StateStore`, `WriterSession`, or package API.

The implementation must not contact Bridge, Execution Substrate, a worker,
provider, host, verifier, custodian, or another repository. C1 never persists a
complete capsule manifest, WorkSpec body, blob map, path list, exception object,
traceback, or other private body.

## Phase identity

The durable pair is `phase_basis_ref` and `phase_basis_digest`, copied from an
exact `RW0PhaseEntryBasisV1`. K8 order is:

1. `program_ref`
2. `semantic_attempt_ref`
3. `candidate_ref`
4. `effect_intent_ref`
5. `author_command_ref`
6. `attempt_fence_ref`
7. `effect_fence_ref`
8. `delivery_attempt_ref`

Phase establishment reconstructs current durable owner state, invokes
`validate_phase_entry_basis(...)` once with the actual transient `WorkSpecV1`,
and durably binds one phase relation with fourteen operands. Mutable selection,
effect, delivery, and global-stop rows are captured as phase-local immutable
admission snapshots. Later progression does not invalidate historical replay or
recovery.

## Evidence inventory and dependency closure

The fixed rank inventory is:

1. `authority_verification_observation`
2. `subordinate_authorization_proposal`
3. `custody_availability_observation`
4. `retrieval_capability_event_observation`
5. `remote_host_readiness_observation`
6. `effect_host_qualification`
7. `worker_mechanism_capability_declaration`
8. `worker_mechanism_capability_observation`
9. `worker_mechanism_capability_qualification`
10. `wire_cancellation_request_observation`
11. `wire_process_observation`
12. `c2a_worker_observation`
13. `wire_worker_result_binding`
14. `wire_process_result_classification_binding`
15. `section41_post_execution_proposal_family_member`

Admission is single-member. Every C1 evidence operand identifies an exact
already-admitted same-phase membership. Legal partial phases are precisely
dependency-closed subsets and imply no completeness.

Every evidence-admission command repeats the immutable program/work CAS
preimages stored by phase establishment. A command naming later mutable-head
preimages is a `current_state_conflict`; C1 does not silently replace the
durable command-reconstruction source. Current owner rows must also still match
those preimages when a fresh admission is evaluated. On a receipt miss, C1
reads the exact phase first, then the actual current program/work rows and
applies that CAS before any registry, membership, prerequisite-member,
relation, or command-owner collision probe. Receipt-present replay remains
receipt-first and does not require historical mutable heads to remain current.
Later progression after a commit does not affect replay or recovery. An actual
missing owner-reader result maps to `owner_row_missing`; an already-sanitized
reader integrity, operational, or uncertainty error propagates unchanged.

Ranks 5 and 7 have no relation. Ordinary rank 12 has one relation;
cancellation acknowledgement or rejection has two. Every other member has one,
so the maximum is two and the overflow read uses `LIMIT 3`. Relation operands
are dense and bounded at fourteen; overflow uses `LIMIT 15`.

Rank 15 wraps the existing Section 41 post-execution family without widening
its owner contract. The exact family is the immutable source-invocation,
private-artifact-binding, and model-proposal rows followed by either zero or
the complete nine post-execution evidence-binding rows. A bounded `LIMIT 16`
reader proves the 0-or-9 cardinality, canonical role/rank/order/required flags,
same proposal and evidence-set coordinates, row self-digests, exclusion of
extra rows, and the reconstructed evidence-set digest. The post-execution safe
projection identity is already embedded in the artifact and proposal rows;
the pre-execution projection table is not part of this family and remains
forbidden for post-execution state.

C1 locates the exact immutable development-owner and Section 41 rows through
literal explicit-column, parameterized, bounded private SELECT contracts. It
validates their row self-digests and reconstructs only the C2A semantic values
needed by C1 through the existing semantic constructors. It does not import or
modify protected owner-row modules, add a caller to the frozen twenty-four
development-reader query inventory, or widen an existing owner reader.

## Identity and privacy

The registry identity is kind-scoped:

```text
PRIMARY KEY (kind_rank, value_ref)
UNIQUE (kind_rank, value_digest)
UNIQUE (kind_rank, value_ref, value_digest, value_schema_id)
```

Cross-kind textual ref or digest reuse is legal. Membership has a stable
caller-preassigned `membership_ref` and a self-verifying `membership_digest`.
A reusable value may belong to multiple phases, but every dependency and later
C2 closure binds the exact membership pair.

Operand source is closed to:

- `c1_evidence`
- `existing_owner_row`
- `transient_private_binding`
- `admission_snapshot_binding`

Transient binding kinds are `work_spec`, `candidate_capsule_manifest`,
`before_blob_set`, `after_blob_set`, and `wire_protocol_error`. Snapshot kinds
are `selection_head_snapshot`, `effect_head_snapshot`,
`delivery_head_snapshot`, and `global_stop_snapshot`.

## Temporal contract

`operation_timestamp` is controller-owned canonical whole-second UTC and is
the actual admission time. It is stored as phase `established_at`, membership
`admitted_at`, and result/receipt `committed_at` as applicable.

`relation_evaluated_at` is the exact semantic instant passed to an owner
`now_utc` parameter and is stored in `relation.evaluated_at`.

For authority verification, subordinate narrowing, custody binding, and
retrieval sequencing, relation evaluation time equals operation time. Rank 6
uses `RW0EffectHostQualificationV1.evaluated_at`. Rank 9 uses the capability
qualification timestamp, which must equal the exact prerequisite rank-6 host
qualification timestamp. Rank-6 and rank-9 evaluation time may precede, but may
not follow, durable admission time. Other relation IDs store NULL.

The temporal-source registry is closed. An unrecognized relation schema ID is
invalid and fails before writes; it is never treated as an implicitly
non-temporal relation.

Replay and recovery never substitute the current clock. Rank-6 and rank-9
admission proves the owner relation only at the historical semantic instant; a
later C2 decision must establish its own closure-time currentness.

## Mutation and recovery

Both families use receipt-first replay after writer fencing. Exact mutation ref
and command digest returns the original projection without writes or a new
clock. Replay also compares the exact durable member, owner, and privacy-safe
transient operand locators with the supplied command. Reuse with another digest
is `mutation_ref_reuse`.

Fresh writes publish the receipt last, perform full in-transaction readback,
invalidate the capability, and attempt commit exactly once. A commit-attempt
exception is `commit_outcome_unknown`; it is never automatically retried. Once
that attempt starts, one private per-operation in-memory witness advances only
through `commit_attempt_started`, `commit_returned_success`, and
`close_proof_complete`. The witness is shared by the controller, module
delegate, and writer-session wrapper and is neither durable nor exported. Every
ordinary exception before result publication, controller/module return,
nominal-capability and connection cleanup, mutation-slot and operation-lease
retirement, process stabilization, and writer-session post-operation cleanup
all prove closed is likewise `commit_outcome_unknown`. `close_proof_complete`
means that internal cleanup is complete; it does not mean that the caller has
received the result. The same witness remains live through the final writer
handoff and actual outer-frame return, and an ordinary failure in that interval
is still `commit_outcome_unknown`. Successful frame return naturally ends the
private witness lifetime; there is no durable or public handoff marker. Raw
cleanup exceptions and narrower integrity or mutation errors cannot escape
after the attempt begins. Replay and conflict paths that never attempt commit
remain outside commit uncertainty and can complete the witness directly from
`precommit`; a standalone ordinary retirement failure on such a path is the
content-free `mutation_failed` classification and does not attempt another
commit.

Explicit recovery under a fresh fenced writer returns exactly one of:

- `committed_exact`
- `definitely_not_committed`
- `unresolved`

Recovery uses a separate private per-operation close witness because it never
attempts commit. No computed recovery disposition is published until mutation-
lease retirement, operation-lease retirement, process stabilization, and outer
writer cleanup prove complete. An ordinary cleanup failure after result
computation, including after recovery `close_proof_complete` and during the
final writer handoff, returns exact content-free `unresolved`. The computed
result stays privately available to construct that unresolved projection until
the outer frame returns successfully. Governing process-control keeps its
existing precedence. Before a recovery result is computed, an established safe
`WriterSessionError`, `SQLiteMutationStoreError`, or private C1 failure remains
primary over a later ordinary operation-retirement failure; the secondary
failure and its traceback are not exposed.

Committed phase recovery verifies the phase row, phase relation, fourteen
dense operands, nine immutable owner rows, transient WorkSpec binding, four
phase snapshots, graph/result/receipt digests, and K8. Committed member recovery
verifies the exact registry and typed rows, children, membership, relation set,
operands, dependencies, graph, result, and receipt. Partial or contradictory
families are unresolved.

Evidence-admission recovery accepts a private immutable selector derived purely
from the validated command before transaction entry. Its semantic identity is
the mutation ref and command digest; phase ref/digest; caller-preassigned
membership ref; kind rank; value ref/digest/schema; exact prerequisite-member
locators; and exact immutable owner-row locators. The selector has its own
self-digest and contains no membership digest, admission time, relation-set or
result/receipt digest, current mutable-head snapshot, database observation, or
raw transient operand. Receipt-present recovery obtains the membership digest,
admission time, and result/graph identities only from the committed family and
returns `committed_exact` only after full-family verification against the
selector.

Receipt-absent evidence recovery returns `definitely_not_committed` only when
the phase, every prerequisite membership family and receipt, and every immutable
owner row are exact; the mutation receipt, preassigned membership ref, both
phase/kind/value membership routes, and both deterministic operation relation
families and globally addressed operands are absent; and independent kind-
scoped registry and typed-payload lookups by both value ref and value digest,
plus independent rank-1/rank-12 child lookups by both routes, prove either
complete absence or one exact reusable global family. Deterministic operation
relation refs are also probed globally rather than only inside the requested
phase. Missing prerequisites, same-kind ref/digest aliases, partial registry/
payload/child families, child-only fragments, foreign-phase relation bindings
or operands, any membership/relation/receipt fragment, malformed rows, and
unreadable state are `unresolved`. Recovery never consults current mutable
heads and never requires the caller to query or guess a membership digest.

## Durable schema

Migration `0004_rw0_c1_durable_evidence` is additive, generation 2,
non-destructive, and has zero seed rows. It adds 23 STRICT tables, 46 immutable
update/delete triggers, and four explicit indexes. The cumulative schema is 62
user tables, 110 triggers, and five explicit indexes.

No C2 decision, closure, completeness row, latch, terminal outcome, worker,
runtime, transport, capsule custody, or external integration is part of C1.

The separate post-execution decision-input owner is implemented only as
private, pure, no-I/O values, projections, evaluators, and bounded helpers. It
may consume safe C1 evidence projections but neither changes C1's fixed
fifteen-kind inventory nor converts that evidence into a durable decision. The
complete tranche has no production caller; performs no runtime or I/O; makes
and writes no durable post-execution decision; adds no migration or SQLite
widening; creates no public export; and acquires no external authority or
custody. It implements no C2B progression, terminal outcome, RW0-D/E, or
Execution Substrate work; C2 persistence and runtime remain absent.
