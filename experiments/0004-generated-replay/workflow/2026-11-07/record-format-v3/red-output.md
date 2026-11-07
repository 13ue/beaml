# RED output: RECORD FORMAT v3 (EXPERIMENT 0005 prerequisite P2)

**[Observed]** 2026-11-07, Solve/RED phase. Mapping: [red-plan.md](red-plan.md).
By: Opus (RED record-v3).

## Run

```
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>/head
cargo build --offline --quiet --manifest-path <scratch>/head/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/head/target
BEAML_SPIKE=<scratch>/head/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/record_v3_test.py
```

- HEAD and P2_BASE: `31d83754ec22d714fedbb422d078d63d351caf3f`. Python 3.13.12, Elixir 1.18.1 (OTP 27), cargo 1.94.0.
- sha256: `record_v3_test.py` `b533cc6e…`, `convert_v3.py` `1eb79e31…`.
- Result: `Ran 24 tests`, `FAILED (failures=139)` (subtest failures), 0 errors, exit 1. One test passes: `test_V8_guard_live_status_reason` (guard).
- The raw log stays in the scratch directory: it holds stored values (DL-124 rule for notes).

## Failures by test (count, reason)

| Test | Fails | Reason today (HEAD) |
|---|---|---|
| `test_V1_to_V10_response_record` | 10 of 14 cases | `version` 2; no `outcome`, `reason`, `span_id`; `unknown_fields` absent; record `reason` nil vs live `decode`. The 4 `V10_guard_*` cases pass |
| `test_V4_V7_V8_constructor_outcome` | 3 of 4 | no `outcome`/`reason`; `V10_guard_digest_constructor` passes |
| `test_V2_V9_keep_value_source` | 1 of 2 | key set lacks `span_id`, `outcome`, `reason`; `V9_guard_kept_value_names_the_field` passes |
| `test_V11_entry_record` | 5 of 6 | ENTRY RECORD `version` 2 and `server_span_id`; RESPONSE RECORD of the flow has v2 keys; `V11_guard_entry_outcome` passes |
| `test_V12_*` (3) | 3 | v2 file builds (exit 0); v1 and none give the `version 2 only (DL-105)` text |
| `test_V13_entry_record_version_2_blocks` | 1 | no ENTRY version check: exit 0 |
| `test_V14_count_lines`, `V14b`, `V14c` | 3 | the v3 fixtures hit the version error (exit 1) |
| `test_V15_no_count_lines_when_nothing_is_rejected` | 1 | tracked `stored/v1.jsonl` is not v3 |
| `test_V16_no_stored_value_in_stderr` | 5 | the planned text (count line, block, D6B-72) is missing; no stored word was found |
| `test_V17_tracked_fixtures_are_v3` | 15 | every tracked fixture is version 2 with v2 keys |
| `test_V17b_tracked_fixtures_equal_the_converter_output` | 15 | tracked files are not the converter output |
| `test_V18_only_the_two_writers_change` | 56 | no hunk in `record/3` (and `entry_record/2` for the ENTRY source); 0 hunks outside the writers; 0 exit or stderr differences |
| `test_V18b_converted_fixtures_keep_exit_and_stderr` | 15 | fixture not converted (precondition) |
| `test_V22_*`, `test_V23_*` | 2 | version error, exit 1 |
| `test_V24_control_accepted_record_without_a_path_blocks` | 1 | version error instead of the path text; setup passed: the base compiler over the v2 twin gives the TYPE path block |
| `test_V25_held_check_reads_a_rejected_record` | 1 | version error instead of the D6B-72 text |
| `test_N2_w2_skips_a_rejected_record`, `test_N2b_*` | 2 | version error, exit 1 |

## Checked

- **[Observed]** Every runtime harness built and ran (PASS lines present). So no failure comes from setup or a typo.
- **[Observed]** Each failure names the missing v3 feature: the record keys, the v3 version reader, the outcome skip or the conversion.
- **[Observed]** The converter ran into a scratch directory twice: from `git show 31d83754` and from the working tree. Both outputs are equal. Each RESPONSE file has the 16 keys, `entries.jsonl` has the 14 core keys, and every digest assert passed. The tracked files did not change.
- **[Inference]** Guards that pass today must stay green after GREEN: `V8_guard`, `V9_guard`, `V10_guard_*` (5), `V11_guard_entry_outcome`.
- **[Unknown]** GREEN alone proves that V18 allows only the two writers and V18b keeps the stderr. RED can show only that both fail today because nothing changed.
