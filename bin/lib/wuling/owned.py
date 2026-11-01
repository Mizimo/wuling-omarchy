"""Owned resources, serialised transactions and recoverable filesystem changes."""

from contextlib import contextmanager
from pathlib import Path
import fcntl
import hashlib
import json
import os
import shutil
import stat
import uuid
from . import Error, atomic_write, paths, read_json


def exists(path):
    return path.exists() or path.is_symlink()


def stamp(path):
    """Tree identity includes unexpected files, modes and symlink targets."""
    if not exists(path):
        return None
    if path.is_symlink():
        return {"type": "link", "target": os.readlink(path)}
    info = path.stat()
    if path.is_file():
        return {"type": "file", "mode": stat.S_IMODE(info.st_mode),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
    if path.is_dir():
        return {"type": "directory", "mode": stat.S_IMODE(info.st_mode),
                "entries": {p.name: stamp(p) for p in sorted(path.iterdir())}}
    raise Error(f"Refusing special file {path}")


def remove(path):
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.is_dir():
        shutil.rmtree(path)


def block(text, name, content, previous=None):
    """Replace only an unchanged named block; preserve all surrounding bytes."""
    start, end = f"-- BEGIN WULING {name}\n", f"-- END WULING {name}\n"
    count = text.count(start), text.count(end)
    if count == (0, 0):
        if previous is not None:
            raise Error(f"Owned {name} block was removed; refusing to recreate it silently")
        if content is None:
            return text
        return text + ("\n" if text and not text.endswith("\n") else "") + start + content + end
    if count != (1, 1):
        raise Error(f"Malformed or duplicate WULING {name} block")
    first, last = text.index(start), text.index(end) + len(end)
    # The caller records every appended byte, including a separator added to a
    # file without a final newline. Removing our block must restore those bytes.
    separator = ""
    if previous is not None and previous.startswith("\n" + start) and first > 0 and text[first - 1] == "\n":
        first -= 1
        separator = "\n"
    current = text[first:last]
    if previous is None or current != previous:
        raise Error(f"The WULING {name} block is not owned or was edited; leaving it unchanged")
    return text[:first] + (separator + start + content + end if content is not None else "") + text[last:]


@contextmanager
def locked():
    # Keep the lock outside the owned state tree so uninstall can remove that
    # tree without permitting a second process to acquire a new lock inode.
    import tempfile
    identity = hashlib.sha256(str(paths()["state"]).encode()).hexdigest()[:20]
    lock = Path(os.environ.get("XDG_RUNTIME_DIR", tempfile.gettempdir())) / f"wuling-{os.getuid()}-{identity}.lock"
    fd = os.open(lock, os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW, 0o600)
    try:
        if os.fstat(fd).st_uid != os.getuid():
            raise Error("WULING lock belongs to another user")
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        os.close(fd)


class Transaction:
    """Write-ahead journal with sibling backups; recover before any mutation."""

    def __init__(self):
        self.root = paths()["state"]
        self.path = self.root / "transaction.json"
        self.data = {"schema_version": 1, "owner": "wuling", "id": uuid.uuid4().hex, "operations": [], "directories": []}

    def flush(self):
        atomic_write(self.path, json.dumps(self.data, indent=2) + "\n", 0o600)

    def mkdir(self, path):
        missing = []
        p = path
        while not exists(p):
            missing.append(p)
            p = p.parent
        if not p.is_dir():
            raise Error(f"Not a directory: {p}")
        for p in reversed(missing):
            self.data["directories"].append(str(p))
            self.flush()
            p.mkdir()

    def replace(self, path, source=None, *, data=None, link=None, delete=False, mode=0o644):
        path = Path(path)
        self.mkdir(path.parent)
        suffix = self.data["id"] + "-" + str(len(self.data["operations"]))
        backup = path.parent / (".wuling-old-" + suffix)
        staged = path.parent / (".wuling-new-" + suffix)
        op = {"path": str(path), "backup": str(backup), "staged": str(staged), "before": stamp(path), "after": None}
        self.data["operations"].append(op)
        self.flush()
        if not delete:
            if link is not None:
                staged.symlink_to(link)
            elif source is not None:
                if source.is_dir():
                    shutil.copytree(source, staged, symlinks=True)
                else:
                    shutil.copy2(source, staged)
            else:
                atomic_write(staged, data, mode)
            op["after"] = stamp(staged)
            self.flush()
        if exists(path):
            os.replace(path, backup)
        if not delete:
            os.replace(staged, path)

    def rollback(self):
        conflicts = []
        for op in reversed(self.data["operations"]):
            path, backup, staged = (Path(op[k]) for k in ("path", "backup", "staged"))
            current = stamp(path)
            if exists(backup):
                if current not in (None, op["after"]):
                    conflicts.append(str(path))
                    continue
                remove(path)
                os.replace(backup, path)
            elif op["before"] is None and current == op["after"]:
                remove(path)
            elif current not in (op["before"], None):
                conflicts.append(str(path))
            remove(staged)
        if conflicts:
            raise Error("Interrupted operation has edited files; preserved journal/backups for: " + ", ".join(conflicts))
        if self.data.get("theme_restore"):
            from .lifecycle import restore_external
            restore_external(self.data["theme_restore"])
        self.path.unlink(missing_ok=True)
        for name in reversed(self.data["directories"]):
            try:
                Path(name).rmdir()
            except OSError:
                pass

    def commit(self):
        self.data["committed"] = True
        self.flush()
        self.clean()

    def clean(self):
        for op in self.data["operations"]:
            remove(Path(op["backup"]))
            remove(Path(op["staged"]))
        self.path.unlink(missing_ok=True)

    def __enter__(self):
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.path.exists():
            raise Error("An interrupted transaction must be recovered first")
        self.flush()
        return self

    def __exit__(self, kind, value, traceback):
        if kind is not None:
            self.rollback()
        else:
            self.commit()


def recover():
    tx = Transaction()
    data = read_json(tx.path)
    if data is None:
        return
    if data.get("owner") != "wuling" or data.get("schema_version") != 1:
        raise Error("Unrecognised transaction journal; leaving it untouched")
    tx.data = data
    if data.get("committed"):
        tx.clean()
    else:
        tx.rollback()
