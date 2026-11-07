# Spec: slice 6b step 12 (spans follow the EFFECT reach) and 12b (a pure constructor)

**[Proposal]** Solve/RED phase, 2026-11-07. Contract for GREEN. No production file changed. No commit. `run.py` not run.
Decisions: DL-108 (C), DL-119 (Q6B-17, S, OWNER), DL-120 (Q6B-18, a, OWNER) in [the decision log](../../../../../wiki/planning/decision-log.md).
Plan: [plan.md](plan.md) (E1 to E10), defaults [decisions.md](decisions.md) (D6B-84 to D6B-95). New defaults: [notes.md](notes.md) (D6B-112 to D6B-118).
By: Opus (RED, slice6b-effect-reach) for every line in this file.

## Contract, step 12

- **Reach map (D6B-84, D6B-85).** For every fn and constructor, the set of EFFECTS it reaches through call edges, transitively, cycles included. A fixpoint, not a fixed number of passes (E4c).
- **Span rule (DL-119 S).** In a whole-body pipe, a step gets a span only when it reaches an EFFECT through a fn. A pure step gets no span, also in the EFFECT flow. A direct EFFECT step keeps its call; its span stays inside the EFFECT function (`:client`).
- **Span form (D6B-90).** `ProbeSupport.span(<<"service.step">>, :internal, INPUT, <<"step">>, fn -> __MODULE__.step(pN) end)`; a failing step binds `{:ok, pM} <- ...`.
- **Span input (D6B-88).** `p0` when the pipe head TYPE is a plain record; else `nil`.
- **Pure-step form (D6B-114).** A pure step in any pipe is the plain call `pN = __MODULE__.f(pM)` (or `{:ok, pN} <- ...`).
- **Prepared event (D6B-89, D6B-114).** The step directly before a direct EFFECT step gets the next `with` clause `_ = ProbeSupport.event(<<"<output>_request_prepared">>, <<"step">>)`. The operation stays the step name. No other step gets an event.
- **One-clause rule (D6B-87).** Unchanged. The text `a function with a pipe body has one clause in slice 1: NAME` fires only for a direct EFFECT step.
- **REPLAY RUN (D6B-93).** Unchanged.
- **Pure modules.** No `ProbeSupport` call (D6B-28).
- **Events (E10).** No source text and no source path in `.beaml/actions.jsonl`.
- **E9.** GREEN adds the unit test `effect_reach_is_transitive` in `main.rs` (D6B-115).

## Contract, step 12b (DL-120)

- A constructor (record or enum TYPE constructor) that reaches an EFFECT, directly or through fns, is a compile error. Exit 1, no stdout.
- Text (D6B-112), two lines:

```text
error: fn T: a constructor cannot reach an EFFECT: T -> f -> ... -> effect.name (DL-120)
  help: call the EFFECT in a lowercase fn, then pipe its result into fn T
```

- Path (D6B-113): the shortest path from `T` to an EFFECT; ties go to the first step in source order (clause order, then step order).
- A lowercase fn may call the EFFECT and pipe its result into a pure constructor (guard).

## Expected results (fixture `slice6/effect-reach/orders.beaml`)

| Clause | Spans (exact, in order) |
|---|---|
| `place` | none (event clause after `prepare`) |
| `checkout` | `orders.place` |
| `ping` | `orders.pong` |
| `pong` 1, 2 | `orders.ping`; `orders.place` |
| `by_id` | `orders.place` (input `nil`) |
| `c1`, `c2`, `c3` | `orders.c2`, `orders.c3`, `orders.place` |
| `label`, `a`, `b`, pure fns | none |

- Runtime (Access-faithful span stub, local TCP payments stub): spans nest by call. `by_id("order-1")`: outer `orders.place` has `order_id: nil`, the EFFECT span keeps `"order-1"`.
- E8: [byte-guard.json](../../../slice6/effect-reach/byte-guard.json), 71 sources, 40 change (D6B-117).

## Exclusions

- Spans for call forms and nested pipes (D6B-85). The REPLAY RUN of an indirect caller. `check --json` reach output.
- The GEN arm query and `arms_test.py` edits: [notes.md](notes.md), "Deferred edits".
