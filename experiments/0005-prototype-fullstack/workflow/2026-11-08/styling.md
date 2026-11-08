# Styling of the PROTOTYPE pages (2026-11-08)

Worker: proto-style (Opus). Scope: the HOST pages `/orders/new`, `/orders`, `/notes`. No change to `app/beaml/`, `app/lib/generated/`, the compiler or `run.py`.

## What was missing

The scaffold was generated without the asset pipeline (the `--no-tailwind --no-esbuild` form of `mix phx.new`):

- No `assets/` directory. `priv/static/assets/` held a prebuilt `default.css` and a stub `app.js` without a LiveSocket. The pages did not connect LiveView in the browser.
- No `tailwind`, `esbuild` or `heroicons` deps. No `assets.setup` / `assets.build` / `assets.deploy` aliases. No `config :tailwind` / `config :esbuild`. `watchers: []` in `config/dev.exs`.
- The three LiveViews did not use `<Layouts.app>` and had no classes.

## What was added

Reference: a fresh `mix phx.new proto --no-install` (installer 1.8.5) in a scratch directory. The asset parts were copied from it.

- `mix.exs`: deps `esbuild ~> 0.10`, `tailwind ~> 0.3`, `heroicons` (v2.2.0, sparse). Aliases `assets.setup`, `assets.build`, `assets.deploy`; `setup` runs them.
- `config/config.exs`: esbuild 0.25.4, tailwind 4.1.12 (generator values).
- `config/dev.exs`: esbuild and tailwind watchers.
- `assets/`: `css/app.css` (Tailwind v4, daisyUI plugin, light and dark theme), `js/app.js` (LiveSocket, topbar, colocated hooks), `vendor/` (daisyui, daisyui-theme, heroicons, topbar), `tsconfig.json`.
- `root.html.heex`: generator version (theme script, no `default.css`). `priv/static/assets/default.css` deleted.
- `layouts.ex`: generator `app/1` with a nav (Orders, New order, Notes), theme toggle, reconnect flashes (plain text, no gettext).
- `core_components.ex`: flash closes through `lv:clear-flash` (generator), not the `data-flash` stub handler.
- `.gitignore`: generator lines (`/priv/static/assets/`, cache manifest, node files).
- Pages: `<Layouts.app flash={@flash}>`; order form and note form as cards with `<.input>` labels and a primary `<.button>`; orders as a daisyUI table with an empty state; notes as a `list` with an empty state.
- Kept: form ids `place` / `note`, every input name, `data-order`, `data-note`, `data-tag`, all `Orders.*` and `ActionLog` calls.

## Results

- `mix assets.setup`, `mix assets.build`: pass (tailwind 4.1.12, daisyUI 5.0.35, esbuild 0.25.4).
- `mix test` (BEAML_SPIKE = the current 0001 debug build, fresh BEAML_RUN_DIR): 27 tests, 0 failures, 8 excluded, 1 skipped.
- `mix test --only phase:n8 --seed 0`: 4 pass. `--only phase:n7_seed`: 1 pass. Phase `n7_read` not run (needs `run.py` to generate note_v2).
- `mix compile --warnings-as-errors`: pass in dev and test.
- curl on the running dev server: the three pages 200, `/assets/css/app.css` and `/assets/js/app.js` 200, the page classes (`card`, `table-zebra`, `navbar`, `btn-primary`, `list-row`) are in the built CSS.
- Limit: without `BEAML_SPIKE`, N1 and N10 fail (`BEAML_SPIKE is not set`). Without a fresh `BEAML_RUN_DIR`, they fail on old snapshot dirs in the tmp dir. Both are test setup, not the styling.

## Decisions

- PS-1. Undo. Copy the asset parts of the 1.8.5 generator, not a custom setup. By: Opus (proto-style).
- PS-2. Undo. Leave out the other generator deps (gettext, swoosh, req, live_dashboard). They are not part of the asset pipeline. By: Opus (proto-style).
- PS-3. Repair. Chose plain text for the reconnect flash titles over adding gettext, because the app has no gettext backend. Commits us to: English text only. By: Opus (proto-style).
- PS-4. Repair. Chose the generator `lv:clear-flash` close over the `data-flash` stub handler, because the new `app.js` has no stub handler. By: Opus (proto-style).
- PS-5. Repair. Chose to ignore `/priv/static/assets/` (generator rule) over keeping the build output in git. Commits us to: a fresh clone runs `mix assets.setup` and `mix assets.build` (or `mix setup`). The main agent must `git rm --cached` the two tracked build files. By: Opus (proto-style).
- PS-6. Undo. Hand-written daisyUI table for the orders list, not `<.table>`, because `<.table>` sets no `data-order` on a row. By: Opus (proto-style).

## Open questions for the OWNER

None above Repair.
