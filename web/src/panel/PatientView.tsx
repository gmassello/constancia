import { useCallback, useEffect, useState } from "react"

import FactChain from "./FactChain"
import Keyterms from "./Keyterms"
import LiveCall from "./LiveCall"
import WeeklyChart from "./WeeklyChart"
import { get, post, type CallRow, type Fact, type Patient, type Week } from "./api"
import { label, type Copy } from "./copy"

type Mode = "scripted" | "replay" | "live"

const day = (value: string) => value.slice(0, 10)

export default function PatientView({
  patient,
  live,
  copy: c,
}: {
  patient: Patient
  live: boolean
  copy: Copy
}) {
  const [facts, setFacts] = useState<Fact[]>([])
  const [weeks, setWeeks] = useState<Week[]>([])
  const [calls, setCalls] = useState<CallRow[]>([])
  const [terms, setTerms] = useState<string[]>([])
  const [callId, setCallId] = useState<string | null>(null)
  const [mode, setMode] = useState<Mode>("scripted")
  const [memory, setMemory] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    const [chain, weekly, rows] = await Promise.all([
      get<Fact[]>(`/patients/${patient.id}/chain`),
      get<Week[]>(`/patients/${patient.id}/weekly`),
      get<CallRow[]>(`/patients/${patient.id}/calls`),
    ])
    setFacts(chain)
    setWeeks(weekly)
    setCalls(rows)
    if (rows.length > 0) setTerms(await get<string[]>(`/calls/${rows[0].id}/keyterms`))
  }, [patient.id])

  useEffect(() => {
    setCallId(null)
    reload().catch((cause: Error) => setError(cause.message))
  }, [reload])

  const call = async () => {
    setError(null)
    try {
      const body = { patient_id: patient.id, memory, mode }
      const started = await post<{ call_id: string }>("/calls", body)
      setCallId(started.call_id)
    } catch (cause) {
      setError((cause as Error).message)
    }
  }

  return (
    <div className="patient">
      <header className="card">
        <div className="chart-head">
          <div>
            <h1>{patient.name}</h1>
            <div className="label">
              {label(c.program, patient.program_type)} · {c.followedSince(day(patient.started_at))}
            </div>
          </div>
          <div className="controls">
            <label>
              <input
                type="checkbox"
                checked={memory}
                onChange={(e) => setMemory(e.target.checked)}
              />
              {c.memory}
            </label>
            <select value={mode} onChange={(e) => setMode(e.target.value as Mode)}>
              <option value="scripted">{c.modeScripted}</option>
              <option value="replay">{c.modeReplay}</option>
              <option value="live" disabled={!live}>
                {live ? c.modeLive : c.modeLiveDisabled}
              </option>
            </select>
            <button className="btn btn-primary" onClick={call}>
              {c.callNow}
            </button>
          </div>
        </div>
        {error && <p className="error">{error}</p>}
      </header>

      {callId && <LiveCall callId={callId} onEnded={reload} copy={c} />}

      <section className="card">
        <WeeklyChart weeks={weeks} copy={c} />
      </section>

      <section className="card">
        <FactChain facts={facts} copy={c} />
      </section>

      <section className="card">
        <Keyterms terms={terms} copy={c} />
        <h3>{c.callsTitle}</h3>
        {calls.length === 0 && <p className="empty">{c.noCalls}</p>}
        {calls.map((row) => (
          <div className="call-row" key={row.id}>
            <div className="label">{c.callMeta(day(row.started_at), row.memory_enabled)}</div>
            {row.summary && <p>{row.summary}</p>}
          </div>
        ))}
      </section>
    </div>
  )
}
