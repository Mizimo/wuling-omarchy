#!/usr/bin/env python3
"""List the documented template keys without executing upstream code.

Usage: inventory-theme.py SOURCE_406 SOURCE_450 OUTPUT.csv
Consumer-only tokens and parameterized border keys are documented separately
in omarchy-shell-api.md. This inventory is not a TOML schema validator.
"""
import csv
from pathlib import Path
import re
import sys


def fields(root):
    source = Path(root) / 'default/themed/shell.toml.tpl'
    section = ''
    output = {}
    for line_number, line in enumerate(source.read_text().splitlines(), 1):
        header = re.fullmatch(r'\[([\w-]+)\]', line)
        if header:
            section = header[1]
        field = re.match(r'\s*(#\s*)?([\w-]+)\s*=\s*(.+)', line)
        if field and section:
            output[section + '.' + field[2]] = (line_number, field[3], bool(field[1]))
    return output


if __name__ == '__main__':
    a, b = fields(sys.argv[1]), fields(sys.argv[2])
    with open(sys.argv[3], 'w', newline='') as stream:
        writer = csv.writer(stream, lineterminator='\n')
        writer.writerow(['key', '4.0.6_line', '4.0.6_template_value', '4.0.6_commented',
                         '4.5.0-rc2_line', '4.5.0-rc2_template_value', '4.5.0-rc2_commented'])
        for key in sorted(a.keys() | b.keys()):
            writer.writerow([key, *a.get(key, ('', '', '')), *b.get(key, ('', '', ''))])
