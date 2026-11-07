# PLAN CHECK: slice 6b step 12 (spans follow the EFFECT reach)

**[Proposal]** PLAN CHECK, 2026-11-07. Fresh context. Not a Devil's Advocate. No production file changed. `run.py` not run.
Read: this ledger (`plan.md`, `plan.json`, `decisions.md`), the [step 11 ledger](../slice6b-host-structs/plan.md), DL-092, DL-100, DL-101, DL-105, DL-106, DL-108, DL-110, the [step 6 plan](../slice6b-redacted/plan.md), `experiments/0001-syntax-to-beam/src/main.rs` (`emit_chain`, the one-clause rule, `flow`, the service-name check), `experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex` (`span/5`), the GEN `query.py`.
By: Opus (PLAN CHECK, slice6b-effect-reach) for every entry in this file.

## Verdict

- **No block on step 12.** E1 is a genuine RED: **[Verified]** `emit_chain` sets `spans` from direct EFFECT steps only (main.rs, D6B-28 line).
- **Block on 12b** until the OWNER answers D6B-91 (O1).

## Scan: does option P change a fixture?

- **[Observed]** A regex scan of 79 `.beaml` files outside `results/` (all of `experiments/**`). It builds the pipe and call edges per fn and runs a fixpoint over them. Result: 0 fns that reach a dotted EFFECT only through another fn. 52 files have a direct EFFECT pipe step.
- **[Observed]** The same scan over 11 inline sources (Python test constants and `main.rs` string literals with `effect` and `|>`): 0 indirect pipes.
- **[Observed]** Only one direct EFFECT pipe has a non-record head: `examples/order-flow.beaml` (`order_id: String`). It does not compile (it uses `interface`). So D6B-88 changes no existing byte.
- Limit: the scan does not see sources that tests build by string replace at runtime. E8 (the `git archive` byte guard) covers the files.
- **[Inference]** The planner's claim holds. Under option P no existing output changes.

## Objections

**O1 · High (for 12b) · D6B-91 is a new language rule. Raise it to Migrate.**
- **[Observed by the planner]** An enum constructor can be the EFFECT flow today, and it compiles. D6B-91 makes every constructor that reaches an EFFECT a compile error.
- **[Verified]** DL-092, DL-100, DL-101 and DL-108 do not restrict what a constructor calls. So the reject is a new rule on syntax that compiles today. The planner states that a later ban after use is Migrate; the ban now removes a form that the OWNER did not remove.
- Real options for the OWNER: (a) reject every constructor that reaches an EFFECT; (b) reject only where the compiler calls the constructor itself (a decode field, the step 8 `--stored` check, the host `T.new`); (c) allow it and give it spans, and the REPLAY RUN substitutes the inner EFFECT.
- **Wrong outcome if it stays Repair.** A source with an EFFECT in an enum constructor stops compiling without an OWNER choice.
- **Smallest test (12b RED, after the answer).** The planner probe source `fn Settled order: Order -> Settled ! PaymentError = order |> payments.authorize |> Done` gives the chosen result.
- By: Opus (PLAN CHECK, slice6b-effect-reach)

**O2 · Medium · A fixed two-pass loop passes E4, E5 and E9.**
- **[Inference]** E4 (`ping` before `pong`) needs two passes in source order. E5 catches "in progress counts as reach". A fixed loop of two passes passes both. It gives a wrong empty set for a longer chain.
- **[Inference]** A real "until nothing changes" loop over set unions is monotone and stops at the right result. A cycle cannot stop it early.
- **Smallest test.** Add to the fixture, in this source order: `fn c1 o: Order -> Payment ! PaymentError = o |> c2`, `fn c2 ... = o |> c3`, `fn c3 ... = o |> place`. E9: `c1` maps to `{payments.authorize}`. A two-pass loop gives the empty set for `c1`.
- By: Opus (PLAN CHECK, slice6b-effect-reach)

**O3 · Medium · D6B-88 `nil` drops the span from the per-order trace.**
- **[Verified]** `ProbeSupport.span/5` writes `order_id: order["order_id"]`. The GEN `query.py` selects span rows by `attributes.order_id` (line 149).
- **[Inference]** With `nil`, the outer span of `by_id` (E6) has `order_id: nil`. The query drops it from the order trace. The inner spans of `place` keep `order_id`, because their `p0` is an `Order`. So the EFFECT spans stay; the helper span gets lost.
- **[Inference]** `nil` is safe: Access on a String, an Int or a struct raises. No existing byte changes (scan above). So it stays Repair.
- **Smaller-loss alternative for the worker or the OWNER.** Pass the nearest plain record: `p0` if the head is a plain record, else the step input `pN` if its TYPE is a plain record, else `nil`. Same bytes for every existing source.
- **Action.** Record the loss as a limit in `plan.md`. E6 asserts the `nil` form as planned.
- By: Opus (PLAN CHECK, slice6b-effect-reach)

## Defaults checked (no change)

- D6B-84, D6B-85, D6B-86, D6B-89, D6B-90, D6B-92 to D6B-95: consistent with DL-108.
- D6B-87: **[Verified]** the one-clause rule fires only for a whole-body pipe with a direct EFFECT step (main.rs, `Checker::new`). `flow()` picks the direct pipe only. A several-clause reaching fn compiles today without spans. So D6B-87 removes no syntax. E7 tests both sides.
- D6B-88: no data loss today, because no existing pipe has a non-record head. See O3 for new pipes.

## Defaults to raise to Migrate

- **D6B-91** (O1). Not part of step 12. 12b waits for the OWNER.

## OWNER question Q6B-17

- Options P (per pipe) and S (per step) are real. DL-108 says "Pure steps stay silent". S is the literal reading; P is the byte-safe reading. The question is right.
- **Missing option H, hybrid.** A pipe with a direct EFFECT step keeps today's spans (P). A pipe that reaches an EFFECT only indirectly gets spans on its reaching steps only (S). No existing byte changes. The GEN `query.py` rows stay. Challenge: two span rules in one compiler.
- E1 holds under P, S and H. E8 holds under P and H.

## Order

- **6a, then 11, then 12, then 12b, then 6b, then 6c: sound.**
- 11 before 12: D6B-88 gives `nil` for a constructor TYPE head as a map or as a struct, so 12 does not need 11 for logic. 11 first lets E6 add a struct head case. Keep.
- 12 before 6b: 6b redacts the span input. With 12 first, 6b sees every spanned pipe. The hand-off (one indirect span case in R2) stays. Note for 6b: an indirect pipe head can be a plain record that holds a struct field (a TYPE that is not an EFFECT input). D6B-19 does not cover that head.
- 12b after 12: it needs the reach map. 12b is blocked by O1.
- 6c is independent of 12.
