import json
import math
import uuid
from datetime import UTC, datetime, timedelta
from functools import cached_property
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
    "confidence, reported_at, valid_until, superseded_by, start_ms, end_ms"
)
PATIENT_COLUMNS = "id, professional_id, program_type, name, phone_e164, started_at"
QUESTION_COLUMNS = (
    "id, patient_id, call_id, question, quote, turn_id, status, answer, asked_at, answered_at"
)
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


def with_phrases(terms: list[str], calls: list[dict]) -> list[str]:
    # ponytail: the newest call that carries an analysis wins outright, rather than the union of
    # every call on file. The list is a prompt, not an archive: last week is what the patient is
    # about to talk about, and a phrase from two months ago costs a slot that a current one wants.
    merged = list(terms)
    seen = {term.casefold() for term in merged}
    heard: list[dict] = []
    for call in calls:
        heard = ((call.get("analysis") or {}).get("phrases")) or []
        if heard:
            break
    for phrase in heard:
        text = (phrase.get("text") or "").strip()
        if text and text.casefold() not in seen:
            merged.append(text)
            seen.add(text.casefold())
    return merged[:MAX_KEYTERMS]


def normalize(vector: list[float]) -> list[float]:
    norm = math.sqrt(sum(value * value for value in vector))
    return [value / norm for value in vector] if norm else vector


class MemoryStore:
    def __init__(self) -> None:
        settings = get_settings()
        self.embedding_model = settings.gemini_embedding_model
        self.embedding_dims = settings.embedding_dims

    # ponytail: built on first use, because everything else here is SQL. A store that opened a
    # network client in its constructor could not be exercised against a real database without a
    # real key, which is how three integration tests ended up unable to pass.
    @cached_property
    def client(self):
        from google import genai

        return genai.Client(api_key=get_settings().gemini_api_key)

    async def embed(self, text: str, emit=None) -> list[float]:
        from google.genai import types

        from app.llm import retrying

        response = await retrying(
            lambda: self.client.aio.models.embed_content(
                model=self.embedding_model,
                contents=text,
                config=types.EmbedContentConfig(output_dimensionality=self.embedding_dims),
            ),
            "gemini embeddings",
            emit,
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

    async def save_analysis(self, call_id: str, analysis: dict) -> int:
        return await db.execute(
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

    async def insert_fact(
        self, call, fact, embedding: list[float], supersedes: str | None = None
    ) -> str:
        # ponytail: one statement, so the insert and the retirement are one transaction. db.execute
        # opens a connection per statement and the pool commits on the way out, so splitting them
        # leaves the old fact and the new one both current the moment the second one fails — which
        # is the state app/AGENTS.md forbids. `where id = null` matches nothing, so no supersession
        # needs no branch.
        fact_id = str(uuid.uuid4())
        await db.execute(
            "with inserted as ("
            "insert into patient_memories (id, patient_id, call_id, fact, term, category, value, "
            "quote, turn_id, confidence, reported_at, embedding) "
            "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s::vector) returning id) "
            "update patient_memories set superseded_by = %s, valid_until = now() "
            "where id = %s and superseded_by is null",
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
                fact_id,
                supersedes,
            ),
        )
        return fact_id

    async def supersede(self, old_id: str, new_id: str) -> None:
        await db.execute(
            "update patient_memories set superseded_by = %s, valid_until = now() "
            "where id = %s and superseded_by is null",
            (new_id, old_id),
        )

    async def set_fact_span(self, fact_id: str, start_ms: int, end_ms: int) -> None:
        await db.execute(
            "update patient_memories set start_ms = %s, end_ms = %s where id = %s",
            (start_ms, end_ms, fact_id),
        )

    async def insert_question(self, call, question) -> str:
        question_id = str(uuid.uuid4())
        await db.execute(
            "insert into patient_questions "
            "(id, patient_id, call_id, question, quote, turn_id, asked_at) "
            "values (%s, %s, %s, %s, %s, %s, %s)",
            (
                question_id,
                call.patient_id,
                call.id,
                question.question,
                question.quote,
                question.turn_id,
                call.started_at,
            ),
        )
        return question_id

    async def questions(self, patient_id: str) -> list[dict]:
        return await db.fetch(
            f"select {QUESTION_COLUMNS} from patient_questions "
            "where patient_id = %s order by asked_at desc, id",
            (patient_id,),
        )

    async def set_question(
        self, question_id: str, was: str, now: str, answer: str | None = None
    ) -> bool:
        # ponytail: the `where status = %s` is the whole 409. Reading the row first and writing
        # after leaves a window where two clicks both see `open` and both answer it.
        rows = await db.execute(
            "update patient_questions set status = %s, answer = coalesce(%s, answer), "
            "answered_at = case when %s = 'answered' then now() else answered_at end "
            "where id = %s and status = %s",
            (now, answer, now, question_id, was),
        )
        return bool(rows)


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
        self.questions_rows: list[dict] = []

    async def embed(self, text: str, emit=None) -> list[float]:
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

    async def save_analysis(self, call_id: str, analysis: dict) -> int:
        if call_id not in self._calls:
            return 0
        self._calls[call_id]["analysis"] = analysis
        return 1

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
        previous = self._calls.get(call.id, {})
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
            "analysis": previous.get("analysis"),
        }

    async def insert_fact(
        self, call, fact, embedding: list[float], supersedes: str | None = None
    ) -> str:
        # ponytail: a counter, not a uuid, because the id is an opaque handle here and a fixture
        # recorded off this store has to come out byte-identical every run. The seeded rows carry
        # uuids, so the two can never collide. A real id is the database's job, in the branch above.
        fact_id = f"fact-{len(self.facts) + 1}"
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
                "start_ms": None,
                "end_ms": None,
            }
        )
        if supersedes:
            await self.supersede(supersedes, fact_id)
        return fact_id

    async def set_fact_span(self, fact_id: str, start_ms: int, end_ms: int) -> None:
        for fact in self.facts:
            if str(fact["id"]) == str(fact_id):
                fact["start_ms"], fact["end_ms"] = start_ms, end_ms

    async def insert_question(self, call, question) -> str:
        question_id = f"question-{len(self.questions_rows) + 1}"
        self.questions_rows.append(
            {
                "id": question_id,
                "patient_id": call.patient_id,
                "call_id": call.id,
                "question": question.question,
                "quote": question.quote,
                "turn_id": question.turn_id,
                "status": "open",
                "answer": None,
                "asked_at": call.started_at,
                "answered_at": None,
            }
        )
        return question_id

    async def questions(self, patient_id: str) -> list[dict]:
        rows = [r for r in self.questions_rows if r["patient_id"] == patient_id]
        return sorted(rows, key=lambda r: (str(r["asked_at"]), str(r["id"])), reverse=True)

    async def set_question(
        self, question_id: str, was: str, now: str, answer: str | None = None
    ) -> bool:
        for row in self.questions_rows:
            if str(row["id"]) == str(question_id) and row["status"] == was:
                row["status"] = now
                if answer is not None:
                    row["answer"] = answer
                if now == "answered":
                    row["answered_at"] = _now()
                return True
        return False

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
    patients, facts, calls, questions = [], [], [], []
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
            for asked in call.get("questions") or []:
                key = f"{call['id']}/{asked['turn_id']}/{asked['question']}"
                questions.append(
                    {
                        **asked,
                        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                        "patient_id": patient["id"],
                        "call_id": call["id"],
                        "asked_at": reported_at,
                        "answered_at": reported_at if asked["status"] != "open" else None,
                    }
                )
            for fact in call["facts"]:
                # ponytail: the term is in the key because one turn can carry more than one
                # fact — an adherence reading and the promise made in the same breath — and two
                # rows sharing an id makes the second supersede whatever the first replaced.
                key = f"{call['id']}/{fact['turn_id']}/{fact['term']}"
                facts.append(
                    {
                        **fact,
                        "id": str(uuid.uuid5(uuid.NAMESPACE_URL, key)),
                        "patient_id": patient["id"],
                        "call_id": call["id"],
                        "reported_at": reported_at,
                        "valid_until": None,
                        "superseded_by": None,
                        "start_ms": None,
                        "end_ms": None,
                    }
                )
    store = FakeStore(patients, facts, calls)
    store.questions_rows = questions
    return store
