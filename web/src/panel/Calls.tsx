import type { Analysis, CallRow } from "./api"
import { label, type Copy } from "./copy"

const PHONE =
  "M7.5 3.5H4.8c-.9 0-1.6.8-1.5 1.7.5 4.3 2.4 8.3 5.5 11.4s7.1 5 11.4 5.5c.9.1 1.7-.6 1.7-1.5v-2.7c0-.8-.6-1.4-1.3-1.5l-2.6-.4c-.6-.1-1.2.2-1.5.7l-.9 1.7a14 14 0 0 1-6.3-6.3l1.7-.9c.5-.3.8-.9.7-1.5l-.4-2.6c-.1-.7-.7-1.3-1.5-1.3Z"
const FLAG = "M5.5 21V4h12.5l-2.6 4.6L18 13.2H5.5"

function Understanding({ analysis, copy: c }: { analysis: Analysis; copy: Copy }) {
  const moods = Object.entries(analysis.sentiment)
  if (analysis.entities.length === 0 && moods.length === 0) return null
  return (
    <div className="call-understanding">
      <h4>{c.understandingTitle}</h4>
      <p className="call-understanding-lede">{c.understandingLede}</p>
      {analysis.entities.length > 0 && (
        <ul className="chips">
          {analysis.entities.map((entity) => (
            <li className="chip" key={`${entity.type}:${entity.text}`} title={entity.type}>
              {c.data(entity.text)}
            </li>
          ))}
        </ul>
      )}
      {moods.length > 0 && (
        <ul className="chips">
          {moods.map(([mood, count]) => (
            <li className={`chip mood-${mood.toLowerCase()}`} key={mood}>
              {label(c.mood, mood)} · {count}
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}

function Row({ row, copy: c }: { row: CallRow; copy: Copy }) {
  const escalated = Boolean(row.escalated)
  const turns = row.transcript ?? []
  return (
    <div className="call-row">
      <div className="call-head">
        <svg
          className={escalated ? "call-icon alarm" : "call-icon"}
          width="15"
          height="15"
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="1.6"
          strokeLinecap="round"
          strokeLinejoin="round"
          aria-hidden="true"
        >
          <path d={escalated ? FLAG : PHONE} />
        </svg>
        <span className="call-day">{c.day(row.started_at)}</span>
        <span className="pill">
          {row.memory_enabled ? c.callWithMemoryTag : c.callWithoutMemoryTag}
        </span>
        {escalated && <span className="pill pill-red_flag">{c.callEscalated}</span>}
      </div>
      {row.summary ? (
        <p className="call-summary">{c.data(row.summary)}</p>
      ) : (
        <p className="call-summary empty">{c.noSummary}</p>
      )}
      {turns.length > 0 && (
        <details className="call-turns">
          <summary>{c.showTranscript(turns.length)}</summary>
          <div className="transcript">
            {turns.map((turn) => (
              <div
                className={turn.speaker === "agent" ? "turn agent" : "turn patient"}
                key={turn.turn_id}
              >
                <span className="who">{turn.speaker === "agent" ? c.agent : c.patient}</span>
                <p>{c.data(turn.text)}</p>
              </div>
            ))}
          </div>
        </details>
      )}
      {row.analysis && <Understanding analysis={row.analysis} copy={c} />}
    </div>
  )
}

export default function Calls({ calls, copy: c }: { calls: CallRow[]; copy: Copy }) {
  return (
    <div>
      <h2>{c.callsTitle}</h2>
      <p className="card-lede">{c.callsLede}</p>
      {calls.length === 0 ? (
        <p className="empty">{c.noCalls}</p>
      ) : (
        calls.map((row) => <Row row={row} key={row.id} copy={c} />)
      )}
    </div>
  )
}
