"""WULING runtime: Python standard library only."""

from pathlib import Path
import json
import os
import subprocess

ROOT = Path(__file__).resolve().parents[3]
SCHEMA = 1


class Error(Exception):
    """An actionable user-facing error."""


def paths():
    home = Path.home()
    return {
        "home": home,
        "config": Path(os.environ.get("XDG_CONFIG_HOME", home / ".config")) / "wuling",
        "data": Path(os.environ.get("XDG_DATA_HOME", home / ".local/share")) / "wuling",
        "state": Path(os.environ.get("XDG_STATE_HOME", home / ".local/state")) / "wuling",
        # Omarchy's own paths are HOME-relative, including with XDG overrides.
        "themes": home / ".config/omarchy/themes",
        "current": home / ".local/state/omarchy/current",
    }


def read_json(path, default=None):
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as exc:
        raise Error(f"Cannot read {path}: {exc}") from exc


def command(argv, **kwargs):
    try:
        result = subprocess.run(argv, capture_output=True, text=True, timeout=120, **kwargs)
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise Error(f"Cannot run {argv[0]}: {exc}") from exc
    if result.returncode:
        raise Error(f"{' '.join(argv)} failed: {result.stderr.strip() or result.stdout.strip()}")
    return result.stdout.strip()


def atomic_write(path, data, mode=0o644):
    """Same-directory replacement; callers own locking and rollback."""
    import tempfile
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".wuling-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(data.encode() if isinstance(data, str) else data)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(name, mode)
        os.replace(name, path)
    finally:
        Path(name).unlink(missing_ok=True)
