from datetime import datetime

from app.memory import keyterms
from app.packs import VerticalPack


def _at(value) -> datetime:
    return value if isinstance(value, datetime) else datetime.fromisoformat(str(value))


def _week(value) -> str:
    year, week, _ = _at(value).isocalendar()
    return f"{year}-W{week:02d}"


def chain(rows: list[dict]) -> list[dict]:
    predecessor = {str(row["superseded_by"]): row for row in rows if row.get("superseded_by")}
    out = []
    for row in rows:
        if row.get("superseded_by"):
            continue
        history, cursor = [], predecessor.get(str(row["id"]))
        while cursor is not None:
            history.append(cursor)
            cursor = predecessor.get(str(cursor["id"]))
        out.append({**row, "superseded": history})
    return out


def followed(rows: list[dict], category: str, term: str | None = None) -> list[dict]:
    # ponytail: a series is one supersession lineage, plus anything sharing a term with it.
    # Grouping by term alone breaks the moment the model names a fact "right knee pain" where
    # last week's was "right knee" — the chain still links them, so the chain is what decides.
    measured = [r for r in rows if r["category"] == category and r.get("value") is not None]
    if term is not None:
        return [r for r in measured if r["term"] == term]
    retired = {str(r["superseded_by"]): r for r in rows if r.get("superseded_by")}
    groups = []
    for head in measured:
        if head.get("superseded_by"):
            continue
        lineage, cursor = [head], retired.get(str(head["id"]))
        while cursor is not None:
            lineage.append(cursor)
            cursor = retired.get(str(cursor["id"]))
        ids = {str(r["id"]) for r in lineage}
        terms = {r["term"] for r in lineage}
        groups.append([r for r in measured if str(r["id"]) in ids or r["term"] in terms])
    return max(groups, key=lambda g: (len(g), g[0]["term"]), default=[])


def _points(rows: list[dict]) -> list[dict]:
    latest: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: _at(r["reported_at"])):
        latest[_week(row["reported_at"])] = row
    return [
        {
            "week": week,
            "day": str(latest[week]["reported_at"]),
            "value": float(latest[week]["value"]),
        }
        for week in sorted(latest)
    ]


def weekly(rows: list[dict], pack: VerticalPack, term: str | None = None) -> list[dict]:
    series = []
    for measure in pack.measures:
        tracked = followed(rows, measure.category, term)
        if not tracked:
            continue
        points = _points(tracked)
        if not points:
            continue
        newest = max(tracked, key=lambda r: _at(r["reported_at"]))
        series.append(
            {
                "category": measure.category,
                "term": newest["term"],
                "scale_max": measure.scale_max,
                "lower_is_better": measure.lower_is_better,
                "points": points,
            }
        )
    return series


def keyterms_at(rows: list[dict], when, pack: VerticalPack) -> list[str]:
    moment = _at(when)
    live = [
        row
        for row in rows
        if _at(row["reported_at"]) < moment
        and (row["valid_until"] is None or _at(row["valid_until"]) > moment)
    ]
    return keyterms(live, pack)
