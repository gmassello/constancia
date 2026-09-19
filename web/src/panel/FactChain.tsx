import type { Fact } from "./api"
import { label, type Copy } from "./copy"

const day = (value: string) => value.slice(0, 10)

function Row({ fact, retired, copy: c }: { fact: Fact; retired: boolean; copy: Copy }) {
  return (
    <div className={retired ? "fact retired" : "fact"}>
      <div className="fact-head">
        <span className={`pill pill-${fact.category}`}>{label(c.category, fact.category)}</span>
        <span className="fact-text">{fact.fact}</span>
        {fact.value !== null && <span className="fact-value">{fact.value}</span>}
      </div>
      <div className="fact-meta">
        {c.quoteMeta(fact.quote, fact.turn_id, day(fact.reported_at))}
        {retired && fact.valid_until && c.retiredOn(day(fact.valid_until))}
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
      {facts.map((fact) => (
        <div className="chain" key={fact.id}>
          <Row fact={fact} retired={false} copy={c} />
          {fact.superseded.map((old) => (
            <Row fact={old} key={old.id} retired copy={c} />
          ))}
        </div>
      ))}
    </div>
  )
}
