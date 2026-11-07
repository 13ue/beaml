# RED plan: slice 6e, several EFFECTS and ENTRY LINES per source, module named from the source

**[Proposal]** Solve/RED phase, 2026-11-07. Maps the repaired [plan](plan.md) (N1 to N15, "Plan repair") onto `tests/slice6_multi_test.py`. Results: [red-output.md](red-output.md). Notes and the N13 base: [notes.md](notes.md).
By: Opus (RED multi-effect) for every line in this file.

## Fixtures (new files only)

| Path under `slice6/multi/` | Role |
|---|---|
| `orders.beaml` | The plan fixture: 6d TYPES plus `Hold`, `StockError`; EFFECTS `payments.authorize`, `stock.reserve`; ENTRY LINES `ui.place`, `ui.hold`; flows `place`, `hold` |
| `no_hold/orders.beaml` | N8, N9: without `stock.reserve`, `ui.hold`, `hold` (D6B-210) |
| `no_hold_retired/orders.beaml` | N8, N9: `no_hold` plus `retire stock.reserve keep 30 days`, `retire ui.hold keep 30 days` |
| `copy/orders.beaml` | N14: byte copy of `slice6/entry/orders.beaml` |
| `bad/two_effects_in_one_pipe.beaml` | N10, Q6E-4 A |
| `bad/same_entry_operation.beaml` | N10, D6B-201 |
| `bad/enum.beaml` | N10, D6B-203 (stem `enum`) |

RECORD SNAPSHOTS are written by the test from the N4 live records into a temp directory (plan "Fixture").

## N → test

| Plan | Test (subtests) | What it asserts |
|---|---|---|
| N1 | `test_n1_two_effects_and_two_entry_lines_build` | exit 0, no stderr; one each of `defmodule Orders do`, `Replay`, `Http`, `BeamlFailure`, `Rejected`, `def ui_place(`, `def ui_hold(`, `def payments_authorize(`, `def stock_reserve(`; no `BeamlSpike` |
| N2 | `test_n2_output_compiles_without_warnings` | `elixirc --warnings-as-errors` exit 0 **and** no `warning` text (Elixir 1.18.1 exits 0 on warnings) |
| N3 | `test_n3_to_n6_runtime` `N3_*` | both live values; both span logs (plan text); request counts `{1, 0}`, `{0, 1}` |
| N4 | `N4_operations`, `N4_traces` | two ENTRY, two RESPONSE RECORDS by operation; each RESPONSE RECORD in its ENTRY trace; traces differ |
| N5 | `N5_*` (7 cases) | `Orders.Replay.entry/2` per ENTRY RECORD; `Orders.Replay.run(op, a0, trace, records)`; wrong flow on a trace and unknown operation → `:operation_mismatch`; `ui.other` → `:operation_mismatch`; changed value → `:body_digest_mismatch` |
| N6 | `N6_hold_reject`, `Q6E2_rejected_shape` | `{:error, %Orders.Rejected{reason: "constructor"}}`, no request, one ENTRY RECORD `ui.hold`/`rejected`/`constructor`, no RESPONSE RECORD; struct keys |
| N7 | `test_n7_stored_snapshot_with_two_operations_builds` | `--stored` over the N4 snapshot: exit 0, `2 entries, 2 checked, 0 rejected at capture` |
| N8 | `test_n8_orphan_block_per_operation` (4) | `no_hold`: the `stock.reserve` RESPONSE block (count 1), no `payments.authorize` block; two blocks with counts 1 and 2; `retire stock.reserve` only: the `ui.hold` ENTRY block (count 1); both RETIRE LINES: exit 0, no error, no DEAD LINE |
| N9 | `test_n9_dead_line_per_operation` (3) | two W1 lines, one per RETIRE LINE; W2 `migrate Payment v1 -> v2` without a Payment record; no W2 with one old `payments.authorize` record beside the hold records |
| N10 | `test_n10_rejects` (3) | exact texts; `bad/` equals the table |
| N11 | `test_n11_fmt_keeps_the_fixture`, `test_n11b_fmt_aligns_a_single_spaced_effect_line` | fixture is a fmt fixed point; single-spaced `stock.reserve` line gets the fixture bytes |
| N12 | inside `compile()` | every compile: no source path, no source text, no stored value in `.beaml/actions.jsonl` |
| N13 | `test_n13_sources_without_an_entry_keep_their_bytes` | guard: every tracked non-ENTRY-LINE source byte-equal against `BASE` (G6D-01 filter) |
| N14 | `test_n14_entry_line_sources_take_the_stem` (4), `test_n14b_…_stays_beamlspike`, `test_n14c_…_stem_error` | `Orders`, `Echo`, `Count`, copy → `Orders`; guard: `slice2/reuse/orders.beaml` stays `BeamlSpike`; guard: stem `order-flow` keeps the existing stem text |
| N15 | `test_n15_module_name_from_stem` (2) | black box: `order_flow` → `OrderFlow`, `v2_orders` → `V2Orders` |

Not in this file (TEST phase): the four pin-site tests with no edit; `cli.rs` `orders_cli_emits_flow_effect_decode_and_replay` with no edit; the cargo unit test `module_name_from_stem` (GREEN adds it to `main.rs`).

## Decisions

**Repair**
→ N9 W2 on Payment statt Hold, weil D6B-39 bans a MIGRATE CHAIN on Hold (constructor field `amount`; observed at HEAD). Commits us to: the "minimum over operations" case uses the `payments.authorize` side. → By: Opus (RED multi-effect) · Repair
→ N5 `a0` = the decoded PlaceOrder statt Order, weil the HEAD `run/3` a0 is the flow parameter and calls `to_order` itself (observed in generated code). Commits us to: Q6E-3 A keeps a0 = flow parameter. → By: Opus (RED multi-effect, default, open) · Repair

**Undo**
→ ENTRY LINE in `bad/two_effects_in_one_pipe.beaml`, so both N13 filters skip it (its text changes by design). → By: Opus (RED multi-effect) · Undo
→ N15 black box statt cargo unit test, weil `main.rs` is off limits here. → By: Opus (RED multi-effect) · Undo
→ Trace-id stub = hex of the root span name, so two flows have two traces. → By: Opus (RED multi-effect) · Undo
→ fmt columns from a scratch probe (HEAD minus the two limit checks); equal to a hand calculation from `aligned`. → By: Opus (RED multi-effect) · Undo
→ N2 also checks the warning text. → By: Opus (RED multi-effect) · Undo
→ N10 reserved name: one case (`enum`). → By: Opus (RED multi-effect) · Undo
→ N12 inside `compile()`, no own test. → By: Opus (RED multi-effect) · Undo
