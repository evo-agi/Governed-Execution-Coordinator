-- Branch-neutral terminal routing. The 0008 normal family remains unchanged.
CREATE TABLE rw0_terminal_anchors (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-terminal-anchor.v1'),
  phase_basis_ref ANY NOT NULL,
  phase_basis_digest ANY NOT NULL,
  family_profile ANY NOT NULL CHECK (typeof(family_profile)='text' AND length(CAST(family_profile AS BLOB)) BETWEEN 1 AND 96 AND substr(family_profile,1,1) GLOB '[0-9A-Za-z]' AND family_profile NOT GLOB '*[^0-9A-Za-z._-]*'),
  family_route ANY NOT NULL,
  mutation_ref ANY NOT NULL,
  command_digest ANY NOT NULL,
  program_ref ANY NOT NULL,
  decision_ref ANY NOT NULL,
  context_ref ANY NOT NULL,
  context_digest ANY NOT NULL,
  outcome_value_ref ANY NOT NULL,
  outcome_value_digest ANY NOT NULL,
  result_ref ANY NOT NULL,
  result_digest ANY NOT NULL,
  receipt_ref ANY NOT NULL,
  receipt_digest ANY NOT NULL,
  graph_profile ANY NOT NULL CHECK (typeof(graph_profile)='text' AND length(CAST(graph_profile AS BLOB)) BETWEEN 1 AND 96 AND substr(graph_profile,1,1) GLOB '[0-9A-Za-z]' AND graph_profile NOT GLOB '*[^0-9A-Za-z.-]*'),
  graph_digest ANY NOT NULL,
  committed_result_digest ANY NOT NULL,
  recorded_at ANY NOT NULL CHECK (typeof(recorded_at)='text' AND length(CAST(recorded_at AS BLOB))=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at),
  CONSTRAINT anchor_safe_refs CHECK (
    typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(phase_basis_ref,1,1) GLOB '[0-9A-Za-z]' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(family_route)='text' AND length(CAST(family_route AS BLOB)) BETWEEN 1 AND 96 AND substr(family_route,1,1) GLOB '[0-9A-Za-z]' AND family_route NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(program_ref)='text' AND length(CAST(program_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(context_ref,1,1) GLOB '[0-9A-Za-z]' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(outcome_value_ref,1,1) GLOB '[0-9A-Za-z]' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(result_ref)='text' AND length(CAST(result_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(result_ref,1,1) GLOB '[0-9A-Za-z]' AND result_ref NOT GLOB '*[^0-9A-Za-z.-]*'
    AND typeof(receipt_ref)='text' AND length(CAST(receipt_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(receipt_ref,1,1) GLOB '[0-9A-Za-z]' AND receipt_ref NOT GLOB '*[^0-9A-Za-z.-]*'
  ),
  CONSTRAINT anchor_safe_digests CHECK (
    typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(command_digest)='text' AND length(CAST(command_digest AS BLOB))=64 AND command_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(result_digest)='text' AND length(CAST(result_digest AS BLOB))=64 AND result_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(receipt_digest)='text' AND length(CAST(receipt_digest AS BLOB))=64 AND receipt_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(graph_digest)='text' AND length(CAST(graph_digest AS BLOB))=64 AND graph_digest NOT GLOB '*[^0-9a-f]*'
    AND typeof(committed_result_digest)='text' AND length(CAST(committed_result_digest AS BLOB))=64 AND committed_result_digest NOT GLOB '*[^0-9a-f]*'
  ),
  PRIMARY KEY (phase_basis_ref),
  UNIQUE (phase_basis_ref, phase_basis_digest),
  UNIQUE (family_route),
  UNIQUE (mutation_ref),
  UNIQUE (decision_ref),
  UNIQUE (context_ref),
  UNIQUE (outcome_value_ref),
  UNIQUE (result_ref),
  UNIQUE (receipt_ref),
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER rw0_terminal_anchors_no_update BEFORE UPDATE ON rw0_terminal_anchors
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_anchors'); END;

CREATE TRIGGER rw0_terminal_anchors_no_delete BEFORE DELETE ON rw0_terminal_anchors
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_anchors'); END;

CREATE TRIGGER rw0_terminal_anchors_require_registered_family BEFORE INSERT ON rw0_terminal_anchors
BEGIN
  SELECT RAISE(ABORT,'invalid_rw0_terminal_anchor') WHERE NOT EXISTS (
    SELECT 1 FROM rw0_terminal_receipts AS r
    JOIN rw0_terminal_contexts AS c ON c.context_ref=r.context_ref AND c.context_digest=r.context_digest
    JOIN rw0_terminal_outcomes AS o ON o.context_ref=c.context_ref AND o.context_digest=c.context_digest
    JOIN rw0_terminal_results AS x ON x.result_ref=r.result_ref AND x.result_digest=r.result_digest
    WHERE r.receipt_ref=NEW.receipt_ref AND r.receipt_digest=NEW.receipt_digest
      AND r.profile='artificial_offline_normal.v1'
      AND r.graph_profile='governed-execution.nwp-rw0-terminal-normal-graph.v1'
      AND o.branch='normal' AND x.branch='normal'
      AND r.phase_basis_ref=NEW.phase_basis_ref AND r.phase_basis_digest=NEW.phase_basis_digest
      AND r.profile=NEW.family_profile AND r.family_route=NEW.family_route
      AND r.mutation_ref=NEW.mutation_ref AND r.command_digest=NEW.command_digest
      AND c.program_ref=NEW.program_ref AND r.p1_decision_ref=NEW.decision_ref
      AND r.context_ref=NEW.context_ref AND r.context_digest=NEW.context_digest
      AND r.outcome_value_ref=NEW.outcome_value_ref AND r.outcome_value_digest=NEW.outcome_value_digest
      AND r.result_ref=NEW.result_ref AND r.result_digest=NEW.result_digest
      AND r.graph_profile=NEW.graph_profile AND r.graph_digest=NEW.graph_digest
      AND r.committed_result_digest=NEW.committed_result_digest AND r.recorded_at=NEW.recorded_at
      AND c.mutation_ref=r.mutation_ref AND c.phase_basis_ref=r.phase_basis_ref
      AND c.phase_basis_digest=r.phase_basis_digest AND c.p1_decision_ref=r.p1_decision_ref
      AND c.profile=r.profile AND c.recorded_at=r.recorded_at
      AND o.phase_basis_ref=c.phase_basis_ref AND o.phase_basis_digest=c.phase_basis_digest
      AND o.outcome_value_ref=r.outcome_value_ref AND o.outcome_value_digest=r.outcome_value_digest
      AND o.decision_ref=c.p1_decision_ref AND o.decision_digest=c.p1_decision_digest
      AND o.decision_kind=c.p1_decision_kind
      AND o.guarded_result_ref=c.p1_result_ref AND o.guarded_result_digest=c.p1_result_digest
      AND o.p1_receipt_mutation_ref=c.p1_receipt_mutation_ref
      AND o.p1_receipt_graph_digest=c.p1_receipt_graph_digest
      AND o.evidence_set_ref=c.evidence_set_ref AND o.evidence_set_digest=c.evidence_set_digest
      AND o.acceptance_fact_ref IS c.acceptance_fact_ref
      AND o.acceptance_fact_digest IS c.acceptance_fact_digest
      AND o.closure_stop_bytes=c.closure_stop_bytes
      AND x.context_ref=c.context_ref AND x.context_digest=c.context_digest
      AND x.outcome_value_ref=o.outcome_value_ref AND x.outcome_value_digest=o.outcome_value_digest
      AND x.branch=o.branch AND x.outcome=o.outcome AND x.recorded_at=r.recorded_at
  );
END;

INSERT INTO rw0_terminal_anchors (
  schema_id, phase_basis_ref, phase_basis_digest, family_profile, family_route,
  mutation_ref, command_digest, program_ref, decision_ref,
  context_ref, context_digest, outcome_value_ref, outcome_value_digest,
  result_ref, result_digest, receipt_ref, receipt_digest,
  graph_profile, graph_digest, committed_result_digest, recorded_at
)
SELECT
  'governed-execution.nwp-rw0-terminal-anchor.v1',
  r.phase_basis_ref, r.phase_basis_digest, r.profile, r.family_route,
  r.mutation_ref, r.command_digest, c.program_ref, r.p1_decision_ref,
  r.context_ref, r.context_digest, r.outcome_value_ref, r.outcome_value_digest,
  r.result_ref, r.result_digest, r.receipt_ref, r.receipt_digest,
  r.graph_profile, r.graph_digest, r.committed_result_digest, r.recorded_at
FROM rw0_terminal_receipts AS r
JOIN rw0_terminal_contexts AS c
  ON c.context_ref=r.context_ref AND c.context_digest=r.context_digest
 AND c.mutation_ref=r.mutation_ref AND c.phase_basis_ref=r.phase_basis_ref
 AND c.phase_basis_digest=r.phase_basis_digest AND c.p1_decision_ref=r.p1_decision_ref
 AND c.profile=r.profile AND c.recorded_at=r.recorded_at
JOIN rw0_terminal_outcomes AS o
  ON o.context_ref=c.context_ref AND o.context_digest=c.context_digest
 AND o.phase_basis_ref=c.phase_basis_ref AND o.phase_basis_digest=c.phase_basis_digest
 AND o.outcome_value_ref=r.outcome_value_ref AND o.outcome_value_digest=r.outcome_value_digest
 AND o.decision_ref=c.p1_decision_ref AND o.decision_digest=c.p1_decision_digest
 AND o.decision_kind=c.p1_decision_kind
 AND o.guarded_result_ref=c.p1_result_ref AND o.guarded_result_digest=c.p1_result_digest
 AND o.p1_receipt_mutation_ref=c.p1_receipt_mutation_ref
 AND o.p1_receipt_graph_digest=c.p1_receipt_graph_digest
 AND o.evidence_set_ref=c.evidence_set_ref AND o.evidence_set_digest=c.evidence_set_digest
 AND o.acceptance_fact_ref IS c.acceptance_fact_ref
 AND o.acceptance_fact_digest IS c.acceptance_fact_digest
 AND o.closure_stop_bytes=c.closure_stop_bytes
JOIN rw0_terminal_results AS x
  ON x.result_ref=r.result_ref AND x.result_digest=r.result_digest
 AND x.context_ref=c.context_ref AND x.context_digest=c.context_digest
 AND x.outcome_value_ref=o.outcome_value_ref AND x.outcome_value_digest=o.outcome_value_digest
 AND x.branch=o.branch AND x.outcome=o.outcome AND x.recorded_at=r.recorded_at
WHERE r.profile='artificial_offline_normal.v1'
  AND r.graph_profile='governed-execution.nwp-rw0-terminal-normal-graph.v1'
  AND o.branch='normal' AND x.branch='normal'
ORDER BY r.phase_basis_ref;

CREATE TRIGGER rw0_terminal_receipts_register_anchor AFTER INSERT ON rw0_terminal_receipts
BEGIN
  INSERT INTO rw0_terminal_anchors (
    schema_id, phase_basis_ref, phase_basis_digest, family_profile, family_route,
    mutation_ref, command_digest, program_ref, decision_ref,
    context_ref, context_digest, outcome_value_ref, outcome_value_digest,
    result_ref, result_digest, receipt_ref, receipt_digest,
    graph_profile, graph_digest, committed_result_digest, recorded_at
  )
  SELECT
    'governed-execution.nwp-rw0-terminal-anchor.v1',
    r.phase_basis_ref, r.phase_basis_digest, r.profile, r.family_route,
    r.mutation_ref, r.command_digest, c.program_ref, r.p1_decision_ref,
    r.context_ref, r.context_digest, r.outcome_value_ref, r.outcome_value_digest,
    r.result_ref, r.result_digest, r.receipt_ref, r.receipt_digest,
    r.graph_profile, r.graph_digest, r.committed_result_digest, r.recorded_at
  FROM rw0_terminal_receipts AS r
  JOIN rw0_terminal_contexts AS c ON c.context_ref=r.context_ref AND c.context_digest=r.context_digest
  JOIN rw0_terminal_outcomes AS o ON o.context_ref=c.context_ref AND o.context_digest=c.context_digest
  JOIN rw0_terminal_results AS x ON x.result_ref=r.result_ref AND x.result_digest=r.result_digest
  WHERE r.receipt_ref=NEW.receipt_ref
    AND c.mutation_ref=r.mutation_ref AND c.phase_basis_ref=r.phase_basis_ref
    AND c.phase_basis_digest=r.phase_basis_digest AND c.p1_decision_ref=r.p1_decision_ref
    AND c.profile=r.profile AND c.recorded_at=r.recorded_at
    AND o.phase_basis_ref=c.phase_basis_ref AND o.phase_basis_digest=c.phase_basis_digest
    AND o.outcome_value_ref=r.outcome_value_ref AND o.outcome_value_digest=r.outcome_value_digest
    AND o.decision_ref=c.p1_decision_ref AND o.decision_digest=c.p1_decision_digest
    AND o.decision_kind=c.p1_decision_kind
    AND o.guarded_result_ref=c.p1_result_ref AND o.guarded_result_digest=c.p1_result_digest
    AND o.p1_receipt_mutation_ref=c.p1_receipt_mutation_ref
    AND o.p1_receipt_graph_digest=c.p1_receipt_graph_digest
    AND o.evidence_set_ref=c.evidence_set_ref AND o.evidence_set_digest=c.evidence_set_digest
    AND o.acceptance_fact_ref IS c.acceptance_fact_ref
    AND o.acceptance_fact_digest IS c.acceptance_fact_digest
    AND o.closure_stop_bytes=c.closure_stop_bytes
    AND x.context_ref=c.context_ref AND x.context_digest=c.context_digest
    AND x.outcome_value_ref=o.outcome_value_ref AND x.outcome_value_digest=o.outcome_value_digest
    AND x.branch=o.branch AND x.outcome=o.outcome AND x.recorded_at=r.recorded_at
    AND r.profile='artificial_offline_normal.v1'
    AND r.graph_profile='governed-execution.nwp-rw0-terminal-normal-graph.v1'
    AND o.branch='normal' AND x.branch='normal';
  SELECT RAISE(ABORT,'missing_rw0_terminal_anchor') WHERE NOT EXISTS (
    SELECT 1 FROM rw0_terminal_anchors AS a
    WHERE a.phase_basis_ref=NEW.phase_basis_ref AND a.phase_basis_digest=NEW.phase_basis_digest
      AND a.receipt_ref=NEW.receipt_ref AND a.receipt_digest=NEW.receipt_digest
      AND a.family_profile=NEW.profile AND a.family_route=NEW.family_route
      AND a.mutation_ref=NEW.mutation_ref AND a.command_digest=NEW.command_digest
      AND a.context_ref=NEW.context_ref AND a.context_digest=NEW.context_digest
      AND a.outcome_value_ref=NEW.outcome_value_ref AND a.outcome_value_digest=NEW.outcome_value_digest
      AND a.result_ref=NEW.result_ref AND a.result_digest=NEW.result_digest
      AND a.graph_profile=NEW.graph_profile AND a.graph_digest=NEW.graph_digest
      AND a.committed_result_digest=NEW.committed_result_digest AND a.recorded_at=NEW.recorded_at
  );
END;
