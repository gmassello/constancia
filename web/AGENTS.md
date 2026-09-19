# web/ — rules

In addition to [`../AGENTS.md`](../AGENTS.md), which applies everywhere.

- **No ramp step or text opacity outside `src/tokens.css`.** Use the semantic aliases
  (`--text-secondary`, `--text-muted`, `--text-accent`, `--section-ink`, `--tone-dim`,
  `--fill-subtle`, `--color-danger`). The gate, which must return nothing:
  ```bash
  grep -rn 'color-neutral-[0-9]\|color-accent-[0-9]' src \
    --include=*.tsx --include=*.ts --include=*.css | grep -v tokens.css
  ```
  It includes `.tsx` because some colours live there as data, not as styles.
- **Every visible string comes from a `copy.ts`.** Add it to the type first; `tsc` then names every
  set that is missing it. A string that interpolates a value is typed as a **function**, never built
  by concatenation — word order moves in Spanish.
- **English is the annotated base, Spanish the translation.** Patient data is different: it is keyed
  by the Spanish string in `panel/content.ts` and falls through untranslated on purpose.
- **`pnpm build` is the only check** — `tsc -b && vite build`. There is no test runner here and
  presentational components do not earn one.
- **Measure contrast by compositing on a canvas**, not by parsing the CSS string: `getComputedStyle`
  returns `color(srgb r g b / a)` with 0–1 components for `color-mix()` values.
- **Respect `prefers-reduced-motion`** in CSS *and* in JS — `prefersReducedMotion()` in `src/prefs.ts`.
- **Exact dependency versions.** No `^` or `~`; `pnpm-lock.yaml` is committed.
- **No comments**, except `ponytail:` markers naming a deliberate ceiling and its upgrade path.

Reference: [`../docs/FRONTEND.md`](../docs/FRONTEND.md) · [`../docs/LANDING.md`](../docs/LANDING.md)
