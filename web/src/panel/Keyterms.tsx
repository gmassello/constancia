import type { Copy } from "./copy"

const FILE = "M13 2.5H6.5v19h11V7zM13 2.5V7h4.5M9.5 12h5M9.5 16h3.5"
const TAG = "M11.5 3H3v8.5l9.5 9.5 8.5-8.5zM7.2 7.2h.01"
const MIC = "M12 3a3 3 0 0 1 3 3v6a3 3 0 0 1-6 0V6a3 3 0 0 1 3-3ZM5 11a7 7 0 0 0 14 0M12 18v3"
const ARROW = "M4 12h12M11.5 7l5 5-5 5"

function Icon({ path, size, className }: { path: string; size: number; className: string }) {
  return (
    <svg
      className={className}
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.6"
      strokeLinecap="round"
      strokeLinejoin="round"
      aria-hidden="true"
    >
      <path d={path} />
    </svg>
  )
}

function Step({ path, caption }: { path: string; caption: string }) {
  return (
    <div className="terms-step">
      <Icon path={path} size={22} className="terms-icon" />
      <span>{caption}</span>
    </div>
  )
}

export default function Keyterms({ terms, copy: c }: { terms: string[]; copy: Copy }) {
  return (
    <div className="keyterms">
      <h2>{c.keytermsTitle}</h2>
      <p className="card-lede">{c.keytermsLede}</p>
      {terms.length === 0 ? (
        <p className="empty">{c.firstCall}</p>
      ) : (
        <>
          <div className="terms-flow">
            <Step path={FILE} caption={c.keytermsFile} />
            <Icon path={ARROW} size={18} className="terms-arrow" />
            <Step path={TAG} caption={c.keytermsPass} />
            <Icon path={ARROW} size={18} className="terms-arrow" />
            <Step path={MIC} caption={c.keytermsHear} />
          </div>
          <div className="chips">
            {terms.map((term) => (
              <span className="chip" key={term}>
                {c.data(term)}
              </span>
            ))}
          </div>
          <p className="card-note">{c.keytermsNote}</p>
        </>
      )}
    </div>
  )
}
