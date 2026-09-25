import { useEffect, useState } from "react"

import { prefersReducedMotion, type Lang } from "../prefs"
import type { Copy } from "./copy"

type Week = "week1" | "week2"

type RailKey = "recall" | "newFact" | "retired" | "summary"

type Text = { es: string; en: string }

type Pick = (value: Text) => string

const both = (value: string): Text => ({ es: value, en: value })

type Beat = {
  d: number
  turn?: { who: "agent" | "patient"; text: Text }
  rail?: {
    key: RailKey
    text?: Text
    detail?: Text
    quote?: Text
    turn?: number
  }
}

const CHAIN_HOLD_MS = 4200
const PACE = 1.6

const TONE: Record<RailKey, string> = {
  recall: "var(--color-accent)",
  newFact: "var(--text-accent)",
  retired: "var(--tone-dim)",
  summary: "var(--tone-dim)",
}

const WEEK2: Beat[] = [
  {
    d: 500,
    rail: {
      key: "recall",
      detail: {
        es: "rodilla derecha · ejercicios en casa · rigidez · caída en el baño",
        en: "right knee · home exercises · stiffness · bathroom fall",
      },
    },
  },
  {
    d: 1000,
    turn: {
      who: "agent",
      text: {
        es: "Hola Ana. La semana pasada me dijiste que la rodilla te dolía 7 de 10 al subir escaleras. ¿Cómo viene esta semana?",
        en: "Hi Ana. Last week you told me your knee hurt 7 out of 10 climbing stairs. How has this week been?",
      },
    },
  },
  {
    d: 1500,
    turn: {
      who: "patient",
      text: {
        es: "La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.",
        en: "My knee is a lot better — it is four out of ten on the stairs now.",
      },
    },
  },
  {
    d: 800,
    rail: {
      key: "newFact",
      text: {
        es: "dolor en la rodilla derecha 4/10 al subir escaleras",
        en: "right knee pain 4/10 climbing stairs",
      },
      quote: { es: "me duele cuatro de diez", en: "it is four out of ten" },
      turn: 4,
    },
  },
  { d: 600, rail: { key: "retired", detail: both("valid_until 2026-09-07") } },
  {
    d: 1100,
    turn: {
      who: "agent",
      text: {
        es: "¿Cuántas veces pudiste hacer los ejercicios esta semana?",
        en: "How many times did you manage the exercises this week?",
      },
    },
  },
  {
    d: 1400,
    turn: {
      who: "patient",
      text: {
        es: "Esta semana los hice cinco veces, me organicé mejor.",
        en: "I did them five times this week, I got myself better organised.",
      },
    },
  },
  {
    d: 800,
    rail: {
      key: "newFact",
      text: {
        es: "hizo los ejercicios cinco veces en la semana",
        en: "did the exercises five times this week",
      },
      quote: { es: "los hice cinco veces", en: "I did them five times" },
      turn: 6,
    },
  },
  {
    d: 1000,
    turn: {
      who: "agent",
      text: {
        es: "Listo, eso era todo por hoy. Le paso el resumen a tu kinesióloga. Hablamos la semana que viene.",
        en: "That is everything for today. I will send the summary to your physio. We will talk next week.",
      },
    },
  },
  { d: 700, rail: { key: "summary" } },
]

const WEEK1: Beat[] = [
  {
    d: 500,
    rail: {
      key: "recall",
      text: { es: "sin datos en ficha", en: "no facts on file" },
      detail: { es: "primera llamada", en: "first call" },
    },
  },
  {
    d: 1000,
    turn: {
      who: "agent",
      text: {
        es: "Hola Ana, soy el seguimiento de la clínica. ¿Cómo viene la rodilla esta semana?",
        en: "Hi Ana, this is the clinic follow-up. How has your knee been this week?",
      },
    },
  },
  {
    d: 1500,
    turn: {
      who: "patient",
      text: {
        es: "La rodilla derecha me duele siete de diez al subir escaleras.",
        en: "My right knee hurts seven out of ten climbing stairs.",
      },
    },
  },
  {
    d: 800,
    rail: {
      key: "newFact",
      text: {
        es: "dolor en la rodilla derecha 7/10 al subir escaleras",
        en: "right knee pain 7/10 climbing stairs",
      },
      quote: {
        es: "La rodilla derecha me duele siete de diez",
        en: "My right knee hurts seven out of ten",
      },
      turn: 4,
    },
  },
  {
    d: 1100,
    turn: {
      who: "agent",
      text: {
        es: "¿Cuántas veces pudiste hacer los ejercicios esta semana?",
        en: "How many times did you manage the exercises this week?",
      },
    },
  },
  {
    d: 1400,
    turn: {
      who: "patient",
      text: {
        es: "Los hice tres veces, me salté dos días por trabajo.",
        en: "I did them three times, I skipped two days because of work.",
      },
    },
  },
  {
    d: 800,
    rail: {
      key: "newFact",
      text: {
        es: "hizo los ejercicios tres veces y se salteó dos días por trabajo",
        en: "did the exercises three times, skipped two days for work",
      },
      quote: {
        es: "Los hice tres veces, me salté dos días",
        en: "I did them three times, I skipped two days",
      },
      turn: 6,
    },
  },
  {
    d: 1000,
    turn: {
      who: "agent",
      text: {
        es: "Listo, eso era todo por hoy. Te llamo la semana que viene.",
        en: "That is everything for today. I will call you again next week.",
      },
    },
  },
  { d: 700, rail: { key: "summary" } },
]

const SCRIPTS: Record<Week, Beat[]> = { week1: WEEK1, week2: WEEK2 }

const CHAIN = {
  pain: {
    category: "symptom",
    current: {
      text: {
        es: "dolor en la rodilla derecha 4/10 al subir escaleras",
        en: "right knee pain 4/10 climbing stairs",
      },
      value: "4/10",
      quote: { es: "me duele cuatro de diez", en: "it is four out of ten" },
      turn: 4,
      day: "2026-09-07",
    },
    previous: {
      text: {
        es: "dolor en la rodilla derecha 7/10 al subir escaleras",
        en: "right knee pain 7/10 climbing stairs",
      },
      value: "7/10",
      quote: {
        es: "La rodilla derecha me duele siete de diez",
        en: "My right knee hurts seven out of ten",
      },
      turn: 4,
      from: "2026-08-31",
      until: "2026-09-07",
    },
  },
  adherence: {
    category: "adherence",
    current: {
      text: {
        es: "hizo los ejercicios cinco veces en la semana",
        en: "did the exercises five times this week",
      },
      value: "5×",
      quote: { es: "los hice cinco veces", en: "I did them five times" },
      turn: 6,
      day: "2026-09-07",
    },
    previous: {
      text: {
        es: "hizo los ejercicios tres veces y se salteó dos días por trabajo",
        en: "did the exercises three times, skipped two days for work",
      },
      value: "3×",
      quote: {
        es: "Los hice tres veces, me salté dos días",
        en: "I did them three times, I skipped two days",
      },
      turn: 6,
      from: "2026-08-31",
      until: "2026-09-07",
    },
  },
}

const WAVE_DELAYS = [0, 0.1, 0.2, 0.3, 0.45, 0.25, 0.15, 0.35]

function Link({
  fill,
  ring,
  label,
  text,
  struck,
  value,
  valueColor,
  meta,
}: {
  fill: string
  ring: string
  label: string
  text: string
  struck?: boolean
  value: string
  valueColor: string
  meta: string
}) {
  return (
    <div style={{ position: "relative" }}>
      <span
        style={{
          position: "absolute",
          left: -17,
          top: 4,
          width: 7,
          height: 7,
          boxSizing: "border-box",
          borderRadius: "50%",
          background: fill,
          border: `1px solid ${ring}`,
        }}
      />
      <div className="eyebrow" style={{ color: "var(--text-muted)", marginBottom: 3 }}>
        {label}
      </div>
      <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
        <span
          className={struck ? "caption noc-strike" : "caption"}
          style={{ flex: 1, color: struck ? "var(--tone-dim)" : undefined }}
        >
          {text}
        </span>
        <span className="card-title" style={{ color: valueColor }}>
          {value}
        </span>
      </div>
      <div className="caption" style={{ color: "var(--text-muted)", marginTop: 2 }}>
        {meta}
      </div>
    </div>
  )
}

function railText(
  copy: Copy,
  beat: Beat,
  t: Pick,
): { label: string; text: string; detail?: string } {
  const rail = beat.rail!
  if (rail.key === "recall") {
    return {
      label: copy.railRecall,
      text: rail.text ? t(rail.text) : copy.railRecallText,
      detail: rail.detail && t(rail.detail),
    }
  }
  if (rail.key === "newFact") {
    const detail = rail.quote
      ? copy.demoTurnRef(t(rail.quote), rail.turn ?? 0)
      : rail.detail && t(rail.detail)
    return { label: copy.railNewFact, text: rail.text ? t(rail.text) : "", detail }
  }
  if (rail.key === "retired") {
    return {
      label: copy.railRetired,
      text: copy.railRetiredText,
      detail: rail.detail && t(rail.detail),
    }
  }
  return { label: copy.railSummary, text: copy.railSummaryText, detail: copy.railSummaryDetail }
}

export default function DemoCard({ copy: c, lang }: { copy: Copy; lang: Lang }) {
  const t: Pick = (value) => value[lang]
  const day = (iso: string) =>
    new Intl.DateTimeFormat(lang, { day: "numeric", month: "short" }).format(
      new Date(`${iso}T00:00:00`),
    )

  const [week, setWeekState] = useState<Week>("week2")
  const script = SCRIPTS[week]
  const [step, setStep] = useState(prefersReducedMotion() ? script.length : 0)
  const [paused, setPaused] = useState(false)
  const still = prefersReducedMotion()
  const first = week === "week1"

  const setWeek = (next: Week) => {
    setWeekState(next)
    setStep(prefersReducedMotion() ? SCRIPTS[next].length : 0)
    setPaused(false)
  }

  useEffect(() => {
    // ponytail: resuming restarts the current beat's whole delay, not its remainder.
    // Store the start timestamp and subtract it if the pacing ever has to be exact.
    if (paused || prefersReducedMotion()) return
    const done = step >= script.length
    const wait = done ? CHAIN_HOLD_MS : script[step].d * PACE
    const timer = setTimeout(() => {
      if (!done) {
        setStep(step + 1)
        return
      }
      if (week === "week1") setWeekState("week2")
      setStep(0)
    }, wait)
    return () => clearTimeout(timer)
  }, [step, paused, script, week])

  const stepTo = (next: number) => {
    setPaused(true)
    if (next > script.length && first) {
      setWeekState("week2")
      setStep(0)
      return
    }
    setStep(Math.min(Math.max(next, 0), script.length))
  }

  const shown = script.slice(0, Math.min(step, script.length)).map((beat, at) => ({ beat, at }))
  const turns = shown.filter((entry) => entry.beat.turn).slice(-6)
  const rail = shown.filter((entry) => entry.beat.rail).slice(-5)
  const ended = step >= script.length
  const turnCount = shown.filter((entry) => entry.beat.turn).length

  return (
    <div
      id="demo"
      className={paused ? "is-paused" : undefined}
      style={{
        minWidth: 0,
        borderRadius: "var(--radius-lg)",
        background:
          "linear-gradient(180deg, var(--color-surface), color-mix(in srgb, var(--color-surface) 70%, var(--color-bg)))",
        boxShadow: "var(--shadow-md)",
        overflow: "hidden",
        scrollMarginTop: 90,
      }}
    >
      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "12px 16px",
          borderBottom: "1px solid var(--color-divider)",
        }}
      >
        <span
          className="noc-pulse"
          style={{
            width: 7,
            height: 7,
            borderRadius: "50%",
            background: "var(--color-accent)",
            boxShadow: "0 0 10px var(--color-accent)",
            animationDuration: "1.6s",
          }}
        />
        <span className="eyebrow">{c.demoCaption}</span>
        <div className="seg" style={{ marginLeft: "auto" }}>
          {(["week1", "week2"] as Week[]).map((option) => (
            <label className="seg-opt" key={option}>
              <input
                type="radio"
                name="demo-week"
                checked={week === option}
                onChange={() => setWeek(option)}
              />
              {option === "week1" ? c.demoWeek1 : c.demoWeek2}
            </label>
          ))}
        </div>
        <span className={first ? "tag tag-outline" : "tag tag-accent"}>
          {first ? c.demoMemoryOff : c.demoMemoryOn}
        </span>
      </div>

      {ended ? (
        <div
          style={{
            padding: 16,
            minHeight: 372,
            display: "flex",
            flexDirection: "column",
            gap: 12,
          }}
        >
          <h6 style={{ margin: 0, color: "var(--text-muted)" }}>
            {first ? c.demoChainFirst : c.demoChain}
          </h6>
          {(Object.keys(CHAIN) as Array<keyof typeof CHAIN>).map((key) => {
            const row = CHAIN[key]
            return (
              <div
                className="noc-in"
                key={key}
                style={{
                  border: "1px solid var(--color-divider)",
                  borderRadius: "var(--radius-md)",
                  padding: "11px 12px",
                  display: "flex",
                  flexDirection: "column",
                  gap: 9,
                }}
              >
                <span className="tag tag-accent" style={{ alignSelf: "flex-start" }}>
                  {c.demoCategory[row.category] ?? row.category}
                </span>
                <div
                  style={{
                    marginLeft: 3,
                    paddingLeft: 13,
                    borderLeft: "1px solid var(--color-divider)",
                    display: "flex",
                    flexDirection: "column",
                    gap: 10,
                  }}
                >
                  {first ? (
                    <Link
                      fill="var(--color-accent)"
                      ring="var(--color-accent)"
                      label={`${c.demoChainCurrent} · ${day(row.previous.from)}`}
                      text={t(row.previous.text)}
                      value={row.previous.value}
                      valueColor="var(--text-accent)"
                      meta={c.demoTurnRef(t(row.previous.quote), row.previous.turn)}
                    />
                  ) : (
                    <>
                      <Link
                        fill="var(--color-accent)"
                        ring="var(--color-accent)"
                        label={`${c.demoChainCurrent} · ${day(row.current.day)}`}
                        text={t(row.current.text)}
                        value={row.current.value}
                        valueColor="var(--text-accent)"
                        meta={c.demoTurnRef(t(row.current.quote), row.current.turn)}
                      />
                      <Link
                        fill="var(--color-bg)"
                        ring="var(--tone-dim)"
                        label={`${c.demoChainRetired} · ${day(row.previous.from)} → ${day(row.previous.until)}`}
                        text={t(row.previous.text)}
                        struck
                        value={row.previous.value}
                        valueColor="var(--tone-dim)"
                        meta={c.demoTurnRef(t(row.previous.quote), row.previous.turn)}
                      />
                    </>
                  )}
                </div>
              </div>
            )
          })}
          <div className="caption" style={{ marginTop: "auto", color: "var(--text-muted)" }}>
            {first ? c.demoChainNoteFirst : c.demoChainNote}
          </div>
        </div>
      ) : (
        <div
          className="demo-split"
          style={{
            display: "grid",
            gridTemplateColumns: "minmax(0, 1.15fr) minmax(0, 1fr)",
            minHeight: 372,
          }}
        >
          <div
            style={{
              padding: "14px 16px",
              borderRight: "1px solid var(--color-divider)",
              display: "flex",
              flexDirection: "column",
              gap: 10,
            }}
          >
            <h6 style={{ margin: 0, color: "var(--text-muted)" }}>{c.demoTranscript}</h6>
            {turns.map(({ beat, at }) => (
              <div className="noc-in" key={at}>
                <div className="eyebrow" style={{ color: "var(--text-muted)", marginBottom: 3 }}>
                  {beat.turn!.who === "agent" ? c.demoAgent : c.demoPatient}
                </div>
                <p
                  className="body-sm"
                  style={{
                    margin: 0,
                    color: beat.turn!.who === "agent" ? "var(--text-accent)" : "var(--color-text)",
                  }}
                >
                  {t(beat.turn!.text)}
                </p>
              </div>
            ))}
            <div style={{ marginTop: "auto", display: "flex", alignItems: "flex-end", gap: 3, height: 22 }}>
              {WAVE_DELAYS.map((delay, index) => (
                <span
                  className="noc-wave"
                  key={index}
                  style={{
                    flex: 1,
                    background: "color-mix(in srgb, var(--color-accent) 55%, transparent)",
                    height: "100%",
                    transformOrigin: "bottom",
                    animationDelay: `${delay}s`,
                  }}
                />
              ))}
            </div>
          </div>
          <div
            style={{
              padding: "14px 16px",
              display: "flex",
              flexDirection: "column",
              gap: 9,
              background: "color-mix(in srgb, var(--color-bg) 45%, transparent)",
            }}
          >
            <h6 style={{ margin: 0, color: "var(--text-muted)" }}>{c.demoActivity}</h6>
            {rail.map(({ beat, at }) => {
              const line = railText(c, beat, t)
              const tone = TONE[beat.rail!.key]
              return (
                <div
                  className="noc-slide"
                  key={at}
                  style={{ borderLeft: `2px solid ${tone}`, paddingLeft: 9 }}
                >
                  <div className="eyebrow" style={{ color: tone, marginBottom: 2 }}>
                    {line.label}
                  </div>
                  <div className="caption">{line.text}</div>
                  {line.detail && (
                    <div className="caption" style={{ marginTop: 2, color: "var(--text-muted)" }}>
                      {line.detail}
                    </div>
                  )}
                </div>
              )
            })}
          </div>
        </div>
      )}

      <div
        style={{
          display: "flex",
          alignItems: "center",
          gap: 10,
          padding: "11px 16px",
          borderTop: "1px solid var(--color-divider)",
        }}
      >
        <button
          className="btn btn-ghost"
          aria-label={c.demoRestart}
          onClick={() => setWeek("week1")}
        >
          ↺
        </button>
        <button
          className="btn btn-ghost"
          aria-label={c.demoBack}
          disabled={step === 0}
          onClick={() => stepTo(step - 1)}
        >
          ◀
        </button>
        {!still && (
          <button
            className="btn btn-ghost"
            onClick={() => setPaused(!paused)}
          >
            {paused ? c.demoResume : c.demoPause}
          </button>
        )}
        <button
          className="btn btn-ghost"
          aria-label={c.demoForward}
          disabled={step === script.length && !first}
          onClick={() => stepTo(step + 1)}
        >
          ▶
        </button>
        <button
          className="btn btn-ghost"
          onClick={() => {
            setStep(still ? script.length : 0)
            setPaused(false)
          }}
        >
          {c.demoReplay}
        </button>
        <span className="caption" style={{ marginLeft: "auto", color: "var(--text-muted)" }}>
          {ended
            ? first
              ? c.demoEndedFirst
              : c.demoEnded
            : paused
              ? c.demoPaused(turnCount)
              : c.demoStreaming(turnCount)}
        </span>
      </div>
    </div>
  )
}
