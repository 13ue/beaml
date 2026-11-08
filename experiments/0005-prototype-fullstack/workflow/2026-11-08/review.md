# TEST and review: EXPERIMENT 0005 GREEN (commit d4e11f78)

**Verdict: PASS.** No critical or high objection. Three medium objections are recorded below.
By: Opus (TEST exp0005) for every line of this file. Not committed. Date 2026-11-08.

## Setup

→ Compiler: `git archive HEAD experiments/0001-syntax-to-beam` into a scratch dir, `cargo build -q`. Not the working-tree compiler.
→ Compiler sha256 `16ee6285…09a6` (debug build, scratch path). It differs from the GREEN build (`ad078850…3f89`). The generated output is byte-equal (below), so the difference is the build path only. **[Inference]**
→ Database: `run.py db-up` once, `db-reset` and `db-down` at the end. **[Verified]** `pg_ctl status`: no server running.

## 1 · Runs

| Check | Result | Time (real) | Evidence |
|---|---|---|---|
| `run.py run` #1 | `pass`, exit 0, 19 pass, N9 `blocked: fate slice (D036)`, `acceptance` `[]` | 17.6 s | [20261108T003740313204Z](../../results/20261108T003740313204Z/result.json) |
| `run.py run` #2 | same | 18.1 s | [20261108T003757953791Z](../../results/20261108T003757953791Z/result.json) |
| `mix compile --force --warnings-as-errors` | exit 0 | 1.0 s | this review |
| `mix test` alone (BEAML_SPIKE set) | 27 tests, 0 failures, 8 excluded (phases), 1 skipped (N9) | 3.9 s | this review |
| `mix test` alone, BEAML_SPIKE unset | 2 failures (N1, N10: "BEAML_SPIKE is not set") | — | honest fail, no false pass |

→ **[Verified]** Output hashes of both runs equal GREEN: orders `f32433c8…51c7`, note_v2 `b0990620…30c1c4`. Tracked `lib/generated/orders.ex` is `f32433c8…51c7` after the runs.
→ **[Verified]** All 16 steps exit 0 in both runs. `gen-note_v2.stderr`: `rows: 2 rows, 2 checked, 0 not decodable`.
→ db-up [20261108T003739765156Z](../../results/20261108T003739765156Z/), db-reset [20261108T004433428563Z](../../results/20261108T004433428563Z/), db-down [20261108T004433863051Z](../../results/20261108T004433863051Z/).

## 2 · Thesis probes (own scratch LiveViewTest file, deleted afterwards)

| Probe | Observed |
|---|---|
| Good submit on `/orders/new` | live redirect to `/orders`; one row `Order` v1; core keys are the v3 core (`artifact_id`, `attempt`, `operation`, `outcome`, `reason`, `redacted`, `span_id`, `trace_id`, `type`, `unknown_fields`, `unknown_keys`, `value`, `value_sha256`, `version`), `version` 3, `outcome` `accepted`; one ENTRY RECORD `ui.place` `accepted` |
| List page | shows the row; `through_beaml!("ui.orders", "orders.list")` holds |
| Empty or missing amount, empty currency (through the form) | flash `form rejected: constructor`, 0 rows, one ENTRY RECORD `rejected`/`constructor`, 0 db records. The form always sends every input, so a missing field arrives as `""` |
| Amount as a string (page event `place`) | flash `form rejected: decode`, 0 rows, ENTRY RECORD `rejected`/`decode` |
| `Orders.ui_place/1` direct: `%{}` → `Rejected{reason: "decode"}`; an extra key → accepted | as DL-133 |
| One undecodable `Order` row inserted by SQL | the whole `/orders` page shows `store failed: decode` and no row (P4 default "fails `db.list` at run time"; P4c covers the build side only) |
| N2c | `jsonb_typeof(value->'reason')` = `null` (test and run) |
| N7 / N7b | v1 row reads with `tag ""` through `ui.notes`/`notes.list`; v2 submit writes version 2; mixed list holds both; live builds 2/2 and 3/3 |
| N8 / N8b / N8c | stricter `Amount` build exits non-zero with the DL-102 constructor text; control 1/1 checked; after the SQL delete 0 rows, exit 0; every `snapshot-meta.json` names `proto_test`, table `records`, `row_ids` equal the separate `psql` read (tested in `provenance!/1`) |
| N10 | removed `ui.place` fails the host build at `Orders.ui_place/1` |
| N11 | migrations dir unchanged since the scaffold commit b40acbed; columns equal the scaffold |
| N12 | `place` results `ok`, `rejected:constructor`; no form value in the action log |
| N13 | no secret literal in `lib/` or `config/` (keys only checked, values stripped); `runtime.exs` makes salt and key at boot |
| R1 beyond `lib/proto_web` | `Repo` use only in `lib/proto/beaml_db.ex` and `lib/mix/tasks/beaml.stored.ex` (host store and snapshot task). No other `lib/proto` path reads SQL |

## 3 · GREEN defaults and test repairs

→ **`Orders.__beaml_encode_order/1` in the list page.** Not hidden: owner-review.md "0005 GREEN defaults" lists it as **Big** with options A/B/C, and green-output.md lists it as Migrate-looking. It is a language-interface decision: the host depends on a compiler-internal name. See O3 for the smallest public projection.
→ **`BeamlDb.get/3`** (`@>`, newest row). Flagged Big, unused. Probe shows a semantic gap, see O2.
→ **One `/notes` page.** Page-visible only; the tests pin `/notes`. No objection.
→ **Test repair 1** (`File.mkdir_p!`): harness fault, copy set unchanged. Honest.
→ **Test repair 2** (`v2_module!` by the encoder key `tag`): still fails under the v1 module (v1 encoder has no `tag`). Honest; it also ties the test to the internal name (noted in green-output).
→ **Test repair 3** (R1 guard): a text scan for `Repo.` and `"records"`. It does not catch `BeamlDb.` or `Ecto.Adapters.SQL` in a page. N5, N7 and N7b (`through_beaml!`) prove the read path for the tested pages. Low; dropped.
→ **Register gap (note):** none of the 0005 RED or GREEN defaults is in `wiki/planning/decisions-to-be-made.md` yet. That is docs-phase work.

## 4 · Screens (OWNER visual check)

`mix phx.server` on port 4517, `proto_dev`, demo rows written through `Orders.ui_place/1` and `Orders.ui_note/1`. Headless Chrome, dark, 2x, 720×900.

→ [screens/orders-new.png](screens/orders-new.png)
→ [screens/orders.png](screens/orders.png)
→ [screens/notes.png](screens/notes.png)

**[Verified]** The list pages show the BEAML values, the Unknown channel as its text. **[Verified]** The form inputs are invisible in dark mode (no border, no background; `app.css` loads with HTTP 200). The OWNER sees labels but no fields. Medium for the OWNER test by hand; not evidence for the thesis. Server stopped, port free, `proto_dev` truncated by `db-reset`.

## 5 · Objections (one round, max three)

**O1 · Medium · The repeatable command never checks the dev rows, and it erases them.**
→ Evidence: `run.py run` truncates `proto_dev` and `proto_test`, then snapshots `proto_test` (0 rows) for the shipped `gen-orders`. It truncates both again before the last `gen-orders`.
→ Consequence: rows the OWNER makes by hand on `/orders` are lost at the next run. The shipped `orders.ex` is checked against 0 rows; a stricter TYPE with dev rows passes `run.py`. N8 proves the gate in `proto_test` only.
→ Resolving test: a `run.py build` (or `gen` without reset) that snapshots `proto_dev`; one dev row plus `variants/stricter` exits non-zero. Or state in the README that `run` wipes `proto_dev`.

**O2 · Medium · `BeamlDb.get/3` matches the raw stored JSON, not the migrated value.**
→ Evidence (probe): a v1 `Note` row without `tag`; key `%{"text" => …}` finds it; key with the v2 default `tag ""` finds nothing; key `%{}` returns the newest row of any content.
→ Consequence: when a source line uses `db.get`, a key over a field added by `migrate` misses every older row. An empty key returns an arbitrary row.
→ Resolving test: in the `db.get` step, a get by a v2-default field over a v1 row returns the migrated value; an empty key is a decode or build error. Add both facts to the owner-review Big entry.

**O3 · Medium · The page depends on a compiler-internal name.**
→ Evidence: `order_list_live.ex` calls `Orders.__beaml_encode_order/1`; the generated encoders are public `def` with the internal `__beaml_` prefix; notes_test.exs uses `__beaml_encode_note/1`.
→ Consequence: a compiler refactor of internal names breaks the host build (not the page at run time). The host API is set by default, not by an OWNER decision.
→ Smallest public projection (option C, concrete): for each output TYPE of an ENTRY LINE the compiler emits one line `def project_<type>(v), do: __beaml_encode_<type>(v)` (e.g. `Orders.project_order/1`). Resolving test: extend the R1 guard with "no `__beaml_` in `lib/proto_web`" and assert `Orders.project_order/1` gives the DL-105 projection.

## Decisions

**Undo**
→ Scratch compiler from `git archive HEAD` statt working tree, weil another worker edits `main.rs` → By: Opus (TEST exp0005)
→ Port 4517 for the server, demo rows through `Orders.ui_*` → By: Opus (TEST exp0005)
→ Screenshot with `--timeout=4000` statt `--virtual-time-budget`, weil the LiveView socket kept the budget open → By: Opus (TEST exp0005)
→ `db-reset` before `db-down`, so `proto_dev` holds no demo row → By: Opus (TEST exp0005)
→ R1 guard gap (`BeamlDb.`, `Ecto`) dropped as low → By: Opus (TEST exp0005)
→ Invisible inputs noted, not an objection (no thesis effect) → By: Opus (TEST exp0005)

**Repair**
→ PASS statt BLOCK, weil no objection reaches high: all use cases pass twice, probes match the thesis. Commits us to: O1 to O3 stay open → By: Opus (TEST exp0005)
→ O1, O2, O3 as medium statt high, weil O1 is a run-design limit (N8 proves the gate), O2 is unused code, O3 is already flagged Big → By: Opus (TEST exp0005)

**Migrate (OWNER chooses; defaults stay as built)**
→ O3: public projection A (as built) · C `project_<type>/1` emitted by the compiler → By: Opus (TEST exp0005, open)
→ O1: `run` keeps the reset and the README says so · a separate dev-rows build step → By: Opus (TEST exp0005, open)
