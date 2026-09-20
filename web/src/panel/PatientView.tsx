import { useCallback, useEffect, useState } from "react"

import Calls from "./Calls"
import FactChain from "./FactChain"
import Keyterms from "./Keyterms"
import LiveCall from "./LiveCall"
import WeeklyChart from "./WeeklyChart"
import { get, post, type CallRow, type Fact, type Patient, type Series } from "./api"
import { label, type Copy } from "./copy"

type Mode = "scripted" | "replay" | "live"

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
  const [series, setSeries] = useState<Series[]>([])
  const [calls, setCalls] = useState<CallRow[]>([])
  const [terms, setTerms] = useState<string[]>([])
  const [callId, setCallId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(async () => {
    const [chain, weekly, rows] = await Promise.all([
      get<Fact[]>(`/patients/${patient.id}/chain`),
      get<Series[]>(`/patients/${patient.id}/weekly`),
      get<CallRow[]>(`/patients/${patient.id}/calls`),
    ])
    setFacts(chain)
    setSeries(weekly)
    setCalls(rows)
    if (rows.length > 0) setTerms(await get<string[]>(`/calls/${rows[0].id}/keyterms`))
  }, [patient.id])

  useEffect(() => {
    setCallId(null)
    reload().catch((cause: Error) => setError(cause.message))
  }, [reload])

  const call = async (memory: boolean, mode: Mode, script?: string) => {
    setError(null)
    try {
      const body = { patient_id: patient.id, memory, mode, script }
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
              {label(c.program, patient.program_type)} · {c.followedSince(c.day(patient.started_at))}
            </div>
          </div>
          <div className="controls">
            <div className="controls-row">
              <button className="btn btn-secondary" onClick={() => call(false, "scripted")}>
                {c.callWithoutMemory}
              </button>
              <button className="btn btn-primary" onClick={() => call(true, "scripted")}>
                {c.callWithMemory}
              </button>
            </div>
            <p className="controls-hint">{c.callHint}</p>
            <div className="controls-row">
              <button
                className="btn btn-ghost"
                onClick={() => call(false, "scripted", "week2-off")}
              >
                {c.callSameWithoutMemory}
              </button>
              <button className="btn btn-ghost" onClick={() => call(true, "replay")}>
                {c.callReplay}
              </button>
              <button className="btn btn-ghost" onClick={() => call(true, "scripted", "alarm")}>
                {c.callAlarm}
              </button>
            </div>
            {live && (
              <div className="controls-live">
                <div className="controls-row">
                  <button className="btn btn-secondary" onClick={() => call(false, "live")}>
                    {c.callLiveWithoutMemory}
                  </button>
                  <button className="btn btn-primary" onClick={() => call(true, "live")}>
                    {c.callLiveWithMemory}
                  </button>
                </div>
                <p className="controls-hint">{c.callLiveHint}</p>
              </div>
            )}
          </div>
        </div>
        {error && <p className="error">{error}</p>}
      </header>

      {callId && <LiveCall callId={callId} onEnded={reload} copy={c} />}

      <section className="card">
        <WeeklyChart series={series} copy={c} />
      </section>

      <section className="card">
        <FactChain facts={facts} copy={c} />
      </section>

      <section className="card">
        <Keyterms terms={terms} copy={c} />
      </section>

      <section className="card">
        <Calls calls={calls} copy={c} />
      </section>
    </div>
  )
}
