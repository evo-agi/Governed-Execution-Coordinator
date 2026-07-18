# P1.1 Transition Event Algebra

A2-P1.1 defines contract objects for a future atomic state backend. B3a adds
canonical persistence and provenance contracts, but it still does not implement
that backend.

The P1.1 model has one durable outcome record for each committed transition:
the event. The event is the receipt. Caller code never supplies a proposed
state, proposed event, or proposed receipt.

## Responsibility Owners

The parser and model layer owns closed-world parsing, duplicate JSON object key
rejection, scalar and identifier validation, canonical command identity,
schema-aligned decision/event/replay mappings, and typed decision/context
validation. It rejects malformed values before a store apply call.

External versioned inputs are exact-shape and non-coercing. Collection fields
must verify their external JSON-array/Python-list shape before element
validation, normalization, canonicalization, or digest verification. Malformed
array-like input must not be canonicalized into an accepted command identity.

The atomic apply boundary owns writer-session fencing, internal idempotency
lookup, authoritative current-state loading, expected-version comparison,
authoritative context reconstruction, pure evaluator invocation, atomic
state/event persistence, and exact replay. `WriterSession.apply_transition`
accepts only `TransitionCommand`; caller-supplied `TransitionContext` is not
authority.

The pure evaluator owns domain rules: target-state support, invariant P1 stage
availability, typed lease identity/runtime and authorization decision effects,
dependency rules, budget and counter rules, global-stop domain effects, and
construction of accepted or domain-rejected events.

The report layer owns projection only. Reports do not mutate state, authorize
work, accept work, publish work, or become transition inputs.

## Failure Taxonomy

### 1. Local / Pre-Store Invalid

Examples include malformed external mappings, invalid canonical digests,
unsafe typed refs, impossible typed object construction, closed writer
sessions, writer-session process mismatch, and B2c mutation-unavailable
calls.

Result: local safe validation failure, no event, no `StateStore` call, no
SQLite apply, and no apply conflict. `validation_failed` is not a catch-all for
parser, model-construction, session-lifecycle, or mutation-unavailable
failures.

### 2. Transactional Validation Conflict

Examples include locally valid commands whose persisted lease, authorization,
dependency, global-stop, current-record, or addressing bindings do not match
authoritative records inside the fenced SQLite atomic boundary, or whose
authorization model is schema vocabulary but unsupported by the accepted
runtime authorization architecture.

Result: `ApplyConflict` with `validation_failed`, no `TransitionEvent`, and no
domain evaluation when the authoritative binding prerequisite failed.

### 3. Other Apply Conflicts

Examples include stale or wrong writer session, idempotency key reuse with a
different command digest, expected-version conflict, and work item not found at
the authoritative store boundary.

Result: `ApplyConflict`, no `TransitionEvent`.

Expected-version mismatch is an apply conflict. It is not a domain rejection
and creates no domain event.

### 4. Durable Domain Rejection

Examples include invalid predecessor, unsupported or blocked authorization,
global stop, P1 `stage_not_enabled`, dependency failure, budget failure, and
missing required evidence. Within domain evaluation, unsupported target state
precedes the invariant P1 stage gate. For a valid bound command targeting a
P1-disabled stage, `stage_not_enabled` precedes lease-runtime, global-stop,
terminal, predecessor, authorization, dependency, evidence, budget, attempt,
and repair-limit reasons.

Result: `TransitionEvent` with `outcome=domain_rejected`. Current state remains
unchanged, and the unchanged current state plus event are persisted atomically.
The event still carries the complete authoritative context provenance,
including the nested `LeaseRuntimeDecision`; provenance fields do not override
the invariant P1 authority reason.

### 5. Committed Acceptance

Result: `TransitionEvent` with `outcome=accepted`. Next state and event are
persisted atomically.

### 6. Exact Replay

Preconditions: valid active writer session, same idempotency key, and same
canonical command digest.

Result: original committed state and event with `replayed=true`. No new event,
counter change, budget effect, or state mutation occurs.

## Invariants

- The event is the receipt.
- Transition events carry lease-identity, authorization, dependency,
  lease-runtime, and global-stop provenance fields.
- Event sequence and SQL `created_at` are operational metadata. SQL
  `created_at` is not independently hashed as a column, but it must equal the
  event's integrity-bound `lease_runtime.evaluated_at` timestamp. Event digest
  and event identity cover that semantic runtime timestamp through the event
  JSON.
- Replay `WorkItemRecord` snapshots exclude SQLite `updated_at`.
- No separate result reason can disagree with event reason.
- Apply conflicts never carry events.
- Durable domain rejections always carry events.
- P1-disabled targets always reject with `stage_not_enabled` after pre-apply
  binding and target-support checks but before contextual domain reasons.
- Caller code never provides proposed state or proposed event.
- Writer sessions are apply authority only and are not part of command identity.
- State version and event identity are not conflated.
- Global-stop updates use the same command/event/conflict/outcome algebra.
