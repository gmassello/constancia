# Documentation

Start here. The repo carries two kinds of document and mixing them up wastes time:

- **Reference** describes the system as it is today, in the present tense. If it disagrees with the
  code, it is a bug.
- **Record** describes what was intended or what happened. Written at a point in time, kept because
  the reasoning is worth having. It is not a description of the present.

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
| know why the landing looks like that | [`LANDING.md`](LANDING.md) |
| know what the hackathon asked for | [`HACKATHON.md`](HACKATHON.md), [`SUBMISSION.md`](SUBMISSION.md) |
| shoot the demo video | [`video-script.md`](video-script.md) |
| pitch it, or reuse the claims | [`deck.md`](deck.md) |

## Reference

| File | Covers |
|---|---|
| [`PRODUCT.md`](PRODUCT.md) | The problem, who buys it, what the patient hears, the three verticals, what the professional sees. No jargon. |
| [`ARCHITECTURE.md`](ARCHITECTURE.md) | One call end to end, the six phases, the three modes, how memory and supersession work, and the system's limits. |
| [`BACKEND.md`](BACKEND.md) | The eighteen modules, the four pieces worth reading first, configuration and the import-time rule. |
| [`FRONTEND.md`](FRONTEND.md) | Build and serving, the design system and its gate, the bilingual machinery, the panel's components. |
| [`API.md`](API.md) | All twenty routes, the Twilio webhooks and the SSE contract. |
| [`OPERATIONS.md`](OPERATIONS.md) | The three ways to run it, every environment variable, the database, Docker and Render. |
| [`WORKING.md`](WORKING.md) | The Makefile, the four gates, why the tests never touch the network, the conventions, and how to add things. |

## Record

Three documents, none of them a description of the present. Read them for reasoning, not for facts
about the code.

| File | What it is | Written |
|---|---|---|
| [`INTENT.md`](INTENT.md) | The **pre-code specification**. Market research with citations, the business case, and the design contract. Its last section is called *Before writing code* — which is when it was written. Where it and the code disagree, the code is right and [`PLAN.md`](PLAN.md)'s deviation register usually says why. | 2026-09-02 |
| [`PLAN.md`](PLAN.md) | The four-stage build order, the four human checkpoints, and — at the top, lines 21 to 62 — **the deviation register**: twenty numbered entries recording what was built differently from `INTENT.md` and why. That register is the real decision log of this project. | during the build |
| [`LANDING.md`](LANDING.md) | Written as a spec for one piece of work, half-converted into a log. Contains the densest technical content in the repo: the OKLCH derivation of the light theme with measured contrast ratios, and the design of the copy types. | stage 4 |

## Hackathon

| File | What it is |
|---|---|
| [`HACKATHON.md`](HACKATHON.md) | The rules and judging criteria, transcribed from lablab.ai. Static reference. |
| [`SUBMISSION.md`](SUBMISSION.md) | The deliverables tracker. Every row needs evidence: a path, a URL or a video timestamp. |
| [`deck.md`](deck.md) | The content of the submitted slides, kept next to the code that backs each claim. |
| [`video-script.md`](video-script.md) | The shot list: seven beats, what the camera sees, what the human says on the phone, and both ways to shoot each call. Its narration is [`../video/narration.tsv`](../video/narration.tsv). |

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
