import { useEffect, useRef } from "react"

import type { Event } from "./api"
import { label, type Copy } from "./copy"

const NEAR_BOTTOM = 40

type Line = { key: number; tone: string; label: string; text: string; detail?: string }
type Shown = Line & { fresh: boolean }

function describe(event: Event, c: Copy): Line | null {
  const key = event.seq
  switch (event.type) {
    case "recall":
      return {
        key,
        tone: "recall",
        label: c.railRecall,
        text: c.railRecallText(Number(event.facts)),
        detail: (event.keyterms as string[]).map(c.data).join(" · "),
      }
    case "fact_stored":
      return {
        key,
        tone: "stored",
        label: c.railStored,
        text: c.data(String(event.fact)),
        detail: c.railQuote(c.data(String(event.quote)), Number(event.turn_id)),
      }
    case "fact_superseded":
      return { key, tone: "superseded", label: c.railSuperseded, text: c.railSupersededText }
    case "fact_rejected":
      return {
        key,
        tone: "rejected",
        label: c.railRejected,
        text: c.data(String(event.fact)),
        detail: label(c.reason, event.reason),
      }
    case "guard_hit":
      return { key, tone: "alarm", label: c.railAlarm, text: label(c.rule, event.rule) }
    case "memory_off":
      return {
        key,
        tone: "muted",
        label: c.railMemoryOff,
        text: c.railMemoryOffText(label(c.phase, event.phase)),
        detail: label(c.reason, event.reason),
      }
    case "summary":
      return { key, tone: "summary", label: c.railSummary, text: c.data(String(event.text)) }
    case "analysis_ready":
      return {
        key,
        tone: "stored",
        label: c.railAnalysis,
        text: c.railAnalysisText(Number(event.entities)),
      }
    case "facts_extracted":
      return {
        key,
        tone: "muted",
        label: c.railExtracted,
        text: c.railExtractedText(Number(event.count)),
      }
    case "call_started":
      return {
        key,
        tone: "muted",
        label: c.railCall,
        text: c.railCallStarted(Boolean(event.memory)),
      }
    case "call_ended":
      return { key, tone: "muted", label: c.railCall, text: c.railCallEnded }
    case "patient_hung_up":
      return { key, tone: "muted", label: c.railCall, text: c.railHungUp }
    case "phase_failed":
    case "warning":
    case "extract_failed":
    case "analysis_failed":
      return {
        key,
        tone: "rejected",
        label: c.railFailed,
        text: label(c.phase, event.phase ?? event.type.replace("_failed", "")),
        detail: String(event.error ?? ""),
      }
    case "facts_lost":
      return {
        key,
        tone: "rejected",
        label: c.railFailed,
        text: c.railFactsLost(Number(event.count)),
        detail: String(event.error ?? ""),
      }
    case "extract_retry":
    case "llm_retry":
      return { key, tone: "muted", label: c.railRetry, text: c.railRetryText(Number(event.attempt)) }
    case "recording_ready":
      return { key, tone: "muted", label: c.railRecording, text: c.railRecordingReady }
    case "agent_turn":
    case "patient_turn":
    case "llm":
    case "phase_started":
    case "phase_done":
    case "twilio_frame":
      return null
    default:
      return { key, tone: "muted", label: event.type.replace(/_/g, " "), text: "" }
  }
}

export default function ActivityRail({
  events,
  copy: c,
}: {
  events: Event[]
  copy: Copy
}) {
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const node = box.current
    if (!node) return
    const atBottom = node.scrollHeight - node.scrollTop - node.clientHeight < NEAR_BOTTOM
    if (atBottom) node.scrollTop = node.scrollHeight
  }, [events])

  // ponytail: the flash fires when a line mounts, and lines are keyed by `seq` on a list that only
  // grows, so each one animates exactly once. `replayed` is what the server puts on the frames it
  // sends from the buffer, which is the only way to tell a backlog line from one landing now.
  // Anything that makes these remount — reordering, a key that is not `seq` — flashes them again.
  const lines: Shown[] = events.flatMap((event) => {
    const line = describe(event, c)
    return line ? [{ ...line, fresh: !event.replayed }] : []
  })

  return (
    <div className="rail" ref={box}>
      <h3>{c.activity}</h3>
      {lines.length === 0 && <p className="empty">{c.waitingForCall}</p>}
      {lines.map((line) => (
        <div className={`event ${line.tone}${line.fresh ? " fresh" : ""}`} key={line.key}>
          <span className="event-label">{line.label}</span>
          <span className="event-text">{line.text}</span>
          {line.detail && <span className="event-detail">{line.detail}</span>}
        </div>
      ))}
    </div>
  )
}
