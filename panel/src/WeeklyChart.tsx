import type { Week } from "./api"

const PLOT_FILL = 88

export default function WeeklyChart({ weeks }: { weeks: Week[] }) {
  if (weeks.length === 0) {
    return <p className="empty">Todavía no hay ningún valor numérico para graficar.</p>
  }
  const max = Math.max(...weeks.map((week) => week.value), 1)

  return (
    <div>
      <div className="chart-head">
        <h2>Evolución semanal</h2>
        <span className="label">{weeks[0].term}</span>
      </div>
      <div className="chart">
        <div className="gridline" style={{ top: 0 }} />
        <div className="gridline" style={{ top: "50%" }} />
        <div className="gridline" style={{ bottom: 0 }} />
        {weeks.map((week) => (
          <div className="chart-col" key={week.week}>
            <div className="bar-value">{week.value}</div>
            <div className="bar" style={{ height: `${(week.value / max) * PLOT_FILL}%` }} />
          </div>
        ))}
      </div>
      <div className="chart-axis">
        {weeks.map((week) => (
          <span key={week.week}>{week.week.replace("-W", " s")}</span>
        ))}
      </div>
    </div>
  )
}
