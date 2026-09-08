export default function Keyterms({ terms }: { terms: string[] }) {
  return (
    <div className="keyterms">
      <h3>Key terms que alimentaron el STT</h3>
      {terms.length === 0 ? (
        <p className="empty">Primera llamada: no había nada en ficha.</p>
      ) : (
        <div className="chips">
          {terms.map((term) => (
            <span className="chip" key={term}>
              {term}
            </span>
          ))}
        </div>
      )}
    </div>
  )
}
