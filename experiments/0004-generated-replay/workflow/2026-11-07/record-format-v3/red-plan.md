# RED plan: RECORD FORMAT v3 (EXPERIMENT 0005 prerequisite P2)

**[Proposal]** Solve/RED phase, 2026-11-07. New files only: [`tests/record_v3_test.py`](../../../../tests/record_v3_test.py), fixtures under [`slice6/record-v3/`](../../../../slice6/record-v3/), the converter [convert_v3.py](convert_v3.py). No production file, no existing test, no existing fixture changed. Evidence: [red-output.md](red-output.md).
Plan: [plan.md](plan.md) with "Plan repair"; re-check notes N1 to N3 in [plan-review.md](plan-review.md#re-check-after-plan-repair).
By: Opus (RED record-v3) for every mapping and decision in this file.

## P2 base

- `P2_BASE = "31d83754"` (HEAD at RED). V18, V18b and V24 build it with `s5.compiler_at` (`git archive`).
- **[Observed]** At RED the working copy also holds uncommitted edits of another worker in `main.rs` (+24 lines) and `tests/slice6_entry_test.py` (+18 lines). RED uses the HEAD build only (`BEAML_SPIKE`).

## V-test → test → plan item

| V | Test (case) | Plan item |
|---|---|---|
| V1 | `test_V1_to_V10_response_record` [`V1_version_is_3`] | Change 1, `version: 3` |
| V2 | [`V2_key_set_is_the_core_and_the_http_extras`], `test_V2_V9_keep_value_source` [`V2_key_set_with_a_keep_value_variant`], `test_V11_entry_record` [`V2_response_of_the_flow_key_set`] | 14-key core + `request`, `status` (QV3-1 to QV3-3, RV3-03) |
| V3 | [`V3_span_id_only`], [`V11_entry_span_id_only`] | QV3-2 A |
| V4 | [`V4_accepted`], [`V4_accepted_through_the_constructor`], [`V4_response_of_the_flow_accepted`] | QV3-4 A row 4 |
| V5 | [`V5_status`], [`V5_status_wins_over_decode`] | QV3-4 A row 1 (status first) |
| V6 | [`V6_decode`], [`V6_not_json_is_decode`] | QV3-4 A row 2 |
| V7 | `test_V4_V7_V8_constructor_outcome` [`V7_constructor`] | QV3-4 A row 3 |
| V8 | [`V8_decode_reason_is_the_live_reason`], [`V8_constructor_reason_is_the_live_reason`], `test_V8_guard_live_status_reason` (guard) | record `reason` = live `reason` |
| V9 | [`V9_unknown_fields_always`], [`V9_guard_kept_value_names_the_field`] (guard) | RV3-03 |
| V10 | [`V10_guard_*`] (5 guards) | QV3-6 A, RV3-04, D6B-57 |
| V11 | `test_V11_entry_record` [`V11_entry_version_is_3`, `V11_entry_key_set_is_the_core`, `V11_entry_span_id_only`, `V11_guard_entry_outcome`] | Change 2 |
| V12 | `test_V12_response_record_version_2_blocks`, `_version_1_`, `_without_version_` | Change 3, RV3-11 |
| V13 | `test_V13_entry_record_version_2_blocks` | Change 4, RV3-06 |
| V14 | `test_V14_count_lines` | QV3-7 (O3 text), QV3-8 B |
| V14b | `test_V14b_control_an_accepted_record_still_blocks` | control, `blocked()` filter of both lines |
| V14c (new) | `test_V14c_response_count_lines_before_the_entry_count_line` | Change 5 (output order) |
| V15 | `test_V15_no_count_lines_when_nothing_is_rejected` | QV3-7 A (M = 0) |
| V16 | `test_V16_no_stored_value_in_stderr` (5 subtests: V14, V14b, V22, V23, V25) | DL-124 |
| V17 | `test_V17_tracked_fixtures_are_v3`, `test_V17b_tracked_fixtures_equal_the_converter_output` | QV3-5 A, RV3-08, RV3-12 |
| V18 | `test_V18_only_the_two_writers_change` | diff proof, allowed hunks `Replay.record/3`, `Replay.entry_record/2` |
| V18b (N3) | `test_V18b_converted_fixtures_keep_exit_and_stderr` | "every stderr over a converted fixture" |
| V19 | `compile()` of every test (6d N12 check: no path, no source text, no stored value in events) | V19 |
| V20 | none in RED | TEST phase: `run.py drift` rows = `DRIFT_PIN`; `drift_test.py` with line 198 `!= 3` |
| V21 | none in RED; V24 and V25 assert the unchanged path and D6B-72 texts | TEST phase: existing block text tests |
| V22 | `test_V22_status_record_without_a_path_builds` | QV3-8 B, 503 |
| V23 | `test_V23_rejected_200_record_without_a_path_builds` | QV3-8 B, 200 rejected at capture |
| V24 | `test_V24_control_accepted_record_without_a_path_blocks` | control: the path check still runs |
| V25 | `test_V25_held_check_reads_a_rejected_record` | control: the held check reads rejected records |
| N2 | `test_N2_w2_skips_a_rejected_record`, `test_N2b_control_an_accepted_record_keeps_the_migrate_step` | QV3-8 B, W2 count |

- **Five pin sites:** named in the module docstring of `record_v3_test.py`, with the move time of each (RV3-14).
- **N1 (medium):** no test. A docs item: with QV3-7 A, a file with M = 0 never shows `digest not verified (P2b)`.
- **N3:** V18b names it. The P2 base compiler reads the v2 original (`git show P2_BASE:<file>`, written to a scratch dir, an empty `responses.jsonl` beside `entries.jsonl`). The P2 compiler reads the tracked v3 file. Paths are mapped before the compare.

## Fixtures (`slice6/record-v3/`)

| File | Records | Used by |
|---|---|---|
| `stored-mixed.jsonl` | decode-ctor: 1 accepted (passes `Amount`), 2 rejected/status (503), 3 rejected/constructor; 2 and 3 fail `Amount` | V14, V16 |
| `stored-mixed-fail.jsonl` | the same, line 1 fails `Amount` | V14b, V16 |
| `stored-503-nopath.jsonl` | rejected/status, `Payment v1 {order_id}` (no path in decode-ctor) | V22, V16 |
| `stored-200-rejected-nopath.jsonl` | rejected/constructor, status 200, same TYPE VERSION | V23, V16 |
| `stored-accepted-nopath.jsonl` | accepted twin | V24 |
| `stored-held-rejected.jsonl` | `stored-request-unredacted` as 503 rejected/status | V25, V16 |
| `stored-w2-rejected.jsonl`, `stored-w2-accepted.jsonl` | `stored/v1.jsonl` record as 503 rejected, and as converted | N2, N2b |
| `entry-v2/` | empty `responses.jsonl`, `entries.jsonl` with one version 2 line | V13 |
| `order/` | one rejected RESPONSE RECORD, the 5 converted ENTRY RECORDS | V14c |

- Every v3 record was written with `convert_v3.convert` and then given its status, outcome and digest (`st.value_sha256`).

## Steps for GREEN (from the plan, not built here)

- Run `convert_v3.py` once in place from the repository root; then V17 and V17b pass. `git diff --stat` must name only the 15 files (GREEN check).
- Change the listed existing assertions (plan table "Existing assertions that change").
- Move pin sites 2 to 4 in GREEN; sites 1 and 5 in the commit after GREEN.

## Decisions

**Repair**
→ V14 on the decode-ctor source as is statt a stricter `Amount` source, weil its rule already rejects currency "". → By: Opus (RED record-v3)
→ V22/V23 stdout = P2 build over `empty.jsonl` statt pre-P2 build, weil P2 changes `record/3` bytes (plan text slip). → By: Opus (RED record-v3)
→ V18 asserts "both writers changed" statt hunk list only, weil a hunk list alone passes with no change. → By: Opus (RED record-v3)
→ V18 sources = N13 globs + `arms/` + `byte-guard.json` keys, incl. ENTRY sources, statt N13 only, weil `entry_record/2` lives there. → By: Opus (RED record-v3)
→ V16, V18b with marker or v3 precondition statt plain scan, weil today's version error would pass. → By: Opus (RED record-v3)
→ V17b converter output = tracked file statt a `git diff --stat` test, weil the stat is a commit check. → By: Opus (RED record-v3)
→ V8 status reason as a static guard statt a 503 TCP stub, weil the stub has one fixed 200 reply. → By: Opus (RED record-v3)
→ V14c added for the Change 5 order statt untested, weil no V test covered it. → By: Opus (RED record-v3)
→ N2 on `slice2/N-chain` with a v1 record statt a new source, weil it has `migrate Payment v1 -> v2`. → By: Opus (RED record-v3)
→ `P2_BASE = 31d83754` (HEAD at RED) (default, open): if the uncommitted `main.rs` edits of another worker land first, GREEN sets `P2_BASE` to that commit. → By: Opus (RED record-v3)

**Undo**
→ `rec-loop.jsonl` out of V18b (time-limit source); still in V17, V17b. → By: Opus (RED record-v3)
→ Raw unittest log not kept in the ledger (it holds stored values); summary only. → By: Opus (RED record-v3)
→ Guards named `guard` in the case or test name. → By: Opus (RED record-v3)
