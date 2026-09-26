"""Assemble docs/deck.html from the slide sources in docs/deck/.

    uv run python scripts/build_deck.py

Each docs/deck/<id>.html holds one <section> on a fixed 1920x1080 canvas with
every style inline, and docs/deck/deck.json gives the order and the typefaces.
This turns them into one self-contained page that GitHub Pages serves, so the
deck has a public URL that does not depend on the tool it was designed in.

Speaker notes are stripped, not hidden: an <aside> is what to say, not what to
publish, and CSS that only hides it still ships it to anyone reading the source.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC = ROOT / "docs" / "deck"
DEST = ROOT / "docs" / "deck.html"
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


if __name__ == "__main__":
    raise SystemExit(main())
