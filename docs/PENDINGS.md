# Pending

Open work only, and all of it. Every row says **what is open**, **who closes it** and **the command
or step that closes it**. Anything not on this page is done and carries its evidence in
[`SUBMISSION.md`](SUBMISSION.md).

Deadline: **30 Sep 2026, 12:00 ART** ([`HACKATHON.md`](HACKATHON.md)). Last reviewed: **2026-09-23**.

Four parts: what blocks the submission, the Cadence build programme, the decisions that programme
needs, and what the six new features left behind alongside what is deliberately not being done.

---

## 1. The submission

Two of the four mandatory deliverables are missing, and they are the same critical path: the public
URL and the video.

| | What is open | Who | How it closes |
|---|---|---|---|
| 1 | **Render deploy.** `curl https://constancia-voice.onrender.com/health` answers `404` with `x-render-routing: no-server`: the service does not exist | you | The six-step runbook in [`OPERATIONS.md`](OPERATIONS.md) § *The order*. Unblocks the README's public URL, the endcard, and three rows of `SUBMISSION.md` |
| 2 | **The endcard URL.** `video/endcard.sh:4` burns `constancia-voice.onrender.com` as its default, and that hostname 404s. A dead address on the last frame is worse than none | you | Decide before rendering the card: either the deploy lands first, or the card points at the GitHub repo |
| 3 | **The narration track is stale.** `video/narration.tsv` is from 22 Sep 21:03; `narration.wav`, `captions.srt`, `clips/`, `sil/` and `timing.txt` are from 20 Sep 02:07 — 44 captions against 45 rows. Beat 1 lost a line and beat 6 gained the two AssemblyAI ones. Every number in `timing.txt` is wrong, and `OUTRO_REPLACE=2.4` with it | me | `build-audio.sh` (it wipes `video/out/` first, so re-render the endcard after). Gate: `video/out/timing.txt` says `HARD CAP 5:00 — OK`. Then re-derive `OUTRO_REPLACE` with the snippet in [`video-script.md`](video-script.md) beat 7 |
| 4 | **Ana's voice.** Anita is not available, so the patient's lines are synthesised: [`video/lines.html`](../video/lines.html) shows the 21 turns of the four calls, verbatim from `seed/scripts.json`, and speaks them in English through the browser. The page exists; what is open is the calibration | you | Open it, pick a voice that is **not** `Ava (Premium)` — that one is the narration's, and the patient would sound like the narrator — then test the acoustic coupling in rehearsal 1: laptop speaker against the phone's microphone, phone **not** on speaker, or the agent's own voice feeds back into the call. If a number comes out mis-transcribed, pre-render the lines with `say` instead |
| 5 | **The cold open.** `video/hook.json` does not exist, and neither does the concept anywhere in the repo | me | **Blocked on you**: it needs one photograph with a clear licence for the scale shot. The other four shots are already in `video/shots/`. Droppable at no cost |
| 6 | **The three rehearsals and the take.** Closes **C2** and **C3** | you and me | [`video-script.md`](video-script.md) § *The day, in order*. The order is not negotiable: the three calls back to back come **before** the final reset, never after |
| 7 | **Assemble `demo.mp4`.** None of `raw-fitted.mov`, `demo.mp4` or `demo.en.srt` exist. The 20 Sep take is split across `raw-parte1.mov` and `raw-parte2.mov`, which the documented pipeline does not contemplate | me, after the take | `fit-to-audio.py --beats`, then `build-video.sh` with `OUTRO`/`OUTRO_REPLACE`. Under 300 s |
| 8 | **Share the deck and submit on lablab** | you | The artifact is linked from [`SUBMISSION.md`](SUBMISSION.md); it has to be shared before it can be uploaded |
| 9 | **The GitHub shop window.** `description` and `homepageUrl` are both empty, no topics | you or me | `gh repo edit`. The homepage waits on row 1; the description does not |

**The video is now shot after the features, not before.** Three of the six changed what the agent
says on the call, so `seed/scripts.json` and all four fixtures moved with them. The narration in
`video/narration.tsv` was already stale against its built track (row 3); it now also describes a call
that no longer happens that way, and has to be written against the new behaviour before
`build-audio.sh` runs. What the panel's buttons show that they did not a day ago: a promise made in
week 1 and asked about in week 2, a read-back of a number the recogniser was unsure of, an answer
from the professional spoken word for word in the greeting, and a new question landing in the queue.

**[`video-script.md`](video-script.md) is corrected.** Its three patient-line tables now match
`seed/scripts.json` turn for turn — beat 3 with the promise and the conditional read-back, beat 5 with
the promise answer and the stairs question — and the session it describes is the one that is actually
possible: you answer the phone and [`video/lines.html`](../video/lines.html) speaks the lines.

**What that leaves for row 3.** Two narration lines are now wrong rather than merely stale: beat 3's
*"Two facts, and every one needs a literal quote"* is **three** facts, and beat 5 gained two patient
turns, so its 42 s no longer covers what happens on screen. Both are inputs to the rewrite, not
separate jobs.

**Checkpoints.** C1 is closed. **C2** (three real calls back to back, no reset, the third superseding
the 7/10) and **C3** (the panel live during a call) close during the recording session — row 6.
**C4** is the submission itself. Their definitions are in [`PLAN.md`](PLAN.md).

---

## 2. The Cadence build programme

[`DESIGN.md`](DESIGN.md) is the **target** design system, not a description of what is built. What it
defines and the front end does not have yet is this list, ordered by how visible it is. Nothing here
is started.

**Honest sizing.** This is roughly twenty items touching every file in `web/src`, there is no test
runner in the front end, and it competes directly with part 1 for the days that are left. Group A is
what the camera films; group C is the largest and the least visible. A cut that keeps the video
intact is **A only**.

The gate for every item is `make web` (`tsc -b && vite build`) plus a look at both themes and both
languages, and contrast measured per theme.

### A. What the camera films

| | What | Where |
|---|---|---|
| A1 | **The waveform.** 96 bars, 4px wide, 3px apart, 32px maximum, centred; `--color-accent` at 70% with the bar under the playhead at full; `--tone-dim` while the agent speaks; 15% at rest; `transform 90ms linear`, and a jump instead of an ease under `prefers-reduced-motion`. Today the only wave is eight decorative bars in the demo card | `panel/LiveCall.tsx`, `panel/panel.css`. Needs decision 1 |
| A2 | **Animated counters.** 0 → value over 900ms, ease-out, fired once by an `IntersectionObserver` at 50%; the final value written directly under reduced motion. Today `Stat` prints the string as-is | `landing/Landing.tsx:47`. Requires splitting the figure from its suffix in `landing/copy.ts` for both languages, with the number format coming from the language rather than hardcoded, and its `parity` entry |
| A3 | **The orbs.** `--orb-mint` behind the hero headline, `--orb-sky` bottom right of the closing: static radial gradients, 40% opacity, 120px blur, `pointer-events: none`. Today the two `.glow` elements are accent gradients that **pulse** (`noc-breathe`), which `DESIGN.md` § *Effects* forbids. The three tokens exist in `tokens.css` and nothing consumes them | `landing/Landing.tsx:161,452`, `landing/landing.css` |

### B. Components and states

| | What | Where |
|---|---|---|
| B1 | `[data-loading]` with a 14px spinner and the width preserved — zero matches in the repo today. And the real `disabled`: `--fill-subtle` / `--tone-dim` instead of `opacity: 0.45`, which is the one resource the rules discourage | `tokens.css` |
| B2 | Card at `--radius-lg` with `--space-6` padding and a hover that moves it to level 2. Today `.card` is `--radius-md` with 16px and has no hover rule | `panel/panel.css:73` |
| B3 | The state pill as an actual pill: `9999px`, caption size, +0.03em, 2px/8px, in three variants. Today `.pill` is a 6px rectangle at 10px with two variants | `panel/panel.css:224` |
| B4 | Transcript turn: the speaker label in `eyebrow`, and the verbatim quote in `--font-mono` — the rule says mono is reserved for verbatim, and the quote is the one thing that is not mono today | `panel/panel.css:215,277` |
| B5 | Activity rail row: phase name in `eyebrow` uppercase `--color-accent-800`, detail in caption, a right-aligned `mono` timestamp (not rendered at all today), and the phase name in `--color-danger` when it fails — today only the left border changes | `panel/ActivityRail.tsx`, `panel/panel.css:293` |

### C. The type scale

The largest item, and the one with nothing to show for it on camera. No token or class from the
published 13-row scale exists; every size is a literal in px, inline or in CSS.

| | What | Where |
|---|---|---|
| C1 | Define the thirteen steps as classes in `tokens.css` — `display-xl` through `eyebrow` and `mono` | `tokens.css` |
| C2 | Replace every loose px size with them. This is what makes the rule *"display type never below `card-title`"* enforceable: there are seven violations today, from 12px to 20px | `landing/Landing.tsx`, `landing/DemoCard.tsx`, `panel/panel.css`, `panel/Keyterms.tsx` |
| C3 | Fonts: move the `@import` at `tokens.css:1` to the two `<link rel="preconnect">` plus the stylesheet link the doc publishes, in both HTML heads — today the import blocks the CSS and there is no preconnect. Resolve Inter 700, which is downloaded and not declared | `web/index.html`, `web/panel/index.html`, `tokens.css` |

### D. Layout and elevation

| | What | Where |
|---|---|---|
| D1 | Container at 1280px (1180 today), 16px minimum gutter (20 today), prose capped at `68ch`, and the published section-padding clamp | `landing/Landing.tsx`, `landing/landing.css`, `panel/panel.css:70` |
| D2 | Elevation levels 2 and 3, neither of which exists. **`.live` is applied in `LiveCall.tsx:47` and defined nowhere**, so the live call card sits at level 1 while a call runs | `panel/panel.css` |
| D3 | `--radius-xl` on the live call card and the demo card — declared and never used today | `panel/panel.css`, `landing/DemoCard.tsx:436` |
| D4 | Nav: 64px tall, background at 85%, `blur(12px)`, the bottom border appearing only on scroll, and the current section in `--color-accent` with a 2px underline. Today the border is unconditional and there is no current-section state | `landing/landing.css:65`, `landing/Landing.tsx` |
| D5 | The selected patient row gets its 2px `--color-accent` left rule | `panel/panel.css:68` |

### E. Panel

| | What | Where |
|---|---|---|
| E1 | Call controls: six buttons in two rows with the live pair as `btn-primary`. Today there are **seven in three rows**, the live pair is secondary + primary, and three keyless ones are `btn-ghost`. Needs decision 4 | `panel/PatientView.tsx:92-129` |
| E2 | **`WeeklyChart` to two sparkline tiles with verdict arrows.** Today it renders whatever series the backend returns, as bar columns with gridlines. The single largest component rewrite in this list | `panel/WeeklyChart.tsx`, `panel/panel.css:138` |
| E3 | `RETIRED` as a `.pill` instead of the flat `.entry-state` span | `panel/FactChain.tsx:47` |

### F. Rules and cleanup

| | What | Where |
|---|---|---|
| F1 | *"Do not animate anything except the two effects above."* Today `landing.css` defines six live keyframes and `panel.css` a seventh. Decide which survive, and note that `.is-paused` covers only two of the three that loop — `noc-breathe` keeps running with the demo paused | `landing/landing.css`, `panel/panel.css:309` |
| F2 | `--color-accent-2` is declared in both themes and used nowhere, while the rules forbid a second accent. Give it a use or remove it | `tokens.css:10,81` |
| F3 | After each change, contrast measured per theme by compositing on a canvas — `getComputedStyle` returns `color(srgb …)` for `color-mix()` values | — |

---

## 3. Decisions the programme needs

Four questions `DESIGN.md` does not answer. They are not tasks; nothing above them can be built
until they are settled.

1. **Where does the waveform's level come from?** The doc says each bar is *"scaled by the audio
   level of the turn being spoken"*, but the browser never has the call audio — it is on the phone.
   Either the level is synthesised from turn state, in which case it is an activity indicator rather
   than an audio readout and the doc has to say so, or `app/channel.py` emits a level over SSE. It is
   the only question in this list that reaches the backend.
2. **The metrics band.** The doc puts it on `--fill-subtle`; the code has a dark teal band built from
   `--color-section` and `--color-section-glow`, with `--section-ink` on top. Building the doc
   retires three tokens and removes the page's only high-contrast block.
3. ~~**The `.input` component.**~~ **Settled.** The question queue needed somewhere for the
   professional to type an answer, so `.input` now exists in `panel/panel.css` and is used by
   `panel/Questions.tsx`. It has a base, a focus ring and a placeholder, not the five states
   `DESIGN.md` specifies and not the `aria-describedby` error pattern; that gap moves into group B
   above rather than staying a question.
4. **`.btn-ghost`.** It exists, it is used three times in the panel, and the component table does not
   name it while a rule forbids components the system does not name. Either it joins the table, or
   the three ghost buttons become secondary.

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
