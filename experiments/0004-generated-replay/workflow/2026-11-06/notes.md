---
id: experiment-0004-slice-1-notes
kind: ledger
status: red-repaired
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

## Test files (SHA-256 after RED repair)

| File | Tests | SHA-256 |
| --- | --- | --- |
| `experiments/0001-syntax-to-beam/tests/cli.rs` | 12 (9 new RED, 1 new guard, 2 existing) | `bf2b82fd1ff015ae86181b2b392018d1853aa8cb624f2507b09d582dd227210b` (RED: `78c4212f…`) |
| `experiments/0004-generated-replay/tests/overlay_diff_test.py` | 3 (2 RED, 1 guard) | `6fe091cdb018f9479fd15be6400cbfc1870bddc10ba0f52452d29ba68b5d76f7` |
| `experiments/0004-generated-replay/tests/arms_test.py` | 16 (15 RED, 1 guard) | `c0f35e8f64dd6d1b48747d04ace68153c0f048238596a8b33bcfb7effcfa2d4f` (RED: `83c0f832…`) |
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

## RED repair (2026-11-06)

**[Requirement]** Input: [red-review.md](red-review.md), verdict BLOCK, objections 1–3 (high). The main agent ordered the repair. Tests only; no compiler, Elixir app or `run.py` change. No commit.

**Objection 1, template control (`cli.rs`).**
- The generated decode of `Payment` has the fixed name `__beaml_decode_payment/1` (`def` or `defp`). `orders_cli_emits_flow_effect_decode_and_replay` requires it.
- New helper `decode_body` slices the emitted source from the first decode head to its last clause `end`. Field names are checked inside that slice only.
- `orders_cli_template_control_drift_r_decode_names_reference`: base decode names `order_id`, `status`, not `reference`; DRIFT-R decode names all three. The whole base output still must not name `reference`.
- New `orders_cli_template_control_drift_n_decode_follows_field_rename`: base decode names `status`, not `state`; DRIFT-N decode names `order_id` and `state`, not `status`.
- **[Verified]** Scratch self-check of `decode_body` (not in the repository): a multi-line decode and a two-clause one-line decode slice correctly; `finish/1` and `__beaml_valid__` outside the slice do not count.

**Objection 2, case (d2) (`arms_test.py`).**
- New live case `test_d2_L3_live_missing_key_is_typed_decode_error`: stub 200 with `MISSING_KEY_BODY`. Expect HTTP 502 `downstream_failure`, span `orders.payments.authorize` with `outcome: "error"` and `reason: "decode"`, one RESPONSE RECORD (status 200, bytes byte-exact), 0 `orders.finish`, transport 1.
- `HARNESS`: the 3-tuple branches are removed. A 3-tuple now reports `unexpected`. With input `observe: true` the eval VM starts only `:opentelemetry` and `ProbeSupport.Capture`, then flushes; the harness adds `out/spans.jsonl` to the replay report (`report.json`, key `spans`).
- R2 expects `{"ok": PAYMENT}` and reads `unknown_keys == ["fraud_score"]` from the replay `orders.payments.authorize` span in the replay report.
- **[Verified]** Probe, not a test: an eval VM of the 0002 Orders release started `:opentelemetry` and `ProbeSupport.Capture` and wrote one span with `unknown_keys` to `spans.jsonl`. So the README [Unknown] "eval VM writes no span" does not block R2. No 0003 copy changes; no table change.

**Objection 3, LIB strength (`arms_test.py`).**
- Before the freeze, `test_e_lib_type_mismatch_outcomes_recorded_then_frozen` asserts LIB R1 is `{"error": "%ReplayLib.Error{...}"}` with `step: "decode"` or `step: "finish"` and a `reason`. A raise, an untyped tuple or a missing record fails. L1, L2 and R2 stay recorded, not asserted.
- The `"rescue" in lib` check stays as a guard only.

**Runs.** Serial, each changed command once. Raw output: [red-output.log](red-output.log), section "RED repair". Retained result: `results/20261106T115740198926Z`.

| Group | Command | Result | Reason |
| --- | --- | --- | --- |
| 1 | `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml --test cli` | 9 failed, 3 passed (exit 101) | Lexer stop `unsupported token at byte 215` on the base source; both template controls stop at `assert_compiles` |
| 3 | `python3 -B experiments/0004-generated-replay/tests/arms_test.py` | 15 failed, 1 passed, 0 errors (exit 1) | GEN: `compiler exit 1` (b, d2 incl. L3), missing copies and router (c, d); LIB: no `ReplayLib`, no copies |
| 2, 4 | not changed | not run again | — |

**[Inference]** All new failures are missing behavior. L3 and the R2 hint share the compiler root cause today. After GREEN-1 they need the fresh per-case RED check (RED check, main agent).

**[Requirement]** Review condition (red-review.md, "Two-step GREEN"): GREEN-1 stops at the shape that case (b) checks. Case (b) now also checks `__beaml_decode_payment/1` and its field names. GREEN-1 may derive the field names into the decode, but it must not write the decode behavior that (d2) asserts. After GREEN-1, record per (d2) case the failure reason (for example R1 `ok` instead of `decode`).

**[Unknown]** README case (d2) does not list L3 yet; README line 80 and the decision rows still need the D7 repair text. A plan worker must update them.

### Decisions (Decision4, RED repair)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| D15 | Decode function name `__beaml_decode_payment/1` (`def` or `defp`) | Undo | Reviewer proposal; follows the 0001 `__beaml_` prefix. The name is internal; no stored data depends on it |
| D16 | Decode slice rule | Undo | From the first head to the first other line at the same or a smaller indentation; other clauses of the same name and the `end` stay in |
| D17 | Second asserted drift test uses DRIFT-N (rename) | Undo | Existing fixture; a rename shows both an added and a removed name in the decode |
| D18 | EFFECT span attribute `reason` for a failed EFFECT (L3) | Migrate | Span consumers and `query.py` filters may depend on the name. Same value set as `PaymentError.reason` |
| D19 | L3 reply body `{"error": "downstream_failure"}` | Undo | Same router error path as L2 |
| D20 | Replay hint source: eval VM with `observe` starts only `:opentelemetry` and `ProbeSupport.Capture` | Undo | Router and Orders application stay stopped; R2 only. Other replay cases keep the 0003 eval VM without applications |
| D21 | LIB R1 typed check by pattern `%ReplayLib.Error{` with `step` `decode`/`finish` and `reason` | Undo | README fixes the shape; the `reason` value is not asserted ("any typed shape counts" for its content) |


## RED repair check (main agent, 2026-11-06)

**[Proposal]** D18 class lowered from Migrate to Repair by the main agent. Reason: the span attribute name `reason` on a failed EFFECT is contained in this experiment and changes with one emit edit. Decision4 rule: every de-escalation is recorded.
**[Verified]** README updated: case L3, the LIB R1 assertion before the freeze, LIB runs L3, and the D7 return shape of `Replay.run/3`.

## GREEN-1 (compiler)

**Scope.** Compiler only: `experiments/0001-syntax-to-beam/src/main.rs`. No change to tests, fixtures, router, apps, arm overlays, LIB or `run.py`. No commit. Input: the review condition in [red-review.md](red-review.md) ("Two-step GREEN") and the RED check of the main agent.

### Change summary

`main.rs`: 1038 → 1639 lines (`git diff --numstat`: +631, −30). `rustfmt --check` passes on `main.rs`.

- **Lexer.** Dotted names (`payments.authorize`, `http.post`), token `|>`, symbols `!` and `|`. A plain identifier position still rejects a dotted name.
- **Parser.** `effect NAME IN -> OUT ! ERR = KIND("path")`. `! A | B` after the output TYPE of `fn` and `effect`. A `fn` body `head |> step |> step`.
- **Checker.** Unsupported EFFECT kind (only `http.post`). EFFECT name `namespace.operation`. Failure TYPES are declared interfaces. An EFFECT has one failure TYPE with `reason: String`, an interface output with String fields only, a safe path. Pipe: unknown step, input TYPE per step, each step failure TYPE in the `!` list of the enclosing fn. A `!` fn is a pipe step only. One EFFECT, one flow per EFFECT (one clause, its parameter starts the pipe). The existing pattern check gives "unknown field: Payment.amount".
- **Emit, derived from the declarations.** Service name = source file stem (`orders`). `place/1` (`{:ok, v}` or `{:error, e}`, `with` chain, a failed step stops the pipe), spans `<service>.<step>` through `ProbeSupport.span/5`, the event `<EFFECT output TYPE, lower case>_request_prepared` in the span of the pure step before the EFFECT, `payments_authorize/1` (client span, trace context, `Http.post`, `Replay.record/3` before the status check), `__beaml_decode_payment/1` (field names from the TYPE), one struct module per failure TYPE (`PaymentError`), `Http` (0002 framing on `:gen_tcp`), `Replay.record/3` (RESPONSE RECORD version 1), `Replay.run/3` (the flow with the EFFECT step replaced by the six 0003 checks, then decode in a replay span `orders.payments.authorize`, then `finish`). Without EFFECTS, `!` lists and pipes, the output is unchanged (`payments.beaml` snapshot test).

**[Verified]** Held back, per the review condition (decode behavior that (d2) asserts must not be written in GREEN-1): the missing-key and wrong-TYPE decode error, the `unknown_keys` hint (record and span), the typed `PaymentError` for transport, status and decode, the span attribute `reason`. In GREEN-1 these paths raise (`MatchError`, `ArgumentError`). GREEN-2 therefore needs a compiler change too.

### Commands (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` | 0 | unit 9/9, `cli` 12/12 (all (a), (b), both template controls, both guards) |
| `python3 -B experiments/0003-source-linked-replay/run.py` | 0 | control `pass`, `results/20261106T121058907971Z` |
| `python3 -B experiments/0004-generated-replay/tests/overlay_diff_test.py` | 1 | 2 failed, 1 passed |
| `python3 -B experiments/0004-generated-replay/tests/arms_test.py` | 1 | 13 failed, 3 passed; `results/20261106T121208673328Z` |
| `python3 -B experiments/0004-generated-replay/tests/drift_test.py` | 1 | 2 failed, 1 passed |

Also run once before: `arms_test.py -k test_b` → pass (`results/20261106T121006597252Z`). SHA-256 `tests/cli.rs` before and after: `bf2b82fd1ff015ae86181b2b392018d1853aa8cb624f2507b09d582dd227210b` (equal). `main.rs` after: `80d596170a1eb361a9481474a6443c15db8391b7950e016d5f860876daba61ec`.

### Fresh RED check input (after GREEN-1)

| Test | Status | Reason |
| --- | --- | --- |
| `test_b_gen_module_compiles_with_warnings_as_errors` | pass | Generated module compiles with `--warnings-as-errors` in the GEN tree |
| `test_d2_L0_live_valid_body_baseline` | pass | Not RED: the old router and host transport serve it; the generated EFFECT is not on the live path |
| `test_d2_L1_live_unknown_key_accepted_with_hint` | fail | HTTP 502, not 200: host `payment_http.ex` passes the extra key to `finish`; no `unknown_keys`. Router (GREEN-2) and hint (held back) |
| `test_d2_L2_live_status_503_rejected` | fail | 0 records, span `orders.payment_http`: host transport raises before its CAPTURE. Router (GREEN-2) |
| `test_d2_L3_live_missing_key_is_typed_decode_error` | fail | No `orders.payments.authorize` span, `finish` 1: host path. Router (GREEN-2) and typed decode (held back) |
| `test_d2_R1_replay_missing_key_is_decode_error` | fail | Own reason: `raised ArgumentError`, `finish/1` 1, not `PaymentError{reason: "decode"}` with `finish/1` 0. `:json.decode/1` 1, transport 0 hold |
| `test_d2_R2_replay_of_L1_record_gives_same_success_and_hint` | fail | Own reason: result `{ok, PAYMENT}` and counts equal; replay span has no hint (`[None]`, not `[["fraud_score"]]`) |
| `test_d2_R3_replay_wrongly_typed_field_is_decode_error` | fail | Own reason: `raised ArgumentError`, `finish/1` 1 |
| `test_d2_P1_pipe_stops_after_failed_effect` | fail | Own reason: `raised MatchError`, not `PaymentError{reason: "transport"}`; `prepare/1` 1 and `finish/1` 0 hold |
| `test_c_gen_router_calls_only_place_...` | fail | Router calls `finish`, `prepare`; `payment_http.ex`, `replay.ex` present (GREEN-2) |
| `test_c_gen_0003_runner_passes_all_five_steps`, `test_d_gen_replay_matrix_eight_cases` | fail | GEN copy of `replay_run_test.py` not in the tree (GREEN-2) |
| `test_e_*` (3) | fail | No `ReplayLib`, descriptor, LIB copies or freeze (LIB arm) |
| `test_control_originals_unchanged_by_arm_runs` | pass | Guard |
| overlay `..._gen`, `..._lib` | fail | Copies and `assertion-changes.json` missing |
| drift `test_f_lib_is_frozen_before_drift` | fail | No `arms/lib/freeze.json` |
| drift `test_f_drift_outcomes_recorded_per_arm_and_derivative` | fail | `run.py` stub exits 2 `not_implemented` |

**[Inference]** R1, R2, R3 and P1 fail for their own reason. L1, L2 and L3 still fail on the host router first; their own reason shows only after the GREEN-2 router overlay.

### Decisions (Decision4, GREEN-1)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| G1 | Hold back the (d2) behaviors (decode checks, hint, typed transport/status/decode failure, span `reason`) | Undo | Review condition; keeps the fresh RED of R1, R2, R3, P1 genuine. GREEN-2 needs a compiler step |
| G2 | `<service>` of span names = source file stem, required to be a lowercase identifier when a pipe or an EFFECT exists | Repair | README derives `<service>.<step>`; the source has no other service name. One emit edit changes it |
| G3 | `<TYPE>_request_prepared` uses the output TYPE of the EFFECT (`Payment` → `payment`), lower case without separators | Repair | Only reading that gives the kept `payment_request_prepared` |
| G4 | Failure TYPE in the `!` list is matched by name, not structurally | Repair | The generated struct carries the name. Structural later only accepts more sources. Owner question candidate |
| G5 | `! A \| B` lists parse and check for `fn`; an EFFECT has exactly one failure TYPE with `reason: String` | Undo | Owner decision allows lists; Q6 default (i) for slice 1 |
| G6 | A `!` fn may only be a pipe step; a pipe is only a whole fn body; a pipe fn has one clause | Undo | Slice 1 boundary; no `with` yet |
| G7 | One EFFECT per source; its flow has one parameter that starts the pipe and calls the EFFECT once; EFFECT output fields are String only | Undo | Slice 1 boundary (README "second EFFECT" is later; decode "String values") |
| G8 | Nested modules: `import Kernel, only: [..., defmodule: 2]` only when failure TYPES or EFFECTS exist; `Http` and `Replay` import full `Kernel`; `Replay` reaches the parent by `@parent` from `Module.split` | Undo | Keeps `payments.beaml` output byte-identical and survives the 0002 rename of one `defmodule BeamlSpike do` |
| G9 | Decode is `def` (public), because `Replay.run/3` calls it from the nested module | Undo | Test accepts `def` or `defp` |
| G10 | `Replay.run/3` runs the pure steps without spans and without the Orders log; one replay span `orders.payments.authorize` (`:internal`) wraps the decode | Undo | 0003 replay had no spans; R2 reads the hint from this span |
| G11 | The old parser message `expected interface, enum, or fn` stays unchanged | Undo | D14 guard depends on it |

### Events outside the plan

- **[Verified]** A careless shell command ran `git stash` once during GREEN-1. The worker restored the change at once with `git stash pop`; `git stash list` is empty and the diff is complete. No commit.
- **[Verified]** A compiler run from the 0001 directory wrote `experiments/0001-syntax-to-beam/.beaml/actions.jsonl`. The worker removed this untracked file.
