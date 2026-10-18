from __future__ import annotations

import os
import stat
from dataclasses import replace
from pathlib import Path

import pytest

from ge_nwp_coordinator._rw0_d1_capsule import (
    D1CapsuleError, build_candidate_capsule, verify_candidate_capsule,
)
from ge_nwp_coordinator._rw0_d1_offline import artificial_fixture, run_rw0_d1_offline
import ge_nwp_coordinator._rw0_d1_workspace as workspace_owner
from ge_nwp_coordinator._rw0_d1_workspace import (
    D1CandidateCapture, D1CapturedEntry, D1Workspace, D1WorkspaceError,
    MAX_FILE_BYTES, PATHS,
)
from test_rw0_d1_offline_integration import work_spec


def base() -> dict[str, bytes]:
    return artificial_fixture(work_spec()).base_blobs()


def test_materialize_capture_and_remove(tmp_path: Path) -> None:
    with D1Workspace(base()) as workspace:
        root = workspace.root
        assert tuple(sorted(p for p in base())) == tuple(sorted(PATHS))
        target = root / PATHS[2]
        target.write_bytes(target.read_bytes() + b"// candidate\n")
        capture = workspace.capture(selected_path=PATHS[2])
        assert capture.changed_path == PATHS[2]
        assert all(entry.mode == "100644" for entry in capture.entries)
        with pytest.raises(D1WorkspaceError):
            workspace.capture(selected_path=Path(PATHS[2]))
    assert not root.exists()


@pytest.mark.parametrize("change", ("extra", "missing", "symlink", "hardlink", "mode", "oversized"))
def test_unsafe_workspace_changes_fail_closed(change: str) -> None:
    with D1Workspace(base()) as workspace:
        target = workspace.root / PATHS[2]
        if change == "extra":
            (workspace.root / "extra.txt").write_bytes(b"x")
        elif change == "missing":
            target.unlink()
        elif change == "symlink":
            target.unlink()
            target.symlink_to("/tmp")
        elif change == "hardlink":
            (workspace.root / "extra.txt").hardlink_to(target)
        elif change == "mode":
            target.chmod(0o600)
        else:
            target.write_bytes(b"x" * (1024 * 1024 + 1))
        with pytest.raises(D1WorkspaceError):
            workspace.capture(selected_path=PATHS[2])


def test_outside_owned_hardlink_is_the_only_capture_defect(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch,
) -> None:
    work = work_spec()
    immutable_base = base()
    with run_rw0_d1_offline(work, artificial_fixture(work)) as run:
        handback = run.handback
        edited = next(entry.after for entry in handback.capture.entries
                      if entry.path == PATHS[2])
        owned_root = tmp_path / "owned_root"
        owned_root.mkdir()
        monkeypatch.setattr(workspace_owner.tempfile, "tempdir", str(owned_root))
        alias_dir = owned_root / "external_alias"
        alias_dir.mkdir()

        with D1Workspace(immutable_base) as workspace:
            root = workspace.root
            assert root.parent == owned_root
            assert root != alias_dir
            (root / PATHS[2]).write_bytes(edited)
            linked = root / PATHS[0]
            alias = alias_dir / "owned_alias"
            try:
                alias.hardlink_to(linked)
                # The consumer sees only the three authorized workspace paths,
                # normal modes and one real content edit. The alias is outside.
                entries = tuple(path for path in root.rglob("*") if path.is_file())
                assert {str(path.relative_to(root)) for path in entries} == set(PATHS)
                assert len(entries) == len(PATHS)
                assert all(stat.S_ISREG(path.lstat().st_mode)
                           and stat.S_IMODE(path.lstat().st_mode) == 0o644
                           and path.lstat().st_size <= MAX_FILE_BYTES
                           for path in entries)
                assert tuple(name for name in PATHS
                             if (root / name).read_bytes() != immutable_base[name]) == (PATHS[2],)
                linked_stat = linked.lstat()
                alias_stat = alias.lstat()
                assert linked_stat.st_nlink > 1
                assert (linked_stat.st_dev, linked_stat.st_ino) == (
                    alias_stat.st_dev, alias_stat.st_ino,
                )
                with pytest.raises(D1WorkspaceError, match="^unsafe_candidate$"):
                    workspace.capture(selected_path=PATHS[2])
            finally:
                alias.unlink(missing_ok=True)
                alias_dir.rmdir()
        assert not root.exists()

        with D1Workspace(immutable_base) as clean_workspace:
            (clean_workspace.root / PATHS[2]).write_bytes(edited)
            capture = clean_workspace.capture(selected_path=PATHS[2])
            assert capture.changed_path == PATHS[2]
            command = handback.author_command
            manifest = build_candidate_capsule(
                capture, command=command.worker_command,
                attempt_fence=command.attempt_fence,
                effect_fence=command.effect_fence,
                manifest_ref="capsule-manifest.d1",
            )
            verify_candidate_capsule(
                manifest, immutable_base=immutable_base, capture=capture,
                command=command.worker_command,
                attempt_fence=command.attempt_fence,
                effect_fence=command.effect_fence,
            )


def test_parent_manifest_is_independently_reconstructed() -> None:
    work = work_spec()
    fixture = artificial_fixture(work)
    with run_rw0_d1_offline(work, fixture) as run:
        h = run.handback
        command = h.author_command.worker_command
        attempt = h.author_command.attempt_fence
        effect = h.author_command.effect_fence
        verify_candidate_capsule(
            h.capsule_manifest, immutable_base=fixture.base_blobs(),
            capture=h.capture, command=command,
            attempt_fence=attempt, effect_fence=effect,
        )
        wrong = fixture.base_blobs()
        wrong[PATHS[2]] = b"different base"
        with pytest.raises(D1CapsuleError):
            verify_candidate_capsule(
                h.capsule_manifest, immutable_base=wrong,
                capture=h.capture, command=command,
                attempt_fence=attempt, effect_fence=effect,
            )


def test_capture_value_closes_every_entry_container_and_leaf() -> None:
    entries = tuple(D1CapturedEntry(path, "100644", b"base", b"changed" if i == 2
                                    else b"base") for i, path in enumerate(PATHS))
    valid = D1CandidateCapture(entries, PATHS[2])
    assert valid.blobs()[1][PATHS[2]] == b"changed"
    for invalid in (list(entries), tuple(reversed(entries)), entries[:2],
                    (entries[0], object(), entries[2])):
        with pytest.raises(D1WorkspaceError):
            D1CandidateCapture(invalid, PATHS[2])
        with pytest.raises(D1WorkspaceError):
            replace(valid, entries=invalid)
    for invalid in (Path(PATHS[2]), object(), b"docs_contract_test.go", PATHS[1]):
        with pytest.raises(D1WorkspaceError):
            replace(valid, changed_path=invalid)
    for field_name, bad_values in (
        ("path", (Path(PATHS[2]), object(), "not/allowed")),
        ("mode", (Path("100644"), object(), "100755")),
        ("before", (Path("base"), object(), bytearray(b"base"), b"x" * (MAX_FILE_BYTES + 1))),
        ("after", (Path("changed"), object(), memoryview(b"changed"),
                   b"x" * (MAX_FILE_BYTES + 1))),
    ):
        for invalid in bad_values:
            with pytest.raises(D1WorkspaceError):
                D1CapturedEntry(**{
                    "path": PATHS[2], "mode": "100644", "before": b"base",
                    "after": b"changed", field_name: invalid,
                })
            with pytest.raises(D1WorkspaceError):
                replace(entries[2], **{field_name: invalid})
    with pytest.raises(D1WorkspaceError):
        D1CandidateCapture(tuple(D1CapturedEntry(path, "100644", b"base", b"base")
                                 for path in PATHS), PATHS[2])
    with pytest.raises(D1WorkspaceError):
        replace(valid, entries=(entries[1], entries[0], entries[2]))


def test_forged_capture_is_rejected_at_both_capsule_boundaries() -> None:
    work = work_spec()
    fixture = artificial_fixture(work)
    with run_rw0_d1_offline(work, fixture) as run:
        handback = run.handback
        capture = handback.capture
        forged = object.__new__(D1CandidateCapture)
        object.__setattr__(forged, "entries", (capture.entries[0], run, capture.entries[2]))
        object.__setattr__(forged, "changed_path", PATHS[2])
        command = handback.author_command.worker_command
        attempt = handback.author_command.attempt_fence
        effect = handback.author_command.effect_fence
        with pytest.raises(D1CapsuleError, match="^capsule_mismatch$"):
            build_candidate_capsule(forged, command=command, attempt_fence=attempt,
                                    effect_fence=effect, manifest_ref="capsule-manifest.d1")
        with pytest.raises(D1CapsuleError, match="^capsule_mismatch$"):
            verify_candidate_capsule(
                handback.capsule_manifest, immutable_base=fixture.base_blobs(),
                capture=forged, command=command, attempt_fence=attempt,
                effect_fence=effect,
            )
        assert not run.closed
