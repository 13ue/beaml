# Plan: slice 6b step 12, spans follow the EFFECT reach of every fn

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no commit, no `run.py` run.
Decision: DL-108 (Q6B-7, C) in [the decision log](../../../../../wiki/planning/decision-log.md). Also read: DL-092, DL-093, DL-099, DL-101, DL-105, DL-106, DL-107, DL-109, DL-110; the [slice 6b plan](../slice6b-plan/plan.md) (D6B-25 to D6B-28), its [decisions](../slice6b-plan/decisions.md) and [plan review](../slice6b-plan/plan-review.md); the GREEN sections of the [step 2](../slice6b-failure/notes.md) (H1 stub), [step 3](../slice6b-type-constructor/notes.md) (G13, G14), [step 5](../slice6b-pipe/notes.md) (P3, P6, P7) and [step 8](../slice6b-decode-constructor/notes.md) (G4, G7) ledgers; the step 4 ledger E10 and R1; the [step 6 plan](../slice6b-redacted/plan.md); the [step 11 plan](../slice6b-host-structs/plan.md); `experiments/0001-syntax-to-beam/src/main.rs`.
Design decisions that DL-108 does not settle: [decisions.md](decisions.md) (D6B-84 to D6B-95, OWNER question Q6B-17). Machine form: [plan.json](plan.json).
By: Opus (PLAN, slice6b-effect-reach) for every proposal in this file (DL-107).

## Facts the step builds on (observed at HEAD 8924cb3f)

- **[Verified]** `emit_chain` sets `spans = steps.iter().any(|s| self.effect(s).is_some())` (D6B-28, step 3 G13). Only a whole-body pipe with a direct EFFECT step has spans.
- **[Observed]** Probe in the scratch directory with the current debug binary: `fn checkout order: Order -> Payment ! PaymentError = order |> prepare |> place |> tag`, where `place` is the EFFECT flow, compiles to a plain `with` with no `ProbeSupport` call. This is the DL-108 case.
- **[Verified]** No call graph exists. `referenced_names` collects variable names only. The dead-line code (`dead_lines`) works on MIGRATE and RETIRE LINES, not on calls.
- **[Verified]** A fn that can fail cannot be a call form (`X can fail: call it as a pipe step`) or a step of a nested pipe (D6B-27). Every EFFECT has a failure TYPE. The `!` rule puts the failures of every step into the `!` list of its fn.
- **[Inference]** So today only whole-body pipe steps can reach an EFFECT. Call forms and nested pipes are graph edges that cannot reach today. They can when a failure can be handled (a later `case` or `with ... else`).
- **[Observed]** Probe: mutual recursion through whole-body pipe steps (`fn a o = o |> b`, `fn b o = o |> a`) compiles. So the graph has cycles.
- **[Observed]** Probe: an enum constructor can be the EFFECT flow (`fn Settled order: Order -> Settled ! PaymentError = order |> payments.authorize |> Done` compiles). DL-101 decode calls constructors, so a decode could call an EFFECT (D6B-91).
- **[Verified]** `ProbeSupport.span/5` (experiment 0002) reads `order["order_id"]` from its third argument. **[Inference]** That raises for a String, an Int, an enum tuple and a struct (structs have no Access). Today the argument is always the head of the EFFECT flow, an EFFECT input record.
- **[Verified]** The one-clause rule (`a function with a pipe body has one clause in slice 1`) holds only for a whole-body pipe with a direct EFFECT step (step 4 E10, R1). It exists for `flow()`, the one pipe that the REPLAY RUN replays.
- **[Verified]** The service-name check fires when the source has an EFFECT (`spans = !program.effects.is_empty()` in `compile`, step 3 G14).
- **[Observed]** A scan of every `.beaml` file outside `results/` finds no pipe that reaches an EFFECT only through another fn. The GEN arm query (`arms/gen/overlay/.../query.py`) expects the span `orders.prepare` and the log `payment_request_prepared` inside it.

## Change

1. **Reach map** (D6B-84, D6B-85). After the checks, the Checker computes `reach: signature key -> set of EFFECT names`. Edges: whole-body pipe steps (fn, constructor, EFFECT), nested pipe steps, call forms `f(x)` and constructor calls `T(x)`. Variants are no edges. A fixpoint loop handles recursion.
2. **Span rule** (D6B-86, Q6B-17). A whole-body pipe gets spans when one of its steps is an EFFECT or reaches one. Which steps of that pipe get a span is Q6B-17. Default for RED: option P, every step of such a pipe, as today.
3. **Pure fns stay silent.** A pipe whose steps reach no EFFECT keeps plain calls (D6B-28 for pure pipes stays). A pure module has no `ProbeSupport` call.
4. **One-clause rule** (D6B-87). Unchanged: only for a pipe with a direct EFFECT step. A pipe that reaches an EFFECT indirectly may stand in a several-clause fn and gets spans per clause.
5. **Span input** (D6B-88). `p0` when the pipe head TYPE is a plain record; else `nil`.
6. **`ProbeSupport` in every module on the path** (D6B-92). One source is one module today, so this is the one module. The service-name check stays as it is.
7. **REPLAY RUN** (D6B-93). Unchanged. It replays the EFFECT flow only.

## First failing test: `tests/slice6_effect_reach_test.py`

Harness: build asserts on the generated text; runtime with the release-free stubs of step 7 (`slice6_decode_test.STUBS`) and a `ProbeSupport.span/5` stub that reads `order["order_id"]` like the real one, then appends the span name to a file in the RUN DIRECTORY. Fixture `slice6/effect-reach/orders.beaml`: the GEN orders source plus `tag`, `checkout`, `ping`/`pong`, the pure cycle `a`/`b`, `to_order` and `by_id` below.

- **E1 (first RED).** `fn checkout order: Order -> Payment ! PaymentError = order |> prepare |> place |> tag`. The `checkout` clause holds `{:ok, p2} <- ProbeSupport.span(<<"orders.place">>, :internal, p0, <<"place">>, fn -> __MODULE__.place(p1) end)` (exact text, binaries as the compiler writes them). Today (observed in the probe): `{:ok, p2} <- __MODULE__.place(p1)`, no span.
- **E2 (waits for Q6B-17).** The spans of the pure steps `prepare` and `tag` in `checkout`: present under option P, absent under option S. Before the answer, E2 is an open case, not a pass.
- **E3 (pure stays silent).** A pure fn with a pipe (`fn label p: Payment -> String = p |> status_of`) has no `ProbeSupport` in its clause. `slice6/pipe/pipe.beaml` (a pure module) has zero `ProbeSupport` lines (guard, step 5 S14). `test_pure_pipe_beside_an_effect_has_no_span` (step 3) stays green.
- **E4 (recursion reaches).** `pong` has two clauses: one pipes into `ping`, one into `place`; `ping` pipes into `pong`. Both get the span of their reaching step. The fixture puts `ping` before `pong` in the source, so a memo that caches "in progress" as "no reach" gives a false result for `ping`.
- **E5 (pure recursion stays silent).** `fn a o: Order -> Order = o |> b`, `fn b o: Order -> Order = o |> a`: no span. This catches a bias "in progress counts as reach".
- **E6 (span input, D6B-88).** `fn by_id id: String -> Payment ! PaymentError = id |> to_order |> place`: the spans get `nil` as input, not `p0`. Runtime `by_id("order-1")` with the Access-faithful stub gives `{:ok, payment}`. Today (inference): no span; with the span and `p0` it raises in the stub.
- **E7 (one-clause rule).** `test_effect_pipe_keeps_one_clause` (step 4) keeps its exact text. `pong` (two clauses, indirect) compiles.
- **E8 (byte guard).** Under option P every existing source gives byte-equal output against the pre-step compiler (`git archive` build of the base commit): every `slice2` to `slice6`, `arms`, `bad`, `drift`, `examples` source that compiles, and `payments.beaml` against its snapshot. The step 5 hash guards (S12) stay. Only the new fixture differs.
- **E9 (unit test).** `effect_reach_is_transitive` in `main.rs`: the reach map of the fixture: `place` and `checkout` and `ping` and `pong` and `by_id` map to `{payments.authorize}`; `prepare`, `tag`, `a`, `b`, `to_order`, `label` map to the empty set.
- **E10 (events).** No source text and no path in `.beaml/actions.jsonl` (the existing harness check).

## Byte changes

- **Option P (default for RED).** No existing fixture changes bytes (scan above). The GEN arm, the slice 2 to 5 replay tests and the GEN `query.py` keep their span expectations. DL-110 is not touched.
- **Option S.** Every source with an EFFECT flow that has a pure step changes: the pure step loses its span, and `<output>_request_prepared` leaves the span of `prepare`. That is `arms/gen/orders.beaml`, `slice2/reuse/orders.beaml` and about 50 EFFECT sources under `slice2` to `slice6`, `bad`, `drift`, `examples`. The step 5 S12 hashes change. The GEN `query.py` rows `orders.prepare` and `('payment_request_prepared', 'orders.prepare')` change, so the `run.py` GEN release check changes. **[Inference]** The LIB arm keeps `orders.prepare`; after 6a (DL-110 B) the LIB comparison is retained evidence only, so no LIB line must change.

## Order

- **[Proposal]** After 6a and after step 11; before 6b.
  - **After 6a.** Under option P the order against 6a does not matter for the arm. Under option S step 12 changes span bytes of the GEN arm; DL-110 ends the GEN against LIB comparison with 6a, so after 6a no LIB copy line must be rewritten. Running after 6a keeps both options open at no cost.
  - **After step 11.** D6B-88 treats a struct head as a non-plain record. With step 11 first, E6 can add a struct head case.
  - **Before 6b.** 6b redacts the span input (D6B-32). With step 12 first, 6b covers every spanned pipe in one place, indirect pipes included. Hand-off to 6b: add one indirect span case to R2.
  - 6c is independent of step 12.
- **Follow-up 12b (D6B-91).** A constructor that reaches an EFFECT becomes a compile error, in its own mini-step after step 12 GREEN (one concern each).

## Checks

- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` (0001).
- The six compile-level test files, every `slice6_*_test.py`, the new test file.
- `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase. Under option P its result must equal the 6a TEST result.

## Exclusions

- A declared reach form in the signature (DL-108: after modules, roadmap part 4).
- Higher-order functions (DL-108: the graph then needs an approximation).
- Spans for call forms and nested pipes (D6B-85): they cannot reach an EFFECT today.
- The REPLAY RUN of an indirect caller (D6B-93).
- Reach output in `beaml check --json` (D6B-94, note only).
- The other DL-108 users: replay capture, test stubs, the PII flow check, dead-EFFECT detection, IDE hover.
- `integrations/zed-beaml/`.

## Limits

- **[Inference]** The span `outcome` attribute is `ok` when a step returns `{:error, _}` (ProbeSupport, slice 1). An indirect failing step shows `ok`. Not changed here.
- **[Unknown]** The real `ProbeSupport` and the OTel exporter are not run in this step's harness. `run.py` covers the release path only for the GEN orders source, which has no indirect pipe.
- **[Inference]** With modules, "every module on such a path" needs the reach map across modules. Today one source is one module.
