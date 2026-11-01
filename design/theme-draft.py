#!/usr/bin/env python3
"""Design draft of the four themes used for VM screenshots (not the product; the product generates these from one token file).

    python3 design/theme-draft.py   → design/theme-draft/<theme>/ (not tracked; unlock.png needs Chromium and design/fonts)
"""
import os, pathlib, shutil, subprocess, tempfile
ROOT = pathlib.Path(__file__).resolve().parent
OUT = ROOT / 'theme-draft'

MIST = dict(mode='dark', accent='#FEF700', selection='#24302D', muted='#4D5D59',
  background='#0E1211', dark_background='#0A0D0C', darker_background='#050707', lighter_background='#141A18',
  foreground='#C9D3CE', dark_foreground='#6F827D', light_foreground='#E6EBE5', bright_foreground='#F4F5EF',
  red='#E3432F', yellow='#FEF700', orange='#C9A55C', green='#62D9A6', cyan='#49B9C2', blue='#4C93C6', magenta='#C65D7B', brown='#6B5A36',
  bright_red='#FF6B57', bright_yellow='#FFFA8A', bright_green='#9AF2CC', bright_cyan='#86DAE0', bright_blue='#79B4E0', bright_magenta='#E68BA5',
  hyprland_active_border='#FEF700', hyprland_inactive_border='#24302D')
PAPER = dict(mode='light', accent='#6B5F00', selection='#D3D9D1', muted='#A3ADA8',
  background='#ECEEE7', dark_background='#E4E7E0', darker_background='#D9DDD5', lighter_background='#F6F7F2',
  foreground='#2A3330', dark_foreground='#7A8783', light_foreground='#121614', bright_foreground='#121614',
  red='#C8361F', yellow='#7A6F00', orange='#8F6B1E', green='#0F8A68', cyan='#1D7F88', blue='#2F6F9E', magenta='#A33F62', brown='#6B5A36',
  bright_red='#A82A1C', bright_yellow='#6B5F00', bright_green='#0B6B51', bright_cyan='#166870', bright_blue='#265C84', bright_magenta='#88324F',
  hyprland_active_border='#121614', hyprland_inactive_border='#C3CBC3')

def colors(p):
    return ''.join(f'{k} = "{v}"\n' for k, v in p.items())

def shell(p, *, ink0, ink1, ink2, ink3, line, fg, fg_dim, crit, crit_txt,
          bar_h=30, sel_bg, sel_alpha, sel_txt, sel_border, sel_w, pop_border, pop_w, mark, lock_border, scrim_a=.72):
    return f'''# WULING design draft for VM screenshots: not the product.
[bar]
background       = "{ink2}"
background-alpha = 1.0
text             = "{fg}"
active           = "{crit}"
scale-with-font  = true
size-horizontal  = {bar_h}
size-vertical    = {bar_h + 2}

[hyprland]
active-border            = "{p['hyprland_active_border']}"
active-border-foreground = "{line}"

[controls]
normal-color        = "{fg}"
normal-fill-alpha   = 0.04
normal-border       = "{line}"
normal-border-width = 1
normal-border-alpha = 1.0
hover-cursor-color        = "{fg}"
hover-cursor-fill-alpha   = 0.08
hover-cursor-border       = "{line}"
hover-cursor-border-width = 1
hover-cursor-border-alpha = 1.0
focus-color        = "{fg}"
focus-fill-alpha   = 0.08
focus-border       = "{mark}"
focus-border-width = 1
focus-border-alpha = 1.0
selected-color        = "{fg}"
selected-fill-alpha   = 0.14
selected-border       = "{fg}"
selected-border-width = 0
selected-border-alpha = 1.0
pressed-fill-alpha   = 0.22
selection-fill-alpha = 0.35

[spacing]
scale = 1.0
scale-with-font = true

[font]
base-size = 12

[popups]
background       = "{ink2}"
background-alpha = 1.0
text             = "{fg}"
border           = "{pop_border}"
border-alpha     = 1.0
border-width     = {pop_w}

[tooltip]
background       = "{ink3}"
background-alpha = 0.97
text             = "{fg}"
border           = "{line}"
border-alpha     = 1.0

[notifications]
background       = "{ink3}"
background-alpha = 1.0
text             = "{fg}"
border           = "{pop_border}"
border-alpha     = 1.0
border-width     = {pop_w}
countdown        = "{mark}"

[menu]
background                = "{ink2}"
background-alpha          = 1.0
text                      = "{fg}"
border                    = "{pop_border}"
border-alpha              = 1.0
scrim                     = "{ink0}"
scrim-alpha               = {scrim_a}
selected-background       = "{sel_bg}"
selected-background-alpha = {sel_alpha}
selected-text             = "{sel_txt}"
selected-border           = "{sel_border}"
selected-border-alpha     = 1.0
selected-border-width     = "{sel_w}"

[polkit]
background       = "{ink2}"
background-alpha = 1.0
text             = "{fg}"
text-error       = "{crit_txt}"
border           = "{p['hyprland_active_border']}"
border-error     = "{crit}"
border-alpha     = 1.0
scrim            = "{ink0}"
scrim-alpha      = {scrim_a}
accent           = "{mark}"

[lock]
background       = "{ink1}"
background-alpha = 0.88
text             = "{fg}"
placeholder      = "{fg_dim}"
text-error       = "{crit_txt}"
border           = "{line}"
border-active    = "{p['hyprland_active_border']}"
border-error     = "{crit}"
border-alpha     = 1.0
selection        = "{mark}"
selection-alpha  = 0.35

[image-picker]
scrim                   = "{ink0}"
scrim-alpha             = {scrim_a}
text                    = "{fg}"
selected-border         = "{p['hyprland_active_border']}"
selected-border-alpha   = 1.0
unselected-border       = "{fg}"
unselected-border-alpha = 0.28
'''

DARK = dict(ink0='#050707', ink1='#0A0D0C', ink2='#0E1211', ink3='#141A18', line='#2B3734', fg='#E6EBE5', fg_dim='#6F827D', crit='#E3432F', crit_txt='#FF6B57', mark='#FEF700')
THEMES = {
  # as before: white selected row with a yellow edge, hairline cards
  'wuling-as': (MIST, shell(MIST, **DARK, sel_bg='#F4F5EF', sel_alpha=1.0, sel_txt='#0E1211', sel_border='#FEF700', sel_w='0 0 0 2', pop_border='#2B3734', pop_w=1, lock_border='#2B3734'), 'bg-original-mist.png'),
  # calm: selection is a quiet raised row, yellow only marks the focused window's neighbours; neutral active border
  'wuling-calm': (dict(MIST, hyprland_active_border='#C9D3CE'), shell(dict(MIST, hyprland_active_border='#C9D3CE'), **dict(DARK, mark='#C9D3CE'), bar_h=28, sel_bg='#E6EBE5', sel_alpha=.1, sel_txt='#F4F5EF', sel_border='#2B3734', sel_w='0', pop_border='#2B3734', pop_w=1, lock_border='#2B3734', scrim_a=.5), 'land-mist-1920x1080.png'),
  # bold: yellow selection fill, yellow card borders
  'wuling-bold': (MIST, shell(MIST, **DARK, bar_h=32, sel_bg='#FEF700', sel_alpha=1.0, sel_txt='#0E1211', sel_border='#0E1211', sel_w='0 0 0 2', pop_border='#FEF700', pop_w=1, lock_border='#FEF700', scrim_a=.8), 'bg-original-mist.png'),
  # paper: canon yellow only as a fill with ink on top
  'wuling-paper': (PAPER, shell(PAPER, ink0='#D9DDD5', ink1='#E4E7E0', ink2='#ECEEE7', ink3='#F6F7F2', line='#C3CBC3', fg='#121614', fg_dim='#7A8783', crit='#C8361F', crit_txt='#A82A1C', mark='#121614', sel_bg='#FEF700', sel_alpha=1.0, sel_txt='#121614', sel_border='#121614', sel_w='0 0 0 2', pop_border='#C3CBC3', pop_w=1, lock_border='#C3CBC3', scrim_a=.74), 'bg-original-paper.png'),
}
for name, (pal, sh, bg) in THEMES.items():
    d = OUT / name
    (d / 'backgrounds').mkdir(parents=True, exist_ok=True)
    (d / 'colors.toml').write_text(colors(pal))
    (d / 'shell.toml').write_text(sh)
    (d / 'icons.theme').write_text('Yaru-yellow\n' if pal is not PAPER else 'Yaru-olive\n')
    if pal is PAPER:
        (d / 'light.mode').write_text('')
    shutil.copy(ROOT / 'assets' / bg, d / 'backgrounds' / ('1-' + bg))

# unlock.png: emblem and name on transparency, the size Omarchy's own themes use (1108×523)
CHROME = os.environ.get('CHROME') or sorted(pathlib.Path.home().glob('.cache/ms-playwright/chromium-*/chrome-linux64/chrome'))[-1]
PAGE = '''<!doctype html><meta charset="utf-8"><style>
@font-face {{ font-family: "Geist Mono"; src: url("{font}"); }}
html, body {{ margin: 0; width: 1108px; height: 523px; background: transparent; }}
.w {{ width: 1108px; height: 523px; display: flex; flex-direction: column; align-items: center; justify-content: center; gap: 28px; }}
img {{ width: 190px; height: 190px; display: block; }}
.t {{ display: flex; align-items: center; gap: 20px; color: {fg}; font: 500 22px/1 "Geist Mono", monospace; letter-spacing: .34em; }}
.t b {{ font: 900 44px/1 "Noto Serif CJK TC", "Noto Serif TC", serif; letter-spacing: .14em; }}
.t i {{ width: 1px; height: 30px; background: {ln}; display: block; }}
</style><div class="w"><img src="{emblem}"><div class="t"><b>武陵</b><i></i><span>WULING</span></div></div>'''
for name, (pal, _, _) in THEMES.items():
    light = pal is PAPER
    page = PAGE.format(font=(ROOT / 'fonts' / 'GeistMono-Bold.ttf').as_uri(), emblem=(ROOT / 'assets' / 'emblem.svg').as_uri(),
                       fg='#121614' if light else '#E6EBE5', ln='#7A8783' if light else '#6F827D')
    with tempfile.NamedTemporaryFile('w', suffix='.html', encoding='utf-8') as f:
        f.write(page); f.flush()
        subprocess.run([str(CHROME), '--headless=new', '--no-sandbox', '--disable-gpu', '--hide-scrollbars', '--default-background-color=00000000',
                        '--window-size=1108,523', '--virtual-time-budget=2000', f'--screenshot={OUT / name / "unlock.png"}', f'file://{f.name}'],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
print('ok', list(THEMES))
