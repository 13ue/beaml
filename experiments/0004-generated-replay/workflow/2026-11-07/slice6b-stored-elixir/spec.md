# Spec: slice 6b step 13, the `--stored` check runs the generated Elixir constructor (RED)

**[Proposal]** Solve / RED phase, 2026-11-07. Contract source: [plan.md](plan.md), with the section "Plan repair" where the two differ; [decisions.md](decisions.md) D6B-102 to D6B-111 and D6B-119 to D6B-126; DL-121, DL-122 and DL-124 in [the decision log](../../../../../wiki/planning/decision-log.md).
By: Opus (RED, slice6b-stored-elixir). No production file changes in this phase. Evidence: [red-output.log](red-output.log). Decisions: [notes.md](notes.md).

## Contract (summary of the plan)

1. The static pass runs first, in today's order, and adds the DL-122 lost-literal rule. A static error ends the check. Elixir does not start (D6B-105).
2. DL-122 as narrowed by DL-124: a stored String of a literal enum field that is not in `unknown_fields` and is no current ENUM LITERAL blocks. The text names the TYPE VERSION, the operation, the field, the enum, the count and the record lines. It never holds the stored String (D6B-124).
3. When the static pass is clean, one `elixir -e <DRIVER>` run calls `new_T_k` for each record and each constructor field whose first matching signature has a failure TYPE (D6B-102 to D6B-104, D6B-122).
4. An `error F` result gives the step 8 DL-102 block text, byte-equal.
5. No pass without Elixir: `elixir` not on PATH gives the D6B-106 text. A bad exit, a signal, a time limit (default 60 s, `BEAML_STORED_ELIXIR_LIMIT_S`) or wrong result lines give the run error (D6B-119, D6B-121). Exit 1.
6. No stored value in stderr, events or files (DL-032, D6B-106, D6B-123, D6B-124).
7. One event `stored-elixir` per Elixir run: `result` ok, blocked or error; Int `ms`; `calls` (D6B-107).

## Tests: `experiments/0004-generated-replay/tests/slice6_stored_elixir_test.py`

Fixtures: `experiments/0004-generated-replay/slice6/stored-elixir/` (D6B-110). Records are line 1 of `slice6/decode-ctor/stored.jsonl` with a new `amount`, `trace_id`, `client_span_id` and `value_sha256` (`stored_types_test.value_sha256`).

| Case | Test | Kind | Today (HEAD 5110e92f) |
|---|---|---|---|
| E1 | `test_e1_failure_in_a_pipe_step_blocks` | RED | FAIL: exit 0, empty stderr |
| E2 | `test_e2_failure_in_a_nested_constructor_blocks` | RED | FAIL: exit 0 |
| E3 | `test_e3_passing_records_build` | guard | ok |
| E3 event | `test_e3_passing_records_give_an_ok_event` | RED | FAIL: no `stored-elixir` event |
| E4 | `test_e4_no_elixir_on_path_blocks` (empty dir as PATH) | RED | FAIL: exit 0 |
| E5 | `test_e5_event_has_time_and_count_only` | RED | FAIL: no event |
| E6 | `test_e6_static_error_needs_no_elixir` (empty dir as PATH) | guard | ok |
| E7 | `test_e7_no_stored_value_in_output` | guard | ok |
| E8 | `test_e8_endless_constructor_hits_the_time_limit` (`BEAML_STORED_ELIXIR_LIMIT_S=2`) | RED | FAIL: exit 0 |
| E9 a | `test_e9a_check_follows_the_signature_order` | RED | FAIL: exit 0 |
| E9 b | `test_e9b_runtime_decode_follows_the_signature_order` | guard | ok |
| L1 | `test_l1_removed_literal_blocks` | RED | FAIL: exit 0 |
| L1b | `test_l1b_changed_literal_blocks` | RED | FAIL: exit 0 |
| L2 | `test_l2_current_literal_and_kept_value_build` | guard | ok |
| L3 | `test_l3_resolved_note_stays` | guard | ok |
| U1 | Rust unit test of `parse_elixir_results` in `main.rs` | RED | written by GREEN (notes.md "Left for GREEN") |

Run: `python3 -B experiments/0004-generated-replay/tests/slice6_stored_elixir_test.py` (set `BEAML_SPIKE` to a scratch binary for a self-check only).

## Acceptance (GREEN)

- All 15 tests of the new file pass; U1 exists and passes in `cargo test`.
- The deferred edit in [notes.md](notes.md) is applied; `slice6_decode_test.py` and `slice6_decode_ctor_test.py` pass unchanged otherwise.
- Every other `slice6_*_test.py` and the compile-level test files pass. `cargo fmt --check` and `cargo clippy --offline --all-targets -- -D warnings` are clean.
- No generated Elixir byte changes (plan "Byte changes").
