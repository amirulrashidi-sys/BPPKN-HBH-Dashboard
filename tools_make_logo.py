"""Rebuild assets/ and logo_data.py from a full-resolution crest.

Run this only when the artwork changes:

    python tools_make_logo.py path/to/new_crest.png

It writes a 192px crest and a 96px tab icon into assets/, then regenerates
logo_data.py so the embedded copy matches. Keeping the two in step matters,
because the app prefers the file on disk and falls back to the embedded copy;
if they drift, the crest changes depending on whether assets/ was deployed.

The source is quantised to 128 colours, which takes a multi-megabyte export
down to about 10 KB with no visible difference at the size it is displayed.
"""

from __future__ import annotations

import base64
import sys
import textwrap
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
SIZES = ((192, "mkn_logo.png", "LOGO_B64"), (96, "mkn_favicon.png", "FAVICON_B64"))
COLOURS = 128

HEADER = '''"""The MKN crest, embedded as base64 so it cannot go missing.

Binary files are easy to leave out of a git push or an upload through the
GitHub web interface, and a crest that silently fails to appear is hard to
diagnose. Keeping it here means the artwork travels with the source: if
`assets/mkn_logo.png` is present it wins, otherwise these constants are used.

Regenerate after changing the artwork:

    python tools_make_logo.py path/to/new_crest.png
"""

'''


def main(source: str) -> None:
    src = Image.open(source).convert("RGBA")
    ASSETS.mkdir(exist_ok=True)

    blocks = []
    for px, filename, const in SIZES:
        out = ASSETS / filename
        (src.resize((px, px), Image.LANCZOS)
            .quantize(colors=COLOURS, method=Image.FASTOCTREE, dither=Image.NONE)
            .save(out, "PNG", optimize=True))
        encoded = base64.b64encode(out.read_bytes()).decode("ascii")
        wrapped = "\n".join(textwrap.wrap(encoded, 96))
        blocks.append(f'{const} = """\\\n{wrapped}\n"""\n')
        print(f"{filename}: {px}px, {out.stat().st_size / 1024:.1f} KB")

    (HERE / "logo_data.py").write_text(HEADER + "\n".join(blocks))
    print("logo_data.py regenerated")

    import logo_data  # noqa: E402  - verify what we just wrote
    for _, filename, const in SIZES:
        assert base64.b64decode(getattr(logo_data, const)) == (ASSETS / filename).read_bytes()
    print("verified: embedded copies match the files exactly")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: python tools_make_logo.py path/to/crest.png")
    main(sys.argv[1])
