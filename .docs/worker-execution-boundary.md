# Worker Execution Boundary

## Status And Purpose

Status: target contract/design record only. This document enables no runtime
implementation, no wire schema, no transport, and no placement.

The Worker Execution Boundary is the reserved, transport-neutral boundary
between Coordinator-owned durable development progression and Execution
Substrate-owned execution admission and runtime lifecycle authority. This
document records strategic target direction and required invariants for future
work. It is not evidence that dispatch, worker execution, ES submission, result
ingest, or an autonomous loop exists.

This tranche selects no final schema, table, queue, service, IPC, public API,
polling model, callback model, runtime profile, Codex protocol, adapter
placement, gateway service, Development Program, or append-only event-sourcing
architecture.

## Current Implementation Reality

Coordinator currently owns bounded internal durable SQLite mutation authority for
coding-work state. Current internal SQLite `WriterSession` behavior includes
durable writer issuance, fencing, transition persistence, global-stop
persistence, verification of already-persisted operator-decision receipts,
idempotency and exact replay, accepted-current CAS, rollback, one COMMIT
attempt, commit uncertainty, and explicit retry.

The public `StateStore` remains unwidened. Internal `WriterSession` mutation is
not a general public `StateStore` backend, service, API, worker loop, dispatcher,
or runtime integration.

Coordinator currently has no worker, scheduler, queue consumer, dispatcher,
reconciler, public service/API, Codex invocation, Execution Substrate handoff,
runtime-profile integration, result-ingest path, repair executor, publication
path, autonomous loop, dispatch command identity, worker attempt identity,
adapter invocation identity, ES run identity, Codex process/session identity,
outbox/inbox state, retained-result reference, or cancellation acknowledgement.

Current P1 worker, validation, audit, repair, commit, and cleanup lifecycle
names remain declared contract vocabulary with invariant `stage_not_enabled`
behavior. Those state names do not prove runtime implementation.

Execution Substrate currently owns execution admission, prepare and submit
handoff, runtime-profile compatibility, runtime identity and credential-handoff
boundaries, Nomad-backed lifecycle projection, runtime cancellation-request
boundaries, and retained execution results.

Bridge is currently a guarded adapter, transport, redaction, local-proof, and
evidence surface. Bridge is not durable program authority, runtime lifecycle
truth, work-selection authority, scheduling policy, retry/repair authority,
acceptance authority, or hidden Coordinator state.

Control Plane remains relevant only to current maintained MVP/demo
compatibility, migration, filming, freeze, reference, or retirement context. It
is not part of the target autonomous-development topology in this document.

## Target Topology

The strategic target topology is:

```text
reasoning model
    -> Coordinator
    -> Worker Execution Boundary
    -> [in-process adapter | widened Bridge adapter | separate stateless gateway]
    -> Execution Substrate
    -> ES-owned runtime backend
    -> worker
```

Model reasoning owns cognitive intent, architectural judgment, semantic
judgment, planning, replanning, and evidence review. Model sessions and model
responses are not durable program truth by themselves.

Coordinator is intended to become the durable autonomy core for software
development progression. Execution Substrate continues to own execution
admission and runtime authority. Git owns repository object and ref truth. CI or
validating runtimes own observed validation results.

Direct local Codex execution outside Execution Substrate may exist only as an
explicitly named bootstrap or proof edge. It must not silently become the target
execution path.

## Desired Development State Versus Observed Execution Facts

Coordinator-owned target facts are desired development facts. External facts are
observations or receipts owned by their source system. Coordinator may retain
safe references and bounded observations needed for correlation and
decision-making. Retaining a reference does not transfer ownership of the
external fact.

Coordinator-owned target facts include:

- semantic attempt identity;
- desired progression;
- durable dispatch intent;
- retry or repair decision;
- cancellation intent;
- reconciliation decision;
- evidence requirements;
- evidence bindings;
- global-stop effect planning;
- acceptance progression;
- governed advancement toward allowed Git or publication effects.

Externally owned facts include:

- ES admission decision;
- ES `run_id`;
- ES/Nomad lifecycle observation;
- ES cancel-request receipt;
- terminal runtime observation;
- retained-result reference;
- adapter invocation/session reference;
- Git object/ref identity;
- validation observation.

External runtime identifiers may be correlation references, but they are not
semantic work identity and do not become Coordinator runtime authority.

## Placement-Neutral Dispatch Semantics

A future Worker Execution Boundary requires, without freezing final field names,
schemas, tables, public endpoints, or transports:

- semantic attempt identity;
- dispatch command identity;
- canonical command digest;
- work item and optional future program correlation;
- repository and base Git identity;
- policy or authorization references;
- global-stop reference;
- evidence requirements;
- idempotent delivery acknowledgement;
- idempotent observation ingest;
- duplicate, lost, late, stale, and ambiguous outcome handling.

Transport redelivery is not a new semantic attempt. A new semantic attempt
requires a Coordinator decision.

## Effect And Transaction Ordering

External I/O does not occur inside the SQLite mutation transaction. A
recoverable durable effect intent must exist before an external dispatch effect
is attempted.

Delivery acknowledgement is not runtime admission. An ES submit receipt is not
semantic work acceptance. An unknown dispatch outcome remains unknown until it is
reconciled. Observations cannot silently advance desired state without
Coordinator evaluation.

An outbox/inbox is a likely implementation candidate for durable effect intent
and observation ingest. This document does not freeze outbox/inbox as mandatory.
Exact persistence, table, queue, delivery, polling, callback, service, and IPC
mechanics remain open. Equivalent designs must satisfy the same recovery and
authority invariants.

## ES Submit Ambiguity

The current ES public submit contract returns an internally generated `run_id`
after successful submit. The current public contract does not expose a
caller-supplied submit idempotency key, dispatch command identity, or
query-by-dispatch-command recovery path.

An accepted submit whose response is lost can therefore be ambiguous to a
caller. Coordinator must not compensate by inventing a second ES lifecycle store,
scraping Nomad as Coordinator authority, treating trace/request IDs as recovery
authority, or storing a parallel submitted-execution lifecycle truth.

ES submit ambiguity is a blocker to reliable real dispatch. Reliable real
dispatch requires an ES-owned idempotency, correlation, or recovery decision, or
an explicitly bounded bootstrap exception. This Coordinator document does not
define that ES contract.

## Cancellation And Global Stop

Coordinator owns semantic cancellation intent and global-stop effect planning.
Execution Substrate owns the runtime cancellation-request boundary.

An ES cancel receipt proves request acceptance, not terminal stop. Terminal
cancellation is learned through ES-owned lifecycle observation.

Global stop prevents new semantic dispatch and retry/repair progression. Active
work cancellation attempts must be recorded as effects and observations without
falsely claiming runtime termination.

This tranche implements no cancellation propagation and no global-stop runtime
propagation.

## Restart And Recovery

Before real dispatch, pending dispatch intent must be discoverable after
restart. Acknowledged but uncorrelated effects must remain reconcilable.
Duplicate acknowledgement and duplicate observation must be idempotent. Late
observations must be bound to the intended semantic attempt. Stale observations
must not overwrite newer Coordinator decisions. Ambiguous outcomes must not be
converted into success or failure by inference.

This document does not choose polling versus callback, a service, local IPC, a
queue, or an exact database representation.

## Placement Alternatives

The Worker Execution Boundary keeps all three placement alternatives open:

- in-process Coordinator adapter;
- explicitly widened Bridge adapter;
- separate stateless gateway.

Placement is a deployment and implementation decision after placement-neutral
contracts exist. A separate gateway is not justified merely for conceptual
neatness. A widened Bridge adapter must consume an already defined Coordinator
command port and ES-owned runtime contracts; it must not define durable
progression, scheduling, retry, repair, acceptance, or lifecycle truth.
Bridge is not selected as mandatory adapter placement by this tranche.

## Private Material And Safe Projections

Public reports must not contain raw prompts, raw Codex JSONL, raw logs,
credentials, trust material, local absolute paths, private endpoints, retained
bundles, or arbitrary runtime payloads.

Coordinator may retain safe opaque references to external observations when
needed for correlation and decision-making. Retained bundles remain ES-owned
opaque results. Raw/private context-package or worker-input storage is not
decided by this tranche and requires a separate privacy/security contract.

## Explicit Non-Claims

This document and tranche add:

- no worker or Codex invocation;
- no scheduler;
- no dispatcher or reconciler;
- no service/API/IPC;
- no schema or migration;
- no outbox/inbox implementation;
- no ES call;
- no Bridge widening;
- no selected gateway service;
- no connector dependency;
- no Development Program prerequisite;
- no full event-sourcing decision;
- no direct-local-Codex target path;
- no runtime-profile selection;
- no authority issuance implementation;
- no publication behavior.

## Required-Before-Real-Dispatch Gates

These are local gates, not one global project sequence:

- Coordinator semantic identity and command contract;
- durable effect-intent and observation contract;
- authorization or policy reference contract;
- ES submit idempotency, correlation, or recovery decision;
- cancellation and global-stop effect semantics;
- safe read projections;
- adapter implementation;
- independent audit and provenance.

## Open Seams

The following target seams remain open:

- exact attempt model;
- relationship to current finite backlog and lease;
- authority issuer and standing-policy representation;
- exact outbox/inbox or equivalent design;
- schema;
- polling versus callback;
- service or local IPC;
- adapter placement;
- Codex CLI versus App Server;
- runtime profile;
- first bounded bootstrap exception;
- raw/private context retention.
