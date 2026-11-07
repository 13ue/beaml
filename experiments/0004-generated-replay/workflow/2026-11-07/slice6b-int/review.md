# Slice 6b step 1: review

Reviewer: a fresh-context agent. Type: REVIEW (pipeline step 7), not a Devil's Advocate.
Inputs: spec.md, notes.md, red-output.log, red-review.md, green-output.log, test-output.log, test-result.json, `../slice6b-plan/plan.md` step 1, `../slice6b-plan/decisions.md` (D6B-02, D6B-03, D6B-47), `git diff 713e8cdc..HEAD` on `main.rs`, `tests/slice6_int_test.py` and `slice6/`.

## Verdict

**PASS.** No critical, high or medium defect. One low note (A2b text).

## Step met (observed)

- Plan step 1 code list: `Node::Int` from `Token::Number`, `check_type`, `pattern`, `expression`, `normalized` (`int:<n>`), `useful` (`other-int`), `emit_node`, `__beaml_valid__` with `is_integer(v)`. All in the diff.
- First RED: Rust unit test `int_literals_and_patterns` has the three plan sources with exact text. It passes.
- Fixture `slice6/int/int.beaml` exists. The fixture test asserts the planned Elixir lines.
- Runtime: 13 of 13 subtests in `test_runtime` (the subtest names are in `RUNTIME_CASES`; the test fails on a missing line).
- Exclusions (D6B-03): `1 + 2` rejects, `-1` rejects, `Int` in an EFFECT input and output rejects. No change in `integrations/zed-beaml/`.
- `payments.beaml` output stays byte-identical (`slice5_syntax_test`, `payments_cli_output_stays_byte_identical`).

## Additions the step did not need

- `int_inside` (G1) and the unit test `effect_input_has_no_int_also_nested` (G3). They close red-review N1. This is a guard for D6B-03, not new language. Accepted.
- The G4 column check. The step test `test_int_literal_against_string_parameter` needs it. 9 lines. Accepted.
- Nothing else. No refactor, no new file in `src/`.

## G4: type mismatch text only with an `Int` column (observed)

Compiler: `experiments/0001-syntax-to-beam/target/debug/beaml-spike`. Each source in a scratch directory.

| Source | Exit | stdout | stderr |
|---|---|---|---|
| A1: `type R { a: String }` / `fn f r: R -> String = "r"` / `fn f "x" -> String = "x"` | 1 | empty | `inconsistent function signature: f` |
| A2: `fn f 0 -> String = "a"` / `fn f 0, s: String -> String = s` | 1 | empty | `inconsistent function signature: f` |
| A2b: `fn f 0 -> String = "a"` / `fn f s: String, 0 -> String = s` | 1 | empty | `type mismatch: expected Int, got String` |

- A1: acceptable. The text is the pre-6b text. The plan forbids a change of existing reject texts.
- A2: acceptable. Arity differs, first columns agree; the old arity text comes.
- A2b: **[Inference]** acceptable, low. The source is rejected, no code is emitted. The real fault is the arity, but the text names the first column. The `zip` in the G4 loop runs before the arity check. No wrong outcome: a reject stays a reject. A later text unification (notes, G4 limits) can put the arity check first.

## G6: is the `is_integer` import rule complete (observed)

Question: can a source use an `Int` literal with no `Int` in any TYPE or signature?

- Every literal is checked against an expected TYPE: a fn output, a record field, a call argument (fn signature or enum argument), a pipe step input, or a clause pattern (the pattern itself puts `Int` into the signature). `+` rejects `Int`. So an `Int` literal always has an `Int` in a signature or a TYPE.
- `__beaml_valid__(_, <<"Int">>)` is called only for TYPE fields, enum arguments, fn parameters and outputs, and EFFECT inputs and outputs (`Int` rejected there). The rule covers each of these.
- Adversarial sources:

| Source | Compile | `elixirc --warnings-as-errors` |
|---|---|---|
| G6c: `fn k -> String = 0 \|> f` / `fn f n: Int -> String = "a"` | exit 0, import and Int clause present | exit 0, `.beam` written |
| G6b: `enum E { A(Int) B() }`, `fn h -> E = A(3)`, `fn u A(0)`, `A(_)`, `B()` | exit 0, import and Int clause present | exit 0, `.beam` written |
| `fn m -> String = f(0)` with `fn f "x"` / `fn f s: String` | exit 1, `type mismatch: expected String, got Int` | not reached |
| `type R { a: String }`, `fn f R { a: 0 }` | exit 1, `type mismatch: expected String, got Int` | not reached |

- Result: no source found where the module fails to compile. The rule is complete for the current language. **[Inference]** A later step that adds an untyped place for a literal (a `with` binding, a pipe in any expression) must recheck it.
- Limit: `elixirc --warnings-as-errors` exits 0 on unused imports (notes.md limits). So a spare import would not fail; a missing import would fail. The case that matters is covered.

## Existing validation (observed, TEST)

See test-result.json. All checks pass: fmt, clippy, cargo test 27 (13 unit, 14 CLI), 0004 `run.py` 15 of 15 checks (17 min 29 s, `results/20261107T105123558886Z`), 0001 `run.py` (`results/20261107T105132361944Z`), wiki lint 0 errors, slice6_int 16 of 16. `run.py` does not contain `slice6_int_test.py`; it ran separately.

## Evidence consistency (observed)

- RED: 16 tests, 15 FAIL, 1 pass (`test_no_negative_literal`, a guard). red-output.log, red-review rerun and notes agree.
- GREEN: 16 OK, 13 runtime subtests; cargo 27 (13 unit, 14 CLI), before 25 (+2 unit tests G3). This TEST: the same counts.
- The test file and the fixture did not change between the RED commit `48f7b731` and the GREEN commit `922389ab` (`git diff --stat` empty).
- Compile-level files in TEST: slice3_types 69, slice4_retire 87, slice5_syntax 60, slice5_squash 24, slice5_rewrite 5, stored_types 33. Equal to GREEN.

## Defects

- **L1 · low · A2b text.** `fn f 0` then `fn f s: String, 0` gives `type mismatch: expected Int, got String`, not the arity text. Minimum repair (optional, later): run the G4 loop only when the arity is equal. No repair in this step.
- No other defect.

## Decisions

| # | Class | Choice | Reason |
|---|---|---|---|
| R1 | Undo | Accept G4 with the A2b text as low, no repair. | A reject stays a reject. No code emitted. Text change only later, with the plan. |
| R2 | Undo | Accept G6 as complete. | Every literal is typed against a signature or a TYPE; two adversarial sources compile in `elixirc`. |
| R3 | Undo | Accept G1 and G3 (nested EFFECT input check) as in scope. | It closes red-review N1 and guards D6B-03. |
| R4 | Undo | Adversarial sources stay in scratch, not in the test file. | The reviewer changes no tests. A test for A2b belongs to a later text step. |
