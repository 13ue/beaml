# RED plan: DB TRANSPORTS, part P4a (EXPERIMENT 0005 prerequisite P4)

**[Proposal]** Solve/RED phase, 2026-11-07. By: Opus (RED db-transport). Test file: `tests/slice6_db_test.py`. Fixtures: `slice6/db/`. Evidence: [red-output.md](red-output.md).
Inputs: [plan.md](plan.md) with "Plan repair" and "Plan repair 2" (these override the first sections), [decisions.md](decisions.md), [plan-review.md](plan-review.md) (PASS after re-check 2), the record-format-v3 plan (key names win) and the multi-effect-module plan (module from the stem, `run(operation, …)`).
No production file, no existing test and no existing fixture changed. P4b (N17 to N27 except N25b) is a later RED.

## N to plan mapping

| Test (method or case prefix) | Plan item | Asserts |
|---|---|---|
| `test_N1_db_source_builds` | N1, PDB-20 | `orders.beaml` exits 0; `defmodule Orders do`, `def orders_save(`, `orders_load(`, `orders_list(`, `ui_orders(`, `defmodule Replay do`; no `defmodule Http do`, no `BeamlSpike` |
| `test_N1b_variants_build` | PDB-28, PDB-34 | `plain/`, `plain_v2/`, `two_rows/`, `no_app/` build |
| `N2_*` | N2, PDB-14, PDB-30, O1 | one put `{"records", {"Order", 1}, json}` with `is_binary(json)`; decoded key set = the 14 core keys; values (version 3, operation, attempt 1, `type`, `value == wire1`, digest, `accepted`, reason `:null`, empty lists) |
| `N3_kept_value` | N3, PDB-13 | `channel: "tv"`, `unknown_fields ["channel"]`, digest |
| `N4_*` | N4 | list round trip in host order; the list call `{:db, :list, "records", "Order", %{}}` |
| `N5_control_v1_writer` (plain/) | N5 support | the v1 writer emits the test-built `type`, `value`, digest, so the test-built v1 row is trustworthy |
| `N5_*` (plain_v2/) | N5, DL-127 lazy, PDB-31 | v1 row migrates on read (`note ""`); the stored row keeps version 1 and its core; save writes `{"Order", 2}`; list holds both; load migrates |
| `N6_control_*` | N6 control | the test-built good core lists and loads (a reader that rejects every row fails here) |
| `N6_list_*`, `N6_load_*` | N6, PDB-15, O2 | digest, `type.name`, `type.version`, fingerprint → `decode`; currency `""` with a good digest → `constructor`; list only: core not a map, not JSON, value not a binary → `decode` |
| `QDB4_one_bad_row_fails_the_list` | QDB-4 A | a bad row behind a good newer row fails the list with `decode` |
| `N7_*` | N7, QDB-1 A | load by the one String key field; the get call carries the key map; no row → `not_found` |
| `QDB3_newest_row_wins` | QDB-3 A | two rows with one key: the newer one comes back |
| `N8_<mode>_is_transport` | N8, PDB-12 | modes down, raise, exit, junk, okjunk: save, load, list each give `transport`; no row; the process lives |
| `N9_*` | N9 | client spans `orders.orders.save` / `.load` / `.list`; a failure sets `{:attr, :reason, "transport", …}` |
| `N10_*` | N10, QDB-5 A, QDB-6b, PDB-17, PDB-18 | one `"responses"` record per call: key set core + `request`; save, load, list values; `items.0.channel`; rejected records for transport, not_found, decode (`value` null) |
| `N11_*` | N11, PDB-19, PDB-29 | `Orders.Replay.run(operation, a0, trace_id, records)` for save, list, load with the fake in `:forbid` (no call); a rejected record replays to `transport`; wrong operation → `:operation_mismatch` |
| `test_N12_rejects` (15 files) | N12, Checks table, PDB-31 | each `bad/*.beaml` exits 1 with its exact text (table below) |
| `test_N12_order_v2_…` | N12, PDB-31 | `order_v2/` exits 1 with the D6B-39 constructor text for `Order.amount` |
| `test_N12_s13_db_get_is_a_kind_now` | "Existing assertions that change" | `bad/unsupported_effect_kind.beaml` gives the table text |
| `test_N13_…keep_their_bytes` (guard) | N13 | 148 tracked sources without a db EFFECT or LIST TYPE: exit, stdout, stderr equal to `P4_BASE` |
| N14 (in `compile()`) | N14 | every compile: no path, no source text, no stored value, no `db.put(` in `.beaml/actions.jsonl` |
| `test_N15_*` | N15 | fmt keeps the five valid fixtures; single-spaced db EFFECT lines align back to the fixture |
| `test_N16_grammar_list_type` | N16 | `list_type: ($) => seq("[", $.type, "]")`, `test/corpus/list_type.txt`, `"["` `"]"` punctuation; `tree-sitter parse` of three fixtures without ERROR |
| `test_N25b_*` | N25b, M-a, PDB-33 | `orders.list` record with item 0 `channel "app"` under `no_app/` exits 1 with the DL-122 text; `tv` with `items.0.channel` exits 0; the same `app` record under `orders.beaml` exits 0 |
| `test_N2c_…` (skipped) | 0005 N2c | the host-side `jsonb_typeof` tie needs Postgres; 0005 only |

N12 files and texts (one EFFECT per file, no ENTRY LINE, so they do not depend on P3): `fourth_kind` (`db.query`), `table`, `put_head`, `get_key`, `get_key_field`, `list_query`, `list_output`, `list_elsewhere`, `list_element`, `row_constructor`, `row_redacted`, `row_enum_no_keep`, `row_enum_no_literals`, `row_enum_chain`, `row_constructor_chain`. Texts as the Checks table of plan.md; the two `*_chain` texts are the built D6B-39 texts (Plan repair O3).

## Dependencies (would fail for P2 or P3/P5 until both are GREEN)

| Needs | Tests |
|---|---|
| P3/P5 (several EFFECTS, module `Orders`, `Replay.run/4`) | N1, N1b, every runtime case (N2 to N11, N5), N15 and N15b (fmt runs the checks: `slice 1 supports one effect`), N25b (three EFFECTS) |
| P2 (v3 keys, `accepted`/`rejected`, `span_id`, the v3 `--stored` reader) | N2 key set and values, N10, N11 rejected replay, N25b (record version 3) |
| Neither | N12 (all 17 reject cases), N13, N16 |

- **[Inference]** With P2 and P3 GREEN and P4 not built, the first failures stay the lexer (`[`) and `unsupported effect kind` texts. A RED review after P2/P3 should re-run and confirm no case fails on a P2 or P3 text.
- `P4_BASE` (N13) is `ea64059c`, the HEAD at this RED. P2 and P3 GREEN change EFFECT bytes first, so the P4 GREEN worker sets `P4_BASE` to its start commit.

## GREEN notes

- `tests/slice6_pipe_test.py` S13 (`BAD["unsupported_effect_kind.beaml"]`) must change to the table text in GREEN (plan table). This file asserts the new text already.
- Five pin sites are named in the test docstring. None moves in P4.
- Fixtures not created here: `stricter/`, `put_only/`, row files (P4b).

## Decisions

**Undo**
→ Fixtures carry no VERSION MARK (`type Order { … }` plus `migrate`) statt `type Order v2`, weil `fmt` (DL-104 form b) deletes an implied mark and N15 needs fmt-stable fixtures. → By: Opus (RED db-transport) · Undo
→ Effect line columns follow the HEAD `aligned` rule (computed, HEAD `fmt` cannot run on these sources). → By: Opus (RED db-transport) · Undo
→ `order_v2` text names `orders.save` and `Order.amount` (first db EFFECT, first field in source order); closes the plan [Unknown] by default. → By: Opus (RED db-transport, default, open) · Undo
→ N25b text names `TYPE Order v1` and field `channel` (the ROW TYPE and its field), not `OrderList` or `items.0.channel`. → By: Opus (RED db-transport, default, open) · Undo
→ Bad files minimal with one EFFECT each. → By: Opus (RED db-transport) · Undo
→ `row_enum_chain` added beside `row_constructor_chain` (both built D6B-39 texts). → By: Opus (RED db-transport) · Undo
→ Fourth KIND case uses `db.query` (DL-129 option S). → By: Opus (RED db-transport) · Undo
→ Fake BeamlDb in an `Agent`, not the process dictionary, and mode `:okjunk` (`{:ok, :what}`) for "every other return shape". → By: Opus (RED db-transport) · Undo
→ N6 extra list cases: not JSON, value not a binary (Plan repair O2 text). → By: Opus (RED db-transport) · Undo
→ Controls added: N5 v1 writer on `plain/`, N6 good core, N25b same record under `orders.beaml`. → By: Opus (RED db-transport) · Undo
→ N9 by membership, not the whole log (a prepared event for a one-step pipe is not this step's question). → By: Opus (RED db-transport) · Undo
→ `slice6/db/stored/` holds an empty `responses.jsonl` and `rows.jsonl`; every build uses it, so PDB-23 cannot hide a check. → By: Opus (RED db-transport) · Undo
→ N16 checks file facts and `tree-sitter parse`; `generate` and `test --rebuild` stay GREEN/TEST commands (they write `src/`). Skip when the binary is missing. → By: Opus (RED db-transport) · Undo
→ N2c skipped with its reason (0005 only). → By: Opus (RED db-transport) · Undo
