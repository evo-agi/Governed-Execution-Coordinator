CREATE TABLE development_post_execution_proposal_contexts (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-section41-post-execution-proposal-context-row.v1'),
  "proposal_phase" ANY NOT NULL CHECK (typeof("proposal_phase")='text' AND "proposal_phase"='post_execution_semantic_review'),
  "context_ref" ANY NOT NULL CHECK (typeof("context_ref")='text' AND length(CAST("context_ref" AS BLOB)) BETWEEN 1 AND 96 AND "context_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("context_ref",1,1) GLOB '[0-9A-Za-z]'),
  "context_digest" ANY NOT NULL CHECK (typeof("context_digest")='text' AND length(CAST("context_digest" AS BLOB))=64 AND "context_digest" NOT GLOB '*[^0-9a-f]*'),
  "proposal_ref" ANY NOT NULL CHECK (typeof("proposal_ref")='text' AND length(CAST("proposal_ref" AS BLOB)) BETWEEN 1 AND 96 AND "proposal_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("proposal_ref",1,1) GLOB '[0-9A-Za-z]'),
  "proposal_digest" ANY NOT NULL CHECK (typeof("proposal_digest")='text' AND length(CAST("proposal_digest" AS BLOB))=64 AND "proposal_digest" NOT GLOB '*[^0-9a-f]*'),
  "phase_basis_ref" ANY NOT NULL CHECK (typeof("phase_basis_ref")='text' AND length(CAST("phase_basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND "phase_basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("phase_basis_ref",1,1) GLOB '[0-9A-Za-z]'),
  "phase_basis_digest" ANY NOT NULL CHECK (typeof("phase_basis_digest")='text' AND length(CAST("phase_basis_digest" AS BLOB))=64 AND "phase_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "safe_basis_bytes" ANY NOT NULL CHECK (typeof("safe_basis_bytes")='blob' AND length("safe_basis_bytes") BETWEEN 1 AND 131072),
  "safe_basis_digest" ANY NOT NULL CHECK (typeof("safe_basis_digest")='text' AND length(CAST("safe_basis_digest" AS BLOB))=64 AND "safe_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "context_row_digest" ANY NOT NULL CHECK (typeof("context_row_digest")='text' AND length(CAST("context_row_digest" AS BLOB))=64 AND "context_row_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (context_ref),
  UNIQUE (proposal_phase,context_ref,context_digest),
  UNIQUE (proposal_phase,proposal_ref),
  FOREIGN KEY (proposal_phase,proposal_ref) REFERENCES development_model_proposals(proposal_phase,proposal_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (phase_basis_ref,phase_basis_digest) REFERENCES rw0_phase_instances(phase_basis_ref,phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE development_post_execution_proposal_receipts (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-section41-post-execution-proposal-receipt-row.v1'),
  "mutation_ref" ANY NOT NULL CHECK (typeof("mutation_ref")='text' AND length(CAST("mutation_ref" AS BLOB)) BETWEEN 1 AND 96 AND "mutation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("mutation_ref",1,1) GLOB '[0-9A-Za-z]'),
  "mutation_command_digest" ANY NOT NULL CHECK (typeof("mutation_command_digest")='text' AND length(CAST("mutation_command_digest" AS BLOB))=64 AND "mutation_command_digest" NOT GLOB '*[^0-9a-f]*'),
  "proposal_phase" ANY NOT NULL CHECK (typeof("proposal_phase")='text' AND "proposal_phase"='post_execution_semantic_review'),
  "context_ref" ANY NOT NULL CHECK (typeof("context_ref")='text' AND length(CAST("context_ref" AS BLOB)) BETWEEN 1 AND 96 AND "context_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("context_ref",1,1) GLOB '[0-9A-Za-z]'),
  "context_digest" ANY NOT NULL CHECK (typeof("context_digest")='text' AND length(CAST("context_digest" AS BLOB))=64 AND "context_digest" NOT GLOB '*[^0-9a-f]*'),
  "proposal_ref" ANY NOT NULL CHECK (typeof("proposal_ref")='text' AND length(CAST("proposal_ref" AS BLOB)) BETWEEN 1 AND 96 AND "proposal_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("proposal_ref",1,1) GLOB '[0-9A-Za-z]'),
  "proposal_digest" ANY NOT NULL CHECK (typeof("proposal_digest")='text' AND length(CAST("proposal_digest" AS BLOB))=64 AND "proposal_digest" NOT GLOB '*[^0-9a-f]*'),
  "phase_basis_ref" ANY NOT NULL CHECK (typeof("phase_basis_ref")='text' AND length(CAST("phase_basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND "phase_basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("phase_basis_ref",1,1) GLOB '[0-9A-Za-z]'),
  "phase_basis_digest" ANY NOT NULL CHECK (typeof("phase_basis_digest")='text' AND length(CAST("phase_basis_digest" AS BLOB))=64 AND "phase_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "source_invocation_ref" ANY NOT NULL CHECK (typeof("source_invocation_ref")='text' AND length(CAST("source_invocation_ref" AS BLOB)) BETWEEN 1 AND 96 AND "source_invocation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("source_invocation_ref",1,1) GLOB '[0-9A-Za-z]'),
  "source_invocation_digest" ANY NOT NULL CHECK (typeof("source_invocation_digest")='text' AND length(CAST("source_invocation_digest" AS BLOB))=64 AND "source_invocation_digest" NOT GLOB '*[^0-9a-f]*'),
  "artifact_ref" ANY NOT NULL CHECK (typeof("artifact_ref")='text' AND length(CAST("artifact_ref" AS BLOB)) BETWEEN 1 AND 96 AND "artifact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("artifact_ref",1,1) GLOB '[0-9A-Za-z]'),
  "artifact_digest" ANY NOT NULL CHECK (typeof("artifact_digest")='text' AND length(CAST("artifact_digest" AS BLOB))=64 AND "artifact_digest" NOT GLOB '*[^0-9a-f]*'),
  "artifact_binding_digest" ANY NOT NULL CHECK (typeof("artifact_binding_digest")='text' AND length(CAST("artifact_binding_digest" AS BLOB))=64 AND "artifact_binding_digest" NOT GLOB '*[^0-9a-f]*'),
  "evidence_set_ref" ANY NOT NULL CHECK (typeof("evidence_set_ref")='text' AND length(CAST("evidence_set_ref" AS BLOB)) BETWEEN 1 AND 96 AND "evidence_set_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("evidence_set_ref",1,1) GLOB '[0-9A-Za-z]'),
  "evidence_set_digest" ANY NOT NULL CHECK (typeof("evidence_set_digest")='text' AND length(CAST("evidence_set_digest" AS BLOB))=64 AND "evidence_set_digest" NOT GLOB '*[^0-9a-f]*'),
  "safe_basis_digest" ANY NOT NULL CHECK (typeof("safe_basis_digest")='text' AND length(CAST("safe_basis_digest" AS BLOB))=64 AND "safe_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "c1_mutation_ref" ANY NOT NULL CHECK (typeof("c1_mutation_ref")='text' AND length(CAST("c1_mutation_ref" AS BLOB)) BETWEEN 1 AND 96 AND "c1_mutation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("c1_mutation_ref",1,1) GLOB '[0-9A-Za-z]'),
  "c1_membership_ref" ANY NOT NULL CHECK (typeof("c1_membership_ref")='text' AND length(CAST("c1_membership_ref" AS BLOB)) BETWEEN 1 AND 96 AND "c1_membership_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND substr("c1_membership_ref",1,1) GLOB '[0-9A-Za-z]'),
  "mutation_graph_digest" ANY NOT NULL CHECK (typeof("mutation_graph_digest")='text' AND length(CAST("mutation_graph_digest" AS BLOB))=64 AND "mutation_graph_digest" NOT GLOB '*[^0-9a-f]*'),
  "committed_result_digest" ANY NOT NULL CHECK (typeof("committed_result_digest")='text' AND length(CAST("committed_result_digest" AS BLOB))=64 AND "committed_result_digest" NOT GLOB '*[^0-9a-f]*'),
  "committed_outcome" ANY NOT NULL CHECK (typeof("committed_outcome")='text' AND "committed_outcome"='proposal_recorded'),
  "committed_at" ANY NOT NULL CHECK (typeof("committed_at")='text' AND length("committed_at")=20 AND strftime('%Y-%m-%dT%H:%M:%SZ',"committed_at")="committed_at"),
  "receipt_digest" ANY NOT NULL CHECK (typeof("receipt_digest")='text' AND length(CAST("receipt_digest" AS BLOB))=64 AND "receipt_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (mutation_ref),
  UNIQUE (proposal_phase,proposal_ref),
  UNIQUE (proposal_phase,context_ref,context_digest),
  FOREIGN KEY (proposal_phase,context_ref,context_digest) REFERENCES development_post_execution_proposal_contexts(proposal_phase,context_ref,context_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (proposal_phase,proposal_ref) REFERENCES development_model_proposals(proposal_phase,proposal_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (phase_basis_ref,phase_basis_digest) REFERENCES rw0_phase_instances(phase_basis_ref,phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (proposal_phase,source_invocation_ref) REFERENCES development_model_source_invocations(proposal_phase,source_invocation_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (proposal_phase,artifact_ref) REFERENCES development_private_proposal_artifact_bindings(proposal_phase,artifact_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TRIGGER development_post_execution_proposal_contexts_no_update BEFORE UPDATE ON development_post_execution_proposal_contexts
BEGIN SELECT RAISE(ABORT,'immutable_development_post_execution_proposal_contexts'); END;
CREATE TRIGGER development_post_execution_proposal_contexts_no_delete BEFORE DELETE ON development_post_execution_proposal_contexts
BEGIN SELECT RAISE(ABORT,'immutable_development_post_execution_proposal_contexts'); END;
CREATE TRIGGER development_post_execution_proposal_receipts_no_update BEFORE UPDATE ON development_post_execution_proposal_receipts
BEGIN SELECT RAISE(ABORT,'immutable_development_post_execution_proposal_receipts'); END;
CREATE TRIGGER development_post_execution_proposal_receipts_no_delete BEFORE DELETE ON development_post_execution_proposal_receipts
BEGIN SELECT RAISE(ABORT,'immutable_development_post_execution_proposal_receipts'); END;
