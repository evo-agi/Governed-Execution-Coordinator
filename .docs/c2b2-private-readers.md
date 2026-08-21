# C2B2 Slice 3 Private Readers

## Status And Authority

Status: `CURRENT IMPLEMENTED CONTRACT` for the private,
production-unintegrated C2B2 reader layer.

This is an implementation-status and private-API record. The semantic owner
remains `.docs/c2b-durable-development-state.md`; migration 0002 and cumulative
packaged SQL remain physical-schema authority; the existing transaction
controller remains capability authority. This document is not semantic,
schema, migration, capability, or runtime authority, and it defines no public
API.

Slice 3 adds no schema or migration, creates no durable record, and adds no
production caller. It does not widen the package root, `StateStore`, or
`WriterSession`.

## Exact Private Source

The implementation has exactly two new private source modules:

```text
src/ge_nwp_coordinator/_sqlite_development_reader_contracts.py
src/ge_nwp_coordinator/_sqlite_development_readers.py
```

Both have an empty `__all__`. The contracts module is pure and performs no
I/O. The reader module performs only literal SQLite `SELECT`s through the
existing nominal `_SQLiteMutationReadCapability` and the shared bounded SELECT
support in `sqlite_transition_select_support.py`.

## Twelve Private Reader Functions

```text
_read_development_mutation_receipt_by_mutation_ref
_read_development_decision_by_decision_ref
_read_development_program_head_and_current_version
_read_development_initialize_decision_and_resulting_version
_read_development_accepted_intent_revision_by_exact_ref
_read_development_work_item_head_and_revision_by_exact_ref
_read_development_paged_program_version_membership
_read_development_work_spec_safe_binding
_read_development_attempt_fence_command_effect_aggregate
_read_development_authority_evaluation_by_exact_ref
_read_development_effect_head
_read_development_delivery_head
```

There is no registry, dispatcher, dynamic SQL, generic table lookup, public
reader, or production importer.

## Seven Private Aggregate And Page Values

```text
DevelopmentProgramHeadAndCurrentVersionRead
DevelopmentInitializeDecisionAndResultingVersionRead
DevelopmentWorkItemHeadAndRevisionRead
DevelopmentProgramVersionMembershipEntry
DevelopmentProgramVersionMembershipRead
DevelopmentAttemptFenceCommandEffectRead
DevelopmentDeliveryHeadAndCurrentAttemptRead
```

They are manually slotted, factory-constructed, immutable, non-subclassable,
unhashable, content-free in `repr`/`str`, identity-preserving under copy and
deepcopy, and non-pickleable. Collections are tuples. No value retains SQL,
parameters, raw row tuples, mappings, cursors, connections, capabilities, or
epochs.

## Twenty-Four Literal Query Specifications

```text
_MUTATION_RECEIPT_SELECT
_DECISION_SELECT
_PROGRAM_HEAD_SELECT
_CURRENT_PROGRAM_VERSION_SELECT
_INITIALIZE_DECISION_SELECT
_RESULTING_PROGRAM_VERSION_SELECT
_ACCEPTED_INTENT_REVISION_SELECT
_WORK_ITEM_HEAD_SELECT
_WORK_ITEM_REVISION_SELECT
_PROGRAM_VERSION_ROOT_SELECT
_MEMBERSHIP_FIRST_PAGE_SELECT
_MEMBERSHIP_CONTINUATION_PAGE_SELECT
_MEMBERSHIP_WORK_ITEM_REVISION_SELECT
_WORK_SPEC_SAFE_BINDING_SELECT
_EFFECT_INTENT_ROOT_SELECT
_SEMANTIC_ATTEMPT_SELECT
_AUTHOR_COMMAND_SELECT
_ATTEMPT_FENCE_SELECT
_CURRENT_EFFECT_FENCE_SELECT
_AUTHOR_EFFECT_FENCE_SELECT
_AUTHORITY_EVALUATION_SELECT
_EFFECT_HEAD_SELECT
_DELIVERY_HEAD_SELECT
_CURRENT_DELIVERY_ATTEMPT_SELECT
```

Each specification owns fixed SELECT text, exact selected-column order, exact
symbolic parameter order, and one fetch bound. Twenty-two singleton/root/child
queries use `LIMIT 2`; the two membership page queries use `LIMIT 257` and
`ORDER BY membership_ordinal ASC, work_item_ref ASC`.

## Capability, Cardinality, And Error Order

Every reader validates lookup inputs first. It then imports the nominal class
at the bounded function-local gate, requires
`type(capability) is _SQLiteMutationReadCapability`, and only then permits a
borrow or SQL. Structural stand-ins, raw SQLite connections, nominal
subclasses, and forged borrow objects cannot reach the shared SELECT support.
Expired, wrong-process, and wrong-thread capability failures remain capability
errors rather than reader-safe errors.

An absent root returns `None` and issues no child SQL. A duplicate or malformed
root fails before child SQL. Every required child must be exactly one valid row;
missing, duplicate, malformed, or incoherent children fail without a partial
aggregate. SQLite/schema/cardinality/row/relation contradictions are
`database_integrity_failure`. Operational busy, locked, closed, unknown I/O,
and successful-fetch cursor-close failures are `mutation_failed`; an earlier
execute/fetch failure remains primary over a later close failure. Errors expose
no SQL parameters, private row values, credentials, connection details, or
capability epochs. Outward safe error payloads are content-free and detached.
Slice-3-owned traceback frames retain no prohibited raw/private material.
Caller-owned frames remain outside the enforceable purge guarantee.

## Completed Membership

The membership reader validates an exact built-in positive `maximum_members`
before capability gating; `bool` and `int` subclasses are rejected. It first
validates the exact program-version root, then traverses all internal pages
with the same nominal capability and epoch. Physical pages contain at most 257
rows, of which at most 256 are logical members. Row 257 is retained as
has-more evidence and must be re-read as the next page's first row using the
last logical `(membership_ordinal, work_item_ref)` continuation pair.

Completion requires strict lexicographic advance, dense ordinals `0..n-1`, no
overlap, no duplicate pair or ordinal, and one occurrence of each
`work_item_ref` across the whole aggregate. Every member binds its exact work
item revision. Empty membership is invalid for every current program-version
kind. Before processing a member that exceeds `maximum_members`, the reader
fails `mutation_failed` and issues no child query for that excess member. No
continuation or partial aggregate escapes.

## Evidence And Non-Authority

Role 9 uses effect intent as its deterministic root and reads semantic attempt,
author command, attempt fence, current effect fence, and the author fence only
when distinct. It enforces the frozen cross-row identity, ref/digest, Git base,
path, global-stop, allowed-class, expiry, and ceiling relations. It executes no
authority-evaluation query and infers no authority. Its result proves no
capsule identity or custody, semantic acceptance, execution permission, route
eligibility, cancellation-target coherence, graph completeness, replay, or
recovery.

Role 10 selects an authority evaluation only by exact `program_ref` and
`authority_evaluation_ref`. It performs no subject scan, timestamp ordering,
preferred-state selection, or receipt-digest inference. A decoded evaluation,
including a verified evaluation, is evidence only and grants no executable
permission.

The mutation-receipt reader verifies the row and its scalar/projection/digest
algebra. A receipt has no row self-digest. The reader neither defaults graph
entries to empty nor locates referenced rows, and it claims no complete family
graph, replay, or recovery proof.

## Remaining Nonimplementation

Still absent are a production caller, public reader API, package-root export,
`StateStore`/`WriterSession` reader method, C2B mutation API, receipt
persistence, family graph discovery or completeness, replay, recovery, C2B3,
migration 0003, and every worker, model, process, capsule, Git, direct-local,
Execution Substrate, Bridge, publication, or other external effect.
