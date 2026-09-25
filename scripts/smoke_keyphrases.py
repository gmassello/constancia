import asyncio
import json
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import analysis  # noqa: E402
from app.config import settings_or_none  # noqa: E402
from app.memory import keyterms, load_seed  # noqa: E402
from app.packs import get_pack  # noqa: E402

RECORD = Path(__file__).resolve().parent / "keyphrases-measured.json"
PACK = "rehab"


async def vocabulary() -> list[str]:
    store = load_seed()
    patient = (await store.patients())[0]
    facts = await store.current_facts(str(patient["id"]))
    return keyterms(facts, get_pack(PACK))


async def main(url: str) -> None:
    settings = settings_or_none()
    if not settings:
        print("the eight required variables have to be set: this one talks to AssemblyAI")
        return

    print("with auto_highlights ...")
    heard = await analysis.transcribe(url)
    print("without, on the same audio ...")
    control = await analysis.transcribe(url, {"auto_highlights": False})

    found = analysis.summarize(heard)
    plain = analysis.summarize(control)
    known = {term.casefold() for term in await vocabulary()}
    ranked = sorted(
        (heard.get("auto_highlights_result") or {}).get("results") or [],
        key=lambda item: item.get("rank") or 0.0,
        reverse=True,
    )
    fresh = [row["text"] for row in ranked if row["text"].casefold() not in known]

    print(f"\n{'rank':>5}  {'count':>5}  {'new':>3}  phrase")
    for row in ranked:
        new = "yes" if row["text"].casefold() not in known else "-"
        print(f"{row.get('rank') or 0.0:>5.2f}  {row['count']:>5}  {new:>3}  {row['text']}")

    kept = [row["text"] for row in found["phrases"]]
    summary = {
        "returned": len(ranked),
        "kept": len(kept),
        "new_against_vocabulary": len(fresh),
        "new_and_kept": [text for text in kept if text.casefold() not in known],
        "vocabulary": len(known),
        "entities_unchanged": found["entities"] == plain["entities"],
        "sentiment_unchanged": found["sentiment"] == plain["sentiment"],
        "control_returned_phrases": len(plain["phrases"]),
    }
    print(f"\n{json.dumps(summary, ensure_ascii=False, indent=2)}")

    RECORD.write_text(
        json.dumps(
            {
                "measured": date.today().isoformat(),
                "pack": PACK,
                "cap": analysis.MAX_PHRASES,
                "summary": summary,
                "phrases": [
                    {"text": row["text"], "rank": row.get("rank"), "count": row["count"]}
                    for row in ranked
                ],
                "kept": kept,
            },
            ensure_ascii=False,
            indent=2,
        )
        + "\n"
    )
    print(f"\nwritten to scripts/{RECORD.name}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_keyphrases.py <recording_url>")
    asyncio.run(main(sys.argv[1]))
