# Plan review: fates-a1b

**[Proposal]** PLAN CHECK, 2026-11-08, target [plan.md](plan.md) at `bf14e5dd`. By: Opus (PLAN CHECK fates-a1b).
Normal fresh review, not a Devil's Advocate. No commit, no production change.
Basis: DL-166, DL-172, DL-150, DL-158 ([decision log](../../../../../wiki/planning/decision-log.md)); fates ledger
([green-output.md](../fates/green-output.md), [test-a1.md](../fates/test-a1.md)); `experiments/0001-syntax-to-beam/src/main.rs`.
Main agent rulings applied: PB-08 accepted; QB-1 / QB-2 stay open for the OWNER, the plan builds defaults.

## Verdict

**GO with repairs.** One high objection (O1) must be repaired in the plan before RED. O2 is a cheap repair to take in RED.

## What holds (checked against HEAD)

- **[Verified]** DL-166: `renamed_onto` (main.rs 2142, 2156, 2169) is the only rename gate; `versioned_decode` (4774)
  emits the rename `Map.put/Map.delete` before the literal map, and old TYPE VERSION fields of enum / constructor TYPE
  go `:raw`. Deleting the check is enough for the live decode.
- **[Verified]** The `--stored` gap is real: `value_checks` (6094) reads `literal_fields(ty)` / `ctor_fields(ty)` (newest
  names) on the raw stored body; `kept` reads `unknown_fields`, which holds the capture-time (old) name. `stored_key`
  for both `body.get` and `kept` is the right fix. The String branch already uses the stored-version field list.
- **[Verified]** Fate lookup stays on the newest name: `literal_fate` (1740) compares `Map(Some(f))` with the field
  name, and `Checker::fates` checks `f` against `self.record(name)` (newest fields). So a fate line in a rename step
  names the new field, and the newest-name verdict key is consistent.
- **[Verified]** RED reasons at HEAD: N12 stored subTests fail on the QM4-1 A text; S1g fails (HEAD `ctor_fate` lifts
  any quarantine, so `NO_CURRENCY` is lifted under `quarantine value`); S1h fails on PF-11 "has two"; S1i fails
  (HEAD lifts `{value: "0", currency: ""}` under `quarantine currency`; `amount_v2` has `"0", _` before `_, ""`, so
  after GREEN the first matching clause tests `value`). The RED probe (only `renamed_onto` removed) is a sound
  false-pass guard for the stored mapping.
- **[Verified]** 0005: the last retained run (`results/20261108T112920757345Z/stored-order_v2`) has an empty
  `responses.jsonl` after `n7_seed`, only v1 `orders.save` / `notes.save` rows. So R3 (db.list items at newest
  version) does not hit the planned `gen-rename_channel` step. **[Inference]** It would hit if a later phase writes
  `orders.list` RESPONSE RECORDS before that step; keep the step right after `n7_seed`.
- **[Verified]** No byte-pin site sees a rename fixture or a quarantine lift; the six digest/hash sites do not move.

## Objections

### O1 (high): the QB-2 default lifts a rule that tests no field; it breaks DL-172 A

- **Evidence.** Plan §9 QB-2 builds "a failing catch-all clause is lifted by the first parameter (PF-21 fallback)".
  `failing_param` (6394) falls back to position 0 when the matching clause has no literal pattern. Real fixture:
  `slice6/stored-elixir/nested.beaml` line 31 `fn Amount value, c -> Amount ! NoCurrency = c |> Code |> unwrap |> Amount`.
  The failure comes from `c` (currency), the clause has no literal, so the plan default lets `quarantine value` lift it.
- **Consequence.** DL-172 A says the line lifts "only failed clauses that test the named field"; a catch-all tests no
  field. The source text then lies about what it parks, which is the reason DL-172 rejected option C. In a1b the
  outcome is only a different exit-1 text (a1 stop line), but a2 (DL-157 run-time skip) inherits the rule and would
  silently skip rows. Not lifting is the safer default: the row blocks the build (DL-150), loud.
- **Repair.** Build QB-2 default "not lifted": lift only when the matching clause has a literal pattern at the
  quarantined parameter. For a failed clause without a literal pattern, the help must not suggest
  `quarantine <first parameter>` (else help and lift disagree again, test-a1 objection 1). Use a help without a fate
  suggestion, e.g. `no fate line covers a failed rule that tests no parameter with a literal (QB-2 open); restore the
  rule of fn <T> that reads these records`. Add RED `test_S1j_a_rule_without_a_literal_is_not_lifted` (inline
  catch-all failing clause under `quarantine value`: exit 1, ctor block with the new help, no `fate:` line).
- **Pin impact of the repair.** Text pins (not the six byte-pin sites) move once in GREEN, by intent:
  `record_v3_test.py` V18b lines 173 to 175 (`stored-elixir/order`, `nested-fail`, `pipe-fail`),
  `slice6_stored_elixir_test.py` line 41, and any other `help_quarantine` use whose clause has no literal. Plan §5
  must list them; `decode-ctor/stored-fail` (line 171, clause `_, ""`) stays.
- If the main agent keeps the plan default instead, the plan must argue it in §9 and state the nested.beaml case.

### O2 (medium): `stored_key` order is unspecified and no RED case can catch a wrong order

- **Evidence.** Plan §1 A: "walks the steps from the newest back to `version` and undoes each rename". All RED stored
  cases use one step with one rename. A forward walk, a last-step-only walk, or a walk that ignores the order inside
  a step passes every planned test. Rotations exist in the repo (`slice2/rotation`: `a -> c`, `b -> a`, `c -> b`).
- **Consequence.** A v1 row under a chain reads the wrong key: a false block, or a false "fine" on another field's
  value.
- **Repair.** Specify: take steps with `step.from >= version`, newest first; inside a step undo the changes in
  reverse order; each `Rename(old, new)` with `new == name` sets `name = old`. Add two subTests to
  `test_N12_rename_onto_stored`: (a) chain `v1 -> v2 { rename via -> ch }`, `v2 -> v3 { rename ch -> channel }`,
  a v1 row `via: "web"` builds and a v2 row `ch: "tv"` blocks with the lost-literal error for `channel`;
  (b) rename plus `map channel "tv" -> Web` in one step, a v1 row `via: "tv"` gives the `fate: … mapped` line and
  the a1 stop line, not the lost-literal block.

## Notes (not objections)

- AC 2: the enum fixture `row_rename_enum.beaml` has no `amount` field; the v1 row `{order_id, via, amount}` puts
  `amount` into the unread list. Write the expected decode result from the fixture, or drop `amount`.
- S1h builds its source by text replace of `amount_v2`; add a setup assert that the replace changed the text.
- QB-1 default (either tested parameter lifts) is acceptable: every lifted clause does test the named field, so
  DL-172 A holds; requiring all tested parameters is stricter but not safer for a single failing row.
- R1 (a2 needs a clause tag) is correctly recorded; keep it in the a2 plan input.

## Decisions

**Undo**
→ Verdict GO with repairs; no block on O2. By: Opus (PLAN CHECK fates-a1b)
→ R3 accepted as exclusion; 0005 snapshot has no list records at the step. By: Opus (PLAN CHECK fates-a1b)

**Repair**
→ QB-2 default "not lifted" statt "first parameter lifts", weil DL-172 A and nested.beaml. Commits us to: new help text, text pins move in GREEN. By: Opus (PLAN CHECK fates-a1b)
→ Explicit `stored_key` order plus chain and rename+map subTests statt single-step cases only, weil a wrong walk passes all planned tests. By: Opus (PLAN CHECK fates-a1b)
→ QB-1 default (either tested parameter) accepted statt "all tested parameters", weil the lifted clause always tests the named field. By: Opus (PLAN CHECK fates-a1b)

**Migrate**
→ QB-1, QB-2 stay open for the OWNER (card QUAR-FIELD); the built defaults are interim.
