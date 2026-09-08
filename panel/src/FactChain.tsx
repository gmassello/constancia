import type { Fact } from "./api"

const day = (value: string) => value.slice(0, 10)

function Row({ fact, retired }: { fact: Fact; retired: boolean }) {
  return (
    <div className={retired ? "fact retired" : "fact"}>
      <div className="fact-head">
        <span className={`tag tag-${fact.category}`}>{fact.category}</span>
        <span className="fact-text">{fact.fact}</span>
        {fact.value !== null && <span className="fact-value">{fact.value}</span>}
      </div>
      <div className="fact-meta">
        «{fact.quote}» · turno {fact.turn_id} · {day(fact.reported_at)}
        {retired && fact.valid_until && ` · retirado ${day(fact.valid_until)}`}
      </div>
    </div>
  )
}

export default function FactChain({ facts }: { facts: Fact[] }) {
  if (facts.length === 0) {
    return <p className="empty">Sin antecedentes: es la primera vez que hablan.</p>
  }
  return (
    <div>
      <h2>Ficha del paciente</h2>
      {facts.map((fact) => (
        <div className="chain" key={fact.id}>
          <Row fact={fact} retired={false} />
          {fact.superseded.map((old) => (
            <Row fact={old} key={old.id} retired />
          ))}
        </div>
      ))}
    </div>
  )
}
