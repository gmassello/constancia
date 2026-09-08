import { useEffect, useState } from "react"

import PatientView from "./PatientView"
import { get, type Health, type Patient } from "./api"

export default function App() {
  const [patients, setPatients] = useState<Patient[]>([])
  const [selected, setSelected] = useState<Patient | null>(null)
  const [health, setHealth] = useState<Health | null>(null)

  useEffect(() => {
    get<Patient[]>("/patients").then((rows) => {
      setPatients(rows)
      setSelected(rows[0] ?? null)
    })
    get<Health>("/health").then(setHealth)
  }, [])

  return (
    <div className="app">
      <aside>
        <h2>constancia</h2>
        {health && (
          <div className="label">
            datos: {health.store === "seed" ? "seed local" : "postgres"} · teléfono:{" "}
            {health.live ? "listo" : "sin claves"}
          </div>
        )}
        <nav>
          {patients.map((patient) => (
            <button
              className={selected?.id === patient.id ? "nav on" : "nav"}
              key={patient.id}
              onClick={() => setSelected(patient)}
            >
              {patient.name}
              <span className="label">{patient.program_type}</span>
            </button>
          ))}
        </nav>
      </aside>
      <main>
        {selected ? (
          <PatientView patient={selected} live={health?.live ?? false} />
        ) : (
          <p className="empty">No hay pacientes cargados.</p>
        )}
      </main>
    </div>
  )
}
