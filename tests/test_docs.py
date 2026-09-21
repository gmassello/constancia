import re
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PUBLISHED = (
    "README.md",
    "docs/OPERATIONS.md",
    "docs/WORKING.md",
    "docs/SUBMISSION.md",
    "docs/LANDING.md",
    "docs/deck.md",
    "docs/API.md",
    "docs/BACKEND.md",
    "docs/FRONTEND.md",
    "docs/README.md",
    "web/src/landing/copy.ts",
)
SIZED = ("docs/BACKEND.md", "docs/FRONTEND.md")
SIZED_ROW = re.compile(r"^\|\s*\[?`([^`]+)`(?:\]\([^)]*\))?\s*\|\s*(\d+)\s*\|")
# ponytail: every pattern here is checked against the collected total, so a doc may publish that
# number and no other. A "142 passing" would need the suite's own result, and running the suite from
# inside it recurses. Prose says how many skip in words instead. The gate reads digits only, so a
# written in words is invisible to it, which is how six of them drifted, so the counts a doc writes
# out in prose are anchored by the table gates below instead.
COUNTS = (
    re.compile(r"(\d+) green"),
    re.compile(r"(\d+) passed"),
    re.compile(r"(\d+) passing"),
    re.compile(r"(\d+) collected"),
    re.compile(r"(\d+) tests"),
    re.compile(r'statTestsValue: "(\d+)"'),
)
RAMP = re.compile(r"color-neutral-[0-9]|color-accent-[0-9]")
STYLED = ("*.tsx", "*.ts", "*.css")
# ponytail: only API.md. Its anchors are written `symbol` — `file.py:NN`, one symbol per
# cell, so a shift is unambiguous. ARCHITECTURE.md anchors routes and prose, where a line
# names things the file does not define, so its references carry no line number at all.
ANCHORED = ("docs/API.md",)
ANCHOR = re.compile(r"`((?:app/)?[a-z_]+\.py):(\d+)(?:-\d+)?`")
NAME = re.compile(r"`([A-Za-z_][A-Za-z0-9_]*)`")
WINDOW = 4


def collected() -> int:
    run = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--collect-only", "tests"],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )
    found = re.search(r"(\d+) tests collected", run.stdout)
    assert found, run.stdout[-2000:]
    return int(found.group(1))


def published() -> list[tuple[str, int, str]]:
    out = []
    for name in PUBLISHED:
        for number, line in enumerate(ROOT.joinpath(name).read_text().splitlines(), start=1):
            for pattern in COUNTS:
                out += [(name, number, hit) for hit in pattern.findall(line)]
    return out


def defines(module: Path, line: int, symbol: str) -> bool:
    lines = module.read_text().splitlines()
    starts = (
        f"def {symbol}(",
        f"class {symbol}(",
        f"class {symbol}:",
        f"{symbol} = ",
    )
    return any(
        text.lstrip().removeprefix("async ").startswith(start)
        for text in lines[line - 1 : line - 1 + WINDOW]
        for start in starts
    )


def test_every_published_test_count_is_the_one_the_suite_reports() -> None:
    # The rule this enforces is in the hackathon CLAUDE.md: a figure in the README, in docs/, in the
    # video script or on the landing is derived from a reproducible run, never typed by hand. It was
    # violated in ten places at once, with three generations of numbers living side by side — and
    # two of them are rendered on the public landing.
    total = collected()
    stale = [
        f"{name}:{line} says {number}, the suite collects {total}"
        for name, line, number in published()
        if int(number) != total
    ]

    assert stale == []


@pytest.mark.parametrize("doc", ANCHORED)
def test_every_line_anchor_still_points_at_what_the_doc_says(doc: str) -> None:
    # Reference docs anchor handlers and constants by line number, and a line number rots on the
    # next commit that touches the file above it. docs/README.md calls a doc that disagrees with the
    # code a bug, so the anchors are a gate, not prose.
    wrong = []
    for number, line in enumerate(ROOT.joinpath(doc).read_text().splitlines(), start=1):
        anchors = ANCHOR.findall(line)
        if not anchors:
            continue
        names = NAME.findall(line)
        for path, at in anchors:
            module = ROOT / (path if path.startswith("app/") else f"app/{path}")
            if not any(defines(module, int(at), name) for name in names):
                wrong.append(f"{doc}:{number} anchors {path}:{at}, which defines none of {names}")

    assert wrong == []


def test_no_ramp_step_survives_outside_tokens_css() -> None:
    # The design-system gate, run instead of quoted. It lived in four markdown files as a shell
    # command nobody could execute from zsh — an unquoted `--include=*.tsx` is expanded by the
    # shell before grep sees it, so the gate aborted and the empty output read as a pass. A glob
    # that Python walks itself cannot be mangled by a shell that never runs.
    root = ROOT / "web" / "src"
    stray = [
        f"{path.relative_to(ROOT)}:{number}"
        for pattern in STYLED
        for path in root.rglob(pattern)
        if path.name != "tokens.css"
        for number, line in enumerate(path.read_text().splitlines(), start=1)
        if RAMP.search(line)
    ]

    assert stray == []


@pytest.mark.parametrize("doc", SIZED)
def test_every_line_count_in_the_module_tables_matches_the_file(doc: str) -> None:
    # The sibling of the anchor gate, on the other axis. BACKEND.md and FRONTEND.md publish a line
    # count per module, and "every published number comes out of a command" is a rule the repo set
    # itself — so the command runs here instead of being quoted in prose nobody re-runs.
    wrong = []
    for line in ROOT.joinpath(doc).read_text().splitlines():
        found = SIZED_ROW.match(line)
        if not found:
            continue
        path, published = found.group(1), int(found.group(2))
        real = len(ROOT.joinpath(path).read_text().splitlines())
        if real != published:
            wrong.append(f"{doc} publishes {published} lines for {path}, which has {real}")

    assert wrong == []


def test_the_target_table_lists_every_target_in_the_makefile() -> None:
    # WORKING.md publishes how many targets there are and then a row per target, and neither was
    # checked against the Makefile — `make take` and `make smoke-call` had been missing for long
    # enough that the count in the prose had drifted too.
    phony = ROOT.joinpath("Makefile").read_text().splitlines()[0]
    targets = set(phony.removeprefix(".PHONY:").split())
    working = ROOT.joinpath("docs/WORKING.md").read_text()
    table = set(re.findall(r"^\| `make ([a-z-]+)", working, re.M))

    assert table == targets
