# Operational Progression Boundary

## 1. Status And Purpose

Status: target contract/design record only. This document records an accepted
strategic target for bounded operational-change progression. It does not
implement operational progression, change coding-work runtime behavior, or
authorize any effect.

The target says Coordinator may later become the sole component-level durable
progression authority for governed programs admitted to its target operating
model through a conceptual shared owner-neutral progression kernel and
separately versioned software-development and bounded operational-change domain
contracts.

## 2. Current Non-Implementation Reality

Current implementation remains coding-work-specific bounded durable SQLite
mutation authority only. Current `WriterSession` issuance/fencing,
transition/global-stop mutation, receipt verification, idempotency, CAS, exact
replay, rollback, one COMMIT attempt, commit uncertainty, and retry remain
current coding facts. The public `StateStore` remains unwidened.

Current finite backlog, coding lease, transition, dependency, repair, budget,
disabled-stage, and coding `global_stop` contracts remain current implementation
facts. Coordinator currently has no operational-change domain model,
operational schema, worker, scheduler, queue consumer, dispatcher,
service/API/IPC, ES handoff, operational observation ingest, repair executor,
bootstrap executor, publication path, or live operational effect. Reports remain
projections and do not become authority or truth.

## 3. Bounded Operational-Change Domain Definition

A bounded operational-change program is one finite objective to change, repair,
roll back, compensate, contain, bootstrap, or recover a named target under:

- immutable owner action-contract reference;
- immutable externally issued authority reference;
- explicit target and desired-generation references;
- source-attributed preconditions and observations;
- finite attempt/effect ceilings;
- explicit acceptance, stop, and operator-intervention conditions.

It is not:

- a global desired-environment object;
- a continuous drift reconciler;
- a deployment platform;
- a topology controller;
- a capability registry;
- a scheduler;
- an effect engine;
- a source of host/process/systemd/Docker/Nomad/Vault/SPIRE/certificate truth;
- a broad shell/SSH/sudo/helper lane;
- hidden progression in MA, IM, Bridge, CP, chat, reports, or artifacts.

## 4. Shared Owner-Neutral Mechanics Versus Domain-Specific Semantics

Conceptual owner-neutral mechanics may include:

- program, operation, attempt, and effect-intent identity slots;
- durable intent before external I/O;
- idempotent command/ack handling;
- CAS, fencing, replay, and restart recovery;
- source-attributed observation bindings;
- explicit unknown/ambiguous outcomes;
- scoped stop and cancellation intent;
- acceptance, repair, rollback, compensation, containment, blocked, and
  operator-intervention decisions.

This list is conceptual. It creates no schema, module, service, queue, worker,
scheduler, reconciler, or source package. It does not make current coding source
a generic kernel.

Software-development and bounded operational-change domains must not share one
undifferentiated backlog, lease, work-item/state vocabulary, retry/repair
counter, dependency receipt model, global-stop singleton, acceptance grammar,
effect vocabulary, or publication/completion rule.

## 5. Identity And Correlation Non-Collapse

These identities may be explicitly correlated but do not collapse:

- Coordinator program/objective ID;
- semantic operation ID;
- attempt ID;
- effect-intent ID;
- external authority ID;
- owner action-contract ID/version;
- owner invocation/effect-engine task ID;
- ES reliable-submit key;
- ES `run_id`;
- `lifecycle_projection.revision`;
- retained-result/evidence reference;
- provider/runtime fact ID;
- observation ID/revision;
- CP workflow/run/attempt ID;
- Bridge/session/assignment/report ID;
- request/trace/transport/correlation ID.

External IDs and delivery references are safe correlation material only when
their owner permits retention. They do not become Coordinator semantic identity,
runtime truth, or authorization.

## 6. Safe References And Private Material

Coordinator may retain safe opaque references and redacted observation summaries
needed for bounded correlation and progression decisions. Raw credentials, keys,
biometric material, TLS/SPIFFE/Vault/WebAuthn/Codex/OpenAI/API-key material,
private environment files, unrestricted logs, support-bundle bodies, retained
bundle bodies, and private paths/endpoints remain outside Coordinator
durable/public state.

Persistence, reports, Bridge ledgers, IM profiles/bundles, MA proposals, CP
projections/messages, `.out`, retained bundles, trace IDs, request IDs, delivery
receipts, and adapter/session records do not become truth by storage.

## 7. External Operational Authorization

Coordinator may verify and bind allowlisted immutable authority references.
Coordinator may not mint, renew, widen, translate, reinterpret, or
self-supersede operational authority. A digest proves byte identity only.
Owner-blocked routes remain blocked.

This document selects no issuer, verifier, trust root, representation, wire
format, credential form, revocation mechanism, or custody topology.

Any future grant must be externally issued, immutable by Coordinator,
owner/route/target/effect scoped, attempt/effect bounded,
activation/expiry/revocation/freshness aware, and explicit about repair,
rollback, compensation, containment, bootstrap, and operator-intervention
coverage.

CP WebAuthn and MA biometric/lease designs are not adopted as the general
operational authorization model.

## 8. Owner Action-Contract References

The owner contract, not Coordinator, defines:

- route/action identity/version;
- supported target kind;
- immutable inputs;
- eligibility;
- preconditions;
- privilege/runtime-profile/identity/secret/signing requirements;
- effect semantics;
- idempotency/re-entry;
- delivery retry and semantic retry;
- post-check/acceptance inputs;
- repair/rollback/compensation/containment/manual-recovery behavior;
- privacy, redaction, receipts, and evidence retention.

Coordinator target decisions may bind the owner action-contract reference and
evaluate progression against admitted owner-source observations. Binding a
reference does not transfer owner-route meaning or privilege to Coordinator.

## 9. Source Observations, Freshness, Conflict, And Unknown Outcomes

Operational observations require source owner/version, observation ID/revision,
target, observed generation/state, related operation/attempt/effect/run
reference, observation time, receipt time, authenticity/integrity mechanism,
owner-specific freshness, semantic class, safe evidence reference, and redaction
class.

Missing, stale, unverifiable, target-mismatched, conflicting, late-unbound, or
inconclusive evidence remains unknown or blocked. It must not be converted into
success, failure, acceptance, rollback completion, compensation completion, or
containment completion by inference.

## 10. Required Progression Distinctions

Operational progression must distinguish desired target generation, admitted
owner action, durable effect intent, delivery acknowledgement, runtime/provider
observation, post-check observation, acceptance decision, blocked decision,
operator-intervention decision, and stop/cancellation intent.

No observation, delivery receipt, trace, request ID, report, or retained bundle
advances desired state without Coordinator evaluation under the admitted domain
contract.

## 11. Delivery Retry, Semantic Retry, Repair, Rollback, Compensation,
Containment, And Manual Recovery

The effect taxonomy distinguishes:

- delivery retry;
- semantic retry;
- repair;
- rollback;
- compensation;
- containment;
- manual recovery/operator intervention.

Delivery retry is transport-level re-entry for the same durable effect intent.
Semantic retry is a new Coordinator progression decision. Repair, rollback,
compensation, containment, cancellation, and bootstrap are separate effect
families, not generic success paths.

Every repair, rollback, compensation, containment, cancellation, and bootstrap
effect requires its own durable effect intent before I/O, appropriate external
authority, owner action-contract reference, source observation, and separate
acceptance/containment rule.

## 12. Operational Domain And Named-Target Scoped Stop

Current coding `global_stop` remains untouched. The first operational stop
target is operational-domain and named-target scoped. Exact storage and
precedence remain open.

A stop intent or cancellation receipt does not prove termination. Runtime
termination remains a source-owned observed fact. Cross-domain emergency
super-stop remains open and non-implemented.

## 13. Owner-Exposed Dependency Vocabulary

Owner contracts may expose dependency vocabulary for the operational domain,
including owner-source prerequisites, target generation prerequisites,
authorization prerequisites, runtime-profile prerequisites, safety prerequisites,
and validation/post-check prerequisites.

This document does not reuse the current coding dependency receipt model as the
operational dependency model and does not select a universal dependency grammar.

## 14. ES Reliable-Submit Future Gate

Reliable operational effects through ES are future-only. ES must independently
authenticate, default, validate runtime profile, admit, reliably
correlate/recover submit, own runtime handoff/lifecycle/cancel request/retained
result, and preserve its boundary. Operational acceptance remains separate.
Current reliable-submit target docs/model/ADR do not mean implementation.

Forbidden substitutes include current unkeyed submit plus blind retry,
Coordinator Nomad scraping, Bridge/session/report correlation as recovery truth,
trace/request IDs as submit identity, provider IDs as semantic attempt identity,
and parallel Coordinator or adapter lifecycle truth.

## 15. Bootstrap And Catastrophic-Recovery Exception Requirements

A bootstrap or catastrophic-recovery label is not permission.

A future exception must name:

- exact owner/component;
- exact route/action/version;
- immutable target/action/config reference;
- target;
- program/operation/attempt/effect identities;
- immutable external authority;
- privacy/custody boundary;
- preconditions;
- bounded action;
- idempotency/re-entry;
- backup;
- post-check;
- rollback/compensation/containment/manual recovery;
- safe receipt where available;
- explicit ambiguous/unknown outcome;
- later owner-source reconciliation;
- no success without positive owner post-check.

It must not authorize broad shell, SSH, sudo, arbitrary helper dispatch,
credential brokerage, hidden reconciliation, or route widening.

## 16. Sensors May Propose But Not Reconcile

Sensors, probes, reports, Bridge sessions, MA scans, IM diagnostics, CP
projections, CI results, and owner-system observations may propose evidence or
candidate progression inputs. They do not reconcile operational state, advance
desired state, clear stops, accept effects, or close unknown outcomes by
themselves.

## 17. Gateway And Adapter Placement Alternatives

All three placement alternatives remain open:

- in-process Coordinator adapter;
- explicitly widened Bridge adapter after separate owner-repo work/audit;
- separate stateless gateway.

This document selects none of them. Placement-specific mechanics must remain
bounded to protocol translation, ephemeral invocation/session correlation,
redaction, and evidence shaping. They must not own durable progression,
scheduling, retry, repair, acceptance, ES admission, runtime lifecycle truth,
Git truth, validation truth, or hidden program state.

## 18. Required-Before-Source Gates

Before source, schema, service, worker, adapter, gateway, effect-engine,
bootstrap, or runtime work, a later tranche must pin:

- operational domain version and target state vocabulary;
- owner action-contract reference format;
- external authority reference format and verification boundary;
- safe-reference and private-material policy;
- observation authenticity, freshness, conflict, and unknown-state handling;
- effect-intent, retry, repair, rollback, compensation, containment, and manual
  recovery semantics;
- operational stop storage and precedence;
- ES reliable-submit integration contract or explicitly bounded exception;
- gateway/adapter placement decision;
- independent audit and provenance.

## 19. Explicit Non-Claims

This document and tranche add:

- no current operational implementation;
- no source model;
- no schema or migration;
- no worker/scheduler/dispatcher/reconciler;
- no service/API/IPC;
- no outbox/inbox;
- no ES call;
- no Bridge widening;
- no selected gateway;
- no authorization issuer or verifier implementation;
- no observation transport;
- no stop storage;
- no bootstrap executor;
- no effect engine;
- no first route;
- no privileged host action;
- no MA/IM migration decision;
- no production topology;
- no continuous drift loop;
- no current reliable ES operational dispatch.

## 20. Open Decisions

The following decisions remain open:

1. bounded operational-change domain versioning and exact boundary;
2. external authorization issuer;
3. verifier and trust root;
4. grant representation and wire format;
5. credential form and custody topology;
6. exact operational state vocabulary;
7. schema and storage;
8. observation transport and reconciliation path;
9. stop storage and precedence;
10. cross-domain emergency super-stop;
11. ES reliable-submit implementation details;
12. bootstrap or catastrophic-recovery route;
13. repair, rollback, compensation, containment, and manual-recovery semantics;
14. first owner route/action;
15. gateway or adapter placement;
16. effect engine implementation or explicit no-engine decision;
17. MA/IM survival, migration, or retirement;
18. production topology.

## 21. Relationship To The Coding-Specific Worker Execution Boundary

The Worker Execution Boundary remains coding-specific and unchanged. This
operational boundary may derive owner-neutral invariants such as durable intent
before external I/O, idempotent delivery/observation handling, external IDs as
references only, and placement neutrality.

Coding work identity, coding attempt identity, dispatch command identity, worker
attempt identity, ES runtime identity, backlog, coding lease, transition grammar,
dependency receipt model, retry/repair counters, schema, and coding `global_stop`
are not operational identities or universal operational contracts. No current
coding schema, backlog, lease, transition, or `global_stop` is generalized by
this document.
