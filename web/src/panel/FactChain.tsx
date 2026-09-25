import { quoteAudio, type Fact } from "./api"
import { label, type Copy } from "./copy"

const PULSE = "M3 12h3.6l2.1-5.6 3.4 11.2 2.2-5.6H21"
const CHECK = "M4 12.6l5 5L20 6.4"
const FLAG = "M5.5 21V4h12.5l-2.6 4.6L18 13.2H5.5"
const RING = "M20 12a8 8 0 1 1-16 0 8 8 0 0 1 16 0Z"
const CLOCK = "M12 4a8 8 0 1 0 0 16 8 8 0 0 0 0-16M12 7.6v4.8l3.2 1.9"

// ponytail: only the four categories the rehab pack produces have a drawing.
// mood and clinical_value fall back to the ring; give them their own path when a
// postpartum or chronic patient reaches the panel.
const ICON: Record<string, string> = {
  symptom: PULSE,
  adherence: CHECK,
  red_flag: FLAG,
  commitment: CLOCK,
}

function Entry({
  fact,
  current,
  paired,
  copy: c,
}: {
  fact: Fact
  current: boolean
  paired: boolean
  copy: Copy
}) {
  const name = label(c.category, fact.category)
  const audio = quoteAudio(fact)
  return (
    <div className={current ? "entry" : "entry retired"}>
      <span className="entry-dot" />
      <svg
        className={fact.category === "red_flag" ? "entry-icon alarm" : "entry-icon"}
        width="15"
        height="15"
        viewBox="0 0 24 24"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.6"
        role="img"
        aria-label={name}
      >
        <path d={ICON[fact.category] ?? RING} strokeLinecap="round" strokeLinejoin="round" />
      </svg>
      <div className="entry-body">
        <div className="entry-head">
          <span className="entry-text">{c.data(fact.fact)}</span>
          {fact.category === "red_flag" && <span className="pill pill-danger">{name}</span>}
          {paired && (
            <span className={current ? "pill pill-accent" : "pill"}>
              {current ? c.factCurrent : c.factRetired}
            </span>
          )}
        </div>
        <p className="entry-quote">«{c.data(fact.quote)}»</p>
        {audio && (
          <audio
            className="entry-audio"
            controls
            preload="none"
            src={audio}
            aria-label={c.playQuote}
          />
        )}
        <p className="entry-source">
          {c.saidOn(c.day(fact.reported_at), fact.turn_id)}
          {!current && fact.valid_until && c.heldUntil(c.day(fact.valid_until))}
        </p>
      </div>
    </div>
  )
}

export default function FactChain({ facts, copy: c }: { facts: Fact[]; copy: Copy }) {
  if (facts.length === 0) {
    return <p className="empty">{c.noHistory}</p>
  }
  return (
    <div>
      <h2>{c.fileTitle}</h2>
      <p className="card-lede">{c.fileLede}</p>
      {facts.map((fact) => (
        <div className="chain" key={fact.id}>
          <Entry fact={fact} current paired={fact.superseded.length > 0} copy={c} />
          {fact.superseded.map((old) => (
            <Entry fact={old} key={old.id} current={false} paired copy={c} />
          ))}
        </div>
      ))}
      <p className="card-note">{c.fileNote}</p>
    </div>
  )
}
