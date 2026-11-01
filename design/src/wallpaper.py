#!/usr/bin/env python3
"""WULING // FIELD TERMINAL — wallpaper generator.

Layered karst ranges in jade mist (青綠山水, night) + Endfield survey overlay.
Design space is 1366x768 (KJR-01 eDP-1 @1x); render at any size via render.mjs
(the SVG uses viewBox + slice, so 16:9 targets crop nothing important).

usage: wallpaper.py [--variant mist|paper] [--layer land] > out.html   (+ --anchors)
       The old "full"/"plate" layers baked an invented seal, poem and coordinates — retired (DESIGN §0c);
       text and HUD now come only from the live overlay (src/mock-wall-canon.html, scene original-mist/paper).
       wallpaper.py --anchors > wallpaper-anchors.json
  full  : landscape + survey overlay + title block           (static reference / non-shell use)
  plate : landscape + faint grid/rulers, no title, no reticle (lock / overview backdrop)
  land  : landscape only — the shell draws grid, reticle, markers and typography live on top
  --anchors : image-space anchor points (design space 1366x768) for the live overlay
"""
import argparse
import math
import numpy as np

W, H = 1366, 768
WATER_Y = 632

PAL = {
    "mist": dict(
        sky=["#060909", "#0B1312", "#122420", "#18302A"],
        layers=[("#2E4F47", "#1B302B"), ("#213B35", "#132520"), ("#172D28", "#0D1A17"), ("#0F1D1A", "#09110F")],
        mist="138,190,174", glow="98,217,166", water="#08100E",
        ink="#E6EBE5", muted="#93A49F", label="#6F827D", dim="#4D5D59",
        yellow="#FEF700", jade="#62D9A6", red="#E3432F", seal_fg="#0E1211",
        grain_op=0.07, grid_op=0.035,
    ),
    "paper": dict(
        sky=["#F3F4EE", "#ECEEE6", "#E2E7DF", "#D7DFD7"],
        layers=[("#B9C9C1", "#CBD6CF"), ("#96AFA5", "#B4C4BC"), ("#6F8D83", "#94A99F"), ("#3F5A52", "#62786F")],
        mist="243,244,238", glow="98,217,166", water="#DCE3DC",
        ink="#121614", muted="#3E4A46", label="#5C6A66", dim="#8A9792",
        yellow="#FEF700", jade="#0F8A68", red="#C8361F", seal_fg="#F4F5EF",
        grain_op=0.09, grid_op=0.05,
    ),
}


def value_noise(x, scale, seed, octaves=4):
    """1D fractal value noise, cosine-interpolated, roughly in [-1, 1]."""
    rng = np.random.default_rng(seed)
    out = np.zeros_like(x, dtype=float)
    amp, freq, norm = 1.0, 1.0 / scale, 0.0
    for _ in range(octaves):
        n = int(x.max() * freq) + 3
        pts = rng.uniform(-1, 1, n)
        t = x * freq
        i = np.floor(t).astype(int)
        f = t - i
        f = (1 - np.cos(f * math.pi)) / 2
        out += amp * (pts[i] * (1 - f) + pts[i + 1] * f)
        norm += amp
        amp *= 0.5
        freq *= 2.0
    return out / norm


def ridge(x, base, peaks, seed, rough=6.0, rough_scale=60.0, canopy=0.0):
    """Union of peak profiles (y grows downward). peaks: (cx, height, width, power)."""
    y = np.full_like(x, float(base))
    rng = np.random.default_rng(seed + 7)
    for cx, h, w, p in peaks:
        if p >= 3:  # karst pillar: flat-ish top, steep cliff, asymmetric shoulders
            wl, wr = w * rng.uniform(.8, 1.15), w * rng.uniform(.8, 1.15)
            u = np.where(x < cx, (cx - x) / wl, (x - cx) / wr)
            inside = np.clip(1 - np.abs(u) ** (p * 1.9), 0, None) ** (1 / 3.2)
            skirt = np.exp(-np.abs(u / 1.9) ** 2) * .32
            prof = base - h * np.maximum(inside, skirt)
        else:
            prof = base - h * np.exp(-np.abs((x - cx) / w) ** p)
        y = np.minimum(y, prof)
    y += rough * value_noise(x, rough_scale, seed)
    if canopy:
        y += canopy * value_noise(x, 7.0, seed + 99, octaves=2)          # forest fringe
        y += canopy * 1.4 * value_noise(x, 19.0, seed + 131, octaves=2)  # crags
    return y


def path_from(x, y, close_to=H + 2):
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, y))
    return f"M{x[0]:.1f},{close_to} L{pts} L{x[-1]:.1f},{close_to} Z"


LAYERS = [
    # base, peaks(cx, h, w, p), rough, canopy, seed
    (458, [(150, 120, 150, 2), (420, 95, 190, 2), (690, 150, 110, 2.2), (870, 178, 64, 2.6),
           (1060, 120, 120, 2), (1180, 150, 140, 2), (1330, 112, 120, 2)], 7, 0, 11),
    (508, [(300, 92, 210, 2), (520, 84, 150, 2), (640, 168, 36, 3), (722, 206, 30, 3.2),
           (775, 140, 26, 3), (960, 222, 40, 3.1), (1012, 158, 28, 3), (1225, 192, 44, 3),
           (1292, 150, 34, 3)], 5, 2.0, 23),
    (566, [(80, 70, 160, 2), (560, 146, 32, 3), (604, 186, 26, 3.4), (700, 70, 90, 2),
           (830, 66, 120, 2), (1112, 176, 34, 3.2), (1158, 214, 30, 3.4), (1205, 120, 40, 3)], 5, 3.0, 37),
    (628, [(40, 236, 250, 2.2), (300, 90, 180, 2), (640, 46, 160, 2), (900, 58, 150, 2),
           (1260, 150, 150, 2.2), (1366, 214, 160, 2.4)], 6, 3.5, 51),
]


def svg(variant="mist", layer="full"):
    P = PAL[variant]
    x = np.linspace(0, W, 684)
    ridges = [ridge(x, b, pk, s, rough=r, canopy=c) for b, pk, r, c, s in LAYERS]
    defs, body = [], []

    # ---------- defs ----------
    s = P["sky"]
    defs.append(f'''<linearGradient id="sky" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{s[0]}"/><stop offset=".38" stop-color="{s[1]}"/>
      <stop offset=".62" stop-color="{s[2]}"/><stop offset=".82" stop-color="{s[3]}"/></linearGradient>''')
    for i, (top, bot) in enumerate(P["layers"]):
        defs.append(f'''<linearGradient id="L{i}" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="{top}"/><stop offset=".55" stop-color="{bot}"/></linearGradient>''')
    defs.append(f'''<linearGradient id="mistband" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="rgb({P['mist']})" stop-opacity="0"/>
      <stop offset=".7" stop-color="rgb({P['mist']})" stop-opacity=".16"/>
      <stop offset="1" stop-color="rgb({P['mist']})" stop-opacity=".22"/></linearGradient>''')
    defs.append(f'''<radialGradient id="glow" cx="930" cy="470" r="620" gradientUnits="userSpaceOnUse">
      <stop offset="0" stop-color="rgb({P['glow']})" stop-opacity=".13"/>
      <stop offset=".5" stop-color="rgb({P['glow']})" stop-opacity=".04"/>
      <stop offset="1" stop-color="rgb({P['glow']})" stop-opacity="0"/></radialGradient>''')
    defs.append(f'''<linearGradient id="reflfade" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#fff" stop-opacity=".55"/><stop offset=".6" stop-color="#fff" stop-opacity="0"/></linearGradient>
      <mask id="reflmask" maskUnits="userSpaceOnUse" x="0" y="{WATER_Y}" width="{W}" height="{H-WATER_Y}">
        <rect x="0" y="{WATER_Y}" width="{W}" height="{H-WATER_Y}" fill="url(#reflfade)"/></mask>''')
    defs.append('''<filter id="ripple" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.004 0.09" numOctaves="2" seed="4"/>
      <feDisplacementMap in="SourceGraphic" scale="9" xChannelSelector="R" yChannelSelector="G"/></filter>''')
    defs.append('''<filter id="softmist" x="-10%" y="-50%" width="120%" height="200%">
      <feTurbulence type="fractalNoise" baseFrequency="0.0035 0.018" numOctaves="3" seed="8" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 1  0 0 0 0 1  0 0 0 0 1  0 0 0 1.6 -0.62" result="a"/>
      <feComposite in="SourceGraphic" in2="a" operator="in"/></filter>''')
    defs.append('''<filter id="grain" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" stitchTiles="stitch" result="n"/>
      <feColorMatrix in="n" type="matrix" values=".33 .33 .33 0 0  .33 .33 .33 0 0  .33 .33 .33 0 0  0 0 0 0 1"/></filter>''')
    defs.append('''<filter id="cun" x="0" y="0" width="100%" height="100%">
      <feTurbulence type="fractalNoise" baseFrequency="0.045 0.0045" numOctaves="3" seed="12" result="n"/>
      <feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -3.2 1.9"/></filter>''')
    defs.append(f'''<pattern id="hazard" width="8" height="8" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
      <rect width="8" height="8" fill="{P['seal_fg'] if variant=='mist' else '#121614'}"/>
      <rect width="4" height="8" fill="{P['yellow']}"/></pattern>''')
    defs.append(f'''<filter id="stamp" x="-5%" y="-5%" width="110%" height="110%">
      <feTurbulence type="fractalNoise" baseFrequency=".55" numOctaves="2" seed="21" result="t"/>
      <feColorMatrix in="t" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -6 4.1" result="holes"/>
      <feComposite in="SourceGraphic" in2="holes" operator="in" result="worn"/>
      <feTurbulence type="fractalNoise" baseFrequency=".09" numOctaves="1" seed="3" result="w"/>
      <feDisplacementMap in="worn" in2="w" scale="1.1"/></filter>''')

    # ---------- sky + glow ----------
    body.append(f'<rect width="{W}" height="{H}" fill="url(#sky)"/>')
    body.append(f'<rect width="{W}" height="{H}" fill="url(#glow)"/>')
    # high cirrus mist
    body.append(f'<rect x="-40" y="250" width="{W+80}" height="190" fill="rgb({P["mist"]})" opacity=".10" filter="url(#softmist)"/>')

    # ---------- ranges + mist bands ----------
    for i, (yv, (base, *_)) in enumerate(zip(ridges, LAYERS)):
        d = path_from(x, yv)
        defs.append(f'<clipPath id="cl{i}"><path d="{d}"/></clipPath>')
        body.append(f'<path d="{d}" fill="url(#L{i})"/>')
        top = float(yv.min())
        defs.append(f'''<linearGradient id="cf{i}" gradientUnits="userSpaceOnUse" x1="0" y1="{top:.0f}" x2="0" y2="{base:.0f}">
          <stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#fff" stop-opacity=".55"/><stop offset="1" stop-color="#fff" stop-opacity=".08"/></linearGradient>
          <mask id="cm{i}" maskUnits="userSpaceOnUse" x="0" y="0" width="{W}" height="{H}"><rect width="{W}" height="{H}" fill="url(#cf{i})"/></mask>''')
        body.append(f'<g mask="url(#cm{i})"><rect width="{W}" height="{H}" filter="url(#cun)" clip-path="url(#cl{i})" opacity="{.24 + i*.06:.2f}"/></g>')
        rim = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, yv))
        body.append(f'<polyline points="{rim}" fill="none" stroke="rgb({P["mist"]})" stroke-opacity="{.30 - i*.05:.2f}" stroke-width="1"/>')
        band_top = base - (150 if i < 2 else 110)
        body.append(f'<rect x="0" y="{band_top}" width="{W}" height="{base - band_top + 14}" fill="url(#mistband)" opacity="{0.95 - i*0.18:.2f}"/>')
        if i in (0, 1, 2):
            body.append(f'<rect x="-40" y="{base-70}" width="{W+80}" height="120" fill="rgb({P["mist"]})" '
                        f'opacity="{0.16 - i*0.03:.2f}" filter="url(#softmist)"/>')

    # ---------- water ----------
    body.append(f'<rect x="0" y="{WATER_Y}" width="{W}" height="{H-WATER_Y}" fill="{P["water"]}"/>')
    refl = []
    for i in (2, 3):
        yv = ridges[i]
        ry = 2 * WATER_Y - yv
        pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(x, ry))
        refl.append(f'<path d="M0,{WATER_Y-2} L{pts} L{W},{WATER_Y-2} Z" fill="url(#L{i})"/>')
    body.append(f'<g mask="url(#reflmask)" filter="url(#ripple)" opacity=".75">{"".join(refl)}</g>')
    rng = np.random.default_rng(5)
    for _ in range(46):
        yy = WATER_Y + 6 + rng.gamma(2.0, 18.0)
        if yy > H - 4:
            continue
        xx = rng.uniform(-50, W)
        ln = rng.uniform(30, 260)
        body.append(f'<line x1="{xx:.0f}" y1="{yy:.1f}" x2="{xx+ln:.0f}" y2="{yy:.1f}" stroke="rgb({P["mist"]})" '
                    f'stroke-opacity="{rng.uniform(.05,.14):.2f}" stroke-width="1"/>')
    body.append(f'<rect x="0" y="{WATER_Y-10}" width="{W}" height="26" fill="rgb({P["mist"]})" opacity=".10" filter="url(#softmist)"/>')

    if layer == "land":
        body.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" style="mix-blend-mode:overlay" opacity="{P['grain_op']*2.4:.2f}"/>')
        return defs, body

    # ---------- survey grid / rulers ----------
    g = []
    for gx in range(48, W, 48):
        g.append(f'<line x1="{gx}" y1="30" x2="{gx}" y2="{H}"/>')
    for gy in range(30 + 48, H, 48):
        g.append(f'<line x1="0" y1="{gy}" x2="{W}" y2="{gy}"/>')
    body.append(f'<g stroke="{P["ink"]}" stroke-opacity="{P["grid_op"]}" stroke-width="1" shape-rendering="crispEdges">{"".join(g)}</g>')
    t = []
    for ty in range(40, H - 20, 8):
        ln = 9 if (ty - 40) % 64 == 0 else 4
        t.append(f'<line x1="0" y1="{ty+.5}" x2="{ln}" y2="{ty+.5}"/>')
    for tx in range(16, W - 16, 8):
        ln = 9 if (tx - 16) % 64 == 0 else 4
        t.append(f'<line x1="{tx+.5}" y1="{H}" x2="{tx+.5}" y2="{H-ln}"/>')
    body.append(f'<g stroke="{P["dim"]}" stroke-opacity=".75" stroke-width="1" shape-rendering="crispEdges">{"".join(t)}</g>')
    nums = []
    for tx in range(16 + 128, W - 64, 128):
        nums.append(f'<text x="{tx+3}" y="{H-12}">{tx-16:04d}</text>')
    body.append(f'<g font-family="Geist Mono" font-size="7" letter-spacing=".1em" fill="{P["dim"]}">{"".join(nums)}</g>')

    def reg(cx, cy, r=6):
        return (f'<g stroke="{P["muted"]}" stroke-width="1" shape-rendering="crispEdges">'
                f'<line x1="{cx-r}" y1="{cy+.5}" x2="{cx+r+1}" y2="{cy+.5}"/>'
                f'<line x1="{cx+.5}" y1="{cy-r}" x2="{cx+.5}" y2="{cy+r+1}"/></g>')
    for cx, cy in ((26, 52), (W - 27, 52), (26, H - 30), (W - 27, H - 30)):
        body.append(reg(cx, cy))

    if layer == "plate":
        body.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" style="mix-blend-mode:overlay" opacity="{P["grain_op"]*2.4:.2f}"/>')
        return defs, body

    # ---------- reticle locked on PK-03 ----------
    xi = np.argmin(np.abs(x - 960))
    win = slice(xi - 12, xi + 12)
    k = int(np.argmin(ridges[1][win])) + xi - 12
    cx, cy = float(x[k]), float(ridges[1][k])
    R, r2 = 214, 162
    ret = [f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="none" stroke="{P["ink"]}" stroke-opacity=".20"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{r2}" fill="none" stroke="{P["ink"]}" stroke-opacity=".12" stroke-dasharray="2 5"/>',
           f'<circle cx="{cx}" cy="{cy}" r="{R+14}" fill="none" stroke="{P["ink"]}" stroke-opacity=".07"/>']
    for deg in range(0, 360, 5):
        a = math.radians(deg - 90)
        ln = 12 if deg % 30 == 0 else 5
        x1, y1 = cx + R * math.cos(a), cy + R * math.sin(a)
        x2, y2 = cx + (R - ln) * math.cos(a), cy + (R - ln) * math.sin(a)
        op = .42 if deg % 30 == 0 else .2
        ret.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{P["ink"]}" stroke-opacity="{op}"/>')
        if deg % 30 == 0:
            tx, ty = cx + (R + 24) * math.cos(a), cy + (R + 24) * math.sin(a) + 3
            ret.append(f'<text x="{tx:.1f}" y="{ty:.1f}" text-anchor="middle" font-family="Geist Mono" font-size="8" '
                       f'letter-spacing=".08em" fill="{P["label"]}">{deg:03d}</text>')

    def arc(rad, a0, a1, color, width, op=1.0):
        p0 = (cx + rad * math.cos(math.radians(a0 - 90)), cy + rad * math.sin(math.radians(a0 - 90)))
        p1 = (cx + rad * math.cos(math.radians(a1 - 90)), cy + rad * math.sin(math.radians(a1 - 90)))
        large = 1 if (a1 - a0) % 360 > 180 else 0
        return (f'<path d="M{p0[0]:.1f},{p0[1]:.1f} A{rad},{rad} 0 {large} 1 {p1[0]:.1f},{p1[1]:.1f}" fill="none" '
                f'stroke="{color}" stroke-width="{width}" stroke-opacity="{op}"/>')
    ret.append(arc(R + 4, 24, 62, P["yellow"], 2))
    ret.append(arc(R + 4, 66, 70, P["yellow"], 2))
    ret.append(arc(r2, 200, 236, P["jade"], 1.5, .85))
    ja = math.radians(236 - 90)
    jx, jy = cx + r2 * math.cos(ja), cy + r2 * math.sin(ja)
    ret.append(f'<rect x="{jx-2:.1f}" y="{jy-2:.1f}" width="4" height="4" fill="{P["jade"]}"/>')
    ret.append(f'<text x="{jx+8:.1f}" y="{jy-6:.1f}" font-family="Geist Mono" font-size="8" letter-spacing=".12em" fill="{P["jade"]}">MIST SCAN · 0.62</text>')
    for (dx, dy) in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ret.append(f'<line x1="{cx+dx*18:.1f}" y1="{cy+dy*18:.1f}" x2="{cx+dx*(r2-10):.1f}" y2="{cy+dy*(r2-10):.1f}" '
                   f'stroke="{P["ink"]}" stroke-opacity=".16"/>')
    ret.append(f'<rect x="{cx-6:.1f}" y="{cy-6:.1f}" width="12" height="12" fill="none" stroke="{P["yellow"]}" stroke-width="1.2"/>')
    ret.append(f'<rect x="{cx-1.5:.1f}" y="{cy-1.5:.1f}" width="3" height="3" fill="{P["yellow"]}"/>')
    body.append(f'<g>{"".join(ret)}</g>')
    # readout attached to reticle
    rx, ry = cx + R * 0.74 + 18, cy - R * 0.74 - 6
    body.append(f'''<g font-family="Geist Mono" letter-spacing=".12em">
      <line x1="{cx+R*0.71:.1f}" y1="{cy-R*0.71:.1f}" x2="{rx-4:.1f}" y2="{ry+8:.1f}" stroke="{P['yellow']}" stroke-opacity=".8"/>
      <line x1="{rx-4:.1f}" y1="{ry+8:.1f}" x2="{rx+118:.1f}" y2="{ry+8:.1f}" stroke="{P['yellow']}" stroke-opacity=".8"/>
      <text x="{rx:.1f}" y="{ry+2:.1f}" font-size="9" fill="{P['yellow']}" font-weight="600">LOCK · PK-03</text>
      <text x="{rx:.1f}" y="{ry+22:.1f}" font-size="8" fill="{P['muted']}">AZ 214.6°  EL +12.3°</text>
      <text x="{rx:.1f}" y="{ry+33:.1f}" font-size="8" fill="{P['muted']}">DIST 3.20 KM · 1,204 M</text>
    </g>''')

    # survey markers on other peaks
    def marker(px_target, li, code, alt, up=46):
        xi = int(np.argmin(np.abs(x - px_target)))
        w = slice(max(xi - 10, 0), xi + 10)
        k = int(np.argmin(ridges[li][w])) + max(xi - 10, 0)
        mx, my = float(x[k]), float(ridges[li][k])
        return f'''<g font-family="Geist Mono" letter-spacing=".12em">
          <path d="M{mx-4:.1f},{my-9:.1f} L{mx+4:.1f},{my-9:.1f} L{mx:.1f},{my-3:.1f} Z" fill="{P['yellow']}"/>
          <line x1="{mx+.5:.1f}" y1="{my-11:.1f}" x2="{mx+.5:.1f}" y2="{my-up:.1f}" stroke="{P['ink']}" stroke-opacity=".35" stroke-dasharray="2 2"/>
          <text x="{mx+6:.1f}" y="{my-up+4:.1f}" font-size="8" fill="{P['ink']}" fill-opacity=".8">{code}</text>
          <text x="{mx+6:.1f}" y="{my-up+14:.1f}" font-size="7" fill="{P['label']}">{alt}</text></g>'''
    body.append(marker(722, 1, "PK-01", "1,148 M", 54))
    body.append(marker(1158, 2, "PK-05", "  986 M", 40))
    body.append(marker(604, 2, "PK-07", "  912 M", 36))

    # ---------- title block: 武陵 ----------
    halo = P["sky"][0]
    defs.append(f'<style>.halo{{paint-order:stroke;stroke:{halo};stroke-width:3px;stroke-linejoin:round}}</style>')
    tx0 = 54
    body.append(f'''<g>
      <text x="{tx0}" y="196" font-family="Noto Serif TC" font-weight="900" font-size="112" fill="{P['ink']}">武</text>
      <text x="{tx0}" y="316" font-family="Noto Serif TC" font-weight="900" font-size="112" fill="{P['ink']}">陵</text>
      <line x1="30" y1="262.5" x2="214" y2="262.5" stroke="{P['yellow']}" stroke-width="1"/>
      <rect x="214" y="260" width="5" height="5" fill="{P['yellow']}"/>
      <text x="170" y="256" font-family="Geist Mono" font-size="8" letter-spacing=".14em" fill="{P['yellow']}">WL-04</text>
      <line x1="186.5" y1="96" x2="186.5" y2="240" stroke="{P['dim']}" stroke-width="1"/>
    </g>''')
    vert = "以水為脈　以山為骨"
    vy = 104
    for ch in vert:
        if ch != "　":
            body.append(f'<text x="196" y="{vy}" font-family="Noto Serif TC" font-weight="500" font-size="11" fill="{P["muted"]}">{ch}</text>')
        vy += 15
    # seal 武陵工業 (白文: knocked-out glyphs, vermilion block)
    sx, sy, ss = 56, 338, 42
    gl = [("武", sx+ss*.73, sy+ss*.45), ("陵", sx+ss*.27, sy+ss*.45), ("工", sx+ss*.73, sy+ss*.88), ("業", sx+ss*.27, sy+ss*.88)]
    glyphs = "".join(f'<text x="{gx:.1f}" y="{gy:.1f}" text-anchor="middle" font-family="Noto Serif TC" font-weight="900" font-size="17" fill="#000">{c}</text>' for c, gx, gy in gl)
    defs.append(f'''<mask id="sealmask" maskUnits="userSpaceOnUse" x="{sx}" y="{sy}" width="{ss}" height="{ss}">
      <rect x="{sx}" y="{sy}" width="{ss}" height="{ss}" fill="#fff"/>
      <rect x="{sx+2.5}" y="{sy+2.5}" width="{ss-5}" height="{ss-5}" fill="none" stroke="#000" stroke-width="1.2"/>{glyphs}</mask>''')
    body.append(f'<g filter="url(#stamp)"><rect x="{sx}" y="{sy}" width="{ss}" height="{ss}" fill="{P["red"]}" mask="url(#sealmask)"/></g>')
    body.append(f'''<g font-family="Geist Mono" letter-spacing=".14em" class="halo">
      <text x="110" y="351" font-size="8" fill="{P['label']}">FIELD SECTOR</text>
      <text x="110" y="364" font-size="10" fill="{P['ink']}" font-weight="600">WULING / 武陵</text>
      <text x="110" y="377" font-size="8" fill="{P['label']}">TALOS-II · 29°20′N 110°33′E</text>
    </g>''')
    body.append(f'''<text class="halo" x="54" y="430" font-family="Barlow Condensed" font-weight="600" font-size="30" letter-spacing=".34em" fill="{P['ink']}">WULING</text>
      <text class="halo" x="56" y="446" font-family="Geist Mono" font-size="8" letter-spacing=".16em" fill="{P['muted']}">ENDFIELD INDUSTRIES — FIELD TERMINAL KJR-01</text>''')

    # ---------- hazard tag bottom-left ----------
    hx, hy = 40, H - 66
    body.append(f'''<g>
      <rect x="{hx}" y="{hy}" width="24" height="16" fill="url(#hazard)"/>
      <rect x="{hx+24}" y="{hy}" width="196" height="16" fill="{'#0E1211' if variant=='mist' else '#121614'}" fill-opacity=".86"/>
      <text x="{hx+32}" y="{hy+11}" font-family="Geist Mono" font-size="8.5" letter-spacing=".12em" fill="{P['yellow']}">AREA WL-04 · 清波寨 · AIC PLAN</text>
      <text x="{hx}" y="{hy+30}" font-family="Geist Mono" font-size="7.5" letter-spacing=".14em" fill="{P['label']}">CAUTION — HYDRAULIC TERRACE. KEEP CLEAR OF SPILLWAY.</text>
    </g>''')
    # ---------- emblem + barcode bottom-right ----------
    bx, by = W - 252, H - 70
    body.append(f'''<g>
      <path d="M{bx},{by} h17 l5,5 v17 h-22 Z" fill="{P['yellow']}"/>
      <g fill="#0E1211"><rect x="{bx+4}" y="{by+9}" width="3" height="8"/><rect x="{bx+9.5}" y="{by+4.5}" width="3" height="12.5"/>
         <rect x="{bx+15}" y="{by+9}" width="3" height="8"/><rect x="{bx+4}" y="{by+17}" width="14" height="1.6"/></g>
      <text x="{bx+30}" y="{by+8}" font-family="Geist Mono" font-size="8" letter-spacing=".14em" fill="{P['label']}">ENDFIELD INDUSTRIES</text>
      <text x="{bx+30}" y="{by+20}" font-family="Geist Mono" font-size="10" font-weight="600" letter-spacing=".12em" fill="{P['ink']}">KJR-01 · 鯨</text>
    </g>''')
    rngb = np.random.default_rng(77)
    bars, xx = [], bx + 158
    while xx < W - 44:
        w_ = rngb.choice([1, 1, 2, 3])
        bars.append(f'<rect x="{xx}" y="{by+2}" width="{w_}" height="16"/>')
        xx += w_ + rngb.choice([1, 2, 2, 3])
    body.append(f'<g fill="{P["ink"]}" fill-opacity=".55">{"".join(bars)}</g>')
    body.append(f'<text x="{bx+158}" y="{by+29}" font-family="Geist Mono" font-size="7" letter-spacing=".12em" fill="{P["label"]}">EF-WL-KJR01-2610</text>')

    # top-right coordinates (just under the bar)
    body.append(f'''<g font-family="Geist Mono" font-size="8" letter-spacing=".14em" fill="{P['label']}" text-anchor="end">
      <text x="{W-44}" y="56">SURVEY GRID 48 · DATUM WL-TALOS</text>
      <text x="{W-44}" y="68">MIST INDEX 0.62 · VIS 3.4 KM</text></g>''')

    body.append(f'<rect width="{W}" height="{H}" filter="url(#grain)" style="mix-blend-mode:overlay" opacity="{P["grain_op"]*2.4:.2f}"/>')
    return defs, body


def anchors():
    """Peak / reticle anchors in design space; the shell maps them with the same cover transform as the image
    (s = max(W/1366, H/768); ox = (W-1366*s)/2; oy = (H-768*s)/2)."""
    import json
    x = np.linspace(0, W, 684)
    ridges = [ridge(x, b, pk, sd, rough=r, canopy=c) for b, pk, r, c, sd in LAYERS]
    def peak(px_target, li, win=12):
        xi = int(np.argmin(np.abs(x - px_target)))
        w = slice(max(xi - win, 0), xi + win)
        k = int(np.argmin(ridges[li][w])) + max(xi - win, 0)
        return [round(float(x[k]), 1), round(float(ridges[li][k]), 1)]
    pk3 = peak(960, 1)
    return json.dumps({
        "design": {"w": W, "h": H}, "waterY": WATER_Y,
        "reticle": {"center": pk3, "r": 214, "rInner": 162, "rOuter": 228,
                    "yellowArcs": [[24, 62], [66, 70]], "jadeArc": [200, 236], "ticksEvery": 5, "labelsEvery": 30},
        "markers": {"PK-01": {"at": peak(722, 1, 10), "alt": "1,148 M", "lead": 54},
                    "PK-03": {"at": pk3, "alt": "1,204 M", "lock": True},
                    "PK-05": {"at": peak(1158, 2, 10), "alt": "986 M", "lead": 40},
                    "PK-07": {"at": peak(604, 2, 10), "alt": "912 M", "lead": 36}},
        "screenAnchored": "title block, seal, wordmark, rulers, registration marks, hazard tag, emblem/barcode, "
                          "top-right readout: positions as in the full layer (px from the nearest screen edge, scale 1)",
    }, ensure_ascii=False, indent=2)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--variant", default="mist", choices=PAL.keys())
    ap.add_argument("--layer", default="land", choices=["land"])   # full / plate retired (§0c)
    ap.add_argument("--anchors", action="store_true")
    a = ap.parse_args()
    if a.anchors:
        print(anchors())
        return
    defs, body = svg(a.variant, a.layer)
    print(f'''<!doctype html><html><head><meta charset="utf-8">
<link rel="stylesheet" href="fonts.css">
<style>html,body{{margin:0;height:100%;background:#000;overflow:hidden}} svg{{display:block;width:100vw;height:100vh}}</style>
</head><body>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" preserveAspectRatio="xMidYMid slice">
<defs>{"".join(defs)}</defs>
{chr(10).join(body)}
</svg></body></html>''')


if __name__ == "__main__":
    main()
