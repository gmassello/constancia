import asyncio
import json

import pytest

from app import main
from app.calls import Call
from app.packs import get_pack


def build() -> Call:
    return Call(patient_id="test", patient_name="Ana", pack=get_pack("rehab"))


def payloads(frames: list[str]) -> list[dict]:
    return [json.loads(f.split("data: ", 1)[1]) for f in frames if f.startswith("id: ")]


async def drain(gen, count: int) -> list[str]:
    return [await asyncio.wait_for(gen.__anext__(), 1.0) for _ in range(count)]


async def test_a_late_subscriber_gets_the_whole_buffer_in_order_then_live_events() -> None:
    call = build()
    for text in ("a", "b", "c"):
        call.emit("agent_turn", text=text)

    snapshot, queue = call.subscribe()
    gen = main.event_stream(call, snapshot, queue, 0)
    try:
        frames = await drain(gen, 4)
        assert frames[0] == "retry: 3000\n\n"
        assert [e["text"] for e in payloads(frames)] == ["a", "b", "c"]

        call.emit("agent_turn", text="d")
        assert payloads(await drain(gen, 1))[0]["text"] == "d"
    finally:
        await gen.aclose()


async def test_last_event_id_skips_what_the_client_already_saw() -> None:
    call = build()
    for text in ("a", "b", "c"):
        call.emit("agent_turn", text=text)

    snapshot, queue = call.subscribe()
    gen = main.event_stream(call, snapshot, queue, 2)
    try:
        assert [e["text"] for e in payloads(await drain(gen, 2))] == ["c"]
    finally:
        await gen.aclose()


async def test_silence_yields_a_keep_alive_comment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(main, "KEEPALIVE_S", 0.01)
    call = build()
    snapshot, queue = call.subscribe()
    gen = main.event_stream(call, snapshot, queue, 0)
    try:
        assert await drain(gen, 2) == ["retry: 3000\n\n", ": keep-alive\n\n"]
    finally:
        await gen.aclose()


async def test_closing_the_stream_unsubscribes() -> None:
    call = build()
    snapshot, queue = call.subscribe()
    gen = main.event_stream(call, snapshot, queue, 0)
    await drain(gen, 1)
    assert call.subscribers == [queue]

    await gen.aclose()
    assert call.subscribers == []


async def test_the_stream_ends_on_call_ended() -> None:
    call = build()
    snapshot, queue = call.subscribe()
    gen = main.event_stream(call, snapshot, queue, 0)
    await drain(gen, 1)

    call.emit("call_ended", escalated=False, answers={})
    assert payloads(await drain(gen, 1))[0]["type"] == "call_ended"
    with pytest.raises(StopAsyncIteration):
        await asyncio.wait_for(gen.__anext__(), 1.0)


async def test_a_buffer_that_already_ended_does_not_wait_for_more() -> None:
    call = build()
    call.emit("call_started", patient="Ana")
    call.emit("call_ended", escalated=False, answers={})

    snapshot, queue = call.subscribe()
    gen = main.event_stream(call, snapshot, queue, 0)
    frames = [frame async for frame in gen]

    assert [e["type"] for e in payloads(frames)] == ["call_started", "call_ended"]
    assert call.subscribers == []
