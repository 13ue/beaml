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

## P4b: `--stored` over the ROW SNAPSHOT

**[Proposal]** Solve/RED phase, 2026-11-08. By: Opus (RED db-stored). Test file: `tests/slice6_db_stored_test.py` (imports the P4a helpers of `slice6_db_test.py`; no existing test changed). Evidence: [red-output.md](red-output.md#p4b-run).
Inputs: plan.md with both repairs (N17 to N27, N20b), decisions.md (PDB-21 to PDB-36, QDB-7 A, QDB-8 B), the P4a RED review M1, record-format-v3 plan (count lines, QV3-7 A, QV3-8 B, `digest not verified (P2b)`), DL-040, DL-102, DL-122, DL-124, DL-134, DL-136, DL-137, DL-140.
New fixtures: `slice6/db/stricter/orders.beaml` (`fn Amount "0", _` before the general clause), `slice6/db/put_only/orders.beaml` (one `db.put`, no reader, no ENTRY LINE), `slice6/db/stored/meta/` (sample ROW SNAPSHOT: two rows, empty `responses.jsonl`, `snapshot-meta.json`). Row files of every other case are written per test into a temp directory beside an empty or given `responses.jsonl`.

### Mapping

| Test | Plan item | Asserts |
|---|---|---|
| `N17_clean_rows`, `N17b_empty_row_snapshot` | N17, PDB-24 | exit 0, module `Orders`, stderr exactly `rows: 2 rows, 2 checked, 0 not decodable` (empty file: `0 rows, 0 checked, 0`) |
| `N18_stricter_constructor_blocks`, `N18b_…` | N18, DL-102, PDB-32, PDB-36 | `error: TYPE Order: 1 stored ROW of table records fails the constructor of Amount for field amount with BadAmount`, `record source: <rows>:1 (line 1)`, help line by `HELP_PREFIX`; two rows: `2 stored ROWS … fail`, first line 2 |
| `N18_control_*` | N18 controls | same row under `orders.beaml` builds; `stricter/` without the row builds |
| `N19_lost_literal_blocks`, `N19_control_*` | N19, DL-122, DL-124 | the DL-122 ROW text (three lines exact); kept `tv` with `unknown_fields ["channel"]` builds; the `app` row under `orders.beaml` builds |
| `N20_chain_rows_build` | N20, DL-043, DL-127 | `plain_v2/` with a v1 and a v2 row: `2 rows, 2 checked` (the v1 row passes the DL-101 shape check only after the chain) |
| `N20_off_chain_row_blocks`, `N20_newer_version_blocks` | N20 | `error: TYPE Order cannot read 1 stored ROW of table records` and `record source: <rows> (first at line N)` |
| `N20b_two_row_types_build` | N20b, QDB-8 B, PDB-34 | `two_rows/` with one `Order` v1, one `Note` v1, one `Note` v2 row: `3 rows, 3 checked, 0 not decodable` |
| `N20b_control_note_row_under_the_order_type_blocks` | N20b control (Fable) | path text naming `Order`, never `TYPE Note` |
| `N20b_control_note_row_off_its_chain_blocks` | PDB-35 | path text naming `Note` |
| `N21_not_decodable_rows_are_counted` | N21, DL-136, DL-137 | bad digest + `Invoice` row: `3 rows, 1 checked, 2 not decodable` |
| `N21b_rows_not_accepted_are_counted_QV3_8_B`, `N21b_rejected_row_skips_the_constructor_check` | PDB-26, QV3-8 B | a `rejected` row (also off-chain) is counted, not path-checked; a `rejected` `0` row under `stricter/` builds (`1 rows, 0 checked, 1`) |
| `N29_read_order_*` | PDB-15 read order | digest before TYPE VERSION (bad digest + off-chain: counted); TYPE name before TYPE VERSION (`Invoice` v7: counted); TYPE VERSION before DL-101 (off-chain `0` row under `stricter/`: path text only, no constructor text). Chain before DL-101: `N20_chain_rows_build` |
| `N22_no_row_snapshot_blocks_a_reader`, `N22_control_put_only_…` | N22, PDB-23 | exact PDB-23 text; `put_only/` without `rows.jsonl` exits 0 with `def orders_save(` and empty stderr |
| `N23_line_form` (3 subtests) | N23 | not JSON, no `source "db"`, record version 2: each its text and `record source: <rows>:2 (line 2)` |
| `N24_partial_row_snapshot_blocks`, `N24_control_matching_meta_builds`, `N24_sample_builds` | N24, PDB-22, P5-19 | `row_count` 3 beside 2 rows: the PDB-22 text; `row_count` 2 builds; the sample builds with `2 rows, 2 checked` |
| `N24_sample_meta_form` (guard) | P5-19 | sample keys `table`, `database`, `query_time`, `row_count`, `row_ids`; ids sorted and equal to the rows' `row_id`; `row_count` = row lines; digests hold. Passes today (fixture check, not RED) |
| `N25_list_record_constructor_blocks`, `N25_save_record_constructor_blocks` | N25, PDB-17 | the RESPONSE RECORD constructor text for `orders.list` (item 0) and `orders.save` |
| `N25_control_rejected_record_is_counted` | N25 control, QV3-8 B, QV3-7 A | exit 0; stderr is the P2 pair `1 records, 0 checked, 1 rejected at capture` + `digest not verified (P2b)` (adjacent, in this order) and `rows: 0 rows, 0 checked, 0 not decodable` |
| `N26_no_stored_value_in_any_text` (6 subtests) | N26, DL-124 | constructor, literal, path, orphan, list record, count line: the anchor text stands and no stored String (5 chars or more), row id, trace id or span id written by the test is in stderr |
| `N27_events_hold_no_row_value` + every `compile()` | N27 (N14) | `.beaml/actions.jsonl` holds none of those words and not the `--stored` directory; the P4a and 6d checks run too |
| `N28_orphan_rows_of_a_removed_db_effect_block` | DL-040 parity (6d O3) | two `Note` rows of `notes.save` under `orders.beaml`: `error: stored ROW of operation notes.save has no effect in the source`, `record source: <rows>:2 (line 2)`, `stored ROWS of operation notes.save: 2`; help line not compared |
| `N28_control_row_of_a_removed_writer_with_a_reader_is_checked` | DL-137 | an `Order` row of `orders.import` (no such EFFECT) is checked: `1 rows, 1 checked` |
| `N28b_retire_line_frees_orphan_rows` | 6d S5b parity | `@unittest.skip`: the RETIRE LINE meaning for rows is M5 (D036) |
| `N30_literal_swap_on_a_row_blocks`, `N30b_map_migrate_step_frees_the_swap` | DL-140 | `@unittest.skip` with the reason (blocked, not red): no stored variant in a ROW CORE, no `map` form, fate slice P6 (D036). Skip, not `expectedFailure`: an expected failure would turn into "unexpected success" noise and says nothing about the block |
| `N10_constructor_record` (runtime, 2 cases) | P4a RED review M1 | a seeded row that fails the constructor: the `responses` record of `list_orders` and of `load` is `value null, outcome rejected, reason constructor` |
| `N31_note_chain_read_runtime` (runtime, 3 cases) | QDB-8 B | `list_notes` reads a `Note` v1 row with `tag ""`; `save_note` writes `{"Note", 2}` with the v2 `type`; `Order` and `Note` rows read side by side |

### Dependencies

| Needs | Tests |
|---|---|
| P4a GREEN (db KINDS, LIST TYPE, runtime) | every test but `N24_sample_meta_form` |
| P3/P5 (several EFFECTS, module `Orders`) | every `orders.beaml`-family case (three or more EFFECTS); not `put_only/` |
| P2 (v3 reader, count lines, QV3-8 B) | N23 version text, N25 (record version 3, RESPONSE checks), N25 control (count pair) |
| P4b GREEN (rows reader) | N17 to N24, N26 to N29 |
| P4a GREEN only (generated code) | N10_constructor_record, N31 |

- **[Inference]** `N10_constructor_record` and `N31` can turn green with P4a GREEN alone; they stand here because the P4a RED review asked for M1 in P4b and QDB-8 B had no runtime case.
- `slice6_entry_test.py` (imported for `setUp`, `compile`, `elixirc`) is under edit by a GREEN worker at this RED. A change of those helpers changes this file's harness.

### Decisions

**Repair**
→ Orphan rows: block when the `operation` names no EFFECT and no RETIRE LINE and `type.name` has no reader statt block on operation only (RESPONSE form), weil DL-137 says a row that `db.get` or `db.list` decodes is checked; a removed writer with a kept reader must not block. Owner review line. → By: Opus (RED db-stored, default, open) · Repair
→ The `N21` `Invoice` row keeps `operation "orders.save"` (a declared EFFECT), so it stays "counted" under the orphan rule statt a new operation, weil plan N21 says counted. → By: Opus (RED db-stored, default, open) · Repair
→ An off-chain TYPE VERSION blocks with the path text statt "counted, not decodable", weil N20 and the N20b controls (Fable) say exit 1; the plan line "Decodable row … TYPE VERSION is on the chain … every other row is counted" contradicts them. Owner review line. → By: Opus (RED db-stored, default, open) · Repair
→ The rows count line always prints (N17 with `0 not decodable`) statt QV3-7 A for rows, weil PDB-24 says "on success" and the N20b `3 checked` needs the line. The P2 RESPONSE pair keeps QV3-7 A. Owner review line. → By: Opus (RED db-stored, default, open) · Repair

**Undo**
→ DL-122 ROW text `has a value` (the built text with the plan substitution rule) statt the plan's `holds a value`. → By: Opus (RED db-stored, default, open) · Undo
→ Plurals as built: `2 stored ROWS … fail`, `stored ROWS of operation …: N`. → By: Opus (RED db-stored, default, open) · Undo
→ The rows line is not pinned to a place among the stderr lines; only the P2 pair is pinned adjacent. → By: Opus (RED db-stored) · Undo
→ Orphan help line not compared (M4 text, M5 retire for rows). → By: Opus (RED db-stored) · Undo
→ N26 word list: every String of 5 characters or more, every row id, trace id and span id written by the test; short values (`0`, `web`, `app`, `EUR`) are proven by the exact texts. → By: Opus (RED db-stored) · Undo
→ DL-140 and the RETIRE LINE free as `@unittest.skip` with the reason, not `expectedFailure`. → By: Opus (RED db-stored) · Undo
→ New test file statt extending `slice6_db_test.py`, weil the task forbids editing existing tests. → By: Opus (RED db-stored) · Undo
→ Sample database name `beaml_dev` in `snapshot-meta.json` (no secret, a dev name). → By: Opus (RED db-stored) · Undo

## P4c: row shape check

**[Proposal]** Solve/RED phase, 2026-11-08. By: Opus (RED P4c). Inputs: [review.md](review.md) O1 and O3; 0005 [owner review](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) section "Row shape check" (default A: block with the DL-102 text). Test file: `tests/slice6_db_stored_test.py` (four tests appended, N27 changed). Evidence: [red-output.md](red-output.md#p4c).
No new fixture file: every case builds its rows and records in a temp directory per test (`row()`, `db_record()`); N27 reads no shared fixture.

### Mapping

| Test | Plan item | Asserts |
|---|---|---|
| `N32_row_missing_string_field` | O1, default A, DL-102, DL-124 | `orders.beaml`, one `Order` row without the String field `order_id`, own digest: exit 1, stdout empty, `error: TYPE Order: 1 stored ROW of table records has no String value for field order_id`, `  record source: <rows>:1 (line 1)`, help line by `HELP_PREFIX` (DL-102), no stored number in the text |
| `N32b_row_wrong_type_string_field` | O1, default A | the same, with an Int in `order_id`: the same three lines (one text for both faults) |
| `N32_control_complete_row_builds` | O1 control | a complete row: exit 0, `rows: 1 rows, 1 checked, 0 not decodable` (passes today) |
| `N32c_response_record_shape_blocks` (2 subtests) | O1 second stream, owner-review "covers both streams" | the two faults as item 0 of an `orders.list` RESPONSE RECORD beside an empty `rows.jsonl`: `1 stored RESPONSE RECORD of operation orders.list has no String value for field order_id`, record source `<responses>:1 (line 1)`, help line. HEAD builds it, so this is RED, not a guard |
| `N32c_control_complete_list_record_builds` (RED repair, O1) | red-review P4c O1 | a complete `orders.list` RESPONSE RECORD with two complete items (WIRE1, WIRE2), empty `rows.jsonl`: exit 0, the module, stderr exactly `rows: 0 rows, 0 checked, 0 not decodable`. Guard: passes at HEAD and after a correct GREEN; a GREEN that checks the top-level `{"items": …}` instead of each item fails it |
| `row()` (RED repair, M2) | red-review P4c M2 | every row id is a String `row-<n>`; no test uses an Int `row_id` (N24 meta sorts the same, equal width) |
| `N27_events_hold_no_row_value` (changed) | O3 | the two rows of N27 carry String row ids (no digits run that a `ts` epoch float can hold); the event check in `compile()` is unchanged |

### GREEN notes

- The check runs in the DL-101 tail (after the MIGRATE CHAIN, PDB-15), over `String` fields of the ROW TYPE and of a RESPONSE RECORD value (also list items). A missing key and a non-String value give the same text.
- **[Inference]** A `rejected` row or record stays counted, not shape-checked (QV3-8 B, N21b).

### Decisions

**Repair**
→ One text "has no String value for field <f>" for missing and wrong-type statt two texts, weil both fail the same `db.list` decode and the text then holds no value hint. → By: Opus (RED P4c, default, open) · Repair
→ RESPONSE RECORD case as RED test statt a guard, weil HEAD builds it (observed, exit 0). → By: Opus (RED P4c) · Repair
→ RED repair: O3 now fixed in `row()` for all tests (M2), superseding the next line. → By: Opus (RED repair P4c) · Repair
→ O3 fixed in N27 only statt all `row()` ids, weil the task scopes N27 and appends only; every other test still writes 4-digit int ids into its `compile()` check (residual false-fail risk, see red-output P4c Limits). → By: Opus (RED P4c) · Repair

**Undo**
→ No new fixture files: rows are per-test temp files; N27 has no shared fixture. → By: Opus (RED P4c) · Undo
→ Plural form (`2 stored ROWS … have`) not tested. → By: Opus (RED P4c) · Undo
→ RESPONSE case over `orders.list` statt `orders.save`, weil the save record's `request` holds the same value and could block first on the input side. → By: Opus (RED P4c) · Undo
→ RED repair: control `N32c_control_complete_list_record_builds` over two items statt one, weil an item-0-only check stays visible in a later case. → By: Opus (RED repair P4c) · Undo
→ RED repair: control stderr checked as the rows count line only, weil no P2 line prints at 0 rejected (QV3-7 A). → By: Opus (RED repair P4c) · Undo
