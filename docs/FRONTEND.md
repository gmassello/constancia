# Frontend reference

React 19 + Vite + TypeScript in [`../web/`](../web). Twenty-two files, about 4,800 lines, and **no UI
library, no router, no state library, no date library and no charting library**. The chart is one inline
`<svg>` polyline in a stretched `viewBox` with the dots placed in percentages beside it; the dates are
`Intl.DateTimeFormat`; the segmented control is native radios styled with `:has()`.

Two pages, built as two HTML entries: the public landing at `/` and the professional's panel at
`/panel`.

This file describes the front end **as it is**. [`DESIGN.md`](DESIGN.md) describes the design system
as it is **meant to become**, and the gap between the two is tracked in
[`PENDINGS.md`](PENDINGS.md).

## Build and serving

| | |
|---|---|
| Build | `pnpm build` = `tsc -b && vite build`. `make web` wraps it with `pnpm install --frozen-lockfile` first |
| Entries | `landing: index.html` and `panel: panel/index.html` (`web/vite.config.ts:10-13`) |
| Output | `web/dist/` — `index.html`, `panel/index.html`, hashed assets in `assets/` |
| Dev | `make web-dev` on port 5173, proxying the API routes to `localhost:8001` |

There is no router and no SPA fallback. The multi-page split happens at build time, so the landing
never loads the panel's bundle.

FastAPI serves the result (`app/main.py`) and the ordering is deliberate: `/` and `/panel`
are **explicit routes** so they can carry `Cache-Control: no-store`, and the `StaticFiles` mount goes
last, after every API route. Vite hashes the assets but not `index.html`; a cached `index.html` keeps
naming the previous build's bundles, which is a confusing way to lose an afternoon. `/assets/*` stays
cacheable through the mount.

The whole block is inside `if WEB_DIST.is_dir()`, so the API boots fine with no front-end build.

## Files

### Shared

| File | Lines | What it is |
|---|---:|---|
| [`web/src/tokens.css`](../web/src/tokens.css) | 308 | The design system: the tokens with light canonical and dark as the override, the semantic aliases, the reset, the `h1`–`h6` sizes, three steps of the type scale (`.eyebrow`, `.caption`, `.mono`) and the six shared classes — `.text-muted`, `.hr`, `.btn`, `.tag`, `.pill` and `.seg`. |
| [`web/src/prefs.ts`](../web/src/prefs.ts) | 75 | `usePrefs()`, the three initial readers, `localStorage` persistence and `prefersReducedMotion()`. |

### Landing

| File | Lines | What it is |
|---|---:|---|
| `web/src/landing/Landing.tsx` | 601 | A header whose nav marks the current section, seven sections and a footer, with the design's inline styles kept. |
| `web/src/landing/DemoCard.tsx` | 744 | The scripted demo card: two scripts, the fact chain, the player and its controls. |
| `web/src/landing/copy.ts` | 553 | Two full sets, one per language, plus two partial plain-register overrides merged over them. |
| `web/src/landing/landing.css` | 126 | Five keyframes, the pause rule, the reduced-motion block and the sticky header. |
| `web/src/landing/main.tsx` | 12 | Mount. |

### Panel

| File | Lines | What it is |
|---|---:|---|
| `web/src/panel/panel.css` | 425 | Layout and styles, on the aliases. |
| `web/src/panel/copy.ts` | 554 | Two languages, one register, plus the maps for raw backend values. |
| `web/src/panel/ActivityRail.tsx` | 175 | Turns each trace event into a labelled line. An event with no `case` still renders, through the `default` — a new one costs a row here only when it deserves wording of its own. |
| `web/src/panel/PatientView.tsx` | 168 | Loads the patient's data and composes five cards, plus the live one while a call runs. |
| `web/src/panel/content.ts` | 160 | The EN→ES table for canned patient data, keyed by the English string the call produces. |
| `web/src/panel/App.tsx` | 96 | Shell: sidebar, backend status, the two toggles, patient list. |
| `web/src/panel/api.ts` | 155 | Backend types, `get`/`post`, `ApiError` carrying the status and the backend's `detail`, and `subscribe()` over `EventSource`. |
| `web/src/panel/FactChain.tsx` | 97 | The patient file: current facts and what they retired, each with a native `<audio>` for its quote when the recording placed it. |
| `web/src/panel/Questions.tsx` | 109 | What the patient asked and the agent would not answer. An open one carries the only text field in the product; the rest show their status. |
| `web/src/panel/Calls.tsx` | 102 | One row per past call: tags, the summary, and the transcript behind a `<details>`. |
| `web/src/panel/WeeklyChart.tsx` | 93 | One sparkline tile per measure, with scale, delta and a verdict arrow that carries the direction. |
| `web/src/panel/Keyterms.tsx` | 64 | The words handed to the recogniser: the three-step drawing and the chips. |
| `web/src/panel/LiveCall.tsx` | 79 | The SSE subscription, the live transcript and the wave at the foot of the card. |
| `web/src/panel/Wave.tsx` | 60 | The activity wave: 96 bars, who holds the floor derived from the last turn event. |
| `web/src/panel/main.tsx` | 12 | Mount. |

## Theming

There is no `prefers-color-scheme` query anywhere. **The theme is an attribute.**

1. An inline pre-paint script in both HTML entries (`web/index.html:8-18`) reads `localStorage` and
   writes `documentElement.dataset.theme` and `documentElement.lang` before the CSS arrives, so
   nothing flashes.
2. The `:root` in `tokens.css` is the **light** theme — the canonical one, the one the demo video
   records — and `:root[data-theme="dark"]` redeclares **only what changes**. Each block sets its own
   `color-scheme`, which is what makes the panel's native `<select>` and `<input>` follow the theme.
3. `usePrefs()` rewrites the attribute on change, and its initial state is lazy and reads the same
   source as the pre-paint script, so the first effect does not stomp on what the script already
   applied.

The default is **light**, and that is three lines that have to agree: `web/src/prefs.ts:31` and
`:12` in each of the two `index.html` files.

The two themes are measured separately rather than mirrored: a warm off-white canvas and a cool
near-black one are not each other's inverse, and a token with one value cannot clear 4.5:1 against
both. Every pair, with its ratio in each theme, is in [`DESIGN.md`](DESIGN.md).

## The ramp rule

**Nothing outside `tokens.css` may name a ramp step or a text opacity.** The ten entries below are
what exists so that it does not have to. Six of them are aliases in the strict sense — they resolve
to a ramp step, which is the indirection the rule is about. The rest are per-theme values with no
ramp equivalent, listed here because the rule covers them too: use the name, never the hex.

| Alias | For |
|---|---|
| `--text-secondary` | body text that is not primary |
| `--text-muted` | labels, metadata, footers |
| `--text-accent` | accented text that has to clear the accent base |
| `--section-ink` | the same declaration in both themes — the metrics band is dark in both, so the ink stays light |
| `--tone-dim` | the "retired" border and label |
| `--fill-subtle` | tinted fills |
| `--color-divider-strong` | the outline of an input or a secondary button, where the hairline is not enough |
| `--color-accent-hover` + `--color-accent-active` | a pair per theme, because the states run **opposite ways**: light darkens on press, dark lightens |
| `--orb-mint` / `--orb-sky` / `--orb-amber` | atmosphere only, never a fill, a border or a text colour. `--orb-mint` is the bloom behind the hero headline and `--orb-sky` the one bottom right of the closing; `--orb-amber` is declared and unconsumed, because [`DESIGN.md`](DESIGN.md) § *Screens* places two orbs and no third. |
| `--color-danger` + `--danger-fill` | a pair, because no single hex clears both grounds |

A step that reads on one ground does not read on the other; the indirection is what makes two themes
possible at all. The gate is a `grep`:

```bash
grep -rn 'color-neutral-[0-9]\|color-accent-[0-9]' web/src \
  --include='*.tsx' --include='*.ts' --include='*.css' | grep -v tokens.css
```

It must return nothing. It includes `.tsx` on purpose: in `DemoCard.tsx:31-36` the rail colours live
as **data** (`TONE`), not as styles, and reading stylesheets alone would miss them.

`tests/test_docs.py` asserts the same thing by walking `web/src` in Python, so `make test` is what
actually enforces it. The shell line stays because it prints the file and the line, and because the
unquoted version of it is how the gate spent a long time passing without running.

## Two languages

Every visible string comes from a `copy.ts`. English is the annotated, authoritative set and Spanish
the translation. The two pages share **no string**: one shared type across both surfaces would only
guarantee that every error lands in the same enormous file.

### The landing: two languages × two registers

Technical or plain — the same page written for a judge and for the physiotherapist who would pay for
it. Only the prose changes register; nav labels, button text and service names read the same either
way.

Two full sets and two partial override maps, and the typing is what keeps them in sync — `tsc` is
the only check. `copy()` merges the register over the language, `{ ...base[lang], ...plain[lang] }`,
so a key with no plain variant falls through to the prose of that same language:

- `const en = {...} satisfies Copy` and `const es = {...} satisfies Copy` — `satisfies` still
  requires every key of `Copy`, so a missing Spanish one fails the build, and unlike an annotation it
  keeps the literal key types the two lines below depend on.
- `const enPlain = {...} satisfies Partial<Copy>` keeps both the check against `Copy` **and** the
  literal key type.
- `type PlainKey = keyof typeof enPlain` then `const esPlain: Record<PlainKey, string>` closes the
  last hole: nothing otherwise tied the Spanish overrides to the English ones.

### The panel: two languages, one register

The panel is a tool, not a pitch. Duplicating its strings across two registers is work spent on a
surface nobody judges.

### Chrome, data, and raw values

| | What it is | Where it lives | If a translation is missing |
|---|---|---|---|
| **Chrome** | What the interface says: nav, headings, buttons, labels, verdicts, units | `copy.ts`, keyed, typed | Build error |
| **Data** | What the patient said or the agent wrote: transcript turns, facts, quotes, key terms, summaries | Landing: `{es, en}` pairs beside their source in `DemoCard`. Panel: `content.ts`, keyed **by the English string** | Landing: impossible, the type requires both. Panel: falls through to English |
| **Raw backend values** | `symptom`, `red_flag`, `sudden_sharp_pain`, `rehab`, `recall` — taxonomy, not the patient's words | The maps at the end of `panel/copy.ts`, resolved with `label()` | Build error: the `parity` gate |

The maps are typed `Record<string, string>`, which on its own would let a missing Spanish key
compile and let `label()` fall through to `raw.replace(/_/g, " ")` — the Spanish reader would see
`sudden sharp pain`. `en` and `es` are therefore declared with `satisfies Strings` rather than an
annotation, which keeps their literal keys, and the `parity` block at the end of the file asserts
that each of the nine maps carries the same keys in both languages — the ninth is
`questionStatus`, and adding it meant a row in `parity` and its own `Aligned<>` line, not just the
two tables.

The landing has the same gate on a smaller surface: one map, `demoCategory`, and its own `parity`
block at the end of `landing/copy.ts`. Both are type-level assertions — they cost nothing at runtime
and fail the build, which is the only check this side of the repo has.

`speech()` ([`web/src/panel/content.ts`](../web/src/panel/content.ts)) is keyed by the English
string — the one the call actually produces — and carries a `ponytail:` marker saying so: a fact a
real call extracts is not in the table and shows in English rather than in an invented Spanish
translation. Making up the translation of a verbatim quote is worse than showing the quote.

Every interpolated string is typed as a **function**, not a `string` — `saidOn: (day, turn) => string`
— because concatenation works in English and breaks in Spanish, where the word order moves.

The resolver hangs off the copy object (`c.data(text)`, `c.day(iso)`), so no component needs a `lang`
prop.

## Visitor preferences

Three, in `localStorage` under `constancia.*`: theme (`light` by default), language (`en`) and
register (`technical`, landing only). Both reads and writes are wrapped in `try/catch` — under
partitioned storage `localStorage` can throw on the read too — and the pages render on the defaults
if it fails.

`?lang=` takes priority over the stored value and is **not** persisted, which is what gives the
Spanish landing a shareable link.

Landing and panel share no memory: they are two documents, not an SPA. The bridge is `localStorage`,
which belongs to the origin. Walking from `/` to `/panel` is a full navigation; the new page runs its
own pre-paint script and reads the same three keys.

## The panel's components

| Component | Shows | Fed by |
|---|---|---|
| `App` | Sidebar, backend status line, patient list | `GET /patients`, `GET /health` |
| `PatientView` | Header, the call controls, five cards, and the live one while a call runs | `GET /patients/{id}/chain`, `/weekly`, `/calls`, `/questions`, then `/calls/{id}/keyterms` |
| `LiveCall` | The call in progress and its transcript | SSE `GET /calls/{id}/events` |
| `ActivityRail` | One line per trace event | props, from `LiveCall` |
| `WeeklyChart` | One series per measure: previous → current, verdict, sparkline, real dates | props |
| `FactChain` | The patient file, current facts with what they retired hanging below | props |
| `Keyterms` | Where the key terms came from and what they are for, then the terms themselves | props |
| `Calls` | One row per past call: date, memory and escalation tags, the summary, and the transcript folded away | props |

### The call controls

Seven buttons in `PatientView`, in two rows. The first row is the five that cost nothing: *Call
without memory* and *Call with memory* as `btn-secondary`, because the comparison between them is the
demo, then three ghost links — *the same call without memory* (the `week2-off` script), a replay of a
recorded call, and a call with a red flag. Five buttons need 843px in English and 992px in
Spanish, against a 940px card, so they never fit beside the patient's name: `.chart-head` wraps and the
controls take their own line under it, right-aligned. At 1280px the English row is one line and the
Spanish one is two — the Spanish labels are the longer half and this is the one place the difference
shows in the layout. At 390px the row stacks and nothing is clipped.

The second row only renders when `GET /health` reports `live: true`, and mirrors the scripted pair:
*Real phone, no memory* and *Real phone, with memory*, both `mode: "live"` and both `btn-primary`,
separated from the first row by a hairline. They dial `DEMO_PHONE`, since the seeded patient carries no
number of her own.

### Consuming the SSE

`subscribe()` (`web/src/panel/api.ts`) is native `EventSource`, no library, and returns its own close
function — which is exactly what the effect returns as cleanup.

`LiveCall` keeps a `Set` of seen `seq` values and drops repeats. That is what makes `EventSource`'s
automatic reconnect harmless: a reconnect replays, and the client does not care. On `call_ended` it
flips the indicator and calls back into `PatientView.reload()`, so the chain, the series and the call
list refresh from the API the moment the call finishes.

`ActivityRail.describe()` is a closed `switch` over every type the backend emits. Six return `null`
explicitly: five are already visible in the transcript, and `twilio_frame` is stream plumbing that
belongs in `/trace`, not on screen. The four failure types — `phase_failed`, `warning`,
`extract_failed`, `analysis_failed` — share one branch that names the phase through `c.phase` and
uses the translated technical-detail label. Call-ending reasons use the bilingual `reason` map too.
The `default` branch prints the raw event type — reachable only if the backend starts emitting
something new.

The `flash` highlight is not a timer. A line gets `.fresh` when its frame did **not** carry
`replayed` — the flag the SSE generator puts on everything it sends from the buffer — and the
animation fires because the line mounts, once, keyed by `seq` on a list that only grows. Two things
break it and neither is loud: dropping the flag makes the whole backlog flash on every reconnect,
and a key that is not `seq` remounts the lines and flashes them all again.

## Motion and accessibility

`prefers-reduced-motion` is honoured in CSS **and** in JS (`prefersReducedMotion()`), because the demo
card has two clocks:

- The CSS keyframes are switched off in `landing.css` and `panel.css`.
- The card's `setTimeout` chain never schedules: the initial step is the end of the script, so the
  card opens on the fact chain — the payoff — and stays there.
- The pause button is not rendered at all in that path; there is nothing to pause. Step back and step
  forward **are** rendered, because with no timer they are the only way that visitor sees the call.

Pausing normally has to stop both clocks too: the effect stops scheduling, and `animation-play-state`
stops the looping CSS — scoped to the two the card owns, `noc-pulse` and `noc-wave`, because pausing
an entrance animation inside its 0.34 s window would leave that row invisible. Those two are now the
only loops on the page: `noc-breathe` used to pulse the two background blooms and `.is-paused` never
covered it, which is why the orbs are static gradients instead.

The panel's wave keeps a clock of its own, a 90 ms interval in `Wave.tsx`. Under reduced motion the
interval keeps running but the tick returns early while nobody holds the floor, so the bars sit flat
at 15% instead of shimmering; when a speaker does hold it the bars still move, because the wave is a
readout and `DESIGN.md` § *Effects* does not allow hiding it. The easing is CSS, so
`prefers-reduced-motion` drops `transition` and the bars jump to each level.

Contrast is measured, not assumed, and the method matters: colours are composited on a canvas and the
pixel is read, because `getComputedStyle().color` returns `color(srgb r g b / a)` with 0–1 components
for anything from `color-mix()`, and a regex parser reads that as nearly black. Every pair and its
ratio per theme are in [`DESIGN.md`](DESIGN.md); [`LANDING.md`](LANDING.md) keeps only the method,
and its hex values are the old palette.

Also present: `:focus-visible` rings, action `aria-label` values on the theme toggles, `role="img"`
plus a translated `aria-label` on the one SVG that carries meaning — the category glyph in
`FactChain`, while `Keyterms`' drawing is `aria-hidden` — a labelled `← Home` link rather than relying on
the wordmark, and `documentElement.lang` kept in sync with the chosen language.

---

See [`API.md`](API.md) for the endpoints these components read, and [`LANDING.md`](LANDING.md) for why
the landing looks the way it does.
