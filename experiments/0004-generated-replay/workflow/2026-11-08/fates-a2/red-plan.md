# RED plan: fates-a2a (record format draft 4)

**[Proposal]** RED phase, 2026-11-08, HEAD `6427262f` (P2b GREEN `372b2ee1`, TEST `6427262f` landed).
By: Opus (RED fates-a2a). Tests and fixture tooling only; no production file (`main.rs`, generated emit); no commit.
Inputs: [plan.md](plan.md) sections 2, 5 to 7 and "Repairs" (By: Fable), [plan-review.md](plan-review.md).
Scope: a2a only. a2b (fate lines at run time, R*, N9, N9b, QA2-2, QA2-3) is not in this RED.

## Files

| File | Change |
|---|---|
| `experiments/0004-generated-replay/tests/slice6_fates_test.py` | new class `FatesA2a` (V4a to V4i); docstring line; `import copy` |
| `experiments/0005-prototype-fullstack/app/test/prototype/stored_test.exs` | new test N16 (phase n8) |
| `experiments/0005-prototype-fullstack/run.py` | `EXPECTED` gains N16 |
| `workflow/2026-11-08/fates-a2/convert_v4.py` | new: the one-time fixture rewrite (GREEN runs it in place) |
| `workflow/2026-11-08/fates-a2/plan.md` | "Repairs" section (rulings By: Fable) |

The V4 records are built with `draft4(record, nested)` / `draft3(record)` in the test file, not through `sd.core()`.
So the cases hold before and after GREEN rewrites `sd.core()` and `type_of()` to draft 4.

## Tests

| ID | Test (subtests) | Expected after GREEN |
|---|---|---|
| V4a | `test_V4ab_records_are_draft4_with_nested` `V4a_row_core` | db.put ROW CORE: `{version, type.nested} == {4, {"amount": 1, "channel": 1}}` |
| V4b | same test: save, load, list, rejected save record; `ui.orders` ENTRY RECORD | `{4, nested}`; list record `{"items": {"version": 1, "nested": {...}}}` (O1); `OrderQuery` entry `{}` (QA2-1) |
| V4c | `test_V4c_nested_follows_the_mark` (amount_v2: row core + head, ui.place entry, list record, Note row; channel_v2: row core) | `amount` 2 under `type Amount v2`; `channel` 2 under `enum Channel v2`; head stays `{"Order", 1}`; Note `{}` |
| V4i | inside V4c (amount_v2) | guard: `value_sha256` is the digest of the value only (passes before and after) |
| V4d | `test_V4d_stored_reads_draft4_only` (ROW, RESPONSE RECORD, ENTRY RECORD at v3; two draft 4 controls) | `error: stored <KIND> has record version 3; this build reads record version 4 only (DL-168)` + record source; draft 4 builds |
| V4e | `test_V4e_v4_without_nested_is_malformed` (7 RESPONSE RECORD forms, 1 ROW) | `error: stored RESPONSE RECORD has a malformed TYPE VERSION` + record source; ROW: exit 0, `rows: 1 rows, 0 checked, 1 not decodable` |
| V4f | `test_V4f_undeclared_nested_version_blocks` (ROW, ENTRY RECORD exact; LIST item prefix; control nested 2) | SQUASH text of plan section 2 with `ROW` / `ENTRY RECORD`; control builds |
| V4f2 | `test_V4f2_a_newer_stored_version_blocks` | NEWER text (RA-04) + record source; no `migrate Channel` in stderr |
| V4g | `test_V4g_fate_skips_values_at_the_new_version` (ROW, LIST item, ENTRY at `amount` 2; three v1 controls; map v2 `"app"`; map v1 control) | v2 values block with the DL-102 constructor block and `help_q(Amount, 2)`; v1 values keep the a1 fate line and stop line; a v2 `"app"` is a lost literal |
| V4h | `test_V4h_swap_reads_the_stored_version_table` (channel_swap: v2 `"web"`; v1 control) | v2 `"web"` builds `rows: 1 rows, 1 checked, 0 not decodable`; v1 `"web"` keeps the W1 moved block |
| N16 | 0005 `stored_test.exs` "N16 a live row carries type.nested (DL-168)" | live row core and ROW SNAPSHOT line `{4, {"amount": 1, "channel": 1}}`; build exit 0, `rows: 1 rows, 1 checked, 0 not decodable` |

## RED decisions

### Undo
→ RA-01: `FatesA2a` is its own TestCase with copied helpers, not a `Fates` subclass (no double run of 37 tests). By: Opus (RED fates-a2a)
→ RA-03: N16 in phase n8 (`stored_test.exs`), not after `n7_seed`; any live row shows the format. By: Opus (RED fates-a2a)
→ RA-05: `convert_v4.py` written in RED with `--check`; dry run: 26 files, 53 records, digest asserts pass. By: Opus (RED fates-a2a)
→ RA-06: the converter gives every non-String direct field 1 and stops on a LIST field (none in the 26 fixtures), not a source parse. By: Opus (RED fates-a2a)

### Repair
→ RA-02: V4h in the one-step form (channel_swap, stored v2 `"web"`) statt the two-step chain, weil HEAD rejects every two-step enum chain (probe below). Commits us to: GF-02 for two steps goes to fates-b. By: Opus (RED fates-a2a)
→ RA-04: V4f2 text `error: stored ROW holds Channel v2 in field channel; the source declares no Channel v2. The source is older than the stored values; build from a source that declares Channel v2 (DL-155)` statt a SQUASH help, weil review O3 forbids "keep ... and migrate" for a newer value. Commits us to: GREEN prints this text exactly. By: Opus (RED fates-a2a)
→ RA-07: V4e pins the ROW form as "not decodable" (exit 0) statt a block, weil `stored_version` failures of ROWS are counted, not raised, today (N21). Commits us to: a ROW with a hand-deleted `nested` builds. By: Opus (RED fates-a2a)
→ RA-08: V4e treats a missing entry for a non-String field as malformed statt reading it as v1, weil review O1 says no reader guesses. An extra key is not pinned. By: Opus (RED fates-a2a)
→ RA-09: V4f pins the LIST item form by prefix only (`error: stored RESPONSE RECORD holds Channel v1 in field `), weil the field path of an item (`channel` or `items.channel`) is a GREEN text choice. By: Opus (RED fates-a2a)

### Two-step enum chain probe (V4h, plan section 2)
HEAD binary, channel_swap plus `enum Channel v3` and `migrate Channel v2 -> v3 { map "tablet" -> Mobile }`:
- with `quarantine "fax"` in v1 -> v2: `migrate Channel v1 -> v2: a fate line stands only in the last MIGRATE STEP of Channel (v3)`
- with `migrate Channel v1 -> v2 { }`: `... a MIGRATE STEP needs at least one rename, add, drop or fate line`
- without the v1 -> v2 step: `error: enum Channel v1 has no MIGRATE STEP to v2; ... (DL-155)`
An enum step holds fate lines only (ENUM_STEP_ONLY), so no two-step enum chain can be written. [Verified, exit 1 each]

## Fixture rewrite plan (GREEN)

1. Run `python3 -B experiments/0004-generated-replay/workflow/2026-11-08/fates-a2/convert_v4.py` once, in place (26 files).
2. `tests/slice6_db_test.py`: `core()` writes `version: 4`; `type_of()` adds `nested` (non-String direct field 1;
   `LIST_TYPE` `{"items": {"version": 1, "nested": {"amount": 1, "channel": 1}}}`; String-only TYPES `{}`).
   The `BeamlDb.seed(type, version, value)` stub takes the TYPE VERSION, not the record version: no change [Inference].
3. Inline v3 texts and asserts (observed by `rg` at HEAD):
   `stored_types_test.py:93` (`version=3`), `redteam_c1_test.py:38`, `arms_test.py:373`, `slice6_entry_test.py:243`,
   `slice6_record_test.py:80,109` (`P1_version_is_3`), `slice6_record_test.py:123` (text), `record_v3_test.py:66`
   (text), `record_v3_test.py:107,141` (`V1_version_is_3`, `V11_entry_version_is_3`), `slice6_db_stored_test.py:343`
   (text "version 4 only (DL-168)").
4. `tests/slice6_fates_test.py` (a1 cases): `PLACE_TYPE`, `ORDER_V3`, `TIP_ORDER` get nested through `type_of()`.
   S3 "type mark without a step" and "enum mark without a step" gain the SQUASH line (no v1 declared); GREEN records
   the new expected text. F8 is compile-only and keeps.
5. 0005: `app/test/support/prototype.ex` ~104 `{3, "accepted"}` → `{4, "accepted"}`; `run.py run` regenerates
   `app/lib/generated/orders.ex`.

## Expected pin moves

| Site | Kind | When | a2a |
|---|---|---|---|
| `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS` (+ `slice6_struct_order_test.py`) | digest | GREEN | moves (every EFFECT writer) |
| `tests/slice6_host_struct_test.py` `BYTE_GUARD` | digest | GREEN | moves |
| `slice6/effect-reach/byte-guard.json` (keep the (71, 40) invariant) | digest | GREEN | moves |
| `tests/slice5_syntax_test.py` `PIN` | hash | commit after GREEN | moves |
| `tests/slice6_entry_test.py` `BASE` | hash | commit after GREEN | moves |
| `tests/slice6_multi_test.py` `BASE` | hash | commit after GREEN | moves |
| `tests/slice6_db_test.py` `P4_BASE` | hash | commit after GREEN | moves |
| `tests/record_v3_test.py` V17 (`version == 3` → 4) and V17b (compose `convert_v4.convert_text` over `convert_v3`) | format pin | GREEN | moves |
| `tests/record_v3_test.py` V18b (`version == 3` assert → 4; stderr pairs keep) | format pin | GREEN | moves |
| `tests/record_v3_test.py` V18 | diff proof | — | **checked: no move.** `@unittest.skip` at HEAD since the multi-effect GREEN `ce190054` (skip reason: the per-step byte guards carry the proof). `ALLOWED` and `P2_BASE` stay. [Verified, `record_v3_test.py` 371-374] |
