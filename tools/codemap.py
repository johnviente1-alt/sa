# Code map: lists what each engine file defines, with line numbers, so Claude never has to read the big files whole.
#   python3 codemap.py ENGINE/src/short [file.ts ...]      (no file names = every file)
# Then read only the lines needed: grep -n NAME file.ts, and Read with offset/limit around that line.
import os, re, sys
D = sys.argv[1]; only = sys.argv[2:]
pat = re.compile(r'^(export\s+)?(const|function|class|type|interface)\s+(\w+)|^  (private\s+|static\s+)?(\w+)\s*\(.*\)\s*(:\s*[\w<>\[\]|. ]+)?\s*\{\s*(//.*)?$')
for fn in sorted(os.listdir(D)):
    if not fn.endswith(('.ts', '.tsx')) or (only and fn not in only): continue
    L = open(os.path.join(D, fn)).read().split('\n'); kb = sum(len(x) + 1 for x in L) // 1024
    print(f'== {fn}  ({len(L)} lines, {kb} KB)')
    for i, line in enumerate(L):
        m = pat.match(line)
        if not m: continue
        name = m.group(3) or m.group(5)
        if name in ('if', 'for', 'while', 'switch', 'return', 'catch'): continue
        note = ''
        for j in (i - 1, i - 2):
            if j >= 0 and L[j].strip().startswith(('//', '/**', '*')):
                note = L[j].strip().lstrip('/*').strip()[:90]; break
        if not note and '//' in line: note = line.split('//', 1)[1].strip()[:90]
        print(f'  {i + 1:5d} {name}' + (f'  - {note}' if note else ''))
