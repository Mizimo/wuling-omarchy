#!/usr/bin/env python3
"""Read-only inventory of user configuration; raw output stays outside git."""
import hashlib
import json
import os
from pathlib import Path
import stat

root = Path.home() / '.config'
rows = []
for directory, directories, files in os.walk(root, followlinks=False):
    for name in sorted(directories + files):
        path = Path(directory) / name
        info = path.lstat()
        row = {'path': str(path.relative_to(root)), 'mode': stat.S_IMODE(info.st_mode)}
        if path.is_symlink():
            row.update(type='link', target=os.readlink(path))
        elif path.is_file():
            row.update(type='file', sha256=hashlib.sha256(path.read_bytes()).hexdigest())
        elif path.is_dir():
            row.update(type='directory')
        else:
            row.update(type='special')
        rows.append(row)
print(json.dumps(sorted(rows, key=lambda row: row['path']), indent=2))
