# Cadence — the constancia design system

> **This was written as the target, and the code has caught up with it.** Every section below is
> built: the tokens, the thirteen type steps, the component states, the layout numbers and both
> effects. Where the two still differ it is named on the spot, with the measurement that decided it —
> the panel's half of the type scale, the disabled contrast, the spinner under reduced motion, the
> four token choices that failed their own checklist. The rule has not changed: **when this file and
> the code disagree, the code is what ships**. What is still open is one measured gap, in
> [`PENDINGS.md`](PENDINGS.md) § *The Cadence build programme*. For the tokens as they resolve
> today, `web/src/tokens.css` is the source, and [`FRONTEND.md`](FRONTEND.md) describes the front end
> as it stands.

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
3. **The waveform is a live readout, not decoration.** It is driven by the call the page is
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

> Built. Each step is a `--type-*` shorthand in `tokens.css`, and nine of them are also a class —
> the nine the landing sets on an element. `tests/test_docs.py` fails the build on a `font-size`, a
> `fontSize` or a `font:` shorthand with a length of its own anywhere under `web/src` outside
> `tokens.css`; before the gate there were 104 of them.

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:opsz,wght@12..96,600&family=Inter:wght@400;500;600&display=swap" rel="stylesheet">
```

Both heads carry those three tags and nothing imports a font from CSS. The URL asks for **three**
weight-family pairs, which is exactly what the code declares: an earlier draft of this section asked
for Bricolage 500 as well, and no rule has ever paired `--font-heading` with 500 — the two that use
it take 600. Inter 700 went the same way.

- **Bricolage Grotesque** — `--font-heading`. Headlines only, weight 600.
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

**How a step is taken.** Each row is one custom property holding a `font` shorthand —
`--type-caption: 400 0.75rem/1.4 var(--font-body)` — so a stylesheet takes a step with
`font: var(--type-caption)` and never reaches into the markup for a class. Tracking is not part of
the `font` shorthand, so the four steps that track carry it beside the token; that is the one number
written twice, and both copies live in `tokens.css`. Nine steps are *also* a class, for the landing,
which styles inline. `button` is neither: it is spelled once in `.btn`, which every button in the
product already carries, and a `.button` class would have been a tenth class with no consumer —
which is exactly what `.eyebrow`, `.caption` and `.mono` were before this pass.

**The panel takes the small half of the scale.** Its card headings are `body-lg` at weight 500 and
not `card-title`, and nothing in it is smaller than `caption`. The reason is the frame: the video
records the panel at 1280×800, where height is the scarce resource, and seven stacked cards with
22px display headings push the live call card further under the fold than it already is. What the
scale did buy there is the floor — ten sizes between 9.5px and 11.5px became 12 or 13, so no text in
the product is under 12px at any width, which is what the checklist below asks for and never got.

## Spacing, grid, radii and shadows

> Built, and from four tokens: `--container`, `--gutter`, `--measure` and `--section-pad` in
> `tokens.css`. The container was the number 1180 written inline seven times in `Landing.tsx` and
> 980 once in `panel.css`; one place decides now. Levels 2 and 3 both exist — 3 on `.live`, 2 as the
> card hover.

**Spacing.** 4px base. `--space-1` 4 · `--space-2` 8 · `--space-3` 12 · `--space-4` 16 ·
`--space-6` 24 · `--space-8` 32 · `--space-12` 48 · `--space-16` 96.

All eight are declared in `tokens.css`.

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

Four steps and one constant, no more. All four are declared and all four are used: `--radius-xl` is
the live call card.

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

> Built, except for the input's `aria-invalid` error pattern, which has no error to carry yet —
> `panel/Questions.tsx` is the only consumer of `.input` and its one failure mode is the card's own
> error line. The `loading` state, the real `disabled` treatment and the card hover all landed in
> this pass.

**Button — ghost.** No fill and no border: `--color-accent` label, `--space-1` inline padding, and
a wash of the accent behind it on hover (10%) and press (18%). It is for an action that sits inside
a card and must not compete with the card's own primary — the panel's three keyless call buttons.
It was in the code before it was in this table, which is what § *Decisions* item 4 was about; it
earns its place because the alternative, three more bordered buttons in one row, is what the
seven-in-two-rows layout exists to avoid.

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
button keeps its width, so nothing reflows. Measured: 81px wide with the label and 81px with the
spinner. The ring is `--color-bg` at 35% with an opaque head, which is 2.06:1 against the accent for
the ring and 8.6:1 for the head — a shape read by its motion, not by its edge, which is why
**reduced motion does not freeze it**: the rule puts the label back and drops the spinner entirely.
A stopped spinner reads as a broken button, and a button that says what it is doing in words is the
better failure. That is a deliberate departure from the line above.

The disabled treatment measures **3.23:1 in dark and 3.53:1 in light** — `--tone-dim` on
`--fill-subtle`, the pair this section names. It is under the 4.5:1 the checklist asks of body text,
and it stays: WCAG exempts an inactive control from contrast on purpose, and the alternative it
replaced, `opacity: 0.45`, measured 4.18 dark but **3.15 light** and broke the rule against an
opacity on text.

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
to level 2. A card that is a link gets the focus ring on the card, not on the text inside it. The
live call card is the one exception to the hover, because it is already at level 3 and a hover that
lowered it would be a lie about what is happening.

**Navigation.** Sticky header, 64px tall, `--color-bg` at 85% with `backdrop-filter: blur(12px)`, a 1px
`--color-divider` bottom edge that only appears once the page has scrolled. Links are
`body-sm`/`--text-secondary`, `--color-text` on hover, and the current section is `--color-accent`
with a 2px underline in the same colour. The unmarked link is `--text-secondary` and not
`--text-muted`, which this section asked for first: composited over the translucent header,
`--text-muted` measures **4.39:1** in light and fails, where `--text-secondary` measures 9.4:1 light /
11.73:1 dark and the marked link 5.92 / 8.65. Which section is current is read off an
`IntersectionObserver` over the four section ids, taking the topmost one inside a strip that starts
below the header; the strip starts at 88px rather than at the header's 64 because the sections carry
`scroll-margin-top: 80px`, so a nav click parks the boundary at exactly 80 and a narrower strip marks
the section the reader just left.

**State pill.** `9999px`, `caption` uppercase with +0.03em, 2px/8px padding. Three variants:
neutral (`--fill-subtle` / `--text-muted`), accent, danger (`--danger-fill` / `--color-danger`).
`ESCALATED` and `RED FLAG` are the danger variant and they also carry a flag glyph, because a
colour-blind judge has to see it too. Measured on the panel card: neutral 4.17:1 light / 5.29:1
dark, accent 7.55 / 10.12, danger 5.62 / 7.01.

The accent variant is **not** `--color-accent-100` on `--color-accent-800`, which is what an earlier
draft of this section said. The dark theme overrides only the neutral ramp, so the accent steps carry
one value for both themes and `accent-100` is a near-white pill on a `#14171a` panel. It flips per
theme instead, exactly as `.tag-accent` already does: `--color-accent-900` / `--color-accent-200` on
dark, `--color-accent-100` / `--color-accent-800` on light. Both live in `tokens.css`, which is the
only file allowed to name a ramp step.

`CURRENT` and `RETIRED` in the fact chain are the two states of one slot, so both are pills — the
live fact accent, the retired one neutral. This section names only the `RETIRED` pill; rendering its
sibling as loose text made two facts of the same kind look like two different things.

**Transcript turn.** Speaker label in `eyebrow`/`--text-secondary`, text in `body`. The label is
`--text-secondary` rather than `--text-muted` because the live call card is level 3: `--text-muted`
on `--fill-subtle` under the turn wash measures 3.67:1 light and 4.48:1 dark, both under the 4.5:1
this system asks of text that size. `--text-secondary` measures 7.85 and 7.54. **The accent marks
the agent, not the patient** — `--turn-agent-bg` is the accent at 9% on light and 10% on dark, and
the patient sits on a neutral wash of `--color-text`. That is the opposite of the obvious choice and
it is deliberate: what the agent says is the thing the demo exists to show, and the money shot of the
whole video is one agent sentence quoting last week. A quote inside a fact is `mono`, wrapped in
`«»`, `--text-secondary`.

**Activity rail row.** A two-column grid: phase name in `eyebrow` uppercase `--text-accent` and the
timestamp right-aligned in `mono`, with the detail in `caption` spanning both. A failed phase turns
the phase name `--color-danger` and keeps the layout identical, so the rail does not jump when
something breaks.

Two deviations from the first draft, both measured against the rail ground composited over the card
— the ground is translucent, so reading the computed colour instead of compositing gives a number
that is simply wrong. The phase name is `--text-accent`, not `--color-accent-800`: that step is a
ramp step, forbidden outside `tokens.css`, and it has no dark value (2.01:1 on the dark rail).
`--text-accent` measures 6.21:1 light and 9.72:1 dark. The timestamp is `--text-muted`, not
`--tone-dim`: at `caption` size it is body text, and the rule below says `--tone-dim` never is —
it measures 3.89:1 light. `--text-muted` measures 4.6 and 6.29.

## Screens

> Both screens match this list today.

**Landing (`/`)** — eight blocks, in order:

1. **Header** — sticky nav marking the current section, theme / language / register toggles, a
   link into the panel. Its bottom edge appears on scroll.
2. **Hero** — `display-xl` headline left, body and two buttons under it; the **demo card** right,
   playing a scripted call. One orb (`--orb-mint`) blooms behind the headline.
3. **Metrics band** — four figures on the section gradient, `--color-section` to
   `--color-section-glow` with `--section-ink` on top: 70% non-adherence, 3 verticals, 333 free
   streaming hours, 313 tests. **Animated counters.** The band is dark in both themes on purpose —
   it is the page's only high-contrast block, and `--section-ink` is the one alias declared
   identically in both themes for that reason.
4. **How it works** — four steps, 4-up at desktop, each an eyebrow index plus a card title and body.
5. **Memory** — four pillars, 2×2.
6. **Stack** — five service cards, the AssemblyAI one at level 2 to mark it as the protagonist, with
   the honest-limits paragraph in `body-sm`/`--text-muted` under a hairline.
7. **The model** — three columns: who pays, what it costs, what it costs to run.
8. **Closing** — `display-lg`, two CTAs, one orb (`--orb-sky`) bottom right; then the footer.

**Panel (`/panel`)** — a patient list rail and a detail column:

1. **Patient rail** — one row per patient; the selected row is `--color-surface` with a 2px `--color-accent`
   left rule.
2. **Call controls** — seven buttons in two rows: the five keyless ones, then the two live ones,
   separated by a hairline. The first two of the keyless row — the same call with memory and without
   — are `btn-secondary`, because the comparison is the demo; the other three are `btn-ghost`. The
   live pair, which dials a real phone, is `btn-primary`. The seventh button is **replay a recorded
   call**: it re-emits a trace recorded under `seed/replay/`, so it is the one path that shows a
   whole call with no API key set, and it is how the panel is checked. The block always takes its own line under
   the patient's name, right-aligned, because five buttons do not fit beside it. The card is 997px
   wide at 1280px since the container moved, so the five fit on one line in English, which needs
   843px against 949px of card interior; the Spanish labels need 992px and still take two. At 390px
   the row stacks, nothing clipped.
3. **Live call card** — level 3 while a call runs. Transcript left, activity rail right, the
   **waveform** across the bottom, a state dot top right: live / ended / lost.
4. **How she is doing** — two sparkline tiles, pain and sessions, with verdict arrows. The plot is
   96px tall with no gridlines and no axis line: a 2px `--color-accent` polyline through one 7px dot
   per call, each dot carrying its value above it, over a `mono` row of the real dates below. Points
   sit at even intervals inset 4% from each edge, and the tallest reaches 88% of the box, so a
   value at the scale ceiling still has air above it. One call draws a dot and no line, which is
   what the *only one call* verdict says in words.

   **The arrow carries the direction and the verdict, which is the whole point of it.** `↑` or `↓`
   for the move, `→` when nothing changed, `--color-accent` when the change is good and
   `--color-danger` when it is not — and *good* is per measure, so pain falling and sessions falling
   are the same arrow in opposite colours. The sentence under it says the same thing in words, so
   colour is never the only signal.
5. **What the agent remembers** — the fact chain; a retired fact keeps its quote and gets a
   strike-through plus a `RETIRED` pill.
6. **Words the agent listened for** — a three-step diagram and the key-term chips in `mono`.
7. **Calls so far** — one row per call, with its summary, its state pills, and the
   **What AssemblyAI heard** block: entity chips and sentiment counts.

**Design preview (`docs/design-preview.html`)** — not part of the product. Tokens, type scale,
components and the protagonist effect on one page.

## Effects

Two, and no more. Everything else in the system holds still.

**1. The live waveform — the protagonist.** It sits along the bottom of the live call card and it is
a readout, not an ornament: 96 bars in `--color-accent` at 70% opacity, with the newest bar at full
opacity. Bars are `9999px`, 4px wide, 3px apart, with a 32px maximum height, centred in their
container. Fewer or thinner than that and it reads as a detail in a corner instead of the
protagonist. At 96 bars the row is 669px wide, so it spans the card rather than sitting inside the
transcript column, and the oldest bars are what a narrow window clips.

**What scales a bar is an activity envelope, not an audio level, and the doc says so rather than
letting the screen imply otherwise.** The browser never has the call audio — it is on the phone. The
server does, as µ-law frames in `app/channel.py`, but the trace the SSE stream reads is a
`deque(maxlen=500)` sized for the twenty semantic events a call emits, so ten levels a second would
evict the events the activity rail is made of, and the four replay fixtures would show a flat wave
next to a moving live one. The wave is therefore synthesised noise, gated by **who holds the floor**:
it says that the call is moving and whose turn it is, which is what a muted viewer needs, and it does
not claim a loudness it cannot measure. A measured level is the upgrade path, and it needs a carrier
that is not the trace.

Who holds the floor is read backwards off the event list, and the read is not the obvious one: a turn
event lands when that turn is **over**, so an `agent_turn` means the patient now has the floor. The
wave alternates on that, and latches idle on `call_ended`, `patient_hung_up`, or `phase_done` for the
`converse` phase — the last of which is the only event that truthfully means there is no more audio.
A speaker who holds the floor for more than four seconds drops to rest height while keeping the
colour, because the call's own silence timeout is eight seconds and a wave that keeps waving through
it would be lying twice.

When the call is idle the bars rest at 15% height. When the patient is speaking the wave is
`--color-accent`; when the agent is speaking it is `--tone-dim` — so a muted viewer can see who has the
floor. **The agent's bars are the one place the 70% does not apply**: `--tone-dim` at 70% measures
2.47:1 on the light card and 2.55:1 on the dark one, under the 3:1 this system asks of a component
boundary, and the wave reads as gone rather than as dim. At full opacity it measures 4.06:1 and
3.91:1, so that is what it uses; the patient's accent at 70% measures 3.44:1 and 4.46:1. What
separates the two speakers is the hue, teal against a desaturated grey, not the lightness — and
colour is never the only signal here, because the transcript beside it labels every turn.

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
hidden — but they jump to it instead of easing, and the idle shimmer does not run at all: the clock
keeps ticking and the tick returns early while nobody holds the floor, so the bars sit flat at 15%.

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
- Do not animate anything except the two effects above and the one exception named below.
- Do not write a raw hex, `rgba()`, or an opacity on text anywhere outside `tokens.css`.

**The exception, named: the landing's demo card.** Five keyframes run inside it and they stay.
Two are entrances that play once (`noc-in`, `noc-slide`). The third is the strike-through that
retires a superseded fact, and it is not decoration: the crossing-out *is* what the landing exists
to show, so deleting the animation deletes the argument. The fourth is an eight-bar wave that says
the card is playing a call, and the fifth a pulsing dot that says the same thing in the header of the
card. All five are consumed by `web/src/landing/DemoCard.tsx` and by nothing else. The activity
rail's `flash`, which marks the line that just landed during a live call, is in the same exception
for the same reason: it is a readout of arrival, not an ornament.

What makes the exception acceptable is two conditions the code meets today, and they are conditions
rather than an excuse. Every one of the six is switched off under `prefers-reduced-motion` — the five
in `landing.css`, `flash` in `panel.css`. And the only two that loop for ever, `noc-pulse` and
`noc-wave`, stop with the card's own pause button, because `.is-paused` pauses them from the card's
subtree: that is why `noc-pulse` has exactly one consumer and why it is no longer on the header logo.
An infinite animation with a consumer outside that subtree would break the second condition and is
therefore not covered by this exception.

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
- [ ] **The hairlines do not clear 3:1, and that is known.** Measured against `--color-surface`:
      `--color-divider` 1.29:1 light / 1.21:1 dark, `--color-divider-strong` 1.54 / 1.56. The
      checklist above asks 3:1 of a component boundary, and the input's border and the secondary
      button's border are boundaries in that sense. Raising them means re-deriving every hairline in
      the system, so it is one open row in [`PENDINGS.md`](PENDINGS.md) rather than a silent pass.
- [ ] **`--tone-dim` is never body text.** It measures 3.7:1 in light. It is for large text,
      disabled states and non-text boundaries.
- [ ] **Reduced motion** — with `prefers-reduced-motion: reduce`, the counters show their final
      value on first paint and the waveform still renders its levels without transitions.
- [ ] **Both languages** — English and Spanish, on every screen. Spanish runs longer; nothing
      clips, wraps badly, or pushes a button off its row.
- [ ] **Colour is never the only signal** — `ESCALATED`, `RED FLAG` and the error state each carry a
      glyph or a word as well as a colour.
