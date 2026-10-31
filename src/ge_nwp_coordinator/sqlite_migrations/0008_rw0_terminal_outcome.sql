-- Private artificial-offline normal terminal closure. Additive generation-2 schema.

CREATE TABLE rw0_terminal_contexts (
  "schema_id" ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-terminal-context.v2'),
  "context_ref" ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND context_ref GLOB '[0-9A-Za-z]*' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(context_ref,1,instr(context_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "profile" ANY NOT NULL CHECK (typeof(profile)='text' AND profile='artificial_offline_normal.v1'),
  "mutation_ref" ANY NOT NULL CHECK (typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND mutation_ref GLOB '[0-9A-Za-z]*' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "phase_basis_ref" ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND phase_basis_ref GLOB '[0-9A-Za-z]*' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(phase_basis_ref,1,instr(phase_basis_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "phase_basis_digest" ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  "program_ref" ANY NOT NULL CHECK (typeof(program_ref)='text' AND length(CAST(program_ref AS BLOB)) BETWEEN 1 AND 96 AND program_ref GLOB '[0-9A-Za-z]*' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(program_ref,1,instr(program_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "lineage_ref" ANY NOT NULL CHECK (typeof(lineage_ref)='text' AND length(CAST(lineage_ref AS BLOB)) BETWEEN 1 AND 96 AND lineage_ref GLOB '[0-9A-Za-z]*' AND lineage_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(lineage_ref,1,instr(lineage_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof(scope_ref)='text' AND length(CAST(scope_ref AS BLOB)) BETWEEN 1 AND 96 AND scope_ref GLOB '[0-9A-Za-z]*' AND scope_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(scope_ref,1,instr(scope_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p0_act_ref" ANY NOT NULL CHECK (typeof(p0_act_ref)='text' AND length(CAST(p0_act_ref AS BLOB)) BETWEEN 1 AND 96 AND p0_act_ref GLOB '[0-9A-Za-z]*' AND p0_act_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p0_act_ref,1,instr(p0_act_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p0_act_digest" ANY NOT NULL CHECK (typeof(p0_act_digest)='text' AND length(CAST(p0_act_digest AS BLOB))=64 AND p0_act_digest NOT GLOB '*[^0-9a-f]*'),
  "p0_fact_ref" ANY NOT NULL CHECK (typeof(p0_fact_ref)='text' AND length(CAST(p0_fact_ref AS BLOB)) BETWEEN 1 AND 96 AND p0_fact_ref GLOB '[0-9A-Za-z]*' AND p0_fact_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p0_fact_ref,1,instr(p0_fact_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p0_fact_digest" ANY NOT NULL CHECK (typeof(p0_fact_digest)='text' AND length(CAST(p0_fact_digest AS BLOB))=64 AND p0_fact_digest NOT GLOB '*[^0-9a-f]*'),
  "section41_context_ref" ANY NOT NULL CHECK (typeof(section41_context_ref)='text' AND length(CAST(section41_context_ref AS BLOB)) BETWEEN 1 AND 96 AND section41_context_ref GLOB '[0-9A-Za-z]*' AND section41_context_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(section41_context_ref,1,instr(section41_context_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "section41_context_digest" ANY NOT NULL CHECK (typeof(section41_context_digest)='text' AND length(CAST(section41_context_digest AS BLOB))=64 AND section41_context_digest NOT GLOB '*[^0-9a-f]*'),
  "section41_proposal_ref" ANY NOT NULL CHECK (typeof(section41_proposal_ref)='text' AND length(CAST(section41_proposal_ref AS BLOB)) BETWEEN 1 AND 96 AND section41_proposal_ref GLOB '[0-9A-Za-z]*' AND section41_proposal_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(section41_proposal_ref,1,instr(section41_proposal_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "section41_proposal_digest" ANY NOT NULL CHECK (typeof(section41_proposal_digest)='text' AND length(CAST(section41_proposal_digest AS BLOB))=64 AND section41_proposal_digest NOT GLOB '*[^0-9a-f]*'),
  "section41_receipt_mutation_ref" ANY NOT NULL CHECK (typeof(section41_receipt_mutation_ref)='text' AND length(CAST(section41_receipt_mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND section41_receipt_mutation_ref GLOB '[0-9A-Za-z]*' AND section41_receipt_mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(section41_receipt_mutation_ref,1,instr(section41_receipt_mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "section41_receipt_digest" ANY NOT NULL CHECK (typeof(section41_receipt_digest)='text' AND length(CAST(section41_receipt_digest AS BLOB))=64 AND section41_receipt_digest NOT GLOB '*[^0-9a-f]*'),
  "evidence_set_ref" ANY NOT NULL CHECK (typeof(evidence_set_ref)='text' AND length(CAST(evidence_set_ref AS BLOB)) BETWEEN 1 AND 96 AND evidence_set_ref GLOB '[0-9A-Za-z]*' AND evidence_set_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(evidence_set_ref,1,instr(evidence_set_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "evidence_set_digest" ANY NOT NULL CHECK (typeof(evidence_set_digest)='text' AND length(CAST(evidence_set_digest AS BLOB))=64 AND evidence_set_digest NOT GLOB '*[^0-9a-f]*'),
  "c1_membership_ref" ANY NOT NULL CHECK (typeof(c1_membership_ref)='text' AND length(CAST(c1_membership_ref AS BLOB)) BETWEEN 1 AND 96 AND c1_membership_ref GLOB '[0-9A-Za-z]*' AND c1_membership_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(c1_membership_ref,1,instr(c1_membership_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "c1_membership_digest" ANY NOT NULL CHECK (typeof(c1_membership_digest)='text' AND length(CAST(c1_membership_digest AS BLOB))=64 AND c1_membership_digest NOT GLOB '*[^0-9a-f]*'),
  "c1_receipt_digest" ANY NOT NULL CHECK (typeof(c1_receipt_digest)='text' AND length(CAST(c1_receipt_digest AS BLOB))=64 AND c1_receipt_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_basis_ref" ANY NOT NULL CHECK (typeof(p1_basis_ref)='text' AND length(CAST(p1_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND p1_basis_ref GLOB '[0-9A-Za-z]*' AND p1_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p1_basis_ref,1,instr(p1_basis_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p1_basis_digest" ANY NOT NULL CHECK (typeof(p1_basis_digest)='text' AND length(CAST(p1_basis_digest AS BLOB))=64 AND p1_basis_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_decision_ref" ANY NOT NULL CHECK (typeof(p1_decision_ref)='text' AND length(CAST(p1_decision_ref AS BLOB)) BETWEEN 1 AND 96 AND p1_decision_ref GLOB '[0-9A-Za-z]*' AND p1_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p1_decision_ref,1,instr(p1_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p1_decision_digest" ANY NOT NULL CHECK (typeof(p1_decision_digest)='text' AND length(CAST(p1_decision_digest AS BLOB))=64 AND p1_decision_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_decision_kind" ANY NOT NULL CHECK (typeof(p1_decision_kind)='text' AND p1_decision_kind IN ('accept','repair','replan','terminal_reject','block')),
  "p1_result_ref" ANY NOT NULL CHECK (typeof(p1_result_ref)='text' AND length(CAST(p1_result_ref AS BLOB)) BETWEEN 1 AND 96 AND p1_result_ref GLOB '[0-9A-Za-z]*' AND p1_result_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p1_result_ref,1,instr(p1_result_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p1_result_digest" ANY NOT NULL CHECK (typeof(p1_result_digest)='text' AND length(CAST(p1_result_digest AS BLOB))=64 AND p1_result_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_receipt_mutation_ref" ANY NOT NULL CHECK (typeof(p1_receipt_mutation_ref)='text' AND length(CAST(p1_receipt_mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND p1_receipt_mutation_ref GLOB '[0-9A-Za-z]*' AND p1_receipt_mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p1_receipt_mutation_ref,1,instr(p1_receipt_mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p1_receipt_graph_digest" ANY NOT NULL CHECK (typeof(p1_receipt_graph_digest)='text' AND length(CAST(p1_receipt_graph_digest AS BLOB))=64 AND p1_receipt_graph_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_receipt_digest_anchor" ANY NOT NULL CHECK (typeof(p1_receipt_digest_anchor)='text' AND length(CAST(p1_receipt_digest_anchor AS BLOB))=64 AND p1_receipt_digest_anchor NOT GLOB '*[^0-9a-f]*'),
  "acceptance_fact_ref" ANY CHECK (acceptance_fact_ref IS NULL OR (typeof(acceptance_fact_ref)='text' AND length(CAST(acceptance_fact_ref AS BLOB)) BETWEEN 1 AND 96 AND acceptance_fact_ref GLOB '[0-9A-Za-z]*' AND acceptance_fact_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(acceptance_fact_ref,1,instr(acceptance_fact_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))),
  "acceptance_fact_digest" ANY CHECK (acceptance_fact_digest IS NULL OR (typeof(acceptance_fact_digest)='text' AND length(CAST(acceptance_fact_digest AS BLOB))=64 AND acceptance_fact_digest NOT GLOB '*[^0-9a-f]*')),
  "command_safe_bytes" ANY NOT NULL CHECK (typeof(command_safe_bytes)='blob' AND length(command_safe_bytes) BETWEEN 1 AND 49152),
  "reached_owner_manifest_bytes" ANY NOT NULL CHECK (typeof(reached_owner_manifest_bytes)='blob' AND length(reached_owner_manifest_bytes) BETWEEN 1 AND 8192),
  "closure_heads_bytes" ANY NOT NULL CHECK (typeof(closure_heads_bytes)='blob' AND length(closure_heads_bytes) BETWEEN 1 AND 32768),
  "closure_stop_bytes" ANY NOT NULL CHECK (typeof(closure_stop_bytes)='blob' AND length(closure_stop_bytes) BETWEEN 1 AND 1024),
  "recorded_at" ANY NOT NULL CHECK (typeof(recorded_at)='text'
    AND length(CAST(recorded_at AS BLOB))=20
    AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'
    AND CAST(substr(recorded_at,1,4) AS INTEGER) BETWEEN 1 AND 9999
    AND CAST(substr(recorded_at,6,2) AS INTEGER) BETWEEN 1 AND 12
    AND CAST(substr(recorded_at,9,2) AS INTEGER) BETWEEN 1 AND
      CASE
        WHEN CAST(substr(recorded_at,6,2) AS INTEGER)=2 THEN
          CASE WHEN CAST(substr(recorded_at,1,4) AS INTEGER)%400=0
                 OR (CAST(substr(recorded_at,1,4) AS INTEGER)%4=0
                     AND CAST(substr(recorded_at,1,4) AS INTEGER)%100<>0)
            THEN 29 ELSE 28 END
        WHEN CAST(substr(recorded_at,6,2) AS INTEGER) IN (4,6,9,11) THEN 30
        ELSE 31
      END
    AND CAST(substr(recorded_at,12,2) AS INTEGER) BETWEEN 0 AND 23
    AND CAST(substr(recorded_at,15,2) AS INTEGER) BETWEEN 0 AND 59
    AND CAST(substr(recorded_at,18,2) AS INTEGER) BETWEEN 0 AND 59),
  "context_digest" ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (context_ref),
  UNIQUE (mutation_ref),
  UNIQUE (phase_basis_ref),
  UNIQUE (p1_decision_ref),
  UNIQUE (context_ref, context_digest),
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (p0_fact_ref, p0_fact_digest) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref, admission_fact_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, p1_decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (p1_basis_ref, p1_basis_digest) REFERENCES rw0_c2_decision_bases (basis_ref, basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (section41_receipt_mutation_ref) REFERENCES development_post_execution_proposal_receipts (mutation_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (c1_membership_ref) REFERENCES rw0_evidence_memberships (membership_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (p1_receipt_mutation_ref) REFERENCES development_mutation_receipts (mutation_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (acceptance_fact_ref) REFERENCES rw0_c2_bootstrap_acceptance_facts (acceptance_fact_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT acceptance_pair CHECK ((acceptance_fact_ref IS NULL AND acceptance_fact_digest IS NULL) OR (acceptance_fact_ref IS NOT NULL AND acceptance_fact_digest IS NOT NULL))
) STRICT;

CREATE TRIGGER rw0_terminal_contexts_no_update BEFORE UPDATE ON rw0_terminal_contexts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_contexts'); END;
CREATE TRIGGER rw0_terminal_contexts_no_delete BEFORE DELETE ON rw0_terminal_contexts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_contexts'); END;

CREATE TABLE rw0_terminal_outcomes (
  "schema_id" ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-terminal-outcome-value.v2'),
  "outcome_value_ref" ANY NOT NULL CHECK (typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND outcome_value_ref GLOB '[0-9A-Za-z]*' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(outcome_value_ref,1,instr(outcome_value_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "context_ref" ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND context_ref GLOB '[0-9A-Za-z]*' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(context_ref,1,instr(context_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "context_digest" ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  "phase_basis_ref" ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND phase_basis_ref GLOB '[0-9A-Za-z]*' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(phase_basis_ref,1,instr(phase_basis_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "phase_basis_digest" ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  "branch" ANY NOT NULL CHECK (typeof(branch)='text' AND branch='normal'),
  "outcome" ANY NOT NULL CHECK (typeof(outcome)='text' AND outcome IN ('accept','repair','replan','terminal_reject','block')),
  "decision_ref" ANY NOT NULL CHECK (typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND decision_ref GLOB '[0-9A-Za-z]*' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(decision_ref,1,instr(decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "decision_digest" ANY NOT NULL CHECK (typeof(decision_digest)='text' AND length(CAST(decision_digest AS BLOB))=64 AND decision_digest NOT GLOB '*[^0-9a-f]*'),
  "decision_kind" ANY NOT NULL CHECK (typeof(decision_kind)='text' AND decision_kind IN ('accept','repair','replan','terminal_reject','block')),
  "guarded_result_ref" ANY NOT NULL CHECK (typeof(guarded_result_ref)='text' AND length(CAST(guarded_result_ref AS BLOB)) BETWEEN 1 AND 96 AND guarded_result_ref GLOB '[0-9A-Za-z]*' AND guarded_result_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(guarded_result_ref,1,instr(guarded_result_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "guarded_result_digest" ANY NOT NULL CHECK (typeof(guarded_result_digest)='text' AND length(CAST(guarded_result_digest AS BLOB))=64 AND guarded_result_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_receipt_mutation_ref" ANY NOT NULL CHECK (typeof(p1_receipt_mutation_ref)='text' AND length(CAST(p1_receipt_mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND p1_receipt_mutation_ref GLOB '[0-9A-Za-z]*' AND p1_receipt_mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p1_receipt_mutation_ref,1,instr(p1_receipt_mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "p1_receipt_graph_digest" ANY NOT NULL CHECK (typeof(p1_receipt_graph_digest)='text' AND length(CAST(p1_receipt_graph_digest AS BLOB))=64 AND p1_receipt_graph_digest NOT GLOB '*[^0-9a-f]*'),
  "closure_heads_bytes" ANY NOT NULL CHECK (typeof(closure_heads_bytes)='blob' AND length(closure_heads_bytes) BETWEEN 1 AND 4096),
  "closure_stop_bytes" ANY NOT NULL CHECK (typeof(closure_stop_bytes)='blob' AND length(closure_stop_bytes) BETWEEN 1 AND 1024),
  "evidence_set_ref" ANY NOT NULL CHECK (typeof(evidence_set_ref)='text' AND length(CAST(evidence_set_ref AS BLOB)) BETWEEN 1 AND 96 AND evidence_set_ref GLOB '[0-9A-Za-z]*' AND evidence_set_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(evidence_set_ref,1,instr(evidence_set_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "evidence_set_digest" ANY NOT NULL CHECK (typeof(evidence_set_digest)='text' AND length(CAST(evidence_set_digest AS BLOB))=64 AND evidence_set_digest NOT GLOB '*[^0-9a-f]*'),
  "acceptance_fact_ref" ANY CHECK (acceptance_fact_ref IS NULL OR (typeof(acceptance_fact_ref)='text' AND length(CAST(acceptance_fact_ref AS BLOB)) BETWEEN 1 AND 96 AND acceptance_fact_ref GLOB '[0-9A-Za-z]*' AND acceptance_fact_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(acceptance_fact_ref,1,instr(acceptance_fact_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))),
  "acceptance_fact_digest" ANY CHECK (acceptance_fact_digest IS NULL OR (typeof(acceptance_fact_digest)='text' AND length(CAST(acceptance_fact_digest AS BLOB))=64 AND acceptance_fact_digest NOT GLOB '*[^0-9a-f]*')),
  "reconciliation_ref" ANY CHECK (reconciliation_ref IS NULL),
  "reconciliation_digest" ANY CHECK (reconciliation_digest IS NULL),
  "mismatch_ref" ANY CHECK (mismatch_ref IS NULL),
  "mismatch_digest" ANY CHECK (mismatch_digest IS NULL),
  "outcome_value_digest" ANY NOT NULL CHECK (typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (outcome_value_ref),
  UNIQUE (context_ref),
  UNIQUE (phase_basis_ref),
  UNIQUE (decision_ref),
  UNIQUE (outcome_value_ref, outcome_value_digest),
  FOREIGN KEY (context_ref, context_digest) REFERENCES rw0_terminal_contexts (context_ref, context_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (decision_ref) REFERENCES development_decisions (decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (acceptance_fact_ref) REFERENCES rw0_c2_bootstrap_acceptance_facts (acceptance_fact_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  CONSTRAINT normal_pair CHECK (decision_kind=outcome),
  CONSTRAINT acceptance_pair CHECK ((outcome='accept' AND acceptance_fact_ref IS NOT NULL AND acceptance_fact_digest IS NOT NULL) OR (outcome<>'accept' AND acceptance_fact_ref IS NULL AND acceptance_fact_digest IS NULL))
) STRICT;

CREATE TRIGGER rw0_terminal_outcomes_no_update BEFORE UPDATE ON rw0_terminal_outcomes
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_outcomes'); END;
CREATE TRIGGER rw0_terminal_outcomes_no_delete BEFORE DELETE ON rw0_terminal_outcomes
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_outcomes'); END;

CREATE TABLE rw0_terminal_results (
  "schema_id" ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-terminal-result.v1'),
  "result_ref" ANY NOT NULL CHECK (typeof(result_ref)='text' AND length(CAST(result_ref AS BLOB)) BETWEEN 1 AND 96 AND result_ref GLOB '[0-9A-Za-z]*' AND result_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_ref,1,instr(result_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "outcome_value_ref" ANY NOT NULL CHECK (typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND outcome_value_ref GLOB '[0-9A-Za-z]*' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(outcome_value_ref,1,instr(outcome_value_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "outcome_value_digest" ANY NOT NULL CHECK (typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'),
  "context_ref" ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND context_ref GLOB '[0-9A-Za-z]*' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(context_ref,1,instr(context_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "context_digest" ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  "branch" ANY NOT NULL CHECK (branch='normal'),
  "outcome" ANY NOT NULL CHECK (typeof(outcome)='text' AND outcome IN ('accept','repair','replan','terminal_reject','block')),
  "recorded_at" ANY NOT NULL CHECK (typeof(recorded_at)='text'
    AND length(CAST(recorded_at AS BLOB))=20
    AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'
    AND CAST(substr(recorded_at,1,4) AS INTEGER) BETWEEN 1 AND 9999
    AND CAST(substr(recorded_at,6,2) AS INTEGER) BETWEEN 1 AND 12
    AND CAST(substr(recorded_at,9,2) AS INTEGER) BETWEEN 1 AND
      CASE
        WHEN CAST(substr(recorded_at,6,2) AS INTEGER)=2 THEN
          CASE WHEN CAST(substr(recorded_at,1,4) AS INTEGER)%400=0
                 OR (CAST(substr(recorded_at,1,4) AS INTEGER)%4=0
                     AND CAST(substr(recorded_at,1,4) AS INTEGER)%100<>0)
            THEN 29 ELSE 28 END
        WHEN CAST(substr(recorded_at,6,2) AS INTEGER) IN (4,6,9,11) THEN 30
        ELSE 31
      END
    AND CAST(substr(recorded_at,12,2) AS INTEGER) BETWEEN 0 AND 23
    AND CAST(substr(recorded_at,15,2) AS INTEGER) BETWEEN 0 AND 59
    AND CAST(substr(recorded_at,18,2) AS INTEGER) BETWEEN 0 AND 59),
  "result_digest" ANY NOT NULL CHECK (typeof(result_digest)='text' AND length(CAST(result_digest AS BLOB))=64 AND result_digest NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (result_ref),
  UNIQUE (outcome_value_ref),
  UNIQUE (result_ref, result_digest),
  FOREIGN KEY (outcome_value_ref, outcome_value_digest) REFERENCES rw0_terminal_outcomes (outcome_value_ref, outcome_value_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (context_ref, context_digest) REFERENCES rw0_terminal_contexts (context_ref, context_digest) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER rw0_terminal_results_no_update BEFORE UPDATE ON rw0_terminal_results
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_results'); END;
CREATE TRIGGER rw0_terminal_results_no_delete BEFORE DELETE ON rw0_terminal_results
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_results'); END;

CREATE TABLE rw0_terminal_receipts (
  "schema_id" ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-terminal-receipt.v1'),
  "receipt_ref" ANY NOT NULL CHECK (typeof(receipt_ref)='text' AND length(CAST(receipt_ref AS BLOB)) BETWEEN 1 AND 96 AND receipt_ref GLOB '[0-9A-Za-z]*' AND receipt_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(receipt_ref,1,instr(receipt_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "mutation_ref" ANY NOT NULL CHECK (typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND mutation_ref GLOB '[0-9A-Za-z]*' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(mutation_ref,1,instr(mutation_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "command_digest" ANY NOT NULL CHECK (typeof(command_digest)='text' AND length(CAST(command_digest AS BLOB))=64 AND command_digest NOT GLOB '*[^0-9a-f]*'),
  "profile" ANY NOT NULL CHECK (typeof(profile)='text' AND profile='artificial_offline_normal.v1'),
  "family_route" ANY NOT NULL CHECK (typeof(family_route)='text' AND length(CAST(family_route AS BLOB)) BETWEEN 1 AND 96 AND family_route GLOB '[0-9A-Za-z]*' AND family_route NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(family_route,1,instr(family_route,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "phase_basis_ref" ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND phase_basis_ref GLOB '[0-9A-Za-z]*' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(phase_basis_ref,1,instr(phase_basis_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "phase_basis_digest" ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  "p1_decision_ref" ANY NOT NULL CHECK (typeof(p1_decision_ref)='text' AND length(CAST(p1_decision_ref AS BLOB)) BETWEEN 1 AND 96 AND p1_decision_ref GLOB '[0-9A-Za-z]*' AND p1_decision_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(p1_decision_ref,1,instr(p1_decision_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "context_ref" ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND context_ref GLOB '[0-9A-Za-z]*' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(context_ref,1,instr(context_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "context_digest" ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  "outcome_value_ref" ANY NOT NULL CHECK (typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND outcome_value_ref GLOB '[0-9A-Za-z]*' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(outcome_value_ref,1,instr(outcome_value_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "outcome_value_digest" ANY NOT NULL CHECK (typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'),
  "result_ref" ANY NOT NULL CHECK (typeof(result_ref)='text' AND length(CAST(result_ref AS BLOB)) BETWEEN 1 AND 96 AND result_ref GLOB '[0-9A-Za-z]*' AND result_ref NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr(result_ref,1,instr(result_ref,'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "result_digest" ANY NOT NULL CHECK (typeof(result_digest)='text' AND length(CAST(result_digest AS BLOB))=64 AND result_digest NOT GLOB '*[^0-9a-f]*'),
  "graph_profile" ANY NOT NULL CHECK (typeof(graph_profile)='text' AND graph_profile='governed-execution.nwp-rw0-terminal-normal-graph.v1'),
  "graph_digest" ANY NOT NULL CHECK (typeof(graph_digest)='text' AND length(CAST(graph_digest AS BLOB))=64 AND graph_digest NOT GLOB '*[^0-9a-f]*'),
  "committed_result_digest" ANY NOT NULL CHECK (typeof(committed_result_digest)='text' AND length(CAST(committed_result_digest AS BLOB))=64 AND committed_result_digest NOT GLOB '*[^0-9a-f]*'),
  "recorded_at" ANY NOT NULL CHECK (typeof(recorded_at)='text'
    AND length(CAST(recorded_at AS BLOB))=20
    AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z'
    AND CAST(substr(recorded_at,1,4) AS INTEGER) BETWEEN 1 AND 9999
    AND CAST(substr(recorded_at,6,2) AS INTEGER) BETWEEN 1 AND 12
    AND CAST(substr(recorded_at,9,2) AS INTEGER) BETWEEN 1 AND
      CASE
        WHEN CAST(substr(recorded_at,6,2) AS INTEGER)=2 THEN
          CASE WHEN CAST(substr(recorded_at,1,4) AS INTEGER)%400=0
                 OR (CAST(substr(recorded_at,1,4) AS INTEGER)%4=0
                     AND CAST(substr(recorded_at,1,4) AS INTEGER)%100<>0)
            THEN 29 ELSE 28 END
        WHEN CAST(substr(recorded_at,6,2) AS INTEGER) IN (4,6,9,11) THEN 30
        ELSE 31
      END
    AND CAST(substr(recorded_at,12,2) AS INTEGER) BETWEEN 0 AND 23
    AND CAST(substr(recorded_at,15,2) AS INTEGER) BETWEEN 0 AND 59
    AND CAST(substr(recorded_at,18,2) AS INTEGER) BETWEEN 0 AND 59),
  "receipt_digest" ANY NOT NULL CHECK (typeof(receipt_digest)='text' AND length(CAST(receipt_digest AS BLOB))=64 AND receipt_digest NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (receipt_ref),
  UNIQUE (mutation_ref),
  UNIQUE (family_route),
  UNIQUE (phase_basis_ref),
  UNIQUE (p1_decision_ref),
  UNIQUE (context_ref),
  UNIQUE (outcome_value_ref),
  UNIQUE (result_ref),
  FOREIGN KEY (context_ref, context_digest) REFERENCES rw0_terminal_contexts (context_ref, context_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (outcome_value_ref, outcome_value_digest) REFERENCES rw0_terminal_outcomes (outcome_value_ref, outcome_value_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (result_ref, result_digest) REFERENCES rw0_terminal_results (result_ref, result_digest) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER rw0_terminal_receipts_no_update BEFORE UPDATE ON rw0_terminal_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_receipts'); END;
CREATE TRIGGER rw0_terminal_receipts_no_delete BEFORE DELETE ON rw0_terminal_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_terminal_receipts'); END;
