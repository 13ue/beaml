# Slice 6b step 5: notes

## Solve

What this phase takes from the plan (step 5, D6B-25 to D6B-28), DL-086, the step 4 ledger ("Step 5 after S4") and the step 3 review (G13):

- Baseline: commit `80bd33cd`. The compiler was built from a `git archive` of that commit in a scratch directory, because another worker (step 4 GREEN) edits `main.rs` now. The test runs with `BEAML_SPIKE` set to that binary.
- **[Observed]** Today the parser reads a pipe only after a whole clause body (`main.rs`, clause parse). `expression()` rejects `Node::Pipe` with `a pipe is only supported as a whole function body`. `emit_node` has `unreachable!` for `Node::Pipe`.
- **[Observed]** Today a nested pipe fails in the parser with `expected ',' at byte N`, not `expected ')'` as the plan says. The parser reads `p` as the argument and then wants `,`.
- **[Observed]** Today a pipe step must be a `fn` signature or an EFFECT. A variant step gives `unknown pipe step: V`.
- **[Observed]** Today every `fn` with a pipe body has one clause (`a function with a pipe body has one clause in slice 1`). Step 4 R1 keeps this for EFFECT pipes; step 4 GREEN may loosen it for pure pipes (step 4 R2).
- **[Inference]** Step 4 GREEN builds a variant step and the whole-body pipe in an enum constructor clause (step 4 S4). So the step 4 corpus clause is not a step 5 RED. It stays in `slice6_enum_test.py`.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| S1 | Undo | All RED cases go in `slice6_pipe_test.py`. The Rust unit test `pipe_in_any_expression` waits for GREEN. | Add the unit test to `main.rs` now | RED does not change the production file (task; step 3 and 4 S1). |
| S2 | Undo | One fixture `slice6/pipe/pipe.beaml` holds all accept cases. | One source per accept case | The plan names one fixture. One runtime run gives all values. |
| S3 | Undo | The plan corpus clause (`reason \|> DeclineReason \|> Declined`) is not in this fixture. | Repeat it here | Step 4 S4 and `slice6_enum_test.py` cover it. After step 4 GREEN it cannot fail (step 4 red-review, "Step 5 after S4"). |
| S4 | Undo | The plan example `build(p \|> prepare, x)` gets a second parameter `x: String`. | Keep `x` free | A free `x` is `unknown variable: x`. |
| S5 | Undo | A pipe in a record field value ends at `,` and at `}`. The fixture tests both (`Pair`, `box`). | Only `,` and `)` | Record literals separate fields with `,`. D6B-25 names `,` and `)` only; `}` is the same rule in another bracket. |
| S6 | Repair | **Chose:** D6B-27 text `error: fn F: a nested pipe has the EFFECT step S` or `error: fn F: a nested pipe has the failing step S`, then `  help: make the pipe the whole body`. **Over:** a text without the step name. **Because:** the step name tells which step to move. **Commits us to:** GREEN emits these exact texts. | Text without step name | D6B-27 fixes only the `help:` line. |
| S7 | Undo | The nested failing-step reject uses a `fn` whose `!` list has the failure. | A `fn` without `!` | Then nesting is the only reason for the error. |
| S8 | Undo | Variant step texts reuse the `fn` step texts: `pipe step V must take one argument` and `type mismatch in pipe step V: expected T, got U`. | New variant texts | Same rule as for a `fn` step (D6B-26). |
| S9 | Undo | The `!` rule reject is a pure several-clause `fn` with `! Other`, a list without `IsZero`. Existing text. | A whole-body pipe in a one-clause `fn` | The one-clause case passes today (`bad/undeclared_failure.beaml`). The several-clause case is new in step 5 and fails today. |
| S10 | Undo | The lowercase non-`fn` step reject is a variable `x` as a step in an argument pipe. Existing text `unknown pipe step: x`. | Whole-body `\|> nope` | The whole-body form passes today (`bad/unknown_pipe_step.beaml`, guard S13). |
| S11 | Undo | Build assertions: the plain call lines of `g` and `cat` and the `with` line of `pick`. | Assert every line | `g` shows nested calls, `cat` shows the precedence, `pick` shows the `with` (D6B-28). The runtime run checks the rest. |
| S12 | Undo | Byte guard: stdout sha256 of `arms/gen/orders.beaml` and `slice2/reuse/orders.beaml` (with `--stored stored/empty.jsonl`) from the baseline compiler; `payments.beaml` against `tests/payments.generated.snapshot`. | Golden `.ex` files | Hashes keep the test short. A copy of `orders.beaml` in another directory gives the same hash; the output holds no path. |
| S13 | Undo | Guard: the five `bad/*.beaml` files keep their exact baseline texts. | Name checks only (`cli.rs`) | The plan risk: step 5 changes every pipe AST; the first error of each file must stay. |
| S14 | Undo | Runtime checks use the step 3 harness without a ProbeSupport stub. | The step 2 harness with a stub | D6B-28: a pure module must not call ProbeSupport. |
| S15 | Undo | Expected runtime values were checked once on the baseline with a call-form copy of the fixture (`build(prepare(p), x)`, one-clause `pick1`). All 7 checks were true. | No check | A wrong expected value would give a false RED. The copy is in the scratch directory only. |

### Points the plan does not settle

- **[Unknown]** A nested failing step in a `fn` without a matching `!`: D6B-27 text or the `!` rule text first. No test. Class Undo (a message order only).
- **[Unknown]** `x |> f + y`: steps are bare names, so this is a parse error or `f + y` as a step. No test. Class Undo.
- **[Unknown]** A nested pipe inside a pipe head, or a pipe inside a variant call argument (`Declined(r |> paren)`). Not tested; the same parse rule. Class Undo.
- **[Unknown]** A nested pipe with only a 1-input constructor step that cannot fail (`F(r)` form, `r |> F`). Not tested. Class Undo.
- **[Open, OWNER]** A pipe that reaches an EFFECT only through another `fn` has no span (step 3 review, G13). Kept as today. A change is a change of D6B-28. Class Repair at least; the OWNER decides.
- **[Inference]** The variant rejects (S8) may already pass after step 4 GREEN, if step 4 uses the same texts. Then they are guards for step 5. Class Undo.
- **[Inference]** The plan "today" text `expected ')'` is wrong; the actual text is `expected ','`. Class Undo (docs).

## RED

Command (repository root): `BEAML_SPIKE=<scratch>/base80bd/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_pipe_test.py`. Full output: [red-output.log](red-output.log).
Baseline compiler: commit `80bd33cd`, `cargo build --offline` of a `git archive` copy. Toolchain: cargo 1.94.0, rustc 1.94.0, Elixir 1.18.1 (OTP 27), Python 3.13.12.
Inputs: `slice6/pipe/pipe.beaml` sha256 `54ad7b05a5974ea1dfcb9db8d5fb1efba661a34d22b35ffff74c05841504464f`; `tests/slice6_pipe_test.py` sha256 `523b2405657f94df0c9fb0a05e1056d7eb889d69370c5062d31fda5d424061c8`.
Result: 11 tests, 9 FAIL, 2 pass (guards S12, S13). Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_pipe_fixture_compiles_to_plain_calls` | exit 0, plain call lines, `with` line | `expected ',' at byte 632` | No pipe in an argument in the parser. |
| `test_runtime_pipe` | 9 subtests PASS | stops at build, same text | Same. |
| `test_effect_step_in_an_argument_pipe` | S6 EFFECT text | `expected ',' at byte 944` | No nested pipe, no D6B-27 check. |
| `test_failing_step_in_an_argument_pipe` | S6 failing text | `expected ',' at byte 290` | Same. |
| `test_failing_step_without_a_matching_failure` | `pipe step NonZeroInt can fail with IsZero, which is not in the ! list of pick` | `a function with a pipe body has one clause in slice 1: pick` | One-clause rule for every pipe. |
| `test_lowercase_non_fn_step_in_an_argument_pipe` | `unknown pipe step: x` | `expected ',' at byte 189` | No nested pipe. |
| `test_variant_step_without_a_payload` | `pipe step Approved must take one argument` | `unknown pipe step: Approved` | No variant step. |
| `test_variant_step_with_two_payloads` | `pipe step Two must take one argument` | `unknown pipe step: Two` | Same. |
| `test_variant_step_with_a_wrong_payload_type` | `type mismatch in pipe step Declined: expected String, got Int` | `unknown pipe step: Declined` | Same. |
| `test_bad_fixtures_keep_their_texts` | 5 exact texts | pass | Guard S13. |
| `test_effect_fixture_outputs_stay_byte_equal` | 3 byte-equal outputs | pass | Guard S12. |

### RED checks

- Every failure is a missing behavior, not a setup failure. The baseline compiler builds, every case reaches the compiler, every message is a compiler message.
- Each reject asserts the full message, so today's texts give no false pass.
- The action event check runs on every compile (no source text, no path).
- `main.rs` and `slice6_enum_test.py` were not changed by this phase. `run.py` was not run. No result directory was touched. No commit.

## Limits

- The variant rejects may pass after step 4 GREEN (see the points above). They were not run against the step 4 GREEN compiler, because that work is not finished.
- The span loss of an indirect EFFECT pipe is not tested. It is an OWNER question.
- `cargo test` was not run: this phase did not change the production file.
