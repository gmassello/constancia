# Documentation

Start here. The repo carries four kinds of document and mixing them up wastes time:

- **Reference** describes the system as it is today, in the present tense. If it disagrees with the
  code, it is a bug.
- **Record** describes what was intended or what happened. Written at a point in time, kept because
  the reasoning is worth having. It is not a description of the present.
- **Tracker** describes what is true right now and is expected to change: what is done
  ([`SUBMISSION.md`](SUBMISSION.md)) and what is not ([`PENDINGS.md`](PENDINGS.md)).
- **Target** describes what the system is meant to become. One document, [`DESIGN.md`](DESIGN.md),
  and it is the one place where disagreeing with the code is not a bug — the gap is tracked instead.

## I want to…

| | Read |
|---|---|
| understand what this product is and who pays for it | [`PRODUCT.md`](PRODUCT.md) |
| understand how a call works, end to end | [`ARCHITECTURE.md`](ARCHITECTURE.md) |
| change something in `app/` | [`BACKEND.md`](BACKEND.md) |
| change something in `web/` | [`FRONTEND.md`](FRONTEND.md) |
| call the API, or add a route | [`API.md`](API.md) |
| run it, get keys working, or deploy it | [`OPERATIONS.md`](OPERATIONS.md) |
| run the tests, or know what the conventions are | [`WORKING.md`](WORKING.md) |
| know **why** something was built this way | [`PLAN.md`](PLAN.md), the deviation register at the top |
| change a colour, a size or a component | [`DESIGN.md`](DESIGN.md) for the intent, [`FRONTEND.md`](FRONTEND.md) for what is there |
| know why the landing looked like that before | [`LANDING.md`](LANDING.md) |
| know what is left to do, and pick the work back up | [`PENDINGS.md`](PENDINGS.md) |
| know what the hackathon asked for | [`HACKATHON.md`](HACKATHON.md), [`SUBMISSION.md`](SUBMISSION.md) |
| shoot the demo video | [`video-script.md`](video-script.md) |
| pitch it, or reuse the claims | [`deck.md`](deck.md) |

## Reference

| File | Covers |
|---|---|
| [`PRODUCT.md`](PRODUCT.md) | The problem, who buys it, what the patient hears, the three verticals, what the professional sees. No jargon. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | One call end to end, the six phases, the three modes, how memory and supersession work, and the system's limits. |
| [`BACKEND.md`](BACKEND.md) | The eighteen modules, the four pieces worth reading first, configuration and the import-time rule. |
| [`FRONTEND.md`](FRONTEND.md) | Build and serving, the token rule and its gate, the bilingual machinery, the panel's components — the front end **as it stands**, which is what to check before assuming a piece of [`DESIGN.md`](DESIGN.md) is built. |
| [`API.md`](API.md) | All twenty routes, the Twilio webhooks and the SSE contract. |
| [`OPERATIONS.md`](OPERATIONS.md) | The three ways to run it, every environment variable, the database, Docker and Render. |
| [`WORKING.md`](WORKING.md) | The Makefile, the four gates, why the tests never touch the network, the conventions, and how to add things. |

## Target

One document, and the only one in the repo allowed to describe something that does not exist yet.

| File | What it is |
|---|---|
| [`DESIGN.md`](DESIGN.md) | **Cadence**, the design system as it is meant to become: every token in both themes with its measured contrast, the type scale, the components and their states, the two effects, and the rules a change has to obey. The colour tokens are live; a good part of the rest is not. Each section says which, and the gap is a numbered programme in [`PENDINGS.md`](PENDINGS.md). `design-preview.html` beside it shows the whole target on one page, and is not part of the product. |

## Record

Three here, plus `deck.md` and `video-script.md` in the table below. None of them is a description
of the present. Read them for reasoning, not for facts about the code.

| File | What it is | Written |
|---|---|---|
| [`INTENT.md`](INTENT.md) | The **pre-code specification**. Market research with citations, the business case, and the design contract. Its last section is called *Before writing code* — which is when it was written. Where it and the code disagree, the code is right and [`PLAN.md`](PLAN.md)'s deviation register usually says why. | 2026-09-02 |
| [`PLAN.md`](PLAN.md) | The four-stage build order, the four human checkpoints, and — at the top, lines 26 to 68 — **the deviation register**: twenty numbered entries recording what was built differently from `INTENT.md` and why. That register is the real decision log of this project. | during the build |
| [`LANDING.md`](LANDING.md) | Written as a spec for one piece of work, half-converted into a log, and superseded as a palette by [`DESIGN.md`](DESIGN.md). What survives is the method: how a light theme is derived and measured rather than mirrored, and the design of the copy types. | stage 4 |

## Hackathon

| File | What it is |
|---|---|
| [`HACKATHON.md`](HACKATHON.md) | **Reference**, and static: the rules and judging criteria, transcribed from lablab.ai. It tracks nothing. |
| [`SUBMISSION.md`](SUBMISSION.md) | **Tracker.** What is done, with the evidence for it. Nothing open lives here. |
| [`PENDINGS.md`](PENDINGS.md) | **Tracker.** Everything open, in one place: the submission, the Cadence build programme, the decisions it needs, and what is deliberately not being done. Start here to pick the work back up. |
| [`deck.md`](deck.md) | **Record.** The content of the slides, kept next to the code that backs each claim. Written, not yet submitted. |
| [`video-script.md`](video-script.md) | **Record**, and it says so in its own first lines: how the video is meant to be shot. Seven beats, what the camera sees, what the human says on the phone, and both ways to shoot each call. If the take comes out different, the take wins. Its narration is [`../video/narration.tsv`](../video/narration.tsv). |

## For agents

The rules live in `AGENTS.md` files, which most coding agents read on their own. Three of them,
deliberately small:

- [`../AGENTS.md`](../AGENTS.md) — the hard rules, always in context.
- [`../app/AGENTS.md`](../app/AGENTS.md) — applies to the backend.
- [`../web/AGENTS.md`](../web/AGENTS.md) — applies to the front end.

None of them restates the others. They carry rules, not explanations; the explanation is in the
reference document each one points at.

Each directory also has a one-line `CLAUDE.md` pointing at its `AGENTS.md`, so Claude Code picks the
same rules up without a second copy to keep in sync.
