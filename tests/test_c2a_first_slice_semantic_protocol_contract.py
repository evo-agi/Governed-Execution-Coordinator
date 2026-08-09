"""Direct document, schema, and canonical-vector oracle for C2A."""

from __future__ import annotations

import hashlib
import pytest
import re

from c2a_contract_support import (
    AUTHORIZED_PATHS,
    BOOTSTRAP_STOPS,
    CAPSULE_CANCELLATION_VECTOR_ROWS,
    CAPSULE_ENTRY_ROWS,
    CAPSULE_ROLE_ROWS,
    CEILING_FIELDS,
    CLAUSES,
    CROSS_RECORD_ROWS,
    DECISION_ROLE_ROWS,
    DOC,
    FIELD_ROWS,
    GIT_CEILINGS,
    GIT_PROHIBITION_ROWS,
    GIT_REQUIREMENT_ROWS,
    GOLDEN_BYTES,
    GOLDEN_META,
    IDENTITIES,
    MODEL_SECTIONS,
    NON_EQUIVALENCES,
    ONE_WRITER_ROWS,
    RELATION_VECTOR_ROWS,
    SCHEMA_ROWS,
    _BoundedMarkdown,
    _canonical,
    _canonical_mutation,
    _digest,
    _field_names,
    _full_record,
    _golden_from_document,
    _headings,
    _identity_bytes_are_valid,
    _identity_object,
    _normative_table_text,
    _ordered_items,
    _section,
    _strict_json,
    _table,
    _unordered_items,
    _without_fences,
)

EXPECTED_GOLDEN_META = {
    "WorkSpecV1": (
        "governed-execution.nwp-work-spec.v1",
        "governed-execution.nwp-work-spec.v1.identity",
        1158,
        "5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade",
        ("work_spec_digest",),
    ),
    "AttemptFenceV1": (
        "governed-execution.nwp-attempt-fence.v1",
        "governed-execution.nwp-attempt-fence.v1.identity",
        1525,
        "7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e",
        ("attempt_fence_digest",),
    ),
    "EffectFenceV1": (
        "governed-execution.nwp-effect-fence.v1",
        "governed-execution.nwp-effect-fence.v1.identity",
        1928,
        "71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3",
        ("effect_fence_digest",),
    ),
    "WorkerCommandV1": (
        "governed-execution.nwp-worker-command.v1",
        "governed-execution.nwp-worker-command.v1.identity",
        2444,
        "6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927",
        ("effect_fence_digest", "command_digest"),
    ),
    "DeliveryEnvelopeV1": (
        "governed-execution.nwp-delivery-envelope.v1",
        "governed-execution.nwp-delivery-envelope.v1.identity",
        755,
        "83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e",
        ("delivery_envelope_digest",),
    ),
    "WorkerObservationV1": (
        "governed-execution.nwp-worker-observation.v1",
        "governed-execution.nwp-worker-observation.v1.identity",
        1324,
        "b605b2779fa5b46ebff2d23d7026c643debde509c015e840608b0991f1c52a6f",
        ("observation_digest",),
    ),
    "CandidateCapsuleManifestV1": (
        "governed-execution.nwp-candidate-capsule-manifest.v1",
        "governed-execution.nwp-candidate-capsule-manifest.v1.identity",
        2178,
        "b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c",
        ("portable_capsule_digest",),
    ),
}


EXPECTED_GOLDEN_BYTES = {
    "WorkSpecV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","authorized_paths":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","exclusions":["Do not push, create a pull request, merge, or deploy.","Do not modify Execution Substrate runtime source."],"objective":"Document the bounded direct-local bootstrap proof while preserving Execution Substrate migration gates.","privacy_classification":"private_work_spec","program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","requirements":["Modify only the three authorized repository-relative paths.","Preserve Execution Substrate reliable-submit ownership and current P0.","Produce no runtime, schema, or service change."],"review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-work-spec.v1","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_ref":"work-spec.es-docs.0001"}',
    "AttemptFenceV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","aggregate_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":1,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"allowed_effect_classes":["author_candidate","cancel_effect","local_git_commit","review_candidate","validate_candidate"],"attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-attempt-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
    "EffectFenceV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","cancellation_target_effect_fence_digest":null,"cancellation_target_effect_fence_ref":null,"cancellation_target_effect_intent_ref":null,"candidate_ref":"candidate.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","expires_at":"2030-01-01T00:00:00Z","global_stop_ref":"global-stop.current","global_stop_version":7,"parent_standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","parent_standing_grant_ref":"standing-grant.0001","path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"portable_capsule_digest":null,"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-effect-fence.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
}


EXPECTED_GOLDEN_BYTES.update(
    {
        "WorkerCommandV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_authorization_digest":"2222222222222222222222222222222222222222222222222222222222222222","attempt_authorization_ref":"attempt-authorization.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","capsule_profile_ref":"capsule-profile.regular-replace-v1","capsule_schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","command_ref":"worker-command.0001","effect_authorization_digest":"3333333333333333333333333333333333333333333333333333333333333333","effect_authorization_ref":"effect-authorization.0001","effect_ceilings":{"max_active_invocations":1,"max_candidate_bytes":1048576,"max_changed_files":3,"max_cost_microusd":10000000,"max_cpu_seconds":3600,"max_deliveries":2,"max_deployments":0,"max_local_commits":0,"max_memory_bytes":4294967296,"max_merges":0,"max_model_input_tokens":200000,"max_model_output_tokens":50000,"max_pull_requests":0,"max_pushes":0,"max_wall_seconds":3600},"effect_class":"author_candidate","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","global_stop_ref":"global-stop.current","global_stop_version":7,"path_ceiling":[".docs/system_overview/hybrid_integration_architecture_adr.md","PLANS.md","docs_contract_test.go"],"privacy_classification":"private_source_change","program_ref":"program.es-docs","program_version_ref":"program-version.0001","redaction_profile_ref":"redaction.source-private-v1","repository_ref":"repository.execution-substrate","review_requirement_digest":"5555555555555555555555555555555555555555555555555555555555555555","review_requirement_ref":"review.es-docs.0001","schema_id":"governed-execution.nwp-worker-command.v1","semantic_attempt_ref":"semantic-attempt.0001","standing_grant_digest":"1111111111111111111111111111111111111111111111111111111111111111","standing_grant_ref":"standing-grant.0001","validation_requirement_digest":"4444444444444444444444444444444444444444444444444444444444444444","validation_requirement_ref":"validation.es-docs.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001","work_spec_digest":"5ae0add98fb3b6a233b778fe165dfa7ef8d1f3c43e824dddbdb6827958360ade","work_spec_ref":"work-spec.es-docs.0001"}',
        "DeliveryEnvelopeV1": b'{"adapter_kind":"direct_local_bootstrap","adapter_safe_correlation_ref":"adapter-correlation.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","program_ref":"program.es-docs","program_version_ref":"program-version.0001","schema_id":"governed-execution.nwp-delivery-envelope.v1","semantic_attempt_ref":"semantic-attempt.0001"}',
        "WorkerObservationV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","candidate_ref":"candidate.0001","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","delivery_attempt_ref":"delivery-attempt.0001","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","evidence_refs":["evidence.capsule-seal.0001"],"observation_kind":"capsule_sealed","observation_ref":"observation.capsule-sealed.0001","observed_at":"2026-08-08T18:00:00Z","outcome":"sealed","portable_capsule_digest":"b48948a9a0e65cde48edb96b66a2ce2e66eb8ee4abc286b93af0d22cf270d99c","program_ref":"program.es-docs","program_version_ref":"program-version.0001","reason_code":"reason.none","schema_id":"governed-execution.nwp-worker-observation.v1","semantic_attempt_ref":"semantic-attempt.0001","source_invocation_ref":"source-invocation.capsule-builder.0001","source_kind":"capsule_builder","source_ref":"capsule-builder.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
        "CandidateCapsuleManifestV1": b'{"accepted_intent_revision_ref":"intent-revision.0001","attempt_fence_digest":"7609313bb3b8514eac6dd71e1f2edc0ce6b6ee13aac9239eb1d3eb22383b4a4e","attempt_fence_ref":"attempt-fence.0001","authorized_path_scope_digest":"881d8190e95accffbce9d463a68910703595e5106ce81ba00a8433404b6c8116","base_git_object_format":"sha1","base_git_oid":"4f797fb63d3c5b95275b1455af36ebc9b695f773","candidate_ref":"candidate.0001","canonicalization_profile":"canonical-json.sorted-keys.utf8.v1","capsule_manifest_ref":"capsule-manifest.0001","command_digest":"6d4d2cd09e94e1f115d84968b5d03eb4b6c90aa0f1e345df4aeb8850a1982927","command_ref":"worker-command.0001","digest_domain":"governed-execution.nwp-candidate-capsule-manifest.v1.identity","effect_fence_digest":"71c4bbde627c3cb172c4cc8786643a70da23d2e2072211efe71694bac672fad3","effect_fence_ref":"effect-fence.0001","effect_intent_ref":"effect-intent.author.0001","entries":[{"after_blob_sha256":"7c1525eca0dfcccb6dcda32fe7f7f58281aa82be220018b1f69f4b529503ea8a","after_byte_length":52,"before_blob_sha256":"1ac70a99e7e54c57641ba8c0cb1e49ae7d0e6e5a7b1acaa0443e5afc1782f73a","before_byte_length":53,"mode":"100644","operation":"replace_regular_file","path":".docs/system_overview/hybrid_integration_architecture_adr.md"},{"after_blob_sha256":"3b80b40624b6a3834873b32839e8e7e73644def7437389a5eaea12abe480f180","after_byte_length":45,"before_blob_sha256":"d0cc82b8b8733e1b4ee2aba05aad19d474ed16e746bcac709b083d5ce2d848d9","before_byte_length":46,"mode":"100644","operation":"replace_regular_file","path":"PLANS.md"},{"after_blob_sha256":"267a3924b2a2ce1260c9d2532bf75db970eda7c76c40042d192e6cdece8202c2","after_byte_length":53,"before_blob_sha256":"47fc7108400e128ad4deade38d14c9c410b3f4dd23d3e022b008ac279d96ef90","before_byte_length":54,"mode":"100644","operation":"replace_regular_file","path":"docs_contract_test.go"}],"program_ref":"program.es-docs","program_version_ref":"program-version.0001","repository_ref":"repository.execution-substrate","schema_id":"governed-execution.nwp-candidate-capsule-manifest.v1","semantic_attempt_ref":"semantic-attempt.0001","work_item_ref":"work-item.es-docs.0001","work_item_revision_ref":"work-revision.0001"}',
    }
)


def test_clause_inventory_classification_and_timing_are_exact_and_bounded() -> None:
    headings = _headings(DOC)
    observed = tuple(
        (level, title)
        for level, title, _, _ in headings
        if title.startswith("C2A-PROTO-")
    )
    expected = tuple((2, f"{identifier} — {title}") for identifier, title, _, _ in CLAUSES)
    assert observed == expected
    for identifier, title, classification, timing in CLAUSES:
        clause = _without_fences(_section(DOC, f"{identifier} — {title}", 2))
        assert re.findall(r"^Classification: (.+)$", clause, re.MULTILINE) == [classification]
        assert re.findall(r"^Required before: (.+)$", clause, re.MULTILINE) == [timing]
        classification_at = clause.index("Classification:")
        timing_at = clause.index("Required before:")
        body_at = clause.find("\n\n", timing_at)
        assert classification_at < timing_at < body_at


@pytest.mark.parametrize("mutation", ("missing", "duplicate", "reordered", "mismatched", "unclosed"))
def test_clause_structure_mutations_fail_bounded_parser(mutation: str) -> None:
    first = f"## {CLAUSES[0][0]} — {CLAUSES[0][1]}"
    second = f"## {CLAUSES[1][0]} — {CLAUSES[1][1]}"
    mutated = DOC
    if mutation == "missing":
        mutated = mutated.replace(first, "", 1)
    elif mutation == "duplicate":
        mutated = mutated.replace(first, f"{first}\n{first}", 1)
    elif mutation == "reordered":
        mutated = mutated.replace(first, "## TEMP", 1).replace(second, first, 1).replace("## TEMP", second, 1)
    elif mutation == "mismatched":
        mutated = mutated.replace(first, first.replace("Status", "Statuses"), 1)
    else:
        mutated += "\n```json\n{}\n"
    if mutation == "unclosed":
        with pytest.raises(AssertionError):
            _headings(mutated)
    else:
        observed = tuple(
            title for level, title, _, _ in _headings(mutated) if level == 2 and title.startswith("C2A-PROTO-")
        )
        assert observed != tuple(f"{identifier} — {title}" for identifier, title, _, _ in CLAUSES)


def test_fenced_decoy_headings_are_ignored() -> None:
    decoy = "\n~~~text\n## C2A-PROTO-001 — decoy\n~~~\n"
    observed = tuple(
        title
        for level, title, _, _ in _headings(DOC + decoy)
        if level == 2 and title.startswith("C2A-PROTO-")
    )
    assert observed == tuple(f"{identifier} — {title}" for identifier, title, _, _ in CLAUSES)


@pytest.mark.parametrize(
    "mutation",
    ("fenced", "second_conflicting", "changed_header", "changed_separator", "moved", "duplicate_owner"),
)
def test_owner_local_normative_table_parser_rejects_audit_passthroughs(mutation: str) -> None:
    heading = "Observation current-effect relation matrix"
    table = _normative_table_text(DOC, heading)
    mutated = DOC
    if mutation == "fenced":
        mutated = mutated.replace(table, "```text\n" + table + "```\n", 1)
    elif mutation == "second_conflicting":
        changed = table.replace("`worker_started`", "`worker_started_conflict`", 1)
        mutated = mutated.replace(table, table + "\n" + changed, 1)
    elif mutation == "changed_header":
        mutated = mutated.replace("| Observation kind | Permitted current `EffectFenceV1.effect_class` |", "| Observation kind | Wrong effect header |", 1)
    elif mutation == "changed_separator":
        mutated = mutated.replace("| --- | --- |\n| `delivery_acknowledged`", "| :--- | --- |\n| `delivery_acknowledged`", 1)
    elif mutation == "moved":
        mutated = mutated.replace(table, "", 1) + "\n" + table
    else:
        owner = "### Observation current-effect relation matrix"
        mutated = mutated.replace(owner, owner + "\n" + owner, 1)
    with pytest.raises(AssertionError):
        _table(mutated, heading)


@pytest.mark.parametrize(
    "mutation",
    ("changed_excluded", "omitted_excluded", "duplicate_label", "conflicting_schema_label", "duplicate_inside", "duplicate_outside", "moved_outside", "changed_fence"),
)
def test_owner_local_golden_parser_rejects_audit_passthroughs(mutation: str) -> None:
    model = "DeliveryEnvelopeV1"
    title = f"Golden vector — {model}"
    parsed = _BoundedMarkdown(DOC)
    start, end, _ = parsed.span(title, 4)
    section = DOC[start:end]
    block = "```json\n" + GOLDEN_BYTES[model].decode("utf-8") + "\n```"
    excluded = "- Excluded full-record field: `delivery_envelope_digest=83e68b50759dc21746ef7b521edb8f7b61cf5446d819c8c7aa47bee048841f0e`"
    mutated = DOC
    if mutation == "changed_excluded":
        mutated = mutated.replace(excluded, excluded.replace("83e6", "03e6"), 1)
    elif mutation == "omitted_excluded":
        mutated = mutated.replace(excluded + "\n", "", 1)
    elif mutation == "duplicate_label":
        mutated = mutated.replace(excluded, excluded + "\n" + excluded, 1)
    elif mutation == "conflicting_schema_label":
        schema_label = "- Schema ID: `governed-execution.nwp-delivery-envelope.v1`"
        mutated = mutated.replace(schema_label, schema_label + "\n- Schema ID: `wrong-but-nonempty`", 1)
    elif mutation == "duplicate_inside":
        mutated = mutated[:end] + "\n" + block + "\n" + mutated[end:]
    elif mutation == "duplicate_outside":
        mutated += "\n" + block + "\n"
    elif mutation == "moved_outside":
        assert block in section
        mutated = mutated.replace(block, "", 1) + "\n" + block + "\n"
    else:
        mutated = mutated.replace(block, block.replace("```json", "~~~json").replace("\n```", "\n~~~"), 1)
    with pytest.raises(AssertionError):
        _golden_from_document(model, mutated)


@pytest.mark.parametrize("closing", ("~~~", "``"))
def test_bounded_markdown_rejects_unclosed_or_mismatched_fence(closing: str) -> None:
    with pytest.raises(AssertionError):
        _BoundedMarkdown("## Owner\n```json\n{}\n" + closing + "\n")


def test_schema_domain_identity_and_ceiling_inventories_are_exact() -> None:
    assert _table(DOC, "Semantic schema and digest-domain inventory") == SCHEMA_ROWS
    assert len({row[3] for row in SCHEMA_ROWS}) == 7

    identity_heading = f"{CLAUSES[1][0]} — {CLAUSES[1][1]}"
    identity_rows = _table(DOC, "Nominal identity inventory")
    assert tuple(row[1].strip("`") for row in identity_rows) == IDENTITIES
    assert _table(DOC, "One-writer, source, recorder, and custody matrix") == ONE_WRITER_ROWS
    identity_clause = _section(DOC, identity_heading, 2)
    assert _unordered_items(identity_clause) == NON_EQUIVALENCES

    ceiling_rows = _table(DOC, "CeilingsV1 object")
    assert tuple(row[1].strip("`") for row in ceiling_rows) == CEILING_FIELDS

    schema_clause = " ".join(_section(DOC, f"{CLAUSES[2][0]} — {CLAUSES[2][1]}", 2).split())
    for rule in (
        "`process_exit_code` is the sole signed v1 integer and is bounded from -255 through 255",
        "Safe references match `[A-Za-z0-9][A-Za-z0-9.-]*`, are 1 through 96 characters",
        "exact prefixes `connector-`, `tunnel-`, `workspace-`, `org-`, `organization-`, and `user-`",
        "A safe repository-relative path is 1 through 160 characters",
        "Safe evidence reference arrays contain 0 through 32 unique sorted safe refs.",
        "Private objective, requirement, and exclusion strings are each 1 through 512 Unicode code points",
        "Requirements and exclusions each contain 1 through 32 unique strings",
        "No string is trimmed, case-folded, or Unicode-normalized.",
    ):
        assert rule in schema_clause


def test_all_field_role_tables_and_capsule_entry_table_are_exact() -> None:
    assert tuple(FIELD_ROWS) == tuple(MODEL_SECTIONS.values())
    for section, expected in FIELD_ROWS.items():
        assert _table(DOC, section) == expected
        assert tuple(int(row[0]) for row in expected) == tuple(range(1, len(expected) + 1))
    assert _table(DOC, "CapsuleEntryV1 object") == CAPSULE_ENTRY_ROWS


def test_capsule_rules_git_ceiling_and_bootstrap_stop_order_are_exact() -> None:
    capsule = _section(DOC, f"{CLAUSES[7][0]} — {CLAUSES[7][1]}", 2)
    assert tuple(item.strip("`") for item in _ordered_items(capsule)) == AUTHORIZED_PATHS
    assert _table(DOC, "Capsule cross-record binding matrix") == CROSS_RECORD_ROWS
    assert _table(DOC, "Capsule custody-role matrix") == CAPSULE_ROLE_ROWS
    for phrase in (
        "operation `replace_regular_file`",
        "mode `100644` or `100755`",
        "replacement of regular files only",
        "add, delete, rename, symlink, submodule, directory entry, device, socket, FIFO, hardlink",
        "absolute path, traversal, empty segment, dot segment, URI-like path, backslash, NUL",
        "duplicate path, case-equivalent path, normalization-equivalent path, or a fourth ES path",
        "A capsule digest is not a path, credential, authority proof, acceptance decision, or Git identity.",
    ):
        assert phrase in " ".join(capsule.split())

    git = " ".join(_section(DOC, f"{CLAUSES[9][0]} — {CLAUSES[9][1]}", 2).split())
    assert "hard ceilings are exactly one local commit and zero pushes, pull requests, merges, and deployments" in git
    assert GIT_CEILINGS == {
        "max_local_commits": 1,
        "max_pushes": 0,
        "max_pull_requests": 0,
        "max_merges": 0,
        "max_deployments": 0,
    }

    assert _table(DOC, "Decision-role matrix") == DECISION_ROLE_ROWS
    assert _table(DOC, "Current-effect/originating-author relation vectors") == RELATION_VECTOR_ROWS
    assert _table(DOC, "Capsule-consuming cancellation relation vector") == CAPSULE_CANCELLATION_VECTOR_ROWS
    assert _table(DOC, "Git-effect prohibition matrix") == GIT_PROHIBITION_ROWS
    assert _table(DOC, "Git-effect mandatory bindings and reconciliation") == GIT_REQUIREMENT_ROWS

    bootstrap = _section(DOC, f"{CLAUSES[13][0]} — {CLAUSES[13][1]}", 2)
    assert _ordered_items(bootstrap) == BOOTSTRAP_STOPS


def test_normative_golden_vectors_are_independently_pinned() -> None:
    assert (
        tuple(EXPECTED_GOLDEN_META)
        == tuple(EXPECTED_GOLDEN_BYTES)
        == tuple(MODEL_SECTIONS)
    )
    for model, expected_bytes in EXPECTED_GOLDEN_BYTES.items():
        expected_meta = EXPECTED_GOLDEN_META[model]
        schema, domain, length, digest, _ = expected_meta
        assert GOLDEN_META[model] == expected_meta
        assert GOLDEN_BYTES[model] == expected_bytes
        assert _golden_from_document(model) == (schema, domain, length, digest, expected_bytes)
        assert len(expected_bytes) == length
        assert _canonical(_strict_json(expected_bytes)) == expected_bytes
        assert _digest(domain, expected_bytes) == digest
        assert _identity_bytes_are_valid(model, expected_bytes)
        full = _full_record(model)
        rows = FIELD_ROWS[MODEL_SECTIONS[model]]
        required = {row[1].strip("`") for row in rows if row[2] == "yes"}
        assert required <= set(full) <= set(_field_names(model))


def test_golden_vector_domains_are_not_raw_or_cross_schema_digests() -> None:
    domains = {
        model: meta[1] for model, meta in EXPECTED_GOLDEN_META.items()
    }
    assert len(set(domains.values())) == len(domains)
    for model, canonical in EXPECTED_GOLDEN_BYTES.items():
        expected = EXPECTED_GOLDEN_META[model][3]
        assert hashlib.sha256(canonical).hexdigest() != expected
        for other, domain in domains.items():
            assert (_digest(domain, canonical) == expected) is (other == model)


def test_closed_world_encoding_mutations_are_rejected() -> None:
    work = _identity_object("WorkSpecV1")
    duplicate = (
        b'{"schema_id":"governed-execution.nwp-work-spec.v1",'
        + EXPECTED_GOLDEN_BYTES["WorkSpecV1"][1:]
    )
    mutations = {
        "missing key": _canonical_mutation("WorkSpecV1", lambda value: value.pop("objective")),
        "unknown key": _canonical_mutation("WorkSpecV1", lambda value: value.update(extra="x")),
        "duplicate key": duplicate,
        "misspelled key": _canonical_mutation(
            "WorkSpecV1", lambda value: value.__setitem__("objectiv", value.pop("objective"))
        ),
        "wrong schema ID": _canonical_mutation(
            "WorkSpecV1", lambda value: value.__setitem__("schema_id", "governed-execution.nwp-work-spec.v2")
        ),
        "unversioned extension bag": _canonical_mutation(
            "WorkSpecV1", lambda value: value.update(metadata={"x": "y"})
        ),
        "bool where integer is required": _canonical_mutation(
            "AttemptFenceV1", lambda value: value.__setitem__("global_stop_version", True)
        ),
        "malformed list": _canonical_mutation(
            "WorkSpecV1", lambda value: value.__setitem__("authorized_paths", {"path": "PLANS.md"})
        ),
        "malformed object": _canonical_mutation(
            "AttemptFenceV1", lambda value: value.__setitem__("aggregate_ceilings", [])
        ),
        "canonical-byte mismatch": b"{ "
        + EXPECTED_GOLDEN_BYTES["WorkSpecV1"][1:],
        "digest mismatch": _canonical_mutation(
            "WorkSpecV1", lambda value: value.__setitem__("objective", "Different objective")
        ),
    }
    assert len(mutations) == 11
    for name, raw in mutations.items():
        model = "AttemptFenceV1" if name in {"bool where integer is required", "malformed object"} else "WorkSpecV1"
        assert not _identity_bytes_are_valid(model, raw), name


def test_c2a_proto_015_direct_pytest_oracle_retires_meta_oracle_authority() -> None:
    oracle = _section(DOC, "Direct pytest contract oracle", 3)
    normalized = " ".join(oracle.split())
    for rule in (
        "This C2A document is the semantic authority.",
        "independently authored expected schema and vector constants",
        "Core validators consume the actual caller-supplied related records",
        "Pytest parameter rows and deterministic fixtures are test inputs, not semantic authority.",
        "Direct pytest collection and assertion outcomes are execution evidence.",
        "An independent audit constructs and mutates semantic inputs directly",
        "Logical case IDs are not compatibility contracts.",
        "Pytest node IDs, node order, node count, node bytes, AST shape, and their hashes are not compatibility contracts.",
        "Operation, fixture, helper, binding, and trace registries are retired",
        "custom mutation dispatcher, global recorder, execution-token machinery",
        "canonical executed-ledger records",
        "seven frozen schema vectors and five frozen relation vectors remain the byte-semantic contract authorities",
        "No parser output, fixture, parameter row, collected node, assertion report, audit record, or other test artifact becomes durable program truth, runtime truth, semantic acceptance, or executable authority.",
    ):
        assert rule in normalized

    assert "### Executable logical-case ledger" not in DOC
    for retired_active_rule in (
        "separately hash-pinned closed-world authorities",
        "One test-only attestation epoch is global",
        "The canonical executed row contains only case ID",
        "Canonical execution requires 904 observed cases",
        "token issuances, token consumptions, and finalized cases",
    ):
        assert retired_active_rule not in DOC
