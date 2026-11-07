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

# RED review: DB TRANSPORTS, part P4b (`--stored` over ROW SNAPSHOTS)

**Verdict: PASS.** No critical or high objection. Two medium notes below.
2026-11-08. By: Opus (RED review db-stored), fresh context, one round. Inputs: [plan.md](plan.md) with both repairs, [decisions.md](decisions.md), [red-plan.md](red-plan.md#p4b---stored-over-the-row-snapshot), [red-output.md](red-output.md#p4b-run), `tests/slice6_db_stored_test.py`, `slice6/db/stored/`, `stricter/`, `put_only/`, the 0005 [owner review](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) "P4b RED defaults".

## Run (observed)

```
git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>     # HEAD 158ba4e1
cargo build --offline --quiet --manifest-path <scratch>/experiments/0001-syntax-to-beam/Cargo.toml --target-dir <scratch>/target
BEAML_SPIKE=<scratch>/target/debug/beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_db_stored_test.py
```

- **[Observed]** `Ran 40 tests`, `FAILED (failures=43, skipped=3)`. `N24_sample_meta_form` passes (guard). Skips: N28b, N30, N30b with their reasons.
- **[Observed]** Every failure is `unsupported token at byte 301 / 562 / 603 / 609 / 660` (the `[` of a LIST TYPE) or `unsupported effect kind: db.put` (`put_only/`). No P2 or P3 text. Same split as red-output.md.

## Checks

| Question | Finding |
|---|---|
| (1) Counts | **[Observed]** 40 tests, 43 red, 3 skipped, 1 guard green. |
| (2) `snapshot-meta.json` | **[Observed]** N24 pins `row_count` 3 beside 2 rows (block) and 2 beside 2 (build); no meta builds in every other case. The sample guard pins the P5-19 keys, `table`, sorted `row_ids` equal to the rows, `row_count` = lines, digests. **[Verified]** PDB-22: the compiler reads `row_count` only, so no compiler test can fail on another database or a stale snapshot of equal count; that tie is 0005 N8c (ids and count against `psql`), host side. Limit, not a RED gap. `row_count` below the lines is untested: note M2. |
| (3) Read order | **[Observed]** One test per edge: name before version (`Invoice` v7 counted), digest before version (bad digest + off-chain counted), version before DL-101 (off-chain `0` row under `stricter/`: path text, no constructor text), chain before DL-101 (`N20_chain_rows_build`: the v1 row lacks `note`). Each fails only for a reader that swaps that pair. **[Inference]** Digest before DL-101 holds by transitivity for a sequential reader; name versus digest is not observable (both counted). Low, dropped. |
| (4) QV3-8 B for rows | **[Observed]** A skip-all reader fails: N17, N20b and N24 pin `K checked` exactly; N18, N19, N20 need a checked row to block. A reader that checks rejected rows fails N21b (off-chain rejected counted) and the `stricter/` rejected row (builds, `0 checked, 1`). |
| (5) Three `(default, open)` items | **[Observed]** All three stand in the owner review lines 103 to 105. Orphan rule: both halves pinned (N21 `Invoice` of `orders.save` counted; N28 control `Order` of `orders.import` checked; N28 blocks). Rows line versus QV3-7 A: note M1. |
| (6) Skips | **[Verified]** Honest. M5 (RETIRE LINE for rows) is parked by D036, plan "Parked items"; a RED would invent the syntax. DL-140 needs the stored variant, which a ROW CORE does not hold (plan Inference line 241); a swap is not observable, so no red test can be written today. |
| (7) DL-124 | **[Observed]** No expected text or constant holds a stored value: texts name TYPE, field, operation, constructor error and paths only. N26 scans every value String of 5 characters or more, every row id, trace id and span id the test wrote; each subtest needs its anchor in stderr. `compile()` scans the action log with the same list and the `--stored` path; N27 asserts the log exists. No test value appears in red-plan.md, red-output.md or the owner review P4b lines. |

## Notes (medium, no block)

**M1. Count-line policy is one OWNER question, not two rules.** Three count lines now differ: the ENTRY line always prints, the RESPONSE pair prints when M > 0 (QV3-7 A), the rows line always prints (owner review line 105, A). QV3-7 A rests only on "no existing stderr assertion moves"; its own challenge says a clean file shows no proof that the check ran. That challenge is the reason for rows A: under B for rows, N17, N20b (`3 checked`) and N24 lose their proof, and a reader that drops the `Note` rows passes. No P4b test depends on the QV3-7 choice (the N25 control has M = 1).
→ Resolving step: merge owner review line 105 with the QV3-7 "big" line into one question: "Does each `--stored` count line print on every success (QV3-7 B, rows A) or only when M > 0 (QV3-7 A, rows B)?", with the N20b consequence stated. Text-only; no test change.

**M2. N24 tests one direction only.** PDB-22 says "differs"; N24 has `row_count` 3 beside 2 lines. A GREEN that checks `row_count > lines` passes and misses extra rows (a rows.jsonl with appended or duplicated lines).
→ Resolving test: `N24_row_count_below_lines_blocks`: 2 rows, `row_count` 1, exit 1 with `error: rows.jsonl holds 2 rows but snapshot-meta.json counts 1; the ROW SNAPSHOT is partial`. Add in the P4b TEST phase or a RED top-up.

## Dropped (low)

- Digest before DL-101 not pinned directly (transitive, see check 3).
- `row_ids` not compared with the rows' `row_id` (PDB-22 reads the count only; PDB-21 writes one new directory per build).
- N22 uses a source with both `db.get` and `db.list`; a `db.get`-only or `db.list`-only source is untested.
- N23 has no case for `source` with another value than `"db"`.
- `N24_sample_builds` does not add the sample values to the N26/N27 word list.

## Decisions

**Undo**
→ Verdict PASS; M1 and M2 noted, not blocking. → By: Opus (RED review db-stored) · Undo
→ Ran HEAD 158ba4e1, not b0a27004 (the RED run); same test file. → By: Opus (RED review db-stored) · Undo
→ Database and staleness left to 0005 N8c (PDB-22 limit). → By: Opus (RED review db-stored) · Undo
→ Three skips accepted as honest blocks. → By: Opus (RED review db-stored) · Undo
→ Five low gaps dropped. → By: Opus (RED review db-stored) · Undo

**Repair**
→ M1 as one merged owner question statt two separate default lines, weil one rule (proof that the check ran) decides both lines. → By: Opus (RED review db-stored) · Repair
→ M2 test in TEST or a top-up statt a BLOCK, weil `!=` is the natural build and the false pass needs a `>` check. → By: Opus (RED review db-stored) · Repair
