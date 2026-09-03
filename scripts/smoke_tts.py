import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import tts  # noqa: E402


async def main() -> None:
    total = 0
    first = b""
    line = "Hola, soy el asistente de seguimiento. ¿Cómo venís esta semana?"
    async for chunk in tts.stream(line):
        first = first or chunk
        total += len(chunk)
    if tts.looks_like_mp3(first):
        raise SystemExit("got MP3: output_format=ulaw_8000 did not apply")
    print(f"ok: {total} bytes of mu-law, about {total / 8000:.1f} s of audio")


if __name__ == "__main__":
    asyncio.run(main())
