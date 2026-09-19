# constancia — public landing and the Nocturne pass

> **This is a record, not a reference.** Written as a spec before the landing was built, and since
> half-converted into a log — the *Deviations from the design* section is past tense, the rest is
> not. What it still owns is the reasoning: the OKLCH derivation of the light theme with measured
> contrast ratios, and the design of the copy types. For the front end as it is today, read
> [`FRONTEND.md`](FRONTEND.md).

Stage 4 work, written up before it is built. Implements the Claude Design file **`Constancia Landing.dc.html`** (project `a0ec86f1-c514-4b03-b8b0-2404abd0f7f2`, design system **Nocturne** `nocturne-487bbaa7`), brings the professional's panel under the same tokens, and gives both pages three reader preferences: **theme**, **language** and **register**.

## Context

Stages 1 to 3 are done: the agent phones, remembers, and the panel shows the supersession chain live. All of it is served at `/`.

The gap is presentation, not product. The public URL opens straight into the panel: a judge lands on a working tool with no explanation. `INTENT.md` §5 counts *Presentation* and *Business Value* as half the score, and today nothing on screen defends either.

But the landing has two readers who do not want the same page. A hackathon judge needs "Universal-Streaming v3 over Twilio Media Streams, µ-law at 8 kHz" — that is the *Application of Technology* evidence. The buyer in `INTENT.md` §4 is an independent physiotherapist, and that sentence means nothing to them. One page cannot be written for both at once, so it is written twice and the reader picks. Same for the language: the judges read English, the market speaks Spanish.

When this lands: `/` is the landing, `/panel` is the panel, both in Nocturne, both reading the visitor's theme, language and register, all of it with no keys and no database.

## What the design gives us

Nocturne is **CSS only**. `_ds_bundle.js` is empty (`components: []`) and `support.js` is the canvas runtime (`x-dc`, `sc-if`, `sc-for`, `DCLogic`). None of that is ported — in React those are conditionals, `.map()` and state.

From `styles.css` we take the tokens — `--color-bg #161826`, `--color-surface #232532`, `--color-text #e9e9ed`, the blurple accent `--color-accent #9184d9`, the `neutral-100..900` and `accent-100..900` ramps, `--color-section` / `--color-section-glow`, Inter, `--radius-*`, `--shadow-*`, `--space-*` — and the classes `.btn`, `.tag`, `.hr`, and `.seg` + `.seg-opt`, the system's own segmented control on native radios with no script. That last one is what the toggles are built from.

The landing is seven blocks: sticky header; hero with copy left and a live demo card right; a metrics band on the section gradient (70% / 3 verticals / 333 h / 95 tests); *How it works* in four steps; *Memory* in four cards; *Stack* with the five services and the honest limits; a closing CTA; a footer. Six own keyframes: `noc-in`, `noc-slide`, `noc-pulse`, `noc-strike`, `noc-breathe`, `noc-wave`.

The demo card is a scripted loop (`SCRIPTS.week1` and `SCRIPTS.week2`, each a list of beats with delays) behind a week selector, played at `PACE` (1.6) times the delays written into the beats, with two views: `call` (transcript plus activity rail) and `chain` (the facts as dated links, the retired one struck through). Step back, pause, step forward and replay sit under both.

Every number the design prints is already true of this repo: 70% non-adherence (`INTENT.md` §3.1), three packs, 333 free STT hours, 95 tests green.

## Decisions

- **Landing at `/`, panel at `/panel`.**
- **The demo card keeps the design's scripted loop**, not the real SSE replay. Deterministic, no network, tuned to the hero.
- **The panel is restyled to Nocturne.**
- **Three preferences**: theme (dark / light), language (English / Spanish), register (technical / plain). The panel carries theme and language but **not** register — it is a tool, not a pitch, and duplicating its ~56 strings across two registers is work spent on the surface nobody judges.
- **English is the default language.** Deterministic: the judge always opens the same page. Spanish is one click, or one `?lang=es`, away.
- **Light is the default theme**, and `prefers-color-scheme` is deliberately not consulted. Defaulting to the derived theme is only defensible because the corrections below bring it to parity — every role measured clears AA on the light ground, which was not true of the naive mirror. The default is one line in three places that must agree: `initialTheme()` and the pre-paint script in each entry. Honouring the media query instead is a one-line change in the same three.
- **The light theme is derived from Nocturne's own ramps**, with no new hex values invented. Since it is what a first visit shows, its contrast is the one that has to hold.

## The light theme is a derivation, not a mirror

Nocturne is dark by design: its readme opens with "a quiet, compact dark interface", the shadow tokens are "already tuned to the ground", and `.lighten` (`mix-blend-mode: lighten`) only makes sense over a dark backdrop. We get away with it because **our landing has no photographs**, so `.lighten` never comes up.

The derivation rule is the readme's own: on a dark ground the light ramp steps carry text and the dark ones carry fills; on a light ground that inverts. The ramps are OKLCH on one shared lightness scale, so the inversion is principled rather than guesswork.

**It is not symmetric.** The dark ground `#161826` sits much closer to black than the light ground `#e4e7f5` sits to white, so mirroring the step number produces a light theme that fails contrast. Measured against their own grounds, WCAG 2.1 relative luminance:

| Role | Dark | Ratio | Light | Ratio |
|---|---|---|---|---|
| body text | `--color-text` `#e9e9ed` | 14.6:1 | `--color-neutral-900` `#292b31` | 11.5:1 |
| muted text | `--color-neutral-400` `#b2b6ca` | 8.8:1 | `--color-neutral-600` `#75798c` | **3.5:1 — fails** |
| muted text, corrected | — | — | `--color-neutral-700` `#595d6c` | 5.3:1 |
| accent base | `--color-accent` `#9184d9` | 5.5:1 | `--color-accent-600` `#796cbf` | **3.6:1 — fails** |
| accent base, corrected | — | — | `--color-accent-700` `#5d5294` | 5.5:1 |
| accent body text | `--color-accent-300` `#d2cefd` | 11.7:1 | `--color-accent-800` `#423a6a` | 8.1:1 |

Two corrections worth naming, because both look wrong until you do the arithmetic:

**The accent base on light is `accent-700`, not `accent-600`.** The readme's "`--color-accent-600` on a light ground" sits inside *Interaction states*, describing the pressed step, "one step past the base". Reading it as the base drops the `.btn-primary` label — 14px text, not chrome — to 3.6:1, where the same button on dark gives 5.5:1. That is a regression the system itself does not have. With the accent base at 700, `--text-accent` moves down to `accent-800` or it collides with the base and the kicker/body distinction the design relies on disappears.

**Muted text on light is `neutral-700`, not `neutral-600`** — 5.3:1 against 3.5:1. It is used in the footer (11.5px), the hero sub-labels (12px), the Stack card bodies (11.5px) and the demo card's `h6` (10px): all small text, all below AA at 600.

**The `color-mix()` opacities are the same trap in a different costume.** The design writes secondary text as `color-mix(in srgb, var(--color-text) N%, transparent)` at six different percentages — 55, 62, 66, 70, 74. They read fine on dark because full-strength text starts at 14.6:1, so there is headroom to spend. On light the headroom is 11.5:1 and everything at 13.5px or smaller falls under AA: the nav links at 62% blend to roughly `#70727b`, **3.9:1**. Six percentages are one decision wearing six hats, so they collapse into a single alias with a deeper value on light. Nocturne's readme asks for this independently: "prefer ramp steps over ad-hoc `color-mix()`".

**Consequence: nothing outside the theme block may name a ramp step or a text opacity.** Each becomes a semantic alias defined once per theme:

| alias | dark | light | why |
|---|---|---|---|
| `--text-secondary` | `text` at 70% | `text` at 82% | replaces all six percentages |
| `--text-muted` | `neutral-400` | `neutral-700` | one step deeper than the mirror |
| `--text-accent` | `accent-300` | `accent-800` | must clear the accent base |
| `--section-ink` | `neutral-100` | `neutral-100` | invariant — see below |
| `--tone-dim` | `neutral-500` | `neutral-700` | the rail's "retired" border and label |
| `--fill-subtle` | `neutral-800` | `neutral-200` | tinted fills |
| `--color-danger` | a light red | a deep red | a **pair**; no single hex clears both grounds |

**The metrics band is the one that bites.** `--color-section` is a saturated indigo that stays put in both themes, which is right — the band is dark either way. But its four big numbers declare no colour of their own: they inherit `--color-text` from the wrapper. On light that is dark ink on dark indigo, **1.07:1 — invisible**. The sub-labels survive by accident because they are mixed from `--color-neutral-200`, which does not change between themes. Hence `--section-ink`, an alias that is deliberately the same in both themes, and four inline colours that stop inheriting.

`--shadow-sm/md/lg` are hardcoded hex values, not token references. The light theme redeclares **all three**, including the `0 0 0 1px` hairline ring — on a near-white ground that ring is the part you actually see, and a dark one reads as a bug.

`--color-danger` does not exist in Nocturne at all. The panel needs it for red flags and escalation, and it has to be a pair: the panel's current `#b03636` gives 4.97:1 on light but 2.87:1 on dark. Record it as a gap in the system.

## Copy: two languages × two registers

Four combinations, but not four documents. Only the prose changes register — nav labels, button text, service names, stat numbers and the footer read the same to an engineer and to a physiotherapist. So each language ships one full set plus a partial override of the roughly twenty-five keys that actually change.

```
web/src/landing/copy.ts

  type Copy                    the single source of keys; interpolated strings are
                               typed as functions, not as string
  const en: Copy               technical register, English — the annotated base
  const es: Copy               technical register, Spanish
  const enPlain = {...} satisfies Partial<Copy>
  type PlainKey = keyof typeof enPlain
  const esPlain: Record<PlainKey, string>
  copy(lang, register)         base[lang], then the override when asked for
```

**`tsc` is the only check there is** — the front end has no test runner, and `pnpm build` runs `tsc`. That shape is what makes it a real one:

- `const es: Copy` makes a missing Spanish key a build error. EN/ES drift is covered.
- A key in an override that does not exist on `Copy` is also an error: the excess-property check fires on an object literal checked against an annotation.
- The hole that stays open without the last two lines is that **nothing ties `enPlain`'s keys to `esPlain`'s**. Simplify twenty-five keys in English and twenty in Spanish, and the plain register silently serves five technical sentences to a Spanish reader. `satisfies` keeps both the check against `Copy` and the literal key type; `Record<PlainKey, string>` then demands exactly that set.
- Roughly ten strings interpolate a value (`${n} facts on file`, `turn ${n} · streaming`). Typing those as `string` and concatenating works in English and breaks in Spanish, where the word order moves. They are typed as functions on `Copy`.

The panel gets its own `copy.ts` with its own type and **one register**. The two surfaces do not share a single string, and one shared 116-key type would only guarantee that every error lands in the same enormous file.

**The panel also printed raw backend values** when this was written — none of them reachable by a `copy.ts` on its own, and wrong even in Spanish. All four are fixed: the maps live at the end of `web/src/panel/copy.ts` and are resolved through `label()`; the `switch` in `ActivityRail` is now closed; and `WeeklyChart` labels its axis with real dates. The list is kept as the record of what was wrong:

- `FactChain` renders `fact.category` verbatim — `symptom`, `adherence`, `mood`, `clinical_value`, `red_flag` from `app/extract.py`. Needs a five-entry map per language. So does `patient.program_type`.
- `ActivityRail` prints `event.rule` from the guard (`sudden_sharp_pain`, `fall`, `swelling_with_fever`), `event.phase`, and `event.reason` — which arrives as literal English from `app/extract.py` and `app/orchestrator.py`.
- Its `switch` falls through to printing the raw event type as a label.
- `WeeklyChart` does `week.week.replace("-W", " s")`, where that `s` is *semana*. A language dependency hidden inside a string method.

**With `lang=en` the panel shows English chrome over Spanish data.** The summary is written by the agent, and the facts, quotes, key terms and transcript are the patient's own words. That is correct — the patient is not the visitor — but it belongs in this document rather than being discovered while recording.

## Assumptions

- `panel/` is renamed **`web/`**: it stops being a panel and becomes two pages. Six mechanical reference updates — `app/main.py`, `Dockerfile`, `Makefile`, `.gitignore`, `README.md`, `SUBMISSION.md`.
- **Vite multi-page, no router**: `web/index.html` and `web/panel/index.html` as two `rollupOptions.input` entries. No routing library, no SPA fallback, and the landing does not drag the panel's bundle.
- `StaticFiles(html=True)` resolves a directory to its `index.html`, so `/panel` needs no new route. **Verify with `curl` first**; if Starlette does not resolve it without a trailing slash, add an explicit `@app.get("/panel")` returning a `FileResponse`.
- Nocturne's `.card` and `.nav` collide with the panel's own, and so does `.tag` — the panel's is a 10px uppercase pill, the system's is an 11px ramp-tinted label, and `FactChain` generates classes like `.tag-symptom` that exist nowhere. The panel's gets renamed; the shared sheet carries only tokens, reset, `.btn`, `.tag`, `.seg` and `.hr`.
- **`localStorage` can throw on read**, not only on write, under partitioned storage. Every access is wrapped; on failure the pages render on the defaults, which is dark and English.
- Nothing is committed without an explicit request.

## Files

```
  web/                       renamed from panel/; package name constancia-web
    vite.config.ts           rollupOptions.input: { landing: index.html, panel: panel/index.html }
    index.html               landing entry + pre-paint theme script + color-scheme meta
    panel/index.html         panel entry + the same two
    src/tokens.css           Nocturne :root, the derived [data-theme="light"], the aliases,
                             color-scheme per theme, reset, type scale, .btn .tag .seg .hr
    src/prefs.ts             usePrefs(): theme, lang, register; guarded localStorage;
                             writes data-theme and documentElement.lang; reads ?lang= at boot
    src/landing/
      main.tsx
      Landing.tsx            the seven sections, aliases in place of ramp steps
      DemoCard.tsx           SCRIPT + CHAIN + renderVals — colours live here as DATA
      copy.ts                en / es, plus the plain overrides
      landing.css            the six noc-* keyframes, under prefers-reduced-motion
    src/panel/               the eight existing files
      copy.ts                en / es, one register, plus the backend-value maps
      panel.css              renamed from styles.css, retuned onto the aliases
  app/main.py                PANEL_DIST -> WEB_DIST, pointing at web/dist
  CLAUDE.md                  the English-only rule gains its second exception
```

## Steps

1. **Rename `panel/` to `web/`** — the eight panel files move to `web/src/panel/`, `web/src/landing/` is new, `package.json` becomes `constancia-web`.

2. **`web/src/tokens.css`** — Nocturne's `:root` as shipped, the `[data-theme="light"]` block derived as measured above, the seven aliases defined once per theme, `color-scheme` per theme, the re-tuned light shadows, the reset, the type scale, and `.btn` / `.tag` / `.seg` / `.hr`. Not `.card`, `.nav`, `.input`, `.table` or `.dialog` — nothing uses them. Inter from Google Fonts, as the system does.

3. **`web/src/prefs.ts`** — `usePrefs()` returning the three preferences and their setters. Its initial state must be **lazy and read the same source the pre-paint script reads**: starting from a fixed default means the first effect overwrites the `data-theme` the script already set, and a visitor who chose light sees a dark frame on every load. It writes `documentElement.dataset.theme` and `documentElement.lang`, and reads `?lang=` once at boot so the Spanish landing has a shareable link.

4. **The pre-paint script** — four guarded lines inline in both `index.html` files, plus `<meta name="color-scheme" content="dark light">` for the browser's own canvas in the window before CSS arrives. In `pnpm dev` a white flash is unavoidable because Vite injects CSS through JS; that is a dev-server artefact, not a bug to chase.

5. **`web/vite.config.ts`** — the two entries; the existing dev proxy (`/patients`, `/calls`, `/health`, `/reset`, `/search`) is unchanged.

6. **`web/src/landing/copy.ts`** — the four sets in the shape described above. The technical register is the design's own copy, verbatim; the plain register is written fresh for a professional who does not know what a WebSocket is.

7. **`web/index.html` and `web/src/landing/`** — the seven sections in JSX, keeping the design's inline styles (each encodes a `clamp()` or a `color-mix()` decided there) with every ramp step and text opacity swapped for an alias, and every string from `copy()`. **`DemoCard.tsx` needs the same treatment on its data, not just its styles**: `SCRIPT`, `CHAIN` and `renderVals()` carry `var(--color-accent-300)` and `var(--color-neutral-500)` as *values*. Rewriting only the styles leaves the agent's turn at 1.4:1 and the supersession line at 2.4:1 on light — the two things the landing exists to show. `landing.css` puts the six keyframes under `prefers-reduced-motion`, and `DemoCard` renders the final step without scheduling when the query matches: ten infinite animations is exactly what that query is for.

8. **The controls** — language and theme in the header (`.seg` and `.btn-icon`, with `aria-label` and `aria-pressed`); the register toggle under the hero paragraph, not in the header, because it changes the prose rather than the chrome and that is where the reader first meets prose. All three inherit Nocturne's hover, pressed and `:focus-visible` states, which follow `--color-accent` and therefore need no theme work of their own.

9. **`web/panel/index.html` and `web/src/panel/copy.ts`** — translate the panel to English **first**, which `CLAUDE.md` already required and which was pending, then add Spanish as the second language: `en` is the annotated, authoritative set. Include the maps for the raw backend values listed above, and narrow the `switch` so an unmapped event type cannot fall through to printing its own name.

10. **`web/src/panel/panel.css`** — the panel on the aliases so both themes work. Four hard-coded light-theme hex values need theming: the agent and patient turn backgrounds, the rail's `flash`, and the `.tag-red_flag` pair. Rename the panel's `.tag`. Do **not** map `--write` to `--color-accent-2`: the readme calls accent-2 "a machine-derived stand-in … treat them as one role", and its 100–300 steps are literally the same hex values as accent's, which would make `stored` and `superseded` indistinguishable in the rail — the one contrast the demo exists to show. It becomes `--tone-dim`, which the label text and the strike-through already disambiguate.

11. **`app/main.py`, `Dockerfile`, `Makefile`, `.gitignore`** — `PANEL_DIST` becomes `WEB_DIST` at `web/dist`, mount stays at `/` and stays last.
    Both entry pages are served by explicit routes rather than by the mount, so they can carry `Cache-Control: no-store`. Vite hashes the asset filenames but not `index.html`, and a cached `index.html` keeps naming the bundles it was built against: rebuild, reload, and the browser serves the previous build with no sign anything is stale. The pages are ~1.1 kB, so never storing them costs nothing, and `/assets/*` stays cacheable through the mount, which is the half that matters. `panel/` → `web/` across the five Dockerfile lines, `make panel` / `panel-dev` → `make web` / `web-dev`, and the two ignore entries.

12. **`CLAUDE.md`** — the rule says the only Spanish in the repo is what the patient hears in `app/packs.py`. A bilingual interface adds `web/src/*/copy.ts`. Amend it rather than leave the repo quietly breaking its own standard.

## Deviations from the design

1. **The landing gets links to `/panel`, and the panel gets one back.** The design anchors every CTA to `#demo` because it did not know an app existed at another route. The header button and the closing secondary CTA point at the panel: a landing with no way into the product is a dead end.
   The reverse was a dead end too. The panel's only way home was the `constancia` wordmark, which carries no underline, no icon and no hover cue until the pointer is already on it — a convention, not an affordance, and useless to anyone who does not know to try it. The sidebar now has a labelled `← Home` under the store line, matching the landing's explicit *Open the panel* rather than relying on a reader guessing that a heading is a link. The wordmark stays a link as well; it costs nothing.
2. **The `chain` view plays by itself when the script ends, and is laid out as a chain.** On the canvas `hero` is an enum the designer flips by hand; the landing renders one. The script already ends on a 3.2 s hold and `CHAIN` is already computed — showing the chain during that hold uses both of the design's views and puts the payoff on screen. Then it loops back.
   The canvas nested the retired fact inside a tinted box under the current one, distinguished only by dimming and a rule drawn over it. Two near-identical sentences differing in one digit, and the reader had to infer which replaced which. It is now a two-link vertical timeline: a filled dot for the fact in force, labelled with the date it took effect, and a hollow one for the retired fact, labelled with the window it was true for (`31 Aug → 7 Sep`). Both values stay legible — the comparison between 7 and 4 *is* the story, so the strike-through covers the sentence and not the number.
   The strike itself was an absolutely positioned 1 px `div` at a hard-coded `top: 17`, spanning the full padded width: it overshot the sentence, crossed the value on the right, and would have floated free of any text that wrapped. It is now `text-decoration: line-through` on the text itself, with the `noc-strike` keyframe animating `text-decoration-color` from transparent. The browser owns the geometry, wrapped lines included.
3. **The card plays both calls, not just the second one.** The design shipped one script, the week-two call, and the page around it promised two: the hero CTA reads *Watch week 1 → week 2* and the closing block is titled *Two calls. One patient. That is the whole demo.* A judge clicking that button saw a single call, which is the kind of overclaim that costs more than the feature is worth. `SCRIPTS` now holds a week-one script — memory off, the agent asking from a blank file, the same two questions — and a `.seg` in the card header switches between them, resetting the player. Week one does not loop on itself: after its chain has held, the card moves on to week two, so choosing week one plays the sequence the CTA names rather than stranding the visitor on the call that proves nothing. Week two then loops, because it is the payoff and because a visitor who never asked for week one should not be made to sit through it.
   The two ends are what carry the argument, so they differ: week one closes on two facts with a single dated link each and *nothing to retire*, week two on the same two facts with their predecessors struck through beneath them. Week one's own note (`demoChainNoteFirst`) points forward — *the file was empty before this call; these two facts are what week 2 opens by asking about* — so the selector reads as a sequence rather than two unrelated demos. Week one's rail says `no facts on file · first call` where week two's says `4 facts on file`.
   There is no third copy of the data: week one's chain renders the `previous` half of each `CHAIN` entry as current, dated from `from` instead of `from → until`. The same fact, framed by which call you are watching.

4. **`replaySpeed` is not exposed, but a pause is.** Speed was a canvas knob and the landing pins it at 1 for the
   visitor. Internally the beats are stretched by a single `PACE` constant instead of nineteen edited delays:
   the design's timings put a fifteen-word sentence on screen for 1.5 s, which is under what it takes to read
   one. `PACE` multiplies the beats only — `CHAIN_HOLD_MS` stays at 4.2 s, because the chain is the frame
   people actually stop on and the pause button is there for holding it longer.
   Pause is the one playback control the card does surrender, and deviation 2 is the reason: the chain is the
   payoff, it plays on a timed hold, and a visitor who wants to read the struck-through fact should not have to
   wait out another full loop. It also stops the card from restarting under a narrator while the video is being
   recorded. `Replay` resumes as well as restarts, so the card can never be left frozen on its first frame.
   `↺` sits ahead of all of them and is the only control that resets the demo rather than the call: back to
   week one, first beat, playing. `Replay` deliberately keeps its narrower meaning — watch *this* call
   again — because after the selector exists, restarting the current week and restarting the sequence are
   different things and a visitor deep in week two wants both.
   Flanking it, `◀` and `▶` walk the script a beat at a time and pause on the way, which is how anyone gets
   to read a rail entry that is on screen for 600 ms. `▶` crosses out of week one into week two exactly as
   the timer does, so the button never refuses a move the loop would have made by itself; it greys out only
   at the end of week two, through Nocturne's own `.btn:disabled`. `◀` does not cross back: the selector is
   one click away, and a back button that rewinds into a different call is a stranger thing than a bounded
   one. Both are rendered under `prefers-reduced-motion`, where the pause button is not — that path pins the
   card on the chain and schedules nothing, so stepping is the only way that visitor sees the call at all.
   Pause stops two separate things, because the card has two clocks. The beats are a chained `setTimeout`, which
   the effect simply stops scheduling. The looping CSS — the live dot and the audio bars — is the browser's own,
   and stopping it takes `animation-play-state`. Without it the card would say *paused* while the dot kept
   pulsing, which reads as a hang rather than a pause.
   That rule names `.noc-pulse` and `.noc-wave`, the two that loop, and deliberately not every animation in the
   subtree. A one-shot entrance paused at its first frame never gets a second one: `noc-in` starts at
   `opacity: 0` with `fill: both`, so pausing inside its 0.34 s window strands that row invisible until the
   visitor resumes, and the card appears to have lost its content. A pause should stop what repeats, not
   abandon what was arriving.
   Under `prefers-reduced-motion` the button is not rendered at all: that path never animates, so there is
   nothing to pause.
5. **The call content is translated, and each language renders alone.** The agent really does speak Rioplatense
   Spanish, so the card shows a call that happened in Spanish. An earlier pass kept that Spanish on screen in
   both languages and hung a dimmed italic translation beneath every line, which left the English reader — the
   one who needs the translation — reading the money shot twice. Now every turn, every extracted fact, the
   key-term list and the quotes carry an `{ es, en }` pair and the card renders one side of it: English is
   English throughout, Spanish is Spanish throughout, and nothing is subtitled.
   The cost is that the quote travels with the rest. A translated quote is no longer verbatim, so in English the
   grounding claim narrows from *these are the syllables she said* to *this fact comes from turn 4* — which is
   what the turn number beside it already asserted, and what the panel can still prove against the real
   transcript. Each English quote is written as a literal substring of the English turn above it, so the card
   stays internally consistent. The pairs live beside their source in `SCRIPT` and `CHAIN`, not in `copy.ts`,
   because they translate that datum rather than the interface.
   The card header carried an `es-AR` tag, which was what named the call's real language and marked the English
   rendering as a translation. It was removed on request, so nothing on the card says so any more and the
   English reader has no reason to think the call was not in English. The claim survives in the prose — the
   `Stack` section still says the transcription runs in Spanish, in both registers — but not beside the
   transcript. Put a locale back in the header if that ever has to be legible at a glance.
6. **Three toggles the design does not have, and a light theme the system does not ship.** Both are extensions of Nocturne — derived from its ramps, built from its `.seg` — not departures from it.
7. **Ramp steps and text opacities become semantic aliases.** A step that reads on one ground does not read on the other, so the indirection is what makes two themes possible at all.
8. **The six looping animations respect `prefers-reduced-motion`.** The design loops them unconditionally.

## Verification

```bash
uv run ruff check . && uv run pytest -q     # 95 green, with no environment variable set
cd web && pnpm build                        # tsc is the copy check; two HTML outputs
grep -rn 'color-neutral-[0-9]\|color-accent-[0-9]' web/src \
  --include=*.tsx --include=*.ts --include=*.css | grep -v tokens.css
make web && make dev
curl -s -o /dev/null -w '%{http_code}\n' localhost:8001/ localhost:8001/panel
docker build -t constancia:landing .
```

That `grep` must return **nothing**. No ramp step may survive outside `tokens.css`, `.tsx` included — it is what catches the `DemoCard` data problem in step 7, which no amount of reading the stylesheets would find.

By eye in a browser, both pages, both themes, both languages, with no `.env` and no `DATABASE_URL`:

- Each toggle moves its own axis and nothing else. A reload keeps all three. A hard reload shows no flash of the wrong theme.
- On light, the muted captions, the accent-coloured lines **and the four numbers in the metrics band** are all readable — the band being the one that inherits its colour onto a fixed indigo ground.
- Spanish has no key falling back to English and no text overflowing its box. Spanish runs longer than English and the hero headline is where that shows first.
- Walking from `/` to `/panel` carries theme and language across, and the panel's native `<select>` and `<input>` follow the theme rather than staying white.
- In the panel, **Call now** in scripted mode behaves exactly as before: the 7/10 struck through by the 4/10, a two-bar chart.
- With *Reduce motion* on, the loops stop and nothing else breaks.
- The Docker image carries `web/dist/index.html` and `web/dist/panel/index.html`.

## Documentation to update

- `README.md` — `panel/` → `web/`, `make web`, the two routes, the three preferences, and the layout rows.
- `docs/PLAN.md` — the landing joins stage 4 as a presentation deliverable; deviations 17 onward.
- `SUBMISSION.md` — the landing is the evidence for *Business Value*, and the plain register is what makes that case legible to a judge who is not an engineer.
- `CLAUDE.md` — the amended language rule (step 12).
- `docs/INTENT.md` — none; deviations are annotated there together in stage 4, as already planned.

## Out of scope

- Wiring the landing card to the real SSE replay. The design's script stands.
- A third language, and any i18n library: two languages and one merge function do not earn a dependency.
- Translating `app/packs.py`. The agent speaks Rioplatense Spanish on the phone whatever the visitor picked on the website — the patient is not the visitor.
- `@media print`. Browsers drop backgrounds by default, so light text lands on white paper; nobody prints a landing page.
- Authentication. There still is none, and the landing's footer says so.
- Render deploy, video and deck (the rest of stage 4).
- Checkpoints C1 and C2.
- Pushing anything back to the Claude Design project: this is a one-way import.
- Commits and pushes.
