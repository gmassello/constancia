# Shot list — the 5-minute demo

The narration is [`../video/narration.tsv`](../video/narration.tsv); its beat labels are the rows of
this table. Produced with the `personal-record-video` skill: the voice is synthetic, the human
records the browser window with the mic off, and the video is fitted to the audio afterwards.

**The call audio is not on the recording.** What the camera sees is the panel with the live
transcript of both sides while the phone rings off camera.

> **This is a record of how the video is meant to be shot.** If the take comes out different, the
> take wins: rewrite the narration line, do not re-shoot for a prettier sentence.

## Before pressing record

```bash
bash video/reset.sh --check     # every line green, or do not record
make web && make dev            # the panel at http://localhost:8001/panel
```

Window mode (`Cmd+Shift+5` → *Record Selected Window*), 1280x800, mic off, phone off camera, the
browser in **English** and the **light** theme — both are the defaults, and English is what the
judges read. Between takes: `bash video/reset.sh`, then delete the old `video/raw.mov`.

Check the Gemini and AssemblyAI quotas in their consoles **before** the session. A rehearsal plus a
take plus the verification run can exhaust a daily free tier, and it does not fail cleanly: the
agent answers with a generic error and the beat dies on camera for no visible reason.

## The two paths

Every beat that involves a call has two ways to shoot it. They are not equivalent and the choice is
made once, for the whole video, before the session:

| | **live** — the one to aim for | **keyless** — the fallback |
|---|---|---|
| Needs | `.env` filled, ngrok up, C1 and C2 done | nothing |
| The call | a real phone rings; you answer and read the lines below | the panel's own buttons |
| AssemblyAI | Universal-Streaming on real audio | not exercised |
| What you say | the lines in each beat, out loud | nothing — the lines are already in `seed/scripts.json` |
| Risk | the model phrases differently every take | none; it is byte-identical every time |

The patient lines are **the same in both paths**, because the keyless scripts were written from
them. So the extraction, the supersession and the key terms behave identically either way.

## The beats

| # | Beat | Track | On screen |
|---|---|---|---|
| 1 | `1:problem` | 21 s | The landing at `/`, the opening claim |
| 2 | `2:product` | 24 s | The landing: one sentence, then the three packs |
| 3 | `3:call-one` | 46 s | 🎯 Week 1. Empty file, four questions, the facts land |
| 4 | `4:memory-off` | 23 s | Week 2 with memory off: the generic protocol |
| 5 | `5:memory-on` | 34 s | 🎯 Week 2 with memory on: the knee, and the 7/10 retired |
| 6 | `6:panel` | 31 s | The chart, the file, the key terms, a red flag |
| 7 | `7:close` | 15 s | Business model on the landing, then the endcard |

Track lengths are what `video/out/timing.txt` measured; the recording can be longer, because
`fit-to-audio.py` keeps the moments where the screen changes at 1x and compresses the waiting.

---

### 1 · `1:problem` — the problem

**Screen:** the landing at `http://localhost:8001/`, top of the page, plain register.
**You:** nothing. Slow scroll to the problem statement, one pause on the number.

INTENT §9 called for a slide here. The landing says the same thing, was designed for exactly this
audience, and is already deployed — a slide would be a second copy to keep in sync.

---

### 2 · `2:product` — the product in one sentence

**Screen:** keep scrolling the landing: the one-sentence description, then the three-pack band
(rehab / postpartum / chronic).
**You:** nothing.

---

### 3 · `3:call-one` — week 1, live 🎯

**Screen:** the panel at `/panel`, Ana selected, camera on the **live call card** — the transcript
and the activity rail. The rail's first line says the agent has nothing on file for this call, which
is what makes it week one.

**live:** `make call PHONE=+54911...` from a terminal that is not on camera. Answer the phone and
read, one line per question, waiting for the agent to finish:

| | You say |
|---|---|
| greeting | «Hola, sí, soy Ana.» |
| pain | «La rodilla derecha me duele siete de diez, sobre todo cuando subo escaleras.» |
| adherence | «Los ejercicios los hice tres veces, me salté dos días porque estuve con mucho trabajo.» |
| side effects | «Después de los ejercicios me queda un poco rígida, nada raro.» |
| red flags | «No, caídas no tuve, nada de eso.» |

**keyless:** replay the recorded week-1 call, from the same off-camera terminal:

```bash
curl -s -X POST localhost:8001/calls -H 'content-type: application/json' \
  -d '{"patient_id":"8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5","memory":false,"mode":"replay","script":"week1"}'
```

It re-emits the recorded trace at its original pace, so the panel fills exactly as it did when the
call ran. A replay writes nothing to the store, so it leaves no residue for the next take.

**What the camera must catch:** the transcript filling turn by turn, and then the activity rail:
`EXTRACTION 2 facts`, each new fact with its quote and its turn number. Hold on the rail — that quote
is the proof that the fact is not invented.

---

### 4 · `4:memory-off` — week 2, memory off

**Screen:** the panel, same patient, still on the live call card. The narration says "one week
later"; nothing on screen has to.

**live:** the panel's **Call without memory** button, and answer the phone with the week-2 lines
from beat 5. The agent gets no memory block in its prompt, so it asks the generic pain question.
**keyless:** replay the recorded take of exactly this call:

```bash
curl -s -X POST localhost:8001/calls -H 'content-type: application/json' \
  -d '{"patient_id":"8c9d0e1f-2a3b-4c5d-6e7f-8091a2b3c4d5","memory":false,"mode":"replay","script":"week2-off"}'
```

**The point of the beat is the question, not the answer.** She says the knee is at four out of ten
and the agent has no idea that means anything: it never asks about the knee, and the rail shows
`MEMORY OFF` on both the recall and the store phases. Thirty seconds of honest "before".

Cut this beat first if the track ever needs to lose time.

---

### 5 · `5:memory-on` — week 2, memory on 🎯

**Screen:** the panel. This is the beat the project exists for.

**live:** **Call with memory** (or `make call` with the patient's file already populated). Answer:

| | You say |
|---|---|
| greeting | «Hola, sí, soy Ana.» |
| pain | «La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.» |
| adherence | «Esta semana los hice cinco veces, me organicé mejor.» |
| side effects | «No, ninguna molestia nueva.» |
| red flags | «No, nada de eso.» |

**keyless:** the same button. With memory on and Ana's file populated, `run_scripted` picks the
week-2 script on its own (`app/replay.py:49`) and the scripted patient says exactly those lines.
This one runs the real pipeline, not a recording: the supersession happens on camera.

**What the camera must catch,** in this order:

1. The agent's **first sentence**, which quotes last week: "la semana pasada me contaste que la
   rodilla te dolía siete de diez al subir escaleras".
2. In the file, the 7/10 going **struck through** under the new 4/10, with `RETIRED` beside it.
3. The rail line `FACT RETIRED`.

If the agent phrases the opening differently — it will — that is the take. Rewrite the caption.

---

### 6 · `6:panel` — what the professional sees

**Screen:** scroll the panel, top to bottom, pausing on each card:

1. **How she is doing** — pain 7 → 4, sessions 3 → 5, with the verdict arrows.
2. **What the agent remembers** — the chain, with the retired entry still there and its quote.
3. **The words the agent listened for** — the three-step drawing and the chips: her own vocabulary
   from last week, handed to AssemblyAI as `keyterms_prompt`.
4. **The red flag.** Press **call with a red flag**. The patient reports a fall, the guard stops the
   call, the remaining questions are never asked, and the row lands marked `ESCALATED`.

The red-flag call takes about 25 s of wall clock and the narration gives it about 6 s — that is what
`fit-to-audio.py` compresses. Let it run in full on camera; do not cut it short by hand.

Cut the key-terms card second if the track needs to lose more time.

---

### 7 · `7:close` — business and endcard

**Screen:** the landing's business band, then `video/out/endcard.png`.
**You:** nothing.

```bash
PUBLIC_URL=https://<render-url> bash video/endcard.sh
```

## What can come out differently

The agent is not deterministic on the live path. Things that change between takes, and what to do:

| What changes | What to do |
|---|---|
| The greeting's exact wording | Nothing. It always carries the knee and the 7/10; the caption says so, not the sentence |
| The order of the facts in the rail | Nothing; the quote and the turn number are what the beat claims |
| A question phrased as two sentences | Nothing |
| The agent skipping a question | Stop the take. That is a bug, not a phrasing |
| A fact landing without a quote | Impossible by construction — if it happens, stop and open an issue |
| The patient line mis-transcribed | Re-shoot that call. The key terms exist to prevent exactly this |

## If the track goes over 300 s

Decided now, not on the day:

1. Cut beat 4 (`4:memory-off`) to its first two lines.
2. Cut the key-terms card out of beat 6.
3. Nothing else. Beats 3 and 5 are the video.
