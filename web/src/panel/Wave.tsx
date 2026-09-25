import { useEffect, useRef, useState } from "react"

import { type Event } from "./api"
import { prefersReducedMotion } from "../prefs"

const BARS = 96
const TICK_MS = 90
const REST = 0.15
const STALE_MS = 4000

type Floor = "agent" | "patient" | "idle"

// ponytail: a turn event lands when that turn is over (`app/channel.py:274,287`), so the floor
// belongs to the other speaker until the next one lands. Strict alternation paints the model's
// thinking time as agent speech — about a second live, none on replay, where the gap is fixed.
// Bracket the agent side with `llm` instead once every spoken turn has one; the read-back and the
// goodbye do not.
function floorOf(events: Event[]): Floor {
  for (let index = events.length - 1; index >= 0; index -= 1) {
    const event = events[index]
    if (event.type === "call_ended" || event.type === "patient_hung_up") return "idle"
    if (event.type === "phase_done" && event.phase === "converse") return "idle"
    if (event.type === "agent_turn") return "patient"
    if (event.type === "patient_turn") return "agent"
  }
  return "idle"
}

// ponytail: synthesised noise gated by who holds the floor, not the call's audio level — the browser
// never has that audio, and the trace the SSE stream reads is a deque(maxlen=500) sized for the
// twenty semantic events a call emits, not for ten levels a second. Send a measured level once
// something other than the trace can carry it.
export default function Wave({ events }: { events: Event[] }) {
  const [levels, setLevels] = useState(() => Array<number>(BARS).fill(REST))
  const floor = floorOf(events)
  const held = useRef({ floor, since: Date.now() })

  useEffect(() => {
    held.current = { floor, since: Date.now() }
  }, [floor])

  useEffect(() => {
    const reduced = prefersReducedMotion()
    const timer = window.setInterval(() => {
      const active = held.current.floor !== "idle" && Date.now() - held.current.since < STALE_MS
      if (reduced && !active) return
      const target = active ? 0.35 + Math.random() * 0.65 : REST + Math.random() * 0.05
      setLevels((previous) => [...previous.slice(1), (previous[BARS - 1] + target) / 2])
    }, TICK_MS)
    return () => window.clearInterval(timer)
  }, [])

  return (
    <div className={`wave ${floor}`} aria-hidden="true">
      {levels.map((level, index) => (
        <span className="wave-bar" key={index} style={{ transform: `scaleY(${level})` }} />
      ))}
    </div>
  )
}
