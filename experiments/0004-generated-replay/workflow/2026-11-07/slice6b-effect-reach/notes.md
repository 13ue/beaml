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

## GREEN

Phase: GREEN, 2026-11-07. Base: git HEAD a42a701c. No commit. `run.py` not run.
By: Opus (GREEN, slice6b-effect-reach) for every entry in this section.

### Changes in `experiments/0001-syntax-to-beam/src/main.rs`, by function

- `Checker` (struct, `new`): new field `reach: BTreeMap<signature key, BTreeSet<EFFECT name>>` (D6B-84).
- `validate`: now `&mut self`. After the flow checks it sets `reach` and runs `pure_constructors`. The two callers (`build_with_refusals`, `formatted`) take `let mut checker`.
- `edges` (new): the call edges of each signature key in source order: whole-body pipe step targets, call forms, nested pipe steps, record field values (D6B-85).
- `callees` (new): the recursive walk over `Node` for `edges`.
- `reach_map` (new): the fixpoint over `edges` (D6B-84). A `ponytail:` comment names the O(n x e) ceiling.
- `reaches` (new): true when a key reaches an EFFECT.
- `pure_constructors` (new, DL-120): the D6B-112 text with a breadth-first path over `edges` (D6B-113).
- `emit_chain`: new parameter `head` (the span input). The D6B-28 `spans` flag is gone. A live step has a span only when it reaches an EFFECT (DL-119 S). A pure step is a plain call. After the step before a direct EFFECT step (not failing), the next `with` clause is `_ = ProbeSupport.event(...)` (D6B-89, D6B-114).
- `emit`: computes the span input: `p0` for a plain record head, else `nil` (D6B-88). The REPLAY RUN call passes `p0` (not used there).
- Tests: new unit test `effect_reach_is_transitive` (E9, D6B-115): a chain, a reaching cycle, a pure cycle.

### Deferred edits applied

1. GEN `query.py`: `orders.prepare` and `orders.finish` rows removed from `CONTRACT`; `LOGS` with three columns; loop and `operation` check and `expected` as in the list.
2. `arms_test.py` L0 and L1: `"finish": 0` with the DL-119 comment.
3. `slice6_constructor_test.py` `test_effect_pipe_keeps_its_spans`: the `_ = ProbeSupport.event(...)` assert and the `assertNotIn` of `orders.prepare`.
4. `slice6_pipe_test.py` `EFFECT_OUTPUTS`: the two new hashes; the re-pin comment names step 12.
5. `slice6_host_struct_test.py` `BYTE_GUARD`: 36 rows take the `byte-guard.json` sha256; 9 rows unchanged; a comment line names the re-pin.
6. O1: `tests/cli.rs` no longer requires `orders.prepare` and `orders.finish`; the comment names `orders.request` and DL-119.

### Test tightening (RED review O2, O3)

- O2: E8 asserts `(71, 40)` = (rows, changed rows) of `byte-guard.json` before the row checks. `byte-guard.py` asserts 40 changed rows before it writes. Observed: run with the GREEN build, it stops with `BEAML_SPIKE is not a pre-step-12 build` and writes nothing.
- O3: new 12b case `enum_equal_paths` (`h1`, `h2`, two paths of length 3). Expected path: `Settled -> h1 -> place -> payments.authorize`.

### Results (observed)

- `cargo fmt --check`, `cargo clippy -- -D warnings`: clean. `cargo test`: unit 20 of 20, `cli.rs` 14 of 14.
- Pass: `slice6_effect_reach_test` 8 of 8, `slice6_constructor` 25, `slice6_decode_ctor` 8, `slice6_decode` 10, `slice6_enum` 20, `slice6_failure` 22, `slice6_fmt` 25, `slice6_host_struct` 3, `slice6_int` 16, `slice6_pipe` 12, `slice6_record` 5, `slice6_struct_order` 3, `drift_test` 5, `slice3_types` 69, `slice4_retire` 87, `slice5_rewrite` 5, `slice5_squash` 24.
- Fail, expected: `slice6_stored_elixir_test` 9 of 15 (step 13 RED, commit b0802087; not this step).
- Fail, cause A (19 tests): `arms_test` 2 of 11 (L2, P1), `slice2_replay` 5 of 21, `slice3_replay` 6 of 31, `slice4_replay` 2 of 27, `slice5_replay` 4 of 12. Every one is an eval VM `place` call that raises `FunctionClauseError`.
  - **[Observed]** The `arms_test` HARNESS calls `OrdersBeamlSpike.place(order)` with no open span (no router). The real `ProbeSupport.event/2` (0002 `probe_support.ex` line 86) calls `OpenTelemetry.Span.hex_trace_id(current_span_ctx())`. `otel_span:hex_trace_id/1` matches only a `#span_ctx{}`, so `:undefined` raises.
  - **[Inference]** Before step 12 the event stood inside the `orders.prepare` span, so a span context was always there. D6B-114 moves it out. The RED runtime stubs hid this (notes.md, "Open points").
  - Not changed. Fixes need a host or harness change outside the deferred list: see the decisions below.
- Fail, cause B (33 subtests): `slice5_syntax_test` F01 (2) and A2 (31) compare the output with the output of the PIN compiler `0747c315`. The only differences are the DL-119 span lines. A re-pin of these guards is not in the deferred list. Not changed.

### Decisions

Undo:
- `reach` is a `Checker` field, set in `validate` (the default of decisions.md).
- The 12b check runs last in `validate`, so every earlier error text stays first.
- The prepared event keeps the old condition: only when the step before the EFFECT cannot fail (same bytes as `byte-guard.py`).
- `fmt` also runs the 12b check, because it calls `validate`.

Repair:
- D6B-113 path: chose a breadth-first search over the source-ordered edges, over a depth-first walk, because it gives the shortest path and the first one in source order. Commits us to: a second `edges` pass per compile.
- O2: chose a count assert in the test and in `byte-guard.py`, over a recorded base hash, because it is one line in each and a GREEN build gives 0 changed rows.

Migrate (stop, for the main agent and the OWNER):
- Cause A, the event outside any span. Options: (1) `ProbeSupport.event/2` accepts no span context (`trace_id`/`span_id` nil) in 0002 `probe_support.ex`; (2) the eval HARNESS opens an outer span around `place`; (3) change D6B-114 back to an event inside a span. Each option changes a file outside this step, or a decision.
- Cause B, `slice5_syntax_test` F01 and A2: re-pin PIN to the step 12 compiler, or apply the `byte-guard.py` transform to the PIN output.

## GREEN follow-up (main agent decisions on cause A and cause B)

By: Opus (GREEN, slice6b-effect-reach) for every entry in this section, unless a line says otherwise.

### Cause A: the event with no open span

- **D6B-127 · Repair · `ProbeSupport.event/2` does not raise when no span is open.** Chose: with no current span context (`:undefined`), the event records `trace_id` and `span_id` as the literal `"none"`. No fresh span, no crash. Over: the eval HARNESS opens a span around `place`; the event back inside a span. Because: a host that calls `place` without an open span is a real production situation until an entry point is declared (D018). Generated code must not crash at the host boundary. The harness must not fake a span that the host does not have. Commits us to: a log row with `"none"` has no span link; the GEN `query.py` does not see it (it reads only router runs). Decision by: Fable (main agent, GREEN follow-up); edit by: Opus (GREEN, slice6b-effect-reach).
- File: `experiments/0002-http-correlation/apps/probe_support/lib/probe_support.ex` (`event/2`). **[Observed]** It is the only tracked copy outside `results/`. The copies under `results/` are retained run evidence and stay unchanged.
- **[Observed]** The DRIFT repair JSONs (`arms/gen/repair/*.json`, `arms/lib/repair/*.json`) replace only the `valid_payment!` line of this file. `event/2` is not in them. `drift_test.py` re-run: see the counts below.
- ID check: D6B-127 was free at this edit (highest found: D6B-126). The main agent checks for a collision again before the commit.
- Prototype follow-up (**[Proposal]**): a declared entry point gives the root span. Then the event always has a span, and `"none"` stays only for an undeclared host call.

### Cause B: the slice 5 byte pin

- Rule (main agent): as in [the 6a re-pin](../slice6b-records-v2/repin.md). R-EQ stays BASE `f29e3f12` against PRE 6A `4a7cffba`. The byte pin moves from `0747c315` to the step 12 compiler.
- **Diff proof [Observed].** PIN `0747c315` (scratch `git archive` build) against the step 12 working tree build. Sources: the 47 A2 sources (`rewrite_sources()`) and 21 B5 texts (fixture and 20 random draws). `--stored stored/empty.jsonl` for a source with `effect` or `retire`. `difflib` per line; each changed line is a removed `ProbeSupport.span(..., :internal, p0, ...)` step line or an added plain step call or `_ = ProbeSupport.event(...)` clause.
  - Exit code and stderr: equal for all 68.
  - 52 change (31 A2, 21 B5), 16 A2 do not change. 104 hunks, 0 elsewhere.
  - Hunk locations, the same in each of the 52 (PIN lines / step 12 lines), in `__beaml_place`: `35/35-36` (the `prepare` span becomes the call and the `_ =` event clause) and `37/38` (the `finish` span becomes the call). Exception: `drift/Q/orders.beaml` is one line later (`36/36-37`, `38/39`).
- **The pin line is not changed yet.** `PIN` in `tests/slice5_syntax_test.py` is a commit for `git archive`. The step 12 compiler has no commit (workers do not commit). The main agent commits `experiments/0001-syntax-to-beam` first, then sets `PIN` to that commit, as in commit `1bd1217b` after `0747c315`. Comment update for line 36: "PIN, the step 12 compiler (DL-119), pins the bytes; before: 0747c315 (step 6a)."
- **[Observed]** Check without a commit: `slice5_syntax_test` run with `PIN` mapped to the working tree build in memory (scratch runner, no file change): 60 of 60 OK. R-EQ passes unchanged.
- **[Observed] Re-run after D6B-127** (test files unchanged except as listed above): `arms_test` 11/11, `drift_test` 5/5, `slice2_replay` 21/21, `slice3_replay` 31/31, `slice4_replay` 27/27, `slice5_replay` 12/12. slice6: constructor 25, decode_ctor 8, decode 10, effect_reach 8, enum 20, failure 22, fmt 25, host_struct 3, int 16, pipe 12, record 5, struct_order 3, all OK. `slice6_stored_elixir_test` not run (step 13 RED). `slice5_syntax_test` with the file as is: 33 fail until `PIN` moves; with `PIN` mapped in memory: 60/60.
