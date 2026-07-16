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

Writer-session authority is mutation fencing contract shape only until a
future backend tranche implements it. B2a removes standalone reconstructable
public-token mutation authority: mutation authority belongs to an opaque future
`WriterSession`, not to safe writer metadata or a durable SQLite row. P1/P1.1
and B2a do not acquire, renew, persist, or honor a production writer session.
Stale-writer conflicts are apply-boundary failures and never disclose
idempotency status or return transition events. Closed-session and
process-mismatch failures are session-local failures before the apply boundary;
they are not durable apply conflicts.

Transition events are durable receipts for future accepted or domain-rejected
commands. Apply conflicts are not receipts and do not provide acceptance,
authorization, publication, or product truth.

B1 SQLite bootstrap and migration operations are operator-local administrative
schema operations. They do not create work-item authority, global-stop update
authority, authorization receipts, executable permission, acceptance, commit,
publication, or product truth.

B2a writer-session contract objects do not create work-item authority,
global-stop update authority, executable authorization, acceptance, commit,
publication, product truth, or process liveness truth. Safe writer metadata is
diagnostics/evidence only and cannot reconstruct a private writer credential.

Coordinator P1 reports are closed typed public projections. They cannot widen
authority, cannot mutate state, and cannot carry raw private content,
endpoints, local paths, platform identifiers, credentials, trust material, or
execution claims.
