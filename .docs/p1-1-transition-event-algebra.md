# P1.1 Transition Event Algebra

A2-P1.1 defines contract objects for a future atomic state backend. It does
not select or implement that backend.

The P1.1 model has one durable outcome record for each committed transition:
the event. The event is the receipt. Caller code never supplies a proposed
state, proposed event, or proposed receipt.

## Responsibility Owners

The parser and model layer owns closed-world parsing, duplicate JSON object key
rejection, scalar and identifier validation, canonical command identity, and
typed decision and context validation. It rejects malformed values before a
store apply call.

External versioned inputs are exact-shape and non-coercing. Collection fields
must verify their external JSON-array/Python-list shape before element
validation, normalization, canonicalization, or digest verification. Malformed
array-like input must not be canonicalized into an accepted command identity.

The atomic apply boundary owns writer fencing, internal idempotency lookup,
authoritative current-state loading, expected-version comparison, pure
evaluator invocation, atomic state/event persistence, and exact replay.

The pure evaluator owns domain rules: predecessor rules, P1 stage availability,
typed lease and authorization decision effects, dependency rules, budget and
counter rules, global-stop domain effects, and construction of accepted or
domain-rejected events.

The report layer owns projection only. Reports do not mutate state, authorize
work, accept work, publish work, or become transition inputs.

## Failure Taxonomy

### 1. Pre-Apply Invalid Command

Examples include malformed schema or digest, unsafe identifiers or references,
wrong work-item addressing, broken decision binding, and cross-lease decision
mismatch.

Result: local safe validation failure, no event, and no store apply.

### 2. Apply Conflict

Examples include stale or wrong writer token, idempotency key reuse with a
different command digest, expected-version conflict, and work item not found at
the authoritative store boundary.

Result: `ApplyConflict`, no `TransitionEvent`.

Expected-version mismatch is an apply conflict. It is not a domain rejection
and creates no domain event.

### 3. Durable Domain Rejection

Examples include invalid predecessor, unsupported or blocked authorization,
global stop, P1 `stage_not_enabled`, dependency failure, budget failure, and
missing required evidence.

Result: `TransitionEvent` with `outcome=domain_rejected`. Current state remains
unchanged, and the unchanged current state plus event are persisted atomically.

### 4. Committed Acceptance

Result: `TransitionEvent` with `outcome=accepted`. Next state and event are
persisted atomically.

### 5. Exact Replay

Preconditions: valid current writer, same idempotency key, and same canonical
command digest.

Result: original committed state and event with `replayed=true`. No new event,
counter change, budget effect, or state mutation occurs.

## Invariants

- The event is the receipt.
- No separate result reason can disagree with event reason.
- Apply conflicts never carry events.
- Durable domain rejections always carry events.
- Caller code never provides proposed state or proposed event.
- Writer tokens are apply authority only and are not part of command identity.
- State version and event identity are not conflated.
- Global-stop updates use the same command/event/conflict/outcome algebra.
