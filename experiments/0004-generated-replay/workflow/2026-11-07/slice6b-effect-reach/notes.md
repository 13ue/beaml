# Notes: slice 6b step 12 and 12b, Solve/RED

Phase: Solve/RED, 2026-11-07. Base: git HEAD 4f638c0b (the 0001 compiler tree is the same as at 1d32db0b). No commit. `run.py` not run.
The compiler was built only in a scratch copy (`git archive HEAD experiments/0001-syntax-to-beam`), used through `BEAML_SPIKE`.
No proposal files exist for this step (no Ponytail duel was run); the plan, the plan check and DL-119, DL-120 are the input.
By: Opus (RED, slice6b-effect-reach) for every entry in this file.

## Files

- Test: `tests/slice6_effect_reach_test.py` (own `compiler()` and `build`; imports only `arm_tree`).
- Fixture: `slice6/effect-reach/orders.beaml`; E8 table: `slice6/effect-reach/byte-guard.json`.
- E8 table tool: [byte-guard.py](byte-guard.py). Contract: [spec.md](spec.md). Evidence: [red-output.log](red-output.log).

## RED result (observed)

Command: `BEAML_SPIKE=<scratch build> python3 -B experiments/0004-generated-replay/tests/slice6_effect_reach_test.py`.
8 tests: 5 fail, 3 pass (guards). 64 subtests fail.

| Test | Case | Fails today because |
|---|---|---|
| `test_span_names_per_clause` | E1, E2, E4, E4c, E6 | 9 of 17 clauses. `place` has `orders.prepare`, `orders.finish`; no reaching step has a span. 8 pure clauses pass. |
| `test_exact_lines_per_clause` | E1 (first RED), E2, E4, E4c, E6 | 6 of 6 clauses miss the span line or the `_ = ProbeSupport.event(...)` clause. The D6B-89 check passes. |
| `test_runtime_spans_follow_the_reach` | E1, E2, E4, E4c, E6 | 5 of 6. The span log is the old `place` log (prepare, event, authorize, finish) for every caller. `label` (E3) passes. |
| `test_sources_keep_their_bytes_except_pure_step_spans` | E8 | 40 of 71 sources still have pure-step spans. 31 unchanged rows pass. |
| `test_constructor_that_reaches_an_effect_is_rejected` | 12b | 4 of 4 compile with exit 0. |
| `test_pure_pipes_stay_silent` | E3, E5 | Guard, passes. |
| `test_one_clause_rule_stays_for_a_direct_effect_step` | E7 | Guard, passes. |
| `test_fn_may_pipe_an_effect_result_into_a_pure_constructor` | 12b | Guard, passes. |

- **[Observed]** Every failure is a missing behaviour: the build exits 0, `elixirc --warnings-as-errors` passes, and the runtime EFFECT returns `{:ok, payment}` through the local TCP stub.
- **[Observed]** E2 under DL-119: the expected values of the plan for option P are gone; E2 is a full RED now, not an open case.

## Decisions

### Undo

- U1: The runtime harness has its own stubs: an Access-faithful `ProbeSupport.span/5` that logs `{:span, name, order["order_id"], parent}`, a span stack for the parent, `event/2` that logs the parent, and a local `:gen_tcp` payments stub. Over: the `slice6_decode_test.STUBS` with a file log. Because: the EFFECT then runs its generated transport, and the parent shows the tree of DL-119. (D6B-116)
- U2: E9 (`effect_reach_is_transitive` in `main.rs`) is GREEN work. RED must not edit `main.rs`. The Python cases cover the map through its effects. (D6B-115)
- U3: 12b covers 4 shapes: record and enum constructor, each direct and through helpers. A record literal is legal only in its constructor (DL-092), so the record constructor ends in a call of itself (`Ticket`). The direct shapes have no `place`, so the "exactly one pipe" rule does not fire first. (D6B-118)
- U4: The fixture pattern for the two `pong` clauses is a signature line plus a literal field pattern `Order { order_id: "loop" }`; the first clause pipes a record literal into `ping`. It compiles today and ends after one loop at run time.
- U5: The span sets are exact ordered lists per clause (`name#i`), so present and absent names are one assertion. A setup check compares the parsed clause keys with the table, so a parser fault is no false pass.
- U6: E3 and E5 stay guards. They pass today and must pass after GREEN; the span table also holds them.
- U7: New IDs D6B-112 to D6B-118. D6B-102 to D6B-111 are taken by the parallel step `slice6b-stored-elixir`. The main agent checks for a collision again before the commit.

### Repair

- D6B-112 · Repair · 12b text. Chose: `error: fn T: a constructor cannot reach an EFFECT: PATH (DL-120)` and `  help: call the EFFECT in a lowercase fn, then pipe its result into fn T`. Over: the D6B-91 original text with "(it reaches E)". Because: DL-120 asks for the constructor, the EFFECT and the path; the path ends in the EFFECT, so one line names all three. Commits us to: the path format below.
- D6B-113 · Repair · Path. Chose: `T -> f -> ... -> effect.name`, the shortest path; ties go to the first step in source order. Over: the first path found by the walk. Because: one stable text for each source. Commits us to: a breadth-first search over the reach graph for the message (the reach map gives sets only).
- D6B-114 · Repair · Pure-step form under DL-119 S. Chose: a pure step is the plain call (D6B-28 form), also in the EFFECT flow; the prepared event is the next `with` clause `_ = ProbeSupport.event(<<event>>, <<step>>)`; the operation stays the step name. Over: a block `pN = (result = f(pM); event; result)`, or an operation `request`. Because: the plain call is the existing pure form; `_ =` is a legal `with` clause and compiles under `--warnings-as-errors` (observed). Commits us to: 40 existing outputs change (E8); the GEN query must read the event in `orders.request` with operation `prepare` (Deferred edit 1).
- D6B-117 · Repair · E8 under DL-119. Chose: a table of 71 sources with the exit code and the sha256 of the pre-step output after a mechanical transform (remove each pure-step span, D6B-114 event form). Over: the plan E8 "byte-equal" (true under P only), or no guard. Because: a hash per source catches any other byte change. Commits us to: [byte-guard.py](byte-guard.py) is the rule; it asserts that no step span is left, which holds because no existing step reaches an EFFECT through a fn (plan-check scan).

## Deferred edits (files that `run.py` runs, or guards that step 12 moves)

Not applied. GREEN applies them after its own change, then re-runs the named tests.

1. `arms/gen/overlay/experiments/0002-http-correlation/query.py` (the GEN arm query, `run.py` release check):
   - Remove the rows `'orders.prepare': ('orders', 'internal', 'orders.request'),` and `'orders.finish': ('orders', 'internal', 'orders.request'),` from `CONTRACT`.
   - `LOGS = [('payment_request_prepared', 'orders.request', 'prepare'), ('payment_stub_returned', 'payments.authorize', 'authorize')]`.
   - Line 190: `for eventname,spanname,operation in LOGS:`. Line 193: `... and log.get('operation')==operation]`.
   - Line 196: `expected={e: s for e, s, _ in LOGS}.get(log.get('event'))`.
   - **[Inference]** The router opens `orders.request` around `place`, so the event lands in it. The LIB arm query stays (DL-110: retained evidence only).
2. `tests/arms_test.py`: `test_d2_L0_live_valid_body_baseline` (line 360) and `test_d2_L1_live_unknown_key_accepted_with_hint` (line 374): `"finish": 1` becomes `"finish": 0`, with the comment `# DL-119: finish is pure and has no span; the reply shows its result.` **[Inference]** L2 and L3 keep `"finish": 0`; that live check then holds trivially, the L2 `place` call count still shows that `finish` did not run.
3. `tests/slice6_constructor_test.py` `test_effect_pipe_keeps_its_spans` (lines 141 to 145): replace the `assertIn` with `self.assertIn("_ = ProbeSupport.event(%s, %s)," % (b("payment_request_prepared"), b("prepare")), stdout)` and `self.assertNotIn("ProbeSupport.span(%s" % b("orders.prepare"), stdout)`.
4. `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS` (S12): `arms/gen/orders.beaml` → `2b8dc63670aa2a9a3bcd889ec680e5bbc5a66ea789676d98045964cf50909fed`; `slice2/reuse/orders.beaml` → `597ad5824fca31814599e47e2761d191fbe190c0e728962687d1a71e2d045ab8`. Update its re-pin comment.
5. `tests/slice6_host_struct_test.py` `BYTE_GUARD` (H8): for each row whose key has `"changed": true` in `byte-guard.json`, the new value is that row's `sha256` (36 rows; the 9 unchanged rows keep their values).
- Not moved: `payments.generated.snapshot` (no pipe), the slice 2 to 5 replay tests (they read EFFECT spans only), the drift LIB hashes.

## Open points for the RED review

- **[Inference]** D6B-114 changes 40 generated outputs and the GEN release trace. DL-119 orders this; only the form is a default.
- **[Unknown]** The parallel step `slice6b-stored-elixir` (DL-121) may change outputs of sources with constructors before step 12 GREEN. Then `byte-guard.py` must run again on that base.
- **[Inference]** The runtime check runs the stubs, not the real `ProbeSupport` and OTel exporter. `run.py` (TEST phase) covers the GEN release path, which has no indirect pipe.
- 12b: a constructor that reaches an EFFECT only through a recursion through another constructor is not tested.
