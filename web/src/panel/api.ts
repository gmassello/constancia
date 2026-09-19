const base = import.meta.env.VITE_API ?? ""

export type Event = {
  seq: number
  at: string
  type: string
  [key: string]: unknown
}

export type Fact = {
  id: string
  fact: string
  term: string
  category: string
  value: number | null
  quote: string
  turn_id: number
  reported_at: string
  valid_until: string | null
  superseded_by: string | null
  superseded: Fact[]
}

export type Patient = {
  id: string
  name: string
  program_type: string
  phone_e164: string
  started_at: string
}

export type CallRow = {
  id: string
  started_at: string
  ended_at: string | null
  summary: string | null
  escalated: unknown
  memory_enabled: boolean
  transcript: Turn[] | null
}

export type Turn = { turn_id: number; speaker: string; text: string; at: string }

export type Week = { week: string; value: number; term: string }

export type Health = { status: string; calls: number; store: string; live: boolean }

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, init)
  if (!response.ok) throw new Error(`${init?.method ?? "GET"} ${path} → ${response.status}`)
  return (await response.json()) as T
}

export const get = <T,>(path: string) => json<T>(path)

export const post = <T,>(path: string, body: unknown) =>
  json<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

export function subscribe(callId: string, onEvent: (event: Event) => void): () => void {
  const source = new EventSource(`${base}/calls/${callId}/events`)
  source.onmessage = (message) => {
    const event = JSON.parse(message.data) as Event
    onEvent(event)
    if (event.type === "call_ended") source.close()
  }
  return () => source.close()
}
