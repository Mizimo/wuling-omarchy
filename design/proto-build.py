#!/usr/bin/env python3
"""Pack the Dispatch prototype into one self-contained HTML file (fonts subset, icons by codepoint, images inlined).

    python3 design/proto-build.py        → design/proto/dispatch.html

Fonts come from design/fonts (run design/fetch-fonts.sh first). Needs fontTools, brotli and Pillow.
"""
import base64, io, json, logging, pathlib, re
from fontTools import subset as fts
from fontTools.ttLib import TTFont
from PIL import Image
logging.getLogger('fontTools').setLevel(logging.ERROR)

D = pathlib.Path(__file__).resolve().parent
SRC, FONTS, OUT = D / 'src', D / 'fonts', D / 'proto' / 'dispatch.html'

def read(p): return (SRC / p).read_text(encoding='utf-8')

sources = read('mock.js') + read('proto.js') + read('proto.css') + read('ui.css')
chars = {c for c in sources if ord(c) >= 32} | set('0123456789 ,.:;·—–-+%°×÷=()[]{}<>/\\\'"!?#@&*_~|') | {' ', '›', '‹', '⏎', '↑', '↓', '←', '→', '●', '■', '▌'}

def ligatures(font):
    cmap = font.getBestCmap()
    ch = {g: cp for cp, g in cmap.items() if cp < 128}
    pua = {}
    for cp, g in cmap.items():
        if cp >= 0xE000: pua.setdefault(g, cp)
    names = {}
    for lk in font['GSUB'].table.LookupList.Lookup:
        for t in lk.SubTable:
            t = getattr(t, 'ExtSubTable', t)
            if getattr(t, 'LookupType', 0) != 4: continue
            for first, ligs in t.ligatures.items():
                for lig in ligs:
                    seq = [first] + list(lig.Component)
                    if all(g in ch for g in seq) and lig.LigGlyph in pua:
                        names[''.join(chr(ch[g]) for g in seq)] = pua[lig.LigGlyph]
    return names

def subset(path, unicodes, icons=False):
    opts = fts.Options(); opts.flavor = 'woff2'; opts.layout_features = [] if icons else ['*']; opts.name_IDs = ['*']; opts.hinting = False
    if icons: opts.drop_tables += ['GSUB', 'GPOS', 'STAT']   # icons are addressed by codepoint; the ligature table is not needed
    opts.notdef_outline = True; opts.ignore_missing_glyphs = True; opts.ignore_missing_unicodes = True
    f = TTFont(path); s = fts.Subsetter(opts); s.populate(unicodes=sorted(unicodes)); s.subset(f)
    f.flavor = 'woff2'; b = io.BytesIO(); f.save(b); return base64.b64encode(b.getvalue()).decode()

# Material Symbols: only the icons named in the sources, addressed by their private-use codepoints
ms_path = FONTS / 'MaterialSymbolsSharp.ttf'
lig = ligatures(TTFont(ms_path))
used = sorted({w for w in re.findall(r"[a-z][a-z0-9_]{2,}", sources) if w in lig})
icons = {n: chr(lig[n]) for n in used}

faces, total = [], 0
for m in re.finditer(r'font-family: "([^"]+)"; font-weight: ([0-9 ]+); src: url\("\.\./fonts/([^"]+)"\)', read('fonts.css')):
    fam, w, fn = m.groups()
    uni = {ord(c) for c in icons.values()} if fn.startswith('MaterialSymbols') else {ord(c) for c in chars}
    data = subset(FONTS / fn, uni, icons=fn.startswith('MaterialSymbols')); total += len(data)
    faces.append(f'@font-face{{font-family:"{fam}";font-weight:{w};font-style:normal;font-display:block;src:url(data:font/woff2;base64,{data}) format("woff2")}}')
fonts_css = '\n'.join(faces) + '\n' + re.sub(r'^@font-face[^\n]*\n', '', read('fonts.css'), flags=re.M)

def img(name, w=1366):
    im = Image.open(D / 'assets' / name).convert('RGB')
    if im.width != w: im = im.resize((w, round(im.height * w / im.width)), Image.LANCZOS)
    b = io.BytesIO(); im.save(b, 'JPEG', quality=78, optimize=True); return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

ui = re.sub(r'@import url\("[^"]+"\);\n', '', read('ui.css'))
ui = re.sub(r'url\("\.\./assets/([^"]+\.(?:png|jpg))"\)', lambda m: f'url("{img(m.group(1))}")', ui)
html = f'''<!doctype html><html lang="zh-Hant"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>WULING · Dispatch 調度 — prototype</title>
<style>{fonts_css}\n{read('tokens.css')}\n{ui}\n{read('proto.css')}</style>
<script>window.ICONS={json.dumps(icons, ensure_ascii=False)};</script>
<script>{read('mock.js').replace("SCREEN = Q.get('screen') || 'desk'", "SCREEN = 'proto'")}</script>
<script>{read('proto.js')}</script>
</head><body><div class="stage"></div></body></html>'''
OUT.parent.mkdir(exist_ok=True)
OUT.write_text(html, encoding='utf-8')
print(f'{OUT.relative_to(D.parent)}  {len(html) / 1e6:.2f} MB · fonts {total / 1e6:.2f} MB (base64) · {len(icons)} icons')
