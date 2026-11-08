# RED plan: fates-a1 (syntax, checks, `--stored`)

**[Proposal]** RED phase of step a1, 2026-11-08. By: Opus (RED fates-a1). Plan: [plan.md](plan.md) with "Plan repair
after plan check"; rulings and RED decisions RF-01 to RF-12: [decisions.md](decisions.md). Run evidence:
[red-output.md](red-output.md). No production file changed; `main.rs` in the working tree is untouched.

Test file: `experiments/0004-generated-replay/tests/slice6_fates_test.py` (not in `run.py`, DL-147; the GREEN commit adds
step `slice6-fates`). Fixtures: `experiments/0004-generated-replay/slice6/db/fates/` (six db sources, N13 filter, `//`
comments). Wrong forms are inline swaps of these fixtures.

## Fixtures

| Fixture | Form | Used by |
|---|---|---|
| `stricter_v1/` | 0005 `stricter` as today: no mark, no step (fmt-checked) | S1b, S3, S3b, S4, S5; a3 copies it to `variants/stricter_v1/` |
| `amount_v2/` | `type Amount v2` + `migrate Amount v1 -> v2 { quarantine value }` (form A) | F1, F4, F5, F7, F7b, S1 to S1d, S1f, S3, S3b, S4; a3 form of `variants/stricter/` |
| `two_ctor/` | `amount_v2` plus a stricter `Tip` without a fate line | S1e |
| `channel_v1/` | `App` leaves Channel, `Mobile` is new; no mark, no step (fmt-checked) | S2b, S3b, S4 |
| `channel_v2/` | `enum Channel v2` + `migrate Channel v1 -> v2 { map "app" -> Mobile }` | F2, F5, F7, F8, S2, S2c, S3, S3b, S4; a3 form of `variants/channel_v2/` |
| `order_map/` | `type Order v3`, `migrate Order v2 -> v3 { map channel "app" -> Mobile }` | F3, F4, F5, F6, F7, S2 |

## Test → proof

| Test | Proves | Expected (exact unless noted) |
|---|---|---|
| F1 `test_F1_quarantine_line_builds` | form A parses and builds | exit 0, module `Orders` |
| F2 `test_F2_enum_version_and_bare_map_build` | `enum E vN` and a bare `map` build; two map lines on two literals are valid (RF-04) | exit 0, module `Orders` |
| F3 `test_F3_qualified_map_builds` | `map channel "app" -> Mobile` in the last owner step builds | exit 0 |
| F4 `test_F4_fate_only_step_is_valid` | PF-05: a fate-only step is valid; the empty-step text names fate lines | builds; `… needs at least one rename, add, drop or fate line` |
| F5 `test_F5_rejects` (20 subTests) | one compile error per wrong form (PF-06, PF-08, PF-11, PF-23, repair 9, RF-02 to RF-07) | exit 1, empty stdout, the exact text; the payload case: parse error `a map target takes no payload (QF-6 A) at byte N` |
| F6 `test_F6_redact_and_retire_parse_and_wait` | PF-09: both parse; the checker says the meaning waits | exact PF-09 texts |
| F7 `test_F7_no_dead_line_for_a_fate_step` | ruling on O1: a fate step is never a DEAD LINE | setup: a `drop` step on nested `Amount` is a DEAD LINE; `amount_v2`, `channel_v2` give exactly `rows: 1 rows, 1 checked, 0 not decodable`; no DEAD LINE on `migrate Order v2 -> v3` |
| F7b `test_F7b_remove_dead_keeps_a_fate_step` | `--remove-dead --assume-complete` keeps the fate step | setup: the `drop` step is removed; the quarantine source is byte-equal after the run, exit 0 |
| F8 `test_F8_enum_mark_disagrees_with_its_chain` | the TYPE mark rule applies to enums (`enum` in the text) | `enum Channel v3` with only `v1 -> v2`: the mark-chain text |
| S1 `test_S1_quarantine_lifts_the_constructor_block_over_rows` | DL-102 lifted over rows; `fate:` count; a1 stop line (ruling on O2) | `fate: 1 stored ROW of table records quarantined by migrate Amount v1 -> v2 (quarantine value)`, `NOT_BUILT_Q`; exit 1; the rows line, if printed, is `2 rows, 2 checked` and after the fate line |
| S1b `test_S1b_control_without_the_line_blocks_with_the_version_help` (4 subTests) | the block holds without the line, with the DL-155 help in rows, RESPONSE RECORDS, ENTRY RECORDS; PF-21 picks `value` or `currency` | DL-102 lines + `help: declare the next TYPE VERSION and a fate (DL-155): type Amount v2 and migrate Amount v1 -> v2 { quarantine value }` (`currency` for the `_, ""` clause) |
| S1c `test_S1c_quarantine_over_response_records` | PF-12, PF-17: a list RESPONSE RECORD is counted once | `fate: 1 stored RESPONSE RECORD of operation orders.list …`, `NOT_BUILT_Q` |
| S1d `test_S1d_quarantine_over_entry_records` | PF-12: ENTRY RECORDS of `ui.place` | `fate: 1 stored ENTRY RECORD of operation ui.place …`, `NOT_BUILT_Q` |
| S1e `test_S1e_line_lifts_only_its_type` | a line frees only its own TYPE | the `Tip` block (line 2, help `type Tip v2 … { quarantine value }`) stands; no line names `constructor of Amount` |
| S1f `test_S1f_a_quarantined_value_with_a_lost_literal_still_blocks` | repair 9: a row failing both the Amount rule and a literal | the DL-122 block with the enum help stands (contiguous); exit 1 |
| S2 `test_S2_map_lifts_the_lost_literal_block` (2 subTests) | DL-122 lifted by the bare and the qualified form | `fate: 1 stored ROW … mapped by migrate Channel v1 -> v2 (map "app" -> Mobile)` / `… migrate Order v2 -> v3 (map channel "app" -> Mobile)`, `NOT_BUILT_M` |
| S2b `test_S2b_control_without_map_blocks_with_the_version_help` (2 subTests) | DL-122 holds, help names the enum version form, no stored String | DL-122 lines + `help: … enum Channel v2 and migrate Channel v1 -> v2 { map "<old literal>" -> <Variant> }`; `"app"` absent |
| S2c `test_S2c_kept_value_is_neither_mapped_nor_blocked` (2 subTests) | DL-142: a kept value is not counted as mapped | a kept and a lost row: count 1; a kept row alone: exit 0, the rows line only |
| S3 `test_S3_gate_affected_values_need_the_next_version` (3 subTests) | DL-155 gate: affected values without the next version and a fate line block; the help names the next version after the newest mark (RF-08) | no mark: `type Amount v2 …`; `type Amount v2` alone: `type Amount v3 and migrate Amount v2 -> v3`; `enum Channel v2` alone: `enum Channel v3 and migrate Channel v2 -> v3` |
| S3b `test_S3b_gate_without_affected_values_is_free` (4 subTests) | DL-155: no affected value, no block, also with fate lines that no value hits | exit 0, exactly the rows line |
| S4 `test_S4_no_stored_value_in_any_text` (6 subTests) | DL-124: fate lines, helps and stop lines hold no stored String (5+ chars), row id or trace id | anchor present, no stored word |
| S5 `test_S5_help_where_no_fate_line_lifts_the_block` (3 subTests) | repair 5: the help where fates-a has no exit (RF-09) | ENUM CONSTRUCTOR no signature: `no fate line covers an ENUM CONSTRUCTOR yet (D041 open) …`; constructor TYPE no signature: `… a decode fault …`; guard: "no variant" keeps the DL-102 help |

Events: every compile goes through the `slice6_db_stored_test` harness, which asserts that `.beaml/actions.jsonl` holds no
source path, no source text, no stored word and no row or trace id (N12, N14, N27).

## Depth probe

A scratch copy of `main.rs` (`git archive` of `396405aa`) whose parser accepts `quarantine`, `redact`, `retire … keep N
days`, `map [field] "old" -> V` and `enum E vN`, drops them, lets a fate-only step pass K8 and skips the chain check of an
enum. No check, no lift, no help change ([red-probe.diff](red-probe.diff)). Required: S1b, S2b, S2c, F5 and the gate tests
fail on it. Result: [red-output.md](red-output.md), "Depth probe".

## Retired or moved by a1 GREEN (not by this RED)

- Help constants: `slice6_db_stored_test.py` `HELP_PREFIX`, `LITERAL_HELP` (and `slice6_m4_test` by import),
  `slice6_entry_test.py` `CTOR_BLOCK`, `LITERAL_BLOCK`, `slice6_stored_elixir_test.py`, `slice6_decode_test.py`,
  `slice6_db_test.py`, `slice6_decode_ctor_test.py` `HELP_MIGRATE`: they pin today's DL-102 and DL-122 help lines.
- `record_v3_test.py` V18b (`P2_BASE`): four pairs change their help line (plan repair section).
- `slice6_m4_test.py` `rename_text` stays (QM4-4 open).
- `redteam_c3_test.py` C4 fails while `slice6_fates_test.py` has no `run.py` step; the GREEN commit adds the step
  (DL-147, as for M4).

## Not in a1 (a2, a3, a4)

R1 to R8 (run-time decode, REPLAY RUN, `db.get`, R1b, R1c, R5b, R8), N9 and N9b, T1, T2, T2b, G1. a2 RED changes S1,
S1c, S1d, S2 and the S2c pair to exit 0 and removes `NOT_BUILT_Q` and `NOT_BUILT_M`.
