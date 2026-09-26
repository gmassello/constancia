"""Assemble docs/deck.html from the slide sources in docs/deck/.

    uv run python scripts/build_deck.py
    uv run python scripts/build_deck.py --pdf

Each docs/deck/<id>.html holds one <section> on a fixed 1920x1080 canvas with
every style inline, and docs/deck/deck.json gives the order and the typefaces.
This turns them into one self-contained page that GitHub Pages serves, so the
deck has a public URL that does not depend on the tool it was designed in.

--pdf writes docs/deck.pdf as well, because lablab's submission form takes the
deck as an uploaded PDF and not as a link. It renders through headless Chrome,
which is not a dependency of this project: without it the HTML deck still
builds and only the PDF is skipped.

The PDF is light and the page is dark, because a deck that gets printed or read
in a bright room is not the one that gets projected. The slides carry their
colours inline and there is no light palette to switch to, so the light one is
derived: every colour keeps its hue and saturation and has its lightness
mirrored. That inverts the relationships rather than the pixels, so a chip that
reads as raised on the dark slide still reads as raised on the light one, which
a filter over the finished page would not do.

Two slides are skipped, and the test is their own root background rather than a
list of names: week-one-two is already white and privacy is already the accent
fill, so both were drawn to be read on light and mirroring them would make the
light deck the only one with a black slide in the middle.

Speaker notes are stripped, not hidden: an <aside> is what to say, not what to
publish, and CSS that only hides it still ships it to anyone reading the source.
"""

import colorsys
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "deck"
DEST = ROOT / "docs" / "deck.html"
PDF = ROOT / "docs" / "deck.pdf"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
NOTES = re.compile(r"\s*<aside>.*?</aside>", re.DOTALL)

PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="An agent that phones your patients every week
 and remembers what they said last time.">
{fonts}
<style>
  html, body {{ margin: 0; padding: 0; background: #0f1119; }}
  body {{ scroll-snap-type: y mandatory; overflow-x: hidden; }}
  /* --s is set from script: scale() takes a NUMBER, and calc(100vw / 1920) is a
     length, so the whole transform would be dropped and the slide would render
     at its full 1920px. */
  .slide {{
    scroll-snap-align: start;
    width: calc(1920px * var(--s, 1));
    height: calc(1080px * var(--s, 1));
    margin: 0 auto;
    overflow: hidden; position: relative;
  }}
  .slide > section {{
    position: absolute; top: 0; left: 0;
    width: 1920px; height: 1080px;
    box-sizing: border-box;
    transform-origin: top left;
    transform: scale(var(--s, 1));
  }}
  section h1, section h2, section h3, section p, section ul, section ol {{ margin: 0; }}
  section table {{ border-collapse: collapse; width: 100%; }}
  section th, section td {{ padding: 20px 24px; text-align: left; vertical-align: top; }}
</style>
</head>
<body>
{slides}<script>
  const fit = () => document.documentElement.style.setProperty(
    "--s", Math.min(innerWidth / 1920, innerHeight / 1080));
  addEventListener("resize", fit);
  fit();
</script>
</body>
</html>
"""


HEX = re.compile(r"#([0-9a-fA-F]{6})\b")


def lightness(colour):
    value = int(colour.lstrip("#"), 16)
    return colorsys.rgb_to_hls(
        ((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255
    )[1]


def already_light(slide):
    opening = re.search(r"<section[^>]*>", slide)
    root = opening and re.search(r"background:\s*(#[0-9a-fA-F]{6})", opening.group(0))
    return bool(root) and lightness(root.group(1)) > 0.5


def mirrored(match):
    value = int(match.group(1), 16)
    r, g, b = ((value >> 16) & 255) / 255, ((value >> 8) & 255) / 255, (value & 255) / 255
    hue, level, saturation = colorsys.rgb_to_hls(r, g, b)
    red, green, blue = colorsys.hls_to_rgb(hue, 1.0 - level, saturation)
    return f"#{round(red * 255):02x}{round(green * 255):02x}{round(blue * 255):02x}"


PRINT_PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>{title}</title>
{fonts}
<style>
  @page {{ size: 1920px 1080px; margin: 0; }}
  html, body {{ margin: 0; padding: 0; background: #0f1119; }}
  .slide {{ width: 1920px; height: 1080px; overflow: hidden; position: relative;
           break-after: page; }}
  .slide:last-child {{ break-after: auto; }}
  .slide > section {{ position: absolute; top: 0; left: 0;
                     width: 1920px; height: 1080px; box-sizing: border-box; }}
  section h1, section h2, section h3, section p, section ul, section ol {{ margin: 0; }}
  section table {{ border-collapse: collapse; width: 100%; }}
  section th, section td {{ padding: 20px 24px; text-align: left; vertical-align: top; }}
</style>
</head>
<body>
{slides}</body>
</html>
"""


def to_pdf(html):
    if not Path(CHROME).exists():
        print(f"  no Chrome at {CHROME}; skipping the PDF")
        return
    with tempfile.NamedTemporaryFile("w", suffix=".html", delete=False) as handle:
        handle.write(html)
        source = handle.name
    subprocess.run(
        [CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
         "--virtual-time-budget=10000", f"--print-to-pdf={PDF}", f"file://{source}"],
        check=True, capture_output=True,
    )
    Path(source).unlink()
    print(f"  -> {PDF.relative_to(ROOT)} ({PDF.stat().st_size // 1024} KB)")


def main():
    index = json.loads((SRC / "deck.json").read_text(encoding="utf-8"))
    fonts = "\n".join(
        f'<link rel="stylesheet" href="{face["href"]}">'
        for face in index.get("faces", {}).values()
        if "href" in face
    )
    slides = []
    for slide_id in index["order"]:
        if not re.fullmatch(r"[A-Za-z0-9_-]{1,64}", slide_id):
            raise SystemExit(f"refusing a slide id that is not a plain name: {slide_id!r}")
        section = (SRC / f"{slide_id}.html").read_text(encoding="utf-8").strip()
        section = NOTES.sub("", section).rstrip()
        slides.append(f'<div class="slide">\n{section}\n</div>\n')

    DEST.write_text(
        PAGE.format(title=index["title"], fonts=fonts, slides="".join(slides)),
        encoding="utf-8",
    )
    print(f"  {len(slides)} slides -> {DEST.relative_to(ROOT)}")

    if "--pdf" in sys.argv:
        light = "".join(
            slide if already_light(slide) else HEX.sub(mirrored, slide) for slide in slides
        )
        to_pdf(PRINT_PAGE.format(title=index["title"], fonts=fonts, slides=light))


if __name__ == "__main__":
    raise SystemExit(main())
