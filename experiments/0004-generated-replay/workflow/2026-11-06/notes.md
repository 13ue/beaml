---
id: experiment-0004-slice-1-notes
kind: ledger
status: red-recorded
updated: 2026-11-06
---

# Notes: EXPERIMENT 0004, slice 1

## Proposals

**[Verified]** No `proposal-ultra.md` and no `proposal-lite.md` exist in this ledger. The RED worker used [plan.md](plan.md), the [README](../../README.md) (revision 4) and the dispositions in [plan-review.md](plan-review.md). The RED worker chose no proposal and rejected no complexity.

## Owner decision change (2026-11-06)

**[Requirement]** The main agent sent this owner decision of 2026-11-06 during RED. It replaces the strict decode default of the same day (commit `49aedb9`, README "Owner decisions").

- An unknown key (example `fraud_score`) is accepted when every declared field is present with its TYPE.
- The result is the normal success: Orders replies HTTP 200, `finish` runs once.
- The unknown key names are a hint: field `unknown_keys` in the RESPONSE RECORD and an attribute on the EFFECT span.
- A missing or wrongly typed declared field stays `PaymentError{reason: "decode"}`. R1 does not change.
- The body bytes in the RESPONSE RECORD stay byte-exact.
- A replay of the L1 record gives the same success and the same hint (added replay case).

**[Verified]** Changes in the RED tests: L1 now expects HTTP 200, one `orders.finish` span, `unknown_keys == ["fraud_score"]` in the record and on the client span. R2 now replays the L1 record and expects success with the hint. R3 is new (wrongly typed field). R1, L2 and P1 do not change.

**[Unknown]** README case (d2) text (L1 reject, R2 "same result as R1") and the decision row "Typed decode rejects an extra key" are now stale. The RED worker did not edit the README. A plan worker must update them.

## RED

**Scope.** Tests and fixtures only. No compiler change, no generated output, no router change, no LIB arm. Stub: `experiments/0004-generated-replay/run.py` exits 2 with `not_implemented`. It exists only so that `drift_test.py` fails on behavior, not on a missing file.

**Runs.** Serial, loopback only, each command once. Raw output: [red-output.log](red-output.log). Retained results: `experiments/0004-generated-replay/results/20261106T114911001663Z` (counted run of GROUP 3) and `results/20261106T114845593236Z` (setup error, not counted).

### GROUP 1: compiler, cases (a) and (b)

Command: `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml --test cli`. Result: 8 failed, 3 passed (exit 101).

| Test | Expected → actual | Reason |
| --- | --- | --- |
| `orders_cli_accepts_effect_pipe_place` | exit 0 and `def place(` → exit 1, `unsupported token at byte 215` | The lexer has no `.` in names (`payments.authorize`). No `effect`, `!`, `\|>` |
| `orders_cli_rejects_unknown_pipe_step` | message names `charge` → `unsupported token at byte 215` | Same lexer stop; no pipe check |
| `orders_cli_rejects_pipe_type_mismatch` | message names `finish`, `Order`, `Payment` → same lexer message | No pipe TYPE check |
| `orders_cli_rejects_undeclared_pipe_failure` | message names `payments.authorize`, `PaymentError` → same lexer message | No `!` list check |
| `orders_cli_rejects_field_not_in_type` | message names `amount` → same lexer message | The source does not parse, so the field check is not reached |
| `orders_cli_rejects_unsupported_effect_kind` | message names `db.get` → same lexer message | No EFFECT kind check |
| `orders_cli_emits_flow_effect_decode_and_replay` | exit 0 and the slice 1 module → exit 1 | No emit of `place/1`, `payments_authorize/1`, decode, `PaymentError`, `Replay.record/3`, `Replay.run/3` |
| `orders_cli_template_control_drift_r_decode_names_reference` | both sources compile → exit 1 on the base source | No emit; the DRIFT-R control is not reached |
| `payments_cli_emits_checked_authorize_reference` | pass → pass | Guard (0003 gate 1), not RED |
| `invalid_source_emits_no_code_and_actions_do_not_capture_source` | pass → pass | Existing 0001 test, not RED |
| `payments_cli_output_stays_byte_identical` | pass → pass | Guard, not RED: snapshot of the HEAD compiler output |

**[Inference]** The plan predicted `expected interface, enum, or fn`. The actual stop is one stage earlier, in the lexer (`.` at byte 215 of the `effect` line). Both are missing behavior. The negative tests assert the named tokens, so the shared lexer message cannot pass them.

### GROUP 2: overlay diff, case (c) first check

Command: `python3 -B experiments/0004-generated-replay/tests/overlay_diff_test.py`. Result: 2 failed, 1 passed (exit 1).

| Test | Expected → actual | Reason |
| --- | --- | --- |
| `test_overlay_copies_equal_change_table_gen` | copies diff equals the table → `assertion-changes.json` and 6 copies missing | GEN overlay copies do not exist (plan: "RED while the copies are missing") |
| `test_overlay_copies_equal_change_table_lib` | same → same, LIB | LIB overlay copies do not exist |
| `test_table_rows_name_original_lines` | pass → pass | Guard: every README table line number points at the stated original text |

**[Verified]** Self-check in the scratch directory, not in the repository: a correct GEN copy set passes; one extra changed line (`query.py` line 17) fails.

### GROUP 3: arms harness, cases (b), (c), (d), (d2), (e)

Command: `python3 -B experiments/0004-generated-replay/tests/arms_test.py`. Run 1 had a setup error (TypeError, `Path % tuple` precedence in the harness). The harness was repaired; run 1 is not counted. Run 2: 14 failed, 1 passed (exit 1).

| Test | Expected → actual | Reason |
| --- | --- | --- |
| `test_b_gen_module_compiles_with_warnings_as_errors` | strict compile passes → `gen-generate-orders: compiler exit 1: unsupported token at byte 215` | No generated module |
| `test_c_gen_router_calls_only_place_and_host_replay_files_are_deleted` | router calls only `place`; `payment_http.ex`, `replay.ex` deleted → router calls `finish`, `prepare`; both files present | No GEN router overlay, no deletions |
| `test_c_gen_0003_runner_passes_all_five_steps` | 5 steps pass → GEN copy of `replay_run_test.py` not in the tree | No GEN copies; the 0003 runner does not start (prevents a false pass on the originals) |
| `test_d_gen_replay_matrix_eight_cases` | 8 cases equal → same precondition fails | Same |
| `test_d2_L0_live_valid_body_baseline` | HTTP 200, 1 record, 1 finish → compiler exit 1 | No generated module; release not built |
| `test_d2_L1_live_unknown_key_accepted_with_hint` | HTTP 200, record `unknown_keys == ["fraud_score"]`, span hint, 1 finish → compiler exit 1 | Same |
| `test_d2_L2_live_status_503_rejected` | HTTP 502, 1 record status 503, error span, 0 finish → compiler exit 1 | Same |
| `test_d2_R1_replay_missing_key_is_decode_error` | `PaymentError{reason: "decode"}`, decode 1, finish 0, transport 0 → compiler exit 1 | Same |
| `test_d2_R2_replay_of_L1_record_gives_same_success_and_hint` | `{ok, PAYMENT, hint unknown_keys}`, finish 1, transport 0 → compiler exit 1 | Same |
| `test_d2_R3_replay_wrongly_typed_field_is_decode_error` | as R1 → compiler exit 1 | Same |
| `test_d2_P1_pipe_stops_after_failed_effect` | `PaymentError{reason: "transport"}`, prepare 1, finish 0 → compiler exit 1 | Same |
| `test_e_lib_form_is_the_fixed_strongest_library` | ReplayLib ≤ 60 lines with `rescue`, descriptor without field names, `replay.ex` deleted, one `ReplayLib.record` → all four missing | No LIB arm |
| `test_e_lib_arm_replays_matrix` | 5 steps and 8 cases pass → LIB copy of `replay_run_test.py` not in the tree | No LIB copies; the 0003 runner does not start (prevents a false pass: an empty LIB tree equals the control) |
| `test_e_lib_type_mismatch_outcomes_recorded_then_frozen` | outcomes recorded, freeze hashes equal → no `ReplayLib` module | No LIB arm, no freeze |
| `test_control_originals_unchanged_by_arm_runs` | pass → pass | Guard, not RED |

**[Inference]** The 7 (d2) tests and (b) share one root cause now: the compiler. After compiler GREEN they must show RED again on the generated behavior (decode, hint, pipe stop) before the emit is accepted. This follows the skill rule "For each new meaningful behavior step, repeat RED".

### GROUP 4: DRIFT, case (f)

Command: `python3 -B experiments/0004-generated-replay/tests/drift_test.py`. Result: 2 failed, 1 passed (exit 1).

| Test | Expected → actual | Reason |
| --- | --- | --- |
| `test_f_lib_is_frozen_before_drift` | freeze record equals LIB hashes → no `arms/lib/freeze.json` | No LIB, no freeze |
| `test_f_drift_outcomes_recorded_per_arm_and_derivative` | `run.py drift` exit 0 with 3 × 2 outcome classes → exit 2 `not_implemented` | No DRIFT runner (stub) |
| `test_f_drift_fixtures_change_only_beaml_declarations` | pass → pass | Guard: fixtures change only declarations; the pipe lines stay |

## Decisions (Decision4)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| D1 | Fixture and overlay layout | Undo | `bad/`, `drift/{R,N,Q}/` at the EXPERIMENT root. An arm overlay mirrors repository paths under `arms/<arm>/overlay/`; deletions are in `arms/<arm>/delete.txt`; GEN source is `arms/gen/orders.beaml`. One generic apply rule |
| D2 | "One `beaml-declaration-v1` comment per declaration" | Undo | One comment per callable declaration (`effect` and `fn` clause), none for `interface`. The name is the BEAML name (`payments.authorize`). Smallest reading of the 0001 rule |
| D3 | String checks in generated code | Undo | Accept plain text or the 0001 byte-list form (`<<...>>`), because the emitter writes strings as byte lists |
| D4 | Strict compile of (b) | Undo | Checked in the GEN tree with `mix compile --force --warnings-as-errors`, because the module calls `ProbeSupport` |
| D5 | Arm tree builder | Undo | Test support in `tests/arm_tree.py`. `run.py` stays a stub until GREEN; GREEN can reuse the builder |
| D6 | Hint name and place (owner change) | Migrate | Field `unknown_keys` (list of key names) in the RESPONSE RECORD and attribute `unknown_keys` on span `orders.payments.authorize`. Stored records depend on the field name. The record `version` stays 1 here; a version change is open |
| D7 | Hint in a REPLAY RUN | Repair | `Replay.run/3` returns `{:ok, payment}` without an unknown key and `{:ok, payment, %{unknown_keys: [...]}}` with one. The 0003 matrix and table line 57 stay unchanged. Review this choice before GREEN |
| D8 | Replay cases after the owner change | Undo | R2 = replay of the L1 record (success and hint), the added case. New R3 = wrongly typed declared field (`status: 7`) → decode error, from the restated owner rule |
| D9 | Base record of R1 and R3 | Undo | Live case L0 (stub, valid compact body) gives the record, not the first call against the real Payments release. Same Orders release and record writer |
| D10 | DRIFT-Q shape | Undo | New request TYPE `PaymentRequest { order_id, channel }` with literal `"web"`, because `Order` is also the input of `prepare` and the router input. Payments `Order` gets `channel` |
| D11 | LIB form checks in (e) | Undo | Assert: ReplayLib ≤ 60 lines, `rescue` present, descriptor names no TYPE field, one `ReplayLib.record` call, router unchanged. The descriptor budget "about 10 lines" is not asserted |
| D12 | DRIFT outcomes | Undo | Recorded, not asserted (README). RED only on the freeze precondition and the record shape of `run.py drift`. Class tokens: `compile_error`, `typed_reject`, `correct_accept`, `false_reject`, `wrong_accept`, `untyped_crash` |
| D13 | `payments.beaml` byte-identical guard | Undo | Snapshot of the HEAD compiler output in `tests/payments.generated.snapshot` |
| D14 | Negative tests and the old parser | Undo | A negative test also fails when the message is the old parser message `expected interface, enum, or fn` |

## Test files (SHA-256 at RED)

| File | Tests | SHA-256 |
| --- | --- | --- |
| `experiments/0001-syntax-to-beam/tests/cli.rs` | 11 (8 new RED, 1 new guard, 2 existing) | `78c4212f80713aa73ed983afc8dfdf5854055499900d847c8b5b6fe283512fdc` |
| `experiments/0004-generated-replay/tests/overlay_diff_test.py` | 3 (2 RED, 1 guard) | `6fe091cdb018f9479fd15be6400cbfc1870bddc10ba0f52452d29ba68b5d76f7` |
| `experiments/0004-generated-replay/tests/arms_test.py` | 15 (14 RED, 1 guard) | `83c0f832f9485731de7bbc2b9baacc06b784abd0a7a9c195945abe195be15479` |
| `experiments/0004-generated-replay/tests/drift_test.py` | 3 (2 RED, 1 guard) | `556e8ecd7aead19ffa7bf89d2e79c789c0482d1c2861aa35e9f4cff0100c2f73` |
| `experiments/0004-generated-replay/tests/arm_tree.py` | support | `ff23d780e43c16afcf58fa20fcab7ded44c4e6e14f3af5af657a77b7f0ae6b1d` |
| `experiments/0004-generated-replay/tests/payments.generated.snapshot` | data | `69bbf771460420f55a9ebf5e6ef7db6229ef81658b1784e2c32793398ea8233e` |
| `experiments/0004-generated-replay/run.py` | stub | `f50c4b2d190bfe479d0d7696133101503d4702984d1423818bae23bd054393f1` |
| `experiments/0004-generated-replay/arms/gen/orders.beaml` | fixture | `8a4f7b2043b28668e42bbb5778387e383c5a59ffba2da12a550eee96199c5c09` |

Bad and DRIFT fixture hashes are in [red-output.log](red-output.log).

## Events outside the plan

- **[Verified]** Commit `49aedb9` (main agent, owner decision change) also contains the new tests in `tests/cli.rs`. The RED worker made no commit.
- **[Verified]** GROUP 3 run 1 had a setup error in the test harness. It is retained and not counted.
- **[Unknown]** P1 and the observer control run in an eval VM without the OpenTelemetry application. RED does not show yet whether the generated span code works there (README limit, revision 4).

## RED check (main agent, 2026-11-06)

**[Proposal]** D7 changed (Repair): `Replay.run/3` keeps one return shape, `{:ok, payment}` or `{:error, reason}`. The `unknown_keys` hint is not part of the return value. A REPLAY RUN reports it the same way as live: as the `unknown_keys` attribute on the replay EFFECT span and in the replay report. Reason: two success shapes would force every caller to handle both. R2 reads the hint from the replay report.
**[Proposal]** D6 accepted as Undo: the hint field name `unknown_keys` came from the main agent. The record version stays 1.
**[Inference]** (b) and the (d2) cases share one root cause today (the compiler). GREEN runs in two steps: GREEN-1 compiler (cases a, b); then a fresh RED check that each (d2) case fails for its own reason; then GREEN-2.
**[Verified]** The main agent's commit 49aedb9 included this worker's cli.rs tests while the worker still ran. No content was lost. This broke the rule "never commit while a worker writes files".
