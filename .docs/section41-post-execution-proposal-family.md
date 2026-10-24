# Section 41 native post-execution proposal family (bounded offline successor)

Status: **selected contract for the private post-D2 implementation**. This is
subordinate to `.docs/c2b-durable-development-state.md` and does not change
the existing pre-execution selection grammar or the D2 v1 handback.

## Authority and ownership

The original, open D2 run is the in-process custody operand. Its typed
preadmission handback, D1 capsule owner, two bound effects, fourteen ordered
C1 checked admissions, and three cleaned child outcomes are revalidated at
the final consuming boundary. No detached dictionary, clone, closed run, or
wrong-process wrapper can substitute for that operand. The historical child
witness records the checker result; it is not a replay of a child or external
source authentication. Raw artifacts, prompts, WorkSpec, file bytes, process
output, paths, PID, environment, and V10/V11 supply are never stored.

The guarded writer session and the existing resource-bound transaction
controller exclusively own the two transactions. Transaction A records the
native post proposal; transaction B uses the existing C1 admission writer to
admit rank 15. A committed A with failed B CAS is retained proposal evidence,
not a C2 decision or a block. The original D2 run remains open through A,
B, checked readback and pure V22; the outer continuation closes it in `finally`.
No writer remains open across child launches. The result is transient.

## Closed input and safe basis

`RecordPostExecutionProposalCommandV1` contains one preassigned mutation ref,
phase basis ref/digest, V02 context ref/digest, source invocation ref/digest,
artifact ref/digest and binding digest, proposal ref/digest, evidence-set
ref/digest, nine ordered `(role, rank, ordinal, schema_id, ref, digest)`
selectors, the safe-basis digest and two preassigned bounded C1 route refs.
Its command digest is domain-separated over precisely those fields plus its
schema ID, excluding its own digest. The command has no rows, receipt,
connection, mutable head, authority Boolean, path or run owner. C1 route refs
are derived once from the preassigned phase/proposal/mutation identities,
before the command digest. A supplied command and the original run must agree
on every repeated identity.

`safe_basis_bytes` is canonical compact UTF-8 JSON, sorted keys, no duplicate
keys, finite scalar grammar, maximum 131072 bytes. The top-level keys are
exactly `lineage_v01`, `context_v02`, `capsule_safe_projection_v04`,
`model_safe_projection_v05`, `private_input_manifest_v07`,
`model_input_binding_v09`, `artifact_safe_projection`, and
`d2_checkpoint_witness`. The first six are the exact existing typed
`to_mapping()` / `from_supplied()` grammars for V01, V02, V04, V05, V07 and
V09, including their existing nested cardinalities. The V07 entries (V08)
retain only their typed metadata refs/schema IDs/digests/lengths and
classification; no V10/V11 `typed_canonical_value` or support payload is
allowed. `artifact_safe_projection` is the exact existing typed safe
projection mapping. The witness is a closed object with fourteen ordered C1
selectors (kind ranks `12,12,12,12,13,14,1,1,5,6,12,6,12,1`, each with
membership ref/digest, admission mutation ref and graph digest), two
bound-effect receipt selectors (effect class, mutation ref,
receipt mutation-graph digest), and three ordered child attestations (role, safe outcome
digest, `clean_success=true`, `cleanup_complete=true`). Its fixed lengths and
literal role orders are checked against the original run. Every nested object
uses exact builtins and its typed schema; unknown fields, bool-as-int, depth
or byte excess and noncanonical JSON fail before storage. The safe-basis
digest is domain-separated over the canonical bytes.

## Additive 0005 physical schema

`0005_section41_post_execution_proposal_family.sql` adds exactly two STRICT
immutable tables, no seed rows or explicit index. `development_post_execution_proposal_contexts`
has ordered columns `schema_id`, `proposal_phase`, `context_ref`,
`context_digest`, `proposal_ref`, `proposal_digest`, `phase_basis_ref`,
`phase_basis_digest`, `safe_basis_bytes`, `safe_basis_digest`,
`context_row_digest`. It has primary `context_ref`, unique
`(proposal_phase,context_ref,context_digest)` and
`(proposal_phase,proposal_ref)`, and immediate restricted FKs to the
phase-qualified common proposal and C1 phase. The byte field is a BLOB with
length 1..131072. `development_post_execution_proposal_receipts` has ordered
columns `schema_id`, `mutation_ref`, `mutation_command_digest`,
`proposal_phase`, `context_ref`, `context_digest`, `proposal_ref`,
`proposal_digest`, `phase_basis_ref`, `phase_basis_digest`,
`source_invocation_ref`, `source_invocation_digest`, `artifact_ref`,
`artifact_digest`, `artifact_binding_digest`, `evidence_set_ref`,
`evidence_set_digest`, `safe_basis_digest`, `c1_mutation_ref`,
`c1_membership_ref`, `mutation_graph_digest`, `committed_result_digest`,
`committed_outcome`, `committed_at`, `receipt_digest`. Its mutation ref is
primary; composite context/proposal, phase, and phase-qualified source and
artifact FKs are immediate and restricted. Its non-FK repeated digests and
coordinates are checked by typed write and complete readback, not claimed as
SQL-enforced digest equality. Both tables have UPDATE and DELETE abort guards.
The cumulative expected catalog is five migrations, 64 tables, 114 triggers
and five explicit indexes. Generation remains 2: additive 0005 requires the
already-gated SQLite >=3.37.0 and no grammar-breaking change to generation-2
application rows. An exact 0004 state is admitted only by explicit
`migrate_database()`; normal read, validation, writer acquisition and product
mutation never auto-migrate. Older binaries reject the new exact tip.

## A transaction and digest order

The writer performs exact local preflight, acquires its operation lease and
mutation slot, begins one resource-bound `BEGIN IMMEDIATE` and fences before
receipt disclosure. A receipt hit is checked as the whole historical
context/common/evidence/receipt family before same-command replay; mismatch
is an identity conflict. Replay does not resample current heads or expiry.

On a miss it samples one whole-second transaction time, rereads actual
phase/program/work/selection/effect/delivery/stop owners and compares the
original D2 B-time coordinates. At expiry equality, fresh admission fails.
Original observation timestamps remain historical. All global and composite
source/artifact/proposal/context/receipt/evidence routes are probed before
write. No upsert, key substitution or fragment completion is permitted.
Source, artifact, proposal, safe context, and exactly nine ordered evidence
rows are inserted under their immediate FKs. The same transaction then reads
the exact proposal with `LIMIT 2` and evidence ordered by role rank/ordinal
with `LIMIT 10`, checks the nine-role set and all cross-row relations, and
only then inserts the receipt. Full row/graph readback precedes capability
invalidation and one COMMIT attempt. Commit-call or post-attempt cleanup
failure cannot become a proven no-write outcome.

The acyclic digest order is: command identity; canonical safe basis; each
context/common row self-digest; mutation graph over ordered row identities;
committed result projection over immutable committed facts and time; receipt
identity; returned presentation result. The committed projection contains
neither its own digest, the later receipt digest, nor fresh/replay status.
Domain-separated SHA-256 identities use the exact closed mappings in the
family-local contract module. The checked reader uses actual bounded SELECT
tuples, never tuples reserialized from expected caller values. It reconstructs
V02, safe basis, context, twelve common owner rows and receipt, then checks
the immutable phase/C1/effect witness relations that are still retained. Each
C1 witness is checked through the existing complete C1 membership-family and
receipt validator, rather than trusting a few selected columns. C1 B commit
uncertainty is followed by read-only recovery and checked result reconstruction
from persisted C1 rows; it does not reissue the admission command.

## Recovery, B and final proof

Before attempts, freeze selectors for every claimed route. A fresh fenced
read-only recovery classifies only `committed_exact` (complete receipt-first
historical graph and command), `definitely_not_committed` (all routes absent
with exact prerequisite identities), or `unresolved` (partial, foreign,
inaccessible or contradictory). No automatic retry, repair or model rerun.
B is a fresh writer session and an existing C1 rank-15 command built from the
checked persisted twelve common owner rows, immutable phase CAS preimages and
the preassigned C1 route. C1 retains its own receipt-first/CAS/recovery
semantics and generic 0-or-9 family support. Final proof reads A and B in
fresh guarded sessions, includes twelve actual SELECT tuples and owner values,
and calls the unchanged pure V22 with an independently assembled expected
assertion. B CAS conflict reports A retained/not admitted. Proven B commit
with failed final verification is distinct from failed B commit. Neither A,
B, V22 nor the five recommendations authorize C2 acceptance or any effect.

The private `PostD2ContinuationResultV1` has a closed status and exact typed
result shape. A read-only A recovery of `definitely_not_committed` reports
`proposal_not_recorded`; an unresolved A recovery reports
`proposal_uncertain`. A read-only B recovery of `definitely_not_committed`
reports `proposal_recorded_not_admitted` with the known A result; an
unresolved B recovery reports `admission_uncertain`. A proven B commit with
later checked-readback or V22 failure reports `admitted_verification_failed`.
`projected` requires A, B and V22 values. A borrowed continuation leaves
`cleanup_complete` unset while the original run is still open; the outer
creator-process owner sets it true only after close succeeds.
`cleanup_unresolved` sets it false and carries no clean projection claim.
These transient labels do not become durable Coordinator state.

The first connected test must exercise actual D2 fake processes and A/B/V22,
then donor-policy, nine-role gate, B CAS, and historical replay controls
before broader fault coverage. Full selector-free collection and execution
from an authenticated external copy are the final candidate gate.
The final A gate tests omit each of the nine actual inserts in turn and fault
the bounded SELECT observation with extra, duplicate, reordered, role, phase,
source, set, digest and ref discrepancies. The physical role algebra and
unique keys also prevent a tenth valid persisted member; SELECT fault tests
exercise the independent reader/gate refusal without claiming a physically
inserted tenth row. All failures must leave no A target or receipt row.
An explicit transaction-time control samples one second before the earliest
applicable expiry, exactly at expiry and one second after; the first may
record only while every other original currentness premise still holds, and
the latter two must refuse without A rows.

## Unit 2 original-run association and two-layout successor

The private continuation and fresh Section 41 writer share one derivation of
the complete `RecordPostExecutionProposalCommandV1` and canonical safe-basis
bytes from the original open D2 run. On a fresh receipt miss, after writer
fencing and before route probing, insertion, or receipt construction, the
writer requires the supplied command and basis to equal that derivation
exactly. A valid donor command or basis with its dependent digests recomputed
is refused before target rows. This fresh association is separate from
receipt-first historical replay and checked persisted-family readback; replay
does not rerun children or require present process custody.

The safe-basis `d2_checkpoint_witness.checked_memberships` has exactly one
complete legal sequence: 13 ranks `(12, 12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12,
1)` for two Worker Wire observations, or the historical 14 ranks `(12, 12,
12, 12, 13, 14, 1, 1, 5, 6, 12, 6, 12, 1)` for three. Parent-owned candidate
capture exists in both; omission of the optional `candidate_captured` worker
observation is not a missing-candidate claim. `worker_completed` retains no
candidate or capsule conditional fields. The three-observation command and
safe-basis bytes remain unchanged. Clean malformed validator or reviewer
evidence returns a typed D2 stop before this native writer is called.

The existing A/B transaction split, nine model-evidence roles, twelve common
Section 41 owner rows, C1 rank-15 admission, V22 semantics, physical 0005
schema, and three-way recovery remain unchanged. This bounded offline proof
adds no C2 decision, acceptance, executable permission, provider, ES route,
Git effect, publication, or autonomous loop. Independent review remains
outstanding.
