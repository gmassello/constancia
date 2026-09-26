"""Fail when a number this repo publishes has drifted from the command that produces it.

    make check-numbers

Two facts are anchored. The test count is published in eighteen places — the README's
command block, five docs, the deck source and its build, the design preview, both halves
of the landing copy — and nothing inside pytest can guard it: a test that counted tests
would add one to the count, and `video/out/demo-coldopen.mp4` is a render that prints the
figure on screen and cannot be re-cut cheaply. The count of honest limits is published on
one deck slide, and its truth is the README's own list, which is the place that names them.

Markup is blanked before scanning, in place so line numbers survive: a tag becomes spaces,
which keeps a CSS `font-weight:600` from reading as a count, while the digits of a
`data-count` attribute stay where they were, because an animated counter is a published
figure like any other. A lone `0` is blanked too: it is the placeholder such a counter
starts at, and it otherwise hides the real number behind it.
"""

import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

TAG = re.compile(r"<[^>]*>", re.DOTALL)
DATA_COUNT = re.compile(r"data-count=\"(\d+)\"")
PLACEHOLDER = re.compile(r"(?<![\w.])0(?![\w.])")

LIMITS = re.compile(r"(?<![-:.\w])(\d{1,2})[^\d;]{0,80}?\blimits we say out loud\b")

COUNT = re.compile(
    r"(?<![-:.\w])(\d{3})[^\d;]{0,80}?\btests?\b(?![/\\_])"
    r"|\btests?\b(?![/\\_])[^\d;]{0,30}?(?<![-:.\w])(\d{3})\b"
    r"|(?<![-:.\w])(\d{3}) (?:passed|collected)\b"
)


def blanked(text):
    def blank_tag(match):
        tag = match.group(0)
        kept = ["\n" if c == "\n" else " " for c in tag]
        for attr in DATA_COUNT.finditer(tag):
            for i in range(*attr.span(1)):
                kept[i] = tag[i]
        return "".join(kept)

    return PLACEHOLDER.sub(" ", TAG.sub(blank_tag, text))


def limits():
    body = (ROOT / "README.md").read_text(encoding="utf-8").split("## Honest limits")[1]
    return len(re.findall(r"^- \*\*", body.split("\n## ")[0], re.M))


def collected():
    out = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", "--no-header"],
        cwd=ROOT, capture_output=True, text=True,
    ).stdout
    found = re.search(r"(\d+) tests? collected", out)
    if not found:
        sys.exit(f"could not read a collection count from pytest:\n{out[-800:]}")
    return int(found.group(1))


def tracked():
    out = subprocess.run(
        ["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True
    ).stdout.split()
    keep = (".md", ".ts", ".tsx", ".html", ".py", ".json")
    return [ROOT / f for f in out if f.endswith(keep) and f != "scripts/check_numbers.py"]


def published(pattern):
    for path in tracked():
        try:
            text = blanked(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, OSError):
            continue
        for hit in pattern.finditer(text):
            line = text[: hit.start()].count("\n") + 1
            yield path.relative_to(ROOT), line, int(next(g for g in hit.groups() if g))


FACTS = [
    ("the test count", "pytest --collect-only", collected, COUNT),
    ("the honest limits", "the README's own list", limits, LIMITS),
]


def main():
    failed = 0
    for label, source, produce, pattern in FACTS:
        truth = produce()
        copies = list(published(pattern))
        stale = [f"    {path}:{line} says {number}" for path, line, number in copies
                 if number != truth]
        print(f"  {label}: {source} gives {truth}; {len(copies)} published copies checked")
        if "--list" in sys.argv:
            for path, line, number in copies:
                print(f"      {path}:{line} {number}")
        if stale:
            print(f"  {len(stale)} disagree:")
            print("\n".join(stale))
            failed = 1
    return failed


if __name__ == "__main__":
    raise SystemExit(main())
