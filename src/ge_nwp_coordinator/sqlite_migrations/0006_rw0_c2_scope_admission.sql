CREATE TABLE rw0_c2_verified_admission_acts (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-verified-admission-act.v1'),
  "act_ref" ANY NOT NULL CHECK (typeof("act_ref")='text' AND length(CAST("act_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("act_ref",1,1) GLOB '[0-9A-Za-z]' AND "act_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("act_ref",1,instr("act_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "act_digest" ANY NOT NULL CHECK (typeof("act_digest")='text' AND length(CAST("act_digest" AS BLOB))=64 AND "act_digest" NOT GLOB '*[^0-9a-f]*'),
  "lineage_ref" ANY NOT NULL CHECK (typeof("lineage_ref")='text' AND length(CAST("lineage_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("lineage_ref",1,1) GLOB '[0-9A-Za-z]' AND "lineage_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("lineage_ref",1,instr("lineage_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof("scope_ref")='text' AND length(CAST("scope_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("scope_ref",1,1) GLOB '[0-9A-Za-z]' AND "scope_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("scope_ref",1,instr("scope_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "guard_profile" ANY NOT NULL CHECK (typeof("guard_profile")='text' AND "guard_profile"='rw0-c2-guard-v1'),
  "applicability" ANY NOT NULL CHECK (typeof("applicability")='text' AND "applicability"='admitted_direct_local_bootstrap'),
  "provenance_ref" ANY NOT NULL CHECK (typeof("provenance_ref")='text' AND length(CAST("provenance_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("provenance_ref",1,1) GLOB '[0-9A-Za-z]' AND "provenance_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("provenance_ref",1,instr("provenance_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "provenance_digest" ANY NOT NULL CHECK (typeof("provenance_digest")='text' AND length(CAST("provenance_digest" AS BLOB))=64 AND "provenance_digest" NOT GLOB '*[^0-9a-f]*'),
  "projection_digest" ANY NOT NULL CHECK (typeof("projection_digest")='text' AND length(CAST("projection_digest" AS BLOB))=64 AND "projection_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (act_ref),
  UNIQUE (act_ref, act_digest)
) STRICT;

CREATE TABLE rw0_c2_scope_admission_facts (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-scope-admission-fact.v1'),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "act_ref" ANY NOT NULL CHECK (typeof("act_ref")='text' AND length(CAST("act_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("act_ref",1,1) GLOB '[0-9A-Za-z]' AND "act_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("act_ref",1,instr("act_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "act_digest" ANY NOT NULL CHECK (typeof("act_digest")='text' AND length(CAST("act_digest" AS BLOB))=64 AND "act_digest" NOT GLOB '*[^0-9a-f]*'),
  "lineage_ref" ANY NOT NULL CHECK (typeof("lineage_ref")='text' AND length(CAST("lineage_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("lineage_ref",1,1) GLOB '[0-9A-Za-z]' AND "lineage_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("lineage_ref",1,instr("lineage_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "scope_ref" ANY NOT NULL CHECK (typeof("scope_ref")='text' AND length(CAST("scope_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("scope_ref",1,1) GLOB '[0-9A-Za-z]' AND "scope_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("scope_ref",1,instr("scope_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "guard_profile" ANY NOT NULL CHECK (typeof("guard_profile")='text' AND "guard_profile"='rw0-c2-guard-v1'),
  "applicability" ANY NOT NULL CHECK (typeof("applicability")='text' AND "applicability"='admitted_direct_local_bootstrap'),
  "provenance_ref" ANY NOT NULL CHECK (typeof("provenance_ref")='text' AND length(CAST("provenance_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("provenance_ref",1,1) GLOB '[0-9A-Za-z]' AND "provenance_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("provenance_ref",1,instr("provenance_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "provenance_digest" ANY NOT NULL CHECK (typeof("provenance_digest")='text' AND length(CAST("provenance_digest" AS BLOB))=64 AND "provenance_digest" NOT GLOB '*[^0-9a-f]*'),
  "one_shot_ceiling" ANY NOT NULL CHECK (typeof("one_shot_ceiling")='integer' AND "one_shot_ceiling"=1),
  "admission_fact_digest" ANY NOT NULL CHECK (typeof("admission_fact_digest")='text' AND length(CAST("admission_fact_digest" AS BLOB))=64 AND "admission_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (admission_fact_ref),
  UNIQUE (admission_fact_ref, admission_fact_digest),
  UNIQUE (act_ref),
  UNIQUE (lineage_ref),
  UNIQUE (scope_ref),
  FOREIGN KEY (act_ref, act_digest) REFERENCES rw0_c2_verified_admission_acts (act_ref, act_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE rw0_c2_scope_admission_recording_bases (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-scope-admission-recording-basis.v1'),
  "operation_ref" ANY NOT NULL CHECK (typeof("operation_ref")='text' AND length(CAST("operation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("operation_ref",1,1) GLOB '[0-9A-Za-z]' AND "operation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("operation_ref",1,instr("operation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "command_digest" ANY NOT NULL CHECK (typeof("command_digest")='text' AND length(CAST("command_digest" AS BLOB))=64 AND "command_digest" NOT GLOB '*[^0-9a-f]*'),
  "act_projection_digest" ANY NOT NULL CHECK (typeof("act_projection_digest")='text' AND length(CAST("act_projection_digest" AS BLOB))=64 AND "act_projection_digest" NOT GLOB '*[^0-9a-f]*'),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_digest" ANY NOT NULL CHECK (typeof("admission_fact_digest")='text' AND length(CAST("admission_fact_digest" AS BLOB))=64 AND "admission_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  "enrollment_ref" ANY NOT NULL CHECK (typeof("enrollment_ref")='text' AND length(CAST("enrollment_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("enrollment_ref",1,1) GLOB '[0-9A-Za-z]' AND "enrollment_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("enrollment_ref",1,instr("enrollment_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "incarnation_ref" ANY NOT NULL CHECK (typeof("incarnation_ref")='text' AND length(CAST("incarnation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("incarnation_ref",1,1) GLOB '[0-9A-Za-z]' AND "incarnation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("incarnation_ref",1,instr("incarnation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "authority_process_ref" ANY NOT NULL CHECK (typeof("authority_process_ref")='text' AND length(CAST("authority_process_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("authority_process_ref",1,1) GLOB '[0-9A-Za-z]' AND "authority_process_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("authority_process_ref",1,instr("authority_process_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "storage_custody_ref" ANY NOT NULL CHECK (typeof("storage_custody_ref")='text' AND length(CAST("storage_custody_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("storage_custody_ref",1,1) GLOB '[0-9A-Za-z]' AND "storage_custody_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("storage_custody_ref",1,instr("storage_custody_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "enrollment_evidence_ref" ANY NOT NULL CHECK (typeof("enrollment_evidence_ref")='text' AND length(CAST("enrollment_evidence_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("enrollment_evidence_ref",1,1) GLOB '[0-9A-Za-z]' AND "enrollment_evidence_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("enrollment_evidence_ref",1,instr("enrollment_evidence_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "enrollment_evidence_digest" ANY NOT NULL CHECK (typeof("enrollment_evidence_digest")='text' AND length(CAST("enrollment_evidence_digest" AS BLOB))=64 AND "enrollment_evidence_digest" NOT GLOB '*[^0-9a-f]*'),
  "recording_permission_evidence_ref" ANY NOT NULL CHECK (typeof("recording_permission_evidence_ref")='text' AND length(CAST("recording_permission_evidence_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("recording_permission_evidence_ref",1,1) GLOB '[0-9A-Za-z]' AND "recording_permission_evidence_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("recording_permission_evidence_ref",1,instr("recording_permission_evidence_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "recording_permission_evidence_digest" ANY NOT NULL CHECK (typeof("recording_permission_evidence_digest")='text' AND length(CAST("recording_permission_evidence_digest" AS BLOB))=64 AND "recording_permission_evidence_digest" NOT GLOB '*[^0-9a-f]*'),
  "custody_evidence_ref" ANY NOT NULL CHECK (typeof("custody_evidence_ref")='text' AND length(CAST("custody_evidence_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("custody_evidence_ref",1,1) GLOB '[0-9A-Za-z]' AND "custody_evidence_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("custody_evidence_ref",1,instr("custody_evidence_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "custody_evidence_digest" ANY NOT NULL CHECK (typeof("custody_evidence_digest")='text' AND length(CAST("custody_evidence_digest" AS BLOB))=64 AND "custody_evidence_digest" NOT GLOB '*[^0-9a-f]*'),
  "recorded_at" ANY NOT NULL CHECK (typeof("recorded_at")='text' AND length("recorded_at")=20 AND "recorded_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"recorded_at")="recorded_at"),
  "basis_digest" ANY NOT NULL CHECK (typeof("basis_digest")='text' AND length(CAST("basis_digest" AS BLOB))=64 AND "basis_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (operation_ref),
  UNIQUE (operation_ref, command_digest, basis_digest, recorded_at),
  UNIQUE (admission_fact_ref),
  FOREIGN KEY (admission_fact_ref, admission_fact_digest) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref, admission_fact_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TABLE rw0_c2_scope_admission_recording_receipts (
  "schema_id" ANY NOT NULL CHECK (typeof("schema_id")='text' AND "schema_id"='governed-execution.nwp-rw0-c2-scope-admission-recording-receipt.v1'),
  "operation_ref" ANY NOT NULL CHECK (typeof("operation_ref")='text' AND length(CAST("operation_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("operation_ref",1,1) GLOB '[0-9A-Za-z]' AND "operation_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("operation_ref",1,instr("operation_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "command_digest" ANY NOT NULL CHECK (typeof("command_digest")='text' AND length(CAST("command_digest" AS BLOB))=64 AND "command_digest" NOT GLOB '*[^0-9a-f]*'),
  "act_ref" ANY NOT NULL CHECK (typeof("act_ref")='text' AND length(CAST("act_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("act_ref",1,1) GLOB '[0-9A-Za-z]' AND "act_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("act_ref",1,instr("act_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "act_digest" ANY NOT NULL CHECK (typeof("act_digest")='text' AND length(CAST("act_digest" AS BLOB))=64 AND "act_digest" NOT GLOB '*[^0-9a-f]*'),
  "act_projection_digest" ANY NOT NULL CHECK (typeof("act_projection_digest")='text' AND length(CAST("act_projection_digest" AS BLOB))=64 AND "act_projection_digest" NOT GLOB '*[^0-9a-f]*'),
  "admission_fact_ref" ANY NOT NULL CHECK (typeof("admission_fact_ref")='text' AND length(CAST("admission_fact_ref" AS BLOB)) BETWEEN 1 AND 96 AND substr("admission_fact_ref",1,1) GLOB '[0-9A-Za-z]' AND "admission_fact_ref" NOT GLOB '*[^0-9A-Za-z.-]*' AND lower(substr("admission_fact_ref",1,instr("admission_fact_ref",'-'))) NOT IN ('connector-','tunnel-','workspace-','org-','organization-','user-')),
  "admission_fact_digest" ANY NOT NULL CHECK (typeof("admission_fact_digest")='text' AND length(CAST("admission_fact_digest" AS BLOB))=64 AND "admission_fact_digest" NOT GLOB '*[^0-9a-f]*'),
  "basis_digest" ANY NOT NULL CHECK (typeof("basis_digest")='text' AND length(CAST("basis_digest" AS BLOB))=64 AND "basis_digest" NOT GLOB '*[^0-9a-f]*'),
  "result_digest" ANY NOT NULL CHECK (typeof("result_digest")='text' AND length(CAST("result_digest" AS BLOB))=64 AND "result_digest" NOT GLOB '*[^0-9a-f]*'),
  "recorded_at" ANY NOT NULL CHECK (typeof("recorded_at")='text' AND length("recorded_at")=20 AND "recorded_at" GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]T[0-9][0-9]:[0-9][0-9]:[0-9][0-9]Z' AND strftime('%Y-%m-%dT%H:%M:%SZ',"recorded_at")="recorded_at"),
  "outcome" ANY NOT NULL CHECK (typeof("outcome")='text' AND "outcome"='committed'),
  "receipt_digest" ANY NOT NULL CHECK (typeof("receipt_digest")='text' AND length(CAST("receipt_digest" AS BLOB))=64 AND "receipt_digest" NOT GLOB '*[^0-9a-f]*'),
  PRIMARY KEY (operation_ref),
  UNIQUE (admission_fact_ref),
  UNIQUE (act_ref),
  FOREIGN KEY (operation_ref, command_digest, basis_digest, recorded_at) REFERENCES rw0_c2_scope_admission_recording_bases (operation_ref, command_digest, basis_digest, recorded_at) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (admission_fact_ref, admission_fact_digest) REFERENCES rw0_c2_scope_admission_facts (admission_fact_ref, admission_fact_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE,
  FOREIGN KEY (act_ref, act_digest) REFERENCES rw0_c2_verified_admission_acts (act_ref, act_digest) ON UPDATE RESTRICT ON DELETE RESTRICT NOT DEFERRABLE INITIALLY IMMEDIATE
) STRICT;

CREATE TRIGGER rw0_c2_verified_admission_acts_no_update BEFORE UPDATE ON rw0_c2_verified_admission_acts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_verified_admission_acts'); END;

CREATE TRIGGER rw0_c2_verified_admission_acts_no_delete BEFORE DELETE ON rw0_c2_verified_admission_acts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_verified_admission_acts'); END;

CREATE TRIGGER rw0_c2_scope_admission_facts_no_update BEFORE UPDATE ON rw0_c2_scope_admission_facts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_scope_admission_facts'); END;

CREATE TRIGGER rw0_c2_scope_admission_facts_no_delete BEFORE DELETE ON rw0_c2_scope_admission_facts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_scope_admission_facts'); END;

CREATE TRIGGER rw0_c2_scope_admission_recording_bases_no_update BEFORE UPDATE ON rw0_c2_scope_admission_recording_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_scope_admission_recording_bases'); END;

CREATE TRIGGER rw0_c2_scope_admission_recording_bases_no_delete BEFORE DELETE ON rw0_c2_scope_admission_recording_bases
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_scope_admission_recording_bases'); END;

CREATE TRIGGER rw0_c2_scope_admission_recording_receipts_no_update BEFORE UPDATE ON rw0_c2_scope_admission_recording_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_scope_admission_recording_receipts'); END;

CREATE TRIGGER rw0_c2_scope_admission_recording_receipts_no_delete BEFORE DELETE ON rw0_c2_scope_admission_recording_receipts
BEGIN SELECT RAISE(ABORT,'immutable_rw0_c2_scope_admission_recording_receipts'); END;
