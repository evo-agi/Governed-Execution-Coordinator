CREATE TABLE rw0_c2_historical_continuity_bases (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-verified-lineage-continuity.v1'),
  "basis_ref" ANY NOT NULL CHECK (typeof("basis_ref")='text' AND length(CAST("basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("basis_ref",1,instr("basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "source_ref" ANY NOT NULL CHECK (typeof("source_ref")='text' AND length(CAST("source_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("source_ref",1,1) GLOB '[0-9A-Za-z]' AND "source_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("source_ref",1,instr("source_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "source_digest" ANY NOT NULL CHECK (typeof("source_digest")='text' AND length(CAST("source_digest" AS BLOB))=64 AND "source_digest" NOT GLOB '*[^0-9a-f]*'),
  "lineage_ref" ANY NOT NULL CHECK (typeof("lineage_ref")='text' AND length(CAST("lineage_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("lineage_ref",1,1) GLOB '[0-9A-Za-z]' AND "lineage_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("lineage_ref",1,instr("lineage_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof("scope_ref")='text' AND length(CAST("scope_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("scope_ref",1,1) GLOB '[0-9A-Za-z]' AND "scope_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("scope_ref",1,instr("scope_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "authority_epoch_ref" ANY NOT NULL CHECK (typeof("authority_epoch_ref")='text' AND length(CAST("authority_epoch_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("authority_epoch_ref",1,1) GLOB '[0-9A-Za-z]' AND "authority_epoch_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("authority_epoch_ref",1,instr("authority_epoch_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "currentness_ref" ANY NOT NULL CHECK (typeof("currentness_ref")='text' AND length(CAST("currentness_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("currentness_ref",1,1) GLOB '[0-9A-Za-z]' AND "currentness_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("currentness_ref",1,instr("currentness_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "currentness_digest" ANY NOT NULL CHECK (typeof("currentness_digest")='text' AND length(CAST("currentness_digest" AS BLOB))=64 AND "currentness_digest" NOT GLOB '*[^0-9a-f]*'),
  "provenance_ref" ANY NOT NULL CHECK (typeof("provenance_ref")='text' AND length(CAST("provenance_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("provenance_ref",1,1) GLOB '[0-9A-Za-z]' AND "provenance_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("provenance_ref",1,instr("provenance_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "provenance_digest" ANY NOT NULL CHECK (typeof("provenance_digest")='text' AND length(CAST("provenance_digest" AS BLOB))=64 AND "provenance_digest" NOT GLOB '*[^0-9a-f]*'),
  "projection_digest" ANY NOT NULL CHECK (typeof("projection_digest")='text' AND length(CAST("projection_digest" AS BLOB))=64 AND "projection_digest" NOT GLOB '*[^0-9a-f]*'),
  "program_ref" ANY NOT NULL CHECK (typeof("program_ref")='text' AND length(CAST("program_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("program_ref",1,1) GLOB '[0-9A-Za-z]' AND "program_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("program_ref",1,instr("program_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "captured_at" ANY NOT NULL CHECK (typeof("captured_at")='text' AND length("captured_at")=20 AND "captured_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"captured_at")="captured_at"),
  PRIMARY KEY (basis_ref),
  UNIQUE (basis_ref, projection_digest),
  FOREIGN KEY (program_ref) REFERENCES development_program_heads (program_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (admission_fact_ref) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE rw0_c2_historical_sole_active_bases (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-verified-sole-active.v1'),
  "basis_ref" ANY NOT NULL CHECK (typeof("basis_ref")='text' AND length(CAST("basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("basis_ref",1,instr("basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "source_ref" ANY NOT NULL CHECK (typeof("source_ref")='text' AND length(CAST("source_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("source_ref",1,1) GLOB '[0-9A-Za-z]' AND "source_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("source_ref",1,instr("source_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "source_digest" ANY NOT NULL CHECK (typeof("source_digest")='text' AND length(CAST("source_digest" AS BLOB))=64 AND "source_digest" NOT GLOB '*[^0-9a-f]*'),
  "lineage_ref" ANY NOT NULL CHECK (typeof("lineage_ref")='text' AND length(CAST("lineage_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("lineage_ref",1,1) GLOB '[0-9A-Za-z]' AND "lineage_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("lineage_ref",1,instr("lineage_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof("scope_ref")='text' AND length(CAST("scope_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("scope_ref",1,1) GLOB '[0-9A-Za-z]' AND "scope_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("scope_ref",1,instr("scope_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "authority_epoch_ref" ANY NOT NULL CHECK (typeof("authority_epoch_ref")='text' AND length(CAST("authority_epoch_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("authority_epoch_ref",1,1) GLOB '[0-9A-Za-z]' AND "authority_epoch_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("authority_epoch_ref",1,instr("authority_epoch_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "currentness_ref" ANY NOT NULL CHECK (typeof("currentness_ref")='text' AND length(CAST("currentness_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("currentness_ref",1,1) GLOB '[0-9A-Za-z]' AND "currentness_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("currentness_ref",1,instr("currentness_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "currentness_digest" ANY NOT NULL CHECK (typeof("currentness_digest")='text' AND length(CAST("currentness_digest" AS BLOB))=64 AND "currentness_digest" NOT GLOB '*[^0-9a-f]*'),
  "active_authority_ref" ANY NOT NULL CHECK (typeof("active_authority_ref")='text' AND length(CAST("active_authority_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("active_authority_ref",1,1) GLOB '[0-9A-Za-z]' AND "active_authority_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("active_authority_ref",1,instr("active_authority_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "sole_active_assertion_ref" ANY NOT NULL CHECK (typeof("sole_active_assertion_ref")='text' AND length(CAST("sole_active_assertion_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("sole_active_assertion_ref",1,1) GLOB '[0-9A-Za-z]' AND "sole_active_assertion_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("sole_active_assertion_ref",1,instr("sole_active_assertion_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "sole_active_assertion_digest" ANY NOT NULL CHECK (typeof("sole_active_assertion_digest")='text' AND length(CAST("sole_active_assertion_digest" AS BLOB))=64 AND "sole_active_assertion_digest" NOT GLOB '*[^0-9a-f]*'),
  "provenance_ref" ANY NOT NULL CHECK (typeof("provenance_ref")='text' AND length(CAST("provenance_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("provenance_ref",1,1) GLOB '[0-9A-Za-z]' AND "provenance_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("provenance_ref",1,instr("provenance_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "provenance_digest" ANY NOT NULL CHECK (typeof("provenance_digest")='text' AND length(CAST("provenance_digest" AS BLOB))=64 AND "provenance_digest" NOT GLOB '*[^0-9a-f]*'),
  "projection_digest" ANY NOT NULL CHECK (typeof("projection_digest")='text' AND length(CAST("projection_digest" AS BLOB))=64 AND "projection_digest" NOT GLOB '*[^0-9a-f]*'),
  "program_ref" ANY NOT NULL CHECK (typeof("program_ref")='text' AND length(CAST("program_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("program_ref",1,1) GLOB '[0-9A-Za-z]' AND "program_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("program_ref",1,instr("program_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "captured_at" ANY NOT NULL CHECK (typeof("captured_at")='text' AND length("captured_at")=20 AND "captured_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"captured_at")="captured_at"),
  PRIMARY KEY (basis_ref),
  UNIQUE (basis_ref, projection_digest),
  FOREIGN KEY (program_ref) REFERENCES development_program_heads (program_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (admission_fact_ref) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE rw0_c2_decision_bases (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-decision-basis.v2'),
  "basis_ref" ANY NOT NULL CHECK (typeof("basis_ref")='text' AND length(CAST("basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("basis_ref",1,instr("basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "mutation_ref" ANY NOT NULL CHECK (typeof("mutation_ref")='text' AND length(CAST("mutation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("mutation_ref",1,1) GLOB '[0-9A-Za-z]' AND "mutation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("mutation_ref",1,instr("mutation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "program_ref" ANY NOT NULL CHECK (typeof("program_ref")='text' AND length(CAST("program_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("program_ref",1,1) GLOB '[0-9A-Za-z]' AND "program_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("program_ref",1,instr("program_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_digest" ANY NOT NULL CHECK (typeof("admission_fact_digest")='text' AND length(CAST("admission_fact_digest" AS BLOB))=64 AND "admission_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  "continuity_basis_ref" ANY NOT NULL CHECK (typeof("continuity_basis_ref")='text' AND length(CAST("continuity_basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("continuity_basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "continuity_basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("continuity_basis_ref",1,instr("continuity_basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "continuity_basis_digest" ANY NOT NULL CHECK (typeof("continuity_basis_digest")='text' AND length(CAST("continuity_basis_digest" AS BLOB))=64 AND "continuity_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "sole_active_basis_ref" ANY NOT NULL CHECK (typeof("sole_active_basis_ref")='text' AND length(CAST("sole_active_basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("sole_active_basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "sole_active_basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("sole_active_basis_ref",1,instr("sole_active_basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "sole_active_basis_digest" ANY NOT NULL CHECK (typeof("sole_active_basis_digest")='text' AND length(CAST("sole_active_basis_digest" AS BLOB))=64 AND "sole_active_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "current_program_version_ref" ANY NOT NULL CHECK (typeof("current_program_version_ref")='text' AND length(CAST("current_program_version_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("current_program_version_ref",1,1) GLOB '[0-9A-Za-z]' AND "current_program_version_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("current_program_version_ref",1,instr("current_program_version_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "selected_attempt_ref" ANY NOT NULL CHECK (typeof("selected_attempt_ref")='text' AND length(CAST("selected_attempt_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("selected_attempt_ref",1,1) GLOB '[0-9A-Za-z]' AND "selected_attempt_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("selected_attempt_ref",1,instr("selected_attempt_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "selected_candidate_ref" ANY NOT NULL CHECK (typeof("selected_candidate_ref")='text' AND length(CAST("selected_candidate_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("selected_candidate_ref",1,1) GLOB '[0-9A-Za-z]' AND "selected_candidate_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("selected_candidate_ref",1,instr("selected_candidate_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "selected_fence_ref" ANY NOT NULL CHECK (typeof("selected_fence_ref")='text' AND length(CAST("selected_fence_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("selected_fence_ref",1,1) GLOB '[0-9A-Za-z]' AND "selected_fence_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("selected_fence_ref",1,instr("selected_fence_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "selected_fence_digest" ANY NOT NULL CHECK (typeof("selected_fence_digest")='text' AND length(CAST("selected_fence_digest" AS BLOB))=64 AND "selected_fence_digest" NOT GLOB '*[^0-9a-f]*'),
  "branch" ANY NOT NULL CHECK (typeof("branch")='text' AND "branch" IN ('candidate_acceptance','candidate_repair','attempt_selecting_replan','program_terminal_reject','post_execution_program_block')),
  "basis_bytes" ANY NOT NULL CHECK (typeof("basis_bytes")='blob' AND length("basis_bytes") BETWEEN 1 AND 49152),
  "basis_digest" ANY NOT NULL CHECK (typeof("basis_digest")='text' AND length(CAST("basis_digest" AS BLOB))=64 AND "basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "captured_at" ANY NOT NULL CHECK (typeof("captured_at")='text' AND length("captured_at")=20 AND "captured_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"captured_at")="captured_at"),
  PRIMARY KEY (basis_ref),
  UNIQUE (mutation_ref),
  UNIQUE (basis_ref, basis_digest),
  FOREIGN KEY (program_ref) REFERENCES development_program_heads (program_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (admission_fact_ref, admission_fact_digest) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref, admission_fact_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (continuity_basis_ref, continuity_basis_digest) REFERENCES rw0_c2_historical_continuity_bases (basis_ref, projection_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (sole_active_basis_ref, sole_active_basis_digest) REFERENCES rw0_c2_historical_sole_active_bases (basis_ref, projection_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (program_ref, current_program_version_ref) REFERENCES development_program_versions (program_ref, program_version_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE rw0_c2_guarded_family_relations (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-guarded-family-relation.v2'),
  "relation_ref" ANY NOT NULL CHECK (typeof("relation_ref")='text' AND length(CAST("relation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("relation_ref",1,1) GLOB '[0-9A-Za-z]' AND "relation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("relation_ref",1,instr("relation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "branch" ANY NOT NULL CHECK (typeof("branch")='text' AND "branch" IN ('candidate_acceptance','candidate_repair','attempt_selecting_replan','program_terminal_reject','post_execution_program_block')),
  "lineage_ref" ANY NOT NULL CHECK (typeof("lineage_ref")='text' AND length(CAST("lineage_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("lineage_ref",1,1) GLOB '[0-9A-Za-z]' AND "lineage_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("lineage_ref",1,instr("lineage_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof("scope_ref")='text' AND length(CAST("scope_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("scope_ref",1,1) GLOB '[0-9A-Za-z]' AND "scope_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("scope_ref",1,instr("scope_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "command_digest" ANY NOT NULL CHECK (typeof("command_digest")='text' AND length(CAST("command_digest" AS BLOB))=64 AND "command_digest" NOT GLOB '*[^0-9a-f]*'),
  "admission_act_ref" ANY NOT NULL CHECK (typeof("admission_act_ref")='text' AND length(CAST("admission_act_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_act_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_act_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_act_ref",1,instr("admission_act_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_act_digest" ANY NOT NULL CHECK (typeof("admission_act_digest")='text' AND length(CAST("admission_act_digest" AS BLOB))=64 AND "admission_act_digest" NOT GLOB '*[^0-9a-f]*'),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_digest" ANY NOT NULL CHECK (typeof("admission_fact_digest")='text' AND length(CAST("admission_fact_digest" AS BLOB))=64 AND "admission_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  "continuity_basis_ref" ANY NOT NULL CHECK (typeof("continuity_basis_ref")='text' AND length(CAST("continuity_basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("continuity_basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "continuity_basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("continuity_basis_ref",1,instr("continuity_basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "continuity_basis_digest" ANY NOT NULL CHECK (typeof("continuity_basis_digest")='text' AND length(CAST("continuity_basis_digest" AS BLOB))=64 AND "continuity_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "sole_active_basis_ref" ANY NOT NULL CHECK (typeof("sole_active_basis_ref")='text' AND length(CAST("sole_active_basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("sole_active_basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "sole_active_basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("sole_active_basis_ref",1,instr("sole_active_basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "sole_active_basis_digest" ANY NOT NULL CHECK (typeof("sole_active_basis_digest")='text' AND length(CAST("sole_active_basis_digest" AS BLOB))=64 AND "sole_active_basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "decision_ref" ANY NOT NULL CHECK (typeof("decision_ref")='text' AND length(CAST("decision_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("decision_ref",1,1) GLOB '[0-9A-Za-z]' AND "decision_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("decision_ref",1,instr("decision_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "decision_digest" ANY NOT NULL CHECK (typeof("decision_digest")='text' AND length(CAST("decision_digest" AS BLOB))=64 AND "decision_digest" NOT GLOB '*[^0-9a-f]*'),
  "version_ref" ANY NOT NULL CHECK (typeof("version_ref")='text' AND length(CAST("version_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("version_ref",1,1) GLOB '[0-9A-Za-z]' AND "version_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("version_ref",1,instr("version_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "version_digest" ANY NOT NULL CHECK (typeof("version_digest")='text' AND length(CAST("version_digest" AS BLOB))=64 AND "version_digest" NOT GLOB '*[^0-9a-f]*'),
  "historical_head_ref" ANY NOT NULL CHECK (typeof("historical_head_ref")='text' AND length(CAST("historical_head_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("historical_head_ref",1,1) GLOB '[0-9A-Za-z]' AND "historical_head_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("historical_head_ref",1,instr("historical_head_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "historical_head_revision" ANY NOT NULL CHECK (typeof("historical_head_revision")='integer' AND "historical_head_revision">=0),
  "historical_head_digest" ANY NOT NULL CHECK (typeof("historical_head_digest")='text' AND length(CAST("historical_head_digest" AS BLOB))=64 AND "historical_head_digest" NOT GLOB '*[^0-9a-f]*'),
  "historical_head_postimage" ANY NOT NULL CHECK (typeof("historical_head_postimage")='blob' AND length("historical_head_postimage") BETWEEN 1 AND 4096),
  "historical_work_head_ref" ANY CHECK ("historical_work_head_ref" IS NULL OR (typeof("historical_work_head_ref")='text' AND length(CAST("historical_work_head_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("historical_work_head_ref",1,1) GLOB '[0-9A-Za-z]' AND "historical_work_head_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("historical_work_head_ref",1,instr("historical_work_head_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))),
  "historical_work_head_revision" ANY CHECK ("historical_work_head_revision" IS NULL OR (typeof("historical_work_head_revision")='integer' AND "historical_work_head_revision">=1)),
  "historical_work_head_digest" ANY CHECK ("historical_work_head_digest" IS NULL OR (typeof("historical_work_head_digest")='text' AND length(CAST("historical_work_head_digest" AS BLOB))=64 AND "historical_work_head_digest" NOT GLOB '*[^0-9a-f]*')),
  "historical_work_head_postimage" ANY CHECK ("historical_work_head_postimage" IS NULL OR (typeof("historical_work_head_postimage")='blob' AND length("historical_work_head_postimage") BETWEEN 1 AND 4096)),
  "acceptance_fact_ref" ANY CHECK ("acceptance_fact_ref" IS NULL OR (typeof("acceptance_fact_ref")='text' AND length(CAST("acceptance_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("acceptance_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "acceptance_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("acceptance_fact_ref",1,instr("acceptance_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-'))),
  "acceptance_fact_digest" ANY CHECK ("acceptance_fact_digest" IS NULL OR (typeof("acceptance_fact_digest")='text' AND length(CAST("acceptance_fact_digest" AS BLOB))=64 AND "acceptance_fact_digest" NOT GLOB '*[^0-9a-f]*')),
  "generic_result_projection_digest" ANY NOT NULL CHECK (typeof("generic_result_projection_digest")='text' AND length(CAST("generic_result_projection_digest" AS BLOB))=64 AND "generic_result_projection_digest" NOT GLOB '*[^0-9a-f]*'),
  "family_route" ANY NOT NULL CHECK (typeof("family_route")='text' AND length(CAST("family_route" AS BLOB)) BETWEEN 1 AND 96 AND substr("family_route",1,1) GLOB '[0-9A-Za-z]' AND "family_route" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("family_route",1,instr("family_route",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "relation_digest" ANY NOT NULL CHECK (typeof("relation_digest")='text' AND length(CAST("relation_digest" AS BLOB))=64 AND "relation_digest" NOT GLOB '*[^0-9a-f]*'),
  "mutation_ref" ANY NOT NULL CHECK (typeof("mutation_ref")='text' AND length(CAST("mutation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("mutation_ref",1,1) GLOB '[0-9A-Za-z]' AND "mutation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("mutation_ref",1,instr("mutation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "program_ref" ANY NOT NULL CHECK (typeof("program_ref")='text' AND length(CAST("program_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("program_ref",1,1) GLOB '[0-9A-Za-z]' AND "program_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("program_ref",1,instr("program_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "basis_ref" ANY NOT NULL CHECK (typeof("basis_ref")='text' AND length(CAST("basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("basis_ref",1,instr("basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "basis_digest" ANY NOT NULL CHECK (typeof("basis_digest")='text' AND length(CAST("basis_digest" AS BLOB))=64 AND "basis_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (relation_ref),
  UNIQUE (mutation_ref),
  UNIQUE (decision_ref),
  UNIQUE (family_route),
  UNIQUE (relation_ref, relation_digest),
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (program_ref, version_ref) REFERENCES development_program_versions (program_ref, program_version_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (basis_ref, basis_digest) REFERENCES rw0_c2_decision_bases (basis_ref, basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (admission_fact_ref, admission_fact_digest) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref, admission_fact_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (program_ref, historical_work_head_ref) REFERENCES development_work_item_heads (program_ref, work_item_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  CONSTRAINT acceptance_pair CHECK ((acceptance_fact_ref IS NULL AND acceptance_fact_digest IS NULL) OR (acceptance_fact_ref IS NOT NULL AND acceptance_fact_digest IS NOT NULL)),
  CONSTRAINT replan_work_head_witness CHECK ((branch='attempt_selecting_replan' AND historical_work_head_ref IS NOT NULL AND historical_work_head_revision IS NOT NULL AND historical_work_head_digest IS NOT NULL AND historical_work_head_postimage IS NOT NULL) OR (branch<>'attempt_selecting_replan' AND historical_work_head_ref IS NULL AND historical_work_head_revision IS NULL AND historical_work_head_digest IS NULL AND historical_work_head_postimage IS NULL))
) STRICT;

CREATE TABLE rw0_c2_guarded_progression_results (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-guarded-progression-result.v2'),
  "guarded_result_ref" ANY NOT NULL CHECK (typeof("guarded_result_ref")='text' AND length(CAST("guarded_result_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("guarded_result_ref",1,1) GLOB '[0-9A-Za-z]' AND "guarded_result_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("guarded_result_ref",1,instr("guarded_result_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "branch" ANY NOT NULL CHECK (typeof("branch")='text' AND "branch" IN ('candidate_acceptance','candidate_repair','attempt_selecting_replan','program_terminal_reject','post_execution_program_block')),
  "generic_v1_result_schema_id" ANY NOT NULL CHECK (typeof("generic_v1_result_schema_id")='text' AND "generic_v1_result_schema_id"='governed-execution.nwp-record-development-progression-decision-result.v1'),
  "generic_v1_result_digest" ANY NOT NULL CHECK (typeof("generic_v1_result_digest")='text' AND length(CAST("generic_v1_result_digest" AS BLOB))=64 AND "generic_v1_result_digest" NOT GLOB '*[^0-9a-f]*'),
  "family_relation_ref" ANY NOT NULL CHECK (typeof("family_relation_ref")='text' AND length(CAST("family_relation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("family_relation_ref",1,1) GLOB '[0-9A-Za-z]' AND "family_relation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("family_relation_ref",1,instr("family_relation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "family_relation_digest" ANY NOT NULL CHECK (typeof("family_relation_digest")='text' AND length(CAST("family_relation_digest" AS BLOB))=64 AND "family_relation_digest" NOT GLOB '*[^0-9a-f]*'),
  "receipt_graph_profile_id" ANY NOT NULL CHECK (typeof("receipt_graph_profile_id")='text' AND "receipt_graph_profile_id"='governed-execution.nwp-rw0-c2-receipt-graph-profile.v2'),
  "guarded_result_digest" ANY NOT NULL CHECK (typeof("guarded_result_digest")='text' AND length(CAST("guarded_result_digest" AS BLOB))=64 AND "guarded_result_digest" NOT GLOB '*[^0-9a-f]*'),
  "mutation_ref" ANY NOT NULL CHECK (typeof("mutation_ref")='text' AND length(CAST("mutation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("mutation_ref",1,1) GLOB '[0-9A-Za-z]' AND "mutation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("mutation_ref",1,instr("mutation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "program_ref" ANY NOT NULL CHECK (typeof("program_ref")='text' AND length(CAST("program_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("program_ref",1,1) GLOB '[0-9A-Za-z]' AND "program_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("program_ref",1,instr("program_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "decision_ref" ANY NOT NULL CHECK (typeof("decision_ref")='text' AND length(CAST("decision_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("decision_ref",1,1) GLOB '[0-9A-Za-z]' AND "decision_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("decision_ref",1,instr("decision_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "version_ref" ANY NOT NULL CHECK (typeof("version_ref")='text' AND length(CAST("version_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("version_ref",1,1) GLOB '[0-9A-Za-z]' AND "version_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("version_ref",1,instr("version_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "decided_at" ANY NOT NULL CHECK (typeof("decided_at")='text' AND length("decided_at")=20 AND "decided_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"decided_at")="decided_at"),
  PRIMARY KEY (guarded_result_ref),
  UNIQUE (mutation_ref),
  UNIQUE (decision_ref),
  UNIQUE (guarded_result_ref, guarded_result_digest),
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (program_ref, version_ref) REFERENCES development_program_versions (program_ref, program_version_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (family_relation_ref, family_relation_digest) REFERENCES rw0_c2_guarded_family_relations (relation_ref, relation_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE rw0_c2_bootstrap_acceptance_facts (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-bootstrap-acceptance-fact.v1'),
  "acceptance_fact_ref" ANY NOT NULL CHECK (typeof("acceptance_fact_ref")='text' AND length(CAST("acceptance_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("acceptance_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "acceptance_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("acceptance_fact_ref",1,instr("acceptance_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "lineage_ref" ANY NOT NULL CHECK (typeof("lineage_ref")='text' AND length(CAST("lineage_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("lineage_ref",1,1) GLOB '[0-9A-Za-z]' AND "lineage_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("lineage_ref",1,instr("lineage_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof("scope_ref")='text' AND length(CAST("scope_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("scope_ref",1,1) GLOB '[0-9A-Za-z]' AND "scope_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("scope_ref",1,instr("scope_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_digest" ANY NOT NULL CHECK (typeof("admission_fact_digest")='text' AND length(CAST("admission_fact_digest" AS BLOB))=64 AND "admission_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  "mutation_ref" ANY NOT NULL CHECK (typeof("mutation_ref")='text' AND length(CAST("mutation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("mutation_ref",1,1) GLOB '[0-9A-Za-z]' AND "mutation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("mutation_ref",1,instr("mutation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "command_digest" ANY NOT NULL CHECK (typeof("command_digest")='text' AND length(CAST("command_digest" AS BLOB))=64 AND "command_digest" NOT GLOB '*[^0-9a-f]*'),
  "decision_ref" ANY NOT NULL CHECK (typeof("decision_ref")='text' AND length(CAST("decision_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("decision_ref",1,1) GLOB '[0-9A-Za-z]' AND "decision_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("decision_ref",1,instr("decision_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "decision_digest" ANY NOT NULL CHECK (typeof("decision_digest")='text' AND length(CAST("decision_digest" AS BLOB))=64 AND "decision_digest" NOT GLOB '*[^0-9a-f]*'),
  "version_ref" ANY NOT NULL CHECK (typeof("version_ref")='text' AND length(CAST("version_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("version_ref",1,1) GLOB '[0-9A-Za-z]' AND "version_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("version_ref",1,instr("version_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "version_digest" ANY NOT NULL CHECK (typeof("version_digest")='text' AND length(CAST("version_digest" AS BLOB))=64 AND "version_digest" NOT GLOB '*[^0-9a-f]*'),
  "historical_head_ref" ANY NOT NULL CHECK (typeof("historical_head_ref")='text' AND length(CAST("historical_head_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("historical_head_ref",1,1) GLOB '[0-9A-Za-z]' AND "historical_head_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("historical_head_ref",1,instr("historical_head_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "historical_head_revision" ANY NOT NULL CHECK (typeof("historical_head_revision")='integer' AND "historical_head_revision">=0),
  "historical_head_digest" ANY NOT NULL CHECK (typeof("historical_head_digest")='text' AND length(CAST("historical_head_digest" AS BLOB))=64 AND "historical_head_digest" NOT GLOB '*[^0-9a-f]*'),
  "selected_attempt_ref" ANY NOT NULL CHECK (typeof("selected_attempt_ref")='text' AND length(CAST("selected_attempt_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("selected_attempt_ref",1,1) GLOB '[0-9A-Za-z]' AND "selected_attempt_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("selected_attempt_ref",1,instr("selected_attempt_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "selected_candidate_ref" ANY NOT NULL CHECK (typeof("selected_candidate_ref")='text' AND length(CAST("selected_candidate_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("selected_candidate_ref",1,1) GLOB '[0-9A-Za-z]' AND "selected_candidate_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("selected_candidate_ref",1,instr("selected_candidate_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "basis_ref" ANY NOT NULL CHECK (typeof("basis_ref")='text' AND length(CAST("basis_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("basis_ref",1,1) GLOB '[0-9A-Za-z]' AND "basis_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("basis_ref",1,instr("basis_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "basis_digest" ANY NOT NULL CHECK (typeof("basis_digest")='text' AND length(CAST("basis_digest" AS BLOB))=64 AND "basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "family_route" ANY NOT NULL CHECK (typeof("family_route")='text' AND length(CAST("family_route" AS BLOB)) BETWEEN 1 AND 96 AND substr("family_route",1,1) GLOB '[0-9A-Za-z]' AND "family_route" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("family_route",1,instr("family_route",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "accepted_at" ANY NOT NULL CHECK (typeof("accepted_at")='text' AND length("accepted_at")=20 AND "accepted_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"accepted_at")="accepted_at"),
  "acceptance_fact_digest" ANY NOT NULL CHECK (typeof("acceptance_fact_digest")='text' AND length(CAST("acceptance_fact_digest" AS BLOB))=64 AND "acceptance_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  "program_ref" ANY NOT NULL CHECK (typeof("program_ref")='text' AND length(CAST("program_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("program_ref",1,1) GLOB '[0-9A-Za-z]' AND "program_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("program_ref",1,instr("program_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  PRIMARY KEY (acceptance_fact_ref),
  UNIQUE (admission_fact_ref),
  UNIQUE (lineage_ref),
  UNIQUE (scope_ref),
  UNIQUE (mutation_ref),
  UNIQUE (decision_ref),
  FOREIGN KEY (admission_fact_ref, admission_fact_digest) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref, admission_fact_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (program_ref, decision_ref) REFERENCES development_decisions (program_ref, decision_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (program_ref, version_ref) REFERENCES development_program_versions (program_ref, program_version_ref) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (basis_ref, basis_digest) REFERENCES rw0_c2_decision_bases (basis_ref, basis_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TRIGGER rw0_c2_historical_continuity_bases_no_update BEFORE UPDATE ON rw0_c2_historical_continuity_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_historical_continuity_bases'); END;

CREATE TRIGGER rw0_c2_historical_continuity_bases_no_delete BEFORE DELETE ON rw0_c2_historical_continuity_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_historical_continuity_bases'); END;

CREATE TRIGGER rw0_c2_historical_sole_active_bases_no_update BEFORE UPDATE ON rw0_c2_historical_sole_active_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_historical_sole_active_bases'); END;

CREATE TRIGGER rw0_c2_historical_sole_active_bases_no_delete BEFORE DELETE ON rw0_c2_historical_sole_active_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_historical_sole_active_bases'); END;

CREATE TRIGGER rw0_c2_decision_bases_no_update BEFORE UPDATE ON rw0_c2_decision_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_decision_bases'); END;

CREATE TRIGGER rw0_c2_decision_bases_no_delete BEFORE DELETE ON rw0_c2_decision_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_decision_bases'); END;

CREATE TRIGGER rw0_c2_guarded_family_relations_no_update BEFORE UPDATE ON rw0_c2_guarded_family_relations
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_guarded_family_relations'); END;

CREATE TRIGGER rw0_c2_guarded_family_relations_no_delete BEFORE DELETE ON rw0_c2_guarded_family_relations
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_guarded_family_relations'); END;

CREATE TRIGGER rw0_c2_guarded_progression_results_no_update BEFORE UPDATE ON rw0_c2_guarded_progression_results
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_guarded_progression_results'); END;

CREATE TRIGGER rw0_c2_guarded_progression_results_no_delete BEFORE DELETE ON rw0_c2_guarded_progression_results
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_guarded_progression_results'); END;

CREATE TRIGGER rw0_c2_bootstrap_acceptance_facts_no_update BEFORE UPDATE ON rw0_c2_bootstrap_acceptance_facts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_bootstrap_acceptance_facts'); END;

CREATE TRIGGER rw0_c2_bootstrap_acceptance_facts_no_delete BEFORE DELETE ON rw0_c2_bootstrap_acceptance_facts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_bootstrap_acceptance_facts'); END;
