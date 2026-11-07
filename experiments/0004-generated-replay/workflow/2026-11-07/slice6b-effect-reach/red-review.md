# RED review: slice 6b step 12 (spans on the EFFECT path) and 12b (a pure constructor)

**[Observed]** RED REVIEW, 2026-11-07. Fresh context. Not a Devil's Advocate. Git HEAD 474bcb93. No production file, no test, no fixture changed. `run.py` not run. No commit.
Compiler: scratch build (`git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --offline`), used through `BEAML_SPIKE`.
Read: [SKILL.md](../../../../../skills/implement-step/SKILL.md) (RED review), [plan.md](plan.md), [plan-review.md](plan-review.md), [decisions.md](decisions.md), [spec.md](spec.md), [notes.md](notes.md), [red-output.log](red-output.log), [byte-guard.py](byte-guard.py), DL-108, DL-119, DL-120, D018, `tests/slice6_effect_reach_test.py`, `slice6/effect-reach/orders.beaml`, `slice6/effect-reach/byte-guard.json`.
By: Opus (RED review, slice6b-effect-reach) for every judgement in this file.

## Verdict

- **Pass. No block.** Three medium objections (O1 to O3). GREEN may start; apply O1 with the deferred edits.
- By: Opus (RED review, slice6b-effect-reach)

## 1. Re-run (observed)

- Command: `BEAML_SPIKE=<scratch build> python3 -B experiments/0004-generated-replay/tests/slice6_effect_reach_test.py`.
- Result: 8 tests, 5 fail, 3 pass, 64 failed subtests. Same as `red-output.log`.
- Per test: span names 9, exact lines 6, runtime 5, E8 byte guard 40, 12b reject 4.
- Every failure is missing behaviour: 0 `setup:` failures; `elixirc --warnings-as-errors` passes; the runtime returns `{:ok, payment}` and logs the old `place` trace (`orders.prepare`, event in `orders.prepare`, `orders.finish`) for every caller; the 4 reject sources compile with exit 0.
- By: Opus (RED review, slice6b-effect-reach)

## 2. DL-119 faithfulness of `SPANS` (checked by hand)

| Clause | Steps | Expected | Judgement |
|---|---|---|---|
| `place` | prepare (pure), payments.authorize (EFFECT), finish (pure) | none in the clause | right: the EFFECT span is the `:client` span inside `payments_authorize`; `orders.prepare` and `orders.finish` go |
| `checkout` | prepare, place (reaches), tag | `orders.place` | right |
| `label`, `a`, `b` | pure, pure cycle | none | right |
| `ping` | pong (reaches through a cycle) | `orders.pong` | right |
| `pong` 1, 2 | ping; place | `orders.ping`; `orders.place` | right (two levels: ping -> pong -> place) |
| `by_id` | to_order (pure), place | `orders.place`, input `nil` | right (D6B-88) |
| `c1`, `c2`, `c3` | c2, c3, place | one span each | right (three levels to place) |
| non-pipe fns | none | none | right |

- No expected list is wrong. The runtime parents (`orders.place` as parent of the event and of the EFFECT span) also follow the call tree of DL-119.
- By: Opus (RED review, slice6b-effect-reach)

## 3. D6B-114 and the GEN query (Deferred edit 1)

- **[Verified]** The real `ProbeSupport.event/2` takes the current span context and the given operation; `order_id` is fixed `"order-1"`. The GEN router opens `orders.request` around `OrdersBeamlSpike.place(order)` (router line 16 to 18). So the event lands in `orders.request` with operation `prepare`; the edited `LOGS` row matches it. `unlinked_log` uses the new span name. `trace_shape` then expects exactly 4 spans.
- **[Inference]** The edited query finds the event and the request span.
- Log order: `test_exact_lines_per_clause` does not check line order. `test_runtime_spans_follow_the_reach` checks the log order (event before the EFFECT span), and E8 checks the exact bytes of `place` in `arms/gen/orders.beaml`. A GREEN that moves the event cannot pass both.
- By: Opus (RED review, slice6b-effect-reach)

## 4. E8 byte guard (`byte-guard.py`, `byte-guard.json`)

- **[Observed]** I loaded `byte-guard.py` as a module (no file write) and ran `sources()` and `expected()` with the scratch build: 71 of 71 rows give the stored code and sha256; 59 compile; 40 change.
- **[Observed]** A line diff of each pre-step output against its expected text: every removed line holds `ProbeSupport.span(`; every added line is a plain step call or `_ = ProbeSupport.event(...)`. Nothing else changes.
- A GREEN that also drops or moves other bytes fails the sha256 of that source.
- `byte-guard.json` is committed in the RED commit 474bcb93, so GREEN cannot change it without a visible diff. Limit: see O2.
- Step 13 (DL-121): **[Unknown]** whether its GREEN changes stdout. With `--stored stored/empty.jsonl` the check has no values to run. If step 13 changes output first, the E8 table, `EFFECT_OUTPUTS` (S12) and `BYTE_GUARD` (H8) are stale together; re-run `byte-guard.py` with a pre-step-12 build of the new base (notes.md already says so).
- By: Opus (RED review, slice6b-effect-reach)

## 5. 12b (DL-120)

- Two of four reject cases are transitive: `Ticket -> settle -> place -> payments.authorize` and `Settled -> place -> payments.authorize`. A GREEN that rejects only direct EFFECT steps fails 2 subtests. The exact text checks D6B-112 and the path of D6B-113.
- Guard `PURE_CONSTRUCTOR` keeps "an EFFECT in a lowercase fn, then a pure constructor". E8 keeps every existing constructor source compiling (code 0 rows).
- Gap: the D6B-113 tie rule (O3). Constructor -> constructor -> EFFECT is untested (notes.md states it).
- By: Opus (RED review, slice6b-effect-reach)

## 6. Deferred edits: completeness

- Edits 1 to 5 checked against the files. `slice6_struct_order_test.py` reuses `slice6_pipe_test.EFFECT_OUTPUTS`, so edit 4 also covers it.
- Not moved, confirmed: `drift_test.py` (LIB hashes only), `payments.generated.snapshot` (no pipe; row unchanged in E8), the slice 3 and 4 replay tests (call counts of `finish/1`, not spans), the GEN 0003 overlay tests (calls, not spans), `main.rs` unit tests (no step span text).
- Missing: `experiments/0001-syntax-to-beam/tests/cli.rs` (O1).
- By: Opus (RED review, slice6b-effect-reach)

## Objections

**O1 · Medium · The deferred edits miss a cargo test.**
- **[Verified]** `tests/cli.rs` `orders_cli_emits_flow_effect_decode_and_replay` (lines 293 to 298) compiles `arms/gen/orders.beaml` and requires `mentions` of `orders.prepare` and `orders.finish`.
- **Wrong outcome.** After a correct GREEN both names leave that output; `cargo test --no-fail-fast` fails. A GREEN worker that applies the list verbatim meets an unplanned failure and improvises the fix.
- **Repair.** Add deferred edit 6: remove `"orders.prepare"` and `"orders.finish"` from that list; keep `orders.payments.authorize` and `payment_request_prepared`; update the comment on line 293 ("the kept Orders log under orders.request", DL-119).
- **Smallest test.** `cargo test --no-fail-fast` in 0001 after GREEN.
- By: Opus (RED review, slice6b-effect-reach)

**O2 · Medium · `byte-guard.py` accepts any compiler.**
- **[Inference]** Run with a GREEN build, `expected()` is the identity, the "no span left" assert holds, and the script rewrites the table with the GREEN output. E8 then passes trivially. The risk is real when step 13 forces a re-run (section 4).
- **Repair.** In `main()`, assert that the changed count is 40 (or record the base commit and the compiler `src/main.rs` sha256 in the JSON), and state that only a `git archive` build of the pre-step-12 base may run it.
- **Smallest test.** Run the script with a GREEN build: it must stop, not write.
- By: Opus (RED review, slice6b-effect-reach)

**O3 · Medium · The D6B-113 tie rule has no test.**
- **[Inference]** Every reject case has one shortest path. A GREEN that takes the last step, or the first found by a depth-first walk, passes all 4 cases and gives a different text for another source.
- **Smallest test.** One more reject case with two equal paths on `WITH_PLACE`: `fn h1 o: Order -> Order ! PaymentError = o |> place |> to_order`, `fn h2 o: Order -> Payment ! PaymentError = o |> place`, `fn Settled order: Order -> Settled ! PaymentError = order |> h1 |> h2 |> Done`. Expect the path `Settled -> h1 -> place -> payments.authorize`.
- By: Opus (RED review, slice6b-effect-reach)

## Counts observed

- 8 tests: 5 fail, 3 pass; 64 failed subtests (9 + 6 + 5 + 40 + 4).
- E8: 71 sources, 59 compile, 40 change, 0 rows differ on re-computation, 0 non-span line changes.
