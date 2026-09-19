import type { Week } from "./api"
import type { Copy } from "./copy"

const PLOT_FILL = 88

export default function WeeklyChart({ weeks, copy: c }: { weeks: Week[]; copy: Copy }) {
  if (weeks.length === 0) {
    return <p className="empty">{c.noNumbers}</p>
  }
  const max = Math.max(...weeks.map((week) => week.value), 1)
  const axis = (iso: string) => {
    const [year, week] = iso.split("-W")
    return c.weekLabel(year, week)
  }

  return (
    <div>
      <div className="chart-head">
        <h2>{c.weeklyTitle}</h2>
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
          <span key={week.week}>{axis(week.week)}</span>
        ))}
      </div>
    </div>
  )
}
