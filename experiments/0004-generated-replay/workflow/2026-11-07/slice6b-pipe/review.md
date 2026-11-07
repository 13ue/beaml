# Slice 6b step 5: review

Fresh-context review (implement-step step 7). Not a Devil's Advocate round.
Inputs: [spec.md](spec.md), plan step 5 and D6B-24 to D6B-28 in [decisions.md](../slice6b-plan/decisions.md), DL-086, [red-review.md](red-review.md), [notes.md](notes.md) (GREEN P1 to P8), [test-result.json](test-result.json), the diff `git diff 44a90819..HEAD` of `main.rs`, `tests/slice6_pipe_test.py` and `slice6/pipe/`.
Base: HEAD `cd379ff0`, clean tree. No code or test was changed by this review.

## Verdict

**PASS. No block.** Two medium notes, two low notes.

## Step met

| Contract point | Evidence |
|---|---|
| Pipe in call argument, record field value, clause body (DL-086) | **[Observed]** `piped` is used in the three places. `g`, `last`, `cat`, `Pair`, `box` compile and run (9 of 9 runtime subtests). |
| `+` binds first (D6B-25) | **[Observed]** `cat("a","b","c") == "(ab)-c"`; unit test `pipe_in_any_expression`. |
| Step kinds (D6B-26) | **[Observed]** fn, variant (`box`), constructor (`pick`, probe p7); variant texts are guards since step 4. |
| D6B-27 nested EFFECT or failing step | **[Observed]** Call argument and record field value rejects, exact text plus `help:` line. |
| D6B-28 whole-body pure pipe in several clauses, `with` | **[Observed]** `pick` `with` line and four runtime cases. |
| One-clause rule, spans, `emit_chain` for EFFECT pipes | **[Observed]** Whole-body path unchanged (P7). S12 hash guards pass. Probe p5b. |
| Nested pipe as plain calls | **[Observed]** `emit_node` fold; probes p2b, p2c, p6, p7. |
| Test count 11 to 12 | **[Observed]** O2 test added before `main.rs`, RED on `44a90819` (green-output.log section 2). Consistent with RED review O2 and notes.md. |

## Adversarial probes

Compiler: `experiments/0001-syntax-to-beam/target/debug/beaml-spike` built from HEAD `cd379ff0`. Sources in the scratch directory only. HEAD for p1 to p4, p6, p7: `f s: String -> String`, `g s: String -> String`, `j a: String, b: String -> String`.

| # | Source (last line) | Exit | Exact output |
|---|---|---|---|
| 1a | `fn p x: String, y: String -> String = x \|> f + y` | 1 | `expected identifier at byte 171` |
| 1b | `... = j(x \|> f + y, y)` | 1 | `expected ',' at byte 173` |
| 2a | `fn p a: String -> String = (a \|> f) \|> g` | 1 | `expected expression or pattern at byte 153` |
| 2b | `... = j(a \|> f \|> g, a)` | 0 | `__MODULE__.j(__MODULE__.g(__MODULE__.f(v_a)), v_a)` |
| 2c | `... = j(j(a \|> f, a) \|> g, a)` | 0 | `__MODULE__.j(__MODULE__.g(__MODULE__.j(__MODULE__.f(v_a), v_a)), v_a)` |
| 3 | `fn w n: Int -> NonZeroInt ! IsZero = keep(n \|> NonZeroInt)` | 1 | `error: fn w: a nested pipe has the failing step NonZeroInt` / `  help: make the pipe the whole body` |
| 3b | `... = keep(n \|> NonZeroInt \|> keep)` | 1 | same text |
| 4 | `fn p B { v: x \|> f } -> String = x` | 1 | `expressions are not patterns` |
| 4b | `fn p (x \|> f) -> String = x` | 1 | `expected expression or pattern at byte 131` |
| 5 | orders `place` as 2 clauses, both whole-body EFFECT pipes | 1 | `a function with a pipe body has one clause in slice 1: place` |
| 6 | `fn p r: String -> Outcome = Declined(r \|> f)` | 0 | `{"Outcome", "Declined", [__MODULE__.f(v_r)]}` (binary form) |
| 7 | `... = j(r, r \|> W \|> show)`, `W` a 1-input constructor | 0 | `__MODULE__.j(v_r, __MODULE__.show(__MODULE__.new_W_1(v_r)))` |
| 8 | orders `place` = `prepare(order \|> prepare) \|> payments.authorize \|> finish` | 1 | `slice 1 replays a flow with one parameter that starts its pipe and calls payments.authorize once: place` |

- **(1) [Observed]** The plan (D6B-25) makes `\|>` weaker than `+`, so `x \|> f + y` has the step `f + y`. Steps are bare names, so the source is not valid. The code rejects it at parse; it never gives `f(x) + y` or `f(x + y)`. Correct, but the text is a byte offset only.
- **(2) [Observed]** Parentheses do not hold a pipe. A pipe chain in an argument and a pipe whose head holds a pipe compile to correct nested calls.
- **(3) [Observed]** D6B-27 forbids a nested failing step, also when the outer `fn` declares the failure. The code rejects with the D6B-27 text. P3 settles the message order for a `fn` without a matching `!` the same way.
- **(4) [Observed]** Expected text.
- **(5) [Observed]** One-clause rule fires with its existing text. S12 byte guards pass in the TEST run.

## Notes

**N1 · Medium · A parenthesized pipe does not parse.**
- Plan step 5 says `Node::Pipe` moves into `node()`. The code adds `piped` around `node` (P1). So `(a \|> f) \|> g`, `(x \|> f) + y` and a pipe as an operand of `+` give a parse error.
- Consequence: no wrong output; a source is rejected with `expected expression or pattern`. DL-086 says "any expression". The spec names only argument, field value and body, so the step is met.
- Minimum repair, if wanted: parse `piped` inside the parenthesized form of `node`. One test: `(a \|> f) + a`. Class Undo.

**N2 · Medium · Probe 8 changes its reject text without a test.**
- On `44a90819` the source failed with `expected ','`. Now the slice 1 flow rule rejects it. This is correct and existing behavior. No test pins it. Class Undo.

**N3 · Low · Parse texts for `x \|> f + y` carry only a byte offset.** Accepted Undo point of the RED review.

**N4 · Low · P5 prefix compare.** `body` adds `fn F` by a prefix compare on the own text. Only caller today. Accepted.

## Nothing beyond need

- **[Observed]** One helper, one step loop shared by both pipe forms, one emit arm, one unit test, one added Python test. No new texts other than the two D6B-27 texts. No signature, span or event change.

## Decisions

| # | Class | Choice | Reason |
|---|---|---|---|
| V1 | Undo | Verdict PASS | Every contract point has a passing check; probes show no wrong output. |
| V2 | Undo | N1 is a note, not a block | Spec positions are met; reject is safe, no silent wrong value. |
| V3 | Undo | Probes stay in the scratch directory, not in the test file | Review changes no test. |
| V4 | Undo | 11 to 12 tests accepted | RED review O2 asked for the test; it was RED before `main.rs`. |

## Limits

- Probes check compile output only; no runtime run for probes 2b, 2c, 6, 7.
- The OWNER question on the span of an indirect EFFECT pipe (D006, Q6B-7) is not touched.
