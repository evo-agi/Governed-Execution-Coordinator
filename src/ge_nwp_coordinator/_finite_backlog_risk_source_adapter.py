"""Private pure one-way FiniteBacklog risk-source compatibility adapter.

The adapter consumes an explicitly supplied mapping value.  It does not import
the backlog runtime, issue a lease, equate backlog and development identities,
or own progression.
"""

import typing

from ._post_execution_policy_values import (
    PostExecutionRiskSourceBindingV1,
    PostExecutionRiskSourceProfileV1,
    _PostExecutionValue,
)

__all__ = ()

_FINITE_BACKLOG_RISK_SOURCE_PROFILE_REF = 'finite_backlog_risk_source.v1'
_FINITE_BACKLOG_RISK_SOURCE_PROFILE_DIGEST = '2ea8aa75234deb0901d3ca0a32d19877da072378e1acd438c901ce5cf1e489bc'

FiniteBacklogRiskSourceBindingV1 = typing.cast(
    type[_PostExecutionValue],
    _PostExecutionValue._define(
        'FiniteBacklogRiskSourceBindingV1', 'ge_nwp_coordinator._finite_backlog_risk_source_adapter',
        {'v_number': 'V19',
 'schema_id': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1',
 'ordered_fields': [{'constant': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1',
                     'name': 'schema_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'development_work_item_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'backlog_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'backlog_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'backlog_lease_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'backlog_work_item_id',
                     'nullable': False,
                     'type': 'exact_builtin_str'},
                    {'name': 'risk_lane', 'nullable': False, 'type': 'exact_builtin_str'},
                    {'name': 'mapping_author_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'mapping_author_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'mapping_evidence_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'mapping_evidence_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'},
                    {'name': 'binding_ref',
                     'nullable': False,
                     'rule': 'bounded_exact_string;closed_by_governing_profile_where_enumerated',
                     'type': 'exact_builtin_str'},
                    {'name': 'binding_digest',
                     'nullable': False,
                     'rule': '64_lowercase_hex',
                     'type': 'exact_builtin_str'}],
 'governing_profile_pair': {'profile_digest': '2ea8aa75234deb0901d3ca0a32d19877da072378e1acd438c901ce5cf1e489bc',
                            'profile_ref': 'finite_backlog_risk_source.v1'},
 'reference_posture': {'domain': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1.key',
                       'field': 'binding_ref',
                       'posture': 'generated',
                       'prefix': 'finite-backlog-risk-binding.',
                       'preimage_fields': ['development_work_item_ref',
                                           'backlog_ref',
                                           'backlog_digest',
                                           'backlog_lease_ref',
                                           'backlog_work_item_id',
                                           'risk_lane',
                                           'mapping_author_ref',
                                           'mapping_author_digest',
                                           'mapping_evidence_ref',
                                           'mapping_evidence_digest']},
 'digest_posture': {'domain': 'governed-execution.nwp-finite-backlog-risk-source-binding.v1.identity',
                    'field': 'binding_digest',
                    'self_exclusion': ['binding_digest']}},
        nested={},
        meta={},
    ),
)


def finite_backlog_risk_source_projection(
    value: object,
    *,
    evaluated_at: str,
    expires_at: str,
) -> tuple[PostExecutionRiskSourceProfileV1, PostExecutionRiskSourceBindingV1]:
    """Project a supplied V19 binding into the generic V43/V44 contract."""

    source = typing.cast(
        FiniteBacklogRiskSourceBindingV1,
        FiniteBacklogRiskSourceBindingV1.from_supplied(value),
    )
    profile_mapping: dict[str, object] = {
        "schema_id": "governed-execution.nwp-post-execution-risk-source-profile.v1",
        "source_profile_ref": "post-risk-source-profile.placeholder",
        "source_family": "versioned_external_risk_source",
        "source_system_schema_id": source.schema_id,
        "adapter_profile_ref": _FINITE_BACKLOG_RISK_SOURCE_PROFILE_REF,
        "adapter_profile_digest": _FINITE_BACKLOG_RISK_SOURCE_PROFILE_DIGEST,
        "profile_version": 1,
        "external_authority_claim": False,
        "source_profile_digest": "0" * 64,
    }
    profile_probe = PostExecutionRiskSourceProfileV1.__new__(PostExecutionRiskSourceProfileV1)
    for field in PostExecutionRiskSourceProfileV1._FIELDS:
        object.__setattr__(profile_probe, field, PostExecutionRiskSourceProfileV1._normalize_field(
            next(spec for spec in PostExecutionRiskSourceProfileV1._FIELD_SPECS if spec["name"] == field),
            profile_mapping[field],
        ))
    profile_mapping["source_profile_ref"] = profile_probe.computed_ref()
    object.__setattr__(profile_probe, "source_profile_ref", profile_mapping["source_profile_ref"])
    profile_mapping["source_profile_digest"] = profile_probe.computed_digest()
    profile = PostExecutionRiskSourceProfileV1.from_mapping(profile_mapping)
    binding_mapping: dict[str, object] = {
        "schema_id": "governed-execution.nwp-post-execution-risk-source-binding.v1",
        "source_binding_ref": "post-risk-source-binding.placeholder",
        "source_profile_schema_id": profile.schema_id,
        "source_profile_ref": profile.source_profile_ref,
        "source_profile_digest": profile.source_profile_digest,
        "development_work_item_ref": source.development_work_item_ref,
        "risk_lane": source.risk_lane,
        "source_value_schema_id": source.schema_id,
        "source_value_ref": source.binding_ref,
        "source_value_digest": source.binding_digest,
        "mapping_evidence_ref": source.mapping_evidence_ref,
        "mapping_evidence_digest": source.mapping_evidence_digest,
        "evaluated_at": evaluated_at,
        "expires_at": expires_at,
        "source_binding_digest": "0" * 64,
    }
    binding_probe = PostExecutionRiskSourceBindingV1.__new__(PostExecutionRiskSourceBindingV1)
    for field in PostExecutionRiskSourceBindingV1._FIELDS:
        object.__setattr__(binding_probe, field, PostExecutionRiskSourceBindingV1._normalize_field(
            next(spec for spec in PostExecutionRiskSourceBindingV1._FIELD_SPECS if spec["name"] == field),
            binding_mapping[field],
        ))
    binding_mapping["source_binding_ref"] = binding_probe.computed_ref()
    object.__setattr__(binding_probe, "source_binding_ref", binding_mapping["source_binding_ref"])
    binding_mapping["source_binding_digest"] = binding_probe.computed_digest()
    return profile, PostExecutionRiskSourceBindingV1.from_mapping(binding_mapping)
