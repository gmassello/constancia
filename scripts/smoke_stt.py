import asyncio
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.stt import StreamingSTT  # noqa: E402


async def main() -> None:
    stt = StreamingSTT(keyterms=["rodilla", "kinesiologia"])
    await stt.connect()
    print("connected")
    async for message in stt.messages():
        print(json.dumps(message)[:200])
        if message.get("type") == "Begin":
            break
    await stt.terminate()
    print("terminated")


if __name__ == "__main__":
    asyncio.run(main())
