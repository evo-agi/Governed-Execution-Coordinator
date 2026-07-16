import json

import pytest

from ge_nwp_coordinator.canonicalization import canonical_sha256
from ge_nwp_coordinator.state_machine import TransitionCommand, WorkItemState
from ge_nwp_coordinator.state_store import SafeWriterMetadata


def _command(**kwargs: object) -> TransitionCommand:
    fields = {
        "work_item_id": "wi-1",
        "idempotency_key": "transition-k1",
        "expected_version": 0,
        "target_state": WorkItemState.LEASE_ADMITTED,
        "lease_identity_decision_ref": "lease-identity-lease-1",
        "authorization_decision_ref": "authz-lease-1",
        "global_stop_ref": "global-stop-clear",
        "global_stop_version": 0,
        "dependency_decision_ref": None,
        "evidence_refs": (),
        "safe_failure_class": None,
        "budget_cost": 0,
    }
    fields.update(kwargs)
    return TransitionCommand.create(**fields)


def _external_payload(command: TransitionCommand) -> dict[str, object]:
    payload = command.canonical_identity_payload()
    payload["evidence_refs"] = list(command.evidence_refs)
    payload["canonical_command_digest"] = command.canonical_command_digest
    return payload


def test_transition_command_round_trips_closed_payload() -> None:
    command = _command(evidence_refs=("safe-evidence",), budget_cost=1)
    payload = _external_payload(command)
    assert TransitionCommand.from_dict(payload) == command
    assert TransitionCommand.from_json(json.dumps(payload)) == command


def test_transition_command_rejects_unknown_and_duplicate_fields() -> None:
    command = _command()
    payload = _external_payload(command)
    payload["private_brief"] = "not-allowed"
    with pytest.raises(ValueError, match="unknown_field:transition_command.private_brief"):
        TransitionCommand.from_dict(payload)

    with pytest.raises(ValueError, match="duplicate_field:schema_id"):
        TransitionCommand.from_json('{"schema_id":"a","schema_id":"b"}')


@pytest.mark.parametrize(
    ("field_name", "value"),
    (
        ("expected_version", True),
        ("global_stop_version", True),
        ("budget_cost", True),
        ("evidence_refs", ("https://example.invalid/evidence",)),
        ("idempotency_key", "private-brief-ref"),
    ),
)
def test_transition_command_rejects_bool_as_int_and_unsafe_refs(field_name: str, value: object) -> None:
    with pytest.raises(ValueError):
        _command(**{field_name: value})


def test_transition_command_rejects_string_to_character_tuple_digest_exploit() -> None:
    raw_string = "safe"
    command = _command(evidence_refs=("placeholder",))
    payload = _external_payload(command)
    payload["evidence_refs"] = raw_string
    old_coerced_identity = dict(payload)
    old_coerced_identity.pop("canonical_command_digest")
    old_coerced_identity["evidence_refs"] = tuple(raw_string)
    payload["canonical_command_digest"] = canonical_sha256(old_coerced_identity)

    with pytest.raises(ValueError) as exc_info:
        TransitionCommand.from_dict(payload)
    assert "invalid_field_type:transition_command.evidence_refs" in str(exc_info.value)
    assert raw_string not in str(exc_info.value)
    assert payload["canonical_command_digest"] not in str(exc_info.value)


@pytest.mark.parametrize(
    "raw_evidence_refs",
    (
        "",
        "safe-evidence",
        b"safe-evidence",
        bytearray(b"safe-evidence"),
        {"0": "safe-evidence"},
        1,
        True,
        None,
        ("safe-evidence",),
        [["safe-evidence"]],
        [1],
        [True],
        ["https://example.invalid/evidence"],
        ["private-brief-ref"],
        ["safe-evidence", "safe-evidence"],
    ),
)
def test_transition_command_external_evidence_refs_rejects_malformed_collections(
    raw_evidence_refs: object,
) -> None:
    command = _command(evidence_refs=("safe-evidence",))
    payload = _external_payload(command)
    payload["evidence_refs"] = raw_evidence_refs
    payload_without_digest = dict(payload)
    payload_without_digest.pop("canonical_command_digest")
    try:
        payload["canonical_command_digest"] = canonical_sha256(payload_without_digest)
    except Exception:
        payload["canonical_command_digest"] = "a" * 64

    with pytest.raises(ValueError) as exc_info:
        TransitionCommand.from_dict(payload)
    if isinstance(raw_evidence_refs, str) and raw_evidence_refs:
        assert raw_evidence_refs not in str(exc_info.value)


def test_transition_command_external_evidence_refs_valid_list_succeeds() -> None:
    command = _command(evidence_refs=("safe-evidence",))
    payload = _external_payload(command)
    assert isinstance(payload["evidence_refs"], list)
    assert TransitionCommand.from_dict(payload) == command


def test_transition_command_direct_constructor_requires_tuple_storage() -> None:
    command = _command(evidence_refs=("safe-evidence",))
    direct = TransitionCommand(
        work_item_id=command.work_item_id,
        idempotency_key=command.idempotency_key,
        expected_version=command.expected_version,
        target_state=command.target_state,
        lease_identity_decision_ref=command.lease_identity_decision_ref,
        authorization_decision_ref=command.authorization_decision_ref,
        global_stop_ref=command.global_stop_ref,
        global_stop_version=command.global_stop_version,
        dependency_decision_ref=command.dependency_decision_ref,
        evidence_refs=command.evidence_refs,
        safe_failure_class=command.safe_failure_class,
        budget_cost=command.budget_cost,
        canonical_command_digest=command.canonical_command_digest,
    )
    assert direct == command

    with pytest.raises(ValueError, match="invalid_field_type:transition_command.evidence_refs"):
        TransitionCommand(
            work_item_id=command.work_item_id,
            idempotency_key=command.idempotency_key,
            expected_version=command.expected_version,
            target_state=command.target_state,
            lease_identity_decision_ref=command.lease_identity_decision_ref,
            authorization_decision_ref=command.authorization_decision_ref,
            global_stop_ref=command.global_stop_ref,
            global_stop_version=command.global_stop_version,
            dependency_decision_ref=command.dependency_decision_ref,
            evidence_refs=list(command.evidence_refs),  # type: ignore[arg-type]
            safe_failure_class=command.safe_failure_class,
            budget_cost=command.budget_cost,
            canonical_command_digest=command.canonical_command_digest,
        )


def test_transition_command_digest_covers_semantic_fields_and_excludes_itself() -> None:
    base = _command()
    variants = (
        _command(work_item_id="wi-2"),
        _command(idempotency_key="transition-k2"),
        _command(expected_version=1),
        _command(target_state=WorkItemState.BLOCKED, safe_failure_class="operator_action_required"),
        _command(lease_identity_decision_ref="lease-identity-other"),
        _command(authorization_decision_ref="authz-other"),
        _command(global_stop_ref="stop-1", global_stop_version=1),
        _command(dependency_decision_ref="deps-ready"),
        _command(evidence_refs=("safe-evidence",)),
        _command(safe_failure_class="validation_failed"),
        _command(budget_cost=1),
    )
    for variant in variants:
        assert variant.canonical_command_digest != base.canonical_command_digest

    payload = base.canonical_identity_payload()
    assert "canonical_command_digest" not in payload
    assert base.compute_digest() == base.canonical_command_digest


def test_safe_writer_metadata_is_not_part_of_transition_command_identity() -> None:
    command = _command()
    writer = SafeWriterMetadata(
        writer_ref="writer-main",
        generation=1,
        issued_ref="writer-issued-1",
        acquired_at="2026-07-16T00:00:00Z",
    )
    other_writer = SafeWriterMetadata(
        writer_ref="writer-other",
        generation=2,
        issued_ref="writer-issued-2",
        acquired_at="2026-07-16T00:00:00Z",
    )
    payload = command.canonical_identity_payload()
    assert writer.writer_ref not in payload.values()
    assert other_writer.writer_ref not in payload.values()
    assert command.compute_digest() == command.canonical_command_digest
