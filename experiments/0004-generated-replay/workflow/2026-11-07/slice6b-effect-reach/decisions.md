# Decisions: slice 6b step 12 (spans follow the EFFECT reach)

**[Proposal]** PLAN phase, 2026-11-07. Design decisions that DL-108 and the decision log do not settle.
Classes follow Decision4. Undo and Repair entries give the default that the step worker takes. Migrate and Answer entries are OWNER questions.
Every entry carries a `By:` line (DL-107). The worker records each taken default again in its `notes.md` (DL-097). A Repair that changes language behaviour or a check also gets a decision-log entry at the end of its phase.

## OWNER question

### Q6B-17 · Migrate · Which steps of a reaching pipe get a span? (blocks E2 and the GREEN of E2 only)

- **Context.** **[Verified]** DL-108: "Pure steps stay silent; steps on a path to an EFFECT get a span". **[Verified]** Today every step of a pipe with a direct EFFECT step has a span, pure steps included: `prepare` in `order |> prepare |> payments.authorize` has the span `orders.prepare`, and the log `payment_request_prepared` is inside it. **[Verified]** The GEN arm query expects both (`arms/gen/overlay/experiments/0002-http-correlation/query.py`, lines 11 and 17). The DL-108 text can mean the pipe or the step.
- **Option P, per pipe.** A whole-body pipe in which any step is or reaches an EFFECT gets a span on every step, as a direct EFFECT pipe does today. "Pure steps" means the steps inside a pure fn. No existing byte changes.
- **Option S, per step.** Only a step that is or reaches an EFFECT gets a span. `prepare` and every step after the EFFECT lose their spans; the prepared log moves to the parent span. About 50 EFFECT sources change bytes, the step 5 hash guards and the GEN `query.py` rows change, and the `run.py` GEN release check changes.
- **Option H, hybrid.** A pipe with a direct EFFECT step keeps today's spans (P). A pipe that reaches an EFFECT only indirectly gets spans on its reaching steps only (S). No existing byte changes; the GEN `query.py` rows stay. Challenge: two span rules in one compiler. By: Opus (PLAN REPAIR, slice6b-effect-reach) (plan check, Q6B-17)
- **Challenges.** P puts spans on pure work next to an EFFECT (the trace shows `prepare` time). S gives a smaller trace but removes a span that slices 1 to 5 tested and that the 0002 probe reads.
- **Why Migrate.** The trace contract of every EFFECT flow, the arm evidence and the 0002 query.
- **Interim.** RED uses P for E1, E3 to E10; E1 holds under both options. E2 waits.
- By: open, decided later by `13ue`. Question by Opus (PLAN, slice6b-effect-reach).

### Q6B-18 · Migrate · A constructor that reaches an EFFECT (was D6B-91; blocks 12b)

- **Context.** **[Observed by the planner]** An enum constructor can be the EFFECT flow today, and it compiles. **[Verified by the plan check]** DL-092, DL-100, DL-101 and DL-108 do not restrict what a constructor calls. A reject removes syntax that compiles today.
- **Option a.** Reject every constructor that reaches an EFFECT (the old D6B-91 default).
- **Option b.** Reject only where the compiler calls the constructor itself: a decode field, the step 8 `--stored` check, the host `T.new`.
- **Option c.** Allow it, give it spans; the REPLAY RUN substitutes the inner EFFECT.
- **Why Migrate.** A source with an EFFECT in a constructor stops compiling, or changes its replay, without an OWNER choice.
- **Smallest test (12b RED, after the answer).** `fn Settled order: Order -> Settled ! PaymentError = order |> payments.authorize |> Done` gives the chosen result.
- By: open, OWNER. Raised by Opus (PLAN REPAIR, slice6b-effect-reach) on plan check O1.

## Undo and Repair defaults

Format: **ID · class · decision.** Chose / Over / Because. Commits us to (Repair only).

**D6B-84 · Repair · The reach map is a fixpoint over all call edges.**
Chose: `reach: BTreeMap<signature key, BTreeSet<EFFECT name>>`, computed after the checks. Start: each fn's direct EFFECT steps. Repeat: add the reach of every callee, until nothing changes. Over: a depth-first walk with a memo. Because: a memo that caches a node "in progress" gives a wrong result in a cycle, in one of two directions (E4, E5); the fixpoint is order-free and short. Commits us to: O(n × e) per compile; fine for test sources (`ponytail:` comment names the ceiling, Tarjan SCC if a source grows).
By: Opus (PLAN, slice6b-effect-reach)

**D6B-85 · Undo · Edges include call forms, nested pipe steps and constructor calls; only whole-body pipe steps get spans.**
The walk is one recursive function over `Node` (a sibling of `referenced_names`). Call forms and nested pipes cannot reach an EFFECT today (failing fns cannot stand there, see the plan facts), so they get no span rule now. Alternative: whole-body pipe steps only. Reason: DL-108 asks for the set for every fn, and the later users (replay capture, stubs, PII sinks) need the full graph. The unit test E9 checks the map.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-86 · Repair · A whole-body pipe has spans when a step is or reaches an EFFECT.**
Chose: `spans = steps.iter().any(|s| self.effect(s).is_some() || !self.reach[s].is_empty())` in `emit_chain`. Which steps get the span: Q6B-17 (default P). Over: the D6B-28 test on direct EFFECT steps only. Because: DL-108 C. Commits us to: a reaching pipe in a fn without a direct EFFECT step names spans with the source file stem, so the service-name check must hold for it (it does: reach implies an EFFECT in the source).
By: Opus (PLAN, slice6b-effect-reach)

**D6B-87 · Repair · The one-clause rule stays for a direct EFFECT step only.**
Chose: no change to the rule or its text. A pipe that reaches an EFFECT only through a fn may stand in a several-clause fn; each clause pipe gets its spans. Over: extend the rule to every reaching pipe. Because: the rule serves `flow()`, the one pipe that the REPLAY RUN replays; an indirect caller is not replayed. A base case of a recursive reaching fn needs two clauses (E4). Commits us to: E7 tests both sides.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-88 · Repair · The span input is `p0` only for a plain record head; else `nil`.**
Chose: the compiler knows the head TYPE; for a String, an Int, an enum or a constructor TYPE (a struct after step 11) it passes `nil`. Over: always `p0`. Because: `ProbeSupport.span/5` reads `order["order_id"]`, which raises for these values; today the head is always an EFFECT input record. Commits us to: such spans have `order_id: nil`. 6b redacts a plain record head as before.
By: Opus (PLAN, slice6b-effect-reach)
Plan repair (O3): known consequence: the GEN `query.py` selects spans by `attributes.order_id`, so a helper span with `nil` leaves the per-order trace; the inner EFFECT spans stay. E6 tests it. Alternative recorded: the nearest plain-record step input (`p0` if the head is a plain record, else the step input `pN` if its TYPE is a plain record, else `nil`); same bytes for every existing source. Class of the alternative: Repair (no existing byte changes, a later switch is a worker change). Default kept. By: Opus (PLAN REPAIR, slice6b-effect-reach)

**D6B-89 · Undo · The prepared log stays on the step directly before a direct EFFECT step.**
An indirect step gets no `<output>_request_prepared` log. Alternative: a log before every reaching step. Reason: the log names the EFFECT output; the indirect step is not the preparation of a request.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-90 · Undo · An indirect step span has the form of a pure step span today.**
`ProbeSupport.span(<<"service.step">>, :internal, INPUT, <<"step">>, fn -> CALL end)`; a failing step binds `{:ok, pN} <- ...`. Alternative: a new span kind. Reason: same code path in `emit_chain`; the trace already reads this form.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-91 · Raised to Migrate as Q6B-18 (plan repair O1). Not a default any more; kept as the record of option a.**
By: Opus (PLAN REPAIR, slice6b-effect-reach)

**D6B-91 (original) · Repair · A constructor that reaches an EFFECT is a compile error (built in follow-up 12b).**
Chose: `error: fn T: a constructor cannot reach an EFFECT (it reaches E)`, `  help: call the EFFECT in a lowercase fn, then pipe its result into fn T`. Over: allow it and give it spans. Because: the decode calls constructors (DL-101), so a live decode and a REPLAY RUN would call an EFFECT, and the step 8 `--stored` check runs constructors in Rust without EFFECTS. Observed today: an enum constructor can be the EFFECT flow. Commits us to: a new reject; a later lift is a Repair, a later ban after use would be Migrate. Decision-log entry at the end of 12b.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-92 · Undo · "ProbeSupport in every module on such a path" is the one module today.**
One source compiles to one `BeamlSpike` module. It calls `ProbeSupport` when it has an EFFECT (EFFECT spans, events, `Replay`) or a reaching pipe; a reaching pipe implies an EFFECT in the same source. A pure module has no call. Across modules: with roadmap part 4.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-93 · Undo · The REPLAY RUN does not change.**
It replays the EFFECT flow (`Step::Replay` in `emit_chain`), which has no pure-step spans. An indirect caller is not replayed. Alternative: replay through the caller. Reason: out of DL-108 scope.
By: Opus (PLAN, slice6b-effect-reach)

**D6B-94 · Undo · `beaml check --json` may expose the reach map later. Note only.**
A possible key: `reaches: {"fn": ["EFFECT", ...]}`, names only. Not built. Reason: no consumer yet (DL-096 order: `fmt` and `check --json` first, then the language server).
By: Opus (PLAN, slice6b-effect-reach)

**D6B-95 · Undo · Fixture and test file names.**
Fixture `slice6/effect-reach/orders.beaml`; test `tests/slice6_effect_reach_test.py`; ledger `slice6b-effect-reach/`; unit test `effect_reach_is_transitive`.
By: Opus (PLAN, slice6b-effect-reach)

## Points the decisions do not settle (for the worker, class Undo)

- The exact pattern syntax for the `pong` clauses (a literal field pattern or a signature line). Any form that compiles today and gives two clauses.
- Whether `reach` lives in `Checker` as a field or is computed in `emit`. The field is the default (the unit test reads it).
