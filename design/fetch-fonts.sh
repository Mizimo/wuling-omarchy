#!/bin/sh
# fetch the mockup fonts into design/fonts (same families get installed system-wide on kujira)
set -e; cd "$(dirname "$0")"; mkdir -p fonts; cd fonts
G=https://github.com/google/fonts/raw/main/ofl
for f in Regular Medium SemiBold Bold; do curl -sLo BarlowCondensed-$f.ttf $G/barlowcondensed/BarlowCondensed-$f.ttf; done
curl -sLo NotoSansTC.ttf "$G/notosanstc/NotoSansTC%5Bwght%5D.ttf"
curl -sLo NotoSerifTC.ttf "$G/notoseriftc/NotoSerifTC%5Bwght%5D.ttf"
curl -sLo MaterialSymbolsSharp.ttf "https://github.com/google/material-design-icons/raw/master/variablefont/MaterialSymbolsSharp%5BFILL,GRAD,opsz,wght%5D.ttf"
curl -sLo geist.zip https://github.com/vercel/geist-font/releases/download/v1.7.2/geist-font-v1.7.2.zip
python3 -c "import zipfile,os;z=zipfile.ZipFile('geist.zip');[open(os.path.basename(n),'wb').write(z.read(n)) for n in z.namelist() if '/ttf/' in n and n.endswith('.ttf') and 'Italic' not in n]"
rm geist.zip
