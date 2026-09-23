import { useState } from "react"

import { post, type PatientQuestion } from "./api"
import { label, type Copy } from "./copy"

function Open({
  question,
  onChanged,
  copy: c,
}: {
  question: PatientQuestion
  onChanged: () => void
  copy: Copy
}) {
  const [draft, setDraft] = useState("")
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const send = async (path: string, body: unknown) => {
    setBusy(true)
    setError(null)
    try {
      await post(`/questions/${question.id}/${path}`, body)
      onChanged()
    } catch {
      setError(c.questionFailed)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="ask">
      <p className="ask-text">{c.data(question.question)}</p>
      <p className="entry-quote">«{c.data(question.quote)}»</p>
      <p className="entry-source">{c.saidOn(c.day(question.asked_at), question.turn_id)}</p>
      <label className="ask-label" htmlFor={`answer-${question.id}`}>
        {c.answerLabel}
      </label>
      <textarea
        id={`answer-${question.id}`}
        className="input"
        rows={2}
        value={draft}
        placeholder={c.answerPlaceholder}
        onChange={(event) => setDraft(event.target.value)}
      />
      <p className="ask-note">{c.answerNote}</p>
      <div className="ask-actions">
        <button
          className="btn btn-primary"
          disabled={busy || draft.trim().length === 0}
          data-loading={busy || undefined}
          onClick={() => send("answer", { answer: draft.trim() })}
        >
          {c.answerAction}
        </button>
        <button
          className="btn btn-secondary"
          disabled={busy}
          onClick={() => send("dismiss", {})}
        >
          {c.dismissAction}
        </button>
      </div>
      {error && <p className="error">{error}</p>}
    </div>
  )
}

function Settled({ question, copy: c }: { question: PatientQuestion; copy: Copy }) {
  return (
    <div className="ask settled">
      <div className="entry-head">
        <span className="entry-text">{c.data(question.question)}</span>
        <span className={`pill pill-${question.status}`}>
          {label(c.questionStatus, question.status)}
        </span>
      </div>
      {question.answer && <p className="ask-answer">{c.data(question.answer)}</p>}
    </div>
  )
}

export default function Questions({
  questions,
  onChanged,
  copy: c,
}: {
  questions: PatientQuestion[]
  onChanged: () => void
  copy: Copy
}) {
  const open = questions.filter((question) => question.status === "open")
  const settled = questions.filter((question) => question.status !== "open")
  return (
    <div>
      <h2>{c.questionsTitle}</h2>
      <p className="card-lede">{c.questionsLede}</p>
      {questions.length === 0 && <p className="empty">{c.questionsNone}</p>}
      {open.map((question) => (
        <Open key={question.id} question={question} onChanged={onChanged} copy={c} />
      ))}
      {settled.map((question) => (
        <Settled key={question.id} question={question} copy={c} />
      ))}
    </div>
  )
}
