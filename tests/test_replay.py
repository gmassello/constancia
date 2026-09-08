import pytest

from app import replay
from app.calls import Call
from app.memory import load_seed
from app.packs import get_pack

PATIENT = "8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5"


def build(memory: bool = True) -> Call:
    return Call(
        patient_id=PATIENT, patient_name="Ana", pack=get_pack("rehab"), memory=memory
    )


def types_of(call: Call) -> list[str]:
    return [event["type"] for event in call.trace]


async def test_scripted_week_2_supersedes_the_week_1_knee() -> None:
    store = load_seed()
    call = build()
    await replay.run_scripted(call, store, delay_s=0.0)

    assert types_of(call).count("fact_superseded") == 2
    current = await store.current_facts(PATIENT)
    assert [f["value"] for f in current if f["term"] == "rodilla derecha"] == [4]


async def test_scripted_picks_week_1_for_a_patient_with_no_history() -> None:
    call = build(memory=False)
    await replay.run_scripted(call, None, delay_s=0.0)

    assert "rodilla" not in call.transcript[1]["text"]
    assert call.transcript[3]["text"].startswith("La rodilla derecha me duele siete")


async def test_export_starts_at_zero_and_never_goes_back() -> None:
    call = build()
    await replay.run_scripted(call, load_seed(), delay_s=0.0)
    recording = replay.export(call)

    times = [event["t"] for event in recording["events"]]
    assert times[0] == 0.0
    assert times == sorted(times)
    assert recording["call"]["patient_name"] == "Ana"
    assert all("seq" not in event and "at" not in event for event in recording["events"])


async def test_recorded_replays_the_same_events_and_rebuilds_the_transcript() -> None:
    original = build()
    await replay.run_scripted(original, load_seed(), delay_s=0.0)

    played = build()
    await replay.run_recorded(played, "week2-on", speed=1000.0)

    assert types_of(played) == types_of(original)
    assert [t["text"] for t in played.transcript] == [t["text"] for t in original.transcript]
    assert [t["speaker"] for t in played.transcript] == [t["speaker"] for t in original.transcript]


async def test_an_unknown_recording_says_so() -> None:
    with pytest.raises(FileNotFoundError):
        replay.load_fixture("no-such-take")
