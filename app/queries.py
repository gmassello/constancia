from datetime import datetime

from app.memory import keyterms
from app.packs import VerticalPack

CHART_CATEGORIES = ("symptom", "clinical_value")


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


def tracked_term(rows: list[dict]) -> str | None:
    counts: dict[str, int] = {}
    for row in rows:
        if row.get("value") is not None and row["category"] in CHART_CATEGORIES:
            counts[row["term"]] = counts.get(row["term"], 0) + 1
    return max(counts, key=lambda term: (counts[term], term)) if counts else None


def weekly(rows: list[dict], term: str | None = None) -> list[dict]:
    term = term or tracked_term(rows)
    if term is None:
        return []
    latest: dict[str, dict] = {}
    for row in sorted(rows, key=lambda r: _at(r["reported_at"])):
        if row["term"] == term and row.get("value") is not None:
            latest[_week(row["reported_at"])] = row
    return [
        {"week": week, "value": float(latest[week]["value"]), "term": term}
        for week in sorted(latest)
    ]



def keyterms_at(rows: list[dict], when, pack: VerticalPack) -> list[str]:
    moment = _at(when)
    live = [
        row
        for row in rows
        if _at(row["reported_at"]) < moment
        and (row["valid_until"] is None or _at(row["valid_until"]) > moment)
    ]
    return keyterms(live, pack)
