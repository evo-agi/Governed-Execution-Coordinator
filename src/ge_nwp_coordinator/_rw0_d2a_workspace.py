"""Two isolated parent-owned reconstructions for D2 checking processes."""

from __future__ import annotations

import hashlib
import os
from pathlib import Path
import stat

from ._rw0_d1_workspace import D1CandidateCapture, D1Workspace, PATHS
from ._worker_execution_semantic_values import validate_capsule_manifest_relation

__all__: tuple[str, ...] = ()


class D2ReconstructionError(ValueError):
    """Content-free reconstruction refusal."""


def _fail() -> None:
    raise D2ReconstructionError("invalid_d2_reconstruction")


def read_exact_reconstruction(root: Path) -> tuple[tuple[str, bytes], ...]:
    """Read exactly the three regular no-alias files from one owned root."""
    if not isinstance(root, Path) or root.is_symlink():
        _fail()
    expected_dirs = {".docs", ".docs/system_overview"}
    found: set[str] = set()
    stack = [(root, "")]
    while stack:
        directory, prefix = stack.pop()
        try:
            entries = tuple(os.scandir(directory))
        except OSError:
            _fail()
        for entry in entries:
            relative = prefix + entry.name
            try:
                info = entry.stat(follow_symlinks=False)
            except OSError:
                _fail()
            if stat.S_ISDIR(info.st_mode) and relative in expected_dirs:
                stack.append((Path(entry.path), relative + "/"))
            elif (stat.S_ISREG(info.st_mode) and relative in PATHS
                  and info.st_nlink == 1 and stat.S_IMODE(info.st_mode) == 0o644
                  and info.st_size <= 1_048_576):
                found.add(relative)
            else:
                _fail()
    if found != set(PATHS):
        _fail()
    result: list[tuple[str, bytes]] = []
    for name in PATHS:
        parts = name.split("/")
        try:
            directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
            try:
                for part in parts[:-1]:
                    following = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                        dir_fd=directory)
                    os.close(directory)
                    directory = following
                descriptor = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW,
                                     dir_fd=directory)
                try:
                    info = os.fstat(descriptor)
                    if (not stat.S_ISREG(info.st_mode) or info.st_nlink != 1
                            or stat.S_IMODE(info.st_mode) != 0o644
                            or info.st_size > 1_048_576):
                        _fail()
                    chunks = bytearray()
                    while len(chunks) <= 1_048_576:
                        chunk = os.read(descriptor, min(65536, 1_048_577 - len(chunks)))
                        if not chunk:
                            break
                        chunks.extend(chunk)
                    if len(chunks) != info.st_size:
                        _fail()
                    result.append((name, bytes(chunks)))
                finally:
                    os.close(descriptor)
            finally:
                os.close(directory)
        except (OSError, ValueError):
            _fail()
    return tuple(result)


class D2Reconstruction:
    """One disposable reconstructed candidate; no durable state custody."""

    __slots__ = ("_workspace", "_expected", "_closed")

    def __init__(self, *, capture: D1CandidateCapture, capsule_manifest: object,
                 author_command: object) -> None:
        if type(capture) is not D1CandidateCapture:
            _fail()
        capture.validate()
        before, after, _modes = capture.blobs()
        try:
            validate_capsule_manifest_relation(
                capsule_manifest=capsule_manifest,
                author_command=author_command.worker_command,
                attempt_fence=author_command.attempt_fence,
                author_effect_fence=author_command.effect_fence,
                before_blobs=before, after_blobs=after,
            )
        except Exception:
            _fail()
        self._expected = tuple((name, after[name]) for name in PATHS)
        self._workspace = D1Workspace(after)
        self._closed = False
        try:
            self.verify()
        except BaseException:
            self.close()
            raise

    @property
    def root(self) -> Path:
        if self._closed:
            _fail()
        return self._workspace.root

    @property
    def digests(self) -> tuple[str, ...]:
        return tuple(hashlib.sha256(blob).hexdigest() for _name, blob in self._expected)

    def verify(self) -> None:
        if self._closed or read_exact_reconstruction(self.root) != self._expected:
            _fail()

    def close(self) -> None:
        if self._closed:
            return
        self._workspace.close()
        self._closed = True

    def __enter__(self) -> D2Reconstruction:
        if self._closed:
            _fail()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
