import type { Series } from "./api"
import { label, type Copy } from "./copy"

const PLOT_FILL = 88
const INSET = 4

// ponytail: the tile plots at most a handful of weekly points, so the line is drawn in a stretched
// viewBox and the dots are positioned in percentages beside it, which keeps them round without
// measuring the box. Read the width and project once if this ever plots enough points to matter.
const across = (index: number, total: number) =>
  total < 2 ? 50 : INSET + (index / (total - 1)) * (100 - INSET * 2)

function Chart({ series, copy: c }: { series: Series; copy: Copy }) {
  const points = series.points
  const last = points[points.length - 1]
  const previous = points.length > 1 ? points[points.length - 2] : null
  const top = series.scale_max || Math.max(...points.map((p) => p.value), 1)
  const delta = previous ? last.value - previous.value : 0
  const better = series.lower_is_better ? delta < 0 : delta > 0
  const up = (point: { value: number }) => Math.min(point.value / top, 1) * PLOT_FILL
  const line = points
    .map((point, index) => `${across(index, points.length)},${100 - up(point)}`)
    .join(" ")

  return (
    <div className="series">
      <h3 className="series-title">
        {c.data(series.term)} · {label(c.measure, series.category)}
      </h3>
      <div className="series-change">
        {previous && (
          <>
            <span className="series-was">{previous.value}</span>
            <span className={`series-arrow ${delta === 0 ? "flat" : better ? "good" : "bad"}`}>
              {delta === 0 ? "→" : delta > 0 ? "↑" : "↓"}
            </span>
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
      <div className="spark">
        <svg
          className="spark-line"
          viewBox="0 0 100 100"
          preserveAspectRatio="none"
          aria-hidden="true"
        >
          <polyline points={line} vectorEffect="non-scaling-stroke" />
        </svg>
        {points.map((point, index) => (
          <span
            className="spark-dot"
            key={point.week}
            style={{ left: `${across(index, points.length)}%`, bottom: `${up(point)}%` }}
          >
            <span className="spark-value">{point.value}</span>
          </span>
        ))}
      </div>
      <div className="chart-axis">
        {points.map((point, index) => (
          <span key={point.week} style={{ left: `${across(index, points.length)}%` }}>
            {c.day(point.day)}
          </span>
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
