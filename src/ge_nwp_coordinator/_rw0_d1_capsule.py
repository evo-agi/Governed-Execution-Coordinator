"""Parent manifest construction and separately implemented D1 reconstruction."""

from __future__ import annotations

import hashlib

from ._rw0_d1_workspace import D1CandidateCapture, D1WorkspaceError, PATHS
from ._worker_execution_semantic_values import (
    AttemptFenceV1, CandidateCapsuleManifestV1, EffectFenceV1,
    WorkerCommandV1, validate_capsule_manifest_relation,
)


class D1CapsuleError(ValueError):
    """Content-free capsule mismatch."""


def build_candidate_capsule(
    capture: D1CandidateCapture, *, command: WorkerCommandV1,
    attempt_fence: AttemptFenceV1, effect_fence: EffectFenceV1,
    manifest_ref: str,
) -> CandidateCapsuleManifestV1:
    if type(capture) is not D1CandidateCapture:
        raise D1CapsuleError("capsule_mismatch")
    try:
        before, after, modes = capture.blobs()
    except D1WorkspaceError:
        raise D1CapsuleError("capsule_mismatch") from None
    return CandidateCapsuleManifestV1.create(
        before_blobs=before, after_blobs=after, modes=modes,
        author_command=command, attempt_fence=attempt_fence,
        author_effect_fence=effect_fence, capsule_manifest_ref=manifest_ref,
    )


def verify_candidate_capsule(
    manifest: CandidateCapsuleManifestV1, *,
    immutable_base: dict[str, bytes], capture: D1CandidateCapture,
    command: WorkerCommandV1, attempt_fence: AttemptFenceV1,
    effect_fence: EffectFenceV1,
) -> None:
    """Reconstruct from the original fixture, independently of the builder."""
    if (type(manifest) is not CandidateCapsuleManifestV1
            or type(immutable_base) is not dict
            or type(capture) is not D1CandidateCapture
            or type(command) is not WorkerCommandV1
            or type(attempt_fence) is not AttemptFenceV1
            or type(effect_fence) is not EffectFenceV1
            or set(immutable_base) != set(PATHS)
            or any(type(k) is not str or type(v) is not bytes
                   for k, v in immutable_base.items())):
        raise D1CapsuleError("capsule_mismatch")
    try:
        capture.validate()
    except D1WorkspaceError:
        raise D1CapsuleError("capsule_mismatch") from None
    entries = capture.entries
    if len(entries) != 3 or tuple(e.path for e in entries) != PATHS:
        raise D1CapsuleError("capsule_mismatch")
    if (tuple(e.path for e in manifest.entries) != PATHS
            or manifest.base_git_oid != command.base_git_oid
            or manifest.base_git_oid != attempt_fence.base_git_oid
            or manifest.base_git_oid != effect_fence.base_git_oid):
        raise D1CapsuleError("capsule_mismatch")
    reconstructed: dict[str, bytes] = {}
    changes: list[str] = []
    for item, recorded in zip(entries, manifest.entries, strict=True):
        if (type(item.before) is not bytes or type(item.after) is not bytes
                or item.mode != "100644" or recorded.mode != "100644"
                or item.before != immutable_base[item.path]
                or recorded.before_byte_length != len(immutable_base[item.path])
                or recorded.before_blob_sha256 != hashlib.sha256(immutable_base[item.path]).hexdigest()
                or recorded.after_byte_length != len(item.after)
                or recorded.after_blob_sha256 != hashlib.sha256(item.after).hexdigest()):
            raise D1CapsuleError("capsule_mismatch")
        reconstructed[item.path] = item.after
        if item.before != item.after:
            changes.append(item.path)
    if changes != [capture.changed_path]:
        raise D1CapsuleError("capsule_mismatch")
    reparsed = CandidateCapsuleManifestV1.from_mapping(manifest.to_mapping())
    if reparsed.to_mapping() != manifest.to_mapping():
        raise D1CapsuleError("capsule_mismatch")
    validate_capsule_manifest_relation(
        capsule_manifest=reparsed, author_command=command,
        attempt_fence=attempt_fence, author_effect_fence=effect_fence,
        before_blobs=dict(immutable_base), after_blobs=reconstructed,
    )
