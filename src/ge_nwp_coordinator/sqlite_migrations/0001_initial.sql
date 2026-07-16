-- NWP Coordinator SQLite state schema migration 0001.
-- Status: B1 initial schema installation.
-- Connection settings are owned by sqlite_connection.py and are not part of
-- migration identity.

CREATE TABLE schema_migrations (
    migration_id TEXT PRIMARY KEY CHECK (length(migration_id) BETWEEN 1 AND 96),
    sequence INTEGER NOT NULL UNIQUE CHECK (sequence >= 0),
    schema_digest TEXT NOT NULL CHECK (
        length(schema_digest) = 64
        AND schema_digest = lower(schema_digest)
        AND schema_digest NOT GLOB '*[^0-9a-f]*'
    ),
    applied_at TEXT NOT NULL CHECK (length(applied_at) BETWEEN 20 AND 64),
    min_app_schema INTEGER NOT NULL CHECK (min_app_schema >= 0),
    max_app_schema INTEGER NOT NULL CHECK (max_app_schema >= min_app_schema)
);

CREATE TRIGGER schema_migrations_no_update
BEFORE UPDATE ON schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'append_only_schema_migrations');
END;

CREATE TRIGGER schema_migrations_no_delete
BEFORE DELETE ON schema_migrations
BEGIN
    SELECT RAISE(ABORT, 'append_only_schema_migrations');
END;

CREATE TABLE writer_ownership (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    writer_ref TEXT NOT NULL CHECK (length(writer_ref) BETWEEN 1 AND 96),
    generation INTEGER NOT NULL CHECK (generation >= 0),
    issued_ref TEXT NOT NULL CHECK (length(issued_ref) BETWEEN 1 AND 96),
    issuance_nonce_digest TEXT NOT NULL CHECK (
        length(issuance_nonce_digest) = 64
        AND issuance_nonce_digest = lower(issuance_nonce_digest)
        AND issuance_nonce_digest NOT GLOB '*[^0-9a-f]*'
    ),
    acquired_at TEXT NOT NULL CHECK (length(acquired_at) BETWEEN 20 AND 64)
);

CREATE TABLE lease_identity_records (
    decision_ref TEXT PRIMARY KEY CHECK (length(decision_ref) BETWEEN 1 AND 96),
    lease_ref TEXT NOT NULL CHECK (length(lease_ref) BETWEEN 1 AND 96),
    identity_valid INTEGER NOT NULL CHECK (identity_valid IN (0, 1)),
    lease_digest TEXT CHECK (
        lease_digest IS NULL OR (
            length(lease_digest) = 64
            AND lease_digest = lower(lease_digest)
            AND lease_digest NOT GLOB '*[^0-9a-f]*'
        )
    ),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-standing-lease.v1'),
    canonical_json TEXT NOT NULL CHECK (length(canonical_json) > 0 AND length(canonical_json) <= 1048576),
    canonical_digest TEXT NOT NULL CHECK (
        length(canonical_digest) = 64
        AND canonical_digest = lower(canonical_digest)
        AND canonical_digest NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 64)
);

CREATE TRIGGER lease_identity_records_no_update
BEFORE UPDATE ON lease_identity_records
BEGIN
    SELECT RAISE(ABORT, 'append_only_lease_identity_records');
END;

CREATE TRIGGER lease_identity_records_no_delete
BEFORE DELETE ON lease_identity_records
BEGIN
    SELECT RAISE(ABORT, 'append_only_lease_identity_records');
END;

CREATE TABLE authorization_decision_receipts (
    decision_ref TEXT PRIMARY KEY CHECK (length(decision_ref) BETWEEN 1 AND 96),
    lease_ref TEXT NOT NULL CHECK (length(lease_ref) BETWEEN 1 AND 96),
    lease_identity_decision_ref TEXT NOT NULL REFERENCES lease_identity_records(decision_ref),
    lease_identity_valid INTEGER NOT NULL CHECK (lease_identity_valid IN (0, 1)),
    authorization_model TEXT NOT NULL CHECK (authorization_model IN ('unsupported', 'operator_policy')),
    authorized INTEGER NOT NULL CHECK (authorized IN (0, 1)),
    executable INTEGER NOT NULL CHECK (executable IN (0, 1)),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 96),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-authorization-decision.v1'),
    canonical_json TEXT NOT NULL CHECK (length(canonical_json) > 0 AND length(canonical_json) <= 262144),
    canonical_digest TEXT NOT NULL CHECK (
        length(canonical_digest) = 64
        AND canonical_digest = lower(canonical_digest)
        AND canonical_digest NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 64),
    CHECK (
        authorization_model <> 'unsupported'
        OR (authorized = 0 AND executable = 0 AND reason = 'unsupported_authorization_model')
    )
);

CREATE TRIGGER authorization_decision_receipts_no_update
BEFORE UPDATE ON authorization_decision_receipts
BEGIN
    SELECT RAISE(ABORT, 'append_only_authorization_decision_receipts');
END;

CREATE TRIGGER authorization_decision_receipts_no_delete
BEFORE DELETE ON authorization_decision_receipts
BEGIN
    SELECT RAISE(ABORT, 'append_only_authorization_decision_receipts');
END;

CREATE TABLE admitted_backlogs (
    backlog_id TEXT PRIMARY KEY CHECK (length(backlog_id) BETWEEN 1 AND 96),
    lease_ref TEXT NOT NULL CHECK (length(lease_ref) BETWEEN 1 AND 96),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-finite-backlog.v1'),
    schema_version INTEGER NOT NULL CHECK (schema_version = 1),
    content_digest TEXT NOT NULL CHECK (
        length(content_digest) = 64
        AND content_digest = lower(content_digest)
        AND content_digest NOT GLOB '*[^0-9a-f]*'
    ),
    canonical_json TEXT NOT NULL CHECK (length(canonical_json) > 0 AND length(canonical_json) <= 1048576),
    admitted_at TEXT NOT NULL CHECK (length(admitted_at) BETWEEN 20 AND 64)
);

CREATE TRIGGER admitted_backlogs_no_update
BEFORE UPDATE ON admitted_backlogs
BEGIN
    SELECT RAISE(ABORT, 'append_only_admitted_backlogs');
END;

CREATE TRIGGER admitted_backlogs_no_delete
BEFORE DELETE ON admitted_backlogs
BEGIN
    SELECT RAISE(ABORT, 'append_only_admitted_backlogs');
END;

CREATE TABLE dependency_decision_receipts (
    decision_ref TEXT PRIMARY KEY CHECK (length(decision_ref) BETWEEN 1 AND 96),
    work_item_id TEXT CHECK (work_item_id IS NULL OR length(work_item_id) BETWEEN 1 AND 96),
    dependencies_satisfied INTEGER NOT NULL CHECK (dependencies_satisfied IN (0, 1)),
    reason TEXT NOT NULL CHECK (
        reason IN ('accepted', 'dependencies_not_satisfied')
        AND ((dependencies_satisfied = 1 AND reason = 'accepted')
            OR (dependencies_satisfied = 0 AND reason = 'dependencies_not_satisfied'))
    ),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-dependency-decision.v1'),
    canonical_json TEXT NOT NULL CHECK (length(canonical_json) > 0 AND length(canonical_json) <= 262144),
    canonical_digest TEXT NOT NULL CHECK (
        length(canonical_digest) = 64
        AND canonical_digest = lower(canonical_digest)
        AND canonical_digest NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 64)
);

CREATE TRIGGER dependency_decision_receipts_no_update
BEFORE UPDATE ON dependency_decision_receipts
BEGIN
    SELECT RAISE(ABORT, 'append_only_dependency_decision_receipts');
END;

CREATE TRIGGER dependency_decision_receipts_no_delete
BEFORE DELETE ON dependency_decision_receipts
BEGIN
    SELECT RAISE(ABORT, 'append_only_dependency_decision_receipts');
END;

CREATE TABLE global_stop_operator_decision_receipts (
    decision_ref TEXT PRIMARY KEY CHECK (length(decision_ref) BETWEEN 1 AND 96),
    authorized INTEGER NOT NULL CHECK (authorized IN (0, 1)),
    reason TEXT NOT NULL CHECK (
        reason IN ('accepted', 'operator_authorization_required')
        AND ((authorized = 1 AND reason = 'accepted')
            OR (authorized = 0 AND reason = 'operator_authorization_required'))
    ),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-global-stop-operator-decision.v1'),
    canonical_json TEXT NOT NULL CHECK (length(canonical_json) > 0 AND length(canonical_json) <= 262144),
    canonical_digest TEXT NOT NULL CHECK (
        length(canonical_digest) = 64
        AND canonical_digest = lower(canonical_digest)
        AND canonical_digest NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 64)
);

CREATE TRIGGER global_stop_operator_decision_receipts_no_update
BEFORE UPDATE ON global_stop_operator_decision_receipts
BEGIN
    SELECT RAISE(ABORT, 'append_only_global_stop_operator_decision_receipts');
END;

CREATE TRIGGER global_stop_operator_decision_receipts_no_delete
BEFORE DELETE ON global_stop_operator_decision_receipts
BEGIN
    SELECT RAISE(ABORT, 'append_only_global_stop_operator_decision_receipts');
END;

CREATE TABLE work_items (
    work_item_id TEXT PRIMARY KEY CHECK (length(work_item_id) BETWEEN 1 AND 96),
    lease_id TEXT NOT NULL CHECK (length(lease_id) BETWEEN 1 AND 96),
    backlog_id TEXT NOT NULL REFERENCES admitted_backlogs(backlog_id),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-work-item-state.v1'),
    state TEXT NOT NULL CHECK (state IN (
        'proposed',
        'lease_admitted',
        'ready',
        'cycle_starting',
        'worker_running',
        'validating',
        'auditing',
        'commit_eligible',
        'local_commit_completed',
        'repair_admitted',
        'repair_running',
        'blocked',
        'failed',
        'exhausted',
        'lease_expired',
        'canceled_revoked',
        'cleanup_pending',
        'cleanup_completed'
    )),
    version INTEGER NOT NULL CHECK (version >= 0),
    attempt_count INTEGER NOT NULL CHECK (attempt_count >= 0),
    repair_count INTEGER NOT NULL CHECK (repair_count >= 0),
    budget_consumed INTEGER NOT NULL CHECK (budget_consumed >= 0),
    budget_limit INTEGER NOT NULL CHECK (budget_limit >= 0),
    max_attempts INTEGER NOT NULL CHECK (max_attempts >= 0),
    max_repairs INTEGER NOT NULL CHECK (max_repairs >= 0),
    cleanup_required INTEGER NOT NULL CHECK (cleanup_required IN (0, 1)),
    updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 64)
);

CREATE TABLE transition_events (
    event_ref TEXT PRIMARY KEY CHECK (length(event_ref) BETWEEN 1 AND 96),
    event_sequence INTEGER NOT NULL UNIQUE CHECK (event_sequence >= 0),
    work_item_id TEXT NOT NULL REFERENCES work_items(work_item_id),
    lease_id TEXT NOT NULL CHECK (length(lease_id) BETWEEN 1 AND 96),
    idempotency_key TEXT NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 96),
    command_digest TEXT NOT NULL CHECK (
        length(command_digest) = 64
        AND command_digest = lower(command_digest)
        AND command_digest NOT GLOB '*[^0-9a-f]*'
    ),
    source_state TEXT NOT NULL CHECK (source_state IN (
        'proposed',
        'lease_admitted',
        'ready',
        'cycle_starting',
        'worker_running',
        'validating',
        'auditing',
        'commit_eligible',
        'local_commit_completed',
        'repair_admitted',
        'repair_running',
        'blocked',
        'failed',
        'exhausted',
        'lease_expired',
        'canceled_revoked',
        'cleanup_pending',
        'cleanup_completed'
    )),
    source_version INTEGER NOT NULL CHECK (source_version >= 0),
    resulting_state TEXT NOT NULL CHECK (resulting_state IN (
        'proposed',
        'lease_admitted',
        'ready',
        'cycle_starting',
        'worker_running',
        'validating',
        'auditing',
        'commit_eligible',
        'local_commit_completed',
        'repair_admitted',
        'repair_running',
        'blocked',
        'failed',
        'exhausted',
        'lease_expired',
        'canceled_revoked',
        'cleanup_pending',
        'cleanup_completed'
    )),
    resulting_version INTEGER NOT NULL CHECK (resulting_version >= 0),
    outcome TEXT NOT NULL CHECK (outcome IN ('accepted', 'domain_rejected')),
    reason TEXT NOT NULL CHECK (length(reason) BETWEEN 1 AND 96),
    evidence_refs_json TEXT NOT NULL CHECK (length(evidence_refs_json) <= 262144),
    budget_cost_delta INTEGER NOT NULL CHECK (budget_cost_delta >= 0),
    attempt_count_delta INTEGER NOT NULL CHECK (attempt_count_delta >= 0),
    repair_count_delta INTEGER NOT NULL CHECK (repair_count_delta >= 0),
    lease_identity_decision_ref TEXT NOT NULL REFERENCES lease_identity_records(decision_ref),
    authorization_decision_ref TEXT NOT NULL REFERENCES authorization_decision_receipts(decision_ref),
    dependency_decision_ref TEXT REFERENCES dependency_decision_receipts(decision_ref),
    global_stop_ref TEXT NOT NULL CHECK (length(global_stop_ref) BETWEEN 1 AND 96),
    global_stop_version INTEGER NOT NULL CHECK (global_stop_version >= 0),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-transition-event.v1'),
    event_json TEXT NOT NULL CHECK (length(event_json) > 0 AND length(event_json) <= 1048576),
    event_digest TEXT NOT NULL CHECK (
        length(event_digest) = 64
        AND event_digest = lower(event_digest)
        AND event_digest NOT GLOB '*[^0-9a-f]*'
    ),
    replay_work_item_json TEXT NOT NULL CHECK (length(replay_work_item_json) > 0 AND length(replay_work_item_json) <= 1048576),
    replay_work_item_digest TEXT NOT NULL CHECK (
        length(replay_work_item_digest) = 64
        AND replay_work_item_digest = lower(replay_work_item_digest)
        AND replay_work_item_digest NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 64),
    UNIQUE (work_item_id, idempotency_key),
    CHECK (
        (outcome = 'accepted' AND resulting_version = source_version + 1)
        OR (outcome = 'domain_rejected' AND resulting_version = source_version AND resulting_state = source_state
            AND budget_cost_delta = 0 AND attempt_count_delta = 0 AND repair_count_delta = 0)
    )
);

CREATE TRIGGER transition_events_no_update
BEFORE UPDATE ON transition_events
BEGIN
    SELECT RAISE(ABORT, 'append_only_transition_events');
END;

CREATE TRIGGER transition_events_no_delete
BEFORE DELETE ON transition_events
BEGIN
    SELECT RAISE(ABORT, 'append_only_transition_events');
END;

CREATE TABLE global_stop_current (
    singleton_id INTEGER PRIMARY KEY CHECK (singleton_id = 1),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-global-stop.v1'),
    version INTEGER NOT NULL CHECK (version >= 0),
    active INTEGER NOT NULL CHECK (active IN (0, 1)),
    stop_id TEXT CHECK (stop_id IS NULL OR length(stop_id) BETWEEN 1 AND 96),
    reason_class TEXT CHECK (reason_class IS NULL OR reason_class IN ('operator_stop', 'policy_stop', 'safety_stop')),
    issuer_ref TEXT CHECK (issuer_ref IS NULL OR length(issuer_ref) BETWEEN 1 AND 96),
    issued_at TEXT CHECK (issued_at IS NULL OR length(issued_at) BETWEEN 20 AND 64),
    operator_decision_ref TEXT REFERENCES global_stop_operator_decision_receipts(decision_ref),
    updated_at TEXT NOT NULL CHECK (length(updated_at) BETWEEN 20 AND 64),
    CHECK (
        (active = 0 AND stop_id IS NULL AND reason_class IS NULL AND issuer_ref IS NULL
            AND issued_at IS NULL AND operator_decision_ref IS NULL)
        OR (active = 1 AND stop_id IS NOT NULL AND reason_class IS NOT NULL AND issuer_ref IS NOT NULL
            AND issued_at IS NOT NULL AND operator_decision_ref IS NOT NULL)
    )
);

CREATE TABLE global_stop_events (
    event_ref TEXT PRIMARY KEY CHECK (length(event_ref) BETWEEN 1 AND 96),
    event_sequence INTEGER NOT NULL UNIQUE CHECK (event_sequence >= 0),
    idempotency_key TEXT NOT NULL UNIQUE CHECK (length(idempotency_key) BETWEEN 1 AND 96),
    command_digest TEXT NOT NULL CHECK (
        length(command_digest) = 64
        AND command_digest = lower(command_digest)
        AND command_digest NOT GLOB '*[^0-9a-f]*'
    ),
    action TEXT NOT NULL CHECK (action IN ('activate', 'replace', 'clear')),
    source_version INTEGER NOT NULL CHECK (source_version >= 0),
    resulting_version INTEGER NOT NULL CHECK (resulting_version >= 0),
    outcome TEXT NOT NULL CHECK (outcome IN ('accepted', 'domain_rejected')),
    reason TEXT NOT NULL CHECK (reason IN ('global_stop_update_accepted', 'global_stop_update_blocked', 'operator_authorization_required')),
    operator_decision_ref TEXT NOT NULL REFERENCES global_stop_operator_decision_receipts(decision_ref),
    resulting_global_stop_ref TEXT NOT NULL CHECK (length(resulting_global_stop_ref) BETWEEN 1 AND 96),
    resulting_status TEXT NOT NULL CHECK (resulting_status IN ('active', 'clear')),
    schema_id TEXT NOT NULL CHECK (schema_id = 'governed-execution.nwp-global-stop-event.v1'),
    event_json TEXT NOT NULL CHECK (length(event_json) > 0 AND length(event_json) <= 1048576),
    event_digest TEXT NOT NULL CHECK (
        length(event_digest) = 64
        AND event_digest = lower(event_digest)
        AND event_digest NOT GLOB '*[^0-9a-f]*'
    ),
    replay_global_stop_json TEXT NOT NULL CHECK (length(replay_global_stop_json) > 0 AND length(replay_global_stop_json) <= 1048576),
    replay_global_stop_digest TEXT NOT NULL CHECK (
        length(replay_global_stop_digest) = 64
        AND replay_global_stop_digest = lower(replay_global_stop_digest)
        AND replay_global_stop_digest NOT GLOB '*[^0-9a-f]*'
    ),
    created_at TEXT NOT NULL CHECK (length(created_at) BETWEEN 20 AND 64),
    CHECK (
        (outcome = 'accepted' AND resulting_version = source_version + 1 AND reason = 'global_stop_update_accepted')
        OR (outcome = 'domain_rejected' AND resulting_version = source_version
            AND reason IN ('global_stop_update_blocked', 'operator_authorization_required'))
    )
);

CREATE TRIGGER global_stop_events_no_update
BEFORE UPDATE ON global_stop_events
BEGIN
    SELECT RAISE(ABORT, 'append_only_global_stop_events');
END;

CREATE TRIGGER global_stop_events_no_delete
BEFORE DELETE ON global_stop_events
BEGIN
    SELECT RAISE(ABORT, 'append_only_global_stop_events');
END;

INSERT INTO global_stop_current
    (singleton_id, schema_id, version, active, stop_id, reason_class, issuer_ref,
     issued_at, operator_decision_ref, updated_at)
VALUES
    (1, 'governed-execution.nwp-global-stop.v1', 0, 0, NULL, NULL, NULL, NULL, NULL,
     '1970-01-01T00:00:00Z');
