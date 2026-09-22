# Submission checklist

Every row needs evidence: a file path, a public URL or a video timestamp. A row without evidence is unfinished work.

## Deliverables

| Deliverable | Status | Evidence |
|---|---|---|
| Public repo, MIT license | **done** | <https://github.com/gmassello/constancia> — public, MIT, [`LICENSE`](../LICENSE) at the root |
| Deployed app, public URL | todo | Waits on the Render deploy ([`PLAN.md`](PLAN.md) stage 4, step 1). The hostname `render.yaml` claims is `constancia-voice.onrender.com`; plain `constancia` is an unrelated app |
| Demo video under 5 min | in progress | Written, not shot: shot list [`video-script.md`](video-script.md), narration [`../video/narration.tsv`](../video/narration.tsv) (3:34.6 measured against the 5:00 cap), state check `bash video/reset.sh --check` |
| Deck | **done** | [`deck.md`](deck.md) is the source; the slides are at <https://claude.ai/artifact/CiJaArPDziaaLZR6JWUMb1> and **have to be shared before submitting** |

## Judging criteria

| Criterion | How we show it | Where the judge sees it | Status |
|---|---|---|---|
| Application of Technology | Universal-Streaming v3 live over a real phone call (µ-law 8 kHz, end-of-turn driven), Speech Understanding on the recording after hangup, and memory feeding `keyterms_prompt` for the next call | Live transcript on the panel; the key terms of each call at `GET /calls/{id}/keyterms` and in the panel; `app/stt.py`, `app/analysis.py`; video beat 3 | done — C1 closed on a real call: six phases, both sides in the trace, Speech Understanding on the recording |
| Business Value | 70% non-adherence in home rehab, subscription per professional, three verticals on one engine | The landing at `/`, whose plain register states the case without jargon and whose metrics band carries the number; [`deck.md`](deck.md) slides 2 and 8; [`INTENT.md`](INTENT.md) §3–§4 | done — the deck exists, the deploy does not |
| Originality | The agent recalls and acts on what the patient said weeks ago, with superseded facts retired and visible as a chain | Panel fact chain at `/` (the 7/10 struck through under the 4/10) and `GET /patients/{id}/chain`; video beat 5 | done offline |
| Presentation | Call 1 → call 2 with memory off → call 2 with memory on, same patient | The landing at `/` explains it before the demo runs; the panel's **Call now** with the memory toggle, in `scripted` mode with no keys; video beats 3–5 | done offline |

## Definition of done (INTENT §13)

- [x] Public GitHub repo, MIT license visible in the About section
- [ ] Deployed backend with public `/health` and panel, tested from another network
- [ ] Demo video under 5 minutes, captions burned in
- [ ] Deck submitted — written; the artifact has to be shared and uploaded to lablab
- [x] `make test` green — 172 tests, no environment variable set; the ones that need a database skip themselves
- [ ] `scripts/test_outbound.py` places a real call
- [ ] Week-1 → week-2 moment works live and in replay — replay is green (`seed/replay/week2-on.json`, and the panel's buttons); live is closed too (C1 and C2)
- [ ] `video/reset.sh --check` all green — the seed invariants pass; the credentials and `DEMO_PHONE` checks are red until `.env` is filled, and they are red on purpose now that beats 3, 4 and 5 are live
- [ ] Every row above has evidence
