# New features

Six features taken from other entries of the AssemblyAI Voice Agent Hackathon, read at code level and mapped
onto this codebase. Each one names the source repo, what to change here, how to test it and what can go wrong.
Insertion points were checked against commit `0a2c6b8`.

> **All six are built.** This file is now the record of where each one came from and what it was
> meant to be, not a plan. Where it and the code disagree, the code is right — the sizes below were
> optimistic in four of the six, and three decisions were taken differently while building: the
> critic's fifth rule was dropped, feature 5 ships no fixture recording, and feature 2's promise
> check became a question in the list rather than a branch in the loop. What each one left open is
> in [`PENDINGS.md`](PENDINGS.md) § 4.

Deadline: **30 Sep 2026, 12:00 ART**.

## Order

| # | Feature | Source | Effort | Judging criterion |
|---|---|---|---|---|
| 1 | Out-of-range values never become facts | [crewvoice](https://github.com/bisale24-ops/crewvoice) | S | Business Value |
| 2 | Patient commitments, checked the following week | [pact](https://github.com/Walkrob28/pact) | S-M | Originality, Business Value |
| 3 | Deterministic critic between the LLM and TTS | [gadfly](https://github.com/AshritVerma/gadfly-v3-public) | S | Business Value |
| 4 | Re-ask when a number arrived with low STT confidence | [voiceledger](https://github.com/Darkjay123/voiceledger) | M | Application of Technology |
| 5 | The exact audio behind every quote | [IntakeScribe](https://github.com/Elle31416/IntakeScribe) | M | Presentation, Application of Technology |
| 6 | Patient questions queued for the professional | [Vera](https://github.com/Ad1ty-Gupta23/Vera) | M (S without the spoken answer) | Business Value, Presentation |

1–3 are small and independent. 4 depends on nothing but touches the live channel. 5 needs the post-call
analysis to keep word timestamps. 6 adds the most UI.

Every feature must keep `make test` green with no network, no keys and no database, and must work in
`scripted` and `replay` mode, not only `live`.

---

## 1. Out-of-range values never become facts

**Source.** `crewvoice/server/store.py` `Timesheet.record_hours()` rejects hours outside `0 < h ≤ 16` with
`{"ok": False, "reason": "out_of_range"}`. The rule lives in code, not in the prompt, so the model cannot talk
past it.

**Change here.**
- `app/extract.py` `run()`: drop a fact whose `value` falls outside `0..Measure.scale_max` (`app/packs.py:50`;
  symptom 10, adherence 7).
- Emit `call.emit("fact_rejected", reason="out_of_range", quote=..., value=...)` so it shows in the activity rail.

**Test.** `tests/test_extract.py`: a scripted extraction returning `pain = 14` produces no fact and one
`fact_rejected` event.

**Note.** crewvoice's `heard_as` + `source_utterance` is what `quote` + `turn_id` already do here. Nothing to
port; it is a pitch point.

---

## 2. Patient commitments, checked the following week

**Source.** `pact/commitments.py`:
- Five regexes: `PLEDGE` (I/we + 'll / will / going to / let me), `ACTION` (closed verb list), `DEADLINE`,
  `HEDGE` (maybe / might / if I have time) and `ASK` (can/could you, please).
- A clause is dropped if it is an ASK without a PLEDGE, or lacks PLEDGE or ACTION.
- Confidence starts at 0.55: +0.25 with a deadline, +0.10 for the action, −0.35 if hedged. Anything under 0.4
  is dropped.
- `test_commitments.py` holds 8 positives and 7 hard negatives ("Can you send…", habitual "Our team usually…",
  "I'll be at the conference").

pact needs a second diarized pass to know who spoke. Here the speaker is already known (`add_turn("patient"|"agent")`),
so that part is not needed.

**Change here.**
- `app/extract.py`:
  - add `"commitment"` to `CATEGORIES` (line 9);
  - add pact's rules to the instructions: first person, concrete action, requests do not count, hedged lowers
    confidence;
  - after `ground()`, keep a commitment only if its quote matches `PLEDGE` and not `ASK`. This stops the LLM from
    turning "my physio said I should walk" into a promise.
- The `ACTION` vocabulary must be rewritten for patients: *do the exercises, walk, stretch, take, rest, go to*.
  pact's list is for sales (*send, quote, invoice*).
- `app/packs.py` `memory_block`: a "Promised last week: …" block.
- `app/orchestrator.py` `converse`: before the `adherence` question, ask whether they did what they promised.
  Word it as curiosity, not a reproach.
- A new `adherence` fact supersedes the commitment. The chain *promised → kept / not kept* then comes out of the
  existing supersession machinery, with no schema change (`category` has no constraint in `schema.sql`).
- Panel: a *promised / kept* badge in `web/src/panel/FactChain.tsx` and the labels in `copy.ts`, in both languages.

**Test.**
- `tests/test_extract.py` gets pact-style hard negatives: "Can you send me the video?", "My physio said I should…",
  "I usually walk on Sundays".
- The scripted two-call demo shows the promise in call 1 and the question about it in call 2.

---

## 3. Deterministic critic between the LLM and TTS

**Source.** gadfly:
- `server/critic.ts` `runCritic` runs Haiku (`max_tokens 50`, `temperature 0`), which returns `SHIP` or
  `REVISE: <reason>`. It fails open.
- On REVISE it regenerates once (`server/drafting.ts:110`) and speaks without critiquing again.
- `server/prompts.ts:505` `CRITIC_SYSTEM` is the checklist.
- `server/auditor.ts` is a regex drift heuristic run every 5 outputs.

**Why not a second LLM here.** It adds 0.4–1 s of silence per turn on a phone line. The check is rules only.

**Change here.**
- New `app/critic.py`, or inside `app/guard.py` reusing `normalize`. `check(text, goal, memory, history)` returns
  `ok` or a reason:
  - clinical advice: *take / stop / increase / you should / dose / mg*, in both languages;
  - the reply ends in a question sharing terms with the current goal (`_instruction_of` / `ASK_MARKER` already
    extract it from the pack);
  - every number in the reply appears in the memory block or the history;
  - at most two sentences, as `SYSTEM_RULES` already asks.
- `app/orchestrator.py:14`: wrap `llm.reply(...)`. On failure, do not regenerate: speak a templated fallback
  built from the goal (0 ms extra) and `call.emit("critic_revise", reason=...)` for the activity rail.

**Test.**
- Unit tests for each rule with positive and negative sentences.
- In scripted mode, an LLM stub that returns "You should increase the dose" makes the fallback get spoken.

**Risk.** False positives make the agent sound robotic. `SYSTEM_RULES` and the red-flag guard already cover part
of this; measure with `make smoke-call` before and after.

---

## 4. Re-ask when a number arrived with low STT confidence

**Source.** `voiceledger/src/core/transcribe.ts`:
- `CONFIDENCE_FLOOR = 0.6` and `findDoubtfulAmounts(words)`, which keeps money words under the floor.
- `src/app/api/whatsapp/route.ts` re-asks only that value; the rest of the note is kept.

voiceledger uses the pre-recorded API. According to AssemblyAI's docs, Universal-Streaming v3 `Turn` messages also
carry `words[].confidence`. Verify on the first live call.

**Change here.**
- `app/channel.py:151` already reads `words`, only for barge-in. In `_aai_reader`, also collect the numeric words
  under the floor and pass them along with the transcript. `add_turn` already takes `**data` (`app/calls.py:47`),
  so they go in as `add_turn("patient", text, low_conf=[...])`.
- `ScriptedPatient.listen` returns the same shape, so tests and replay keep working. Add one scripted patient line
  with a low-confidence number.
- `app/orchestrator.py` `converse`: if the question is `pain` or `adherence` and the turn has `low_conf`, one
  extra `ask()` ("Did you say seven out of ten?"). This replaces crewvoice's always-on read-back, which would
  lengthen every weekly call.
- `app/extract.py`: lower the fact's confidence, or drop the value, when its `turn_id` carries `low_conf`.
- `call.emit("low_confidence", words=...)` for the panel.
- New setting `STT_CONFIDENCE_FLOOR`, default 0.6.

**Test.** A scripted turn "my pain is seven" with `confidence: 0.4` on "seven" triggers exactly one re-ask. With
0.9 it does not.

**Risks.**
- With `format_turns=true`, `words` may be unformatted ("seven") while `transcript` says "7". The number matcher
  must accept number words in English and Spanish.
- µ-law at 8 kHz yields lower confidences than clean audio. Calibrate the floor on real calls, or it re-asks
  everything.

---

## 5. The exact audio behind every quote

**Source.** `IntakeScribe/deployment/browser/server.mjs`:
- It proxies the Voice Agent API session artifacts; `/api/sessions/:id/audio` returns a pre-signed URL.
- `highlightAndSeek` / `highlightByTime` sync with `data-ms` per line and `audio.currentTime`.
- It only has a start offset, and invents `idx*5000` when one is missing. Take the mechanics, not the precision.

**Already here.** `app/telephony.py:33` records the call (`record=True`), `/voice/recording` stores
`calls.recording_url`, and every fact carries `quote` + `turn_id`, shown in `FactChain.tsx`.

**Change here (simple path).** Use the word timestamps from the post-call pre-recorded analysis. They are relative
to the recording itself, so there is no stream-vs-recording offset to calibrate.
- `app/analysis.py` `summarize`: keep `words` (`text`, `start`, `end`) instead of discarding them.
- After extraction, align each fact's `quote` against those words and store `start_ms` / `end_ms` on the fact.
  Use a fuzzy match on normalized tokens, not an exact one.
- New `GET /calls/{id}/audio` in `app/main.py`: proxy the recording with Twilio auth, reusing the logic in
  `analysis.hosted` (the browser cannot fetch it directly; see the `ponytail:` note in `analysis.py:12`).
- `web/src/panel/FactChain.tsx`: a play button per quote using `<audio src=".../audio#t=start,end">` (native
  media fragments).
- Document the endpoint in `docs/API.md`.

**Test.**
- A unit test of the alignment on a fixture word list, including a quote that differs by punctuation.
- For the demo, ship a fixture recording for `scripted` / `replay`, which have none today.

**Risks.**
- A quote the LLM paraphrased will not align. Show no button rather than a wrong one.
- The endpoint serves clinical audio on a server with no auth; the README warning already covers this.
- Twilio records mono unless `recording_channels="dual"`.

---

## 6. Patient questions queued for the professional

**Source.** Vera:
- `backend/app/services/knowledge_gaps.py`:
  - `normalize_question` (lowercase, `[a-z0-9]` only, collapsed spaces);
  - `should_capture` (≥5 chars, not a greeting, has "?" or a question starter or ≥3 words);
  - `record_gap`, which upserts and increments `occurrence_count`;
  - `resolve_gap` / `dismiss_gap`.
- `models/knowledge.py` `KnowledgeGap`.
- `api/knowledge_routes.py`: `GET /gaps`, ordered by count then recency; `resolve` returns 409 if not open.
- Handoff lives in `services/call_operations.py`: `wants_human()` + an idempotent `create_handoff`.

**Change here.**
- `app/extract.py`: `open_questions: list[{question, quote, turn_id}]` on `FactSet`, grounded with the same
  `ground()`. These are the questions `phrase()` currently deflects per `SYSTEM_RULES` ("is this normal?", doses).
- Storage: a `patient_questions` table in `schema.sql` (`patient_id`, `call_id`, `question`, `quote`, `turn_id`,
  `status` open/answered/dismissed, `answer`, `answered_at`), plus the in-memory store equivalent for tests.
- `app/main.py`:
  - `GET /patients/{id}/questions`;
  - `POST /questions/{id}/answer`;
  - `POST /questions/{id}/dismiss`, returning 409 when the question is not open.
- Order by recency, not frequency: there is one patient per row, so Vera's count ranking adds little.
- Panel: new `web/src/panel/Questions.tsx`, wired in `api.ts`, `copy.ts` (both languages) and `PatientView.tsx`,
  with the quote and a link to the turn.
- Closing the loop, unlike Vera: the approved answer goes into no knowledge base and no LLM. On the next call,
  `greet` reads it verbatim with `channel.say("Your physiotherapist asked me to tell you: …")`, so the agent never
  generates clinical advice. The panel shows exactly the sentence that will be spoken.
- Handoff already exists (`guard` + `call.escalated`). Only port `wants_human` ("I want to talk to my doctor") as a
  non-terminal rule: it flags the call without ending it.
- Document the routes in `docs/API.md`.

**Test.**
- Extraction of a scripted call with "Is it normal that my knee clicks?" produces one open question.
- The answer endpoint changes its status; a second answer returns 409.
- The next scripted call speaks the answer verbatim.

**Risks.**
- An urgent question ("is this bleeding normal?") cannot wait in a queue. The red-flag guard stays in front and
  escalates first.
- This adds the most UI of the six, with a week to go. Without the spoken answer it drops to S.

---

## Considered and dropped

- **Always-on read-back (crewvoice).** It makes every weekly call longer. #4 re-asks only when needed.
- **LLM critic (gadfly).** Too much latency on a phone call. At most an async post-call audit shown in the panel.
- **Second diarized pass (pact).** Speakers are already separate here.
- **Hash-chained audit log ([dispatch-voice](https://github.com/lukiod/dispatch-voice)).** Out of scope per
  INTENT §12.
