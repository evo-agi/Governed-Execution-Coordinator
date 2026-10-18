"""Parent-owned bounded artificial workspace and exact candidate capture."""

from __future__ import annotations

from dataclasses import dataclass, field
import os
from pathlib import Path, PurePosixPath
import shutil
import stat
import tempfile


PATHS = (
    ".docs/system_overview/hybrid_integration_architecture_adr.md",
    "PLANS.md",
    "docs_contract_test.go",
)
MAX_FILE_BYTES = 1024 * 1024


class D1WorkspaceError(ValueError):
    """Content-free unsafe or excessive workspace condition."""


def _fail(reason: str = "unsafe_candidate") -> None:
    raise D1WorkspaceError(reason)


def _check_path(name: str) -> tuple[str, ...]:
    if type(name) is not str or name not in PATHS:
        _fail()
    parts = PurePosixPath(name).parts
    if not parts or any(part in ("", ".", "..") for part in parts):
        _fail()
    return parts


@dataclass(frozen=True, slots=True, repr=False)
class D1CapturedEntry:
    path: str
    mode: str
    before: bytes = field(repr=False)
    after: bytes = field(repr=False)

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate even an exact entry whose constructor was bypassed."""
        if type(self) is not D1CapturedEntry:
            _fail()
        try:
            path = object.__getattribute__(self, "path")
            mode = object.__getattribute__(self, "mode")
            before = object.__getattribute__(self, "before")
            after = object.__getattribute__(self, "after")
        except AttributeError:
            _fail()
        if (type(path) is not str or path not in PATHS
                or type(mode) is not str or mode != "100644"
                or type(before) is not bytes or type(after) is not bytes):
            _fail()
        if len(before) > MAX_FILE_BYTES or len(after) > MAX_FILE_BYTES:
            _fail("excessive_candidate")


@dataclass(frozen=True, slots=True, repr=False)
class D1CandidateCapture:
    entries: tuple[D1CapturedEntry, ...] = field(repr=False)
    changed_path: str

    def __post_init__(self) -> None:
        self.validate()

    def validate(self) -> None:
        """Validate the complete immutable D1 capture graph without I/O."""
        if type(self) is not D1CandidateCapture:
            _fail()
        try:
            entries = object.__getattribute__(self, "entries")
            changed_path = object.__getattribute__(self, "changed_path")
        except AttributeError:
            _fail()
        if (type(entries) is not tuple or len(entries) != len(PATHS)
                or type(changed_path) is not str or changed_path not in PATHS):
            _fail()
        for entry in entries:
            if type(entry) is not D1CapturedEntry:
                _fail()
            entry.validate()
        if tuple(entry.path for entry in entries) != PATHS:
            _fail()
        if tuple(entry.path for entry in entries if entry.before != entry.after) != (
            changed_path,
        ):
            _fail()

    def blobs(self) -> tuple[dict[str, bytes], dict[str, bytes], dict[str, str]]:
        self.validate()
        return (
            {entry.path: entry.before for entry in self.entries},
            {entry.path: entry.after for entry in self.entries},
            {entry.path: entry.mode for entry in self.entries},
        )


class D1Workspace:
    __slots__ = ("_root", "_base", "_closed")

    def __init__(self, base: dict[str, bytes]) -> None:
        if (type(base) is not dict or set(base) != set(PATHS)
                or any(type(key) is not str or type(value) is not bytes
                or len(value) > MAX_FILE_BYTES for key, value in base.items())):
            _fail()
        self._base = tuple((name, base[name]) for name in PATHS)
        self._root = Path(tempfile.mkdtemp(prefix="rw0-d1-workspace-"))
        self._closed = False
        try:
            self._materialize()
            self._read_all()
        except BaseException:
            self.close()
            raise

    @property
    def root(self) -> Path:
        if self._closed:
            _fail()
        return self._root

    def _parent_fd(self, parts: tuple[str, ...], *, create: bool) -> int:
        fd = os.open(self._root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try:
            for part in parts[:-1]:
                if create:
                    try:
                        os.mkdir(part, mode=0o700, dir_fd=fd)
                    except FileExistsError:
                        pass
                new_fd = os.open(part, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW,
                                 dir_fd=fd)
                os.close(fd)
                fd = new_fd
            return fd
        except BaseException:
            os.close(fd)
            raise

    def _materialize(self) -> None:
        for name, contents in self._base:
            parts = _check_path(name)
            parent = self._parent_fd(parts, create=True)
            try:
                fd = os.open(parts[-1], os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                             os.O_NOFOLLOW, 0o600, dir_fd=parent)
                try:
                    offset = 0
                    while offset < len(contents):
                        offset += os.write(fd, contents[offset:])
                    os.fchmod(fd, 0o644)
                finally:
                    os.close(fd)
            finally:
                os.close(parent)

    def _names(self) -> set[str]:
        names: set[str] = set()
        stack = [(self._root, "")]
        while stack:
            directory, prefix = stack.pop()
            for entry in os.scandir(directory):
                relative = prefix + entry.name
                status = entry.stat(follow_symlinks=False)
                if stat.S_ISDIR(status.st_mode):
                    if relative != ".docs" and relative != ".docs/system_overview":
                        _fail()
                    stack.append((Path(entry.path), relative + "/"))
                elif stat.S_ISREG(status.st_mode):
                    if relative not in PATHS:
                        _fail("excessive_candidate")
                    if status.st_nlink != 1:
                        _fail()
                    names.add(relative)
                else:
                    _fail()
        return names

    def _read_all(self) -> dict[str, bytes]:
        names = self._names()
        if names != set(PATHS):
            _fail("missing_candidate" if names < set(PATHS) else "excessive_candidate")
        observed: dict[str, bytes] = {}
        for name in PATHS:
            parts = _check_path(name)
            parent = self._parent_fd(parts, create=False)
            try:
                fd = os.open(parts[-1], os.O_RDONLY | os.O_NOFOLLOW, dir_fd=parent)
                try:
                    status = os.fstat(fd)
                    if (not stat.S_ISREG(status.st_mode) or status.st_nlink != 1
                            or stat.S_IMODE(status.st_mode) != 0o644
                            or status.st_size > MAX_FILE_BYTES):
                        _fail("excessive_candidate" if status.st_size > MAX_FILE_BYTES
                              else "unsafe_candidate")
                    data = bytearray()
                    while len(data) <= MAX_FILE_BYTES:
                        chunk = os.read(fd, min(65536, MAX_FILE_BYTES + 1 - len(data)))
                        if not chunk:
                            break
                        data.extend(chunk)
                    if len(data) > MAX_FILE_BYTES or len(data) != status.st_size:
                        _fail("excessive_candidate" if len(data) > MAX_FILE_BYTES
                              else "unsafe_candidate")
                    observed[name] = bytes(data)
                finally:
                    os.close(fd)
            finally:
                os.close(parent)
        return observed

    def capture(self, *, selected_path: str) -> D1CandidateCapture:
        if self._closed or type(selected_path) is not str or selected_path not in PATHS:
            _fail()
        after = self._read_all()
        before = dict(self._base)
        changed = tuple(name for name in PATHS if before[name] != after[name])
        if not changed:
            _fail("missing_candidate")
        if len(changed) > 1:
            _fail("excessive_candidate")
        if changed != (selected_path,):
            _fail()
        return D1CandidateCapture(
            tuple(D1CapturedEntry(name, "100644", before[name], after[name])
                  for name in PATHS),
            selected_path,
        )

    def close(self) -> None:
        if self._closed:
            return
        shutil.rmtree(self._root)
        self._closed = True

    def __enter__(self) -> D1Workspace:
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
