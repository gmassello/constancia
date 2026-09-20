import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import llm as llm_module  # noqa: E402
from app.calls import Call  # noqa: E402
from app.memory import load_seed  # noqa: E402
from app.packs import get_pack  # noqa: E402
from app.replay import run_scripted  # noqa: E402

PATIENT_ID = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"
TAKES = (("week1", False), ("week2", True), ("alarm", True))
BUDGETS = {"reply": llm_module.MAX_OUTPUT_TOKENS, "structured": llm_module.MAX_STRUCTURED_TOKENS}


def instrument(rows: list[dict]):
    original = llm_module.GeminiLLM._generate

    async def traced(self, contents, config, emit):
        response = await self.client.aio.models.generate_content(
            model=self.model, contents=contents, config=config
        )
        usage = response.usage_metadata
        kind = "structured" if config.response_mime_type else "reply"
        rows.append(
            {
                "kind": kind,
                "budget": config.max_output_tokens,
                "thinking": getattr(usage, "thoughts_token_count", 0) or 0,
                "output": usage.candidates_token_count or 0,
                "finish": str(response.candidates[0].finish_reason),
            }
        )
        return await original(self, contents, config, emit)

    llm_module.GeminiLLM._generate = traced


async def take(script: str, memory: bool) -> list[str]:
    rows: list[dict] = []
    instrument(rows)
    call = Call(
        patient_id=PATIENT_ID, patient_name="Ana", pack=get_pack("rehab"), memory=memory
    )
    await run_scripted(call, load_seed(), script, delay_s=0.0)

    problems = []
    for event in call.trace:
        if event["type"] == "phase_failed":
            problems.append(f"{script}: phase {event['phase']} failed: {event['error']}")
    for row in rows:
        headroom = row["budget"] - row["thinking"] - row["output"]
        print(
            f"  {script:10} {row['kind']:10} budget={row['budget']:5} "
            f"thinking={row['thinking']:5} output={row['output']:4} "
            f"headroom={headroom:5} {row['finish']}"
        )
        if "MAX_TOKENS" in row["finish"]:
            problems.append(
                f"{script}: {row['kind']} hit MAX_TOKENS at budget {row['budget']} "
                f"(thinking {row['thinking']}, output {row['output']})"
            )
    return problems


async def main() -> None:
    print(f"budgets: {BUDGETS}")
    problems = []
    for script, memory in TAKES:
        problems += await take(script, memory)
    if problems:
        print("\n".join(f"FAIL {p}" for p in problems))
        raise SystemExit(1)
    print("ok: every phase ran and no call was truncated")


if __name__ == "__main__":
    asyncio.run(main())
