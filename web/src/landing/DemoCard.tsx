import { useEffect, useState } from "react"

import { prefersReducedMotion, type Lang } from "../prefs"
import type { Copy } from "./copy"

type RailKey = "recall" | "newFact" | "retired" | "summary"

type Beat = {
  d: number
  turn?: { who: "agent" | "patient"; text: string; gloss: string }
  rail?: {
    key: RailKey
    text?: string
    gloss?: string
    detail?: string
    detailGloss?: string
    quote?: string
    turn?: number
  }
  supersede?: "pain" | "adherence"
}

const CHAIN_HOLD_MS = 4200

const TONE: Record<RailKey, string> = {
  recall: "var(--color-accent)",
  newFact: "var(--text-accent)",
  retired: "var(--tone-dim)",
  summary: "var(--tone-dim)",
}

const SCRIPT: Beat[] = [
  {
    d: 500,
    rail: {
      key: "recall",
      detail: "rodilla derecha · ejercicios en casa · rigidez · caída en el baño",
      detailGloss: "right knee · home exercises · stiffness · bathroom fall",
    },
  },
  {
    d: 1000,
    turn: {
      who: "agent",
      text: "Hola Ana. La semana pasada me dijiste que la rodilla te dolía 7 de 10 al subir escaleras. ¿Cómo viene esta semana?",
      gloss: "Hi Ana. Last week you told me your knee hurt 7 out of 10 climbing stairs. How has this week been?",
    },
  },
  {
    d: 1500,
    turn: {
      who: "patient",
      text: "La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.",
      gloss: "My knee is a lot better — it is four out of ten on the stairs now.",
    },
  },
  {
    d: 800,
    rail: {
      key: "newFact",
      text: "dolor en la rodilla derecha 4/10 al subir escaleras",
      gloss: "right knee pain 4/10 climbing stairs",
      quote: "me duele cuatro de diez",
      turn: 4,
    },
  },
  { d: 600, supersede: "pain", rail: { key: "retired", detail: "valid_until 2026-09-07" } },
  {
    d: 1100,
    turn: {
      who: "agent",
      text: "¿Cuántas veces pudiste hacer los ejercicios esta semana?",
      gloss: "How many times did you manage the exercises this week?",
    },
  },
  {
    d: 1400,
    turn: {
      who: "patient",
      text: "Esta semana los hice cinco veces, me organicé mejor.",
      gloss: "I did them five times this week, I got myself better organised.",
    },
  },
  {
    d: 800,
    supersede: "adherence",
    rail: {
      key: "newFact",
      text: "hizo los ejercicios cinco veces en la semana",
      gloss: "did the exercises five times this week",
      quote: "los hice cinco veces",
      turn: 6,
    },
  },
  {
    d: 1000,
    turn: {
      who: "agent",
      text: "Listo, eso era todo por hoy. Le paso el resumen a tu kinesióloga. Hablamos la semana que viene.",
      gloss: "That is everything for today. I will send the summary to your physio. We will talk next week.",
    },
  },
  { d: 700, rail: { key: "summary" } },
]

const CHAIN = {
  pain: {
    category: "symptom",
    text: "dolor en la rodilla derecha 4/10 al subir escaleras",
    gloss: "right knee pain 4/10 climbing stairs",
    value: "4/10",
    quote: "me duele cuatro de diez",
    turn: 4,
    day: "2026-09-07",
    oldText: "dolor en la rodilla derecha 7/10 al subir escaleras",
    oldGloss: "right knee pain 7/10 climbing stairs",
    oldValue: "7/10",
    oldQuote: "La rodilla derecha me duele siete de diez",
    oldTurn: 4,
    oldDay: "2026-09-07",
    before: {
      text: "dolor en la rodilla derecha 7/10 al subir escaleras",
      gloss: "right knee pain 7/10 climbing stairs",
      value: "7/10",
      quote: "La rodilla derecha me duele siete de diez",
      turn: 4,
      day: "2026-08-31",
    },
  },
  adherence: {
    category: "adherence",
    text: "hizo los ejercicios cinco veces en la semana",
    gloss: "did the exercises five times this week",
    value: "5×",
    quote: "los hice cinco veces",
    turn: 6,
    day: "2026-09-07",
    oldText: "hizo los ejercicios tres veces y se salteó dos días por trabajo",
    oldGloss: "did the exercises three times, skipped two days for work",
    oldValue: "3×",
    oldQuote: "Los hice tres veces, me salté dos días",
    oldTurn: 6,
    oldDay: "2026-09-07",
    before: {
      text: "hizo los ejercicios tres veces y se salteó dos días por trabajo",
      gloss: "did the exercises three times, skipped two days for work",
      value: "3×",
      quote: "Los hice tres veces, me salté dos días",
      turn: 6,
      day: "2026-08-31",
    },
  },
}

const WAVE_DELAYS = [0, 0.1, 0.2, 0.3, 0.45, 0.25, 0.15, 0.35]

function railText(
  copy: Copy,
  beat: Beat,
): { label: string; text: string; detail?: string; gloss?: string; detailGloss?: string } {
  const rail = beat.rail!
  if (rail.key === "recall") {
    return {
      label: copy.railRecall,
      text: copy.railRecallText,
      detail: rail.detail,
      detailGloss: rail.detailGloss,
    }
  }
  if (rail.key === "newFact") {
    const detail = rail.quote ? copy.demoTurnRef(rail.quote, rail.turn ?? 0) : rail.detail
    return { label: copy.railNewFact, text: rail.text ?? "", detail, gloss: rail.gloss }
  }
  if (rail.key === "retired") {
    return { label: copy.railRetired, text: copy.railRetiredText, detail: rail.detail }
  }
  return { label: copy.railSummary, text: copy.railSummaryText, detail: copy.railSummaryDetail }
}

export default function DemoCard({ copy: c, lang }: { copy: Copy; lang: Lang }) {
  const gloss = lang === "en"

  const [step, setStep] = useState(prefersReducedMotion() ? SCRIPT.length : 0)

  useEffect(() => {
    if (prefersReducedMotion()) return
    const done = step >= SCRIPT.length
    const wait = done ? CHAIN_HOLD_MS : SCRIPT[step].d
    const timer = setTimeout(() => setStep(done ? 0 : step + 1), wait)
    return () => clearTimeout(timer)
  }, [step])

  const shown = SCRIPT.slice(0, Math.min(step, SCRIPT.length)).map((beat, at) => ({ beat, at }))
  const turns = shown.filter((entry) => entry.beat.turn).slice(-6)
  const rail = shown.filter((entry) => entry.beat.rail).slice(-5)
  const superseded = new Set(shown.map((entry) => entry.beat.supersede).filter(Boolean))
  const ended = step >= SCRIPT.length
  const turnCount = shown.filter((entry) => entry.beat.turn).length

  return (
    <div
      id="demo"
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
        <span style={{ fontFamily: "var(--font-heading)", fontSize: 13 }}>{c.demoCaption}</span>
        <span className="tag tag-outline" style={{ marginLeft: "auto", fontSize: 10 }}>
          es-AR
        </span>
        <span className="tag tag-accent" style={{ fontSize: 10 }}>
          {c.demoMemoryOn}
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
          <h6 style={{ margin: 0, fontSize: 10, color: "var(--text-muted)" }}>{c.demoChain}</h6>
          {(Object.keys(CHAIN) as Array<keyof typeof CHAIN>).map((key) => {
            const row = CHAIN[key]
            const retired = superseded.has(key)
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
                  gap: 7,
                }}
              >
                <div style={{ display: "flex", alignItems: "baseline", gap: 8 }}>
                  <span className="tag tag-accent" style={{ fontSize: 10 }}>
                    {c.demoCategory[row.category] ?? row.category}
                  </span>
                  <span style={{ fontSize: 13, lineHeight: 1.45, flex: 1 }}>
                    {retired ? row.text : row.before.text}
                    {gloss && (
                      <span className="gloss">{retired ? row.gloss : row.before.gloss}</span>
                    )}
                  </span>
                  <span
                    style={{
                      fontFamily: "var(--font-heading)",
                      fontSize: 20,
                      color: "var(--text-accent)",
                    }}
                  >
                    {retired ? row.value : row.before.value}
                  </span>
                </div>
                <div style={{ fontSize: 10.5, color: "var(--text-muted)" }}>
                  {retired
                    ? c.demoFactMeta(row.quote, row.turn, row.day)
                    : c.demoFactMeta(row.before.quote, row.before.turn, row.before.day)}
                </div>
                {retired && (
                  <div
                    style={{
                      position: "relative",
                      padding: "8px 10px",
                      borderRadius: "var(--radius-sm)",
                      background: "color-mix(in srgb, var(--color-bg) 60%, transparent)",
                    }}
                  >
                    <div style={{ display: "flex", alignItems: "baseline", gap: 8, opacity: 0.55 }}>
                      <span style={{ fontSize: 12, lineHeight: 1.45, flex: 1 }}>
                        {row.oldText}
                        {gloss && <span className="gloss">{row.oldGloss}</span>}
                      </span>
                      <span style={{ fontFamily: "var(--font-heading)", fontSize: 15 }}>{row.oldValue}</span>
                    </div>
                    <div style={{ fontSize: 10.5, opacity: 0.45, marginTop: 2 }}>
                      {c.demoFactMeta(row.oldQuote, row.oldTurn, row.oldDay)}
                    </div>
                    <div
                      className="noc-strike"
                      style={{
                        position: "absolute",
                        left: 10,
                        right: 10,
                        top: 17,
                        height: 1,
                        background: "var(--color-accent)",
                        transformOrigin: "left",
                      }}
                    />
                  </div>
                )}
              </div>
            )
          })}
          <div style={{ marginTop: "auto", fontSize: 11.5, color: "var(--text-muted)" }}>
            {c.demoChainNote}
          </div>
        </div>
      ) : (
        <div
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
            <h6 style={{ margin: 0, fontSize: 10, color: "var(--text-muted)" }}>{c.demoTranscript}</h6>
            {turns.map(({ beat, at }) => (
              <div className="noc-in" key={at}>
                <div
                  style={{
                    fontSize: 10,
                    letterSpacing: "0.07em",
                    textTransform: "uppercase",
                    color: "var(--text-muted)",
                    marginBottom: 3,
                  }}
                >
                  {beat.turn!.who === "agent" ? c.demoAgent : c.demoPatient}
                </div>
                <p
                  style={{
                    margin: 0,
                    fontSize: 13,
                    lineHeight: 1.5,
                    color: beat.turn!.who === "agent" ? "var(--text-accent)" : "var(--color-text)",
                  }}
                >
                  {beat.turn!.text}
                </p>
                {gloss && <p className="gloss">{beat.turn!.gloss}</p>}
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
            <h6 style={{ margin: 0, fontSize: 10, color: "var(--text-muted)" }}>{c.demoActivity}</h6>
            {rail.map(({ beat, at }) => {
              const line = railText(c, beat)
              const tone = TONE[beat.rail!.key]
              return (
                <div
                  className="noc-slide"
                  key={at}
                  style={{ borderLeft: `2px solid ${tone}`, paddingLeft: 9 }}
                >
                  <div
                    style={{
                      fontSize: 10,
                      letterSpacing: "0.06em",
                      textTransform: "uppercase",
                      color: tone,
                      marginBottom: 2,
                    }}
                  >
                    {line.label}
                  </div>
                  <div style={{ fontSize: 12, lineHeight: 1.45 }}>{line.text}</div>
                  {gloss && line.gloss && <div className="gloss">{line.gloss}</div>}
                  {line.detail && (
                    <div
                      style={{
                        fontSize: 10.5,
                        lineHeight: 1.45,
                        marginTop: 2,
                        color: "var(--text-muted)",
                      }}
                    >
                      {line.detail}
                    </div>
                  )}
                  {gloss && line.detailGloss && <div className="gloss">{line.detailGloss}</div>}
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
        <button className="btn btn-ghost" onClick={() => setStep(0)} style={{ fontSize: 12 }}>
          {c.demoReplay}
        </button>
        <span style={{ marginLeft: "auto", fontSize: 11, color: "var(--text-muted)" }}>
          {ended ? c.demoEnded : c.demoStreaming(turnCount)}
        </span>
      </div>
    </div>
  )
}
