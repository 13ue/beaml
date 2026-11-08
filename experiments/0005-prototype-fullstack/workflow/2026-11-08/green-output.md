# GREEN output: EXPERIMENT 0005 (PROTOTYPE), host code

**[Verified]** GREEN phase, 2026-11-08, HEAD eaa1eaf7. Minimum host code for the N-TESTS of [red-plan.md](red-plan.md).
By: Opus (GREEN exp0005) for every line of this file. Not committed.

## Commands

```
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>; cargo build -q   # in <scratch>/experiments/0001-syntax-to-beam
python3 -B experiments/0005-prototype-fullstack/run.py db-up
BEAML_SPIKE=<scratch>/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0005-prototype-fullstack/run.py
python3 -B experiments/0005-prototype-fullstack/run.py db-down
```

Compiler sha256 `ad078850…3f89` (debug build, scratch path). Toolchain: Python 3.13.12, Elixir 1.18.1 / OTP 27, pg_ctl 17.11.

## What exists

| Path | Owner | What |
|---|---|---|
| `app/lib/generated/orders.ex` | BEAML (generated) | `run.py gen` of `app/beaml/orders.beaml` over a live empty snapshot; sha256 `f32433c8…51c7` (Q5-5 A) |
| `app/lib/proto/beaml_db.ex` | host | `BeamlDb.put/3`, `list/3`, `get/3` over `Proto.Repo` and `records`; JSON binaries in (`$n::text::jsonb`) and out (`value::text`); only table `"records"` |
| `app/lib/mix/tasks/beaml.stored.ex` | host | `mix beaml.stored DIR`: `rows.jsonl` (ROW CORE + `source: "db"`, `row_id`), empty `responses.jsonl`, `snapshot-meta.json` (`table`, `database` = `current_database()`, `query_time` = `now()`, `row_count`, sorted `row_ids`) |
| `app/lib/proto_web/live/order_form_live.ex` | host | `/orders/new`: form `#place`, event `place` → `Orders.ui_place/1`; ok → `push_navigate` `/orders`; error → flash |
| `app/lib/proto_web/live/order_list_live.ex` | host | `/orders`: mount → `Orders.ui_orders(%{})`; renders the BEAML value through `Orders.__beaml_encode_order/1` |
| `app/lib/proto_web/live/notes_live.ex` | host | `/notes`: mount → `Orders.ui_notes(%{})`; form `#note`, event `note` → `Orders.ui_note/1`, then `push_navigate` `/notes` (R2) |
| `app/lib/proto_web/action_log.ex` | host | one `source: "ui"` event per mount and event to `<repo>/.beaml/actions.jsonl`: `ts`, `action`, `target`, `result`, `keys` (count). No value |
| `app/lib/proto_web/router.ex` | host | three `live` routes |
| `app/lib/proto/application.ex` | host | creates the capture dir before `ProbeSupport.Capture` writes |
| `app/test/prototype/guard_test.exs` | test | R1: no `Repo.` and no `"records"` in `lib/proto_web` (no `use_case` tag, phase A) |

Flow (observed by N3, N5, N7, N7b): page → `Orders.ui_<event>/1` (BEAML: decode, root span, ENTRY RECORD) → BEAML flow → `BeamlDb` (host: SQL) → BEAML: row decode, MIGRATE CHAIN, db record → page renders the returned value.

## Run [20261108T003455384057Z](../../results/20261108T003455384057Z/result.json)

→ Status `pass`, exit 0. All 16 steps exit 0. `acceptance` `[]`.
→ `use_case_counts`: 19 pass, 1 blocked (N9 `blocked: fate slice (D036)`).
→ `stored-note_v2`: `row_count` 2; `gen-note_v2.stderr`: `rows: 2 rows, 2 checked, 0 not decodable`, no DEAD LINE.
→ Output hashes: orders `f32433c8…51c7` (both gens), note_v2 `b0990620…30c1c4`. Source hashes equal red-output.
→ `compile` and `compile-note_v2`: `mix compile --force --warnings-as-errors` exit 0.

| Use case | Test(s) | Result |
|---|---|---|
| N1 | host copy builds, `Orders` with 4 `ui_` | pass |
| N2, N2c | one Order row, JSON null `reason` | pass |
| N3 | one ENTRY RECORD + one db record, one trace | pass |
| N4 (2) | reject flash, no row; `tv` stored as text | pass |
| N5 | newest first, `ui.orders` + `orders.list` pairs | pass |
| N6 | Unknown channel lists as text | pass |
| N7 (2) | note_v2 live build 2/2; v1 row lists with `tag ""` through BEAML | pass |
| N7b | v2 row; list of v1 and v2; live build 3/3 | pass |
| N8 (2), N8b, N8c | stricter blocks, control, delete frees, snapshot ids | pass |
| N9 | fate slice | blocked |
| N10 | removed `ui.place` fails at `Orders.ui_place/1` | pass |
| N11 | v1 and v2 Note rows, no DDL change | pass |
| N12 | `place` results `ok`, `rejected:constructor`; no value | pass |
| N13 | no secret literal (still green) | pass |

Earlier GREEN runs (kept): `20261108T003326630616Z` fail (N7, N7b, N11: the v2 module check, see repair 2); `20261108T003414309465Z` pass (before `mix format`). db-up `20261108T003150082566Z`, db-down `20261108T003511567572Z`: pass; the cluster is stopped.

## Test repairs (2026-11-08)

→ **1 · `host_build/2`** (`test/support/prototype.ex`): `File.cp_r!/2` makes no parent dir; N1 and N10 raised `File.CopyError` on `test/support` and `_build/test`. Added `File.mkdir_p!` of the parent; the copy set is unchanged. Reason: a harness bug the RED never reached (the snapshot step failed first).
→ **2 · `v2_module!/0`** (`test/prototype/notes_test.exs`): checked a struct `Orders.Note`. The compiler emits no struct for a String-only TYPE (a map), so the check failed under v2. Now `Map.has_key?(Orders.__beaml_encode_note(%{}), "tag")`. The v1 encoder has no `tag`, so the check still fails under the wrong module. The N7 and N7b value asserts are unchanged.
→ **3 · R1 guard** (new `test/prototype/guard_test.exs`): requested by the RED re-check. No `use_case` tag, so EXPECTED in `run.py` does not change.

No contract line of the RED review moved. No markup repair was needed.

## Limits

→ **[Inference]** R1 is a text scan: a page could still read SQL through a helper outside `lib/proto_web`.
→ **[Inference]** The list page calls a generated `__beaml_` encoder; a compiler rename breaks the host build, not the page.
→ **[Unknown]** `BeamlDb.get/3` runs in no test (no source line uses `db.get`, P5-05).
→ No browser test (exclusion). Result files hold the OS account name in paths, as in earlier runs.

## Decisions

**Undo**
→ One `/notes` page with form and list statt `/notes/new` + `/notes`, weil the tests pin `/notes` only → By: Opus (GREEN exp0005)
→ `BeamlDb` passes a `Repo.query` error tuple as is; generated code maps it to `transport` → By: Opus (GREEN exp0005)
→ `BeamlDb` matches the table `"records"` only; another name raises (caught as `transport`) → By: Opus (GREEN exp0005)
→ Snapshot `database` from `current_database()`, rows by `id` → By: Opus (GREEN exp0005)
→ Action event `ts` in whole seconds (no fraction can echo `12.50`, N12) → By: Opus (GREEN exp0005)
→ Action log path fixed at compile time (`<repo>/.beaml/actions.jsonl`) → By: Opus (GREEN exp0005)
→ Capture dir created at app start → By: Opus (GREEN exp0005)
→ Flash through the core `<.flash kind={:error}>`, no `Layouts.app` → By: Opus (GREEN exp0005)
→ Generated module built from `git archive HEAD` compiler in scratch → By: Opus (GREEN exp0005)

**Repair**
→ Test repairs 1 and 2 statt host workarounds, weil both were harness faults (no struct exists; no parent dir). Commits us to: the v2 check depends on the generated encoder name. → By: Opus (GREEN exp0005)
→ R1 guard as an untagged phase A test statt a new use case, weil EXPECTED then stays the 20 pairs. Commits us to: a guard failure fails the `test` step, not a use case. → By: Opus (GREEN exp0005)
→ Notes submit `push_navigate` statt an in-page re-list, weil R2 allows one pair per submit. Commits us to: the page reloads after a note. → By: Opus (GREEN exp0005)

**Migrate-looking (default, open, in [owner-review.md](../2026-11-07/owner-review.md#0005-green-defaults))**
→ List page renders through `Orders.__beaml_encode_order/1` → By: Opus (GREEN exp0005, default, open)
→ `BeamlDb.get/3` key match by `value->'value' @>`, newest row, `{:ok, nil}` when none → By: Opus (GREEN exp0005, default, open)
→ Notes: one page `/notes`, reload after submit → By: Opus (GREEN exp0005, default, open)
