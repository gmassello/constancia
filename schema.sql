create extension if not exists vector;

create table if not exists patients (
  id uuid primary key default gen_random_uuid(),
  professional_id uuid not null,
  program_type text not null,
  name text not null,
  phone_e164 text not null,
  started_at timestamptz not null default now()
);

create table if not exists calls (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references patients(id),
  started_at timestamptz not null,
  ended_at timestamptz,
  twilio_sid text,
  recording_url text,
  transcript jsonb,
  summary text,
  escalated jsonb,
  memory_enabled boolean not null default true
);

create table if not exists patient_memories (
  id uuid primary key default gen_random_uuid(),
  patient_id uuid not null references patients(id),
  call_id uuid not null references calls(id),
  fact text not null,
  term text not null,
  category text not null,
  value numeric,
  quote text not null,
  turn_id int not null,
  confidence numeric(3,2),
  reported_at timestamptz not null,
  valid_until timestamptz,
  superseded_by uuid references patient_memories(id),
  embedding vector(1536)
);

create index if not exists patient_memories_patient_reported_at
  on patient_memories (patient_id, reported_at);
-- ponytail: no vector index. Exact search is fine below ~10k rows; add HNSW when it isn't.
