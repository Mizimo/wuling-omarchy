#!/usr/bin/env python3
"""Run only in a disposable, logged-in Omarchy VM with WULING uninstalled.

Usage: python3 tests/vm-theme-effects.py --disposable-vm
Raw inventories/logs stay in the VM's private cache, never in the repository.
"""
from pathlib import Path
import base64
import hashlib
import json
import os
import shlex
import shutil
import signal
import stat
import subprocess
import sys
import time

assert sys.argv[1:] == ["--disposable-vm"], "This fixture requires a disposable VM"
root = Path(__file__).resolve().parents[1]
home = Path.home()
evidence = home / ".cache/wuling-theme-effects-test"
evidence.mkdir(parents=True, exist_ok=True, mode=0o700)
state = home / ".local/state/wuling"
assert not state.exists(), "Start without WULING's state directory"
native = shutil.which("omarchy")
assert native
results = {}


def run(args, name, **kwargs):
    with (evidence / (name + ".txt")).open("w") as log:
        result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, timeout=180, **kwargs)
    return result.returncode


def inventory():
    # Verification may enumerate the fixture's config; the product must not.
    rows = {}
    folder = home / ".config"
    for directory, dirs, files in os.walk(folder, followlinks=False):
        for name in dirs + files:
            path = Path(directory) / name
            rel = str(path.relative_to(folder))
            if rel == "dconf/user":
                continue  # representation is not a logical desktop setting
            info = path.lstat()
            rows[rel] = [stat.S_IMODE(info.st_mode),
                         ["link", os.readlink(path)] if path.is_symlink() else
                         ["file", hashlib.sha256(path.read_bytes()).hexdigest()] if path.is_file() else ["directory"]]
    rows["dconf logical values"] = subprocess.check_output(["dconf", "dump", "/"], text=True)
    return rows


def compare(before, name):
    after = inventory()
    diff = [key for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)]
    (evidence / (name + ".json")).write_text(json.dumps({"before": before, "after": after, "diff": diff}, indent=2))
    assert not diff, diff


def barrier(command, name):
    folder = evidence / name
    folder.mkdir(exist_ok=True)
    marker, release = folder / "paused", folder / "release"
    marker.unlink(missing_ok=True)
    release.unlink(missing_ok=True)
    wrapper = folder / command
    original = shutil.which(command)
    condition = '[[ "$1 $2 $3" == "theme set wuling" ]]' if command == "omarchy" else "true"
    wrapper.write_text("#!/bin/bash\nif " + condition + "; then\n touch " + shlex.quote(str(marker))
                       + "\n while [[ ! -e " + shlex.quote(str(release)) + " ]]; do sleep .05; done\nfi\nexec "
                       + shlex.quote(original) + ' "$@"\n')
    wrapper.chmod(0o700)
    env = {**os.environ, "PATH": str(folder) + ":" + os.environ["PATH"]}
    log = (folder / "install.txt").open("w")
    child = subprocess.Popen([str(root / "install"), "--yes"], env=env, stdout=log,
                             stderr=subprocess.STDOUT, start_new_session=True)
    deadline = time.monotonic() + 120
    while not marker.exists() and child.poll() is None and time.monotonic() < deadline:
        time.sleep(.1)
    if not marker.exists():
        if child.poll() is None:
            os.killpg(child.pid, signal.SIGTERM)
        raise AssertionError("No fixture pause point; inspect the install log")
    return child, log, release


app = home / ".config/wuling-test-unrelated-app/session.json"
assert not app.parent.exists()
app.parent.mkdir()
old, new = "old synthetic draft\n", "independent new synthetic draft\n"
app.write_text(old)
child, log, release = barrier("omarchy", "concurrent")
journal = (state / "transaction.json").read_text()
assert "wuling-test-unrelated-app" not in journal
assert old.strip() not in journal and base64.b64encode(old.encode()).decode() not in journal
app.write_text(new)
release.touch()
assert child.wait(timeout=180) == 0
log.close()
manifest = (state / "install.json").read_text()
assert "wuling-test-unrelated-app" not in manifest
assert new.strip() not in manifest and base64.b64encode(new.encode()).decode() not in manifest
assert run([str(root / "bin/wuling"), "uninstall", "--yes"], "concurrent-remove") == 0
assert app.read_text() == new
assert not state.exists()
app.unlink()
app.parent.rmdir()
results["concurrent_write_preserved_and_not_recorded"] = True

before = inventory()
for iteration in (1, 2):
    assert run([str(root / "install"), "--yes"], "install-" + str(iteration)) == 0
for iteration in (1, 2):
    assert run([str(root / "bin/wuling"), "uninstall", "--yes"], "remove-" + str(iteration)) == 0
compare(before, "repeat-inventory")
assert not state.exists()
results["repeat_install_remove_clean"] = True

skills = home / ".agents/skills"
assert skills.is_dir()
mode = stat.S_IMODE(skills.stat().st_mode)
try:
    skills.chmod(0o555)
    assert run([str(root / "install"), "--yes"], "permission-failure") != 0
finally:
    skills.chmod(mode)
assert not state.exists()
compare(before, "permission-inventory")
results["permission_failure_removes_created_state"] = True

child, log, release = barrier("fc-cache", "interrupt")
os.killpg(child.pid, signal.SIGKILL)
child.wait(timeout=10)
log.close()
assert run([str(root / "bin/wuling"), "uninstall", "--yes"], "recover-interrupt") == 0
assert not state.exists()
compare(before, "interrupt-inventory")
results["interruption_recovery_removes_created_state"] = True

results["version"] = subprocess.check_output([native, "version"], text=True).strip()
(evidence / "result.json").write_text(json.dumps(results, indent=2) + "\n")
print(json.dumps(results, indent=2))
