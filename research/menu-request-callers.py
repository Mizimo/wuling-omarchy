#!/usr/bin/env python3
"""Read-only direct and transitive request/reply caller inventory.

Usage: menu-request-callers.py /path/to/omarchy-checkout > callers.csv
This lexically follows shipped omarchy-* command references. It inventories
potential callers, not proof that each conditional path executes. No source
code is executed or copied into the output.
"""
import csv,re,sys
from pathlib import Path
root=Path(sys.argv[1]);files={p.name:p for p in (root/'bin').iterdir() if p.is_file()}
refs={}
for name,p in files.items():
 for number,line in enumerate(p.read_text(errors='replace').splitlines(),1):
  if line.lstrip().startswith('#'):continue
  for target in set(re.findall(r'\bomarchy-[a-z0-9-]+\b',line)):
   if target!=name and target in files:refs.setdefault(name,[]).append((target,number))
seeds={'omarchy-menu-select','omarchy-menu-input'}
paths={s:[s] for s in seeds}
changed=True
while changed:
 changed=False
 for name,links in refs.items():
  if name in paths:continue
  candidates=[(target,line) for target,line in links if target in paths]
  if candidates:
   target,line=min(candidates,key=lambda p:len(paths[p[0]]));paths[name]=[name]+paths[target];changed=True
out=csv.writer(sys.stdout,lineterminator="\n");out.writerow(['file','line','kind','request_path'])
for name in sorted(paths):
 if name in seeds:continue
 target=paths[name][1];line=next(n for t,n in refs[name] if t==target)
 out.writerow(['bin/'+name,line,'script',' -> '.join(paths[name])])
# Keep the whole shipped JSONC action surface, including extensions/templates.
for p in sorted(root.rglob('*.jsonc')):
 for number,line in enumerate(p.read_text(errors='replace').splitlines(),1):
  if '"action"' not in line or line.lstrip().startswith('//'):continue
  for command in sorted(set(re.findall(r'\bomarchy-[a-z0-9-]+\b',line)) & paths.keys()):
   row=re.match(r'\s*"([^"]+)"',line)
   out.writerow([str(p.relative_to(root)),number,'action:'+ (row[1] if row else '?'),' -> '.join(paths[command])])
