# Slice 6b step 3: REVIEW

Reviewer: a fresh-context agent. This is a normal REVIEW (implement-step step 7), not a Devil's Advocate.
Inputs: spec.md, notes.md (all sections), red-review.md, green-output.log, [test-output.log](test-output.log), plan.md step 3, decisions.md D6B-11 to D6B-19 and D6B-28, DL-092, DL-099 to DL-101.
Diff: `git diff bf4fc161..HEAD -- experiments/0001-syntax-to-beam/src/main.rs` (319 lines). The test file and the fixtures have no diff in this range (they come from the RED commits).

## Verdict

**PASS.** The step meets the spec. No high objection. One test is required before the slice closes (G7, see below). Two docs items are open for the docs phase.

## TEST results (observed, this review)

- `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings`: pass.
- `cargo test --no-fail-fast`: 29 pass (15 unit, 14 CLI).
- `slice6_constructor_test.py` 25 OK, `slice6_failure_test.py` 22 OK, `slice6_int_test.py` 16 OK.
- `run.py` of EXPERIMENT 0001: pass. `run.py` of EXPERIMENT 0004: pass, 15 of 15 steps (result dir `results/20261107T114816931475Z`, [test-result.json](test-result.json)).
- `scripts/lint_wiki.py`: 0 errors.

## Whole step (observed in the diff)

| Contract item | Where | Test |
|---|---|---|
| D6B-11 uppercase `fn` is a constructor of a record `type`, output is that TYPE | `fn_name` | S12 texts |
| D6B-12 signature line, `name: TYPE` only, TYPES by position | parser `eat('=')`, `validate` loop | clause annotation test |
| D6B-13 clause before the signature line | byte position compare | S12 text |
| Step 3: second equal line `unreachable signature` | signature loop | S10 text |
| D6B-15 `new_T_1`, `__beaml_new_T_1`, call and pipe step map | `elixir_name` at 4 emit points | runtime nonzero, plain, call form |
| D6B-17 nominal in `same_type` (all gates) | `same_type` | R1 tests (three gates) |
| D6B-18 literal walk over the whole body, own constructor only | `literals` | R3 tests |
| D6B-19 interim EFFECT reject, all four positions | `constructor_inside` | four S9 tests |
| D6B-28 spans part, per pipe | `emit_chain` `spans` | three pure-pipe tests and the guard |

- `literals` matches every `Node` variant without a wildcard. A new node kind fails the build, so the walk cannot skip one silently.
- Nothing beyond need. G14 (service-name error only for a source with an EFFECT) follows from D6B-28. G15 is the unit test of S1. The rest maps to the contract.

## The three untested behaviours (observed, own sources)

Sources and outputs: scratch only, not retained (listed in [test-output.log](test-output.log), section "Review probes").

| # | Source (core lines) | Exact output | Test before slice close? | Class |
|---|---|---|---|---|
| G10 | `type F { reason: String }`, `fn F r: String -> F = F { reason: r }`, `fn mk r: String -> F = F { reason: r }` | exit 1, no stdout: `error: fn mk: the record literal F { ... } is legal only in the clauses of the constructor fn F` / `  help: call the constructor fn F (as a call F(...))` | No. Text only; the rule is the same code path as the tested `!` case. Add the line when a test touches the file. | Undo |
| G7 | HEAD + `fn new_NonZeroInt_1 n: Int -> Int = n`; also `fn new_F_1 r: String -> String = r` before `fn F` | exit 1, no stdout: `duplicate name: new_NonZeroInt_1`; `duplicate name: new_F_1` | **Yes.** One reject line in step 4 RED. Step 4 adds `new_T_k` with k > 1 and changes the naming; without a test, a regression gives two Elixir functions with one name. | Repair (D6B-15 commits to the error) |
| D6B-19 input field | HEAD + `type Req { n: NonZeroInt }`, `effect payments.authorize Req -> Ok ! Err = ...` | exit 1, no stdout: `error: effect payments.authorize: the TYPE NonZeroInt has a constructor and cannot stand in an EFFECT input field Req.n (interim D6B-19, Q6B-3)` plus the help line | No. Same `constructor_inside` loop as the tested output field and input. DL-101 replaces this reject. | Undo |

- **[Observed]** Two levels deep (`Req { i: Inner }`, `Inner { n: NonZeroInt }`) gives `input field Inner.n`, not a path from `Req`. The text names the innermost owner. Low, interim text. Drop.

## G13: spans per pipe (observed, old and new compiler compared)

Old compiler: a scratch build of `main.rs` at `bf4fc161`. Same sources, same `--stored stored/empty.jsonl`.

| Source | Old | New |
|---|---|---|
| orders `place` only (EFFECT pipe) | 4 spans | byte-equal |
| `place = order \|> payments.authorize` (EFFECT step only) | | byte-equal |
| orders `place` + pure `twice o = o \|> prepare \|> prepare` + `indirect order = order \|> place` | 7 spans | 4 spans: only `place` keeps them |

- **An EFFECT pipe cannot lose its span.** `spans = steps.iter().any(|s| self.effect(s).is_some())` is computed per pipe; the `place` lines are unchanged.
- **A pure pipe in an EFFECT module keeps no span.** `twice` is plain calls.
- **[Observed] Medium note.** `indirect` pipes into `place`, which calls the EFFECT. `indirect` loses its span. This follows the D6B-28 text ("a pipe with an EFFECT step"; `place` is not an EFFECT step). No fixture has this shape, so the orders and payments outputs stay byte-equal. If the OWNER wants a span on a pipe that reaches an EFFECT through a fn, that is a change of D6B-28. Not a defect of step 3.

## Nominal TYPE: smuggling tries (observed)

Each source is HEAD (the nonzero constructor) plus `type Plain { value: Int }`. Each gives exit 1 and no stdout.

| Try | Output |
|---|---|
| `type Box { a: NonZeroInt }`, `fn mk p: Plain -> Box = Box { a: p }` | `type mismatch: expected NonZeroInt, got Plain` |
| `fn mk x: Int -> Box = Box { a: Plain { value: x } }` | `type mismatch: expected NonZeroInt, got Plain` |
| structural twin of the box: `type PBox { a: Plain }`, `fn mk b: PBox -> Box = b` | `type mismatch: expected Box, got PBox` |
| pattern: signature `fn conv p: Plain -> Int`, clause `fn conv NonZeroInt { value } -> Int = value` | `type mismatch: expected Plain, got NonZeroInt` |
| pattern with annotation: `fn conv NonZeroInt { value }: Plain -> Int = value` | `type mismatch: expected Plain, got NonZeroInt` |
| nested pattern: `fn unbox Box { a: Plain { value } } -> Int = value` | `type mismatch: expected NonZeroInt, got Plain` |
| enum payload: `enum Wrap { W(NonZeroInt) }`, `fn mk p: Plain -> Wrap = W(p)` | `type mismatch: expected NonZeroInt, got Plain` |
| call argument: `fn mk p: Plain -> NonZeroInt = keep(p)` | `type mismatch: expected NonZeroInt, got Plain` |

- No try gets through. The record of a nominal field is structural only down to the nominal field (`Box` against `PBox`).
- Known open gap, not new: a host call `BeamlSpike.keep(%{"value" => 0})` (Q6B-6, Migrate, OWNER).

## Consistency: RED, reviews, GREEN

- RED (20), RED review (Block, 2 high, 1 medium), RED repair (+5 tests, 25), GREEN (25 of 25). G8 answers objection 1, G9 objection 2, the call-form test objection 3. Consistent.
- GREEN numbers match this TEST run: cargo 29, the three slice 6 files 25, 22, 16.
- Spec pass rule "outputs stay byte-equal": the green byte-equal check (orders, payments) and this review's orders check agree.

## Defects

| # | Severity | Defect | Minimum repair | Phase |
|---|---|---|---|---|
| 1 | Medium | G7 `duplicate name: new_T_1` has no test (D6B-15 Repair). | One reject line `fn new_NonZeroInt_1 n: Int -> Int = n` with the exact text. | Step 4 RED, before the slice closes |
| 2 | Medium (docs) | Q6B-6 (host forges a nominal value at a public wrapper) is not in `wiki/planning/decisions-to-be-made.md` or in `slice6b-plan/decisions.md`. notes.md says "record it at the end of the phase". | Add Q6B-6 with options A and B from notes.md. | Docs |
| 3 | Low (docs) | notes.md S3 says "Decision-log entry at the end of the phase" for the slice 1 output change of pure pipes. No entry exists. | One decision-log line that links D6B-28 and S3, G13. | Docs |

## Decisions of this review

| # | Class | Choice | Reason |
|---|---|---|---|
| V1 | Undo | Verdict PASS, not BLOCK. | No wrong outcome found. Defect 1 is a missing guard for a correct behaviour; step 4 changes that code, so step 4 RED is the right place. |
| V2 | Repair | **Chose:** G7 needs a test before the slice closes. **Over:** no test (Undo). **Because:** D6B-15 (Repair) commits to the `duplicate name` error, and step 4 changes the `new_T_k` naming. **Commits us to:** one line in step 4 RED. | |
| V3 | Undo | G10 and the D6B-19 input field need no own test. | Same code path as tested cases; D6B-19 is interim (DL-101). |
| V4 | Undo | The `indirect` span loss is a note, not a defect. | It follows the D6B-28 text. A change is an OWNER question on D6B-28. |
| V5 | Undo | Review probes stay in scratch; the source lines and outputs are recorded here and in test-output.log. | Probes are review evidence, not fixtures. |

## Limits

- The probes cover compile-time rejects and the span shape. No runtime run of the probes.
- The `indirect` case was only compiled, not run against a host with ProbeSupport.
- Q6B-6 is unchanged by this step.
