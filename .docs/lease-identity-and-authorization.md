# Lease Identity And Authorization

The standing lease schema id is:

`governed-execution.nwp-standing-lease.v1`

The identity contract includes schema/version, lease id, issuer label,
issuance time, valid-from, expiry, revocation state/reference, subject, repo
identity, branch policy, allowed paths, forbidden-path policy identity, task
classes, risk lanes, finite backlog reference/digest, max work items, max
concurrency, max attempts, max repairs, compute/API budget, wall-clock budget,
validation requirements, audit requirements, local-commit permission,
publication permission, cross-repo permission, maintenance permission, cleanup
requirements, reporting cadence, retention policy, global-stop reference,
canonical-digest metadata, and authorization-mechanism descriptor.

Canonicalization uses UTF-8 JSON, sorted object keys, compact separators, and
deterministic primitive encoding. Ordered arrays preserve caller order.
Explicitly set-like string arrays reject duplicates and are sorted
lexicographically. The digest is SHA-256 over the canonical identity payload.

Identity validation proves only:

- schema validity;
- canonical form;
- digest match;
- time-window shape;
- bounded field shape;
- finite-backlog binding shape.

Identity validation never returns executable authorization. The production
authorization boundary is separate and fail-closed because no issuer trust,
verifier trust root, signing authority, key owner, custody model, or
alternative operator-local authorization mechanism is selected in P1.

Production code must contain no allow-all provider, local-dev bypass,
environment-variable bypass, unsigned-fixture execution path, or implicit
trusted-local authority.
