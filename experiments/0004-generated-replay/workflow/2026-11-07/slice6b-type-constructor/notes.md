# Slice 6b step 3: notes

## Solve

What this phase takes from the plan (step 3, D6B-11 to D6B-19, DL-092) and from the plan check (D6B-28):

- Today the signature line fails with `expected '='`. An uppercase `fn` fails with `invalid function name`.
- Today every pipe step emits `ProbeSupport.span`, also in a module without an EFFECT. The step 2 harness needs a stub for that reason (step 2 notes, H1).
- First RED of `plan.json`: the DL-092 fixture compiles; a record literal outside the constructor and a structural twin are rejected.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| S1 | Undo | All RED cases go in `slice6_constructor_test.py`. The Rust unit test `constructor_is_the_only_way_in` waits for GREEN. | Add the unit test to `main.rs` now | RED must not change the production file (step 1 decision 1). |
| S2 | Undo | Fixtures go to `slice6/constructor/`, the test to `slice6_constructor_test.py`. | `slice6/type-constructor/` and `slice6_type_constructor_test.py` from `plan.json` | The task names these paths. The ledger keeps the `plan.json` name. |
| S3 | Repair | **Chose:** D6B-28, spans part, belongs to step 3. **Over:** keep the step 2 stub and leave D6B-28 in step 5. **Because:** `wrap = n \|> NonZeroInt` is a pure module; the plan shape is a plain `with`; plan-review.md (2) found the dependency. A host without ProbeSupport cannot call a pure module with spans. **Commits us to:** slice 1 output changes for pure pipes. Changed outputs: `slice6/failure/body.beaml` (`piped`, `outer`) and the inline `pbad` source of `slice6_failure_test.py`. No other fixture has a pipe without an EFFECT (observed: `rg '\|>'` over all `.beaml` files and the tests). The orders and payments outputs do not change (EFFECT pipes). Decision-log entry at the end of the phase. | Keep the stub | Plan check. |
| S4 | Undo | The one-clause part of D6B-28 stays in step 5. | Move it too | No step 3 fixture has a pipe body with more than one clause. |
| S5 | Undo | The step 3 runtime harness has no ProbeSupport stub and asserts that a pure module does not contain `ProbeSupport`. The step 2 test keeps its stub. | Reuse the step 2 `run_runtime` with the stub | With a stub, a GREEN that keeps spans gives a false pass. The step 2 file is not changed while another worker runs the suite. |
| S6 | Undo | A record success value stays a map with String keys: `{:ok, %{"value" => 3}}`. A record failure value stays a struct: `{:error, %BeamlSpike.IsZero{}}`. | `{:ok, %NonZeroInt{value: 3}}` (task notation) | The plan shape and D6B-07 ("a record TYPE has two Elixir forms"). A struct success value changes every record and the orders output. The task notation is read as shorthand. |
| S7 | Undo | `nonzero.beaml` uses the signature line with unannotated clauses (task forms). `plain.beaml` is the corpus form without a signature line. | The plan fixtures (nonzero without signature, a second `Label` fixture) | Same coverage with the task forms. `Label` adds no rule. |
| S8 | Undo | Record literal text: `error: fn make: the record literal NonZeroInt { ... } is legal only in the clauses of the constructor fn NonZeroInt` and `  help: call the constructor fn NonZeroInt (as a pipe step, because it can fail)`. | `invalid function name` or a text without `help:` | The task asks for a help line that names the constructor. The text is specific to the rule (plan-review.md (5)). |
| S9 | Undo | EFFECT text: `error: effect payments.authorize: the TYPE T has a constructor and cannot stand in an EFFECT <position> (interim D6B-19, Q6B-3)` and `  help: use a TYPE without a constructor at the EFFECT, then pipe it into fn T`. Positions: `input`, `output`, `failure`, `output field P.n`. | Output only | The task names the output; D6B-19 names all four positions. Each is one line in the test. |
| S10 | Undo | Second equal signature line: `unreachable signature: NonZeroInt` and `  help: an earlier signature line of fn NonZeroInt has the same parameters; remove this one`. | A step 3 text "several signatures come in step 4" | Step 4 (D6B-23) rejects the equal line with `unreachable signature`, so the text does not change in step 4. |
| S11 | Undo | Structural twin: `type mismatch: expected NonZeroInt, got Plain`; the other direction `expected Plain, got NonZeroInt`. | One direction | D6B-17 "either side". The text of `require_type` stays. |
| S12 | Undo | D6B-11 to D6B-13 texts: `error: fn Missing: a constructor needs a type Missing` plus `  help: declare type Missing { ... }, or write the fn name in lowercase`; `error: fn NonZeroInt: a constructor returns its own TYPE NonZeroInt, not Int`; `error: fn NonZeroInt: a clause stands before the signature line` plus `  help: move the signature line above the first clause`; a clause annotation against the signature: `type mismatch: expected Int, got String`. | No test for these rules | The plan code list names them. One source line each. |
| S13 | Undo | Accept cases for D6B-18: `fn read NonZeroInt { value } -> Int = value` and `fn keep x: NonZeroInt -> NonZeroInt = x` in `nonzero.beaml`. | No accept case | A GREEN that rejects every use of the TYPE outside the constructor fails then. |
| S14 | Undo | The pipe beside an EFFECT: orders plus `fn twice s: String -> String = s \|> echo` gives `p1 = __MODULE__.echo(p0)`. A guard asserts that the orders flow keeps `ProbeSupport.span` (passes today). | Only the pure module case | D6B-28 says "only for a whole-body pipe with an EFFECT step", not "only in a module without EFFECTS". |

### Points the plan does not settle

- **[Unknown]** An uppercase `fn` named like an enum in step 3 (before step 4): error or not. No test. Class Undo.
- **[Inference]** A record literal of TYPE A inside the constructor of another TYPE B: D6B-18 rejects it. No test (the first error would be unclear). Class Undo.
- **[Inference]** A pure pipe in a source with a non-lowercase file name: after D6B-28 it needs no span name. Whether the service-name error stays for it is open. No test. Class Undo.
- **[Inference]** A constructor without `!` (`fn F r: String -> F`) can be called as `F(r)`. Only used here as an EFFECT failure TYPE source. No runtime test. Class Undo.
- **[Inference]** Order of EFFECT checks: the D6B-19 check must run before the `String fields only` and `--stored` checks, else the field case gives another text. GREEN concern. Class Undo.
- **[Inference]** `elixirc --warnings-as-errors` and the stub: with S3 the step 2 stub has no caller. It stays harmless (step 2 H1). Removal is a later Undo.

## RED

Command: `python3 -B experiments/0004-generated-replay/tests/slice6_constructor_test.py` (repository root). Full output: [red-output.log](red-output.log).
Result: 20 tests, 19 FAIL, 1 pass (the guard). Exit 1.

| Test | Expected | Actual today | Reason |
|---|---|---|---|
| `test_nonzero_fixture_compiles_to_the_planned_shape` | exit 0, planned lines | `expected '=' at byte 201` | No signature line in the parser. |
| `test_plain_fixture_compiles` | exit 0, planned lines | `invalid function name: NonZeroInt` | Uppercase `fn` names are rejected. |
| `test_runtime_nonzero` | 7 subtests PASS | stops at build, `expected '='` | Same as the first row. |
| `test_runtime_plain` | 2 subtests PASS | stops at build, `invalid function name` | Same as the second row. |
| `test_pure_module_has_no_span` | `p1 = __MODULE__.seven(p0)`, `with {:ok, p1} <- __MODULE__.check(p0) do` | the same calls inside `ProbeSupport.span(...)` | D6B-28 not built. |
| `test_runtime_pure_pipe_without_stub` | no `ProbeSupport` in the module, 3 subtests PASS | `ProbeSupport` found | Same. |
| `test_pure_pipe_beside_an_effect_has_no_span` | `p1 = __MODULE__.echo(p0)` | span around `echo` | Same. |
| `test_effect_pipe_keeps_its_spans` | span on `orders.prepare` | pass | Guard (S14). |
| `test_record_literal_outside_the_constructor` | S8 text | `expected '=' at byte 90` | No signature line, no rule. |
| `test_structural_twin_is_not_the_nominal_type` | `type mismatch: expected NonZeroInt, got Plain` | `expected '=' at byte 90` | Same. |
| `test_nominal_type_is_not_its_structural_twin` | `type mismatch: expected Plain, got NonZeroInt` | `expected '=' at byte 90` | Same. |
| `test_second_signature_line` | S10 text | `expected '=' at byte 90` | Same. |
| `test_clause_before_the_signature_line` | S12 text | `expected '=' at byte 141` | Same. |
| `test_clause_annotation_differs_from_the_signature` | `type mismatch: expected Int, got String` | `expected '=' at byte 90` | Same. |
| `test_uppercase_fn_without_its_type` | S12 text | `invalid function name: Missing` | No constructor rule. |
| `test_constructor_returns_another_type` | S12 text | `invalid function name: NonZeroInt` | Same. |
| `test_constructor_type_as_effect_output` | S9 text, `output` | `expected '=' at byte 90` | No signature line, no D6B-19 check. |
| `test_constructor_type_as_effect_input` | S9 text, `input` | `expected '=' at byte 90` | Same. |
| `test_constructor_type_in_an_effect_output_field` | S9 text, `output field P.n` | `expected '=' at byte 90` | Same. |
| `test_constructor_type_as_effect_failure` | S9 text, `failure`, TYPE `F` | `invalid function name: F` | No constructor rule. |

### RED checks

- Every failure is a missing behavior, not a setup failure. The compiler builds, every case reaches the compiler, every message is a compiler message.
- The runtime harness ran against a hand-written module in the planned shape (scratch, not retained, via `BEAML_SPIKE`): `test_runtime_nonzero` 7 of 7 PASS. With `wrap` changed to `{:ok, 9}`, `wrap_ok` FAIL. So the runtime RED is genuine.
- Each reject asserts the full message (plan-review.md (5), step 3). Today's `invalid function name: NonZeroInt` does not give a false pass.
- The action event check of step 2 runs on every compile (no source text, no path).
- Production unchanged: `cargo test --offline --no-fail-fast` 28 pass (14 unit, 14 CLI). `slice6_int_test.py` 16 OK. `slice6_failure_test.py` 22 OK.
- `run.py` was not run and no result directory changed (another worker runs the suite). No commit.

## Limits

- No runtime test of a constructor without `!` called as `T(args)`.
- The struct module place and the `def` wrapper body are not asserted, only the `def` line.
- The other compile-level tests (slice 3 to 5, stored types) were not run in this phase; `main.rs` did not change.

## RED repair

Input: [red-review.md](red-review.md), verdict Block (two high objections, one medium note). This section adds five tests to `slice6_constructor_test.py`. The earlier sections stay as recorded.

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| R1 | Undo | Objection 1: two rejects with the review texts. `fn same p: Plain -> NonZeroInt ! IsZero = p` gives `type mismatch: expected NonZeroInt ! IsZero, got Plain`. `fn keep x: NonZeroInt -> NonZeroInt = x` plus `fn same p: Plain -> NonZeroInt = p \|> keep` gives `type mismatch in pipe step keep: expected NonZeroInt, got Plain`. | A rule in `require_type` only | A GREEN with the nominal rule in `require_type` only passes the first 20 tests. The texts are the current formats of the `!` body check and the pipe step check (observed with lowercase TYPES on the current compiler). |
| R2 | Repair | **Chose (D6B-18 raised from Undo to Repair):** a record literal of TYPE A is legal only inside the OWN clauses of `fn A`, at any depth. A literal of A inside the constructor of B is rejected. **Over:** allow a nested literal inside any constructor clause. **Because:** otherwise any constructor becomes a way in for every TYPE, and DL-092 breaks. **Commits us to:** the check walks the whole body, not the top node, and compares the literal TYPE with the name of the enclosing constructor. | Allow nested | red-review.md objection 2. Replaces the Undo point "literal of A inside the constructor of B" in "Points the plan does not settle". |
| R3 | Undo | Objection 2: two rejects with `type Box { n: NonZeroInt }` and `Box { n: NonZeroInt { value: x } }`, once in `fn Box`, once in `fn make`. Text: the S8 text with `fn Box` or `fn make`. | One case | The `fn Box` case catches "inside any constructor"; the `fn make` case catches "top body node only". |
| R4 | Undo | Objection 3 (medium): one runtime accept case `test_runtime_constructor_call_form`. Source inline: `type F { reason: String }`, `fn F r: String -> F = F { reason: r }`, `fn mk r: String -> F = F(r)`. Check `BeamlSpike.mk("x") == %{"reason" => "x"}`, no ProbeSupport, `elixirc --warnings-as-errors`. | No test (earlier Undo point) | The plan code list names "a constructor as a call". Replaces the Undo point "constructor without `!` as `F(r)`". |
| R5 | Undo | The spec pass rule changes from 20 of 20 to 25 of 25. | Keep 20 | The spec must name the full test set. |

### Open point for the OWNER (Migrate, not decided here)

- **Q6B-6.** A host can forge a constructor success value at the public wrapper: `BeamlSpike.keep(%{"value" => 0})` gives a NonZeroInt that never went through `fn NonZeroInt`. The wrapper checks the shape only. DL-092 ("the only way in") does not cover host calls yet.
- **Option A:** accept the gap as out of scope. DL-092 binds generated BEAML code only.
- **Option B:** make the generated constructor wrapper the only entry. A guard on every public wrapper rejects a nominal value that did not come from the constructor.
- **Evidence:** [Inference] from the wrapper shape in red-review.md, S6. Not built. A struct success value alone does not close the gap (red-review.md).
- Step 3 does not wait for this answer (red-review.md). Record Q6B-6 in decisions-to-be-made at the end of the phase.

### RED repair run

Command: `python3 -B experiments/0004-generated-replay/tests/slice6_constructor_test.py` (repository root). Full output: [red-output.log](red-output.log) (replaced by this run).
Result: 25 tests, 24 FAIL, 1 pass (the guard). Exit 1. The first 19 failures are the same as in the RED table.

| New test | Expected | Actual today |
|---|---|---|
| `test_structural_twin_at_the_failing_body` | `type mismatch: expected NonZeroInt ! IsZero, got Plain` | `expected '=' at byte 90` |
| `test_structural_twin_into_a_pipe_step` | `type mismatch in pipe step keep: expected NonZeroInt, got Plain` | `expected '=' at byte 90` |
| `test_nested_literal_in_another_constructor` | S8 text, `fn Box` | `expected '=' at byte 90` |
| `test_nested_literal_in_a_lowercase_fn` | S8 text, `fn make` | `expected '=' at byte 90` |
| `test_runtime_constructor_call_form` | build, 1 subtest PASS | stops at build, `invalid function name: F` |

- Production unchanged (`main.rs` not touched): `cargo test --offline --no-fail-fast` 28 pass (14 unit, 14 CLI). `slice6_int_test.py` 16 OK. `slice6_failure_test.py` 22 OK.
- `run.py` was not run. No result directory was touched. No commit.
- Limit: the four new rejects fail at the signature line today. They prove the rule only after GREEN parses the signature line. The bypass of objection 1 was not built.

## GREEN

Commands and full output: [green-output.log](green-output.log). Changed file: `experiments/0001-syntax-to-beam/src/main.rs` only. The test and the fixtures are not changed.

### Result (observed)

| Command | Result |
|---|---|
| `slice6_constructor_test.py` | 25 tests, 25 OK, all runtime subtests PASS, no ProbeSupport stub |
| `slice6_failure_test.py` | 22 OK (its stub stays, now without a caller in pure modules) |
| `slice6_int_test.py` | 16 OK |
| `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` | pass |
| `cargo test --offline --no-fail-fast` | 29 pass (15 unit, 14 CLI); one new unit test |
| `stored_types_test.py`, `slice3_types_test.py`, `slice4_retire_test.py` | 33, 69, 87 OK |
| `slice5_syntax_test.py`, `slice5_squash_test.py`, `slice5_rewrite_test.py` | 60, 24, 5 OK |
| Byte-equal check: HEAD compiler (scratch build) against the GREEN compiler | `payments.beaml` and `orders.beaml` outputs byte-equal |
| Diff of the `body.beaml` output | only the two pure pipe steps lose `ProbeSupport.span` (S3) |

### Decisions

| # | Class | Choice | Alternative | Reason |
|---|---|---|---|---|
| G1 | Undo | A signature line is a `fn` line without `=`, kept in `Program.signature_lines`. A parameter that is not `name: TYPE` gives `error: fn N: a signature line has name: TYPE parameters only`. | A `Clause` with an empty body | No dummy body in the emit and coverage code. |
| G2 | Undo | Signature lines are checked before the clauses. They fill `signatures` and `failures`. A clause of the same name takes the TYPE of position i as the expected TYPE of its parameter i. | Merge lines and clauses in one loop | The existing `inconsistent function signature` check then compares each clause with the line. |
| G3 | Undo | D6B-13 compares byte positions: a clause that starts before the signature line of its name is an error. | Order index | Source position is already stored. |
| G4 | Undo | A second equal signature line gives `unreachable signature`. A second different one gives `inconsistent function signature` (step 4 replaces it with several signatures, `ponytail:` comment). | Accept several now | Step 3 scope (spec). |
| G5 | Undo | `fn_name` holds the D6B-11 checks and the old reserved-word check. An uppercase name needs a record `type`; an enum name also gives `a constructor needs a type`. | A special text for an enum | Enum constructors come in step 4 (open Unknown point). |
| G6 | Undo | Elixir name `new_T_1` through one helper `elixir_name`, used in the `def`, the `defp` clauses, the call emit and the pipe step emit. The declaration comment and the span name keep the BEAML name `T`. | Rename in the `signatures` map | One mapping point at emit time; checks keep BEAML names. |
| G7 | Undo | A lowercase `fn new_T_1` beside a constructor `fn T` gives `duplicate name: new_T_1`. | No check | Without it, two Elixir functions get one name. One line. |
| G8 | Repair | **Chose:** the nominal rule in `same_type` (D6B-17), so it holds at `require_type`, the `!` body check, the pipe step check, `failure_types` and `overlap`. **Over:** a rule in `require_type` only. **Because:** RED repair R1 tests all three gates. **Commits us to:** a TYPE with a constructor never equals a structural twin, also as a failure TYPE. | `require_type` only | red-review.md objection 1. |
| G9 | Repair | **Chose:** D6B-18 as a walk over the whole clause body in `validate`, before the body TYPE check. A literal of T is legal only when the clause name is T. **Over:** a check of the top node or of "any constructor". **Because:** RED repair R2. **Commits us to:** record patterns stay free; only expressions are walked. | Top node only | R2, red-review.md objection 2. |
| G10 | Undo | The D6B-18 help line says `(as a pipe step, because it can fail)` for a constructor with `!`, else `(as a call T(...))`. | One text | A constructor without `!` is called as `T(r)` (R4). No test for the second text. |
| G11 | Undo | D6B-19 runs first in the EFFECT checks, after the name, kind and path checks. Positions: `input`, `output`, each `failure`; a nested field gives ` field Owner.field` (enum: `Owner.Variant`). | After the String-field checks | Open point "order of EFFECT checks": else the field case gives another text. |
| G12 | Undo | D6B-19 stays as an interim reject, as the tests expect. **DL-101** (the decode of outside data calls the record constructor) makes it a temporary state: a later step replaces this reject with the decode path. The code comment names DL-101. | Build the decode path now | Out of step 3 scope; the tests expect the reject. |
| G13 | Repair | **Chose:** D6B-28 per pipe: `emit_chain` emits spans only when the pipe has an EFFECT step. **Over:** per module (spans in every pipe of a module with an EFFECT). **Because:** `test_pure_pipe_beside_an_effect_has_no_span` and D6B-28 text "only a whole-body pipe with an EFFECT step". **Commits us to:** pure pipes are plain calls also in an EFFECT module; the orders and payments flows keep their spans (byte-equal, observed). | Per module | S3, S14. |
| G14 | Undo | The service-name error (`a pipe or an effect needs a source file name ...`) now fires only for a source with an EFFECT. | Keep it for every pipe | A pure pipe names no span (red-review.md: narrowing is harmless). Text unchanged. |
| G15 | Undo | New unit test `constructor_is_the_only_way_in` (S1): accept with a pipe step, reject of a literal outside, reject of a structural twin. | No unit test | S1 says it comes with GREEN. |

### Deviations

- None from the spec. The task text "spans only when the module has an EFFECT" is built per pipe (G13), because the test `test_pure_pipe_beside_an_effect_has_no_span` asks for a plain call beside an EFFECT. A per-pipe rule also gives no `ProbeSupport` in a pure module.

### Checks

- **[Verified]** Action events: the event code is not changed. The harness checks on every compile that no source text and no path are in the events.
- **[Verified]** No other fixture has a pipe without an EFFECT step (all slice 2 to 6 suites pass, outputs byte-equal).
- `run.py` was not run. No commit.

### Limits

- **[Unknown]** Q6B-6 (host forges a nominal value at a public wrapper) is not changed by this step.
- No test of the help text for a constructor without `!` (G10), of a nested constructor TYPE inside an EFFECT input field, or of the `duplicate name: new_T_1` check (G7).
- A signature line without any clause gives `non-exhaustive function: T`, not a specific text. No test.
