# Bundled fonts

Geist and Geist Mono are the static non-italic faces from
[Vercel Geist 1.7.2](https://github.com/vercel/geist-font/releases/tag/v1.7.2),
under `Geist-OFL.txt`. Barlow Condensed comes from
[Google Fonts](https://github.com/google/fonts/tree/main/ofl/barlowcondensed),
under `BarlowCondensed-OFL.txt`.

Material Symbols Sharp comes from Google's
[Material Design Icons variable font](https://github.com/google/material-design-icons/tree/master/variablefont),
under `MaterialSymbolsSharp-APACHE.txt`. This is a modified subset produced by
`tools/subset-icons`: only approved design icons remain, addressed by their
private-use codepoints in `tokens/icons.json`; the ligature tables are removed.
Keep the original family name for fontconfig discovery.

The source font binaries are fetched by `design/fetch-fonts.sh`. Rebuilding the
icon subset needs FontTools only on the development machine. Users install the
committed fonts and need no font build tools. CJK fonts are not bundled: stock
Omarchy provides `noto-fonts-cjk`. No system font preference is changed.
