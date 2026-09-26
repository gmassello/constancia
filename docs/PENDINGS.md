# Pending

Open work only, and all of it. Every row says **what is open**, **who closes it** and **the command
or step that closes it**. Anything not on this page is done and carries its evidence in
[`SUBMISSION.md`](SUBMISSION.md).

Deadline: **30 Sep 2026, 12:00 ART** ([`HACKATHON.md`](HACKATHON.md)). Last reviewed: **2026-09-26**, four days out.

Four parts: what blocks the submission, the Cadence build programme, the decisions that programme
needs, and what the six new features left behind alongside what is deliberately not being done.

---

## 1. The submission

One of the four mandatory deliverables is missing: the video. **The deploy is live**, verified from
another network on 25 Sep: `/health` answers
`{"status":"ok","calls":0,"store":"postgres","live":true,"dialable":false}`, `/patients` serves the
seeded Ana, and the landing serves its own title. `dialable` is `false` there on purpose — the public
panel renders no button that dials a real phone. The endcard now names that address and
`homepageUrl` points at it. Evidence in [`SUBMISSION.md`](SUBMISSION.md).

| | What is open | Who | How it closes |
|---|---|---|---|
| 1 | **The take.** The three rehearsals are done: 1 walked the shot list on the keyless buttons, 2 is subsumed by 3, and 3 was a full live call on 26 Sep — eleven turns, the four questions in order, `7 out of 10` transcribed verbatim, and the acoustics settled ([`video-script.md`](video-script.md) § *The day, in order*). What is left is the session itself, which closes **C2** and **C3** | you and me | [`video-script.md`](video-script.md) § *The day, in order*, from *Then the sequence, and only then the take*. The order is not negotiable: the three calls back to back come **before** the final reset, never after. `bash video/reset.sh` came back green on **all eleven** invariants on 26 Sep, the tunnel included — the first time the eleventh could be anything but red |
| 2 | **Assemble `demo.mp4`, and the pipeline that would do it.** ~~`fit-to-audio.py --beats`, then `build-video.sh`.~~ **Neither script exists**: not in the repo, not on disk, and `git log --all` finds no commit that ever added or removed them — they were documented, never written. What exists is their output, in the git-ignored `video/out/`: `narration.wav` (measured 267.781167 s, the 267.8 s five documents publish), 53 clips, the silences, `concat.txt`, `captions.srt`, `timing.txt` and `endcard.png` — 49 MB that cannot be regenerated. `demo.mp4`, `raw-fitted.mov` and `demo.en.srt` do not exist, and the 20 Sep take is split across two `.mov` files | me, after the take | **Decide the route before the take, not after**: write the assembly step, or plan to cut it by hand with ffmpeg. `video/out/` is **already backed up** off the repo — copied whole on 26 Sep with `narration.wav` verified at 267.781167 s on the copy — so the only open half is the route: write the assembly step, or plan to cut it by hand with ffmpeg |
| 3 | **Share the deck and submit on lablab.** The eleven slides are built and current — the *Application of Technology* slide was corrected on 26 Sep to say the key-phrase loop was measured and reverted, and it carries 319 tests and five honest limits. The artifact is **private**, and its URL is deliberately not in the repo: a private link is a dead link for a judge | you | Share it from the artifact's own Share menu, upload it to lablab, and only then does its public URL go in [`SUBMISSION.md`](SUBMISSION.md). [`deck.md`](deck.md) is the source of the content either way |

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
that leaves for row 1: the raw screen recording has to run between **3:19 and 5:45**, or
`build-video.sh` refuses it.

**Checkpoints.** C1 is closed. **C2** (three real calls back to back, no reset, the third superseding
the 7/10) and **C3** (the panel live during a call) close during the recording session — row 1.
**C4** is the submission itself. Their definitions are in [`PLAN.md`](PLAN.md).

---

## 2. The Cadence build programme

**Closed.** [`DESIGN.md`](DESIGN.md) was written as the target and the code has caught up with it:
the tokens, the thirteen type steps, the component states, the layout numbers and both effects are
built. What the four passes took, in order — Group A, the landing and the live call card: the
waveform, the animated counters, the static orbs. The panel's own set: the pill geometry and its
three variants, `CURRENT` / `RETIRED` as pills, the fact quote in `mono`, the speaker label and the
rail row on the type scale, the rail's timestamp, level 3 on the live call card, the selected patient
row, and the sparkline tiles with a verdict arrow that carries the direction. The three the camera
uses: the call controls, the nav's current section, and the animation rule's named exception. And
the last eight: the type scale defined and consumed, the fonts on `<link>` tags instead of a
render-blocking `@import`, the container and gutter from a token, the loading and disabled states,
the card at `--radius-lg` with a hover, and the second accent deleted.

**Two numbers worth keeping.** The scale replaced **104** literal sizes across five files, and
`tests/test_docs.py` now fails the build on the next one. Nothing in the product is under 12px at
any width, which is what `DESIGN.md`'s own checklist asked for and never got — the panel's ten sizes
between 9.5px and 11.5px are the ones that moved.

**What it deliberately did not do**, each written where it happens rather than dropped: the panel
takes the small half of the scale, because the video records it at 1280×800 and 22px display headings
push the live call card further under the fold — it already ends 188px below it. The spinner does
not freeze under reduced motion, it disappears and the label comes back. The disabled state keeps the
pair `DESIGN.md` names even though it measures 3.23:1 dark and 3.53:1 light, because WCAG exempts an
inactive control.

**Nothing stays open.** The last row, F4, closed by getting smaller when it was measured properly.
It read *"the hairlines do not clear 3:1"* and priced the fix at 44 borders and five of the six
shadows — every plane of the video, days before the take. But 3:1 (WCAG 1.4.11) is asked of the
border that **identifies a control**, not of a line that separates two paragraphs. That is three
outlines: the input, the secondary button, the segmented control. All three moved to `--tone-dim`, an
alias that already existed and whose published role was already a border, so the fix added no token
and touched no shadow. Measured in the browser, composited on a canvas: **4.06:1 light / 3.91:1
dark** on a card, **3.68 / 4.24** on the page ground.

The same mapping found a bug that was not on the list: in dark, `--fill-subtle` and `--color-divider`
are the same hex, so the rule left of the activity rail inside the live call card measured **1.00:1** —
literally absent in the theme the video does not use. It is now `--color-divider-strong`, 1.29 dark /
1.34 light, which is what `DESIGN.md`'s level 3 already said it should be.

**Two known limits, both written where they happen rather than left as debt:**

- **The other 41 hairlines stay at 1.13–1.56:1.** They separate; they do not identify a control, and
  a section divider at 3:1 stops being a hairline and becomes a rule — a design decision, not an
  accessibility fix, and not one to take days before recording. `DESIGN.md`'s verification checklist carries the
  measurement.
- **The disabled control keeps `--color-divider`, 1.29:1 light / 1.21:1 dark.** 1.4.11 exempts an
  inactive component on purpose, and the gap between it and the `--tone-dim` of an active one —
  3.14:1 light, 3.23:1 dark — is the signal that it is off.

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
   it left E1 a layout change, which is how E1 closed.

---

## 4. What the features left, and what stays out

**Done, and no longer optional.** All six features in
[`NEW_FEATURES.md`](NEW_FEATURES.md) are built, tested and visible in the panel's scripted buttons.
That file is now the record of where each one came from, not a plan. Row 7 is not one of them: the
key phrases came from AssemblyAI's own API rather than from another entry's repo, so it has no entry
there and its behaviour is described in [`BACKEND.md`](BACKEND.md), [`API.md`](API.md) and
[`SUBMISSION.md`](SUBMISSION.md) instead. What each one left open:

| | Feature | What is still open |
|---|---|---|
| 1 | Out-of-range values | Nothing. The ceiling comes from the pack's own `Measure`, so a vertical with an unbounded reading is not capped — which is correct, not a gap. |
| 2 | Commitments | **Closed.** The action vocabulary lives in `pack.actions`, so a postpartum or chronic promise is scored deterministically by its own pack with no key and no network, and what the vocabulary rejects is measured rather than counted: `make smoke-jev` prints recall, precision and the margin and writes [`../scripts/jev-measured.json`](../scripts/jev-measured.json) with every probability and a hash of the question wording. **Measured 25 Sep, wording `117b8a3c18ac`: recall 0.50, precision 1.00, margin 0.78.** The two questions this row was holding open are both decided in [`OPERATIONS.md`](OPERATIONS.md) with the measurement behind each: the label on *"I will take the pram to the corner every afternoon"* **stands** — its action is walking, which the deterministic vocabulary already scores at 0.90, and enumerating the object instead would score *"I will buy a pram this weekend"* at 0.90 too — and the floor **stays at 0.8** even though 0.5 would take recall to 0.75 with 0.48 of margin left, because four negatives is not a calibration set and the model resolves to ±0.05. Probing that pair found a real bug and fixed it: `DEADLINE` counted *every morning*, *every evening* and *every night* but not *every afternoon*, nor *every week* or *before lunch* beside their own neighbours, so the same promise scored 0.65 or 0.90 depending on which half of the day the patient named. No fixture or seed line used those phrases, so no published number moves; `tests/test_commitments.py` now pins the four parts of the day to one score. Still open, and not about promises: Zero Data Retention is a Pro tier and this is a hobby plan, so `JEV_ZERO_RETENTION` defaults off and the sentence falls under the gateway's ordinary retention; asking for it anyway is a 403 on every call, which is how we found out. The gateway also rate-limits a run of eight in a row with a 429, which the client turns into the same `None`. |
| 3 | The critic | The fifth rule the source design asked for — that the reply share a word with its goal — is **deliberately not built**: a goal here is one clause, so a legitimate recall question shares nothing with it and gets flagged. Measure the other four with `make smoke-call` before trusting them on a real line. |
| 4 | Low-confidence read-back | **`words[].confidence` is documented but not seen.** AssemblyAI's streaming API reference declares it on every word of a `Turn`, *"Confidence score for the word (0.0 to 1.0)"*, so the field is not a guess any more — what is unverified is that it arrives on `universal-3-6-pro` over µ-law at 8 kHz. The code still treats a missing field as certain, which leaves the read-back off rather than firing on every number, and `STT_CONFIDENCE_FLOOR` needs calibrating on real telephone audio once a call confirms it. |
| 5 | Audio behind a quote | Cannot be shown offline: `scripted` and `replay` have no recording, so no quote in the demo has a play button. `/calls/{id}/audio` serves the whole mp3 with no `Range` support. |
| 6 | The question queue | The answer is relayed in the greeting of the **next** call, so the loop takes two calls to close. `wants_human` flags the call and nothing acts on the flag yet beyond the trace and `call_ended`. |
| 7 | Key phrases | **Measured, and half of it reverted.** Closed on 26 Sep against a real recording (`scripts/keyphrases-measured.json`): 15 phrases returned, 10 kept, 9 new against the patient's vocabulary — but of those, three were the agent's own questions (`auto_highlights` reads the whole recording, not just the patient), three were common words the API's own docs warn cause overcorrections (`today`, `work`, `Next week`), and one was **`Anna`, the patient's name as the recogniser mis-heard it** — priming the next call with that would reinforce the error every week. So `with_phrases` and its call in the recall phase are **gone**; the panel card stays, and it costs nothing: `entities_unchanged` and `sentiment_unchanged` both came back true. `tests/test_orchestrator.py` now asserts the phrases do *not* reach the keyterms. Reconnect it the day they are filtered against the detected entities and the pack's vocabulary |

**Deliberately out of scope.** Decided, and not to be reopened without saying so:

- **The cold open.** `video/hook.json` was never written and the concept exists nowhere — not in
  [`video-script.md`](video-script.md), not in `narration.tsv`, not in any script. `video/shots/`
  holds two panel stills and nothing an opening beat could use. The narration is built and
  measured at 267.8 s across 53 captions, so a beat in front of it means re-synthesising a
  finished track five days from the deadline. Dropped on 25 Sep, deliberately.
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
