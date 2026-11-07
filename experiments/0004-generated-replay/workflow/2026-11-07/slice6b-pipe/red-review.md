# Slice 6b step 5: RED review

Fresh-context RED review. Not a Devil's Advocate round.
Inputs: [spec.md](spec.md), [notes.md](notes.md), [red-output.log](red-output.log), plan step 5 and D6B-25 to D6B-28 in [decisions.md](../slice6b-plan/decisions.md), [step 4 red-review.md](../slice6b-enum/red-review.md) ("Step 5 after S4"), [step 4 notes.md](../slice6b-enum/notes.md) (R1, R2), DL-086, `tests/slice6_pipe_test.py`, `slice6/pipe/pipe.beaml`, `main.rs` at commit `80bd33cd`.

## Verdict

**Pass. No block.** Two medium objections. Record them before step 5 GREEN starts.

## Rerun

- Baseline: `git archive 80bd33cd experiments/0001-syntax-to-beam` into the scratch directory, `cargo build --offline`. The live `main.rs` was read only. It was not built. `run.py` was not run.
- Command (repository root): `BEAML_SPIKE=<scratch>/rr5/experiments/0001-syntax-to-beam/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_pipe_test.py`.
- Toolchain: cargo 1.94.0, Elixir 1.18.1 (OTP 27), Python 3.13.12.
- Input hashes are equal to notes.md: `pipe.beaml` `54ad7b05...464f`, `slice6_pipe_test.py` `523b2405...61c8`.
- **[Observed]** Result: 11 tests, 9 FAIL, 2 pass (S12, S13). Same tests and same texts as `red-output.log`.

## Checks

| Point | Result |
|---|---|
| Failures come from the compiler | **[Observed]** Every FAIL shows a compiler message on stderr (`expected ','`, `unknown pipe step`, one-clause text). No setup error. |
| Expected build lines | **[Observed]** A call-form copy of the fixture (`build(prepare(p), x)`, `join(paren(a + b), c)`) on the baseline gives exactly the asserted `__beaml_g` and `__beaml_cat` lines. A one-step `with` line ends in ` do`; only clause `"a"` of `pick` gives it. |
| DL-086 | Covered: pipe in a call argument, in a record field value, in a constructor clause; a variant as a step (`box`); a constructor as a step (`pick`). The `!` rule stays (S9). |
| D6B-25 precedence | **[Verified]** `a + b \|> paren` is `paren(a + b)` is the plan rule (D6B-25, "the Elixir order"). It is also the expected rule: in Elixir, `+` and `<>` bind stronger than `\|>`. The runtime case `cat` separates both readings (`"(ab)-c"` against `"a(b)-c"`). No doubt. |
| D6B-27 texts | The step name in the text is an S6 Repair, not plan text. The two sources are TYPE-correct (`finish` takes `Payment`; `keep` takes `NonZeroInt`; the `!` lists match). So only the nesting rule can reject them. |
| Reject false pass | **[Inference]** None. `assert_rejected` compares exit code, empty stdout and the full stderr. An unrelated error after GREEN (for example `expected ','` from another place) gives another text and fails. |
| Runtime false pass | **[Inference]** None. Each case is a subtest. A missing result line is `None`, not `PASS`. A plain-call emit for `pick` without `with` gives `{:error, ...}` to `keep`; the input check raises, so the case fails. |
| Hash guards | **[Observed]** They pin the stdout of `arms/gen/orders.beaml` and `slice2/reuse/orders.beaml` (empty RECORD SNAPSHOT) and `payments.beaml` against its snapshot. These are the EFFECT whole-body pipes with spans that D6B-28 keeps. The slice 3 to 5 fixtures are in the pass rule through their own tests. |

## Objections

**O1 · Medium · Four RED tests are already step 4 work.**
- **[Observed]** The live `main.rs` of step 4 GREEN has the variant step check with the exact S8 texts (`pipe step V must take one argument`, `type mismatch in pipe step V: ...`). Its one-clause rule now applies only to a pipe with an EFFECT step (step 4 R2). The `!` check is in the same step loop.
- **[Inference]** After step 4 GREEN, these tests pass before step 5 starts: the three variant rejects and `test_failing_step_without_a_matching_failure`. The `pick` `with` line and the four `pick` runtime cases can also pass then. The genuine step 5 RED is the nested pipe: the parse and plain-call emit (`g`, `last`, `cat`, `Pair`, `box`), the two D6B-27 rejects and the nested `unknown pipe step: x`.
- Wrong outcome: the ledger says "9 of 11 fail" against a base that step 5 does not build on. Step 5 GREEN can count step 4 behavior as its own proof. No false pass, because each assertion stays exact.
- Smallest test: after the step 4 GREEN commit, rerun `slice6_pipe_test.py` against that commit. Mark each test that passes as a guard in notes.md. Class Undo.

**O2 · Medium · D6B-27 is tested only in a call argument.**
- Wrong outcome: GREEN can put the D6B-27 check in the call-argument path only. Then `Box { state: n |> NonZeroInt }` compiles to plain calls. The field gets `{:ok, ...}` or `{:error, ...}` instead of a value, without a compile error. `elixirc` does not see this; no runtime case reaches it.
- Smallest test: one reject, a failing step in a record field value: `type B { v: NonZeroInt }` + `fn w n: Int -> B ! IsZero = B { v: n |> NonZeroInt }`, text `error: fn w: a nested pipe has the failing step NonZeroInt` + help line. Add it in the RED repair, or as the first GREEN test. Class Undo.

## Open Undo points (from notes.md, accepted)

- Message order for a nested failing step without a matching `!`: no test.
- `x |> f + y`: no test. With bare-name steps, a parse error is the expected result.
- Pipe in a pipe head, pipe in a variant call argument, nested non-failing 1-input constructor step: no test.
- Plan "today" text `expected ')'` is wrong; the actual text is `expected ','`. Docs fix only.
- The `with` line assert fixes the `p0` binding form of step 3. This is a shape choice, not a plan rule.

## OWNER question (not changed)

- A pipe that reaches an EFFECT only through another `fn` has no span (G13, D6B-28). Class Repair at least. The OWNER decides.

## Limits

- The step 4 GREEN compiler was not run. O1 is from a read of the live, unfinished `main.rs`.
- `cargo test`, `cargo fmt` and `cargo clippy` were not run. RED does not change the production file.
- No production file or test was changed by this review.
