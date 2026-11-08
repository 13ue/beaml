# RED plan: EXPERIMENT 0005 (PROTOTYPE), N-TESTS

**[Proposal]** Solve/RED phase, 2026-11-08, at HEAD b332b12c (P1 to P5 GREEN). Tests, BEAML source, run.py steps and fixtures only. No LiveView page, no `BeamlDb`, no `mix beaml.stored`, no generated module checked in.
Plan: [plan.md](../2026-11-07/plan.md) with "Plan repair", "Corrections" and "Plan repair 2". Evidence: [red-output.md](red-output.md).
By: Opus (RED exp0005) for every line of this file.

## Files

| Path | What |
|---|---|
| `app/beaml/orders.beaml` | the source of plan repair 2: `PlaceForm`, `Order`, `Amount`, `Channel`, `Note`, `NoteForm`, `OrderQuery`, `NoteQuery`, `OrderList`, `NoteList`, `StoreError`; 4 db EFFECTS, 4 ENTRY LINES |
| `app/beaml/variants/{note_v2,stricter,no_place}/orders.beaml` | full sources, diffs below |
| `app/test/prototype/order_pages_test.exs` | N2, N2c, N3, N4 (2), N5, N6, N12 (SQL sandbox) |
| `app/test/prototype/build_test.exs` | N1, N10 (committed, empty table) |
| `app/test/prototype/stored_test.exs` | N8, N8 control, N8b, N8c (phase `n8`) |
| `app/test/prototype/notes_test.exs` | N7 seed (phase `n7_seed`); N7, N7b, N11 (phase `n7_read`) |
| `app/test/prototype/secrets_test.exs` | N13 (guard) |
| `app/test/prototype/fate_test.exs` | N9, `@tag skip: "blocked: fate slice (D036)"` |
| `app/test/support/prototype.ex` | helpers: rows by SQL, capture and action log offsets, live snapshot + provenance (N8c), compiler call, N11 DDL check, host copy build |
| `app/test/support/use_case_formatter.ex` | ExUnit formatter: use-case events to `<repo>/.beaml/actions.jsonl` and `<run>/use-cases.jsonl` |
| `app/test/support/data_case.ex` | tag `committed` (`:truncate`, `:keep`): `sandbox: false` owner (P5-14) |
| `app/test/test_helper.exs` | excludes `:phase`; adds the formatter |
| `run.py` | default subcommand `run` (below) |

## N-test mapping

| N | Test | Phase / generated source | Today fails for |
|---|---|---|---|
| N1 | build_test N1 | A, copy of host with orders.beaml | no `mix beaml.stored` |
| N2 | order_pages N2 | A | no route `/orders/new` |
| N2c | order_pages N2c (`jsonb_typeof(value->'reason') = 'null'`) | A | no route |
| N3 | order_pages N3 | A | no route |
| N4 | order_pages N4 reject, N4 `tv` | A | no route |
| N5 | order_pages N5 (`order-2` before `order-1`) | A | no route |
| N6 | order_pages N6 | A | no route |
| N7 | notes seed N7 (live build of note_v2: `rows: 2 rows, 2 checked, 0 not decodable`), notes read N7 | n7_seed under orders; n7_read under note_v2 | no route; no Note v2 module (gen needs `mix beaml.stored`) |
| N7b | notes read N7b (`rows: 3 rows, 3 checked, 0 not decodable`) | n7_read | no Note v2 module |
| N8 | stored N8 (exact P4 first line, no `order-zero`, trace or span id in stderr, N11 check) and N8 control | n8 under orders | no route |
| N8b | stored N8b (delete by SQL, stricter exit 0) | n8 | no route |
| N8c | in every `snapshot!` (files new, meta keys, ids and count equal a `psql` read) and stored N8c | n8, n7_seed, n7_read, A | no route / no task |
| N9 | fate_test, skipped | none | blocked: fate slice (D036) |
| N10 | build_test N10 (names `Orders.ui_place/1`, not `Orders.ui_orders/1`, no `BeamlDb`) | A, copy with no_place | no `mix beaml.stored` |
| N11 | notes read N11 (a Note v1 and v2 row exist, then migrations and columns equal the scaffold) and in N8 | n7_read, n8 | no Note rows (earlier phases fail) |
| N12 | order_pages N12 (`place` events `ok`, `rejected:constructor`; no value, path, source text) | A | no route |
| N13 | secrets_test N13 | A | **passes today**: a guard, no behaviour RED |

## run.py `run` (default)

1. DB check (`ERROR DATABASE: not reachable at app/.pgsock. Run run.py db-up.`), compiler (`BEAML_SPIKE` or `cargo build` of 0001), `db-reset`.
2. `stored-orders`: `MIX_ENV=test mix beaml.stored <run>/stored-orders`; `gen-orders`: compiler `--stored <dir>/responses.jsonl` → `lib/generated/orders.ex` only on exit 0; hashes of source and output.
3. `compile`: `mix compile --force --warnings-as-errors`; `test`: `mix test --warnings-as-errors` (phase A).
4. `test-n8`, `test-n7_seed` (`--only phase:<p> --seed 0`), `stored`/`gen` of `note_v2`, `compile-note_v2`, `test-n7_read`, `db-reset`.
5. Finally `stored`/`gen` of orders.beaml again; old bytes restored when it fails. `use_cases` in result.json from `<run>/use-cases.jsonl`.

Every step runs and is recorded; one failed step fails the run. A phase test checks that its module is the right one (N7: `Orders.Note` has `tag`).

## Host contract pinned by these tests (for GREEN)

→ `mix beaml.stored DIR`: writes `DIR/rows.jsonl` (each row `value` + `"source":"db"`, `"row_id"`), an empty `DIR/responses.jsonl`, `DIR/snapshot-meta.json` (`table`, `database`, `query_time`, `row_count`, `row_ids`)
→ Routes `/orders/new` (form `#place`, `order[...]`, event `place`), `/orders` (`[data-order]` items), `/notes` (form `#note`, `note[text]`, `[data-note]`, `data-tag` when the field exists)
→ Place: success `push_navigate` to `/orders`; reject flash `form rejected: <reason>`
→ Action events: `source: "ui"`, `action` = UI EVENT name; a mount with no entry call logs `mount`

## Variant diffs (against orders.beaml)

```
note_v2:   type Note { text: String }  →  type Note v2 { text: String tag: String }
           + migrate Note v1 -> v2 { add tag: String = "" }
           to_note → Note { text: text, tag: "" }
stricter:  + fn Amount "0",   _        -> Amount ! BadAmount = BadAmount {}   (before the "" clause)
no_place:  - effect ui.place PlaceForm -> Order ! StoreError = ui.event("place") |> place
```
Each variant also changes line 1 (comment).

## Decisions

**Undo**
→ Source in `app/beaml/` statt `src/`, weil the task names that path
→ Variants in `app/beaml/variants/<v>/orders.beaml` (D6B-210 stem rule)
→ run.py runs the compiler; `mix beaml.stored` writes the snapshot only
→ Tests call the task in the VM (`Mix.Task.rerun`), committed connection; `psql` reads apart
→ N1/N10 build a host copy (`MIX_DEPS_PATH`, `_build/test` without proto, absolute `probe_support` path) statt the checked-in file
→ Phases by tag and `--only phase:<p> --seed 0`
→ N8 phase before N7, reset between: a Note v2 row is off-chain for orders.beaml
→ N7 seeds one Order row too: the rows line proves two ROW TYPES
→ Page markup and action names as listed above
→ N3 excludes `request` of the db record from the no-value check (QDB-5 A)
→ Use-case events: start and finish with the error kind only, no step events (a diff can hold a value)
→ N13 stays a passing guard statt a manufactured RED
→ N11 checks Note v1 and v2 rows first (not vacuous)
→ Every run.py step runs; the last gen restores orders.beaml
All → By: Opus (RED exp0005)

**Repair**
→ N8 first line pinned from the built P4 text (0004 N18) statt 0005 output, weil expected values come from the plan and built texts. Commits us to: a P4 text change moves both. → By: Opus (RED exp0005)

**Migrate-looking (default, open, in [owner-review.md](../2026-11-07/owner-review.md#0005-red-defaults))**
→ The snapshot `responses.jsonl` is empty: `--stored` checks rows only, not the per-run capture records. → By: Opus (RED exp0005, default, open)
→ `mix beaml.stored DIR` argument and file set as the host-called form of Q5-4 B. → By: Opus (RED exp0005, default, open)
