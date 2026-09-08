import { useEffect, useRef } from "react"

import type { Event } from "./api"

const NEAR_BOTTOM = 40

type Line = { key: number; tone: string; label: string; text: string; detail?: string }

function describe(event: Event): Line | null {
  const key = event.seq
  switch (event.type) {
    case "recall":
      return {
        key,
        tone: "recall",
        label: "recall",
        text: `${event.facts} hechos en ficha`,
        detail: (event.keyterms as string[]).join(" · "),
      }
    case "fact_stored":
      return {
        key,
        tone: "stored",
        label: "hecho nuevo",
        text: String(event.fact),
        detail: `«${event.quote}» · turno ${event.turn_id}`,
      }
    case "fact_superseded":
      return {
        key,
        tone: "superseded",
        label: "hecho retirado",
        text: "el dato anterior queda tachado en la ficha",
      }
    case "fact_rejected":
      return {
        key,
        tone: "rejected",
        label: "descartado",
        text: String(event.fact),
        detail: String(event.reason),
      }
    case "guard_hit":
      return { key, tone: "alarm", label: "señal de alarma", text: String(event.rule) }
    case "memory_off":
      return { key, tone: "muted", label: "memoria off", text: `fase ${event.phase} salteada` }
    case "summary":
      return { key, tone: "summary", label: "resumen", text: String(event.text) }
    case "analysis_ready":
      return { key, tone: "stored", label: "análisis", text: `${event.entities} entidades` }
    case "facts_extracted":
      return { key, tone: "muted", label: "extracción", text: `${event.count} hechos del transcript` }
    case "call_started":
      return {
        key,
        tone: "muted",
        label: "llamada",
        text: `empezó · memoria ${event.memory ? "on" : "off"}`,
      }
    case "call_ended":
      return { key, tone: "muted", label: "llamada", text: "terminó" }
    case "agent_turn":
    case "patient_turn":
    case "llm":
    case "phase_started":
    case "phase_done":
      return null
    default:
      return { key, tone: "muted", label: event.type, text: "" }
  }
}

export default function ActivityRail({ events, since }: { events: Event[]; since: number }) {
  const box = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const node = box.current
    if (!node) return
    const atBottom = node.scrollHeight - node.scrollTop - node.clientHeight < NEAR_BOTTOM
    if (atBottom) node.scrollTop = node.scrollHeight
  }, [events])

  const lines = events.map(describe).filter((line): line is Line => line !== null)

  return (
    <div className="rail" ref={box}>
      <h3>Actividad</h3>
      {lines.length === 0 && <p className="empty">Esperando la llamada…</p>}
      {lines.map((line) => (
        <div className={`event ${line.tone}${line.key > since ? " fresh" : ""}`} key={line.key}>
          <span className="event-label">{line.label}</span>
          <span className="event-text">{line.text}</span>
          {line.detail && <span className="event-detail">{line.detail}</span>}
        </div>
      ))}
    </div>
  )
}
