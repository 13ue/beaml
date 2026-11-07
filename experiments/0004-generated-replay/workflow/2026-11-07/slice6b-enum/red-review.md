# RED review: slice 6b step 4 (`slice6b-enum`)

**[Proposal]** Fresh-context RED REVIEW, 2026-11-07. Not a Devil's Advocate round. No production file and no test changed. `run.py` was not run.
Read: `spec.md`, `notes.md`, `red-output.log`, `../slice6b-plan/decisions.md` (D6B-13 to D6B-28), `../slice6b-plan/plan.md` (steps 4 and 5), `../slice6b-plan/plan-review.md`, `../slice6b-type-constructor/notes.md` (GREEN G1 to G15), DL-082 to DL-088, DL-100, DL-102, `tests/slice6_enum_test.py`, the shared harness in `slice6_constructor_test.py` and `slice6_failure_test.py`, `slice6/enum/*.beaml`, `main.rs` (signature lines near line 995, one-clause rule near line 1069, `validate` near line 1705).

## Verdict

**BLOCK on objection 1 (high).** RED repair: add one guard test. Objections 2 and 3 are medium. Add them in the same repair, or note them.

## Rerun (observed)

- `python3 -B experiments/0004-generated-replay/tests/slice6_enum_test.py`: 12 tests, 11 FAIL, 1 ok (guard S14). Same as `red-output.log`.
- Every failure comes from the compiler: `expected '(' at byte N` (no bare variant, no literal) or `error: fn Outcome: a constructor needs a type Outcome` (step 3 G5). No setup failure.
- Each reject asserts exit 1, empty stdout and the full text. An earlier error such as `expected '('` gives a FAIL, not a false pass.
- Runtime harness: a subtest whose name is not in the output gets `None` and fails. A build or `elixirc` failure stops the test. No runtime subtest can pass without a run.

## Rule check (observed in the tests)

| Rule | Test | Result |
|---|---|---|
| DL-082 literal OR constructor | two fixtures, `test_literals_and_constructor_on_one_enum` | encoded |
| DL-084 keys = parameter names | `test_equal_types_with_other_names_is_reachable` | encoded |
| DL-085 first match wins | clause order assertion, `pair_ok` before `pair_unknown`, `from_int` picks signature 3 | encoded |
| DL-087 unreachable signature or clause | three rejects | encoded, gaps in objections 2 and 3 |
| DL-088 one path per enum | D6B-22 text, exact | encoded |
| DL-100 bare variants free in code | `pending` in both fixtures, runtime | encoded |
| D6B-23 "same parameters" = same names AND TYPES | reject: `code: String` twice; accept: `code: String`, then `status: String` | encoded, nothing stricter at equal arity |

- **[Verified]** The D6B-23 reading is correct. DL-084 makes the names the decode keys. A signature with equal TYPES and other names has other keys, so decode can reach it. The tests reject only equal pairs and accept other names.
- **[Inference]** The one-reject and one-accept pair also stops a GREEN that compares TYPES only, at equal arity. At a larger arity nothing stops it (objection 2).

## Objections

### O1 · high · The one-clause rule for an EFFECT pipe body has no test, and step 4 GREEN must loosen it

- **Fact (observed).** `main.rs` near line 1069 rejects every pipe body in a several-clause `fn` (`a function with a pipe body has one clause in slice 1`). No test in `experiments/` asserts this text (search over tests and fixtures, results excluded).
- **Fact (observed).** S4 makes step 4 GREEN accept `reason |> DeclineReason |> Declined` in a several-clause constructor. D6B-28 keeps the one-clause rule for a whole-body pipe with an EFFECT step.
- **Wrong outcome.** The shortest GREEN deletes the whole check. Then a several-clause `fn` with an EFFECT pipe body compiles, with `emit_chain` and spans per clause. All step 4 tests and the byte-equal orders and payments outputs still pass. The trace and replay shape of EFFECT flows changes without a signal.
- **Smallest test.** A reject in `slice6_enum_test.py`: an `effect` line plus `fn f "a" -> Payment ! PaymentError = ... |> payments.authorize` and a second clause of `f`. Assert the existing text `a function with a pipe body has one clause in slice 1: f`. It passes today (guard, like S14) and fails when GREEN drops the rule.

### O2 · medium · The superset check can be positional and still pass

- **Fact (observed).** `test_unreachable_signature_with_more_parameters` uses `code: String`, then `code: String, extra: String`. The earlier pairs are a prefix of the later ones.
- **Wrong outcome.** A GREEN that compares by position (prefix) passes. Then `code: String`, then `extra: String, code: String` compiles. Decode always takes signature 1 when `code` is present, so signature 2 is dead (DL-087, D6B-23 "every (name, TYPE)", a set). The other way, a GREEN that compares TYPES only at larger arity rejects `code: String`, then `status: String, extra: String`, which is reachable (stricter than D6B-23).
- **Smallest test.** Reject: `code: String`, then `extra: String, code: String`, S9 text. Accept: `code: String`, then `status: String, extra: String`.

### O3 · medium · The unreachable clause is tested only in the first signature

- **Fact (observed).** `test_unreachable_clause_after_a_catch_all` has one signature. `validate` today keys coverage by the `fn` name.
- **Wrong outcome.** A GREEN that checks coverage only for signature 1 (or for the last one) passes. A dead clause in signature 2 compiles (DL-087).
- **Smallest test.** `OUTCOME_CODE` as signature 1, then `fn Outcome n: Int -> Outcome`, `fn Outcome n -> Outcome = Other("i")`, `fn Outcome 0 -> Outcome = Approved()`. Assert `unreachable clause: Outcome`.

## Step 5 after S4

- **[Inference]** After step 4 GREEN, the first half of the plan step 5 RED (the corpus clause in a several-clause constructor) passes. It can no longer fail. The step 5 RED must drop it or name it as a guard, and change its "today" text.
- The second half stays a genuine RED: `fn g p: P -> R = build(p |> prepare, x)` fails today with `expected ')'`.
- Step 5 still has to prove:
  - a pipe in an argument, ending at `,` and `)` (D6B-25);
  - `a + b |> f` is `f(a + b)` (D6B-25);
  - a nested pipe with an EFFECT or a failing step is an error with `help: make the pipe the whole body` (D6B-27);
  - a failing constructor step in a whole-body pipe of a several-clause `fn` compiles to a `with`, no spans (plan step 5 Elixir shape; S5 avoids `!`);
  - variant step rules (D6B-26): a variant with zero or two payloads as a step is an error; a wrong payload TYPE is a `type mismatch`. Step 4 builds the variant step but tests only the good path;
  - the one-clause rule for EFFECT pipes, if O1 is not added in step 4;
  - the error order of `bad/*.beaml` and byte-equal orders and payments outputs.

## Open Undo points without tests

- Second payload variant without a literal in a literal enum (D6B-21 "at most one"): text open.
- Call `E(args)` that fits no signature (D6B-16): text open.
- Non-exhaustive signature group: `non-exhaustive function: E` or a text per signature.
- Literal on the keep-value variant (`Unknown(String) = "x"`): assumed S10 text.
- Bare uppercase name in a pattern that is no variant: text open.
- Code call when two signatures have equal TYPES: takes the first (D6B-16), no runtime check.
- `duplicate name: new_PaymentState_1` against a user `fn` (step 3 G7, still untested).
- A variant without a literal and without a payload in a literal enum (D6B-21 "every variant has a literal").

## Limits

- `cargo test`, `cargo fmt` and `cargo clippy` were not rerun. The production state is from the RED notes.
- O1 wrong outcome is an inference. The emit of a several-clause EFFECT pipe was not run, because that needs a production change.
- D6B-51 (enum without a decode path in an EFFECT output) is listed under the step 4 heading in `decisions.md` but in no plan step. Not tested here. Not an objection: a reject now would break the payments output.
