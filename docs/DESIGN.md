# Cadence — the constancia design system

> **This is the target, not a description of what is built.** The colour tokens in *Tokens* below are
> live — `web/src/tokens.css` matches them line for line — but a good part of the typography, the
> component states, the layout numbers and both effects are specified here and not implemented yet.
> When this file and the code disagree, **the code is what ships and this file is what it should
> become**; the gap is tracked item by item in [`PENDINGS.md`](PENDINGS.md) § *The Cadence build
> programme*, and four open questions it does not answer are in § *Decisions the programme needs*.
> For the tokens as they resolve today, `web/src/tokens.css` is the source, and
> [`FRONTEND.md`](FRONTEND.md) describes the front end as it stands.

## Context

**Project.** constancia: a voice agent that phones rehabilitation patients once a week, asks a fixed
set of clinical questions, and opens the next call with what the patient said in the last one. The
demo shows three calls on one patient — week 1, week 2 with memory off, week 2 with memory on — and
the moment a fact is retired rather than overwritten.

**Audience.** The judging panel of the lablab.ai × AssemblyAI Voice Agent Hackathon, reading in
English, opening dozens of these in a row. They have four criteria: use of technology (AssemblyAI in
particular), presentation, business value, originality.

**Base system — Linear.** Layout and structure come from it: the 4px spacing base and its token
ladder, the ~1280px container, the surface-ladder-plus-hairline approach to depth instead of drop
shadows, the radius scale, the 2px focus ring, the aggressive negative tracking on display type, and
the eyebrow's positive tracking as the counterweight.

**Secondary system — ElevenLabs.** Exactly two traits, no more:

1. **The editorial light canvas** — an off-white page floor holding warm near-black ink, with pure
   white cards lifted off it. This is what makes light the canonical mode.
2. **The atmospheric gradient orbs** — soft radial blooms that carry the only ambient colour on the
   page and never contain content, never fill a button, never colour text.

Where the two disagree, the base wins. ElevenLabs keeps display type at weight 300; Cadence does
not — display runs at 600 with Linear's tracking, because the brief is impactful, not editorial.

**Originality.** Three deliberate departures, so this is a system of its own and not a recombination
that reads as either source:

1. **The accent is a deep teal, `#046a63`.** Linear's signature is lavender-blue and the previous
   constancia palette was blurple; ElevenLabs has no accent at all. Teal reads as signal and as
   clinical without being either parent, and it clears 5.87:1 on the light canvas.
2. **Display is Bricolage Grotesque, not Inter.** Body stays Inter. Two families, and the change of
   voice between them is audible rather than silent.
3. **The audio waveform is a live readout, not decoration.** It is driven by the call the page is
   actually showing, and it is the protagonist effect.

No logo, name, or proprietary typeface from either source appears here. Neither `DESIGN.md` is
official or affiliated with the brand it describes.

## Stack

The repository already has a front end and it wins:

- **React 19 + TypeScript + Vite**, multi-page build (`web/index.html` for the landing,
  `web/panel/index.html` for the panel), served from `web/dist` by FastAPI.
- **Plain CSS with custom properties.** No Tailwind, no shadcn/ui, no CSS-in-JS. Tokens live in
  `web/src/tokens.css`; page-specific rules live in `web/src/landing/landing.css` and
  `web/src/panel/panel.css`.
- **No new dependencies.** The repo pins exact versions and does not add any.
- Components keep the inline styles they already carry where those encode a `clamp()` or a
  `color-mix()`; every colour and every opacity goes through a token.

## Tokens

All tokens are CSS custom properties on `:root`, in `web/src/tokens.css`. **The token names are the
repository's**, not this document's: the front end already consumed `--color-bg`, `--text-muted`,
`--fill-subtle` and the rest through a gate, so renaming them would have been a diff with no reader.

**Light is the canonical theme.** It is the `:root` block, it is what the demo video records, and it
is what a judge opens first. `:root[data-theme="dark"]` redeclares only what changes.

There is **no `prefers-color-scheme` query**. An inline pre-paint script in both HTML entries reads
`localStorage` and writes `data-theme` before the CSS arrives, so the attribute is always present and
nothing flashes. The default is light, and three lines have to agree on that: `web/src/prefs.ts` and
the script in each of the two `index.html` files.

Every name is semantic. No component references a ramp step directly — that rule is enforced by a
test, not by discipline (see **Rules**).

```css
:root {
  color-scheme: light;

  --color-bg: #f4f4f2;
  --color-surface: #ffffff;
  --color-text: #0c0a09;
  --color-accent: #046a63;
  --color-accent-2: #035c56;
  --color-accent-hover: #03544f;
  --color-accent-active: #10302e;
  --color-divider: #e4e2df;
  --color-divider-strong: #d3d0cc;

  --color-neutral-100: #fafaf9;
  --color-neutral-200: #f0efed;
  --color-neutral-300: #e4e2df;
  --color-neutral-400: #d3d0cc;
  --color-neutral-500: #a8a29e;
  --color-neutral-600: #847d76;
  --color-neutral-700: #78716c;
  --color-neutral-800: #44403c;
  --color-neutral-900: #0c0a09;

  --color-accent-100: #e4f0ef;
  --color-accent-200: #c3e0dd;
  --color-accent-300: #92cbc4;
  --color-accent-400: #5ad3c4;
  --color-accent-500: #3fbfae;
  --color-accent-600: #0f8a80;
  --color-accent-700: #046a63;
  --color-accent-800: #03544f;
  --color-accent-900: #10302e;

  --color-section: #053f3a;
  --color-section-glow: #0a5a54;

  --text-secondary: var(--color-neutral-800);
  --text-muted: var(--color-neutral-700);
  --text-accent: var(--color-accent-700);
  --section-ink: var(--color-neutral-100);
  --tone-dim: var(--color-neutral-600);
  --fill-subtle: var(--color-neutral-200);
  --color-danger: #b3261e;
  --danger-fill: #fbeae9;

  --orb-mint: #a9e0d2;
  --orb-sky: #a6c6e4;
  --orb-amber: #f0cfa4;

  --font-heading: "Bricolage Grotesque", "Inter", system-ui, sans-serif;
  --font-heading-weight: 600;
  --font-body: "Inter", system-ui, sans-serif;
  --font-mono: ui-monospace, SFMono-Regular, "SF Mono", Menlo, monospace;

  --space-1: 4px;
  --space-2: 8px;
  --space-3: 12px;
  --space-4: 16px;
  --space-6: 24px;
  --space-8: 32px;

  --radius-sm: 6px;
  --radius-md: 8px;
  --radius-lg: 12px;
  --radius-xl: 16px;

  --shadow-sm: 0 0 0 1px var(--color-divider);
  --shadow-md: 0 0 0 1px var(--color-divider-strong), 0 4px 16px rgba(12, 10, 9, 0.04);
  --shadow-lg: 0 0 0 1px var(--color-divider-strong), 0 8px 28px rgba(12, 10, 9, 0.07);
}

:root[data-theme="dark"] {
  color-scheme: dark;

  --color-bg: #0b0d0f;
  --color-surface: #14171a;
  --color-text: #f2f4f5;
  --color-accent: #3fbfae;
  --color-accent-2: #6fdccd;
  --color-accent-hover: #5ad3c4;
  --color-accent-active: #92cbc4;
  --color-divider: #23282d;
  --color-divider-strong: #333a41;

  --color-neutral-100: #f2f4f5;
  --color-neutral-200: #d8dde2;
  --color-neutral-300: #c3c9cf;
  --color-neutral-400: #949ba3;
  --color-neutral-500: #6f767e;
  --color-neutral-600: #545b63;
  --color-neutral-700: #3d444b;
  --color-neutral-800: #23282d;
  --color-neutral-900: #14171a;

  --color-section: #04302d;
  --color-section-glow: #0a4a45;

  --text-secondary: var(--color-neutral-300);
  --text-muted: var(--color-neutral-400);
  --text-accent: var(--color-accent-400);
  --section-ink: var(--color-neutral-100);
  --tone-dim: var(--color-neutral-500);
  --fill-subtle: var(--color-neutral-800);
  --color-danger: #ff8a80;
  --danger-fill: #331b19;

  --orb-mint: #1e4a44;
  --orb-sky: #1c3549;
  --orb-amber: #3d3220;

  --shadow-sm: 0 0 0 1px var(--color-divider);
  --shadow-md: 0 0 0 1px var(--color-divider-strong);
  --shadow-lg: 0 0 0 1px var(--color-neutral-700);
}
```

**Measured contrast.** Every pair a judge reads, in both themes:

| Pair | Light | Dark |
|---|---|---|
| `--color-text` on `--color-bg` | 17.9:1 | 17.7:1 |
| `--text-secondary` on `--color-bg` | 9.3:1 | 11.7:1 |
| `--text-muted` on `--color-bg` | 4.4:1 | 6.9:1 |
| `--tone-dim` on `--color-bg` | 3.7:1 — **large text and non-text only** | 4.2:1 |
| `--color-accent` on `--color-bg` | 5.9:1 | 8.6:1 |
| `--color-accent` on `--color-surface` | 6.5:1 | 8.0:1 |
| `--color-danger` on `--color-bg` | 5.9:1 | 8.5:1 |
| `--section-ink` on `--color-section` | 11.3:1 | 13.9:1 |
| `--color-bg` on `--color-accent` (primary button) | 5.9:1 | 8.6:1 |
| `--color-bg` on `--color-accent-hover` | 8.0:1 | 10.7:1 |
| `--color-bg` on `--color-accent-active` | 12.9:1 | 10.7:1 |

`--color-accent-hover` and `--color-accent-active` exist because the states run in opposite
directions per theme: on light the button **darkens** as it is pressed, on dark it **lightens**.
Reusing one ramp step for both put the light hover at 3.8:1 and the dark active at 2.2:1 — a hover
that fails is a failure nobody screenshots, because it only exists under the cursor.

Dark is not a filter over light. The shadow tokens there carry only their 1px ring and drop the blur,
because a drop shadow on near-black is invisible work; and the two canvases are measured separately
rather than mirrored, because a warm off-white and a cool near-black are not each other's inverse.

## Typography

Two families, both from Google Fonts, plus the system mono — which is not loaded, so it costs
nothing.

> Not built yet: the scale below exists as a table here and as literal pixel sizes in the code —
> there is no token or class for any of its thirteen steps. The fonts load through an `@import` at
> the top of `tokens.css` rather than the links below, so there is no preconnect, and Inter's 700 is
> downloaded without being declared here. [`PENDINGS.md`](PENDINGS.md) § C.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,500;12..96,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
```

- **Bricolage Grotesque** — `--font-heading`. Headlines only, weight 500–600.
- **Inter** — `--font-body`. Body, labels, navigation, captions, buttons.
- **`ui-monospace`** — `--font-mono`. Verbatim quotes, phase names, IDs, key terms. Anything the
  machine said or the patient said word for word.

| Token | Size | Weight | Line height | Tracking | Family | Use |
|---|---|---|---|---|---|---|
| `display-xl` | 5rem | 600 | 1.05 | −0.04em | display | Hero headline |
| `display-lg` | 3.5rem | 600 | 1.10 | −0.032em | display | Section openers |
| `display-md` | 2.5rem | 600 | 1.15 | −0.025em | display | Sub-section headlines |
| `headline` | 1.75rem | 600 | 1.20 | −0.021em | display | Card group titles |
| `card-title` | 1.375rem | 500 | 1.25 | −0.018em | display | Feature and panel card titles |
| `subhead` | 1.25rem | 400 | 1.40 | −0.01em | text | Lead paragraphs |
| `body-lg` | 1.125rem | 400 | 1.50 | 0 | text | Hero subhead |
| `body` | 1rem | 400 | 1.50 | 0 | text | Default |
| `body-sm` | 0.875rem | 400 | 1.50 | 0 | text | Card bodies, footer |
| `caption` | 0.75rem | 400 | 1.40 | 0 | text | Meta, timestamps |
| `button` | 0.875rem | 500 | 1.20 | 0 | text | All button labels |
| `eyebrow` | 0.8125rem | 500 | 1.30 | **+0.03em** | text | Section eyebrows, uppercase |
| `mono` | 0.8125rem | 400 | 1.50 | 0 | mono | Quotes, phases, key terms |

**Principles.**

- **Display tracks negative, hard.** −0.04em at 5rem. This is where the impact lives; it is not
  decoration, it is what makes an 80px headline read as one object instead of a row of letters.
- **The eyebrow tracks positive.** The only positive tracking in the system. Against the negative
  display above it, that is what marks the eyebrow as taxonomy rather than content.
- **Display is never used below `card-title`.** Below that size Bricolage's personality becomes
  noise and Inter is simply more legible.
- **Mono is reserved for verbatim.** If the patient said it or the pipeline emitted it, it is mono.
  If we wrote it, it is not. That rule is what makes a quote look like evidence.

Responsive display: clamp the two largest steps rather than stepping them at breakpoints.

```css
.display-xl { font-size: clamp(2.5rem, 6vw, 5rem); }
.display-lg { font-size: clamp(1.875rem, 4vw, 3.5rem); }
```

## Spacing, grid, radii and shadows

> Not built yet: the container is 1180px and the panel's 980px, the minimum gutter is 20px, no rule
> caps prose at `68ch`, and elevation levels 2 and 3 have no implementation — the live call card
> carries a `.live` class that is defined nowhere. [`PENDINGS.md`](PENDINGS.md) § D.

**Spacing.** 4px base. `--space-1` 4 · `--space-2` 8 · `--space-3` 12 · `--space-4` 16 ·
`--space-6` 24 · `--space-8` 32 · `--space-12` 48 · `--space-16` 96.

The first six are declared in `tokens.css`; `--space-12` and `--space-16` are not yet, and the two
section rhythms below use literals until they are.

- Card interior padding: `--space-6` (24px); `--space-8` (32px) on the hero and the live call card.
- Button padding: 8px vertical, 14px horizontal.
- Input padding: 8px vertical, 12px horizontal.
- Between sections: `96px`. Between blocks inside a section: `--space-6`.

**Grid.** `1280px` 1280px, centred, with a 16px minimum side gutter that never collapses. Card
grids are 3-up at ≥1024px, 2-up at ≥640px, 1-up below. Prose caps at `68ch` (68ch) —
a measure, not a pixel width, because it has to hold in both languages and Spanish runs longer.

Section padding scales rather than stepping:
`padding: clamp(3rem, 6vw, 6rem) clamp(1rem, 5vw, 4rem);`

**Radii.** `--radius-sm` 6 (status chips, inline tags) · `--radius-md` 8 (buttons) · `--radius-lg` 12
(cards) · `--radius-xl` 16 (the live call card, the demo card) · `9999px` (toggles, state pills).

Four steps and one constant, no more. All four are declared; `--radius-xl` has no consumer yet.

**Elevation.** Five levels, and only two of them use a shadow — and only in light.

| Level | Treatment | Use |
|---|---|---|
| 0 | No border, no shadow | Body type, hero copy, footer |
| 1 | `--color-surface` on `--color-bg`, 1px `--color-divider` | Default cards |
| 2 | `--color-surface` on `--color-bg`, 1px `--color-divider-strong`, `--shadow-md` | Hovered cards, the featured card |
| 3 | `--fill-subtle`, 1px `--color-divider-strong`, `--shadow-lg` | Dropdowns, the live call card while a call runs |
| 4 | `2px solid var(--color-accent)` at 2px offset | Any focused interactive element |

Depth is the surface ladder plus hairlines. A card does not get both a heavier border and a heavier
shadow to say the same thing twice.

## Components

Every state is specified. A component without a `:focus-visible` is not finished.

> Not built yet: the `loading` state, the real `disabled` treatment, the card hover, the pill
> geometry, the rail timestamp, and `.input` — which has no consumer in the product at all. The
> `.btn-ghost` the panel uses three times is missing from this table. See
> [`PENDINGS.md`](PENDINGS.md) § B and § *Decisions*, items 3 and 4.

**Button — primary.**

```css
.btn-primary {
  font: 500 0.875rem/1.2 var(--font-body);
  padding: 8px 14px;
  border-radius: var(--radius-md);
  background: var(--color-accent);
  color: var(--color-bg);
  border: 1px solid transparent;
  transition: background 120ms ease;
}
.btn-primary:hover { background: var(--color-accent-hover); }
.btn-primary:active { background: var(--color-accent-active); }
.btn-primary:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 2px; }
.btn-primary:disabled { background: var(--fill-subtle); color: var(--tone-dim); cursor: not-allowed; }
.btn-primary[data-loading] { color: transparent; position: relative; }
```

Loading shows a 14px spinner in `--color-bg` centred on the button; the label is hidden but the
button keeps its width, so nothing reflows.

**Button — secondary.** `background: transparent`, `1px solid var(--color-divider-strong)`,
`color: var(--color-text)`. Hover raises the border to `--tone-dim` and the background to `--color-surface`. Same
focus ring. Disabled drops the text to `--tone-dim` and the border to `--color-divider`.

**Input.**

```css
.input {
  font: 400 1rem/1.5 var(--font-body);
  padding: 8px 12px;
  border-radius: var(--radius-md);
  background: var(--color-surface);
  color: var(--color-text);
  border: 1px solid var(--color-divider-strong);
}
.input::placeholder { color: var(--tone-dim); }
.input:focus-visible { outline: 2px solid var(--color-accent); outline-offset: 1px; border-color: var(--color-accent); }
.input:disabled { background: var(--fill-subtle); color: var(--tone-dim); }
.input[aria-invalid="true"] { border-color: var(--color-danger); }
```

The error message sits below the input in `caption`/`--color-danger`, and is referenced by
`aria-describedby`. Colour is never the only carrier of the error.

**Card.** `--color-surface` on `--color-bg`, 1px `--color-divider`, `--radius-lg`, `--space-6` padding. Hover moves it
to level 2. A card that is a link gets the focus ring on the card, not on the text inside it.

**Navigation.** Sticky header, 64px tall, `--color-bg` at 85% with `backdrop-filter: blur(12px)`, a 1px
`--color-divider` bottom edge that only appears once the page has scrolled. Links are `body-sm`/`--text-muted`,
`--color-text` on hover, and the current section is `--color-accent` with a 2px underline in the same colour.

**State pill.** `9999px`, `caption` uppercase with +0.03em, 2px/8px padding. Three variants:
neutral (`--fill-subtle` / `--text-muted`), accent (`--color-accent-100` / `--color-accent-800`), danger
(`--danger-fill` / `--color-danger`). `ESCALATED` and `RED FLAG` are the danger variant and they also carry
a flag glyph, because a colour-blind judge has to see it too.

**Transcript turn.** Speaker label in `eyebrow`/`--text-muted`, text in `body`. **The accent marks
the agent, not the patient** — `--turn-agent-bg` is the accent at 9% on light and 10% on dark, and
the patient sits on a neutral wash of `--color-text`. That is the opposite of the obvious choice and
it is deliberate: what the agent says is the thing the demo exists to show, and the money shot of the
whole video is one agent sentence quoting last week. A quote inside a fact is `mono`, wrapped in
`«»`, `--text-secondary`.

**Activity rail row.** Phase name in `eyebrow` uppercase `--color-accent-800`, detail in `caption`
`--text-muted`, timestamp right-aligned in `mono`/`--tone-dim`. A failed phase turns the phase name
`--color-danger` and keeps the layout identical, so the rail does not jump when something breaks.

## Screens

> The landing matches this today except for the metrics band's background and the two orbs. The
> panel does not: it has seven call buttons in three rows rather than six in two, its live call card
> has no elevation of its own, the chart tiles are bar columns rather than sparklines, and there is
> no waveform. See [`PENDINGS.md`](PENDINGS.md) § A, § D and § E.

**Landing (`/`)** — eight blocks, in order:

1. **Header** — sticky nav, theme / language / register toggles, a link into the panel.
2. **Hero** — `display-xl` headline left, body and two buttons under it; the **demo card** right,
   playing a scripted call. One orb (`--orb-mint`) blooms behind the headline.
3. **Metrics band** — four figures on `--fill-subtle`: 70% non-adherence, 3 verticals, 333 free
   streaming hours, 311 tests. **Animated counters.**
4. **How it works** — four steps, 4-up at desktop, each an eyebrow index plus a card title and body.
5. **Memory** — four pillars, 2×2.
6. **Stack** — five service cards, the AssemblyAI one at level 2 to mark it as the protagonist, with
   the honest-limits paragraph in `body-sm`/`--text-muted` under a hairline.
7. **The model** — three columns: who pays, what it costs, what it costs to run.
8. **Closing** — `display-lg`, two CTAs, one orb (`--orb-sky`) bottom right; then the footer.

**Panel (`/panel`)** — a patient list rail and a detail column:

1. **Patient rail** — one row per patient; the selected row is `--color-surface` with a 2px `--color-accent`
   left rule.
2. **Call controls** — six buttons in two rows: the four keyless ones, then the two live ones. The
   live pair is `btn-primary`; the rest are secondary.
3. **Live call card** — level 3 while a call runs. Transcript left, activity rail right, the
   **waveform** across the bottom, a state dot top right: live / ended / lost.
4. **How she is doing** — two sparkline tiles, pain and sessions, with verdict arrows.
5. **What the agent remembers** — the fact chain; a retired fact keeps its quote and gets a
   strike-through plus a `RETIRED` pill.
6. **Words the agent listened for** — a three-step diagram and the key-term chips in `mono`.
7. **Calls so far** — one row per call, with its summary, its state pills, and the
   **What AssemblyAI heard** block: entity chips and sentiment counts.

**Design preview (`docs/design-preview.html`)** — not part of the product. Tokens, type scale,
components and the protagonist effect on one page.

## Effects

Two, and no more. Everything else in the system holds still.

> **Neither is built.** Today the only wave is eight decorative bars in the landing's demo card, the
> metrics figures are static strings, the orb tokens have no consumer, and seven keyframes run where
> this section allows two. Where the waveform's level comes from is an open question — the browser
> never has the call audio. [`PENDINGS.md`](PENDINGS.md) § A and § *Decisions*, item 1.

**1. The live waveform — the protagonist.** It sits along the bottom of the live call card and it is
a readout, not an ornament: 96 bars, each scaled by the audio level of the turn being spoken, in
`--color-accent` at 70% opacity, with the bar under the playhead at full opacity. Bars are
`9999px`, 4px wide, 3px apart, with a 32px maximum height, centred in their container. Fewer
or thinner than that and it reads as a detail in a corner instead of the protagonist.

When the call is idle the bars rest at 15% height. When the patient is speaking the wave is
`--color-accent`; when the agent is speaking it is `--tone-dim` — so a muted viewer can see who has the
floor.

```css
.wave-bar {
  width: 4px;
  border-radius: 9999px;
  background: var(--color-accent);
  transform-origin: bottom;
  transition: transform 90ms linear;
}
@media (prefers-reduced-motion: reduce) {
  .wave-bar { transition: none; }
}
```

With reduced motion the bars still render their current level — the wave is data, so it is never
hidden — but they jump to it instead of easing, and the idle shimmer does not run at all.

**2. Animated counters — the metrics band.** Each figure counts up from zero to its value over
900ms with an ease-out curve, triggered once by an `IntersectionObserver` at 50% visibility. Numbers
are tabular (`font-variant-numeric: tabular-nums`) so nothing shifts while counting.

```js
if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) {
  el.textContent = final
} else {
  // ease-out over 900ms, then set the final value exactly
}
```

With reduced motion the final value is written directly, on first paint. It is never animated and
never absent.

**Orbs are not an effect.** They are static radial gradients at 40% opacity with a 120px blur,
behind content, `pointer-events: none`. They do not drift, pulse, or follow the cursor. Three per
page at most, and never behind a paragraph a judge has to read.

## Rules

**Do.**

- Take every colour, size, radius and shadow from a token. If the value you need is not a token, add
  the token.
- Use the semantic alias, never the value: `--text-muted`, not `#78716c`.
- Give every interactive element a visible `:focus-visible` ring — 2px `--color-accent` at 2px offset.
- Put verbatim machine or patient text in `--font-mono`, and nothing else.
- Specify hover, focus, disabled, loading and error for anything a user can touch.
- Keep both themes correct in the same change. A token added to light is added to dark in the same
  commit.
- Test at 390px width. 16px side gutter, no horizontal scroll.

**Do not.**

- Do not introduce a component the system does not name. Compose the ones above.
- Do not use an orb colour as a fill, a border, or a text colour. They are atmosphere.
- Do not put display type below `card-title`.
- Do not add a second accent. One accent; the semantics are `--color-danger` and `--color-accent-700` and they mean
  what they say.
- Do not reach for a drop shadow on dark. It resolves to `none` on purpose.
- Do not animate anything except the two effects above.
- Do not write a raw hex, `rgba()`, or an opacity on text anywhere outside `tokens.css`.

That last rule is enforced, not trusted. `tests/test_docs.py` walks `web/src` in Python and fails the
build on any ramp step outside `tokens.css`; it is walked in Python rather than run as a shell
command because an unquoted `--include` glob is expanded by zsh before grep sees it, which prints
nothing and reads exactly like a pass.

## Verification checklist

Run before calling a design change done.

```bash
make web        # tsc -b && vite build — the only front-end gate; there is no test runner here
make test       # includes the token gate and the bilingual parity gate
```

- [ ] **Dark mode** — every screen under `data-theme="dark"`, and every screen under
      `data-theme="light"` with the system preference set to dark. There is no
      `prefers-color-scheme` query to test: the pre-paint script always writes the attribute, which
      is why the system preference only ever decides the **default**.
- [ ] **Responsive** — 390px, 768px, 1280px, 1920px. 16px side gutter at 390px, no horizontal
      scroll, no text under 12px.
- [ ] **Keyboard** — tab through every screen. Focus is visible on every stop, the order follows the
      page, and no element traps it.
- [ ] **Contrast, measured per theme** — 4.5:1 for body text, 3:1 for large text and for component
      boundaries. Measure by compositing on a canvas, not by parsing the computed style:
      `getComputedStyle` returns `color(srgb r g b / a)` for `color-mix()` values, and a token with
      one value cannot clear 4.5:1 against both a light and a dark background.
- [ ] **`--tone-dim` is never body text.** It measures 3.7:1 in light. It is for large text,
      disabled states and non-text boundaries.
- [ ] **Reduced motion** — with `prefers-reduced-motion: reduce`, the counters show their final
      value on first paint and the waveform still renders its levels without transitions.
- [ ] **Both languages** — English and Spanish, on every screen. Spanish runs longer; nothing
      clips, wraps badly, or pushes a button off its row.
- [ ] **Colour is never the only signal** — `ESCALATED`, `RED FLAG` and the error state each carry a
      glyph or a word as well as a colour.
