# Pending

Open work only, and all of it. Every row says **what is open**, **who closes it** and **the command
or step that closes it**. Anything not on this page is done and carries its evidence in
[`SUBMISSION.md`](SUBMISSION.md).

Deadline: **30 Sep 2026, 12:00 ART** ([`HACKATHON.md`](HACKATHON.md)). Last reviewed: **2026-09-24**.

Four parts: what blocks the submission, the Cadence build programme, the decisions that programme
needs, and what the six new features left behind alongside what is deliberately not being done.

---

## 1. The submission

Two of the four mandatory deliverables are missing, and they are the same critical path: the public
URL and the video.

| | What is open | Who | How it closes |
|---|---|---|---|
| 1 | **Render deploy.** `curl https://constancia-voice.onrender.com/health` answers `404` with `x-render-routing: no-server`: the service does not exist | you | The six-step runbook in [`OPERATIONS.md`](OPERATIONS.md) § *The order*. Unblocks the README's public URL, the endcard, and three rows of `SUBMISSION.md` |
| 2 | **The endcard URL.** `video/endcard.sh:4` burns `constancia-voice.onrender.com` as its default, and that hostname 404s. A dead address on the last frame is worse than none, and `build-audio.sh` wiped the rendered `video/out/endcard.png`, so it has to be re-rendered either way | you | Decide before `bash video/endcard.sh` runs: either the deploy lands first, or the card points at the GitHub repo. It is spliced in at assembly, so it does not block the take |
| 3 | **Ana's voice.** Anita is not available, so the patient's lines are synthesised: [`video/lines.html`](../video/lines.html) shows the 21 turns of the four calls, verbatim from `seed/scripts.json`, and speaks them in English through the browser. The page exists; what is open is the calibration | you | Open it, pick a voice that is **not** `Ava (Premium)` — that one is the narration's, and the patient would sound like the narrator — then test the acoustic coupling in rehearsal 1: laptop speaker against the phone's microphone, phone **not** on speaker, or the agent's own voice feeds back into the call. If a number comes out mis-transcribed, pre-render the lines with `say` instead |
| 4 | **The cold open.** `video/hook.json` does not exist, and neither does the concept anywhere in the repo | me | **Blocked on you**: it needs one photograph with a clear licence for the scale shot. The other four shots are already in `video/shots/`. Droppable at no cost |
| 5 | **The three rehearsals and the take.** Closes **C2** and **C3** | you and me | [`video-script.md`](video-script.md) § *The day, in order*. The order is not negotiable: the three calls back to back come **before** the final reset, never after |
| 6 | **Assemble `demo.mp4`.** None of `raw-fitted.mov`, `demo.mp4` or `demo.en.srt` exist. The 20 Sep take is split across `raw-parte1.mov` and `raw-parte2.mov`, which the documented pipeline does not contemplate | me, after the take | `fit-to-audio.py --beats`, then `build-video.sh` with `OUTRO="video/out/endcard.png:5" OUTRO_REPLACE=2.4`. The track is 267.8 s, so the finished file lands under the 300 s cap |
| 7 | **Share the deck and submit on lablab** | you | The artifact is linked from [`SUBMISSION.md`](SUBMISSION.md); it has to be shared before it can be uploaded |
| 8 | **The GitHub shop window, homepage only.** The description is set — the README's own first sentence — and ten topics are on (`assemblyai`, `voice-agent`, `speech-to-text`, `text-to-speech`, `twilio`, `elevenlabs`, `fastapi`, `react`, `healthcare`, `hackathon`). `homepageUrl` is still empty | you or me, after row 1 | `gh repo edit --homepage <url>` once the deploy answers |

**The video is now shot after the features, not before.** Three of the six changed what the agent
says on the call, so `seed/scripts.json` and all four fixtures moved with them. What the panel's
buttons show that they did not a day ago: a promise made in week 1 and asked about in week 2, a
read-back of a number the recogniser was unsure of, an answer from the professional spoken word for
word in the greeting, and a new question landing in the queue.

**[`video-script.md`](video-script.md) is corrected.** Its three patient-line tables now match
`seed/scripts.json` turn for turn — beat 3 with the promise and the conditional read-back, beat 5 with
the promise answer and the stairs question — and the session it describes is the one that is actually
possible: you answer the phone and [`video/lines.html`](../video/lines.html) speaks the lines.

**The narration is written against that behaviour and built.** `video/narration.tsv` carries 53
captions in 74 rows; `build-audio.sh` measured **267.8 s = 4:27.8** against the 300 s cap with zero
drift, and `OUTRO_REPLACE` re-derives to `2.4`. Beat 3 says *three* facts, and beat 5 narrates the
relayed answer, the promise check-in and the question that lands in the queue. The one constraint
that leaves for row 5: the raw screen recording has to run between **3:19 and 5:45**, or
`build-video.sh` refuses it.

**Checkpoints.** C1 is closed. **C2** (three real calls back to back, no reset, the third superseding
the 7/10) and **C3** (the panel live during a call) close during the recording session — row 5.
**C4** is the submission itself. Their definitions are in [`PLAN.md`](PLAN.md).

---

## 2. The Cadence build programme

[`DESIGN.md`](DESIGN.md) is the **target** design system, not a description of what is built. What it
defines and the front end does not have yet is this list, ordered by how visible it is.

**Group A and the panel's own set are built and out of this list.** Group A was the landing and the
live call card — the waveform, the animated counters, the static orbs. The second pass took the
panel: the pill geometry and its three variants, `CURRENT` / `RETIRED` as pills, the fact quote in
`mono`, the speaker label and the rail row on the type scale, the rail's timestamp, level 3 on the
live call card, the selected patient row, and the chart's sparkline tiles with a verdict arrow that
finally carries the direction. All of it was done before the take, because after the take it is
worth nothing.

**A correction, because it was published wrong here.** This section used to say *"None of what is
left shows up on camera"*. That was false: thirteen of the nineteen items were on camera, and four
of them were on the shot list's own *what the camera must catch*. What makes what is left droppable
is not that it is invisible — it is that **no caption depends on it**. Only three items are never on
screen at all: C3, F2 and F3.

**Honest sizing.** What is left is eleven items, there is no test runner in the front end, and it
competes with part 1 for the days that are left. Group C is the largest and, by the corrected
measure, the one the narration never names.

The gate for every item is `make web` (`tsc -b && vite build`) plus a look at both themes and both
languages, and contrast measured per theme.

### B. Components and states

| | What | Where |
|---|---|---|
| B1 | `[data-loading]` with a 14px spinner and the width preserved — zero matches in the repo today. And the real `disabled`: `--fill-subtle` / `--tone-dim` instead of `opacity: 0.45`, which is the one resource the rules discourage | `tokens.css` |
| B2 | Card at `--radius-lg` with `--space-6` padding and a hover that moves it to level 2. Today `.card` is `--radius-md` with 16px and has no hover rule. Level 2 is the one elevation step still unbuilt; level 3 landed on `.live` | `panel/panel.css:73` |

### C. The type scale

The largest item, and the one no caption names. Three of the thirteen steps now exist as classes —
`.eyebrow`, `.caption` and `.mono`, built because the pill, the speaker label and the rail row needed
them. The other ten do not, and every size outside those three is still a literal in px.

| | What | Where |
|---|---|---|
| C1 | Define the remaining **ten** steps as classes in `tokens.css` — `display-xl` through `button`. `.eyebrow`, `.caption` and `.mono` are built | `tokens.css` |
| C2 | Replace every loose px size with them. This is what makes the rule *"display type never below `card-title`"* enforceable: there are seven violations today, from 12px to 20px | `landing/Landing.tsx`, `landing/DemoCard.tsx`, `panel/panel.css`, `panel/Keyterms.tsx` |
| C3 | Fonts: move the `@import` at `tokens.css:1` to the two `<link rel="preconnect">` plus the stylesheet link the doc publishes, in both HTML heads — today the import blocks the CSS and there is no preconnect. Resolve Inter 700, which is downloaded and not declared | `web/index.html`, `web/panel/index.html`, `tokens.css` |

### D. Layout and elevation

| | What | Where |
|---|---|---|
| D1 | Container at 1280px (1180 today), 16px minimum gutter (20 today), prose capped at `68ch`, and the published section-padding clamp | `landing/Landing.tsx`, `landing/landing.css`, `panel/panel.css:70` |
| D4 | Nav: 64px tall, background at 85%, `blur(12px)`, the bottom border appearing only on scroll, and the current section in `--color-accent` with a 2px underline. Today the border is unconditional and there is no current-section state | `landing/landing.css:65`, `landing/Landing.tsx` |

### E. Panel

| | What | Where |
|---|---|---|
| E1 | Call controls: six buttons in two rows with the live pair as `btn-primary`. Today there are **seven in three rows** and the live pair is secondary + primary. Decision 4 is settled, so the three `btn-ghost` ones stay ghost and this is a layout change only | `panel/PatientView.tsx:92-129` |

### F. Rules and cleanup

| | What | Where |
|---|---|---|
| F1 | *"Do not animate anything except the two effects above."* `landing.css` defines five keyframes and `panel.css` a sixth, `@keyframes flash` at `panel.css:354-357`. A3 removed the awkward one: `noc-breathe` looped on the two background blooms and `.is-paused` never covered it. The two that loop now, `noc-pulse` and `noc-wave`, are both the demo card's and both pause with it. What is left is deciding whether the four entrance animations survive the rule at all | `landing/landing.css`, `panel/panel.css` |
| F2 | `--color-accent-2` is declared in both themes and used nowhere, while the rules forbid a second accent. Give it a use or remove it | `tokens.css:10,81` |
| F3 | After each change, contrast measured per theme by compositing on a canvas — `getComputedStyle` returns `color(srgb …)` for `color-mix()` values | — |

---

## 3. Decisions the programme needs

Four questions `DESIGN.md` did not answer. They are not tasks; nothing above them could be built
until they were settled, and all four now are — kept here because each one records why the code and
the doc disagreed.

1. ~~**Where does the waveform's level come from?**~~ **Settled: synthesised from turn state, and
   `DESIGN.md` says so.** The server does hold the audio — µ-law frames at `app/channel.py:131-136`
   and `:177-189` — so the blocker was never that nobody has it. It is that the trace the SSE stream
   reads is a `deque(maxlen=500)` (`app/calls.py:9,36`) sized for the twenty semantic events a call
   emits: ten levels a second would evict the events the activity rail is made of, and the four
   `seed/replay/*.json` fixtures would show a flat wave beside a moving live one. So `web/src/panel/
   Wave.tsx` gates synthesised noise on who holds the floor and says as much in a `ponytail:` marker
   and in `DESIGN.md` § *Effects*. A measured level stays the upgrade path and needs a carrier that is
   not the trace.
2. ~~**The metrics band.**~~ **Settled: the code wins and `DESIGN.md` was corrected.** The doc put
   the band on `--fill-subtle`; the code has a dark teal band from `--color-section` to
   `--color-section-glow` with `--section-ink` on top. Building the doc would have retired three
   tokens and removed the landing's only high-contrast block — the one the animated counters sit on.
   `--section-ink` is declared identically in both themes precisely because that band is dark in
   both, which is the argument the doc was missing.
3. ~~**The `.input` component.**~~ **Settled.** The question queue needed somewhere for the
   professional to type an answer, so `.input` now exists in `panel/panel.css` and is used by
   `panel/Questions.tsx`. It has a base, a focus ring and a placeholder, not the five states
   `DESIGN.md` specifies and not the `aria-describedby` error pattern; that gap moves into group B
   above rather than staying a question.
4. ~~**`.btn-ghost`.**~~ **Settled: it joins the table.** It existed, it was used three times in the
   panel, and the component table did not name it while a rule forbids components the system does
   not name — so the rule was being broken by the doc's omission, not by the code. It is now
   specified in `DESIGN.md` § *Components* with its hover and press washes. Zero visual change, and
   E1 shrinks to a layout change.

---

## 4. What the six new features left, and what stays out

**Done, and no longer optional.** All six features in
[`NEW_FEATURES.md`](NEW_FEATURES.md) are built, tested and visible in the panel's scripted buttons.
That file is now the record of where each one came from, not a plan. What each one left open:

| | Feature | What is still open |
|---|---|---|
| 1 | Out-of-range values | Nothing. The ceiling comes from the pack's own `Measure`, so a vertical with an unbounded reading is not capped — which is correct, not a gap. |
| 2 | Commitments | **Closed for what a vertical can enumerate.** The action vocabulary moved out of `app/commitments.py` and into `pack.actions`, beside the red flags and the measures, so a postpartum or chronic promise is now scored deterministically by its own pack with no key and no network — in `make test`, `make demo`, `make fixtures` and the recording session alike. Three rules stay generic English in `commitments.py`; only the action is per vertical. `JEV_FLOOR` was re-measured on 24 Sep against the code as it stands: four everyday plans at 0.01 to 0.03 against four promises about the patient's own care at 0.06, 0.15, 0.85 and 0.89, so 0.8 keeps a 0.77 margin and misses two genuine promises it reads as ordinary life. What is open: **recall is roughly half** on that sample, and the sample is eight sentences. Sharpening the question is what opened the gap at all — the first wording scored *"I will call my brother tonight"* at 0.83 against a real promise at 0.49 — so the wording, not the floor, is the knob that matters next. Also open: Zero Data Retention is a Pro tier and this is a hobby plan, so `JEV_ZERO_RETENTION` defaults off and the sentence falls under the gateway's ordinary retention. Asking for it anyway is a 403 on every call, which is how we found out. |
| 3 | The critic | The fifth rule the source design asked for — that the reply share a word with its goal — is **deliberately not built**: a goal here is one clause, so a legitimate recall question shares nothing with it and gets flagged. Measure the other four with `make smoke-call` before trusting them on a real line. |
| 4 | Low-confidence read-back | **`words[].confidence` on a v3 `Turn` is still unverified.** The code treats a missing field as certain, so the read-back is off until a real call proves it arrives. `STT_CONFIDENCE_FLOOR` then needs calibrating on µ-law audio. |
| 5 | Audio behind a quote | Cannot be shown offline: `scripted` and `replay` have no recording, so no quote in the demo has a play button. `/calls/{id}/audio` serves the whole mp3 with no `Range` support. |
| 6 | The question queue | The answer is relayed in the greeting of the **next** call, so the loop takes two calls to close. `wants_human` flags the call and nothing acts on the flag yet beyond the trace and `call_ended`. |

**Deliberately out of scope.** Decided, and not to be reopened without saying so:

- Re-recording `seed/replay/*.json` from real calls — the fixtures stay synthetic.
- Deleting the 20 Sep takes. They stay on disk.
- A test runner in the front end. `tsc` is the check; presentational components do not earn one.
- The hash-chained audit log (`INTENT.md` §12).
- Authentication. The README's warning is the honest version.
- **Jev anywhere but the promise rules.** Three other places were considered and dropped: the critic
  (`app/critic.py`), where the fifth rule it would restore sits in the speech path and 500 ms of p99
  is an audible pause on a phone line; ordering the professional's question queue by urgency; and a
  second net behind the red-flag guard. The guard stays deterministic code either way — that rule is
  not up for a second opinion.
- **Jev's probability as the stored confidence.** Its own README asks for calibration against your
  own data first, so `DEADLINE` and `HEDGE` still set the number.
