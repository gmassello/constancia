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

export type Analysis = {
  transcript_id: string | null
  entities: { text: string; type: string }[]
  sentiment: Record<string, number>
  negative: { text: string; confidence: number }[]
}

export type CallRow = {
  id: string
  started_at: string
  ended_at: string | null
  summary: string | null
  escalated: unknown
  memory_enabled: boolean
  transcript: Turn[] | null
  analysis: Analysis | null
}

export type Turn = { turn_id: number; speaker: string; text: string; at: string }

export type Point = { week: string; day: string; value: number }

export type Series = {
  category: string
  term: string
  scale_max: number | null
  lower_is_better: boolean
  points: Point[]
}

export type Health = { status: string; calls: number; store: string; live: boolean }

export class ApiError extends Error {
  constructor(
    readonly status: number,
    readonly detail: string | null,
  ) {
    super(detail ? `${status} ${detail}` : String(status))
  }
}

async function detail(response: Response): Promise<string | null> {
  try {
    const body = (await response.json()) as { detail?: unknown }
    return typeof body.detail === "string" ? body.detail : null
  } catch {
    return null
  }
}

async function json<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${base}${path}`, init)
  if (!response.ok) throw new ApiError(response.status, await detail(response))
  return (await response.json()) as T
}

export const get = <T,>(path: string) => json<T>(path)

export const post = <T,>(path: string, body: unknown) =>
  json<T>(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  })

export function subscribe(
  callId: string,
  onEvent: (event: Event) => void,
  onError?: () => void,
): () => void {
  const source = new EventSource(`${base}/calls/${callId}/events`)
  let ended = false
  source.onmessage = (message) => {
    const event = JSON.parse(message.data) as Event
    onEvent(event)
    if (event.type === "call_ended") {
      ended = true
      source.close()
    }
  }
  // ponytail: a 404 — any call_id from before a restart — reads exactly like a call that is still
  // dialling, because EventSource says nothing either way. The browser tells them apart: a response
  // that is not an event stream is fatal and leaves readyState CLOSED, while a dropped connection
  // leaves CONNECTING and retries every 3s, which is what `retry:` and `Last-Event-ID` are for. Only
  // the fatal one is reported. No first-event timeout on top: a live call emits nothing until the
  // WebSocket connects, which is after somebody picks up the phone, so a timeout would fire on camera.
  source.onerror = () => {
    if (ended || source.readyState !== EventSource.CLOSED) return
    onError?.()
  }
  return () => {
    ended = true
    source.close()
  }
}
