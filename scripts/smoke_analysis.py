import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import analysis  # noqa: E402


async def main(url: str) -> None:
    payload = await analysis.transcribe(url)
    print(json.dumps(analysis.summarize(payload), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: smoke_analysis.py <recording_url>")
    asyncio.run(main(sys.argv[1]))
