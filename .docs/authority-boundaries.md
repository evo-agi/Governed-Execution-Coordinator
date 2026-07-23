# Authority Boundaries

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

Bridge remains worker/evidence adapter only. Bridge ledgers and reports are
evidence/projection and never become Coordinator durable state.

Control Plane remains product workflow authority and does not become A2
coding-work state owner.

Execution Substrate remains product admission/runtime authority and does not
delegate ES route, TLS, lifecycle, or runtime truth to the Coordinator.

Maintenance Agent remains maintenance authority. Maintenance leases and coding
leases are separate namespaces and are not interchangeable.

Infrastructure Manager remains readiness, provenance, profile, diagnostics,
and support-bundle authority. Its outputs are not Coordinator state truth.

Reports, ChatGPT state, connector state, API sessions, Symphony, and adapter
evidence do not create durable A2 state, lease authority, execution authority,
acceptance, commit authority, or publication authority. A report or adapter
projection does not create durable A2 state.

Writer-session authority is mutation fencing contract shape plus B2c internal
SQLite acquisition. B2a removes standalone reconstructable public-token
mutation authority: mutation authority belongs to an opaque backend-created
`WriterSession`, not to safe writer metadata or a durable SQLite row. B2c
acquires an internal session for a managed database. B3c4c makes public
`WriterSession.apply_transition(command)` delegate through the existing
operation guard to the B3c4b private atomic transition entry. The public wrapper
does not own SQL, transaction control, event or current-state writes, sequence
allocation, context assembly, evaluator invocation, capability construction, or
mutation-slot acquisition. Public `apply_global_stop_update()` still fails
locally with `writer_session_mutation_unavailable`; B4a adds only prerequisite
global-stop contracts, transaction-internal readers with no production caller,
and pure/static write grammar. It does not provision operator-decision
receipts, execute a mutation, begin or commit a transaction, or add public
global-stop delegation. Receipt provisioning remains a separately governed
operator/repo-policy integration seam. Stale
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
