# C2B2 Slice 2 Pure Durable Row/Value Implementation

## Status And Authority

This document is the implementation-status and private-API record for C2B2
Slice 2. The semantic owner remains
`.docs/c2b-durable-development-state.md`, and the generation-2 physical schema
authority remains migration `0002_development_program_and_effect_state` plus
its cumulative packaged SQL. This record is not a new durable tranche identity,
schema authority, reader contract, or source of runtime truth.

Slice 2 implements pure, private, no-I/O row/value source. VS1B consumes a
bounded subset through its private route-neutral program-genesis mutation;
C2B3D consumes the program, effect, decision, receipt, and graph values for one
private author-effect establishment family. Slice 3 consumes the same values
in private SQLite readers recorded in `.docs/c2b2-private-readers.md`. None of
these callers changes this pure layer. Bound-effect, observation-ingest, and
later progression-decision mutation/replay/recovery behavior remains absent.
The implementation grants no retrieval, authorization, execution, acceptance,
publication, worker, runtime, adapter, Bridge, or ES authority.

## Exact Source Layout

The implementation is exactly four private modules:

```text
_development_row_value_support.py
_development_program_row_values.py
_development_effect_row_values.py
_development_decision_row_values.py
```

Every module has `__all__ = ()`; none is exported from the package root. The
support module owns only scalar, timestamp, fixed compound encoding, hashing,
tuple-boundary, immutable-value, and safe-error mechanics. The three owner
modules do not import one another. The program owner imports only `WorkSpecV1`;
the effect owner imports only `AttemptFenceV1`, `EffectFenceV1`,
`WorkerCommandV1`, `DeliveryEnvelopeV1`, and the bounded C2A value error used
for reduction; the decision owner imports no C2A value.

## Nineteen-Table Partition

The program module owns tables 1–9:

```text
development_program_heads
development_program_versions
development_accepted_intent_revisions
development_work_item_heads
development_work_item_revisions
development_program_version_work_items
development_revision_edges
development_work_spec_bindings
development_semantic_attempts
```

The effect module owns tables 10–17:

```text
development_attempt_fences
development_authority_evaluations
development_effect_intents
development_effect_fences
development_author_commands
development_effect_heads
development_delivery_attempts
development_delivery_heads
```

The decision module owns tables 18–19:

```text
development_decisions
development_mutation_receipts
```

Each table has one literal ordered column tuple, one explicit row-value class,
and one explicitly named `development_<family>_row_value_from_row_tuple`
factory. There is no table-name argument, registry, dispatcher, SQL parser,
cursor-description adapter, row factory, or public mapping boundary.

## Value And Digest Behavior

All Slice-2 values are manually defined, slotted, read-only, exact-type
immutable values. They have no instance dictionary or weak-reference slot,
cannot be directly constructed or subclassed, are unhashable, use constant
content-free `repr`/`str`, preserve identity under shallow and deep copy, and
cannot be pickled. Equality includes operational timestamps even when a
timestamp is excluded from a digest. Arrays are retained only as tuples.

Nine program rows, eight effect rows, and the decision row verify eighteen
self-digests. The mutation receipt deliberately has no self-digest. Canonical
C2B identities use compact sorted-key UTF-8 JSON and the owner-frozen
domain-NUL-identity SHA-256 formula. Receipt construction verifies one of five
closed result projections and its family-specific digest before accepting the
row, while treating `mutation_graph_digest` only as a lowercase SHA-256 shape.

## C2A Reconstruction And WorkSpec Projection

Persisted attempt fences, effect fences, author commands, and delivery
envelopes are reconstructed only through the current C2A `from_mapping`
factories. Their stored C2A digests are therefore verified by C2A rather than
by copied validators. The delivery attempt separately verifies the outer C2B
wrapper identity; the physical `schema_id` remains the embedded delivery
envelope schema, while the outer wrapper schema is a fixed implementation
literal and not a twentieth physical column. No capsule-dependent or cross-row
C2A relation is claimed.

WorkSpec-object construction accepts only exact `WorkSpecV1`, reads only the
fourteen named safe source properties, computes the safe-projection digest,
and returns a `DevelopmentWorkSpecSafeProjection`. It never reads or retains
objective, requirements, exclusions, prompts, responses, transcripts,
candidate bytes, capsule data, workspace paths, credentials, endpoints, or
retrieval material. The projection contains the owner-frozen fifteen-key
identity and exact three-path tuple.

Persisted physical-row reconstruction instead treats the stored
`safe_projection_digest` column as required evidence. It requires an exact
non-null lowercase SHA-256, independently recomputes the safe-projection
digest from the other safe physical columns, and requires equality before
constructing the projection. It never synthesizes, defaults, or repairs a
missing persisted component. The outer `work_spec_binding_digest` is then
validated separately. The safe-projection digest excludes `recorded_at`; the
outer binding digest includes the binding's `recorded_at`.

## Decisions, Results, And Supplied Graphs

`DevelopmentDecisionRowValue` contains one of ten explicit private variants:
program genesis, candidate acceptance, candidate repair, program replan,
attempt-selecting replan, program terminal reject, program block, productive
redelivery, cancellation redelivery, or effect cancellation. The factory
enforces the complete kind/variant/nullability algebra before verifying the
decision digest. There is no payload bag, extension mapping, unknown variant,
or fallback.

`DevelopmentMutationReceiptRowValue` verifies exactly one of five explicit
private result projections: initialization, author-effect establishment,
bound-effect establishment, observation ingest, or progression decision. A
projection digest never overrides scalar inequality.

`DevelopmentMutationGraphEntry`, `development_mutation_graph_entry(...)`,
`compute_development_mutation_graph_digest(...)`, and
`require_development_mutation_graph_digest_matches_supplied_entries(...)`
provide only the common supplied-entry primitive. Entry order is significant;
duplicate `(role, ordinal)` and `(role, record_ref)` pairs fail, while one
record ref in different roles is permitted. An explicitly supplied empty tuple
is structurally valid. A digest match proves only the identity of those
supplied entries; it does not prove role validity, family completeness,
record existence, graph location, replay, or recovery.

## Timestamp, Error, Privacy, And No-I/O Boundaries

Every non-null timestamp is an exact built-in string in real Gregorian
`YYYY-MM-DDTHH:MM:SSZ` form. Program/version/revision/membership/attempt,
effect-intent/head, delivery-head, WorkSpec-binding, delivery-wrapper,
decision, receipt, and authority-evaluation operational timestamps participate
in their owner-frozen outer identities. Attempt- and effect-fence expiry is
inside embedded C2A identity. Attempt-fence, effect-fence, and author-command
`recorded_at` remains outside every digest while remaining part of row-value
equality.

Malformed rows, projections, or supplied graph inputs reduce to a newly
constructed `database_integrity_failure` with no internal detail, cause,
context, notes, or rejected value in Slice-2-owned traceback locals. Safe refs
and digests remain inert evidence and confer no retrieval or effect authority.

The four modules contain no SQLite import, SQL, reader capability, connection,
cursor, filesystem, environment, clock, randomness, logging, network,
subprocess, process/thread control, Git invocation, dynamic import, evaluator,
compiler, registry, test import, document/migration parser, reader, writer,
transaction, or mutation controller. Generation-2 schema bytes are unchanged.
