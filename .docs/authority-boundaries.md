# Authority Boundaries

The NWP Coordinator cannot self-authorize. A valid lease digest proves only
schema validity, canonical form, digest match, time-window shape, bounded field
shape, and finite-backlog binding shape. It does not prove authorization or
executability.

The production/default authorization provider is unsupported and fail-closed.
It returns `authorized=false`, `executable=false`, and
`unsupported_authorization_model`.

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
