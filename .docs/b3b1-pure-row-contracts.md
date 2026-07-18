# B3b1 Pure Row Contracts

Status: implemented pure/model row contracts; no SQLite readers or fixtures.

B3b1 implements internal contracts that convert already-fetched explicit-column
SQLite row mappings into typed internal envelopes. These contracts are pure
model adapters. They do not import SQLite, open a connection, own a transaction,
issue SQL, classify row cardinality, classify not-found, seed fixtures, assemble
`TransitionContext`, or mutate work-item or global-stop state.

## Implemented Row Contracts

B3b1 accepts exact mappings for these schema-0001 row shapes:

- `lease_identity_records`;
- `authorization_decision_receipts`;
- `dependency_decision_receipts`;
- `work_items`;
- `admitted_backlogs`;
- `global_stop_current`.

Every adapter requires the complete explicit SQL column set for that row. Missing
or unknown keys, malformed SQLite Boolean values, unsupported schema ids,
timestamp shape errors, canonical JSON mismatches, digest mismatches, and
index/canonical contradictions fail with the safe
`database_integrity_failure` mutation-store classification.

## Internal Envelopes

The adapters return internal frozen envelope values:

- `LeaseIdentityRecordEnvelope`;
- `AuthorizationReceiptEnvelope`;
- `DependencyReceiptEnvelope`;
- `WorkItemRecordEnvelope`;
- `AdmittedBacklogRecordEnvelope`;
- `GlobalStopCurrentRecordEnvelope`.

The envelopes retain operational row timestamps:

- `created_at` for lease identity, authorization, and dependency receipts;
- `admitted_at` for admitted backlogs;
- `updated_at` for current work-item and global-stop rows.

These timestamps are exact canonical UTC `Z` row metadata. They are validated
and retained by the envelope only. They do not change the canonical semantic
identity or digest of `StandingLease`, `AuthorizationDecision`,
`DependencyDecision`, `FiniteBacklog`, `WorkItemRecord`, or `GlobalStopState`.
They are not event/replay digest inputs merely because they are retained, are
not operator/public report fields, and are not package-root exports.

Malformed operational timestamp values fail with only safe field-class
failures. The rejected row value must not appear in public mutation-store
errors, safe repr output, retained exception chains or tracebacks.

B3b1 does not weaken the separate B3a rule that future
`transition_events.created_at` must equal
`TransitionEvent.lease_runtime.evaluated_at`. That future event-row timestamp is
a different contract from these current-row operational envelopes.

## Existing Receipt Rows

The lease identity, authorization, and dependency full-row adapters reuse the
existing canonical row contracts before wrapping the reconstructed typed value
with `created_at`.

Lease identity reconstruction parses literal canonical `StandingLease` JSON,
verifies row digest equality, regenerates `LeaseIdentityValidation`, and checks
row/index equality for decision ref, lease ref, validity, lease digest, and
schema id.

Authorization reconstruction parses literal canonical `AuthorizationDecision`
JSON, verifies digest equality, and checks row/index equality for lease refs,
authorization model, Boolean columns, reason, and schema id. The
`operator_policy` authorization model remains schema vocabulary only and is not
trusted as executable authority.

Dependency reconstruction parses literal canonical `DependencyDecision` JSON,
verifies digest equality, and checks row/index equality for decision ref,
nullable work-item binding, satisfied Boolean, reason, and schema id.

## Work-Item Rows

The work-item adapter maps the complete schema-0001 `work_items` row into a
`WorkItemRecordEnvelope`. `updated_at` is retained only as operational metadata
and remains outside `WorkItemRecord` canonical identity and replay digest.

The compatibility function `work_item_record_from_row(payload)` delegates to
the envelope adapter and returns `.record`.

B3b1 does not invoke `validate_b3_work_item_authority_binding` from the single
work-item row adapter. Lease/backlog/work-item authority binding, exact
lease-copied attempt and repair limits, zero scalar current-state budget fields,
and static multidimensional budget policy remain in the separate binding helper
that B3b2/B3c assembly must call after the relevant rows are loaded.

## Admitted Backlog Rows

The admitted-backlog adapter validates one row only. It requires:

- exact safe backlog id;
- exact safe lease ref;
- schema id `governed-execution.nwp-finite-backlog.v1`;
- exact integer schema version `1`, not Python `bool`;
- exact lowercase SHA-256 content digest;
- non-empty bounded canonical JSON;
- exact canonical UTC `admitted_at`.

Reconstruction parses `canonical_json` with `FiniteBacklog.from_json`, preserves
the embedded content-digest verification, requires literal canonical JSON
equality, and checks row/model equality for backlog id, lease ref, schema id,
schema version, and content digest.

It does not validate cross-record lease/backlog/work-item authority by itself.
Future B3b2/B3c assembly remains responsible for calling
`validate_b3_work_item_authority_binding(...)` with the loaded lease, backlog,
and current work-item record.

## Global Stop Current Rows

The `global_stop_current` adapter validates the singleton current row and
constructs one `GlobalStopState` inside a `GlobalStopCurrentRecordEnvelope`.
The row has no canonical JSON or digest; its explicit typed columns are the
schema-0001 current-state authority.

It requires:

- singleton id exact Python integer `1`, not Python `bool`;
- schema id `governed-execution.nwp-global-stop.v1`;
- exact non-negative integer version, not Python `bool`;
- strict SQLite Boolean parsing for `active`;
- exact canonical UTC `updated_at`;
- active/clear nullable-field consistency.

An active state requires `stop_id`, `reason_class`, `issuer_ref`, `issued_at`,
and `operator_decision_ref`. A clear state requires all of those fields to be
null. Active `issued_at` is validated as exact canonical UTC `Z` before the
typed `GlobalStopState` is constructed.

B3b1 does not read or validate global-stop event history and does not implement
B4 global-stop mutation.

## Boundary

B3b1 adds no SQLite `SELECT`, row cardinality query, connection, transaction,
reader object, fixture insertion helper, seed helper, production admission API,
authorization verifier, `TransitionContext` loader, idempotency/replay runtime,
event sequence allocation, expected-version runtime, B3c transition apply, or
B4 global-stop mutation.

The row contracts are absent from `ge_nwp_coordinator.__all__`, CLI, MCP,
connectors, reports, and examples. They must not expose raw mappings,
canonical JSON, private assignment refs, path policy, branch policy, row values,
database paths, credentials, endpoints, proofs, digests, or secrets through
public errors or safe repr output.

B3b1 tests are repo-hermetic. They validate Coordinator source and contracts
from a standalone Coordinator checkout and do not require sibling checkouts,
shared parent checkout layouts, or related repositories to exist. The
related-repo cleanliness is closeout and audit evidence, not a Coordinator unit-test
contract. Workspace-level integration tests, if added later, require a
separately owned harness outside this B3b1 contract.

B3b2 remains future.
