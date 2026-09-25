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
make web && make take           # the panel at http://localhost:8001/panel
bash video/reset.sh --check     # every line green, or do not record
```

`reset.sh --check` is the gate. Past the demo state it censes the three things that fail in silence
on camera: a Gemini quota that is gone, an AssemblyAI key that is rejected, and a `PUBLIC_BASE_URL`
that is not the ngrok that is running. Gemini costs one request; AssemblyAI opens the streaming
socket rather than spending a transcript; neither prints a key. Each
of them reads as a model bug from the other side of the camera, which is why none of them is left to
be noticed during a take.

`.env` needs `DEMO_PHONE` set to the phone **you** answer off camera, and `PUBLIC_BASE_URL` set
to the tunnel URL **before** `make take`. A stale tunnel URL makes every webhook 403 in
`twilio_form()` (`app/security.py`), and the symptom is a phone that rings and then goes silent — it
reads as a model bug and it is not one. With `.env` complete but `DEMO_PHONE` empty the live buttons
**are not rendered at all** — `/health` reports `dialable: false` and the panel hides them, with the
sidebar reading *phone: no demo number*. Two beats of this video are live calls pressed from those
buttons, so a missing pair of buttons on camera means the same thing a dead one used to: check
`DEMO_PHONE` before recording. `video/reset.sh --check` reads the flag off the running service.

**Record against `make take`, not `make dev`.** `make dev` runs uvicorn with `--reload`: any save
under the repo — an editor's autosave is enough — restarts it, the lifespan runs `load_seed()` again,
and the take's calls vanish. The retired 7/10 comes back as current, mid-video. It cost one take.
`make take` is the same server without the reloader, so the state cannot be swept out from under a
recording.

Window mode (`Cmd+Shift+5` → *Record Selected Window*), 1280x800, mic off, phone off camera, the
browser in **English** and the **light** theme — both are the defaults, and English is what the
judges read. Between takes: `bash video/reset.sh`, then delete the old `video/raw.mov`.

Three things about the window itself, each of which cost something the first time:

- **Take Chrome out of full screen first.** A full-screen window ignores the resize and stays at the
  display's size — the discarded take is 1512×787, not 1280×800.
- **Relaunch Chrome with the debugger banner off, with Chrome fully quit first** — if it is already
  running the flag is ignored in silence:
  `open -a "Google Chrome" --args --silent-debugger-extension-api`
- **Let the panel hydrate before the first click.** A click straight after `navigate` does not fire
  the `onClick`. It happened twice in one rehearsal.

**The recorded window has exactly one tab, and nothing the human reads lives in it.** A window
capture records whichever *tab* is in front, and Claude's screenshots do not: the extension
photographs the tab it drives, so Claude sees the demo while the file records whatever the human
switched to. It cost a full take — two files, seven beats, and the reading sheet on screen for all
of it, with Claude reporting "going perfectly" the whole way. The patient's lines go on a phone.
Everything else — this chat, mail, the tunnel dashboard — goes in the **other** Chrome window
(`Cmd+N`, never `Cmd+T`). One tab is also what keeps the tab strip clean, and the strip is in every
frame: the discarded take has LinkedIn, WhatsApp, Gmail and "Las líneas de Ana" legible across the
133 seconds of it that were otherwise usable.

**Pull a control frame 30 seconds in and look at it.** It is the only check on any of the above that
does not go through Claude, and if the take is already wrong it is what the mistake costs.

```bash
ffmpeg -v error -ss 30 -i video/raw.mov -frames:v 1 -y /tmp/control.jpg
```

One tab, the demo on it, and no *"Claude started debugging this browser"* banner. To sweep a finished
file for the same fault, the reading sheet is dark and the demo is light, so one number every five
seconds separates them:

```bash
ffmpeg -v error -i video/raw.mov -vf "fps=1/5,crop=iw*0.6:ih*0.5:iw*0.2:ih*0.35,\
signalstats,metadata=print:key=lavfi.signalstats.YAVG:file=-" -f null - 2>/dev/null |
  paste - - | sed -E 's/.*pts_time:([0-9.]+).*YAVG=([0-9.]+)/\1 \2/'
```

## The day, in order

Nothing below is optional and the order is the whole point. Three of these steps are rehearsals, and
they exist because the expensive thing here is not the recording — it is the quota. **Each live call
spends about seven Gemini requests**, so a rehearsal plus a take plus a verification is more than
sixty, and an exhausted quota does not fail cleanly: it answers with a generic error that reads, on
camera, as a bug in the agent.

**Rehearsal 1 — the choreography. No phone, no voice, nothing spent.**

```bash
GEMINI_API_KEY= make take     # ScriptedLLM: the keyless buttons are free and repeatable
```

Walk the whole shot list with the keyless buttons: every click, every scroll, the order of the cards,
the window at 1280×800, the debugger banner gone, the hydration pause before the first click. Record
it and throw it away, then sweep the file for a notification or a second tab. **This is where takes
are lost, and here they cost nothing.**

**Rehearsal 2 — the phone. You answer it; Gemini is not involved.**

```bash
make smoke PHONE=+54911...    # one <Say>, nothing else
```

Proves the geographic permissions, the trial-number verification, how the line sounds, and that you
pick up in time. Cheapest thing in the session and the one worth repeating.

**Rehearsal 3 — one full call, once.**

```bash
MEMORY=off make call          # no phone argument: it resolves DEMO_PHONE, the branch the buttons use
curl localhost:8001/calls/<id>/trace
```

Answer the phone and play the week-1 lines from [`video/lines.html`](../video/lines.html), one per
question. The trace has to show the greeting, the four questions in order, both speakers in the
transcript, and the facts with their
quotes. **That closes C1.** It is also where the rhythm is learned, and the rhythm is now yours rather
than an actor's: **wait for the agent to stop talking before pressing space.** Press early and the
recogniser hears the two voices at once. And it is where a mis-transcribed number shows up, because
beats 3 and 4 run the recogniser unprimed. If
*seven out of ten* comes out wrong here, it comes out wrong on camera.

Then `make smoke-analysis URL=<recording url>` on that call, and the panel rehearsal: `bash
video/reset.sh`, `--check` all green, press **Real phone, no memory** and watch the live card fill.

`--check` was run on 25 Sep against a fresh `make take` and **ten of its eleven invariants are
green**: one patient, the five week-1 facts, nothing retired, one call on file, credentials loaded,
`DEMO_PHONE` set, and both quotas alive. The eleventh is the ngrok tunnel, which only exists while
you are recording — it is the one that stays red until the day. The fact list is five and not four
because the commitments feature seeded a week-1 promise; `reset.sh` was still expecting the old four
and would have told you *do not record* on a perfectly good state.

**Then the sequence, and only then the take.**

1. The three calls back to back — beat 3, beat 4, beat 5 — **with no reset in between**, confirming
   that beat 5's opening quotes the 7/10 and that the file shows the strike-through and `FACT
   RETIRED`. **That closes C2.** Check the Gemini and AssemblyAI consoles before starting it.
2. `bash video/reset.sh`, `--check` all green, **and only now** record.

> **The most expensive mistake available** is doing step 1 after step 2 instead of before. The
> supersession runs one way per state of the seed, so re-shooting beat 5 always needs a reset first.

## The two paths

**Beats 3, 4 and 5 are shot live**: three real phone calls, dialled from the panel. That is the
decision for this video, and it is what closes C1 and C2. The keyless column below is the contract to
fall back to if a quota dies mid-session; the red flag in beat 6 stays keyless either way.

| | **live** — the one to aim for | **keyless** — the fallback |
|---|---|---|
| Needs | `.env` filled, ngrok up, C1 and C2 done | nothing |
| The call | a real phone rings; you answer it and [`video/lines.html`](../video/lines.html) speaks the lines below | the panel's own buttons |
| AssemblyAI | Universal-Streaming on real audio | not exercised |
| What the patient says | the lines in each beat, spoken by the page into the phone | nothing — the lines are already in `seed/scripts.json` |
| Risk | the model phrases differently every take | **the same risk, in the recording session** |

The patient lines are **the same in both paths**, because the keyless scripts were written from
them. So the extraction, the supersession and the key terms behave identically either way.
[`video/lines.html`](../video/lines.html) is the operating copy of those lines: it carries the agent's
cues, marks the conditional turns, and
speaks each line in English. The tables in the beats below are the same lines for reading; the page is
the one to have open during a take.

**Keyless does not mean deterministic on the day.** `build_llm` (`app/replay.py`) returns the real
model the moment `GEMINI_API_KEY` is readable, and the live path needs a filled `.env` — so during
the session the keyless buttons run Gemini too. They phrase differently every press and they spend
quota, exactly like a live call minus the phone. The only lever that makes them byte-identical is
starting the server with the key blanked:

```bash
GEMINI_API_KEY= make take     # ScriptedLLM: free, repeatable, and no live buttons at all
```

That is the rehearsal server, not the take server.

## The beats

| # | Beat | Track | On screen |
|---|---|---|---|
| 1 | `1:problem` | 17 s | The landing at `/`, the opening claim |
| 2 | `2:product` | 24 s | The landing: one sentence, then the three packs |
| 3 | `3:call-one` | 62 s | 🎯 Week 1 live. Nothing recalled, four questions, three facts extracted |
| 4 | `4:memory-off` | 24 s | Week 2 live with memory off: the generic protocol |
| 5 | `5:memory-on` | 68 s | 🎯 Week 2 live with memory on: the knee, and the 7/10 retired |
| 6 | `6:panel` | 55 s | The chart, the file, the key terms, what AssemblyAI heard, a red flag |
| 7 | `7:close` | 18 s | The model band on the landing, then the endcard |

Track lengths are what `video/out/timing.txt` measured; the recording can be longer, because
`fit-to-audio.py` keeps the moments where the screen changes at 1x and compresses the waiting.

---

### 1 · `1:problem` — the problem

**Screen:** the landing at `http://localhost:8001/`, top of the page, plain register.
**You:** nothing. Slow scroll to the problem statement, one pause on the number.

INTENT §9 called for a slide here. The landing says the same thing and was designed for exactly this
audience, so a slide would be a second copy to keep in sync. It is filmed locally: the public deploy
does not exist yet ([`PENDINGS.md`](PENDINGS.md) row 1), which changes nothing on camera — the URL
bar is not in frame.

---

### 2 · `2:product` — the product in one sentence

**Screen:** keep scrolling the landing: the one-sentence description, then the three-pack band
(rehab / postpartum / chronic).
**You:** nothing.

---

### 3 · `3:call-one` — week 1, live 🎯

**Screen:** the panel at `/panel`, Ana selected, camera on the **live call card** — the transcript
and the activity rail. The rail opens with `CALL · started · memory off`; the line that matters is
the **second**, `MEMORY OFF · recall skipped`, with *memory disabled for this call* under it. That
is what makes it week one.

**live:** press **Real phone, no memory**. A call started from a terminal never reaches this card —
the page only follows the call its own `POST /calls` returned — so every call in this video is
pressed on screen. You answer off camera and play one line per question from
[`video/lines.html`](../video/lines.html), waiting for the agent to finish each one:

| | The patient says |
|---|---|
| greeting | «Hello, yes, this is Ana.» |
| pain | «My right knee hurts seven out of ten, especially when I climb stairs.» |
| adherence | «I did the exercises three times, I skipped two days because I had a lot of work. Next week I will do them every day.» |
| read-back | «Yes, three times.» — **only if the agent asks you to confirm the number** |
| side effects | «After the exercises it stays a little stiff, nothing strange.» |
| red flags | «No, no falls, nothing like that.» |

The last sentence of the adherence line is the promise, and it is the reason beat 5 has a turn the
other two calls do not: it is what the extractor stores as a `commitment`, and what the agent asks
about a week later. Dropping it costs beat 5 its best turn.

With memory off the `recall` phase is skipped, so the agent genuinely has nothing in its prompt —
that is what makes it week one on a seeded patient. It also means **no `keyterms_prompt` is sent**:
`set_keyterms` lives inside `recall` (`app/orchestrator.py:36`), so this transcription runs unprimed
and the "patient line mis-transcribed" row below is at its most likely here. Play the four numbered
lines through the chosen voice before the take and listen to them: a voice that says *seventh* instead
of *seven out of ten* is found here or it is found on camera.

**keyless:** the panel's **Call without memory** button, which runs the week-1 script.

**What the camera must catch:** the transcript filling turn by turn, and then the activity rail:
`MEMORY OFF recall skipped`, `EXTRACTION 3 facts from the transcript`, `MEMORY OFF storage skipped`.

Those three are the ones the narration names. A live call writes more around them — `SUMMARY`,
`RECORDING ready`, `ANALYSIS N entities`, `CALL ended`, and `RETRY` or `DISCARDED` when something
goes wrong. None of them is a problem on camera; the beat just does not stop on them.

The per-fact lines with their quotes do **not** appear here: with memory off nothing is stored, so
`fact_stored` never fires. The quote-and-turn proof is beat 5's `NEW FACT` lines and the file in
beat 6. Do not promise it in this beat.

---

### 4 · `4:memory-off` — week 2, memory off

**Screen:** the panel, same patient, still on the live call card. The narration says "one week
later"; nothing on screen has to.

**live:** press **Real phone, no memory** again — same button as beat 3, same switch off. Answer
with the week-2 lines:

| | The patient says |
|---|---|
| greeting | «Hello, yes, this is Ana.» |
| pain | «My knee is a lot better, it is four out of ten on the stairs now.» |
| adherence | «I did them five times this week, I got myself better organised.» |
| side effects | «No, no new discomfort.» |
| red flags | «No, nothing like that.» |

Five turns, not six: with memory off `questions_for()` has no `commitment` on file to ask about
(`app/orchestrator.py:119-128`). The same five lines are in
[`video/lines.html`](../video/lines.html) under beat 4.

**keyless:** the panel's **the same call without memory** link. It runs the `week2-off` script: the
week-2 answers with the generic agent lines, because an agent with no memory block cannot open on the
knee.

**No reset between beats 3, 4 and 5.** With memory off `store_facts` returns before the fact loop, so
beats 3 and 4 write no facts: last week's 7/10 is still on file and still current when beat 5 dials.
A reset is only needed before **re-shooting** beat 5, because the supersession only runs one way per
state of the seed.

They do write their **call row**, though — turning memory off stops the agent remembering, not the
call being on the record. The seed already ships one call on file, dated Sep 15 and tagged *with
memory*, and `video/reset.sh` checks for exactly that before a take — so by beat 6 the *Calls so
far* card shows **four** rows: the seeded one, beats 3 and 4 tagged *without memory*, and beat 5
tagged *with memory*. That tag is the A/B in the record rather than only on screen. The narration
says *three calls* because three is what the camera watches happen; the card shows four because the
file did not start empty.

**The point of the beat is the question, not the answer.** She says the knee is at four out of ten
and the agent has no idea that means anything: it never asks about the knee, and the rail shows
`MEMORY OFF` on both the recall and the store phases. Thirty seconds of honest "before".

Cut this beat first if the track ever needs to lose time.

---

### 5 · `5:memory-on` — week 2, memory on 🎯

**Screen:** the panel. This is the beat the project exists for.

**live:** press **Real phone, with memory**. This is the only call in the video where the key terms
are actually sent — `set_keyterms` is inside `recall`, which beats 3 and 4 skip — so it is also the
best-transcribed of the three.

**Wait through two agent turns before the first line.** With memory on the greeting is followed by the
answer the professional left for her, spoken word for word (`app/orchestrator.py:112-113`). Pressing
space after the first one talks over the relay, which is the one turn that demonstrates it.

Six turns here, not five — the promise is asked about before adherence:

| | The patient says |
|---|---|
| greeting | «Hello, yes, this is Ana.» |
| pain | «My knee is a lot better, it is four out of ten on the stairs now.» |
| the promise | «I did better with the daily plan, I managed five of the seven days.» |
| adherence | «I did them five times this week, I got myself better organised.» |
| side effects | «No, no new discomfort. Should I start going up the stairs normally again?» |
| red flags | «No, nothing like that.» |

The question at the end of the side-effects line is deliberate: the agent is not allowed to answer it,
so the extractor puts it in the professional's queue. That is what the panel's question card shows in
beat 6. Both turns are in [`video/lines.html`](../video/lines.html) under beat 5.

**keyless:** **Call with memory**. With Ana's file populated, `run_scripted` picks the week-2 script
on its own (`app/replay.py:49`) and the scripted patient says exactly those lines. This one runs the
real pipeline, not a recording: the supersession happens on camera.

**What the camera must catch,** in this order:

1. The agent's **first sentence**, which quotes last week: "last week you told me your knee hurt
   seven out of ten climbing stairs".
2. In the file, the 7/10 going **struck through** under the new 4/10, with `RETIRED` beside it.
3. The rail line `FACT RETIRED`.

If the agent phrases the opening differently — it will — that is the take. Rewrite the caption.

---

### 6 · `6:panel` — what the professional sees

**Screen:** scroll the panel, top to bottom, pausing on each card:

1. **How she is doing** — pain 7 → 4, sessions 3 → 5, with the verdict arrows.
2. **What the agent remembers** — the chain, with the retired entry still there and its quote.
3. **Words the agent listened for** — the three-step drawing and the chips: her own vocabulary,
   handed to AssemblyAI as `keyterms_prompt`. The list has **two sources** since the key phrases
   landed: the terms of the facts on file, and the phrases Speech Understanding pulled out of the
   most recent analysed recording. In a take that means beat 5 may carry a phrase heard in beat 3
   or 4, if the recording webhook landed before it dialled — a bonus if it shows, never a problem
   if it does not.
4. **Calls so far**, and inside beat 5's row, **What AssemblyAI heard in the recording**: the
   entity chips it pulled out of the audio — `right knee`, `four out of ten`, `five times this
   week` — the sentiment counts beside them, with the negative one tinted, and under them the
   **key phrases** with how often each was said. This is the sponsor's second product in the same
   demo, and the two are wired into a loop rather than sitting side by side: Universal-Streaming
   carried the call, Speech Understanding read the recording Twilio kept after it, and its key
   phrases go back out as the next call's `keyterms_prompt`. It only exists after a **live** call,
   which is what beats 3, 4 and 5 are.

   **The narration does not change for this.** Its two lines here are generic — *"After she hangs
   up, the recording goes back to AssemblyAI"* and *"What she named, and how she sounded saying
   it"* — and card 3's is *"And the words that primed the recogniser"*, which says nothing about
   where they came from. A third chip row and a second source are both covered by what is already
   in `video/narration.tsv`, so the 267.8 s track and `OUTRO_REPLACE` stand.
5. **The red flag, last.** Press **call with a red flag** — this one stays **keyless** on purpose:
   a real call buys nothing here and saves a fourth phone call per take. The patient reports a
   fall, the guard stops the call, the remaining questions are never asked, and the row lands
   marked `ESCALATED`.

**The red flag has to be the last thing filmed in this beat.** Its script
(`seed/scripts.json`, `alarm.facts`) carries `right knee pain 5/10` and `did the exercises twice`,
so pressing it **retires the 4/10 that beat 5 just created**, puts a third point on the chart, and
makes the alarm call the newest one — which is what the key-terms card reads. Film cards 1 to 4,
then press it.

The key-terms card reads the **newest** call (`rows[0]` in `PatientView.tsx`, ordered
`started_at desc`) and `queries.keyterms_at` filters to the facts current *before* that call, so
after beat 5 it still shows the five week-1 terms. Nothing to reset for it — as long as the red
flag has not been pressed yet.

The red-flag call takes about 25 s of wall clock and the narration gives it about 6 s — that is what
`fit-to-audio.py` compresses. Let it run in full on camera; do not cut it short by hand.

Cut the key-terms card second if the track needs to lose more time. The AssemblyAI card is not on
that list: it is the one thing in this beat that a judge for *Application of Technology* is looking
for.

---

### 7 · `7:close` — business and endcard

**Screen:** the landing's **model band** (`#business`), to the end of the take. **The endcard is not
on camera** — it is a still appended at assembly, so nothing opens a `file://` URL in the address bar
on screen.

The band is three columns — *Who pays*, *What it costs*, *What it costs to run* — and it exists
because this beat filmed it before it did: the narration said *sold per professional* over a page
that had nothing of the sort on it. Scroll to it from the nav (**Model**), do not hunt for it.

The hostname is `constancia-voice.onrender.com`, which is what `render.yaml` claims — plain
`constancia.onrender.com` belongs to an unrelated app, so Render would have appended a random suffix
and the card would have pointed at somebody else's form. Re-render the card if the deploy ever lands
on a different hostname; it is spliced in after the take, so it never delays recording.

**The service does not exist yet**, so the card currently names a URL that 404s. Verify before
uploading, because a burned-in address that answers nothing is worse than no address:

```bash
curl -s -o /dev/null -D- https://constancia-voice.onrender.com/health | grep -i 'HTTP/\|x-render-routing'
```

`x-render-routing: no-server` means Render has no service on that hostname. Either the deploy lands
before the upload, or the card points at the GitHub repo instead.

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

On the track built on 24 Sep — **267.8 s = 4:27.8**, 53 captions — it prints `2.4`. Assemble with:

```bash
VIDEO_DIR=$PWD/video MAX_SECONDS=300 \
  OUTRO="video/out/endcard.png:5" OUTRO_REPLACE=2.4 \
  bash ~/.claude/skills/personal-record-video/scripts/build-video.sh video/out/raw-fitted.mov
```

The pipeline was verified end to end against a synthetic recording on an earlier, shorter track:
1920x1080, under the cap, the card up with the final caption on it and quiet after. What it does was
proved; the durations move with the track, so the figures to trust are the ones above.

**One constraint this puts on the take:** `build-video.sh` refuses a recording that is not within
0.75x–1.30x of `narration − OUTRO_REPLACE`, which is **265.4 s**. Anywhere between **3:19 and 5:45**
of raw screen time is fine; `fit-to-audio.py` lands it far closer than that.

## What can come out differently

The agent is not deterministic on the live path. Things that change between takes, and what to do:

| What changes | What to do |
|---|---|
| The greeting's exact wording | Nothing. It always carries the knee and the 7/10; the caption says so, not the sentence |
| The order of the facts in the rail | Nothing; the quote and the turn number are what the beat claims |
| A question phrased as two sentences | Nothing |
| The agent skipping a question | Stop the take. That is a bug, not a phrasing |
| A fact landing without a quote | Impossible by construction — `ground()` rejects a blank quote too |
| The patient line mis-transcribed | Re-shoot that call. The key terms exist to prevent exactly this, and beats 3 and 4 do not get them |
| Nobody answers, or the audio stream never opens | The panel says so — *Nobody picked up* / *audio stream timeout* — instead of hanging. Stop the take and dial again |
| The read-back never fires | Nothing. A synthesised voice is cleaner than a person on a phone line, so `low_conf` may never cross the floor. The read-back is demonstrated by the keyless **Call without memory** button, where the script declares it |

## If the track goes over 300 s

Decided now, not on the day:

1. Cut beat 4 (`4:memory-off`) to its first two lines.
2. Cut the key-terms card out of beat 6.
3. Nothing else. Beats 3 and 5 are the video.
