# Plan check: slice 6e, several EFFECTS and module name (EXPERIMENT 0005 P3, P5)

**[Observed]** 2026-11-07, plan check per `skills/implement-step/SKILL.md`. Fresh context, normal check (not a Devil's Advocate). Read only. Checked together with the [db-transport plan check](../db-transport/plan-review.md), because both plans must fit each other and [the 0005 plan](../../../../0005-prototype-fullstack/workflow/2026-11-07/plan.md).
Target: [plan.md](plan.md), [decisions.md](decisions.md). Also read: the 0005 plan (incl. "Plan repair"), its decisions and [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md); the [record format v3 plan](../record-format-v3/plan.md) with its [plan-review](../record-format-v3/plan-review.md) and the uncommitted "Plan repair" section; DL-127 to DL-144 and D026 (M3, M4, M5, M8, M9).
By: Opus (plan check P3/P4) for every finding and decision in this file.

## Verdict: BLOCK

Two high objections (O1, O2), one medium (O3). Both blocking fixes are plan-text changes; no design restart.

## Checked and holding

- **[Verified] Q6E-4 default A does not make 0005 impossible.** Every 0005 flow calls one EFFECT: `place` = `f |> to_order |> orders.save`, `list_orders` = `q |> orders.list`. The ENTRY LINES (`ui.place`, `ui.orders`) are entries, not EFFECTS in a pipe. No 0005 source holds `payments.authorize`: `grep payments.authorize experiments/0005-prototype-fullstack/` gives no hit. `payments.authorize` and `stock.reserve` stand only in this step's fixture, in two separate flows. So B is not needed for 0005. If the OWNER later wants "authorize, then save" in one flow, the smallest B is: `select(records, trace_id, operation)` in `REPLAY_HELPERS`, the live call passes its operation, each EFFECT at most once per pipe. It moves the four pins (decisions.md Q6E-4 B).
- **[Verified] Q6E-1 C fits the 0005 host calls of `orders.beaml`.** `src/orders.beaml` has ENTRY LINES, so C gives `defmodule Orders`, and the host can call `Orders.ui_place` and `Orders.ui_orders` (DL-131). `BeamlDb` is a host module; the module rule does not touch it.
- **[Inference] Q6E-2 A against DL-133.** DL-133 is a shape decision: its options A, B, C differ in shape (own struct, failure TYPE, tuple). The text `%BeamlSpike.Rejected{}` followed from the one fixed module name. `<Module>.Rejected` keeps the shape. Q6E-2 is flagged big. See O3 for the text.
- **[Verified] Order and re-pin cost.** Under the defaults only P2 moves the pin sites. P3/P5 (C) move no pin site; P4a and P4b move none (db N13). No double re-pin. A second full re-pin comes only with Q6E-1 A or Q6E-4 B. If the OWNER picks one of them, do it as one re-pin sub-step, not one per choice. No smaller order exists: P3 builds on the P2 `record/3`.
- **[Verified] No parked D026 item is decided.** No `redact` (M3), no help-line text (M4), no `retire` (M5), no failure struct as an input (M8), no new block line (M9).
- **[Verified] Big flags.** Q6E-1, Q6E-2, Q6E-4 are big in owner-review.md. Q6E-3 (`Replay.run/4`) is not host-called in 0005; not big is correct.

## Objections

### O1 · high · Variant stems rename the module: 0005 N7, N7b break and N10 passes for the wrong reason

- **Evidence.** Q6E-1 C: the module is the stem for every source with an ENTRY LINE (plan.md Change 2). The 0005 variants are full sources with ENTRY LINES: `src/variants/order_v2.beaml`, `stricter.beaml`, `no_place.beaml` (0005 plan). Their stems give `OrderV2`, `Stricter`, `NoPlace`, not `Orders`.
- **Consequence.** N7 and N7b (generate from `order_v2.beaml`, then `/orders` lists the rows): the host calls `Orders.ui_orders`, which is gone. The host build fails, and the test fails for a reason that is not the MIGRATE CHAIN.
- N10 (generate from `no_place.beaml`, `mix compile` fails and names `Orders.ui_place/1`) **passes falsely.** The module `Orders` is missing, so the host build names `Orders.ui_place/1` also when the `ui.place` line is still in the source. The DL-131 claim is then not tested.
- Plan line 110 (a fixture copy under another stem gets that module) shows that the rule is known. No plan applies it to the 0005 variants.
- **Resolving change.** Each variant keeps the stem `orders`: `src/variants/order_v2/orders.beaml`, `src/variants/stricter/orders.beaml`, `src/variants/no_place/orders.beaml`. Record this in the 0005 plan as a repair line.
- N10 gets a control: the generated file holds `defmodule Orders do`, and the host error names `Orders.ui_place/1` and not `Orders.ui_orders/1`.
- This plan gets one N14 case: a copy of `slice6/entry/orders.beaml` in another directory under the stem `orders` gives `defmodule Orders do`.

### O2 · high · N13 compares against 35c7e3bf, but P2 lands first and changes every EFFECT source

- **Evidence.** N13: "every tracked source without an ENTRY LINE compiles byte-equal against the HEAD compiler 35c7e3bf". The 0005 order is P1 → P2 → P3/P5. P2 changes `Replay.record/3` in every EFFECT source (record-v3 plan, Pin sites). The plan Order section says only "the RED worker re-reads the record keys" if P2 lands first. It does not move the N13 base.
- **Consequence.** After P2, N13 fails by construction for every EFFECT source. A worker then excludes EFFECT sources, and the guard stops guarding the EFFECT bytes that D6B-198 and D6B-199 can move. This is the same fault as record-v3 O1. The byte-pin memory note records two earlier misses of this kind.
- **Resolving change.** N13 base = the P3 base commit (the P2 commit that set the pins, RV3-14). The RED worker records its hash. "The four pin-site tests pass with no edit" then means the P2 values. The fifth site (6d N13 `BASE`) stays at the P2 GREEN hash; this step does not move it.

### O3 · medium · DL-133 and Q5-6 texts still name `BeamlSpike.Rejected`

- **Evidence.** DL-133 option A text: `{:error, %BeamlSpike.Rejected{...}}`. The 0005 host matches `%Orders.Rejected{}`.
- **Consequence.** A later reader takes the 0005 host match as against an OWNER decision, or a worker emits a fixed `BeamlSpike.Rejected` to "follow DL-133".
- **Resolving change.** The docs phase adds an effect note to DL-133: "name follows the module (Q6E-2 A, default, open); shape unchanged". No code change.

## Decisions

**Repair**
→ O1 high statt medium, weil N10 gives a false pass. → By: Opus (plan check P3/P4)
→ O1 fix by directory per variant statt a `module` line, weil no syntax change. → By: Opus (plan check P3/P4)
→ O2 high statt medium, weil the fault is sure and repeats. → By: Opus (plan check P3/P4)
→ Q6E-4 A accepted statt B, weil every 0005 flow has one EFFECT. → By: Opus (plan check P3/P4)
→ Q6E-2 A accepted statt objection, weil DL-133 decides shape. → By: Opus (plan check P3/P4)

**Undo**
→ O3 medium, not blocking. → By: Opus (plan check P3/P4)
→ `BeamlDb` not in the reserved list: dropped as low. → By: Opus (plan check P3/P4)
