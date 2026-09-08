import json
import math
import uuid
from datetime import UTC, datetime, timedelta
from pathlib import Path

from app import db
from app.config import get_settings
from app.packs import VerticalPack

MAX_KEYTERMS = 100
SEARCH_OVERFETCH = 40
SEARCH_LIMIT = 5
SEED_PATH = Path(__file__).resolve().parent.parent / "seed" / "patients.json"

FACT_COLUMNS = (
    "id, patient_id, call_id, fact, term, category, value, quote, turn_id, "
    "confidence, reported_at, valid_until, superseded_by"
)
PATIENT_COLUMNS = "id, professional_id, program_type, name, phone_e164, started_at"
CALL_COLUMNS = (
    "id, patient_id, started_at, ended_at, twilio_sid, recording_url, "
    "transcript, summary, escalated, memory_enabled, analysis"
)


def keyterms(facts: list[dict], pack: VerticalPack) -> list[str]:
    terms: list[str] = []
    for fact in facts:
        term = (fact.get("term") or "").strip()
        if term and fact["category"] in pack.keyterm_categories and term not in terms:
            terms.append(term)
    return terms[:MAX_KEYTERMS]


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


class MemoryStore:
    def __init__(self) -> None:
        from google import genai

        settings = get_settings()
        self.embedding_model = settings.gemini_embedding_model
        self.embedding_dims = settings.embedding_dims
        self.client = genai.Client(api_key=settings.gemini_api_key)

    async def embed(self, text: str) -> list[float]:
        from google.genai import types

        response = await self.client.aio.models.embed_content(
            model=self.embedding_model,
            contents=text,
            config=types.EmbedContentConfig(output_dimensionality=self.embedding_dims),
        )
        return normalize(list(response.embeddings[0].values))

    async def patient(self, patient_id: str) -> dict | None:
        return await db.fetch_one("select * from patients where id = %s", (patient_id,))

    async def current_facts(self, patient_id: str) -> list[dict]:
        return await db.fetch(
            f"select {FACT_COLUMNS} from patient_memories "
            "where patient_id = %s and valid_until is null and superseded_by is null "
            "order by reported_at desc, id",
            (patient_id,),
        )

    async def chain(self, patient_id: str) -> list[dict]:
        return await db.fetch(
            f"select {FACT_COLUMNS} from patient_memories where patient_id = %s "
            "order by reported_at desc, id",
            (patient_id,),
        )

    async def patients(self) -> list[dict]:
        return await db.fetch(f"select {PATIENT_COLUMNS} from patients order by name")

    async def calls(self, patient_id: str) -> list[dict]:
        return await db.fetch(
            f"select {CALL_COLUMNS} from calls where patient_id = %s order by started_at desc",
            (patient_id,),
        )

    async def call(self, call_id: str) -> dict | None:
        return await db.fetch_one(f"select {CALL_COLUMNS} from calls where id = %s", (call_id,))

    async def save_analysis(self, call_id: str, analysis: dict) -> None:
        await db.execute(
            "update calls set analysis = %s::jsonb where id = %s",
            (json.dumps(analysis, ensure_ascii=False), call_id),
        )

    async def search(
        self, professional_id: str, query: str, limit: int = SEARCH_LIMIT
    ) -> list[dict]:
        vector = db.to_vector_literal(await self.embed(query))
        rows = await db.fetch(
            "select m.id, m.patient_id, p.name as patient_name, m.fact, m.term, m.category, "
            "m.value, m.reported_at, m.valid_until, "
            "1 - (m.embedding <=> %s::vector) as similarity "
            "from patient_memories m join patients p on p.id = m.patient_id "
            "where p.professional_id = %s and m.embedding is not null "
            "order by m.embedding <=> %s::vector limit %s",
            (vector, professional_id, vector, SEARCH_OVERFETCH),
        )
        # ponytail: recency re-rank over the 40 nearest. Blend in similarity when a
        # professional has enough history that the newest 5 stop being the useful 5.
        return sorted(rows, key=lambda row: row["reported_at"], reverse=True)[:limit]

    async def save_call(self, call) -> None:
        await db.execute(
            "insert into calls (id, patient_id, started_at, ended_at, twilio_sid, recording_url, "
            "transcript, summary, escalated, memory_enabled) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s) "
            "on conflict (id) do update set ended_at = excluded.ended_at, "
            "recording_url = excluded.recording_url, transcript = excluded.transcript, "
            "summary = excluded.summary, escalated = excluded.escalated",
            (
                call.id,
                call.patient_id,
                call.started_at,
                call.ended_at,
                call.twilio_sid,
                call.recording_url,
                json.dumps(call.transcript, ensure_ascii=False),
                call.summary,
                json.dumps(call.escalated, ensure_ascii=False) if call.escalated else None,
                call.memory,
            ),
        )

    async def insert_fact(self, call, fact, embedding: list[float]) -> str:
        fact_id = str(uuid.uuid4())
        await db.execute(
            "insert into patient_memories (id, patient_id, call_id, fact, term, category, value, "
            "quote, turn_id, confidence, reported_at, embedding) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector)",
            (
                fact_id,
                call.patient_id,
                call.id,
                fact.fact,
                fact.term,
                fact.category,
                fact.value,
                fact.quote,
                fact.turn_id,
                fact.confidence,
                call.started_at,
                db.to_vector_literal(embedding),
            ),
        )
        return fact_id

    async def supersede(self, old_id: str, new_id: str) -> None:
        await db.execute(
            "update patient_memories set superseded_by = %s, valid_until = now() "
            "where id = %s and superseded_by is null",
            (new_id, old_id),
        )


class FakeStore:
    def __init__(
        self,
        patients: list[dict] | None = None,
        facts: list[dict] | None = None,
        calls: list[dict] | None = None,
    ) -> None:
        self._patients = {p["id"]: dict(p) for p in patients or []}
        self._calls = {c["id"]: dict(c) for c in calls or []}
        self.facts = [dict(f) for f in facts or []]
        self.saved_calls: list[str] = []

    async def embed(self, text: str) -> list[float]:
        return normalize([float(len(text)), 1.0])

    async def patients(self) -> list[dict]:
        return sorted(self._patients.values(), key=lambda row: row["name"])

    async def patient(self, patient_id: str) -> dict | None:
        return self._patients.get(patient_id)

    async def calls(self, patient_id: str) -> list[dict]:
        rows = [c for c in self._calls.values() if c["patient_id"] == patient_id]
        return sorted(rows, key=lambda row: row["started_at"], reverse=True)

    async def call(self, call_id: str) -> dict | None:
        return self._calls.get(call_id)

    async def save_analysis(self, call_id: str, analysis: dict) -> None:
        if call_id in self._calls:
            self._calls[call_id]["analysis"] = analysis

    async def search(
        self, professional_id: str, query: str, limit: int = SEARCH_LIMIT
    ) -> list[dict]:
        # ponytail: substring match. The fake store has no embeddings and never will;
        # pgvector similarity is exercised by the integration test against real Postgres.
        needle = query.strip().lower()
        rows = [
            fact
            for fact in self.facts
            if needle in fact["term"].lower() or needle in fact["fact"].lower()
        ]
        return sorted(rows, key=lambda row: row["reported_at"], reverse=True)[:limit]

    async def current_facts(self, patient_id: str) -> list[dict]:
        return [
            fact
            for fact in self.chain_sync(patient_id)
            if fact.get("valid_until") is None and fact.get("superseded_by") is None
        ]

    def chain_sync(self, patient_id: str) -> list[dict]:
        rows = [f for f in self.facts if f["patient_id"] == patient_id]
        return sorted(rows, key=lambda f: f["reported_at"], reverse=True)

    async def chain(self, patient_id: str) -> list[dict]:
        return self.chain_sync(patient_id)

    async def save_call(self, call) -> None:
        self.saved_calls.append(call.id)
        self._calls[call.id] = {
            "id": call.id,
            "patient_id": call.patient_id,
            "started_at": call.started_at,
            "ended_at": call.ended_at,
            "twilio_sid": call.twilio_sid,
            "recording_url": call.recording_url,
            "transcript": call.transcript,
            "summary": call.summary,
            "escalated": call.escalated,
            "memory_enabled": call.memory,
            "analysis": None,
        }

    async def insert_fact(self, call, fact, embedding: list[float]) -> str:
        fact_id = str(uuid.uuid4())
        self.facts.append(
            {
                "id": fact_id,
                "patient_id": call.patient_id,
                "call_id": call.id,
                "fact": fact.fact,
                "term": fact.term,
                "category": fact.category,
                "value": fact.value,
                "quote": fact.quote,
                "turn_id": fact.turn_id,
                "confidence": fact.confidence,
                "reported_at": call.started_at,
                "valid_until": None,
                "superseded_by": None,
            }
        )
        return fact_id

    async def supersede(self, old_id: str, new_id: str) -> None:
        for fact in self.facts:
            if fact["id"] == old_id and fact["superseded_by"] is None:
                fact["superseded_by"] = new_id
                fact["valid_until"] = _now()


def _now() -> str:
    return datetime.now(UTC).isoformat()


def days_ago(days: int) -> str:
    return (datetime.now(UTC) - timedelta(days=days)).isoformat()


def load_seed(path: Path = SEED_PATH) -> FakeStore:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    patients, facts, calls = [], [], []
    for patient in data["patients"]:
        patients.append(
            {
                "id": patient["id"],
                "professional_id": data["professional_id"],
                "name": patient["name"],
                "phone_e164": patient["phone_e164"],
                "program_type": patient["program_type"],
                "started_at": days_ago(patient["started_age_days"]),
            }
        )
        for call in patient["calls"]:
            reported_at = days_ago(call["age_days"])
            calls.append(
                {
                    "id": call["id"],
                    "patient_id": patient["id"],
                    "started_at": reported_at,
                    "ended_at": reported_at,
                    "twilio_sid": None,
                    "recording_url": None,
                    "transcript": call["transcript"],
                    "summary": call["summary"],
                    "escalated": None,
                    "memory_enabled": call["memory_enabled"],
                    "analysis": None,
                }
            )
            for fact in call["facts"]:
                key = f"{call['id']}/{fact['turn_id']}"
                facts.append(
                    {
                        **fact,
                        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                        "patient_id": patient["id"],
                        "call_id": call["id"],
                        "reported_at": reported_at,
                        "valid_until": None,
                        "superseded_by": None,
                    }
                )
    return FakeStore(patients, facts, calls)
