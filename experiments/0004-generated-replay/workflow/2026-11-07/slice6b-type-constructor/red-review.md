# Slice 6b step 3: RED review

Reviewer: a fresh-context agent. This is a normal RED REVIEW, not a Devil's Advocate.
Inputs: spec.md, notes.md, red-output.log, plan.md step 3, decisions.md D6B-07, D6B-11 to D6B-19 and D6B-28, plan-review.md (2) and (5), `slice6b-failure/notes.md`, DL-092, DL-093, `tests/slice6_constructor_test.py`, `slice6/constructor/*.beaml`, `src/main.rs` (`same_type`, `require_type`, `body`, `validate`, the `spans` flag, the call emit).

## Verdict

**Block.** Two high objections. Each needs two or three added reject lines. One medium note. After the repair, the RED passes.

## Rerun (observed)

- `python3 -B experiments/0004-generated-replay/tests/slice6_constructor_test.py`: 20 tests, 19 FAIL, 1 pass (the guard `test_effect_pipe_keeps_its_spans`). Same as red-output.log.
- Every failure is a compiler result: exit 1 with `expected '='` or `invalid function name`, or exit 0 with `ProbeSupport.span` in the output. No setup failure.

## Checks that hold (observed)

- Each reject asserts exit 1, empty stdout and the full text. Today's `invalid function name: NonZeroInt` cannot give a false pass. A GREEN that fails earlier for another reason gives another text, so the test fails (a false fail, not a false pass).
- No runtime subtest can be skipped silently. A build failure or an `elixirc` failure fails the test. A missing `PASS` line fails the subtest. `BODY_PIPE_CASES` is not empty (`piped_ends_in_failure`, `outer_passes_failure`, `outer_ok`).
- The expected values agree with the plan: plan.md step 3, Elixir shape and runtime check, gives `{:ok, %{"value" => 5}}` and `{:error, %IsZero{}}`.
- Reading stays free (D6B-18): `read` with a record pattern and `keep` with the nominal TYPE are accept cases (S13).

## S6: success map, failure struct

- **[Verified]** The plan sets the success value as a map with String keys (plan.md step 3). D6B-07 (Repair, already recorded) commits to "a record TYPE has two Elixir forms". Step 2 GREEN built failures as structs.
- **Assessment.** Acceptable for this step. Not a wrong outcome of step 3. The class is not Undo: the shape is host-visible (D6B-15) and D6B-07 is a Repair. Record S6 as "follows D6B-07 (Repair)", not as a free Undo.
- **[Inference] Pending question, not an objection.** The public wrapper checks the shape only. A host can call `BeamlSpike.keep(%{"value" => 0})` and get a NonZeroInt that never went through the constructor. DL-092 speaks about source code. Whether "the only way in" also binds the host call boundary is open. A struct success value does not close this gap alone. Class Migrate (OWNER). Do not block step 3 on it.

## D6B-28: are the three pure-pipe tests enough?

- **Yes, for this step (observed and inferred).**
  ⠀⠀↳ `run_runtime` asserts no `ProbeSupport` in the whole pure module (nonzero, plain, body), and `elixirc` runs without a stub.
  ⠀⠀↳ `assert_lines` compares whole stripped lines. A span form `p1 = ProbeSupport.span(...)` cannot equal `p1 = __MODULE__.echo(p0)`. So the EFFECT-module case catches a "module has an EFFECT, keep all spans" GREEN.
  ⠀⠀↳ The guard asserts the span on the pure step `orders.prepare` inside the EFFECT pipe. This catches a per-step rule. The slice 5 snapshot and `payments.generated.snapshot` keep the rest byte-equal.
- **[Observed]** No other `.beaml` fixture or inline Rust source has a pipe without an EFFECT step (all multi-line orders pipes contain `payments.*`). The worker's S3 claim holds.
- Not tested, low: a failing pure pipe (a `with`) beside an EFFECT. Drop.

## Objections

### 1. High: nominal TYPE is tested at one gate of three

- **Gap.** `same_type` has three paths that a structural twin can use: `require_type` (`validate` for a fn without `!`, call arguments), the pipe step check (`body`, `!self.same_type(&ty, input)`), and the `!` body check in `validate` (`!self.same_type(&ty, &clause.output)`). Both twin tests go through `require_type` on a body without `!`.
- **Wrong outcome.** A GREEN that puts the nominal rule in `require_type` and not in `same_type` passes all 20 tests. Then `fn same p: Plain -> NonZeroInt ! IsZero = p` compiles, and a `Plain { value: 0 }` becomes a NonZeroInt. DL-092 "the only way in" is broken silently.
- **Smallest test.** Two rejects with `HEAD + "type Plain { value: Int }\n"`:
  ⠀⠀↳ `fn same p: Plain -> NonZeroInt ! IsZero = p`, text `type mismatch: expected NonZeroInt ! IsZero, got Plain`.
  ⠀⠀↳ `fn keep x: NonZeroInt -> NonZeroInt = x` plus `fn same p: Plain -> NonZeroInt = p |> keep`, text `type mismatch in pipe step keep: expected NonZeroInt, got Plain`.

### 2. High: "its own constructor" and nested literals are not tested

- **Gap.** D6B-18: the literal is legal only in the clauses of its OWN constructor. The worker lists "literal of A inside the constructor of B" as an open Undo with no test. The only reject has the literal at the top of a lowercase fn body.
- **Wrong outcome.** Two GREENs pass all 20 tests: a check "inside any constructor clause", and a check on the top-level body node only. Both let `NonZeroInt { value: 0 }` in through a field of another record. This is the core DL-092 rule (Repair D6B-18), not an Undo.
- **Smallest test.** Two rejects with `HEAD + "type Box { n: NonZeroInt }\n"`:
  ⠀⠀↳ `fn Box x: Int -> Box = Box { n: NonZeroInt { value: x } }`, S8 text with `fn Box`.
  ⠀⠀↳ `fn make x: Int -> Box = Box { n: NonZeroInt { value: x } }`, S8 text with `fn make`.
- The first error is clear: `Box` is a valid constructor and the TYPES fit. Only the D6B-18 rule can fire.

### 3. Medium (note, no block): the call form `T(args)` is not tested

- **Gap.** Plan step 3 code: "a constructor as a whole-body pipe step and as a call". **[Observed]** The call emit today writes `__MODULE__.{name}({args})`, so `F(r)` gives `__MODULE__.F(r)`. After GREEN the function is `new_F_1`. The worker lists this as an open Undo.
- **Wrong outcome.** A GREEN without the call mapping passes all tests. A source with `F(r)` compiles to a call of an undefined function, or `elixirc` fails at the host.
- **Smallest test.** Runtime case: `type F { reason: String }`, `fn F r: String -> F = F { reason: r }`, `fn mk r: String -> F = F(r)`, check `BeamlSpike.mk("x") == %{"reason" => "x"}`.

## Open Undo points of the worker

- **Enum name in step 3.** Undo is correct. Step 4 replaces the text.
- **Literal of A in the constructor of B.** Not Undo. Raise to the D6B-18 Repair and test it (objection 2).
- **File name rule for a pure pipe.** Undo is correct. The `spans` flag (main.rs near the `service` match) also gates this error. Narrowing it is harmless.
- **Constructor without `!` as `F(r)`.** In the plan code list for step 3. Test it (objection 3, medium).
- **Order of EFFECT checks.** GREEN concern. The exact texts give a false fail, not a false pass. Undo is correct.

## Limits

- The test was rerun once. `run.py`, `cargo test`, clippy and the slice 3 to 5 tests were not run here.
- The bypass in objection 1 is inferred from the `main.rs` call paths. It was not built.
- No production file or test was changed.
