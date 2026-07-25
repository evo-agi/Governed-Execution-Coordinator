# Authority Boundaries

## Current Authority

The NWP Coordinator cannot self-authorize. A valid lease digest proves only
schema validity, canonical form, digest match, time-window shape, bounded field
shape, and finite-backlog binding shape. It does not prove authorization or
executability.

The production/default authorization provider is unsupported and fail-closed.
It returns `authorized=false`, `executable=false`, and
`unsupported_authorization_model`. Typed authorization decisions may represent
external operator/repo policy truth, but P1/P1.1 implements no executable
authorization provider and no trusted-local bypass.

B3a does not add authorization verification. It aligns
`AuthorizationDecision` with schema 0001 by binding it to
`lease_identity_decision_ref`, keeps `unsupported` as the only current
production posture, requires internally coherent authorization flags and
reasons, and classifies `operator_policy` as unsupported by the accepted
runtime architecture until a separate authorization contract exists.

Bridge remains worker/evidence adapter only in current implementation reality.
Bridge ledgers and reports are evidence/projection and never become Coordinator
durable state, lifecycle truth, retry/repair authority, scheduling policy,
acceptance, or hidden program state.

Control Plane remains relevant only to current maintained MVP/demo
compatibility, migration, filming, freeze, reference, or retirement context. CP
does not become A2 coding-work state owner and is not part of the target
autonomous-development topology.

Execution Substrate remains execution admission/runtime authority and does not
delegate ES route, TLS, lifecycle, runtime-profile compatibility, runtime
identity, credential-handoff boundaries, runtime cancellation request, retained
results, or runtime truth to the Coordinator.

Maintenance Agent remains maintenance authority. Maintenance leases and coding
leases are separate namespaces and are not interchangeable.

Infrastructure Manager remains readiness, provenance, profile, diagnostics,
and support-bundle authority. Its outputs are not Coordinator state truth.

Reports, ChatGPT state, connector state, API sessions, Symphony, and adapter
evidence do not create durable A2 state, lease authority, execution authority,
acceptance, commit authority, or publication authority. A report or adapter
projection does not create durable A2 state.

## Strategic Target Fact Ownership

Coordinator is intended to become the durable autonomy core for software
development progression. Target Coordinator ownership includes durable desired
development progression, semantic work and attempt identity, work selection,
durable dispatch intent, retry and repair decisions, cancellation intent,
global-stop effect planning, evidence requirements and bindings, restart
reconciliation decisions, acceptance progression, and governed advancement
toward allowed Git or publication effects.

Execution Substrate continues to own execution admission, runtime-profile
compatibility, prepare and submit handoff, runtime identity and
credential-handoff boundaries, submitted execution lifecycle projection, runtime
cancellation request boundaries, and retained execution results. Git owns
repository object and ref truth. CI or validating runtimes own observed
validation results.

The Worker Execution Boundary is the reserved transport-neutral boundary between
Coordinator-owned durable development progression and ES-owned runtime
authority. A worker adapter, widened Bridge adapter, or future gateway may own
only bounded placement-specific protocol mechanics, request translation, Codex
CLI or App Server protocol handling, local IPC or transport mechanics,
ephemeral adapter invocation/session correlation, and bounded redaction/evidence
shaping. It must not own durable work selection, scheduling policy, semantic
retry or repair authority, acceptance, ES admission, runtime lifecycle truth,
Git truth, validation truth, or hidden program state.

Model reasoning owns cognitive intent and architectural or semantic judgment.
Model sessions and model responses are not durable program truth by themselves.
The user is not a routine per-task approval service. Connector availability and
a first-class Development Program are not prerequisites for the Worker Execution
Boundary. Full append-only event sourcing is not selected or required by this
tranche.

## Evidence And References Versus Authority

Coordinator may retain safe opaque references and bounded observations needed
for correlation and decision-making. Retaining an ES `run_id`, adapter
invocation reference, Git ref, validation reference, or retained-result
reference does not transfer ownership of the external fact to Coordinator.

The current ES submit contract exposes an internally generated `run_id` after a
successful submit but does not expose caller-supplied submit idempotency or a
query-by-dispatch-command recovery contract. Reliable real dispatch requires an
ES-owned idempotency, correlation, or recovery decision, or an explicitly
bounded bootstrap exception. Coordinator must not compensate by inventing a
second ES lifecycle store, scraping Nomad as its own authority, or treating
trace/request IDs as recovery authority.

External I/O must not occur inside the SQLite mutation transaction boundary. A
recoverable durable effect intent must exist before an external dispatch effect
is attempted. Delivery acknowledgement is not runtime admission. An ES submit
receipt is not semantic work acceptance. Transport redelivery is not a new
semantic attempt; a new semantic attempt requires a Coordinator decision.

Writer-session authority is mutation fencing contract shape plus B2c internal
SQLite acquisition. B2a removes standalone reconstructable public-token
mutation authority: mutation authority belongs to an opaque backend-created
`WriterSession`, not to safe writer metadata or a durable SQLite row. B2c
acquires an internal session for a managed database. B3c4c makes public
`WriterSession.apply_transition(command)` delegate through the existing
operation guard to the B3c4b private atomic transition entry. The public wrapper
does not own SQL, transaction control, event or current-state writes, sequence
allocation, context assembly, evaluator invocation, capability construction, or
mutation-slot acquisition. B4c guarded public global-stop delegation exists:
public `apply_global_stop_update()` enters the same operation guard, performs
bounded function-local loading, maps the exact private global-stop preflight
vocabulary to the public vocabulary, and delegates once to B4b private atomic
global-stop persistence. B4a defines
receipt/read/event/replay/sequence/write contracts, and B4b implements private
atomic global-stop persistence without provisioning operator-decision receipts.
B4c adds no SQL, receipt verification, evaluator, sequence, write, rollback, or
commit ownership to `WriterSession`. Receipt provisioning remains a
separately governed operator/repo-policy integration seam, and no public,
orchestration, worker, service, connector, CLI, or cross-repository authority is
added. Stale
writer conflicts are private apply-boundary failures and never disclose
idempotency status or return transition events. Closed-session and
process-mismatch failures are session-local failures before the apply boundary;
they are not durable apply conflicts.

B3a changes the transition method shape to `apply_transition(command)` and
requires future transition context to be reconstructed inside the fenced store
boundary. It adds canonical event/replay contracts, including integrity-bound
lease-runtime status and evaluation time in `TransitionEvent`, and safe
mutation-store error classes only. It does not create admission, executable
authorization, SQLite transition mutation, global-stop mutation, service,
worker, repair, commit, publication, or related-repo authority.

Transition events are durable receipts for accepted or domain-rejected commands
only after B3c4b private atomic commit succeeds. Apply conflicts are not
receipts and do not provide acceptance,
authorization, publication, or product truth.

B1 SQLite bootstrap and migration operations are operator-local administrative
schema operations. They do not create work-item authority, global-stop update
authority, authorization receipts, executable permission, acceptance, commit,
publication, or product truth.

B2b's state-authority lock is live-process exclusion for initialize/migrate and
B2c writer acquisition. It is not writer authority by itself, not a credential,
not durable state, and not a substitute for private-proof writer fencing.

B2a/B2c writer-session contract objects do not create work-item authority,
global-stop update authority, executable authorization, acceptance, commit,
publication, product truth, or process liveness truth. Safe writer metadata is
diagnostics/evidence only and cannot reconstruct a private writer credential.

Coordinator P1 reports are closed typed public projections. They cannot widen
authority, cannot mutate state, and cannot carry raw private content,
endpoints, local paths, platform identifiers, credentials, trust material, or
execution claims.
