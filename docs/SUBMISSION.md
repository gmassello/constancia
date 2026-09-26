# Submission checklist

What is **done**, with its evidence: a file path, a command, a public URL or a video timestamp. A row
without evidence is unfinished work, and unfinished work lives in [`PENDINGS.md`](PENDINGS.md), which
says who closes it and how. This page does not repeat it.

## Deliverables

| Deliverable | Status | Evidence |
|---|---|---|
| Public repo, MIT license | **done** | <https://github.com/gmassello/constancia> — public, MIT, [`LICENSE`](../LICENSE) at the root |
| Deployed app, public URL | **done** | <https://constancia-voice.onrender.com> — the landing at `/`, the panel at `/panel`, `/health` answering `{"status":"ok","calls":0,"store":"postgres","live":true,"dialable":false}` from another network on 25 Sep, and `/patients` serving the seeded Ana |
| Demo video under 5 min | in progress | Shot list and the day's order in [`video-script.md`](video-script.md), narration in [`../video/narration.tsv`](../video/narration.tsv). The narration track is built (267.8 s); what is left is the take and the assembly: [`PENDINGS.md`](PENDINGS.md) rows 1–2 |
| Deck | in progress | [`deck.md`](deck.md) is the source and the slides are built; sharing the artifact and uploading it is [`PENDINGS.md`](PENDINGS.md) row 3 |

## Judging criteria

The evidence column is what a judge can open **today**: a path in this repo, a command that runs
with no credentials, or the deployed service at <https://constancia-voice.onrender.com>. What the public URL cannot show is
the half that needs a phone — the live call is C2, in the recording session.

| Criterion | How we show it | Where it can be checked now | Status |
|---|---|---|---|
| Application of Technology | Universal-Streaming v3 live over a real phone call (µ-law 8 kHz, end-of-turn driven), Speech Understanding on the recording after hangup — entity detection, sentiment **and key phrases** — memory feeding `keyterms_prompt` for the next call, per-word confidence driving a targeted read-back, and the recording's word timings anchoring every stored quote to the second it was said. Handing those key phrases back as the next call's `keyterms_prompt` was built and then **measured against a real recording and reverted** (`scripts/keyphrases-measured.json`, 26 Sep): the phrases come off the whole recording, so they carried the agent's own questions, common words the API warns cause overcorrections, and the patient's name as the recogniser mis-heard it — priming with that would reinforce the error every week. The panel still shows them; the recogniser is not fed them. A feature measured and taken back out is evidence the numbers here are real | [`app/stt.py`](../app/stt.py), [`app/analysis.py`](../app/analysis.py), [`app/channel.py`](../app/channel.py), `keyterms()` in [`app/memory.py`](../app/memory.py); `make demo` runs the pipeline end to end with no keys; `GET /calls/{id}/keyterms`; the panel's *What AssemblyAI heard in the recording* card | **proved live** — C1 closed on a real call: six phases, both sides in the trace, Speech Understanding on the recording |
| Business Value | 70% non-adherence in home rehab, a subscription per professional, three verticals on one engine | The model band (`#business`) and the metrics band on the landing — `make web && make dev`, then `localhost:8001`; [`deck.md`](deck.md) slides 2 and 8; [`INTENT.md`](INTENT.md) §3–§4 with citations | **written**, and demonstrable on the public URL as well as locally |
| Originality | The agent recalls and **acts on** what the patient said weeks ago: a promise made in week 1 is asked about in week 2 and retired by what actually happened, and a question the agent refused to answer comes back in the next call's greeting in the professional's own words. Recognising the promise is deterministic, and where its vocabulary runs out — a postpartum or chronic promise rather than a rehab one — Jev answers the same question and the deterministic rules still set the score | The panel at `/panel`, *Call with memory* — the 7/10 struck through under the 4/10, the promise retired by what she managed, and the answered question read out in the greeting; `GET /patients/{id}/chain`, `GET /patients/{id}/questions`; `make demo MEMORY=on`. The second opinion: `make smoke-jev`, four promises the rehab vocabulary cannot see rescued at 0.83–0.92 against four non-promises at 0.02–0.08 | **proved offline**, deterministically and with no keys; the second opinion **measured** against the real model |
| Presentation | Call 1 → call 2 with memory off → call 2 with memory on, same patient | The landing explains it before the demo runs; the panel's four scripted buttons run it with no keys | **proved offline**; live is C2, during the recording session |

## Definition of done (INTENT §13)

- [x] Public GitHub repo, MIT license visible in the About section
- [x] `make test` green — 319 tests, no environment variable set; the ones that need a database skip themselves
- [x] `make test` green against a real Postgres too — `make db` and `DATABASE_URL=…`: 319 passed, nothing skipped
- [x] `scripts/test_outbound.py` places a real call — subsumed by C1: a full live call went out, which is the geographic permission proved end to end rather than with a `<Say>`
- [x] C1 — a real call greets, asks the four questions in order, honours barge-in, says goodbye, and the trace shows both sides
- [x] Deployed backend with public `/health` and panel, tested from another network — <https://constancia-voice.onrender.com>/health, answered from outside Render on 25 Sep
- [ ] Demo video under 5 minutes, captions burned in — [`PENDINGS.md`](PENDINGS.md) rows 1–2
- [ ] Deck shared and uploaded to lablab — [`PENDINGS.md`](PENDINGS.md) row 3
- [ ] C2 — week-1 → week-2 live: three calls back to back with no reset. Replay is already green (`seed/replay/week2-on.json` and the panel's buttons); live is [`PENDINGS.md`](PENDINGS.md) row 1
- [ ] C3 — the panel during a live call: transcript, rail with the highlight, the chain, the chart. Same session, [`PENDINGS.md`](PENDINGS.md) row 1
- [x] `video/reset.sh` green on all eleven invariants — the seed state, the credentials, `DEMO_PHONE`, both quotas and the tunnel, run on 26 Sep with `.env` filled and ngrok up, which is the first time the eleventh could be anything but red
- [ ] Every row above has evidence
