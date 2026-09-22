import { useEffect, useMemo, useState } from "react"

import PatientView from "./PatientView"
import { get, type Health, type Patient } from "./api"
import { copy } from "./copy"
import { label } from "./copy"
import { usePrefs, type Lang } from "../prefs"

const SUN = "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10Zm0-14v2m0 18v-2M3 12h2m14 0h2M5.6 5.6l1.4 1.4m10 10 1.4 1.4m0-12.8-1.4 1.4m-10 10-1.4 1.4"
const MOON = "M21 13a9 9 0 1 1-10-10 7 7 0 0 0 10 10Z"

export default function App() {
  const { theme, setTheme, lang, setLang } = usePrefs()
  const [patients, setPatients] = useState<Patient[]>([])
  const [selected, setSelected] = useState<Patient | null>(null)
  const [health, setHealth] = useState<Health | null>(null)
  const [unreachable, setUnreachable] = useState(false)
  const c = useMemo(() => copy(lang), [lang])
  const dark = theme === "dark"

  useEffect(() => {
    get<Patient[]>("/patients")
      .then((rows) => {
        setPatients(rows)
        setSelected(rows[0] ?? null)
      })
      .catch(() => setUnreachable(true))
    get<Health>("/health")
      .then(setHealth)
      .catch(() => setUnreachable(true))
  }, [])

  return (
    <div className="app">
      <aside>
        <a className="brand" href="/">
          {c.brand}
        </a>
        {health && (
          <div className="label">
            {health.store === "seed" ? c.dataSeed : c.dataPostgres} ·{" "}
            {health.live ? c.phoneReady : c.phoneNoKeys}
          </div>
        )}
        <a className="btn btn-secondary aside-home" href="/">
          ← {c.home}
        </a>
        <div className="aside-controls">
          <div className="seg">
            {(["en", "es"] as Lang[]).map((option) => (
              <label className="seg-opt" key={option}>
                <input
                  type="radio"
                  name="lang"
                  checked={lang === option}
                  onChange={() => setLang(option)}
                />
                {option.toUpperCase()}
              </label>
            ))}
          </div>
          <button
            className="btn btn-secondary btn-icon"
            onClick={() => setTheme(dark ? "light" : "dark")}
            aria-label={dark ? c.themeToLight : c.themeToDark}
          >
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6">
              <path d={dark ? SUN : MOON} strokeLinecap="round" strokeLinejoin="round" />
            </svg>
          </button>
        </div>
        <nav>
          {patients.map((patient) => (
            <button
              className={selected?.id === patient.id ? "nav-item on" : "nav-item"}
              key={patient.id}
              onClick={() => setSelected(patient)}
            >
              {patient.name}
              <span className="label">{label(c.program, patient.program_type)}</span>
            </button>
          ))}
        </nav>
      </aside>
      <main>
        {selected ? (
          <PatientView patient={selected} live={health?.live ?? false} copy={c} />
        ) : unreachable ? (
          <p className="error">{c.backendDown}</p>
        ) : (
          <p className="empty">{c.noPatients}</p>
        )}
      </main>
    </div>
  )
}
