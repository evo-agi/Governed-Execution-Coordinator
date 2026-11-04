-- RW0 artificial-offline active-cancel decision and proven-unusable pre-effect closure.

CREATE TABLE rw0_cancel_decision_evidence_bindings (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-cancel-decision-evidence-binding.v1'),
  binding_ref ANY NOT NULL CHECK (typeof(binding_ref)='text' AND length(CAST(binding_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(binding_ref,1,1) GLOB '[0-9A-Za-z]' AND binding_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  mutation_ref ANY NOT NULL CHECK (typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  program_ref ANY NOT NULL CHECK (typeof(program_ref)='text' AND length(CAST(program_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_ref ANY NOT NULL CHECK (typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_ref ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(phase_basis_ref,1,1) GLOB '[0-9A-Za-z]' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_digest ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  role ANY NOT NULL CHECK (typeof(role)='text' AND role IN ('cancel_target_effect','cancel_target_effect_fence','cancel_source_directive','cancel_source_evidence','cancel_target_capsule')),
  evidence_ref ANY NOT NULL CHECK (typeof(evidence_ref)='text' AND length(CAST(evidence_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(evidence_ref,1,1) GLOB '[0-9A-Za-z]' AND evidence_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  evidence_digest ANY NOT NULL CHECK (typeof(evidence_digest)='text' AND length(CAST(evidence_digest AS BLOB))=64 AND evidence_digest NOT GLOB '*[^0-9a-f]*'),
  binding_digest ANY NOT NULL CHECK (typeof(binding_digest)='text' AND length(CAST(binding_digest AS BLOB))=64 AND binding_digest NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (binding_ref),
  UNIQUE (decision_ref, role),
  UNIQUE (mutation_ref, role),
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE rw0_cancel_decision_receipts (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-cancel-decision-receipt.v1'),
  receipt_ref ANY NOT NULL CHECK (typeof(receipt_ref)='text' AND length(CAST(receipt_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(receipt_ref,1,1) GLOB '[0-9A-Za-z]' AND receipt_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  mutation_ref ANY NOT NULL CHECK (typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  command_schema_id ANY NOT NULL CHECK (typeof(command_schema_id)='text' AND command_schema_id='governed-execution.nwp-record-rw0-cancel-decision-command.v1'),
  command_digest ANY NOT NULL CHECK (typeof(command_digest)='text' AND length(CAST(command_digest AS BLOB))=64 AND command_digest NOT GLOB '*[^0-9a-f]*'),
  phase_basis_ref ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(phase_basis_ref,1,1) GLOB '[0-9A-Za-z]' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_digest ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  program_ref ANY NOT NULL CHECK (typeof(program_ref)='text' AND length(CAST(program_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  program_version_ref ANY NOT NULL CHECK (typeof(program_version_ref)='text' AND length(CAST(program_version_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(program_version_ref,1,1) GLOB '[0-9A-Za-z]' AND program_version_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  program_version_number ANY NOT NULL CHECK (typeof(program_version_number)='integer' AND program_version_number>=0),
  semantic_attempt_ref ANY NOT NULL CHECK (typeof(semantic_attempt_ref)='text' AND length(CAST(semantic_attempt_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(semantic_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND semantic_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_ref ANY NOT NULL CHECK (typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_digest ANY NOT NULL CHECK (typeof(decision_digest)='text' AND length(CAST(decision_digest AS BLOB))=64 AND decision_digest NOT GLOB '*[^0-9a-f]*'),
  target_effect_intent_ref ANY NOT NULL CHECK (typeof(target_effect_intent_ref)='text' AND length(CAST(target_effect_intent_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  target_effect_fence_ref ANY NOT NULL CHECK (typeof(target_effect_fence_ref)='text' AND length(CAST(target_effect_fence_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(target_effect_fence_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_fence_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  target_effect_fence_digest ANY NOT NULL CHECK (typeof(target_effect_fence_digest)='text' AND length(CAST(target_effect_fence_digest AS BLOB))=64 AND target_effect_fence_digest NOT GLOB '*[^0-9a-f]*'),
  target_effect_head_revision ANY NOT NULL CHECK (typeof(target_effect_head_revision)='integer' AND target_effect_head_revision>=0),
  target_effect_head_digest ANY NOT NULL CHECK (typeof(target_effect_head_digest)='text' AND length(CAST(target_effect_head_digest AS BLOB))=64 AND target_effect_head_digest NOT GLOB '*[^0-9a-f]*'),
  target_effect_head_postimage ANY NOT NULL CHECK (typeof(target_effect_head_postimage)='blob' AND length(target_effect_head_postimage) BETWEEN 2 AND 49152),
  target_delivery_attempt_ref ANY NOT NULL CHECK (typeof(target_delivery_attempt_ref)='text' AND length(CAST(target_delivery_attempt_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(target_delivery_attempt_ref,1,1) GLOB '[0-9A-Za-z]' AND target_delivery_attempt_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  target_delivery_head_revision ANY NOT NULL CHECK (typeof(target_delivery_head_revision)='integer' AND target_delivery_head_revision>=0),
  target_delivery_head_digest ANY NOT NULL CHECK (typeof(target_delivery_head_digest)='text' AND length(CAST(target_delivery_head_digest AS BLOB))=64 AND target_delivery_head_digest NOT GLOB '*[^0-9a-f]*'),
  target_delivery_head_postimage ANY NOT NULL CHECK (typeof(target_delivery_head_postimage)='blob' AND length(target_delivery_head_postimage) BETWEEN 2 AND 49152),
  basis_safe_bytes ANY NOT NULL CHECK (typeof(basis_safe_bytes)='blob' AND length(basis_safe_bytes) BETWEEN 2 AND 49152),
  command_safe_bytes ANY NOT NULL CHECK (typeof(command_safe_bytes)='blob' AND length(command_safe_bytes) BETWEEN 2 AND 49152),
  authority_evidence_bytes ANY NOT NULL CHECK (typeof(authority_evidence_bytes)='blob' AND length(authority_evidence_bytes) BETWEEN 2 AND 49152),
  recorded_at ANY NOT NULL CHECK (typeof(recorded_at)='text' AND length(CAST(recorded_at AS BLOB))=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at),
  result_digest ANY NOT NULL CHECK (typeof(result_digest)='text' AND length(CAST(result_digest AS BLOB))=64 AND result_digest NOT GLOB '*[^0-9a-f]*'),
  receipt_digest ANY NOT NULL CHECK (typeof(receipt_digest)='text' AND length(CAST(receipt_digest AS BLOB))=64 AND receipt_digest NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (receipt_ref),
  UNIQUE (mutation_ref),
  UNIQUE (phase_basis_ref),
  UNIQUE (decision_ref),
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref) REFERENCES development_program_heads (program_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, program_version_ref) REFERENCES development_program_versions (program_ref, program_version_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, semantic_attempt_ref) REFERENCES development_semantic_attempts (program_ref, semantic_attempt_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, target_effect_intent_ref) REFERENCES development_effect_intents (program_ref, effect_intent_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, target_effect_fence_ref) REFERENCES development_effect_fences (program_ref, effect_fence_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, target_delivery_attempt_ref) REFERENCES development_delivery_attempts (program_ref, delivery_attempt_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE rw0_cancel_pre_effect_contexts (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-cancel-pre-effect-context.v1'),
  context_ref ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(context_ref,1,1) GLOB '[0-9A-Za-z]' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  context_digest ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  profile ANY NOT NULL CHECK (typeof(profile)='text' AND profile='artificial_offline_cancel_pre_effect_block.v1'),
  mutation_ref ANY NOT NULL CHECK (typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_ref ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(phase_basis_ref,1,1) GLOB '[0-9A-Za-z]' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_digest ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  program_ref ANY NOT NULL CHECK (typeof(program_ref)='text' AND length(CAST(program_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(program_ref,1,1) GLOB '[0-9A-Za-z]' AND program_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_ref ANY NOT NULL CHECK (typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_digest ANY NOT NULL CHECK (typeof(decision_digest)='text' AND length(CAST(decision_digest AS BLOB))=64 AND decision_digest NOT GLOB '*[^0-9a-f]*'),
  decision_receipt_ref ANY NOT NULL CHECK (typeof(decision_receipt_ref)='text' AND length(CAST(decision_receipt_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_receipt_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_receipt_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_receipt_digest ANY NOT NULL CHECK (typeof(decision_receipt_digest)='text' AND length(CAST(decision_receipt_digest AS BLOB))=64 AND decision_receipt_digest NOT GLOB '*[^0-9a-f]*'),
  target_effect_intent_ref ANY NOT NULL CHECK (typeof(target_effect_intent_ref)='text' AND length(CAST(target_effect_intent_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(target_effect_intent_ref,1,1) GLOB '[0-9A-Za-z]' AND target_effect_intent_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  mismatch_class ANY NOT NULL CHECK (typeof(mismatch_class)='text' AND mismatch_class IN ('program_head','program_version','semantic_attempt','effect_head','delivery_head','global_stop','attempt_fence','effect_fence','preassignment','persisted_basis')),
  mismatch_ref ANY NOT NULL CHECK (typeof(mismatch_ref)='text' AND length(CAST(mismatch_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mismatch_ref,1,1) GLOB '[0-9A-Za-z]' AND mismatch_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  mismatch_digest ANY NOT NULL CHECK (typeof(mismatch_digest)='text' AND length(CAST(mismatch_digest AS BLOB))=64 AND mismatch_digest NOT GLOB '*[^0-9a-f]*'),
  verification_safe_bytes ANY NOT NULL CHECK (typeof(verification_safe_bytes)='blob' AND length(verification_safe_bytes) BETWEEN 2 AND 49152),
  closure_heads_bytes ANY NOT NULL CHECK (typeof(closure_heads_bytes)='blob' AND length(closure_heads_bytes) BETWEEN 2 AND 49152),
  closure_stop_bytes ANY NOT NULL CHECK (typeof(closure_stop_bytes)='blob' AND length(closure_stop_bytes) BETWEEN 2 AND 49152),
  command_safe_bytes ANY NOT NULL CHECK (typeof(command_safe_bytes)='blob' AND length(command_safe_bytes) BETWEEN 2 AND 49152),
  recorded_at ANY NOT NULL CHECK (typeof(recorded_at)='text' AND length(CAST(recorded_at AS BLOB))=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at),
  PRIMARY KEY (context_ref),
  UNIQUE (mutation_ref),
  UNIQUE (decision_ref),
  UNIQUE (decision_receipt_ref),
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (decision_receipt_ref) REFERENCES rw0_cancel_decision_receipts (receipt_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE rw0_cancel_pre_effect_outcomes (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-cancel-pre-effect-outcome.v1'),
  outcome_value_ref ANY NOT NULL CHECK (typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(outcome_value_ref,1,1) GLOB '[0-9A-Za-z]' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  outcome_value_digest ANY NOT NULL CHECK (typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'),
  context_ref ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(context_ref,1,1) GLOB '[0-9A-Za-z]' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  context_digest ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  phase_basis_ref ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(phase_basis_ref,1,1) GLOB '[0-9A-Za-z]' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_digest ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  branch ANY NOT NULL CHECK (typeof(branch)='text' AND branch='pre_effect_cancel_basis_unusable'),
  outcome ANY NOT NULL CHECK (typeof(outcome)='text' AND outcome='block'),
  decision_ref ANY NOT NULL CHECK (typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  decision_digest ANY NOT NULL CHECK (typeof(decision_digest)='text' AND length(CAST(decision_digest AS BLOB))=64 AND decision_digest NOT GLOB '*[^0-9a-f]*'),
  decision_kind ANY NOT NULL CHECK (typeof(decision_kind)='text' AND decision_kind='cancel'),
  mismatch_ref ANY NOT NULL CHECK (typeof(mismatch_ref)='text' AND length(CAST(mismatch_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mismatch_ref,1,1) GLOB '[0-9A-Za-z]' AND mismatch_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  mismatch_digest ANY NOT NULL CHECK (typeof(mismatch_digest)='text' AND length(CAST(mismatch_digest AS BLOB))=64 AND mismatch_digest NOT GLOB '*[^0-9a-f]*'),
  closure_heads_bytes ANY NOT NULL CHECK (typeof(closure_heads_bytes)='blob' AND length(closure_heads_bytes) BETWEEN 2 AND 49152),
  closure_stop_bytes ANY NOT NULL CHECK (typeof(closure_stop_bytes)='blob' AND length(closure_stop_bytes) BETWEEN 2 AND 49152),
  PRIMARY KEY (outcome_value_ref),
  UNIQUE (context_ref),
  UNIQUE (decision_ref),
  FOREIGN KEY (context_ref) REFERENCES rw0_cancel_pre_effect_contexts (context_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (decision_ref) REFERENCES development_decisions (decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (phase_basis_ref, phase_basis_digest) REFERENCES rw0_phase_instances (phase_basis_ref, phase_basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE rw0_cancel_pre_effect_results (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-cancel-pre-effect-result.v1'),
  result_ref ANY NOT NULL CHECK (typeof(result_ref)='text' AND length(CAST(result_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(result_ref,1,1) GLOB '[0-9A-Za-z]' AND result_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  result_digest ANY NOT NULL CHECK (typeof(result_digest)='text' AND length(CAST(result_digest AS BLOB))=64 AND result_digest NOT GLOB '*[^0-9a-f]*'),
  outcome_value_ref ANY NOT NULL CHECK (typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(outcome_value_ref,1,1) GLOB '[0-9A-Za-z]' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  outcome_value_digest ANY NOT NULL CHECK (typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'),
  context_ref ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(context_ref,1,1) GLOB '[0-9A-Za-z]' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  context_digest ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  branch ANY NOT NULL CHECK (typeof(branch)='text' AND branch='pre_effect_cancel_basis_unusable'),
  outcome ANY NOT NULL CHECK (typeof(outcome)='text' AND outcome='block'),
  recorded_at ANY NOT NULL CHECK (typeof(recorded_at)='text' AND length(CAST(recorded_at AS BLOB))=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at),
  PRIMARY KEY (result_ref),
  UNIQUE (outcome_value_ref),
  UNIQUE (context_ref),
  FOREIGN KEY (context_ref) REFERENCES rw0_cancel_pre_effect_contexts (context_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (outcome_value_ref) REFERENCES rw0_cancel_pre_effect_outcomes (outcome_value_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TABLE rw0_cancel_pre_effect_receipts (
  schema_id ANY NOT NULL CHECK (typeof(schema_id)='text' AND schema_id='governed-execution.nwp-rw0-cancel-pre-effect-receipt.v1'),
  receipt_ref ANY NOT NULL CHECK (typeof(receipt_ref)='text' AND length(CAST(receipt_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(receipt_ref,1,1) GLOB '[0-9A-Za-z]' AND receipt_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  receipt_digest ANY NOT NULL CHECK (typeof(receipt_digest)='text' AND length(CAST(receipt_digest AS BLOB))=64 AND receipt_digest NOT GLOB '*[^0-9a-f]*'),
  mutation_ref ANY NOT NULL CHECK (typeof(mutation_ref)='text' AND length(CAST(mutation_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(mutation_ref,1,1) GLOB '[0-9A-Za-z]' AND mutation_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  command_digest ANY NOT NULL CHECK (typeof(command_digest)='text' AND length(CAST(command_digest AS BLOB))=64 AND command_digest NOT GLOB '*[^0-9a-f]*'),
  profile ANY NOT NULL CHECK (typeof(profile)='text' AND profile='artificial_offline_cancel_pre_effect_block.v1'),
  family_route ANY NOT NULL CHECK (typeof(family_route)='text' AND length(CAST(family_route AS BLOB)) BETWEEN 1 AND 96 AND substr(family_route,1,1) GLOB '[0-9A-Za-z]' AND family_route NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_ref ANY NOT NULL CHECK (typeof(phase_basis_ref)='text' AND length(CAST(phase_basis_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(phase_basis_ref,1,1) GLOB '[0-9A-Za-z]' AND phase_basis_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  phase_basis_digest ANY NOT NULL CHECK (typeof(phase_basis_digest)='text' AND length(CAST(phase_basis_digest AS BLOB))=64 AND phase_basis_digest NOT GLOB '*[^0-9a-f]*'),
  decision_ref ANY NOT NULL CHECK (typeof(decision_ref)='text' AND length(CAST(decision_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(decision_ref,1,1) GLOB '[0-9A-Za-z]' AND decision_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  context_ref ANY NOT NULL CHECK (typeof(context_ref)='text' AND length(CAST(context_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(context_ref,1,1) GLOB '[0-9A-Za-z]' AND context_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  context_digest ANY NOT NULL CHECK (typeof(context_digest)='text' AND length(CAST(context_digest AS BLOB))=64 AND context_digest NOT GLOB '*[^0-9a-f]*'),
  outcome_value_ref ANY NOT NULL CHECK (typeof(outcome_value_ref)='text' AND length(CAST(outcome_value_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(outcome_value_ref,1,1) GLOB '[0-9A-Za-z]' AND outcome_value_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  outcome_value_digest ANY NOT NULL CHECK (typeof(outcome_value_digest)='text' AND length(CAST(outcome_value_digest AS BLOB))=64 AND outcome_value_digest NOT GLOB '*[^0-9a-f]*'),
  result_ref ANY NOT NULL CHECK (typeof(result_ref)='text' AND length(CAST(result_ref AS BLOB)) BETWEEN 1 AND 96 AND substr(result_ref,1,1) GLOB '[0-9A-Za-z]' AND result_ref NOT GLOB '*[^0-9A-Za-z.-]*'),
  result_digest ANY NOT NULL CHECK (typeof(result_digest)='text' AND length(CAST(result_digest AS BLOB))=64 AND result_digest NOT GLOB '*[^0-9a-f]*'),
  graph_profile ANY NOT NULL CHECK (typeof(graph_profile)='text' AND graph_profile='governed-execution.nwp-rw0-terminal-cancel-pre-effect-block-graph.v1'),
  graph_digest ANY NOT NULL CHECK (typeof(graph_digest)='text' AND length(CAST(graph_digest AS BLOB))=64 AND graph_digest NOT GLOB '*[^0-9a-f]*'),
  committed_result_digest ANY NOT NULL CHECK (typeof(committed_result_digest)='text' AND length(CAST(committed_result_digest AS BLOB))=64 AND committed_result_digest NOT GLOB '*[^0-9a-f]*'),
  recorded_at ANY NOT NULL CHECK (typeof(recorded_at)='text' AND length(CAST(recorded_at AS BLOB))=20 AND recorded_at GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',recorded_at)=recorded_at),
  PRIMARY KEY (receipt_ref),
  UNIQUE (mutation_ref),
  UNIQUE (family_route),
  UNIQUE (decision_ref),
  UNIQUE (context_ref),
  UNIQUE (outcome_value_ref),
  UNIQUE (result_ref),
  FOREIGN KEY (context_ref) REFERENCES rw0_cancel_pre_effect_contexts (context_ref) ON UPDATE RESTRICT ON DELETE RESTRICT,
  FOREIGN KEY (result_ref) REFERENCES rw0_cancel_pre_effect_results (result_ref) ON UPDATE RESTRICT ON DELETE RESTRICT
) STRICT;

CREATE TRIGGER rw0_cancel_decision_evidence_bindings_no_update BEFORE UPDATE ON rw0_cancel_decision_evidence_bindings
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_decision_evidence_bindings'); END;

CREATE TRIGGER rw0_cancel_decision_evidence_bindings_no_delete BEFORE DELETE ON rw0_cancel_decision_evidence_bindings
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_decision_evidence_bindings'); END;

CREATE TRIGGER rw0_cancel_decision_receipts_no_update BEFORE UPDATE ON rw0_cancel_decision_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_decision_receipts'); END;

CREATE TRIGGER rw0_cancel_decision_receipts_no_delete BEFORE DELETE ON rw0_cancel_decision_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_decision_receipts'); END;

CREATE TRIGGER rw0_cancel_pre_effect_contexts_no_update BEFORE UPDATE ON rw0_cancel_pre_effect_contexts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_contexts'); END;

CREATE TRIGGER rw0_cancel_pre_effect_contexts_no_delete BEFORE DELETE ON rw0_cancel_pre_effect_contexts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_contexts'); END;

CREATE TRIGGER rw0_cancel_pre_effect_outcomes_no_update BEFORE UPDATE ON rw0_cancel_pre_effect_outcomes
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_outcomes'); END;

CREATE TRIGGER rw0_cancel_pre_effect_outcomes_no_delete BEFORE DELETE ON rw0_cancel_pre_effect_outcomes
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_outcomes'); END;

CREATE TRIGGER rw0_cancel_pre_effect_results_no_update BEFORE UPDATE ON rw0_cancel_pre_effect_results
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_results'); END;

CREATE TRIGGER rw0_cancel_pre_effect_results_no_delete BEFORE DELETE ON rw0_cancel_pre_effect_results
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_results'); END;

CREATE TRIGGER rw0_cancel_pre_effect_receipts_no_update BEFORE UPDATE ON rw0_cancel_pre_effect_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_receipts'); END;

CREATE TRIGGER rw0_cancel_pre_effect_receipts_no_delete BEFORE DELETE ON rw0_cancel_pre_effect_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_cancel_pre_effect_receipts'); END;

DROP TRIGGER rw0_terminal_anchors_require_registered_family;

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
  ) AND NOT EXISTS (
    SELECT 1 FROM rw0_cancel_pre_effect_receipts AS r
    JOIN rw0_cancel_pre_effect_contexts AS c ON c.context_ref=r.context_ref AND c.context_digest=r.context_digest
    JOIN rw0_cancel_pre_effect_outcomes AS o ON o.outcome_value_ref=r.outcome_value_ref AND o.outcome_value_digest=r.outcome_value_digest
    JOIN rw0_cancel_pre_effect_results AS x ON x.result_ref=r.result_ref AND x.result_digest=r.result_digest
    JOIN rw0_cancel_decision_receipts AS d ON d.receipt_ref=c.decision_receipt_ref AND d.receipt_digest=c.decision_receipt_digest
    JOIN development_decisions AS q ON q.decision_ref=c.decision_ref AND q.decision_digest=c.decision_digest
    WHERE r.receipt_ref=NEW.receipt_ref AND r.receipt_digest=NEW.receipt_digest
      AND r.profile='artificial_offline_cancel_pre_effect_block.v1' AND r.graph_profile='governed-execution.nwp-rw0-terminal-cancel-pre-effect-block-graph.v1'
      AND c.profile=r.profile AND c.recorded_at=r.recorded_at
      AND o.branch='pre_effect_cancel_basis_unusable' AND o.outcome='block'
      AND x.branch=o.branch AND x.outcome=o.outcome AND x.recorded_at=r.recorded_at
      AND q.decision_kind='cancel' AND q.decision_variant='effect_cancellation'
      AND d.decision_ref=q.decision_ref AND d.decision_digest=q.decision_digest
      AND c.program_ref=q.program_ref AND c.target_effect_intent_ref=q.target_effect_intent_ref
      AND c.phase_basis_ref=d.phase_basis_ref AND c.phase_basis_digest=d.phase_basis_digest
      AND c.decision_ref=r.decision_ref AND o.decision_ref=c.decision_ref AND o.decision_digest=c.decision_digest
      AND o.decision_kind='cancel' AND o.mismatch_ref=c.mismatch_ref AND o.mismatch_digest=c.mismatch_digest
      AND o.closure_heads_bytes=c.closure_heads_bytes AND o.closure_stop_bytes=c.closure_stop_bytes
      AND x.context_ref=c.context_ref AND x.context_digest=c.context_digest
      AND x.outcome_value_ref=o.outcome_value_ref AND x.outcome_value_digest=o.outcome_value_digest
      AND r.phase_basis_ref=NEW.phase_basis_ref AND r.phase_basis_digest=NEW.phase_basis_digest
      AND r.profile=NEW.family_profile AND r.family_route=NEW.family_route
      AND r.mutation_ref=NEW.mutation_ref AND r.command_digest=NEW.command_digest
      AND c.program_ref=NEW.program_ref AND r.decision_ref=NEW.decision_ref
      AND r.context_ref=NEW.context_ref AND r.context_digest=NEW.context_digest
      AND r.outcome_value_ref=NEW.outcome_value_ref AND r.outcome_value_digest=NEW.outcome_value_digest
      AND r.result_ref=NEW.result_ref AND r.result_digest=NEW.result_digest
      AND r.graph_profile=NEW.graph_profile AND r.graph_digest=NEW.graph_digest
      AND r.committed_result_digest=NEW.committed_result_digest AND r.recorded_at=NEW.recorded_at
      AND c.mutation_ref=r.mutation_ref AND c.phase_basis_ref=r.phase_basis_ref AND c.phase_basis_digest=r.phase_basis_digest
      AND o.context_ref=c.context_ref AND o.context_digest=c.context_digest
      AND o.phase_basis_ref=c.phase_basis_ref AND o.phase_basis_digest=c.phase_basis_digest
  );
END;

CREATE TRIGGER rw0_cancel_pre_effect_receipts_register_anchor AFTER INSERT ON rw0_cancel_pre_effect_receipts
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
    r.mutation_ref, r.command_digest, c.program_ref, r.decision_ref,
    r.context_ref, r.context_digest, r.outcome_value_ref, r.outcome_value_digest,
    r.result_ref, r.result_digest, r.receipt_ref, r.receipt_digest,
    r.graph_profile, r.graph_digest, r.committed_result_digest, r.recorded_at
  FROM rw0_cancel_pre_effect_receipts AS r
  JOIN rw0_cancel_pre_effect_contexts AS c ON c.context_ref=r.context_ref AND c.context_digest=r.context_digest
  JOIN rw0_cancel_pre_effect_outcomes AS o ON o.outcome_value_ref=r.outcome_value_ref AND o.outcome_value_digest=r.outcome_value_digest
  JOIN rw0_cancel_pre_effect_results AS x ON x.result_ref=r.result_ref AND x.result_digest=r.result_digest
  WHERE r.receipt_ref=NEW.receipt_ref AND c.profile=r.profile AND c.recorded_at=r.recorded_at
    AND c.mutation_ref=r.mutation_ref AND c.phase_basis_ref=r.phase_basis_ref AND c.phase_basis_digest=r.phase_basis_digest
    AND c.decision_ref=r.decision_ref AND o.context_ref=c.context_ref AND o.context_digest=c.context_digest
    AND o.phase_basis_ref=c.phase_basis_ref AND o.phase_basis_digest=c.phase_basis_digest
    AND o.outcome_value_ref=r.outcome_value_ref AND o.outcome_value_digest=r.outcome_value_digest
    AND o.decision_ref=c.decision_ref AND o.decision_digest=c.decision_digest
    AND o.decision_kind='cancel' AND o.mismatch_ref=c.mismatch_ref AND o.mismatch_digest=c.mismatch_digest
    AND o.closure_heads_bytes=c.closure_heads_bytes AND o.closure_stop_bytes=c.closure_stop_bytes
    AND x.context_ref=c.context_ref AND x.context_digest=c.context_digest
    AND x.outcome_value_ref=o.outcome_value_ref AND x.outcome_value_digest=o.outcome_value_digest
    AND x.branch=o.branch AND x.outcome=o.outcome AND x.recorded_at=r.recorded_at
    AND r.profile='artificial_offline_cancel_pre_effect_block.v1' AND r.graph_profile='governed-execution.nwp-rw0-terminal-cancel-pre-effect-block-graph.v1'
    AND o.branch='pre_effect_cancel_basis_unusable' AND o.outcome='block';
  SELECT RAISE(ABORT,'missing_rw0_terminal_anchor') WHERE NOT EXISTS (
    SELECT 1 FROM rw0_terminal_anchors AS a
    WHERE a.phase_basis_ref=NEW.phase_basis_ref AND a.phase_basis_digest=NEW.phase_basis_digest
      AND a.receipt_ref=NEW.receipt_ref AND a.receipt_digest=NEW.receipt_digest
      AND a.family_profile=NEW.profile AND a.family_route=NEW.family_route
      AND a.mutation_ref=NEW.mutation_ref AND a.command_digest=NEW.command_digest
      AND a.decision_ref=NEW.decision_ref
      AND a.context_ref=NEW.context_ref AND a.context_digest=NEW.context_digest
      AND a.outcome_value_ref=NEW.outcome_value_ref AND a.outcome_value_digest=NEW.outcome_value_digest
      AND a.result_ref=NEW.result_ref AND a.result_digest=NEW.result_digest
      AND a.graph_profile=NEW.graph_profile AND a.graph_digest=NEW.graph_digest
      AND a.committed_result_digest=NEW.committed_result_digest AND a.recorded_at=NEW.recorded_at
  );
END;
