"""Optional, view-owned cava stream. A missing analyzer is not an error."""

import json
import os
from pathlib import Path
import shutil
import signal
import subprocess
import tempfile
from . import SCHEMA


def bars(line):
    try:
        values = [int(value) for value in line.strip().strip(";").split(";")]
        return [min(1, max(0, value / 1000)) for value in values] if len(values) == 20 else None
    except ValueError:
        return None


def watch():
    def emit(values=None):
        print(json.dumps({"schema_version": SCHEMA, "available": values is not None, "bars": values or []}), flush=True)
    executable = shutil.which("cava")
    if not executable:
        emit()
        return
    def stop(signum, frame):
        raise KeyboardInterrupt
    original = signal.signal(signal.SIGTERM, stop)
    child = None
    try:
        os.setpriority(os.PRIO_PROCESS, 0, 19)
        with tempfile.TemporaryDirectory(prefix="wuling-spectrum-", dir=os.environ.get("XDG_RUNTIME_DIR")) as folder:
            config = Path(folder) / "config"
            config.write_text("[general]\nframerate = 20\nbars = 20\n[input]\nmethod = pipewire\nsource = auto\n"
                              "[output]\nmethod = raw\nraw_target = /dev/stdout\ndata_format = ascii\n"
                              "ascii_max_range = 1000\nbar_delimiter = 59\nframe_delimiter = 10\n")
            child = subprocess.Popen([executable, "-p", str(config)], stdout=subprocess.PIPE,
                                     stderr=subprocess.DEVNULL, text=True, start_new_session=True)
            for line in child.stdout:
                values = bars(line)
                if values is not None:
                    emit(values)
    except (OSError, BrokenPipeError, KeyboardInterrupt):
        pass
    finally:
        if child:
            try:
                os.killpg(child.pid, signal.SIGTERM)
                child.wait(timeout=.3)
            except subprocess.TimeoutExpired:
                os.killpg(child.pid, signal.SIGKILL)
                child.wait()
            except ProcessLookupError:
                child.wait()
            child.stdout.close()
        signal.signal(signal.SIGTERM, original)
