from __future__ import annotations

import ast
import copy
import hashlib
from pathlib import Path
import pickle
import traceback

import pytest

import ge_nwp_coordinator
from ge_nwp_coordinator import _development_decision_row_values as decision
from ge_nwp_coordinator import _development_effect_row_values as effect
from ge_nwp_coordinator import _development_program_row_values as program
from ge_nwp_coordinator import _development_row_value_support as support
from ge_nwp_coordinator.sqlite_errors import SQLiteMutationStoreError


ROOT=Path(__file__).resolve().parents[1]
MODULE_NAMES=(
    "_development_row_value_support.py",
    "_development_program_row_values.py",
    "_development_effect_row_values.py",
    "_development_decision_row_values.py",
)
MODULE_PATHS=tuple(ROOT/"src/ge_nwp_coordinator"/name for name in MODULE_NAMES)

ROW_VALUE_CLASS_NAMES=(
    "DevelopmentProgramHeadRowValue",
    "DevelopmentProgramVersionRowValue",
    "DevelopmentAcceptedIntentRevisionRowValue",
    "DevelopmentWorkItemHeadRowValue",
    "DevelopmentWorkItemRevisionRowValue",
    "DevelopmentProgramVersionWorkItemRowValue",
    "DevelopmentRevisionEdgeRowValue",
    "DevelopmentWorkSpecBindingRowValue",
    "DevelopmentSemanticAttemptRowValue",
    "DevelopmentAttemptFenceRowValue",
    "DevelopmentAuthorityEvaluationRowValue",
    "DevelopmentEffectIntentRowValue",
    "DevelopmentEffectFenceRowValue",
    "DevelopmentAuthorCommandRowValue",
    "DevelopmentEffectHeadRowValue",
    "DevelopmentDeliveryAttemptRowValue",
    "DevelopmentDeliveryHeadRowValue",
    "DevelopmentDecisionRowValue",
    "DevelopmentMutationReceiptRowValue",
)
ROW_TUPLE_FACTORY_NAMES=(
    "development_program_head_row_value_from_row_tuple",
    "development_program_version_row_value_from_row_tuple",
    "development_accepted_intent_revision_row_value_from_row_tuple",
    "development_work_item_head_row_value_from_row_tuple",
    "development_work_item_revision_row_value_from_row_tuple",
    "development_program_version_work_item_row_value_from_row_tuple",
    "development_revision_edge_row_value_from_row_tuple",
    "development_work_spec_binding_row_value_from_row_tuple",
    "development_semantic_attempt_row_value_from_row_tuple",
    "development_attempt_fence_row_value_from_row_tuple",
    "development_authority_evaluation_row_value_from_row_tuple",
    "development_effect_intent_row_value_from_row_tuple",
    "development_effect_fence_row_value_from_row_tuple",
    "development_author_command_row_value_from_row_tuple",
    "development_effect_head_row_value_from_row_tuple",
    "development_delivery_attempt_row_value_from_row_tuple",
    "development_delivery_head_row_value_from_row_tuple",
    "development_decision_row_value_from_row_tuple",
    "development_mutation_receipt_row_value_from_row_tuple",
)
OUTER_IDENTITY_TIMESTAMPS=(
    "program-head updated_at",
    "program-version created_at",
    "accepted-intent created_at",
    "work-revision created_at",
    "membership created_at",
    "revision-edge created_at",
    "semantic-attempt created_at",
    "effect-intent created_at",
    "work-head updated_at",
    "effect-head updated_at",
    "delivery-head updated_at",
    "WorkSpec binding recorded_at",
    "delivery-wrapper recorded_at",
    "decision decided_at",
    "receipt committed_at",
    "authority evaluated_at",
)
EMBEDDED_C2A_IDENTITY_TIMESTAMPS=(
    "attempt-fence expires_at",
    "effect-fence expires_at",
)
CONDITIONAL_OUTER_IDENTITY_TIMESTAMPS=(
    "authority-evaluation expires_at: verified-or-expired only",
)
OUTSIDE_EVERY_DIGEST_TIMESTAMPS=(
    "attempt-fence recorded_at",
    "effect-fence recorded_at",
    "author-command recorded_at",
)


def _digest(domain:str,identity:dict[str,object])->str:
    import json
    canonical=json.dumps(identity,ensure_ascii=False,allow_nan=False,sort_keys=True,separators=(",",":")).encode("utf-8",errors="strict")
    return hashlib.sha256(domain.encode("utf-8")+b"\0"+canonical).hexdigest()


def _program_head_row()->tuple[object,...]:
    identity={"schema_id":"governed-execution.nwp-development-program-head.v1","program_ref":"program-1","current_program_version_ref":"version-1","current_program_version_number":1,"head_revision":0,"program_state":"active","updated_at":"2026-08-15T12:34:56Z"}
    return tuple(identity.values())+(_digest("governed-execution.nwp-development-program-head.v1.identity",identity),)


def test_exact_four_private_modules_are_public_empty_and_not_package_exports()->None:
    present=tuple(sorted(path.name for path in (ROOT/"src/ge_nwp_coordinator").glob("_development_*row_value*.py")))
    assert present==tuple(sorted(MODULE_NAMES))
    for module in (support,program,effect,decision):assert module.__all__==()
    for name in (
        "DevelopmentProgramHeadRowValue","DevelopmentAttemptFenceRowValue",
        "DevelopmentDecisionRowValue","DevelopmentMutationReceiptRowValue",
    ):
        assert not hasattr(ge_nwp_coordinator,name)


def test_import_dag_is_acyclic_and_has_no_peer_owner_edges()->None:
    imports:dict[str,set[str]]={}
    for path in MODULE_PATHS:
        tree=ast.parse(path.read_text(encoding="utf-8"))
        imported=set()
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):imported.update(alias.name for alias in node.names)
            elif isinstance(node,ast.ImportFrom) and node.module:imported.add(node.module)
        imports[path.name]=imported
    assert imports[MODULE_NAMES[0]]=={"__future__","datetime","hashlib","json","re","typing","sqlite_errors"}
    for owner in MODULE_NAMES[1:]:
        assert not any(peer.removesuffix(".py") in imports[owner] for peer in MODULE_NAMES[1:] if peer!=owner)
    assert not any("validate_effect_relation" in path.read_text(encoding="utf-8") for path in MODULE_PATHS)


def test_exact_nineteen_row_classes_and_table_specific_factories_are_literal()->None:
    modules=(program,effect,decision)
    actual_classes={
        name
        for module in modules
        for name,value in vars(module).items()
        if isinstance(value,type) and value.__module__==module.__name__ and name.startswith("Development") and name.endswith("RowValue")
    }
    actual_factories={
        name
        for module in modules
        for name,value in vars(module).items()
        if callable(value) and name.startswith("development_") and name.endswith("_row_value_from_row_tuple")
    }
    assert actual_classes==set(ROW_VALUE_CLASS_NAMES)
    assert actual_factories==set(ROW_TUPLE_FACTORY_NAMES)


def test_timestamp_matrix_is_closed_and_validated_without_a_clock()->None:
    assert len(OUTER_IDENTITY_TIMESTAMPS)==16
    assert EMBEDDED_C2A_IDENTITY_TIMESTAMPS==(
        "attempt-fence expires_at",
        "effect-fence expires_at",
    )
    assert CONDITIONAL_OUTER_IDENTITY_TIMESTAMPS==(
        "authority-evaluation expires_at: verified-or-expired only",
    )
    assert OUTSIDE_EVERY_DIGEST_TIMESTAMPS==(
        "attempt-fence recorded_at",
        "effect-fence recorded_at",
        "author-command recorded_at",
    )
    assert support._require_utc_timestamp("2000-02-29T23:59:59Z")=="2000-02-29T23:59:59Z"


def test_no_forbidden_io_runtime_or_dynamic_constructs_exist()->None:
    forbidden_import_roots={"sqlite3","os","pathlib","time","random","uuid","logging","subprocess","threading","multiprocessing","importlib"}
    forbidden_calls={"eval","exec","compile","open","__import__"}
    for path in MODULE_PATHS:
        tree=ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node,ast.Import):
                assert all(alias.name.split(".")[0] not in forbidden_import_roots for alias in node.names)
            if isinstance(node,ast.ImportFrom) and node.module:
                assert node.module.split(".")[0] not in forbidden_import_roots
            if isinstance(node,ast.Call) and isinstance(node.func,ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node,ast.ExceptHandler) and isinstance(node.type,ast.Name):
                assert node.type.id != "BaseException"
        source=path.read_text(encoding="utf-8")
        for token in ("SELECT ","cursor","connection","row_factory","table_name","decode_row(","row_value_for_schema(","registry[","dataclass","asdict","namedtuple"):
            assert token not in source


def test_no_callable_registry_or_hidden_existing_source_consumer_exists()->None:
    for module in (support,program,effect,decision):
        for name,value in vars(module).items():
            if name.startswith("__"):
                continue
            if type(value) in (dict,list,tuple):
                assert not any(callable(item) for item in value)
                if type(value) is dict:
                    assert not any(callable(item) for item in value.values())
    owner_names={name.removesuffix(".py") for name in MODULE_NAMES}
    expected_consumers={
        "_development_author_effect_establishment_contracts.py":owner_names,
        "_development_program_initialization_contracts.py":{
            "_development_decision_row_values",
            "_development_program_row_values",
            "_development_row_value_support",
        },
        "_sqlite_development_program_initialization.py":{
            "_development_decision_row_values",
            "_development_program_row_values",
            "_development_row_value_support",
        },
        "_sqlite_development_pre_execution_plan_disposition.py":{
            "_development_decision_row_values",
            "_development_effect_row_values",
            "_development_program_row_values",
        },
        "_sqlite_development_author_effect_establishment.py":owner_names,
        "_sqlite_development_reader_contracts.py":owner_names,
        "_sqlite_development_readers.py":owner_names,
    }
    observed_consumers={}
    for path in (ROOT/"src/ge_nwp_coordinator").glob("*.py"):
        if path in MODULE_PATHS:
            continue
        tree=ast.parse(path.read_text(encoding="utf-8"))
        imported={
            node.module.rsplit(".",1)[-1]
            for node in ast.walk(tree)
            if isinstance(node,ast.ImportFrom) and node.module is not None
        }
        imported.update(
            alias.name.rsplit(".",1)[-1]
            for node in ast.walk(tree)
            if isinstance(node,ast.Import)
            for alias in node.names
        )
        imported.update(
            alias.name.rsplit(".",1)[-1]
            for node in ast.walk(tree)
            if isinstance(node,ast.ImportFrom) and node.module is None
            for alias in node.names
        )
        selected=imported & owner_names
        if selected:
            observed_consumers[path.name]=selected
    assert observed_consumers==expected_consumers


class _TupleSubclass(tuple):
    pass


def test_tuple_decoder_rejects_nonexact_tuples_and_boolean_integers()->None:
    row=_program_head_row()
    assert program.development_program_head_row_value_from_row_tuple(row).head_revision==0
    for invalid in (list(row),_TupleSubclass(row),dict(enumerate(row)),row[:-1],row+(None,)):
        with pytest.raises(SQLiteMutationStoreError,match="^database_integrity_failure$"):
            program.development_program_head_row_value_from_row_tuple(invalid)
    bad=list(row);bad[4]=False
    with pytest.raises(SQLiteMutationStoreError):
        program.development_program_head_row_value_from_row_tuple(tuple(bad))


def test_manual_values_are_slotted_immutable_unhashable_content_free_and_unpicklable()->None:
    first=program.development_program_head_row_value_from_row_tuple(_program_head_row())
    second=program.development_program_head_row_value_from_row_tuple(_program_head_row())
    assert first==second
    assert repr(first)==str(first)=="<DevelopmentProgramHeadRowValue>"
    assert not hasattr(first,"__dict__")
    assert not hasattr(first,"__weakref__")
    assert copy.copy(first) is first
    assert copy.deepcopy(first) is first
    with pytest.raises(TypeError):hash(first)
    with pytest.raises(AttributeError):first.program_ref="changed"
    with pytest.raises(AttributeError):del first.program_ref
    with pytest.raises(TypeError):pickle.dumps(first)
    with pytest.raises(TypeError):program.DevelopmentProgramHeadRowValue()
    with pytest.raises(TypeError):type("ForbiddenSubclass",(program.DevelopmentProgramHeadRowValue,),{})


def test_every_manual_class_declares_slots_and_every_property_is_read_only()->None:
    for path in MODULE_PATHS:
        tree=ast.parse(path.read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node,ast.ClassDef):
                assert any(
                    isinstance(statement,(ast.Assign,ast.AnnAssign))
                    and (
                        isinstance(statement,ast.Assign)
                        and any(isinstance(target,ast.Name) and target.id=="__slots__" for target in statement.targets)
                        or isinstance(statement,ast.AnnAssign)
                        and isinstance(statement.target,ast.Name)
                        and statement.target.id=="__slots__"
                    )
                    for statement in node.body
                )
    for module in (program,effect,decision):
        for value in vars(module).values():
            if isinstance(value,type) and value.__module__==module.__name__:
                for descriptor in vars(value).values():
                    if isinstance(descriptor,property):
                        assert descriptor.fset is None
                        assert descriptor.fdel is None


def test_safe_integrity_error_is_detached_and_slice_owned_frames_drop_raw_row()->None:
    sentinel="PRIVATE_RAW_ROW_SENTINEL"
    try:
        program.development_program_head_row_value_from_row_tuple((sentinel,))
    except SQLiteMutationStoreError as error:
        assert error.error_class=="database_integrity_failure"
        assert error.args==("database_integrity_failure",)
        assert str(error)=="database_integrity_failure"
        assert repr(error)=="SQLiteMutationStoreError('database_integrity_failure')"
        assert error.internal_detail is None
        assert error.__cause__ is None
        assert error.__context__ is None
        assert getattr(error,"__notes__",None) is None
        rendered="".join(traceback.format_exception(error))
        assert sentinel not in rendered
        current=error.__traceback__
        while current is not None:
            if "/src/ge_nwp_coordinator/_development_" in current.tb_frame.f_code.co_filename:
                assert sentinel not in repr(current.tb_frame.f_locals)
            current=current.tb_next
    else:raise AssertionError("expected integrity error")


class _PrivateWorkSpecProbe:
    def __repr__(self)->str:
        return "PRIVATE_WORKSPEC_TRACEBACK_SENTINEL"


def test_work_spec_private_material_is_not_retained_by_error_or_slice_frames()->None:
    probe=_PrivateWorkSpecProbe()
    try:
        program.development_work_spec_safe_projection_from_work_spec(work_spec=probe)
    except SQLiteMutationStoreError as error:
        assert "PRIVATE_WORKSPEC_TRACEBACK_SENTINEL" not in repr(error)
        current=error.__traceback__
        while current is not None:
            if "/src/ge_nwp_coordinator/_development_" in current.tb_frame.f_code.co_filename:
                assert "PRIVATE_WORKSPEC_TRACEBACK_SENTINEL" not in repr(current.tb_frame.f_locals)
            current=current.tb_next
    else:raise AssertionError("expected integrity error")


def test_protected_schema_artifacts_retain_pinned_identities()->None:
    expected={
        "src/ge_nwp_coordinator/sqlite_migrations/0001_initial.sql":(17940,"1a3af0f4dc3a9df8fe0a745a68a98590e56dd6f9dc7aeeced3aa975839543148"),
        "src/ge_nwp_coordinator/sqlite_migrations/0002_development_program_and_effect_state.sql":(154434,"5859f49994b1467db71911fb60db4f1cfc562af7517dc6e4d81b5b29ca44d56c"),
        "schemas/sqlite/coordinator-state-v1.sql":(18053,"e51902dd7e151f32a82b32cef7bbe535489f1558ce78fed63e0207df828f9e73"),
    }
    for relative,(size,digest) in expected.items():
        payload=(ROOT/relative).read_bytes()
        assert len(payload)==size
        assert hashlib.sha256(payload).hexdigest()==digest


def test_work_spec_projection_source_reads_only_literal_safe_properties()->None:
    tree=ast.parse((ROOT/"src/ge_nwp_coordinator/_development_program_row_values.py").read_text(encoding="utf-8"))
    function=next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=="_attempt_work_spec_safe_projection")
    attributes={node.attr for node in ast.walk(function) if isinstance(node,ast.Attribute) and isinstance(node.value,ast.Name) and node.value.id=="source"}
    assert attributes=={"work_spec_ref","program_ref","program_version_ref","accepted_intent_revision_ref","work_item_ref","work_item_revision_ref","repository_ref","base_git_object_format","base_git_oid","authorized_paths","validation_requirement_ref","review_requirement_ref","privacy_classification","work_spec_digest"}
    assert not ({"objective","requirements","exclusions"}&attributes)
