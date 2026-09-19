import type { Series } from "./api"
import { label, type Copy } from "./copy"

const PLOT_FILL = 88

function Chart({ series, copy: c }: { series: Series; copy: Copy }) {
  const points = series.points
  const last = points[points.length - 1]
  const previous = points.length > 1 ? points[points.length - 2] : null
  const top = series.scale_max ?? Math.max(...points.map((p) => p.value), 1)
  const delta = previous ? last.value - previous.value : 0
  const better = series.lower_is_better ? delta < 0 : delta > 0

  return (
    <div className="series">
      <h3 className="series-title">
        {c.data(series.term)} · {label(c.measure, series.category)}
      </h3>
      <div className="series-change">
        {previous && (
          <>
            <span className="series-was">{previous.value}</span>
            <span className="series-arrow">→</span>
          </>
        )}
        <span className="series-now">{last.value}</span>
        <span className="series-unit">{label(c.unit, series.category)}</span>
      </div>
      <p className="series-verdict">
        {previous
          ? c.changeBy(Math.abs(delta), delta === 0 ? c.same : better ? c.better : c.worse)
          : c.onlyOneCall}
      </p>
      <div className="chart">
        <div className="gridline" style={{ top: 0 }} />
        <div className="gridline" style={{ top: "50%" }} />
        <div className="gridline" style={{ bottom: 0 }} />
        {points.map((point) => (
          <div className="chart-col" key={point.week}>
            <div className="bar-value">{point.value}</div>
            <div className="bar" style={{ height: `${(point.value / top) * PLOT_FILL}%` }} />
          </div>
        ))}
      </div>
      <div className="chart-axis">
        {points.map((point) => (
          <span key={point.week}>{c.day(point.day)}</span>
        ))}
      </div>
      {series.scale_max !== null && <p className="series-scale">{c.scaleNote(series.scale_max)}</p>}
    </div>
  )
}

export default function WeeklyChart({ series, copy: c }: { series: Series[]; copy: Copy }) {
  return (
    <div>
      <h2>{c.weeklyTitle}</h2>
      {series.length === 0 ? (
        <p className="empty">{c.noNumbers}</p>
      ) : (
        <div className="series-grid">
          {series.map((one) => (
            <Chart series={one} copy={c} key={one.category} />
          ))}
        </div>
      )}
    </div>
  )
}
