# Submission checklist

Every row needs evidence: a file path, a public URL or a video timestamp. A row without evidence is unfinished work.

## Deliverables

| Deliverable | Status | Evidence |
|---|---|---|
| Public repo, MIT license | **done** | <https://github.com/gmassello/constancia> — public, MIT, [`LICENSE`](../LICENSE) at the root |
| Deployed app, public URL | todo | Waits on the Render deploy ([`PLAN.md`](PLAN.md) stage 4, step 1). The hostname `render.yaml` claims is `constancia-voice.onrender.com`; plain `constancia` is an unrelated app |
| Demo video under 5 min | in progress | Written, not shot: shot list [`video-script.md`](video-script.md) with the day's order and the three rehearsals, narration [`../video/narration.tsv`](../video/narration.tsv) measured in `video/out/timing.txt` against the 5:00 cap, state check `bash video/reset.sh --check` |
| Deck | **done** | [`deck.md`](deck.md) is the source; the slides are at <https://claude.ai/artifact/CiJaArPDziaaLZR6JWUMb1> and **have to be shared before submitting** |

## Judging criteria

| Criterion | How we show it | Where the judge sees it | Status |
|---|---|---|---|
| Application of Technology | Universal-Streaming v3 live over a real phone call (µ-law 8 kHz, end-of-turn driven), Speech Understanding on the recording after hangup, and memory feeding `keyterms_prompt` for the next call | Live transcript on the panel; the key terms of each call at `GET /calls/{id}/keyterms` and in the panel; `app/stt.py`, `app/analysis.py`; video beat 3 | done — C1 closed on a real call: six phases, both sides in the trace, Speech Understanding on the recording |
| Business Value | 70% non-adherence in home rehab, subscription per professional, three verticals on one engine | The landing at `/`: the metrics band carries the number and the **model band** (`#business`) carries who pays, what it costs and what it costs to run; [`deck.md`](deck.md) slides 2 and 8; [`INTENT.md`](INTENT.md) §3–§4 | done — the deck exists, the deploy does not |
| Originality | The agent recalls and acts on what the patient said weeks ago, with superseded facts retired and visible as a chain | Panel fact chain at `/` (the 7/10 struck through under the 4/10) and `GET /patients/{id}/chain`; video beat 5 | done offline |
| Presentation | Call 1 → call 2 with memory off → call 2 with memory on, same patient | The landing at `/` explains it before the demo runs; the panel's **Call now** with the memory toggle, in `scripted` mode with no keys; video beats 3–5 | done offline |

## Definition of done (INTENT §13)

- [x] Public GitHub repo, MIT license visible in the About section
- [ ] Deployed backend with public `/health` and panel, tested from another network
- [ ] Demo video under 5 minutes, captions burned in
- [ ] Deck submitted — written; the artifact has to be shared and uploaded to lablab
- [x] `make test` green — 174 tests, no environment variable set; the ones that need a database skip themselves
- [x] `scripts/test_outbound.py` places a real call — subsumed by C1: a full live call went out, which is the geographic permission proved end to end rather than with a `<Say>`
- [ ] Week-1 → week-2 moment works live and in replay — replay is green (`seed/replay/week2-on.json`, and the panel's buttons). **Live is not closed**: C1 is, C2 is not. C2 needs the three calls back to back with no reset, which is [`video-script.md`](video-script.md) §*The day, in order*, step 1 — it happens during the recording session
- [ ] C3 — the panel during a live call: transcript, rail with the highlight, the chain, the chart. Closes in the same session, because that is when the panel is on camera
- [ ] `video/reset.sh --check` green where it can be — the seed invariants, the Gemini quota and the tunnel. The credentials and `DEMO_PHONE` rows stay red until `.env` is filled, which is on purpose and is not a failing gate
- [x] `make test` green against a real Postgres too — `make db` and `DATABASE_URL=…`: 174 passed, nothing skipped
- [ ] Every row above has evidence
