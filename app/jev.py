import httpx

from app.config import settings_or_none

ENDPOINT = "https://ai-gateway.vercel.sh/v1/evaluate"
MODEL = "typesafe-ai/jev"
PROVIDER = "typesafe-ai"
KEY = "commits"
TIMEOUT_S = 2.0
INSTRUCTIONS = (
    "Is the patient promising to do something before the next call to look after their own body — "
    "their treatment, their recovery, or what their condition asks of them day to day? An ordinary "
    "action counts when it is done for their recovery: walking, resting, how they sit or lie, "
    "keeping something on, dry or raised. Following the professional's advice counts too; what "
    "matters is that the patient is the one committing. A plan with nothing to do with their "
    "body — work, errands, seeing people, entertainment — is not one, nor is asking the "
    "professional for "
    "something, nor a habit they already have."
)
CRITERIA = {
    "true": (
        "the patient commits to a concrete action for their own body — treatment, recovery, "
        "movement, rest, position, or protecting a wound — even when the action is an ordinary one"
    ),
    "false": (
        "anything else: a plan unrelated to their body such as work, errands, socialising or "
        "entertainment, a request the patient makes of the professional, a report of what they "
        "already did, or a habit they already have"
    ),
}
# ponytail: what crosses the boundary is one sentence a patient said about their own health, so the
# request pins the provider that may serve it and, when the plan allows, asks the gateway not to
# keep it. Zero Data Retention is a Pro tier: asking for it on a hobby plan is not ignored, it is a
# 403 on
# every call, so it is a knob that defaults off rather than a constant. Upgrade path, if this ever
# carries more than one quote at a time: a BYOK key, so the traffic never reaches Vercel's own
# account, and a line in the README saying which sentences leave the machine.


def payload(quote: str, zero_retention: bool = False) -> dict:
    gateway: dict = {"only": [PROVIDER]}
    if zero_retention:
        gateway["zeroDataRetention"] = True
    return {
        "model": MODEL,
        "state": quote,
        "questions": {
            KEY: {"type": "boolean", "instructions": INSTRUCTIONS, "criteria": CRITERIA},
        },
        "providerOptions": {"gateway": gateway},
    }


async def commits(quote: str, emit=None) -> float | None:
    # ponytail: any failure is a None and the deterministic vocabulary decides alone — no retry and
    # no backoff. This runs inside the extract phase rather than a background task, so a second
    # attempt is a second stall visible on the panel, and the answer it would rescue is one the
    # rules were already willing to drop. The reason is not swallowed, though: a silent `None` made
    # a 403 on every call look exactly like the vocabulary deciding, for as long as nobody ran
    # `make smoke-jev` by hand.
    settings = settings_or_none()
    if not settings or not settings.ai_gateway_api_key:
        return None
    headers = {"Authorization": f"Bearer {settings.ai_gateway_api_key}"}
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT_S) as client:
            response = await client.post(
                ENDPOINT, json=payload(quote, settings.jev_zero_retention), headers=headers
            )
            response.raise_for_status()
            probability = response.json()["answers"][KEY]["probability"]
    except (httpx.HTTPError, KeyError, TypeError, ValueError) as exc:
        if emit:
            emit("warning", phase="jev", error=repr(exc))
        return None
    if not isinstance(probability, int | float):
        return None
    return float(probability) if settings.jev_floor <= probability <= 1.0 else None
