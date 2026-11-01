#!/usr/bin/env python3
"""WULING's backgrounds: a contour map, one survey line, the Endfield Industries mark and its yellow band.

usage: wallpaper.py <line|thin|band> <mist|paper> > src/page.html     (design/render.sh bg bakes them at 3840x2160)

  line  contours and a single survey line, the mark top right: the default
  thin  the mark in the middle on a thin band, contours all round
  band  the mark in the middle on the full band, contours below: the composition of the official banner, and the hud preset's default

Design space is 1366x768. Omarchy only fills a screen by cropping, so anything that must stay readable keeps inside what every common
shape shows: x 107-1259 (3:2 crops the sides), y 112-670 (21:9 crops top and bottom, and the bar covers some).
The same seed always gives the same map. Needs numpy and contourpy.
"""
import argparse
import pathlib
import re

import numpy as np
from contourpy import LineType, contour_generator

W, H = 1366, 768
STEP, PAD = 2.0, 60  # grid spacing in design px; margin so the noise's wrap-around stays off screen
MARK = (pathlib.Path(__file__).parent.parent / "assets" / "ef-mark.svg").read_text()
YELLOW = "#FEF700"

PAL = {
    "mist": dict(ground="#0E1211", line="#E6EBE5", ink="#E6EBE5", label="#6F827D", mark="#F4F5EF", survey=YELLOW, station="#0E1211",
                 minor=.15, major=.34, band_minor=.11, band_major=.26),
    "paper": dict(ground="#F4F5EF", line="#121614", ink="#121614", label="#5C6A66", mark="#121614", survey="#121614", station="#121614",
                  minor=.16, major=.36, band_minor=.16, band_major=.38),
}


def noise(rng, shape, sigma):
    """Gaussian-smoothed white noise, unit variance."""
    ky, kx = np.fft.fftfreq(shape[0]), np.fft.rfftfreq(shape[1])
    gauss = np.exp(-2 * (np.pi * sigma) ** 2 * (kx[None, :] ** 2 + ky[:, None] ** 2))
    out = np.fft.irfft2(np.fft.rfft2(rng.standard_normal(shape)) * gauss, s=shape)
    return out / out.std()


def bilinear(z, x, y):
    x, y = np.clip(x, 0, z.shape[1] - 1.001), np.clip(y, 0, z.shape[0] - 1.001)
    i, j = x.astype(int), y.astype(int)
    a, b = x - i, y - j
    return z[j, i] * (1 - a) * (1 - b) + z[j, i + 1] * a * (1 - b) + z[j + 1, i] * (1 - a) * b + z[j + 1, i + 1] * a * b


def terrain(seed, big, mid, w_mid, warp):
    """Broad smooth ground, gently warped so the lines flow instead of forming blobs."""
    rng = np.random.default_rng(seed)
    shape = (int(H / STEP) + PAD * 2, int(W / STEP) + PAD * 2)
    z = noise(rng, shape, big / STEP) + w_mid * noise(rng, shape, mid / STEP) + .05 * noise(rng, shape, 20 / STEP)
    wx, wy = noise(rng, shape, 90 / STEP) * warp / STEP, noise(rng, shape, 90 / STEP) * warp / STEP
    jj, ii = np.mgrid[0:shape[0], 0:shape[1]]
    xs, ys = (np.arange(shape[1]) - PAD) * STEP, (np.arange(shape[0]) - PAD) * STEP
    return xs, ys, bilinear(z, ii + wx, jj + wy)


def contours(xs, ys, z, spacing):
    gen = contour_generator(x=xs, y=ys, z=z, line_type=LineType.Separate)
    levels = np.arange(z.min() + spacing / 2, z.max(), spacing)
    return [[line for line in gen.lines(level) if len(line) > 6] for level in levels]


def path(lines):
    return "".join("M" + "L".join(f"{x:.1f} {y:.1f}" for x, y in line) for line in lines)


def contour_group(levels, stroke, minor, major):
    """Every fifth line is an index contour, as on a survey map."""
    thin = "".join(path(ls) for i, ls in enumerate(levels) if i % 5)
    index = "".join(path(ls) for i, ls in enumerate(levels) if not i % 5)
    return f'<g fill="none" stroke="{stroke}"><path d="{thin}" stroke-width=".5" stroke-opacity="{minor}"/><path d="{index}" stroke-width=".8" stroke-opacity="{major}"/></g>'


def runs_on_screen(line):
    inside = (line[:, 0] >= -20) & (line[:, 0] <= W + 20) & (line[:, 1] >= -20) & (line[:, 1] <= H + 20)
    runs, start = [], None
    for i, v in enumerate(inside):
        if v and start is None:
            start = i
        if not v and start is not None:
            runs.append(line[start:i])
            start = None
    if start is not None:
        runs.append(line[start:])
    return [r for r in runs if len(r) > 30]


def survey_line(levels):
    """The straightest contour that crosses the whole screen through its middle."""
    best, score = None, -1
    for run in (r for ls in levels for line in ls for r in runs_on_screen(line)):
        span = run[:, 0].max() - run[:, 0].min()
        if span < W * .86 or not 260 < run[:, 1].mean() < 560 or run[:, 1].max() > 690 or run[:, 1].min() < 70:
            continue
        s = span * span / np.sum(np.hypot(*np.diff(run, axis=0).T))
        if s > score:
            best, score = run, s
    return best if best[0, 0] < best[-1, 0] else best[::-1]


def band(ground, cy, half, gap, r_min, first, grow, cx=W / 2):
    """The yellow band, cut by concentric slits around the centre: bars grow outward, as on the official banner."""
    slits, r, bar = "", r_min, first
    while r < 900:
        slits += f'<circle cx="{cx}" cy="{cy}" r="{r:.1f}" fill="none" stroke="{ground}" stroke-width="{gap}"/>'
        r += bar + gap
        bar *= grow
    return (f'<clipPath id="band"><rect x="0" y="{cy - half}" width="{W}" height="{2 * half}"/></clipPath><g clip-path="url(#band)">'
            f'<rect width="{W}" height="{H}" fill="{YELLOW}"/><circle cx="{cx}" cy="{cy}" r="{r_min}" fill="{ground}"/>{slits}</g>')


def mark(x, y, width, color):
    vb = re.search(r'viewBox="([^"]+)"', MARK).group(1).split()
    height = width * float(vb[3]) / float(vb[2])
    svg = MARK.replace("<svg ", '<svg style="position:static;display:block;width:100%;height:100%" ', 1)
    return f'<div class="a" style="left:{x}px;top:{y}px;width:{width}px;height:{height:.1f}px;color:{color}">{svg}</div>'


def line_page(p):
    levels = contours(*terrain(53, big=150, mid=60, w_mid=.42, warp=60), .07)
    survey = survey_line(levels)
    seg = np.hypot(*np.diff(survey, axis=0).T)
    along = np.concatenate([[0], np.cumsum(seg)])
    stations = ""
    for at, code, alt in [(.3, "PK-01", "1,148 M"), (.56, "PK-03", "1,204 M"), (.8, "PK-05", "986 M")]:
        x, y = np.interp(along[-1] * at, along, survey[:, 0]), np.interp(along[-1] * at, along, survey[:, 1])
        stations += (f'<rect x="{x - 3.5:.1f}" y="{y - 3.5:.1f}" width="7" height="7" fill="{YELLOW}" stroke="{p["station"]}"/>'
                     f'<path d="M{x:.1f} {y - 5:.1f}V{y - 24:.1f}" stroke="{p["ink"]}" stroke-opacity=".5" stroke-dasharray="2 2"/>'
                     f'<text x="{x + 6:.1f}" y="{y - 41:.1f}" class="t" font-weight="600" fill="{p["ink"]}">{code}</text>'
                     f'<text x="{x + 6:.1f}" y="{y - 30:.1f}" class="t" fill="{p["label"]}">{alt}</text>')
    g, mx, my = p["ground"], W - 112 - 84, 112 + 76
    clear = (f'<radialGradient id="c" gradientUnits="userSpaceOnUse" cx="{mx}" cy="{my}" r="165"><stop offset=".6" stop-color="{g}"/><stop offset="1" stop-color="{g}" stop-opacity="0"/></radialGradient>'
             f'<rect width="{W}" height="{H}" fill="url(#c)"/>')
    art = contour_group(levels, p["line"], p["minor"], p["major"]) + clear + f'<path d="{path([survey])}" fill="none" stroke="{p["survey"]}" stroke-width="1.5"/>' + stations
    return art, mark(W - 112 - 168, 112, 168, p["mark"]), False


def thin_page(p):
    levels = contours(*terrain(11, big=120, mid=46, w_mid=.34, warp=46), .085)
    g = p["ground"]
    clear = (f'<radialGradient id="c" gradientUnits="userSpaceOnUse" cx="{W / 2}" cy="384" r="330"><stop offset=".62" stop-color="{g}"/><stop offset="1" stop-color="{g}" stop-opacity="0"/></radialGradient>'
             f'<rect width="{W}" height="{H}" fill="url(#c)"/>')
    art = contour_group(levels, p["line"], p["minor"], p["major"]) + clear + band(g, 384, 26, 2.6, 206, 5.0, 1.15)
    return art, mark(W / 2 - 186, 384 - 163, 372, p["mark"]), True


def band_page(p):
    levels = contours(*terrain(11, big=120, mid=46, w_mid=.34, warp=46), .085)
    g = p["ground"]
    fade = (f'<linearGradient id="f" x1="0" y1="0" x2="0" y2="1"><stop offset=".42" stop-color="{g}"/><stop offset=".78" stop-color="{g}" stop-opacity="0"/></linearGradient>'
            f'<rect width="{W}" height="{H}" fill="url(#f)"/>')
    art = contour_group(levels, p["line"], p["band_minor"], p["band_major"]) + fade + band(g, 384, 84, 3.2, 212, 6.0, 1.17)
    return art, mark(W / 2 - 186, 384 - 163, 372, p["mark"]), True


def page(name, theme):
    p = PAL[theme]
    art, mark_html, right_note = {"line": line_page, "thin": thin_page, "band": band_page}[name](p)
    notes = '<div class="a m" style="left:112px;top:644px">WULING · TALOS-II\n武陵 · 塔衛二</div>'
    if right_note:
        notes += '<div class="a m" style="right:112px;top:644px;text-align:right">FIELD TERMINAL\n終端</div>'
    return f'''<!doctype html><html><head><meta charset="utf-8"><link rel="stylesheet" href="fonts.css"><style>
html, body {{ margin: 0; width: {W}px; height: {H}px; overflow: hidden; background: {p["ground"]}; }}
svg.art {{ position: absolute; left: 0; top: 0; }} .a {{ position: absolute; }}
.m {{ font: 500 8px/12px "Geist Mono", "Noto Sans TC", monospace; letter-spacing: .16em; color: {p["label"]}; white-space: pre; }}
.t {{ font: 500 8px "Geist Mono", monospace; letter-spacing: 1.2px; }}
</style></head><body><svg class="art" width="{W}" height="{H}" viewBox="0 0 {W} {H}">{art}</svg>{mark_html}{notes}</body></html>'''


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("name", choices=["line", "thin", "band"])
    ap.add_argument("theme", choices=list(PAL))
    a = ap.parse_args()
    print(page(a.name, a.theme))
