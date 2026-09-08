import { useEffect, useRef, useState } from "react"

import ActivityRail from "./ActivityRail"
import { subscribe, type Event } from "./api"

export default function LiveCall({ callId, onEnded }: { callId: string; onEnded: () => void }) {
  const [events, setEvents] = useState<Event[]>([])
  const [live, setLive] = useState(true)
  const since = useRef(0)

  useEffect(() => {
    setEvents([])
    setLive(true)
    since.current = 0
    const seen = new Set<number>()
    return subscribe(callId, (event) => {
      if (seen.has(event.seq)) return
      seen.add(event.seq)
      setEvents((previous) => [...previous, event])
      if (event.type === "call_ended") {
        setLive(false)
        onEnded()
      }
    })
  }, [callId, onEnded])

  const turns = events.filter((e) => e.type === "agent_turn" || e.type === "patient_turn")

  return (
    <section className="card live">
      <div className="chart-head">
        <h2>Llamada en curso</h2>
        <span className={live ? "dot live-dot" : "dot"}>{live ? "en vivo" : "terminada"}</span>
      </div>
      <div className="live-body">
        <div className="transcript">
          {turns.length === 0 && <p className="empty">Marcando…</p>}
          {turns.map((turn) => (
            <div className={`turn ${turn.type === "agent_turn" ? "agent" : "patient"}`} key={turn.seq}>
              <span className="who">{turn.type === "agent_turn" ? "agente" : "paciente"}</span>
              <p>{String(turn.text)}</p>
            </div>
          ))}
        </div>
        <ActivityRail events={events} since={since.current} />
      </div>
    </section>
  )
}
