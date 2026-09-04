import asyncio
import time
from collections.abc import Callable

from app.config import get_settings

MAX_ATTEMPTS = 4
BASE_DELAY_S = 1.0
RATE_LIMIT_FACTOR = 5.0
MAX_OUTPUT_TOKENS = 120
MAX_STRUCTURED_TOKENS = 2048
TEMPERATURE = 0.4


class LLMError(RuntimeError):
    pass


def _instruction_of(system: str) -> str:
    _, _, tail = system.rpartition("\n\n")
    _, marker, goal = tail.partition("Preguntá sobre: ")
    return (goal if marker else tail).strip()


class ScriptedLLM:
    def __init__(
        self, replies: list[str] | None = None, structured_replies: list[str] | None = None
    ) -> None:
        self.replies = list(replies or [])
        self.structured_replies = list(structured_replies or [])
        self.prompts: list[str] = []
        self.structured_prompts: list[str] = []

    async def reply(
        self, system: str, history: list[dict], emit: Callable[..., object] | None = None
    ) -> str:
        self.prompts.append(system)
        text = self.replies.pop(0) if self.replies else _instruction_of(system)
        if emit:
            emit("llm", tokens=0, elapsed_ms=0, scripted=True)
        return text

    async def structured(self, system: str, user: str, schema) -> str:
        self.structured_prompts.append(f"{system}\n\n{user}")
        return self.structured_replies.pop(0) if self.structured_replies else '{"facts": []}'


class GeminiLLM:
    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        self.model = settings.gemini_model
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def _generate(self, contents, config, emit: Callable[..., object] | None) -> str:
        from google.genai import errors

        started = time.monotonic()
        for attempt in range(MAX_ATTEMPTS):
            try:
                response = await self.client.aio.models.generate_content(
                    model=self.model, contents=contents, config=config
                )
            except errors.APIError as exc:
                code = getattr(exc, "code", None)
                retriable = code == 429 or (isinstance(code, int) and code >= 500)
                if not retriable or attempt == MAX_ATTEMPTS - 1:
                    raise LLMError(f"gemini failed after {attempt + 1} attempts: {code}") from exc
                delay = BASE_DELAY_S * (2**attempt)
                if code == 429:
                    delay *= RATE_LIMIT_FACTOR
                if emit:
                    emit("llm_retry", code=code, attempt=attempt + 1, delay_s=delay)
                await asyncio.sleep(delay)
                continue

            text = (response.text or "").strip()
            if emit:
                usage = getattr(response, "usage_metadata", None)
                emit(
                    "llm",
                    tokens=getattr(usage, "total_token_count", None),
                    elapsed_ms=int((time.monotonic() - started) * 1000),
                )
            if not text:
                raise LLMError("gemini returned an empty reply")
            return text

        raise LLMError("unreachable")

    async def reply(
        self, system: str, history: list[dict], emit: Callable[..., object] | None = None
    ) -> str:
        from google.genai import types

        contents = [
            types.Content(role=turn["role"], parts=[types.Part(text=turn["text"])])
            for turn in history
        ] or [types.Content(role="user", parts=[types.Part(text="(inicio de la llamada)")])]
        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_OUTPUT_TOKENS,
            temperature=TEMPERATURE,
        )
        return await self._generate(contents, config, emit)

    async def structured(self, system: str, user: str, schema) -> str:
        from google.genai import types

        config = types.GenerateContentConfig(
            system_instruction=system,
            max_output_tokens=MAX_STRUCTURED_TOKENS,
            temperature=0.0,
            response_mime_type="application/json",
            response_schema=schema,
        )
        contents = [types.Content(role="user", parts=[types.Part(text=user)])]
        return await self._generate(contents, config, None)
