import type { Copy } from "./copy"

export default function Keyterms({ terms, copy: c }: { terms: string[]; copy: Copy }) {
  return (
    <div className="keyterms">
      <h3>{c.keytermsTitle}</h3>
      {terms.length === 0 ? (
        <p className="empty">{c.firstCall}</p>
      ) : (
        <div className="chips">
          {terms.map((term) => (
            <span className="chip" key={term}>
              {c.data(term)}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
