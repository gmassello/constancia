# Submission checklist

Every row needs evidence: a file path, a public URL or a video timestamp. A row without evidence is unfinished work.

## Deliverables

| Deliverable | Status | Evidence |
|---|---|---|
| Public repo, MIT license | todo | |
| Deployed app, public URL | todo | |
| Demo video under 5 min | todo | |
| Deck | todo | |

## Judging criteria

| Criterion | How we show it | Where the judge sees it | Status |
|---|---|---|---|
| Application of Technology | Universal-Streaming v3 live over a real phone call (µ-law 8 kHz, end-of-turn driven), Speech Understanding on the recording after hangup, and memory feeding `keyterms_prompt` for the next call | Live transcript on the panel; the key terms of each call at `GET /calls/{id}/keyterms` and in the panel; `app/stt.py`, `app/analysis.py`; video beat 3 | partial — live call waits on C1 |
| Business Value | 70% non-adherence in home rehab, subscription per professional, three verticals on one engine | Deck; `docs/INTENT.md` §3–§4 | todo |
| Originality | The agent recalls and acts on what the patient said weeks ago, with superseded facts retired and visible as a chain | Panel fact chain at `/` (the 7/10 struck through under the 4/10) and `GET /patients/{id}/chain`; video beat 5 | done offline |
| Presentation | Call 1 → call 2 with memory off → call 2 with memory on, same patient | The panel's **Llamar ahora** with the memory toggle, in `scripted` mode with no keys; video beats 3–5 | done offline |

## Definition of done (INTENT §13)

- [ ] Public GitHub repo, MIT license visible in the About section
- [ ] Deployed backend with public `/health` and panel, tested from another network
- [ ] Demo video under 5 minutes, captions burned in
- [ ] Deck submitted
- [ ] `make test` green
- [ ] `scripts/test_outbound.py` places a real call
- [ ] Week-1 → week-2 moment works live and in replay
- [ ] `video/reset.sh --check` all green
- [ ] Every row above has evidence
