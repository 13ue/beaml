# Review: slice 6b step 4 (`slice6b-enum`)

**[Proposal]** Fresh-context REVIEW, 2026-11-07, pipeline step 7. Not a Devil's Advocate round. No code and no test changed. No commit.
Read: `spec.md`, `notes.md` (Solve, RED, RED repair, GREEN E1 to E13), `red-review.md`, `green-output.log`, plan step 4 and step 7, D6B-13 to D6B-28, D6B-39, D6B-51, DL-082 to DL-088, DL-100, DL-102, DL-103, the diff `git diff 80bd33cd..HEAD` for `main.rs`, `slice6_enum_test.py` and `slice6/enum/`, and [test-output.log](test-output.log) / [test-result.json](test-result.json).

## Verdict

**PASS.** No critical or high defect. Three medium notes and open Undo points stay open (below).

## TEST result (observed, HEAD `f74be40c`)

All checks pass. See [test-result.json](test-result.json). `cargo fmt --check`, `cargo clippy -D warnings`, `cargo test` (16 unit, 14 CLI), `slice6_int` 16, `slice6_failure` 22, `slice6_constructor` 25, `slice6_enum` 20 OK. EXPERIMENT 0001 pass (`results/20261107T122342047917Z`). `run.py` 0004 pass in 23 min (`results/20261107T122317702373Z`, sub-run directories kept). `lint_wiki.py` 0 errors.

## Step check

| Contract item | Evidence | Result |
|---|---|---|
| Bare variant `A` = `A()` in enum, pattern, expression (D6B-20) | parser `Node::Call(name, [])`; fixtures `pending`, `label Authorized` | met |
| Literal `V = "text"`, payload or literal (DL-098) | `literal_rules`; S10, R7 tests | met |
| Unique literal (D6B-23) | S11 test | met (exact compare, probe 4) |
| Literals or constructor (DL-088, D6B-22 text) | S6 test, unit test | met |
| Several signatures for a constructor, one for a lowercase `fn` (D6B-13, D6B-14) | KEY `T#k`; S14 guard; probe `pa` | met |
| Unreachable signature by `(name, TYPE)` set, unreachable clause per signature (D6B-23, DL-087) | S8, S9, R3, R4, R5 tests | met |
| `def new_E_k` per signature, clauses in source order (D6B-15, D6B-24) | build assertions, runtime 12 subtests | met |
| Static call choice: first signature whose arity and TYPES fit (D6B-16) | `pick`; R8 runtime; probe 1 | met |
| Variants built directly in any `fn`, no only-way-in check (DL-100) | `bare_variant_in_fn` runtime | met |
| No new function for ENUM LITERALS | S17 assertion | met |
| One-clause rule kept for an EFFECT pipe body (R1, D6B-28) | guard test | met |
| Counts: spec 19, file 20 (G7) | `slice6_enum` 20 OK | consistent |

## Adversarial probes (observed, scratch sources, compiled with `target/debug/beaml-spike`, not retained)

| # | Source | Exact output | Reading |
|---|---|---|---|
| 1 | `fn Outcome code: String` (clauses `"ok"`, `other`), then `fn Outcome status: String` (clause `s -> Approved`), `fn pick c: String -> Outcome = Outcome(c)`, `fn pipe c: String -> Outcome = c \|> Outcome` | exit 0. `__beaml_pick(v_c), do: __MODULE__.new_Outcome_1(v_c)`; pipe step `p1 = __MODULE__.new_Outcome_1(p0)`. Runtime: `pick("zz")` = `{"Outcome", "Other", ["zz"]}`, `pick("ok")` = `Approved`, `pipe("zz")` = `Other("zz")`, `new_Outcome_2("zz")` = `Approved` | Code calls and pipe steps always run `new_Outcome_1`. "First match wins" is observable: signature 2 would give `Approved` for `"zz"`. `new_Outcome_2` is reachable only by a direct host call now, and by decode in step 8 (other key). Agrees with D6B-16 and D6B-23. |
| 2a | literal enum `PaymentState` as field `state` of the EFFECT output `Payment` | exit 1, `effect payments.authorize: slice 1 decodes String fields only, not Payment.state` | A compile error, but not a D6B-39 text. |
| 2b | same, `type Payment v2 { ... }` (VERSION MARK) | exit 1, same text | D6B-39 has no own text yet. The plan puts D6B-39 in step 7 (step 7 exclusions). Not a step 4 defect. |
| 3 | `fn f -> E = Zed` and `fn f x: String -> E = Zed(x)`, `Zed` neither variant nor TYPE | exit 1, `unknown function: Zed` (both) | Error, today's text (E2). |
| 4 | `enum PaymentState { Authorized = "ok"  Approved = "OK"  Unknown(String) }` | exit 0 | Literals compare exactly. Both are reachable only if the step 7 decode also compares exactly. |
| 5 | constructor `fn Outcome code: String` with clause `"ok"` only; also with a second signature `n: Int` with clause `0` | exit 1, `non-exhaustive function: Outcome` (both) | An error. The text does not name the signature (open Undo point). |
| extra | clause before the first signature line | exit 1, `error: fn Outcome: a clause stands before the signature line` / `  help: move the signature line above the first clause` | D6B-13 kept. |
| extra | bare payload variant `fn f -> E = B` with `B(String)`; pattern `fn f B -> String` | exit 1, `call arity mismatch: B`; `constructor arity mismatch: B` | Error. |
| extra | three signatures `code: String`, `n: Int`, `flag: String` | exit 0 | Equal TYPES with another name stays reachable (D6B-23). |

## Notes (medium, no block)

- **N1 · medium · D6B-39 has no own text.** **[Observed]** Probe 2: a literal enum in an EFFECT output field fails with the slice 1 String-only text, with and without a VERSION MARK. **[Inference]** Step 7 removes that guard for literal enums. If step 7 does not add D6B-39 at the same time, a versioned output TYPE with an enum field compiles. **Repair (step 7):** the step 7 RED adds a reject for an enum field in a versioned EFFECT output TYPE.
- **N2 · medium · Several-signature behaviour without a test.** **[Observed]** E5 (two signature lines of a record constructor) and E10 (pure pipe in a several-clause lowercase `fn`) compile (GREEN probes). No test fixes them. A later change can remove them without a signal. **Repair (next step that touches signatures or pipes, step 5 is fitting for E10):** one accept test each.
- **N3 · medium · Exact literal compare.** **[Observed]** Probe 4. **[Inference]** If the step 7 decode folds case, `Approved` becomes unreachable without an error. **Repair (step 7):** keep an exact compare in decode, or add a case-fold check here at the same time.

## Other observations

- **[Observed]** `elixirc --warnings-as-errors` (Elixir 1.18.1) gives exit 0 with an `unused import Kernel.<>/2` warning on the step 4 constructor fixture. The fixed import header gives this warning. The harness guard "no warning" is therefore weaker for import warnings. Not caused by step 4 logic.
- **[Observed]** `run.py` does not run the slice 6 tests. They ran separately here.
- **[Observed]** `slice6_pipe_test.py` (step 5 RED, commit `90f90cb4`) is in the same range. It is outside this review.

## RED, reviews and GREEN consistency

- RED: 12 tests, 11 FAIL, then after repair 19 tests, 17 FAIL, 2 guards pass. Each failure is a compiler message (red-review.md rerun). Genuine.
- RED review: O1 (high) answered by R1, O2 by R3 and R4, O3 by R5. Undo points R6 to R8 added.
- GREEN: G7 test written first and failed (`expected '(' at byte 240`) before the `main.rs` change. 20 of 20 now.
- E5 and E10 are Repair, confirmed by the main agent within DL-085 and R2. Commits recorded in notes.
- Nothing beyond need found: E4 (variant without a literal) follows D6B-21 "every variant has a literal"; E11 (G7 for k > 1) follows D6B-15.

## Open Undo points (unchanged, no block)

- Text for a call that fits no signature (D6B-16 "names the argument TYPES"). Today: signature 1 texts (E7).
- `non-exhaustive function: E` does not name the signature (probe 5).
- E4 text for a variant without a literal: no test.
- D6B-51 (enum without a decode path in an EFFECT output): no plan step.

## Decisions of this review

| Class | Choice | Reason |
|---|---|---|
| Repair | PASS over BLOCK | All contract items met, probes give errors or the D6B-16 value, no wrong outcome in step 4 scope. |
| Repair | N1 and N3 go to step 7, over a step 4 repair | D6B-39 and decode are step 7 scope (plan step 7 exclusions). |
| Undo | N2 is a note, not a block | E5 and E10 were confirmed as Repair. Missing tests remove no current behaviour. |
| Undo | Probe 3 and probe 5 texts accepted | Open Undo points. Each gives exit 1 with a message. |
| Undo | Probes not retained as files | Task: change no tests. Sources and outputs are in this table. |

## Limits

- The probes ran on scratch sources only. Byte-equal outputs against HEAD~ were not rebuilt here. The `run.py` suite and the snapshot check cover `payments.beaml`.
- Probe 2b did not add a MIGRATE CHAIN. It used a VERSION MARK only.
