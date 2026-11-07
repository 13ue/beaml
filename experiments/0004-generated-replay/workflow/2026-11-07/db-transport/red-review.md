# RED review: DB TRANSPORTS, part P4a

**Verdict: PASS.** No critical or high objection. Three medium notes below.
2026-11-07. By: Opus (RED review db-transport), fresh context, one round. Inputs: [plan.md](plan.md) with both repairs, [decisions.md](decisions.md), [plan-review.md](plan-review.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), `tests/slice6_db_test.py`, `slice6/db/`.

## Run (observed)

```
git archive b1879fa8 experiments/0001-syntax-to-beam | tar -x -C <scratch>/head
cargo build --offline --quiet --manifest-path <scratch>/head/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/head/target
BEAML_SPIKE=<scratch>/head/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_db_test.py
```

- **[Observed]** `Ran 16 tests`, `FAILED (failures=40, skipped=1)`. N13 passes against `P4_BASE` ca09d361. N2c skipped with its reason.
- **[Observed]** Failure split: N1 1, N1b 4, runtime setup 3 (orders, plain, plain_v2), N12 rejects 15, N12 order_v2 1, N12 S13 1, N15 5, N15b 1, N16 6, N25b 3. Same split as red-output.md.
- **[Observed]** Every failure text is `unsupported token at byte N` (the `[` of a LIST TYPE) or `unsupported effect kind: db.<k>`. No P2 or P3 text.
- **[Observed]** `git diff ca09d361 b1879fa8 -- experiments/0001-syntax-to-beam` is empty, so the HEAD compiler equals the `P4_BASE` compiler.

## Checks

| Question | Finding |
|---|---|
| (1) Counts | **[Observed]** 16 tests, 40 red, N13 green, N2c skipped. |
| (2) One encoder (PDB-30) | **[Observed]** `N2_one_put_with_a_json_binary` pins `is_binary(j)` on the put. `N6_list_value_not_a_binary` seeds a map row and wants `decode`. `N2_reason_is_json_null` pins `:null` (`:json.encode(nil)` gives `"nil"`, so a `nil` core fails). The fake is test code; GREEN cannot pass with maps on write or on list. **[Inference]** The load path has no map-row case; the fake `get` cannot find a map row by key, so it cannot be built here. Low, dropped. |
| (3) v3 words (QDB-6b) | **[Observed]** `accepted`/`:null` (N2, N10 save), `rejected` with `transport`, `not_found`, `decode` (N10). `constructor` is pinned only as the StoreError reason (N6), not in a record: note M1. **[Observed]** No message text holds a stored value: `LITERAL_BLOCK` names the field, not `"app"`; the StoreError carries the reason only. DL-124 over stderr is N26 (P4b). |
| (4) LIST TYPE | **[Observed]** `list_elsewhere` (`Basket.items: [Order]` outside a db.list output) and `list_element` (`[String]`) are negative cases; `list_output` rejects a db.list without a list field. N25b literal check has two controls (kept `tv` with `items.0.channel`; same `app` record under `orders.beaml`). Text form matches the built DL-122 RESPONSE RECORD text (main.rs line 4898). **[Verified]** The per-item constructor check is N25 (P4b, `stricter/`), not N25b; out of P4a scope. |
| (5) QDB-1, QDB-3, QDB-4 | **[Observed]** QDB-1: `get_key`, `get_key_field` rejects, `N7_get` control, `N7_get_call` pins the key map. QDB-4: bad row behind a newer good row fails; control `N6_control_built_core_lists`. QDB-3: the newest row comes from the fake (`Enum.find` over newest-first rows); decisions.md QDB-3 records "Pinned by the fake in N7 only". Host rule, accepted limit. |
| (6) Fourth KIND, table, no HTTP | **[Observed]** `fourth_kind` (`db.query`) with the four-KIND text; `table`; N1 `PDB-20 no Http module` (no `defmodule Http do`, no `BeamlSpike`). |
| (7) `P4_BASE` | **[Observed]** ca09d361 is the v3 GREEN; N13 skips every source with `= db.x(` or `: [`; 148 sources byte-equal. Correct for outbound-only sources after v3. Docstring says the P4 GREEN worker moves it to its start commit after P2 and P3 TEST. Wording gap: note M3. |
| (8) Owner review | **[Observed]** `order_v2` names and N25b names are `(default, open)` in red-plan.md but absent from the 0005 owner-review.md. Note M2. |

## Notes (medium, no block)

**M1. No `rejected`/`constructor` record.** Plan line "Row constructor fails → `rejected`, `constructor`, `:null`" has no N10 case. A GREEN that writes `decode`, or no record, for a constructor failure passes, as long as the StoreError says `constructor`.
→ Resolving test: `N10_constructor_record`: seed `FAULTS["constructor"]`, call `list_orders`, assert `Map.take(r, ["value", "outcome", "reason"]) == %{"value" => :null, "outcome" => "rejected", "reason" => "constructor"}`. Add in P4b RED or the P4a TEST phase.

**M2. RED defaults missing from the owner review.** Two `(default, open)` text choices: `order_v2` names `orders.save` and `Order.amount`; N25b names `TYPE Order v1` and field `channel` (not `OrderList` or `items.0.channel`). Precedent: G6D-12 (an Undo default) is listed there.
→ Resolving step: add both lines under "Database transports (P4)" of `experiments/0005-prototype-fullstack/workflow/2026-11-07/owner-review.md`.

**M3. `P4_BASE` wording.** Line 46 says "the HEAD at this RED", but ca09d361 is the v3 GREEN set by the pin commit b1879fa8. The docstring pin-site list (five sites) omits the multi-effect N13 BASE and `P4_BASE` itself. A missed move fails N13 loudly; no false pass.
→ Resolving step: P3 GREEN or P4 GREEN corrects the comment and names `P4_BASE` and the multi N13 BASE in the pin-site list.

## Dropped (low)

- N8 `BeamlDb.rows() == []` holds by the fake in every non-`:ok` mode; the `transport` reason carries the check.
- Load with a map row (see check 2).

## Decisions

**Undo**
→ Verdict PASS; M1 to M3 noted, not blocking. → By: Opus (RED review db-transport) · Undo
→ Ran HEAD b1879fa8, not ea64059c (the RED run). → By: Opus (RED review db-transport) · Undo
→ QDB-3 fake-only pin accepted (recorded limit). → By: Opus (RED review db-transport) · Undo
→ Per-item constructor check left to N25 (P4b). → By: Opus (RED review db-transport) · Undo
→ Load map-row and N8 row-count gaps dropped as low. → By: Opus (RED review db-transport) · Undo

**Repair**
→ M1 test in P4b RED or TEST statt a P4a re-RED, weil the StoreError reason is pinned and GREEN shares one reason path. → By: Opus (RED review db-transport) · Repair
→ M2 owner-review lines statt red-plan only, weil `(default, open)` lines must reach the OWNER. → By: Opus (RED review db-transport) · Repair
