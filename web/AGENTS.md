# web/ — rules

In addition to [`../AGENTS.md`](../AGENTS.md), which applies everywhere.

- **No ramp step or text opacity outside `src/tokens.css`.** Use a name from the table in
  [`../docs/FRONTEND.md`](../docs/FRONTEND.md) § *The ramp rule* — `--text-secondary`,
  `--text-muted`, `--text-accent`, `--section-ink`, `--tone-dim`, `--fill-subtle`, `--color-danger`
  and the rest of that list. The gate, which must return nothing:
  ```bash
  grep -rn 'color-neutral-[0-9]\|color-accent-[0-9]' src \
    --include='*.tsx' --include='*.ts' --include='*.css' | grep -v tokens.css
  ```
  It includes `.tsx` because some colours live there as data, not as styles. The globs are
  quoted because zsh expands an unquoted one before `grep` sees it and aborts the whole
  command, which prints nothing and reads exactly like a pass. That is why the gate also lives
  in `tests/test_docs.py`, walked in Python: `make test` runs it, and no shell can mangle it.
- **Every visible string comes from a `copy.ts`.** Add it to the type first; `tsc` then names every
  set that is missing it. A string that interpolates a value is typed as a **function**, never built
  by concatenation — word order moves in Spanish.
- **The nested maps have a parity gate too.** `measure`, `unit`, `category`, `mood`, `program`,
  `rule`, `phase` and `reason` in the panel, `demoCategory` in the landing, are typed
  `Record<string, string>`, so `tsc` cannot see a key that only one language has. The `parity` block
  at the end of each `copy.ts` can: it fails the build when the two drift. A key added to one
  language goes in the other in the same change.
- **English is the annotated base, Spanish the translation.** Patient data is different: the call
  happens in English, so `panel/content.ts` is keyed by the English string and translates *into*
  Spanish. Anything the extractor writes live is not in that table and falls through on purpose.
- **`pnpm build` is the check here** — `tsc -b && vite build`. There is no test runner in this
  directory and presentational components do not earn one. It is not the only gate on `web/src`
  though: `make test` walks this tree in Python for the ramp rule and for the line counts
  `docs/FRONTEND.md` publishes, so run both before calling a change done.
- **Measure contrast by compositing on a canvas**, not by parsing the CSS string: `getComputedStyle`
  returns `color(srgb r g b / a)` with 0–1 components for `color-mix()` values.
- **Respect `prefers-reduced-motion`** in CSS *and* in JS — `prefersReducedMotion()` in `src/prefs.ts`.
- **Exact dependency versions.** No `^` or `~`; `pnpm-lock.yaml` is committed.
- **No comments**, except `ponytail:` markers naming a deliberate ceiling and its upgrade path.

Reference: [`../docs/FRONTEND.md`](../docs/FRONTEND.md), the front end as it is ·
[`../docs/DESIGN.md`](../docs/DESIGN.md), as it is meant to become, with the gap in
[`../docs/PENDINGS.md`](../docs/PENDINGS.md) · [`../docs/LANDING.md`](../docs/LANDING.md), a record
