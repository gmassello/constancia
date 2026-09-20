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
ngrok http 8001                 # PUBLIC_BASE_URL in .env = the https URL it prints
bash video/reset.sh --check     # every line green, or do not record
make web && make dev            # the panel at http://localhost:8001/panel
curl -s localhost:8001/health   # "live": true, or the live buttons do not render at all
```

`.env` needs `DEMO_PHONE` set to the phone that will be answered off camera, and `PUBLIC_BASE_URL`
set to the tunnel URL **before** `make dev`. A stale tunnel URL makes every webhook 403 in
`app/security.py:12`, and the symptom is a phone that rings and then goes silent — it reads as a
model bug and it is not one. With `.env` complete but `DEMO_PHONE` empty the live buttons still
render and answer `400 unknown patient` in the panel's error line: a dead button on camera.

Window mode (`Cmd+Shift+5` → *Record Selected Window*), 1280x800, mic off, phone off camera, the
browser in **English** and the **light** theme — both are the defaults, and English is what the
judges read. Between takes: `bash video/reset.sh`, then delete the old `video/raw.mov`.

Check the Gemini and AssemblyAI quotas in their consoles **before** the session. A rehearsal plus a
take plus the verification run can exhaust a daily free tier, and it does not fail cleanly: the
agent answers with a generic error and the beat dies on camera for no visible reason.

## The two paths

**Beats 3, 4 and 5 are shot live**: three real phone calls, dialled from the panel. That is the
decision for this video, and it is what closes C1 and C2. The keyless column below is the contract to
fall back to if a quota dies mid-session; the red flag in beat 6 stays keyless either way.

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
| 3 | `3:call-one` | 61 s | 🎯 Week 1 live. Nothing recalled, four questions, two facts extracted |
| 4 | `4:memory-off` | 24 s | Week 2 live with memory off: the generic protocol |
| 5 | `5:memory-on` | 42 s | 🎯 Week 2 live with memory on: the knee, and the 7/10 retired |
| 6 | `6:panel` | 31 s | The chart, the file, the key terms, a red flag |
| 7 | `7:close` | 18 s | Business model on the landing, then the endcard |

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

**live:** press **Real phone, no memory**. A call started from a terminal never reaches this card —
the page only follows the call its own `POST /calls` returned — so every call in this video is
pressed on screen. Answer the phone and read, one line per question, waiting for the agent to finish:

| | You say |
|---|---|
| greeting | «Hola, sí, soy Ana.» |
| pain | «La rodilla derecha me duele siete de diez, sobre todo cuando subo escaleras.» |
| adherence | «Los ejercicios los hice tres veces, me salté dos días porque estuve con mucho trabajo.» |
| side effects | «Después de los ejercicios me queda un poco rígida, nada raro.» |
| red flags | «No, caídas no tuve, nada de eso.» |

With memory off the `recall` phase is skipped, so the agent genuinely has nothing in its prompt —
that is what makes it week one on a seeded patient. It also means **no `keyterms_prompt` is sent**:
`set_keyterms` lives inside `recall` (`app/orchestrator.py:36`), so this transcription runs unprimed
and the "patient line mis-transcribed" row below is at its most likely here. Rehearse the four
numbers out loud before the take.

**keyless:** the panel's **Call without memory** button, which runs the week-1 script.

**What the camera must catch:** the transcript filling turn by turn, and then the activity rail:
`MEMORY OFF recall skipped`, `EXTRACTION 2 facts from the transcript`, `MEMORY OFF storage skipped`.

The per-fact lines with their quotes do **not** appear here: with memory off nothing is stored, so
`fact_stored` never fires. The quote-and-turn proof is beat 5's `NEW FACT` lines and the file in
beat 6. Do not promise it in this beat.

---

### 4 · `4:memory-off` — week 2, memory off

**Screen:** the panel, same patient, still on the live call card. The narration says "one week
later"; nothing on screen has to.

**live:** press **Real phone, no memory** again — same button as beat 3, same switch off. Answer
with the week-2 lines:

| | You say |
|---|---|
| greeting | «Hola, sí, soy Ana.» |
| pain | «La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.» |
| adherence | «Esta semana los hice cinco veces, me organicé mejor.» |
| side effects | «No, ninguna molestia nueva.» |
| red flags | «No, nada de eso.» |

**keyless:** the panel's **the same call without memory** link. It runs the `week2-off` script: the
week-2 answers with the generic agent lines, because an agent with no memory block cannot open on the
knee.

**No reset between beats 3, 4 and 5.** With memory off `store_facts` returns early *and* `summarize`
skips its `save_call` (`app/orchestrator.py:70,89`), so beats 3 and 4 write nothing at all: last
week's 7/10 is still on file and still current when beat 5 dials. A reset is only needed before
**re-shooting** beat 5, because the supersession only runs one way per state of the seed.

**The point of the beat is the question, not the answer.** She says the knee is at four out of ten
and the agent has no idea that means anything: it never asks about the knee, and the rail shows
`MEMORY OFF` on both the recall and the store phases. Thirty seconds of honest "before".

Cut this beat first if the track ever needs to lose time.

---

### 5 · `5:memory-on` — week 2, memory on 🎯

**Screen:** the panel. This is the beat the project exists for.

**live:** press **Real phone, with memory**. This is the only call in the video where the key terms
are actually sent — `set_keyterms` is inside `recall`, which beats 3 and 4 skip — so it is also the
best-transcribed of the three. Answer:

| | You say |
|---|---|
| greeting | «Hola, sí, soy Ana.» |
| pain | «La rodilla mejoró bastante, ahora me duele cuatro de diez al subir escaleras.» |
| adherence | «Esta semana los hice cinco veces, me organicé mejor.» |
| side effects | «No, ninguna molestia nueva.» |
| red flags | «No, nada de eso.» |

**keyless:** **Call with memory**. With Ana's file populated, `run_scripted` picks the week-2 script
on its own (`app/replay.py:49`) and the scripted patient says exactly those lines. This one runs the
real pipeline, not a recording: the supersession happens on camera.

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
4. **The red flag.** Press **call with a red flag** — this one stays **keyless** on purpose: a real
   call buys nothing here and saves a fourth phone call per take. The patient reports a fall, the
   guard stops the call, the remaining questions are never asked, and the row lands marked
   `ESCALATED`.

The key-terms card reads the **newest** call (`PatientView.tsx:37` takes `rows[0]`, ordered
`started_at desc`) and `queries.keyterms_at` filters to the facts current *before* that call, so
after beat 5 it still shows the four week-1 terms. Nothing to reset for it.

The red-flag call takes about 25 s of wall clock and the narration gives it about 6 s — that is what
`fit-to-audio.py` compresses. Let it run in full on camera; do not cut it short by hand.

Cut the key-terms card second if the track needs to lose more time.

---

### 7 · `7:close` — business and endcard

**Screen:** the landing's business band, to the end of the take. **The endcard is not on camera** —
it is a still appended at assembly, so nothing opens a `file://` URL in the address bar on screen.

The hostname is `constancia-voice.onrender.com`, which is what `render.yaml` claims — plain
`constancia.onrender.com` belongs to an unrelated app, so Render would have appended a random suffix
and the card would have pointed at somebody else's form. Re-render the card if the deploy ever lands
on a different hostname; it is spliced in after the take, so it never delays recording.

```bash
PUBLIC_URL=constancia-voice.onrender.com bash video/endcard.sh   # no scheme: a bare domain on the card
```

The endcard covers the last spoken line, so "constancia. Thanks for watching" is heard *and* burned
over the card instead of over a screenshot of the landing. `OUTRO_REPLACE` is what buys that, and it
is the length of the last caption — re-derive it whenever the narration changes:

```bash
python3 - <<'EOF'
import re
srt = open("video/out/captions.srt").read().strip().split("\n\n")[-1].splitlines()[1]
h, m, rest = re.split("[:]", srt.split(" --> ")[0], maxsplit=2)
start = int(h) * 3600 + int(m) * 60 + float(rest.replace(",", "."))
end = open("video/out/timing.txt").read().split("TOTAL")[1].split()[0]
print(f"OUTRO_REPLACE={float(end) - start:.1f}")
EOF
```

At 3:39.5 of narration that is `2.4`. Assemble with:

```bash
VIDEO_DIR=$PWD/video MAX_SECONDS=300 \
  OUTRO="video/out/endcard.png:5" OUTRO_REPLACE=2.4 \
  bash ~/.claude/skills/personal-record-video/scripts/build-video.sh video/out/raw-fitted.mov
```

Verified end to end against a synthetic recording: 1920x1080, **222.1 s = 3:42.1**, under the cap,
the card up from 3:37.1 with the final caption on it and 2.6 s of quiet after.

**One constraint this puts on the take:** `build-video.sh` refuses a recording that is not within
0.75x–1.30x of `narration − OUTRO_REPLACE`, which is 217.1 s. Anywhere between about 2:43 and 4:42
of raw screen time is fine; `fit-to-audio.py` lands it far closer than that.

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
