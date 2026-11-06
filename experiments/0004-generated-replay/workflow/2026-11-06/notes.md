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

## RED repair round 2

**[Requirement]** Input: fresh review of the RED tests after GREEN-1, objections 1 and 2 (high), 3 (medium). Tests only: `tests/arms_test.py`, `tests/drift_test.py`. No compiler, router, app, LIB or `run.py` change. No commit.

**Fix 1 (high), L2 typed reason (`arms_test.py`).** A raise (for example `200 = status`, `MatchError`) also gives span `outcome: "error"`. L2 now requires:
- live span `orders.payments.authorize` = `[("error", "status")]` (attribute `reason`, D18);
- new eval run `L2-place` (`mode: place`, `observe: true`) against the same 503 stub: result `{"error": "%OrdersBeamlSpike.PaymentError{reason: \"status\"}"}`, stub `sent` 1, `payments_authorize/1` 1, `:gen_tcp.connect/4` 1, `finish/1` 0, and the eval client span `[("error", "status")]`.
- L3 already asserts `reason: "decode"` on the span; no change.
- New helper `payments_stub(status, body)` (the stub of `live`, moved out unchanged).

**Fix 2 (high), DRIFT evidence (`drift_test.py`).** Contract for `run.py drift` (comment `EVIDENCE_CONTRACT` text in the file): last stdout line `{"run": <new dir in results/>, "drift": ...}`; per row `evidence = {build_output, build_exit_code, new_live_report, pre_change_replay_report}`. The test requires:
- the run dir is new and lies directly in `results/`; each evidence file exists and lies inside the run dir;
- build exit ≠ 0 ⇔ `build == "compile_error"`; with a failed build, `new_live` and `pre_change` are `compile_error`;
- `new_live`: HTTP 200 → `correct_accept` | `wrong_accept`; else `typed_reject` | `false_reject` | `untyped_crash`;
- `pre_change`: `ok` → accept family, `error` → `typed_reject` | `false_reject`, `raised` → `untyped_crash`.
- **[Verified]** Scratch self-check (not in the repository) of `evidence_problems`: a consistent row passes; a wrong build class, a wrong live class, a wrong replay class, a path outside the run dir and missing evidence each fail.

**Fix 3 (medium), L0 and P1 (`arms_test.py`).**
- L0: exactly 1 `orders.payments.authorize` span and 0 `orders.payment_http` spans.
- P1: `payments_authorize/1` 1 and `:gen_tcp.connect/4` 1 (call counts from `WATCHED`, as in R2).

**Runs (serial).** Retained result: `results/20261106T121933265225Z`.

| Command | Exit | Result |
| --- | --- | --- |
| `python3 -B experiments/0004-generated-replay/tests/arms_test.py` | 1 | 14 failed, 2 passed, 0 errors |
| `python3 -B experiments/0004-generated-replay/tests/overlay_diff_test.py` | 1 | 2 failed, 1 passed (unchanged: copies missing) |
| `python3 -B experiments/0004-generated-replay/tests/drift_test.py` | 1 | 2 failed, 1 passed, 0 errors |
| `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` | 0 | unit 9/9, `cli` 12/12 |

| Changed test | Status | Reason |
| --- | --- | --- |
| `test_d2_L0_live_valid_body_baseline` | fail (was pass) | Own reason: `effect_spans` 0, `host_transport_spans` 1. The host transport serves L0 |
| `test_d2_L2_live_status_503_rejected` | fail | Live: 0 records, no EFFECT span (host path). Eval `L2-place`: `raised MatchError`, client span `("error", None)`. This is the false pass of objection 1, now caught |
| `test_d2_P1_pipe_stops_after_failed_effect` | fail | Own reason: `raised MatchError`; `effect` 1, `connect` 1, `prepare` 1, `finish` 0 hold |
| `test_f_drift_outcomes_recorded_per_arm_and_derivative` | fail | `run.py` stub exits 2 `not_implemented`; evidence checks not reached (self-check above) |

SHA-256 after: `tests/arms_test.py` `a726338a8552459f18f60ef75221ad022f5cf1969c3dfc1a2c8761e3c4186963`, `tests/drift_test.py` `87d309d14af335bbbbd3179d42136018feb616810ac75ba2ea60a7d51effc486`.

### Decisions (Decision4, RED repair round 2)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| D22 | L2 typed check through an eval `place` against a 503 stub, plus span `reason` live | Repair | A live HTTP reply cannot show a raise versus a typed error; the eval result can. Over: span attribute only. Commits GREEN-2 to a typed `status` path in `place/1` |
| D23 | Span attribute name `reason` (D18, README L3) for `status` too | Undo | Same name and value set as `PaymentError.reason` |
| D24 | DRIFT evidence keys `build_output`, `build_exit_code`, `new_live_report`, `pre_change_replay_report`; `run` key for the run dir | Repair | README fixes no names. Over: free-form evidence. Commits `run.py drift` (GREEN) to this shape; one test edit changes it |
| D25 | Failed build ⇒ `new_live` and `pre_change` are `compile_error`, report paths may be absent | Repair | No release exists, so nothing can run. Over: a separate "not run" class, which the README does not list |
| D26 | Re-derive class families, not exact classes (accept / reject / crash) | Undo | `correct` versus `wrong` and `typed` versus `false` need the expected outcome; the README judges that |

## GREEN-2

**Scope.** Compiler (d2) behaviour, GEN overlay, LIB arm (fresh worker), LIB freeze, `run.py`. No test file changed. No commit.

### Steps (in order)

1. **Compiler** (`main.rs`, +60 −38 against GREEN-1; `rustfmt --check --edition 2024` clean). Derived from the declarations, no fixture name in the emitter:
   - `__beaml_decode_<output>/1`: one `:json.decode/1` in a `try`; `Map.take` of the declared fields, checked by the existing `__beaml_valid__` of the TYPE; returns `{:ok, value, unknown_keys}` or `:error`. Extra keys are a sorted hint.
   - `payments_authorize/1`: `Http.post` returns `{:ok, status, bytes}` or `:error` (connect, send, framing, read: never a raise). `Replay.record/3` before the status check. Status ≠ 200 → `status`; `:error` → `transport`; decode `:error` → `decode`.
   - A failure sets span attribute `reason`, then raises `BeamlFailure` inside the span (outcome `error`); `__beaml_attempt__/1` turns it into `{:error, %PaymentError{reason: r}}` outside the span. `place` stops the pipe (`with`).
   - Hint: `unknown_keys` on the EFFECT span (only when not empty) and always in the RESPONSE RECORD (`[]` when none).
   - `Replay.run/3`: the EFFECT step is `{:ok, p} <- __beaml_attempt__(span(... __beaml_result_payments_authorize(bytes)))`. Returns only `{:ok, p}` or `{:error, r}` (D7); the hint goes to the replay span.
   - `cargo test`: exit 0 (unit 9/9, cli 12/12; `payments.beaml` snapshot byte-identical).
2. **LIB arm** (fresh worker, no access to the GEN emitter, BEAML or GEN results). `ReplayLib` 59 lines, descriptor 14 lines, one `ReplayLib.record` call, `replay.ex` deleted. Passed (e) (`-k test_e_lib_form -k test_e_lib_arm_replays_matrix`, `results/20261106T122649926410Z`), then **freeze** `arms/lib/freeze.json` (ReplayLib `e5ad6e17…`, descriptor `933566cd…`), then `-k test_e_lib_type_mismatch` (`results/20261106T122809017595Z`): R1 `%ReplayLib.Error{step: "finish", reason: "ArgumentError"}`. No LIB repair before or after the freeze. LIB recorded outcomes: L0 200; L1 502 (no hint); L2 502, 0 records; R2 same error as R1.
3. **GEN overlay**: router calls only `OrdersBeamlSpike.place/1` (keeps `orders.request`, `valid_order!`, `valid_payment!`, reply); `delete.txt` removes `payment_http.ex` and `replay.ex`; 6 copies with the 11 table rows; `assertion-changes.json`. GEN (d2) was judged only after the LIB freeze (12:28 UTC freeze; first full GEN run 12:29).
4. **RED check of L0–L3 after the overlay** (GREEN-1 `main.rs` swapped in temporarily, restored, `cmp` equal; `results/20261106T123209852972Z`): L0 pass (overlay alone serves it); L1 fail own reason (no record hint, no span hint); L2 fail own reason (`raised MatchError`, span `reason` None); L3 fail own reason (span `ok`, `finish` 1). **[Verified]** Step 1 was written before this check, so this is a check of the reasons, not a strict RED-first order.
5. **`run.py`** replaces the stub: default runs `compiler`, `overlay-diff`, `lib-freeze` (verify only), `arms`, `drift`; `drift`; `freeze`; `--list-steps`. Actions to `.beaml/actions.jsonl`, job bus `exp-0004-run`.

### Commands (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` | 0 | 9/9, 12/12 |
| `tests/overlay_diff_test.py` | 0 | 3/3 |
| `tests/arms_test.py` | 0 | 16/16, `results/20261106T122905368972Z` |
| `python3 -B experiments/0003-source-linked-replay/run.py` (control) | 0 | `pass`, `0003/results/20261106T123239743362Z` |
| `run.py drift` (first) | 0 | `results/20261106T123350493778Z`; Q repair failed (see events) |
| `tests/drift_test.py` (second DRIFT) | 0 | 3/3, `results/20261106T123902454745Z`; LIB probe defect (see events) |
| `tests/drift_test.py` (counted DRIFT) | 0 | 3/3, `results/20261106T124451474390Z` |
| `python3 -B experiments/0004-generated-replay/run.py` | 0 | `pass`, `results/20261106T124950474588Z`: all 5 steps exit 0; its DRIFT run gives the same 18 classes and site counts |

### DRIFT (counted run `results/20261106T124451474390Z`)

Classes are derived per row from `observed.json` (reply, proxy exchange, flow probe) and the pre-change `report.json`; the expected outcome comes from the Payments bytes and the drifted TYPE. Sites: replay = manual change sites; domain = `valid_payment!/2` / `valid_order!/1`; test = 0003 test expectations. Every repaired tree passed the 0003 8-case replay test again (exit 0).

| DRIFT | Arm | build | new_live (cause) | pre_change (result) | replay | domain | test |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R | GEN | correct_accept | false_reject (host `valid_payment!`) | typed_reject (`PaymentError decode`) | 0 | 1 | 2 |
| R | LIB | correct_accept | false_reject (host `valid_payment!`) | typed_reject (`ReplayLib.Error finish`) | 0 | 1 | 2 |
| N | GEN | correct_accept | false_reject (host `valid_payment!`) | typed_reject (`PaymentError decode`) | 0 | 1 | 2 |
| N | LIB | correct_accept | false_reject (host `valid_payment!`) | typed_reject (`ReplayLib.Error finish`) | 0 | 1 | 2 |
| Q | GEN | correct_accept | typed_reject (Payments 400 → `PaymentError status`) | typed_reject (`request_mismatch`) | 0 | 1 | 1 |
| Q | LIB | correct_accept | untyped_crash (Payments 400 → transport `MatchError`) | typed_reject (`request_mismatch`) | 0 | 1 | 1 |

Sum of manual change sites: GEN 0, LIB 0. Replay lines: GEN router 0; LIB 59 + 14 + 1. Compiler `main.rs` 1661 lines (one-time cost).

**[Inference]** Q new_live: Payments `valid_order!/1` rejects the drifted request (400) before any decode, in both arms. GEN reports it typed (`status`), the unchanged 0002 transport of LIB raises. This is a live-path difference, not a REPLAY RUN difference. The pass and reject rule is not judged here (review).

### Decisions (Decision4, GREEN-2)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| G12 | Failure inside the span as a raise of a generated `BeamlFailure` exception, caught by `__beaml_attempt__/1` | Repair | Chose raise-and-catch over own span code, because `ProbeSupport.span/5` (fixed SHA) sets `outcome: "error"` only on a raise. Commits us to one hidden exception module per output |
| G13 | `Replay.record/3` computes the hint with a second decode call | Repair | Chose a second `:json.decode` live over `record/4`, because `record/3` is fixed (README, cli.rs). Live decode count is not asserted; replay keeps 1 |
| G14 | Record field `unknown_keys` always present (`[]`); span attribute only when not empty | Undo | Stable record shape; no attribute noise |
| G15 | Any transport failure (connect, send, framing, read) is `transport` | Undo | One reason for "no usable HTTP response" |
| G16 | Decode reuses `__beaml_valid__` of the output TYPE on `Map.take` of the declared fields | Undo | Derived from the TYPE; template control stays |
| G17 | LIB written by a fresh worker | Repair | Chose a separate worker over writing LIB myself, because the README forbids GEN-emitter access to the LIB writer and I had read it |
| G18 | LIB DRIFT BEAML = drifted lines whose declaration exists in the 0002 `orders.beaml`, plus new interfaces | Repair | Chose this derivation over hand-written LIB fixtures, because the same TYPE edit must apply and LIB has no `effect`/`place`. One function in `run.py` |
| G19 | Loopback proxy and an eval flow probe give the cause of a live failure | Repair | Chose extra evidence over the HTTP code alone, because a 502 does not show host validation versus arm failure. Commits DRIFT to two Payments calls per row |
| G20 | Host validation reject of a fitting response = `false_reject`, same class in both arms; domain sites counted apart | Repair | README counts `valid_payment!/2` apart; classifying it `untyped_crash` would charge the host to an arm |
| G21 | Build class `correct_accept` on exit 0 (both BEAML files change together) | Undo | drift_test ties `compile_error` to exit ≠ 0 |
| G22 | Repairs as `arms/<arm>/repair/<D>.json` text edits; hunks counted from the real file diff; verified by the 0003 replay test in the repaired tree | Repair | Chose spec plus measured diff over a hand count. Commits the count to the file-class rule (ProbeSupport = domain, 0003 copies = test, else replay) |
| G23 | Q repair edits `valid_order!/1` (Payments accepts `channel: "web"`) | Repair | Found by the first DRIFT run (Payments 400). Domain site, equal in both arms |
| G24 | `run.py` default runs all steps, including `arms` and `drift` | Undo | One repeatable command, as 0003 |

### Events outside the plan

- **[Verified]** First DRIFT run: Q repair incomplete (Payments `valid_order!/1` 400); repaired by G23. Retained.
- **[Verified]** Second DRIFT run: the LIB flow probe called the transport outside a span; `ReplayLib.record` then raised `FunctionClauseError` on `:undefined` span context, so LIB R/N showed `untyped_crash` while the live router failed in host validation. The probe now wraps the transport in `orders.payment_http` as the router does. Retained, not counted.
- **[Verified]** One `run.py` all-steps run was stopped by me after this finding: `results/20261106T124408155023Z` and `results/20261106T124410526023Z` are partial, not counted.
- **[Verified]** The LIB worker wrote no file outside `arms/lib/` and `results/`.

## Slice 2 RED

**Scope.** README revision 6, tests and fixtures only. No compiler, router, app, LIB or `run.py` change. No commit. Input: OWNER answers O1–O4 of 2026-11-06 (main agent), README slice 2 (commits `c376880`, `419cfd7`).

### README revision 6 changes (Slice 2 section only)

- MIGRATE CHAIN replaces the RENAME ALIAS options S1, S2, S3: `migrate Payment 1 -> 2 { rename status -> state }`. The `interface` is the newest version. Old versions are derived backwards.
- RESPONSE RECORD key `type` gets `version`. Fingerprint = lower-case hex SHA-256 of the compact JSON of `fields`, sorted by field name; TYPE name not included.
- Path check: the build fails only when a stored TYPE VERSION has no path to the newest version. The `help` line is `migrate <TYPE> <stored> -> <next> { rename <old> -> <new> }`.
- C5 (DRIFT R, no chain) is now a compile error. `add`, `drop` and changed field TYPES are out of scope. C7 uses the slice 1 source, so that the missing `type` key is the only fault.
- C2 new call runs `place/1` in an eval VM, not through the router (host `valid_payment!/2` checks `status`).
- O1–O4 answered in the OWNER questions list; O5 open.
- Gap recorded: three GEN 0003 copies call the compiler without `--stored` (see below).
- GLOSSARY: TYPE VERSION gets the version number; RENAME ALIAS is a `rename` step; new term MIGRATE CHAIN.

### Fixtures

- `stored/v1.jsonl`: the slice 1 L0 RESPONSE RECORD (`results/20261106T125806715083Z`) plus `type` of `Payment 1 { order_id status }`. Its `artifact_id` comes from the slice 1 build.
- `stored/v1-v2.jsonl`: the `v1` record and a hand-built `Payment 2 { order_id state }` record (body `state: "settled"`, `artifact_id` = SHA-256 of a fixed text, no build).
- `stored/empty.jsonl`: empty file.
- `slice2/{N-chain,N-statuz,N2,N2-chain}/orders.beaml`. The file stem stays `orders` (G2 service name). A guard test checks that the template with the fixture names gives these sources.

### Runs (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `cargo test --offline --manifest-path experiments/0001-syntax-to-beam/Cargo.toml` | 101 | unit 9/9; `cli` 9 passed, 5 failed |
| `python3 -B experiments/0004-generated-replay/tests/stored_types_test.py` | 1 | 22 failed, 1 passed (guard) |
| `python3 -B experiments/0004-generated-replay/tests/slice2_replay_test.py` | 1 | 8 failed, 1 passed (guard); `results/20261106T150916971663Z` |
| `python3 -B experiments/0004-generated-replay/tests/arms_test.py` | 1 | 9 failed, 7 passed; `results/20261106T151045829318Z` |
| `python3 -B experiments/0004-generated-replay/tests/overlay_diff_test.py` | 0 | 3/3 |
| `python3 -B experiments/0004-generated-replay/tests/drift_test.py` | 0 | 3/3; `results/20261106T151333319036Z` |
| `python3 -B experiments/0003-source-linked-replay/run.py` | 0 | `pass`, `0003/results/20261106T151828796490Z` |

### New and changed tests, fail reason

| Test | Case | Status | Reason |
| --- | --- | --- | --- |
| `cli.rs` `orders_cli_effect_source_without_stored_is_rejected` | C8 | fail | Exit 0: no `stored TYPE VERSIONS unknown` check |
| `cli.rs` `orders_cli_parse_and_type_errors_come_before_stored_check` | C16 | pass | Guard: the pipe check already names `charge` |
| `cli.rs` `orders_cli_accepts_effect_pipe_place`, `..._emits_flow_effect_decode_and_replay`, both template controls | C10 | fail | `usage:`: the CLI takes no `--stored` input. Expected, they now pass the empty snapshot |
| `stored_types_test.py` C1, C4, C5, C15 (Fixture, Template) | C1, C4, C5, C15 | fail | Exit 1 with `usage:`; no TYPE, field, path or `help` token |
| `stored_types_test.py` C7 | C7 | fail | `usage:`; no `stored RESPONSE RECORD has no TYPE VERSION` |
| `stored_types_test.py` C8 | C8 | fail | Exit 0 without `--stored` |
| `stored_types_test.py` C2, C3, C6, C10, C14 | build cases | fail | Exit 1 `usage:` instead of exit 0 |
| `stored_types_test.py` `test_fixtures_match_the_template_rule` | — | pass | Guard: fixture fingerprints and sources follow the template rule |
| `slice2_replay_test.py` C2 (old record, new call), C3, C11, C12, C13, C14, C9 | replay cases | fail | Build stops at `<tree>-generate-orders: compiler exit 1: usage:` |
| `slice2_replay_test.py` `test_control_originals_unchanged_by_slice_2_runs` | — | pass | Guard |
| `arms_test.py` (b), (d2) L0–L3, P1, R1–R3 | C10 | fail | `gen-generate-orders: compiler exit 1: usage:`. Expected, the GEN build now passes `--stored stored/empty.jsonl` |

**[Verified] Own reason, scratch self-checks (not in the repository).**
- `stored_types_test.py` with `BEAML_SPIKE` = the slice 1 compiler that drops `--stored`: C6 and C10 pass (Fixture and Template). C1, C5, C15, C7, C8 fail on exit 0. C2, C3, C14 fail on `unsupported token` (`migrate`). C4 fails on missing tokens. So each case fails on missing compiler behaviour, not on the harness.
- `slice2_replay_test.py` with a compiler call that drops `--stored` (`results/20261106T150934590159Z`, not counted): C9 passes end to end (typed decode error, `finish/1` 0, `artifact_id` differs). The chain cases fail on `unsupported token`.
- Accept path on the slice 1 source with the same drop (`results/20261106T151006992836Z`, not counted): `replay_plain` gives `{ok: {order_id, status}}`, `:json.decode/1` 1, `finish/1` 1, hint `[["fraud_score"]]`; the `place` new call writes one record (no `type` key yet). `cross_build` was false there, because the slice 1 source rebuilds the exact slice 1 BEAM. The slice 2 case sources differ, so their builds differ.

**[Verified] Old tests.** Only the C10 tests above fail, and only because they pass `--stored` (expected). Unchanged and passing: unit 9/9, five `bad/*` tests, both `payments_cli_*` tests, `invalid_source_...`, arms (c), (d), (e) and the control guard, overlay diff 3/3, drift 3/3. 0003 `run.py` exits 0: its `compiler-reference` step runs only `payments_cli_emits_checked_authorize_reference`, and its tests compile the 0002 `orders.beaml` (no `effect`).

**[Verified] Gap for GREEN.** drift_test and the arms tests (c), (d) pass today only because the current compiler ignores the missing `--stored`. After GREEN (O2) they fail: `run.py` (GEN `generate-orders`) and three GEN 0003 copies (`replay_run_test.py:140`, `response_capture_test.py:91`, `trace_lookup_test.py:50`) compile the GEN `orders.beaml` without `--stored`. The copies are part of the slice 1 change table and the overlay diff test, so GREEN must change the table too.

### SHA-256 of changed files

| File | SHA-256 |
| --- | --- |
| `experiments/0001-syntax-to-beam/tests/cli.rs` | `2354c81a1bd0b29f04dcda855870c3d8c3e45fcde5e0e27e38d7e04eb28b8d8b` |
| `experiments/0004-generated-replay/tests/arms_test.py` | `0298a9d9be2a050bf016434a4fe2f64acc46b6bd88026aae0547faf898b9bdf2` |
| `experiments/0004-generated-replay/tests/stored_types_test.py` | `627b67fc9cd70d216144e4fed3099fbee31239fede8318287f9580ce061ed538` |
| `experiments/0004-generated-replay/tests/slice2_replay_test.py` | `a77f32ed853765ade5351aafdb811051da7d44c45534b4a68b638d535c809dad` |
| `experiments/0004-generated-replay/stored/v1.jsonl` | `e438abc24d23ef3ea62f5d748f2168151f3252a2700ccd4f1448255c40e574a4` |
| `experiments/0004-generated-replay/stored/v1-v2.jsonl` | `14dac3d471df969ffc43ab42cc26a72e14ace06080843164bac43da044da4585` |
| `experiments/0004-generated-replay/stored/empty.jsonl` | `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855` |
| `experiments/0004-generated-replay/slice2/N-chain/orders.beaml` | `b93307fff885ee1192c8715e73e07c950b246e1952655524e5b92c95f34e4c3a` |
| `experiments/0004-generated-replay/slice2/N-statuz/orders.beaml` | `e1ea15fc8e23e6c52c3fd24cad7f5a537d5b4658588b0849be2ccef4259a2bee` |
| `experiments/0004-generated-replay/slice2/N2/orders.beaml` | `d4c6ca512447bd3d2c11bb340f84a2bbad89efb8f7ed6b98b585f05eddac7819` |
| `experiments/0004-generated-replay/slice2/N2-chain/orders.beaml` | `841a3a488f924543686dae4ad7b820fef3ce997471becca81cb2adff0168ac79` |

### Decisions (Decision4, slice 2 RED)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| S1 | Fingerprint text: compact JSON of the sorted `[name, TYPE]` list, TYPE name not included | Undo | No record with `type` exists yet; one constant in tests and compiler |
| S2 | CLI form `SOURCE --stored PATH` | Undo | One form in all tests |
| S3 | `migrate` line directly after its `interface` | Undo | Fixture position only; the grammar may accept others |
| S4 | O3 reading: with backwards derivation the old field is always in the derived version; C4 is caught by the path check and must name `statuz` and `status` | Repair | Chose this over "old field in no stored version" (plan text), because that reading rejects every chain with an empty snapshot. Over: a separate O3 error text. Because: answer 2 says the build fails only for a missing path. Commits C4 to the path check message |
| S5 | C2 new call through the eval `place/1` against the stub, not the router | Repair | Chose eval over the slice 1 DRIFT N domain repair of `valid_payment!/2`. Because: the host check is not the TYPE claim. Commits C2 to an eval VM run that writes the record |
| S6 | Template run of every compile case with random TYPE and field names | Repair | Chose a template over more fixtures. Because: a compiler with fixture names in it cannot pass. Commits the compiler to `__beaml_decode_<lower TYPE>` for any TYPE name |
| S7 | Harness mode `replay_plain` (no `valid_payment!/2`) and report key `artifact` in `arms_test.py` | Repair | Chose a harness mode over a host repair. Because: `valid_payment!/2` knows only `status`. Commits the shared HARNESS to two more lines |
| S8 | C3 replays both records on the C2 build (v1 snapshot); the C3 build with `v1-v2` is checked at compile level only | Undo | Saves one release build; the generated code must not depend on the snapshot |
| S9 | C7 source = slice 1 source, untyped record at line 2 | Undo | Isolates the missing `type` key from the path check |
| S10 | Hand-built `v1` and `v2` fixtures before GREEN | Repair | Chose hand-built over the planned `run.py` capture, because the compiler writes no `type` key yet. Commits GREEN to compare a real `v1` capture with this fixture |
| S11 | `:json.decode/1` count 1 in replay cases | Undo | Same as slice 1 R1; the fallback must not decode twice |

**[Unknown]** No Migrate question came up. The GEN 0003 copy gap needs a change to the slice 1 change table; the main agent decides who writes it.

## Slice 2 RED repair

Three medium gaps of the RED check are closed in `tests/stored_types_test.py`. Each new case runs with the fixture names and with random names.

| Case | Snapshot | Source | Expected |
| --- | --- | --- | --- |
| C1b | line 1: `T 1 { k n }` (path); line 2: `T 1 { k o }` (no path) | N | C1 tokens, help `1 -> 2` |
| C17 | one record: `fields` = `T 1 { k n }`, `fingerprint` = fingerprint of `{ k o }` | N | compile error that names `T`, the `--stored` path, `fingerprint` and the first 12 hex of the stored fingerprint |
| C18 | one record: `T 2 { k n }` | N2-over-chain: `interface T { k2 n }`, `migrate T 1 -> 2 { rename o -> n }` | tokens `T`, `k`, `k2`, path, help `migrate T 2 -> 3 { rename k -> k2 }` |

Every assertion message now ends with the names of the run (`[names: T=... k=... ...]`), so a failed template case can be re-run.

Run: 29 tests, 28 fail, 0 errors. The guard test passes. All six new tests fail for the same reason as the old ones: the compiler prints its usage text, because it does not accept `--stored`.

New SHA-256 of `experiments/0004-generated-replay/tests/stored_types_test.py`: `a69b8886e8e8b032822e45b02a8caac84f19cbf4b81a3b9855d464845bd3257f`

### Decisions (Decision4, slice 2 RED repair)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| S12 | C17: the fingerprint wins over `fields` | Repair | Chose "fingerprint decides, no path" over "fields decide". Because: README path check says equal means the same fingerprint, and the compiler reads `fields` only for its message. The README has no text for a fields/fingerprint mismatch. Over: a separate mismatch error text. Commits the message to name `fingerprint` and the first 12 hex of the stored fingerprint (README error text line) |
| S13 | C18 help form `<stored> -> <newest + 1>` | Undo | README rule, literally: `<stored>` = version of the stored record, `<next>` = newest version + 1 |
| S14 | C18 source kind `N2-over-chain` is written from the template, also for the fixture names; no new file under `slice2/` | Repair | Chose a generated source over a new fixture file, because the repair scope excludes `slice2/`. Commits the fixture form of C18 to the template text; the guard test does not cover it |
| S15 | C1b, C17, C18 snapshots are written per test, also for the fixture names; no new file under `stored/` | Undo | Same pattern as C7 (`v1-untyped`) |
| S16 | `help_line` takes the stored and newest version; old calls keep `1 -> 2` | Undo | Default arguments; C1, C1b and C15 are unchanged in effect |

## Slice 2 GREEN

**Scope.** Compiler, `run.py`, GEN overlay copies, change table. No test assertion changed, except the three TABLE rows of `overlay_diff_test.py` (Repair below, decided by the main agent). No commit.

### Steps

1. Compiler CLI: `beaml-spike SOURCE.beaml [--stored SNAPSHOT.jsonl]`. A source with an `effect` and no `--stored` fails with `stored TYPE VERSIONS unknown`, after the parse, TYPE and service checks (C16).
2. Lexer: version number token. Parser: `migrate T a -> b { rename old -> new }`. Check: steps `1 -> 2 -> ...` without gaps, `new` in version `b`, `old` not in it. Old TYPE VERSIONS are derived backwards from the `interface`.
3. Path check: every RECORD SNAPSHOT line is read (no body bytes). Each distinct (operation, name, version, fingerprint, fields) must have the EFFECT output TYPE name and the fingerprint of the derived version with the same number. Errors per README text; an older stored version also shows its derived version (C4).
4. Generated `record/3` writes `type` (name, newest version, sorted fields, fingerprint). Generated decode: one block per `rename` step in chain order; the old key is read only when the current key is missing, and it is consumed (C11, C12, C13).
5. SHA-256 and a small JSON reader are in the compiler; it still has no dependencies.
6. `run.py`: the GEN build passes `--stored stored/empty.jsonl` and writes `stored-snapshot.json` (path, SHA-256). GEN copies: lines 141, 92, 51 pass `--stored` with `stored-empty.jsonl` (new empty file in the GEN overlay). README change table, `assertion-changes.json` and TABLE have the three rows.

### Runs (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `cargo test --offline` (0001) | 0 | unit 9/9, `cli` 14/14 |
| `tests/stored_types_test.py` | 0 | 29/29 |
| `tests/slice2_replay_test.py` | 0 | 9/9; `results/20261106T153231809212Z`; strict compile 0 for the three case trees |
| `tests/arms_test.py` | 0 | 16/16; `results/20261106T153328146003Z` |
| `tests/overlay_diff_test.py` | 0 | 3/3 |
| `tests/drift_test.py` | 0 | 3/3 |
| `0003-source-linked-replay/run.py` | 0 | `pass`, `0003/results/20261106T154124026960Z` |
| `0004-generated-replay/run.py` | 0 | `pass`, `results/20261106T154230007902Z` |

**[Verified] S10.** The real L0 capture of the base GEN build (`results/20261106T153328146003Z/gen/live/L0`) has the same `type` value and the same key set as `stored/v1.jsonl`.

### Test SHA-256 before and after

| File | Before | After |
| --- | --- | --- |
| `0001/tests/cli.rs` | `2354c81a…8d8b` | unchanged |
| `tests/stored_types_test.py` | `a69b8886…d3257f` | unchanged |
| `tests/slice2_replay_test.py` | `a77f32ed…c809dad` | unchanged |
| `tests/arms_test.py` | `0298a9d9…f9b9bdf2` | unchanged |
| `tests/drift_test.py` | `87d309d1…5d76f7` | unchanged |
| `tests/arm_tree.py` | `ff23d780…ae6b1d` | unchanged |
| `tests/overlay_diff_test.py` | `6fe091cdb018f9479fd15be6400cbfc1870bddc10ba0f52452d29ba68b5d76f7` | `3bfb0a6186462dfe930de6b40195da503a1d7ce6f9091050071b23f6a650a56a` |
| GEN copy `replay_run_test.py` | `34e27bcd…87bcae` | `80803eb94b77342147ef1aa04c57ecc07b1225b9e4beee008c90761a449b5f7a` |
| GEN copy `response_capture_test.py` | `12b7f00f…e99381` | `1c243fce95d8989221e35ca4c0fb71f9e2ada20fc482ffe58a264324cf5974ad` |
| GEN copy `trace_lookup_test.py` | `6a703619…b9ebe` | `1bba3d32e767ffe095108283bc24b0ec6a6796246e3970c7dab1f94620f85d56` |

### Decisions (Decision4, slice 2 GREEN)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| G1 | Add 3 TABLE rows to `overlay_diff_test.py` | Repair (main agent) | Chose add 3 TABLE rows. Over: leave copies unchanged. Because: the copies only gain a harness argument, and the table must list every changed line. Commits the change table to slice 2 rows |
| G2 | Changed copy lines are 141, 92, 51, not 140, 91, 50 | Undo | The README gap named the first line of each call; the argument list is on the second line |
| G3 | Empty snapshot of the copies: new file `stored-empty.jsonl` in the GEN overlay | Undo | Over `/dev/null`: a real empty RECORD SNAPSHOT, as in `stored/` |
| G4 | SHA-256 and JSON reader written in the compiler | Repair | Chose own code over the `sha2` and `serde_json` crates. Because: the compiler has no dependencies and builds offline. Commits the compiler to about 250 more lines |
| G5 | A record of an operation with no `effect` in the source is a compile error | Repair | Chose an error over ignoring the record. Because: no generated runner can read it. Over: README "fails only for a missing path". Commits a source that drops an EFFECT to an empty or cleaned snapshot |
| G6 | A stored TYPE name other than the EFFECT output TYPE has no path | Undo | README path check names (name, version, fingerprint) |
| G7 | Malformed `type` key, invalid JSON line, version 0: compile error with path and line | Undo | Same form as C7 |
| G8 | Stored version older than the newest: message compares it with its derived version and gives a chain help line; same or newer: compares with the newest and gives the README `rename` help | Undo | Message text only; tokens per README |
| G9 | Added field only (C5): help names the `add` step and says only `rename` exists | Undo | O4 text; `add` is out of scope |
| G10 | `--stored` given to a source without `effect`: snapshot is read and checked | Undo | No test path; payments output stays byte-identical without `--stored` |
| G11 | Chain errors: gaps, empty step, `new` not in the next version, `old` still in it | Undo | Out of scope in README; an error is safer than a wrong derivation |

## Slice 2 final review repair

**[Observed] Defect (high).** The generated decode applied every `rename` step of the MIGRATE CHAIN by key presence and ignored the TYPE VERSION.
- Name reuse (`Payment { phase status }`, steps `status -> state`, `code -> status`, `state -> phase`): a current v4 body gave `PaymentError{reason: "decode"}`, live and in a REPLAY RUN.
- Rotation (`Payment { a b }`, steps `a -> c`, `b -> a`, `c -> b`): a current body decoded with `a` and `b` swapped (live wrong accept).

**Repair.** The decode reads a body as the TYPE VERSION of its RESPONSE RECORD. A record of version n gets the steps n -> n+1 -> ... -> newest in chain order. A live body is the newest version and gets no rename. `Replay.run` passes `record["type"]` to the decode. A TYPE without a MIGRATE CHAIN keeps the slice 1 decode (payments output byte-identical, `cli.rs` check passes). The rule "stored record for an operation without an EFFECT fails the build" is unchanged.

### New tests

| File | Cases |
| --- | --- |
| `tests/stored_types_test.py` | C19 reuse, C20 rotation: compile with v1+v4 and v1..v4; Fixture and Template (random names). Fixture guard checks the two new sources |
| `tests/slice2_replay_test.py` | C19/C20 x fixture/random names: strict compile; live current body decodes exactly to current fields, record `type` v4, no unknown keys; v1, v2, v3, v4 records replay to the current values |
| `slice2/reuse/orders.beaml`, `slice2/rotation/orders.beaml` | New fixture sources |

Expected values come from a carrier table in the test (field that holds X and Y per version), not from the compiler.

**[Verified] RED** (`final-review-red.log`, `results/20261106T160628867615Z`): 8 of 12 fail, only for the defect. Reuse v4 and live: decode error. Rotation v4 and live: `a` and `b` swapped. v1 to v3 pass before the repair. Strict compile passes.

### SHA-256

| File | Before | After |
| --- | --- | --- |
| `tests/stored_types_test.py` | `a69b8886e8e8b032822e45b02a8caac84f19cbf4b81a3b9855d464845bd3257f` | `d22775b2e23e381280b4f12ae8a974d58377edc3a41f3db4433301fe757d33f4` |
| `tests/slice2_replay_test.py` | `a77f32ed853765ade5351aafdb811051da7d44c45534b4a68b638d535c809dad` | `ca07a09bd6369a00fd95d4725ded943338aa8e01be7a616f48daebadd9db57f6` |
| `0001/src/main.rs` | `8321971cd4a684ee8cf53eceb55adbd4693b6b5db46a24f9eef8bc4ac4ff8994` | `e90df458bd88bc437d5f72bad44ca4d345bceafc3c961fbaf0da43f38c403b01` |
| `0001/tests/cli.rs`, `arms_test.py`, `arm_tree.py`, `drift_test.py`, `overlay_diff_test.py` | unchanged | unchanged |

### TEST (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `cargo test --offline` (0001) | 0 | 9 + 14 passed |
| `tests/stored_types_test.py` | 0 | 33/33 |
| `tests/slice2_replay_test.py` | 0 | 21/21; `results/20261106T160821878019Z` |
| `tests/arms_test.py` | 0 | 16/16; `results/20261106T161015448243Z` |
| `tests/overlay_diff_test.py` | 0 | 3/3 |
| `tests/drift_test.py` | 0 | 3/3 |
| `0003-source-linked-replay/run.py` | 0 | `pass`, `0003/results/20261106T161756863262Z` |
| `0004-generated-replay/run.py` | 0 | `pass`, `results/20261106T161859486046Z` |

### Decisions (Decision4, final review repair)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| F1 | Decode by record version, not by key presence | Repair (main agent) | Chose version. Over: key presence (README decision row "Decode reads the old name ... as a fallback"). Because: key presence decodes reuse and rotation wrong. Commits live traffic to the newest names only; the README row is now out of date |
| F2 | Record without a `type` key: newest version | Repair | Chose newest. Over: decode error. Because: C7 rejects untyped records at compile time; slice 1 behaviour stays. Commits an untyped old body to a decode error, not a wrong accept |
| F3 | Record `type` with another TYPE name or a version outside 1..newest: typed decode error | Undo | Same error as a body without a path |
| F4 | In each step, `old` is read as `new` only without `new` (C12 kept) | Undo | Keeps the hint rule of C12 |
| F5 | Version dispatch only for a TYPE with a MIGRATE CHAIN | Repair | Chose chain-only. Over: dispatch for every TYPE. Because: payments output must stay byte-identical. Commits two decode forms in the compiler |
| F6 | Runtime random-name variants run in arm trees (template source in a temp dir) | Undo | Test-only; 4 more release builds |
| F7 | New fixture sources under `slice2/`; snapshots written by the tests | Undo | Same pattern as `repair_records` |

## Slice 3 plan repair and RED

STATE README: revision 7.1 (slice 3 section, front matter and one plan history line only).

### Plan changes (README revision 7.1)

| # | Fault (fresh check) | Change |
| --- | --- | --- |
| 1 | HIGH: the body value won over the `add` constant (DL-047 form) | DL-048 in "Generated decode (slice 3)": `add` always puts the constant; a body key with the same name goes into `unknown_keys`; a `rename` always removes the old key from the working body. New `unknown_keys` rule (C11 and C12 unchanged). D8 expects `reference: "pre-v2"` and `unknown_keys == ["reference"]`. New case D11b. Decision row superseded. |
| 2 | MEDIUM: K2, K4 and the help row for a non-String added field looked unreachable (`main.rs` EFFECT check, String output fields only) | Check order stated: K checks run in `derive_versions`, which `Checker::new` calls before `effects()`. K2 and K4 stay. The help row is removed: an added field is in the newest TYPE VERSION, and `effects()` rejects a non-String newest field before `--stored`. |
| 3 | MEDIUM: a `drop` with a declared TYPE had no replay case | `drop` takes `String` only. K6 now covers every non-String TYPE (`String fields only`). D7 and D7b are source errors (K6). The help table row for a removed non-String field says `drop supports String fields only` (new case D5c). |
| 4 | MEDIUM: help lines with two changes untested | D2b (two `add`, sorted by field name), D5b (`rename` help line plus `drop`/`add` line, DRIFT N source). |
| 5 | Minor | `unknown_keys == []` stated for D11 v1, v2, v3 and D14 (replay and live). |

### RED tests

New files (pattern of slice 2: Fixture class with fixture files, Template class with random TYPE names, field names and constants; a random constant holds `"`, `\` and `é`; expected values from tables in the tests).

| File | Cases | RED result |
| --- | --- | --- |
| `tests/slice3_types_test.py` | D2, D2b, D3, D5, D5b, D5c, D6, D7, D7b, D12, D13, D15, D15b, K1–K12 (K7 two forms), builds D1, D4, D11, D14; fixture guard | 59 run, 56 failures (54 tests + 2 K7 subtests), 0 Python errors. Pass: D3, D6 (controls, as C6), fixture guard |
| `tests/slice3_replay_test.py` | D1, D4 (replay and live), D8, D9 (missing and `7`), D10 (live), D11 v1–v3, D11b, D14 (replay and live), strict build; fixture and random names | 23 run, 22 failures, 0 Python errors. Pass: control hashes unchanged. `results/20261106T164321602324Z` |

Fail reasons (current compiler):

- Sources with `add` or `drop`: `unsupported migrate step (slice 2 supports rename only)` (builds D1, D4, D11, D14; D7, D7b, D12, D13, D15, D15b; K1–K7, K11; every replay tree).
- D2, D2b, D5, D5b, D5c: the error exists, but the asserted `help` line (`add ... = <constant>`, `drop ... : String`, `drop supports String fields only`) is missing.
- K8: `a step needs at least one rename` (token `at least one rename, add or drop` missing). K9, K10, K12: the slice 2 parse message, without `expected ','`, `expected rename, add or drop`, or `add` and `drop`.

Fake checks (scratch only, not in the repository):

- A mocked harness that decodes by the README rule passes all 22 replay and live tests: the test logic runs without Python errors.
- A mocked decode that ignores `add` and `drop` (slice 2 decode) fails D1, D4, D8, D9, D11, D11b and D14, with fixture and random names. Inferred, not run: a decode where the body value wins fails D8 and D11b, because the table expects the constant.

### SHA-256 (new files; changed: README only)

| File | SHA-256 |
| --- | --- |
| `tests/slice3_types_test.py` | `5b1f0d53922dfba874b46c33ee01cbef9f24c2fee2f476bf966ddf350a561f4e` |
| `tests/slice3_replay_test.py` | `6f310c41f7271686dce924dc5edeceb002c0d82a951c24d534793cd170714cf6` |
| `slice3/R-add/orders.beaml` | `6a69e59710c35b45b654ac8a58c349a29b1199d6f1db015403756c792df88055` |
| `slice3/R2/orders.beaml` | `3dd37d0d519244b3bdcd6cec45736af512991221d3ae2f74a42d592a96a6b28f` |
| `slice3/D-drop/orders.beaml` | `8165ff376514f99e6742419ae270d54d36bc1c4232506deea65cb5ed5f097df4` |
| `slice3/D/orders.beaml` | `c44b187ec4fee7ec7bcc9db5725115b7f8cab2756d2fda5213bc592809323790` |
| `slice3/M/orders.beaml` | `ff13cbc02825bd7b0dc61ca373e91b7f0c46783b32eced94d6f2abeccb176f56` |
| `slice3/M-nodrop/orders.beaml` | `2c58cf7f0e4b51691628ea03ec60cd004b15230112370324f86d1d733f14172e` |
| `slice3/Z/orders.beaml` | `9289b51326867f06335e4b0489a8b01c74bf060b192acd08afd0712a06509fef` |
| `slice3/D15/orders.beaml` | `138fc21653baf840af2945c2aa3d0c521cc82734f0068c1a095863c57e3de4de` |
| `slice3/D7/orders.beaml` | `eb1bad739058486ce1ecdd54f4ed534757c3cc081ac179109473c4c6135863c4` |
| `tests/stored_types_test.py`, `tests/slice2_replay_test.py`, `0001/src/main.rs`, `run.py` | unchanged |

### Verification (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `cargo test --offline` (0001) | 0 | 9 + 14 passed |
| `tests/slice3_types_test.py` | 1 | RED as above |
| `tests/slice3_replay_test.py` | 1 | RED as above |
| `tests/stored_types_test.py` | 0 | OK |
| `tests/slice2_replay_test.py` | 0 | 21/21; `results/20261106T164415019578Z` |

### Decisions (Decision4, slice 3 plan repair and RED)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| P1 | `add` constant always wins; body key into `unknown_keys`; `rename` removes the old key | Repair (DL-048, decided by the main agent) | Applied as decided |
| P2 | K checks before the EFFECT output check; keep K2, K4; remove the non-String `add` help row | Repair | Chose the existing order (`derive_versions` before `effects()`). Over dropping K2 and K4. Because the order needs no extra code and keeps a precise message; no source reaches the help row. Commits GREEN to keep the K checks in `derive_versions` |
| P3 | `drop` takes `String` only (K6 widened; D7 and D7b are source errors; new D5c) | Repair | Chose `String` only. Over a declared-TYPE `drop` with a replay case. Because the decode checks `String` values only; a nested decode is not cheap, and an untested claim is not honest. Commits record and `enum` `drop` to a later slice. The decision log text of DL-044 must change (main agent) |
| P4 | `unknown_keys` = keys the decode does not read, sorted, each once | Undo | Local to the generated decode; keeps C11 and C12 |
| P5 | D5b uses the DRIFT N source; D11b expects `state` from the body (C12) and `status` from the constant | Undo | Reuses the slice 2 rule; no new rule |
| P6 | K fixtures come from the template with fixture names (no files); main cases have files in `slice3/` | Undo | Slice 2 pattern (`GENERATED_KINDS`) |
| P7 | Replay tests import the slice 2 helpers (`counts`, `accepted`, `decode_rejected`) | Undo | No copy; slice 2 files unchanged |
| P8 | R+add field order `order_id status reference` (README text aligned) | Undo | Same order as DRIFT R; R+add is R plus the chain |

## Slice 3 RED repair

Repairs four medium gaps of the fresh RED check. No compiler change. README unchanged.

### Cases

| Gap | Change | RED result |
| --- | --- | --- |
| M1 | Build `z` now uses RECORD SNAPSHOT `Z-all` (records of version 1 and 3, one fingerprint). New replay row D14-v3: body `{k, o: "done"}` → `o: "done"`, `unknown_keys == []`. New compile case: D14 build with `Z-all` | Fail: `unsupported migrate step` (Z build) |
| M2 | New source RR (`slice3/RR/orders.beaml`): `{rename o -> t}`, `{rename x -> o}`; snapshot `RR-v1` `{k, o, x}`. Replay D11c: v1 body `{k, o: "o-old", t: "t-kept", x: "x-new"}` → `{k, t: "t-kept", o: "x-new"}`, `unknown_keys == [o]` (README rule: a key that a `rename` removes unread). New compile case: D11c build | Build passes (rename only, slice 2 compiler). Replay fails for the DL-048 reason: the current decode keeps `o`, gives `o: "o-old"` and `unknown_keys == [x]` |
| M3 | D13 and D15 assert `the MIGRATE CHAIN of T must derive version 2` / `... version 1` | Fail: `unsupported migrate step` |
| M4 | `random_names(order)` sorts random names into a given role order. D2b Template runs orders `xc` (declaration order) and `cx` (reverse). New D2c ("other counts" row): source `{k, x}` no chain, snapshot `{k, o, c}`; help `migrate T 1 -> 2 { drop c: String, drop o: String, add x: String = <constant> }` (groups sorted); Template orders `cxo`, `oxc`, `xco`. Each order is a subTest; names printed on failure | Fail: help line missing |

### Verification (serial)

| Command | Exit | Result |
| --- | --- | --- |
| `tests/slice3_types_test.py` | 1 | 65 run, 63 failures (incl. subtests), 0 Python errors. Pass: D3, D6, D11c build (fixture, template), fixture guard |
| `tests/slice3_replay_test.py` | 1 | 27 run, 26 failures, 0 Python errors. Pass: control hashes. `results/20261106T165027202655Z` |
| `cargo test --offline` (0001) | 0 | 9 + 14 passed |
| `tests/stored_types_test.py` | 0 | OK |
| `tests/slice2_replay_test.py` | 0 | OK; `results/20261106T165130356970Z` |

### SHA-256

| File | SHA-256 |
| --- | --- |
| `tests/slice3_types_test.py` | `c4266ffc25de392856254b8675d14325cde1ef29e710e1c3d41f2547e6445f1c` |
| `tests/slice3_replay_test.py` | `a2080d9d88a34ebd8baf303dc4425064bfc49eb62f9cfbae26cf481c53c841a0` |
| `slice3/RR/orders.beaml` | `e7f266a378b699406b82fdda84af194c9fe79276fcb35854cb2dd4f4b8a9c129` (new) |
| other slice 3 fixtures, slice 2 tests, `0001/src/main.rs` | unchanged |

### Decisions (Decision4)

| ID | Decision | Class | Choice and reason |
| --- | --- | --- | --- |
| R1 | Build `z` replaces snapshot `v1` by `Z-all`; the D14 `v1` compile case stays | Undo | Both records need a path in the replay build |
| R2 | D11c expects `unknown_keys == [o]`, read from the README `unknown_keys` rule | Undo | README rule gives the list; no deviation from the task |
| R3 | D11c passes its build on the slice 2 compiler; the replay is the RED | Undo | Rename-only chain; the gap is in the decode |
| R4 | New case IDs D2c, D11c, D14-v3 are not in the README case table | Repair | Chose test-only IDs. Over a README revision now. Because the rows test existing README rules. Commits the main agent to add them to the README case table |
| R5 | D2c source comes from the template (no fixture file), as the K cases | Undo | Pattern P6 |
| R6 | Template source directory keyed by kind and names hash | Undo | The sort-order subtests change the names inside one test |
