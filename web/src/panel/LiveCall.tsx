import { useEffect, useState } from "react"

import ActivityRail from "./ActivityRail"
import { subscribe, type Event } from "./api"
import { label, type Copy } from "./copy"

export default function LiveCall({
  callId,
  onEnded,
  copy: c,
}: {
  callId: string
  onEnded: () => void
  copy: Copy
}) {
  const [events, setEvents] = useState<Event[]>([])
  const [live, setLive] = useState(true)
  const [lost, setLost] = useState(false)

  useEffect(() => {
    setEvents([])
    setLive(true)
    setLost(false)
    const seen = new Set<number>()
    return subscribe(
      callId,
      (event) => {
        if (seen.has(event.seq)) return
        seen.add(event.seq)
        setEvents((previous) => [...previous, event])
        if (event.type === "call_ended") {
          setLive(false)
          onEnded()
        }
      },
      () => {
        setLive(false)
        setLost(true)
      },
    )
  }, [callId, onEnded])

  const turns = events.filter((e) => e.type === "agent_turn" || e.type === "patient_turn")
  const ended = events.find((e) => e.type === "call_ended" && e.reason)

  return (
    <section className="card live">
      <div className="chart-head">
        <h2>{c.liveTitle}</h2>
        <span className={live ? "dot live-dot" : "dot"}>
          {live ? c.liveNow : lost ? c.liveLost : c.liveEnded}
        </span>
      </div>
      <div className="live-body">
        <div className="transcript">
          {turns.length === 0 && (
            <p className={lost || ended ? "error" : "empty"}>
              {lost
                ? c.liveLostDetail
                : ended
                  ? `${ended.unanswered ? c.liveUnanswered : c.liveFailed} ${label(c.reason, ended.reason)}`
                  : c.liveDialling}
            </p>
          )}
          {turns.map((turn) => (
            <div className={`turn ${turn.type === "agent_turn" ? "agent" : "patient"}`} key={turn.seq}>
              <span className="who">{turn.type === "agent_turn" ? c.agent : c.patient}</span>
              <p>{c.data(String(turn.text))}</p>
              {turn.heard === false && <span className="turn-note">{c.turnUnheard}</span>}
            </div>
          ))}
        </div>
        <ActivityRail events={events} copy={c} />
      </div>
    </section>
  )
}
