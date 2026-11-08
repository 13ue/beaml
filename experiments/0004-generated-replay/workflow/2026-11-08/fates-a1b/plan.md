# Plan: fates-a1b (DL-166 rename onto an enum or constructor field, DL-172 quarantine per field)

**[Proposal]** PLAN phase, 2026-11-08, HEAD `fafc9195`. By: Opus (PLAN fates-a1b). No commit, no production change.
Basis: DL-166 (By: 13ue), DL-172 (By: Fable), DL-158 (By: 13ue), DL-150, DL-152, the fates ledger
([decisions.md](../fates/decisions.md) PF-11, PF-21, RF-04, GF-13; [green-output.md](../fates/green-output.md);
[test-a1.md](../fates/test-a1.md) objection 1). Compiler: `experiments/0001-syntax-to-beam/src/main.rs`.

Test-first applies: both parts change checker and `--stored` behavior. One slice, two behaviors, so two RED / RED review /
GREEN rounds are not needed: both are checker changes in one file with no shared state; one RED with both test groups,
one GREEN (PB-01).

## 1. What changes

### A. DL-166: `rename old -> new` onto an enum or constructor field builds

- **[Verified]** HEAD rejects it in `output_fields` through `renamed_onto` (main.rs ~2142, ~2156, ~2169), text
  `… names the enum field …; a MIGRATE STEP on an enum or constructor field waits for the fate forms (M3, DL-152)`.
- **[Verified]** The live decode already runs the rename before the literal map and the constructor call:
  `versioned_decode` emits `Map.put(value, new, Map.get(value, old))` per step, and the per-version field list takes
  enum and constructor fields `:raw` (PM4-07). Deleting the check is enough for the live decode (http and db).
- **[Verified] Hidden gap in `--stored`.** `value_checks` (main.rs ~6094) reads `body.get(&field)` and `kept(&field)` with
  the field names of the **newest** TYPE VERSION (`literal_fields(ty)`, `ctor_fields(ty)`) on the raw stored body of
  version `stored.version`. No step is applied. A v1 row `{via: "web"}` under `rename via -> channel` then has no key
  `channel`: the enum branch counts it in `mapped` ("no variant of Channel for field channel"), the constructor branch
  gets `ctor_pick(None)` ("matches no signature"). So deleting `renamed_onto` alone makes every live v1 row block the
  build. **[Inference]** The String check already reads the fields of the stored version, so only the enum and
  constructor branches need the mapping.
- Change: delete `renamed_onto` and its two calls and its comment (GF-13: no step keeps the QM4-1 A text; `add` / `drop`
  of a non-String field stop earlier at K4 / K6). Add one helper `stored_key(ty, version, field) -> String` that walks
  the MIGRATE STEPS of `ty` from the newest back to `version` and undoes each `rename` onto the name. Use it in
  `value_checks` for `body.get(..)` and `kept(..)` of the enum and constructor branches. Error texts keep the newest
  field name (the name in the source today).
- All three callers of `value_checks` (RESPONSE RECORDS ~6000, `db.list` items ~6018, rows ~6609) route through the
  helper; the `db.list` item path passes the newest version, so the helper is a no-op there (see risk R3).

### B. DL-172: `quarantine <field>` lifts only failed clauses that test that field

- **[Verified]** HEAD: `ctor_fate(ctor)` (~6388) picks any `Quarantine(Some(_), None)` of the last step; the Elixir
  verdict loop (~6302) lifts every failed rule of the constructor TYPE. `Checker::fates` (~1532) rejects a second
  quarantine line with `one quarantine line per constructor TYPE; Amount has two (PF-11)`.
- **[Verified]** PF-21 help: `failing_param(ctor, sig, inputs)` (~6394) mirrors the clause order and returns the first
  parameter with a literal pattern in the first clause that matches the inputs, else the first parameter.
- Change: in the verdict loop compute the failing clause once; lift only when the last step of `ctor` holds
  `quarantine p` for a parameter `p` that the clause tests (PB-03). Delete the PF-11 "has two" error; keep
  `two fate lines name the field f` (RF-04) and `quarantine f names no field of T`. Make `ctor_fate` take the parameter
  and match `Quarantine(Some(f), None) if f == p`. One clause mirror serves the help and the lift, so they cannot
  disagree (PB-04).
- `fate:` lines: one per quarantine line, each with its own count (the existing `fated` key holds the line text).

## 2. Acceptance criteria

1. `slice6/db/bad_rename/row_rename_enum.beaml` and `row_rename_constructor.beaml` build (exit 0, module on stdout).
2. Live decode over the fake BeamlDb: a v1 row `{order_id, via: "web", amount}` decodes to v2 with `channel` the Web
   variant; a v1 row `{price: {value: "12.50", currency: "EUR"}}` decodes to v2 with `amount` built by the constructor.
3. http: `sdec.CHAIN` (`rename status -> state` onto `PaymentState`) builds; a v1 body `{status: "ok"}` decodes to
   `state` Authorized.
4. `--stored` over the rename fixtures: a v1 row with `via: "web"` builds (counted, no error); a v1 row with
   `via: "tv"` and no kept mark blocks with the DL-122 lost-literal error for field `channel`; the same row with
   `unknown_fields: ["via"]` builds (kept); a v1 row `price: {value: "12.50", currency: ""}` blocks with the constructor
   error for field `amount`; a v2 row with `channel: "web"` builds (control: newest keys unchanged).
5. DL-172: `AMOUNT_V2` + `row(NO_CURRENCY)` exits 1 with the constructor block for `Amount` and the PF-21
   help naming `currency` (`help_q` with the version the S1b helper uses for this source), and **no** `fate:` line.
6. DL-172: `quarantine value, quarantine currency` on `Amount` + rows `ZERO`, `NO_CURRENCY` gives two `fate:` lines
   (count 1 each, each with its own line text) and the a1 stop line `NOT_BUILT_Q`; exit 1.
7. DL-172: only `quarantine currency` + row `{value: "0", currency: ""}` blocks: the first matching clause is
   `"0", _`, which tests `value` (first-match order, PB-03).
8. All of 0004 `run.py` passes (40 steps, counts move only in `slice6-m4` and `slice6-fates`); `cargo test`, `clippy
   -D warnings`, `cargo fmt --check` pass.
9. 0005 `run.py db-up` + `run.py run` pass with the DL-158 case of §6.

## 3. RED tests (written before any `main.rs` change)

All must fail at HEAD `fafc9195`; the reason is named per test.

| Test | File | Fails at HEAD on |
|---|---|---|
| `test_N12_rename_onto_builds` (replaces `test_N12_rename_rejects`, R2) | `slice6_m4_test.py` | exit 1 with the QM4-1 A text |
| `test_N12_rename_onto_runtime` (enum and constructor, AC 2) | `slice6_m4_test.py` | build error before the runtime |
| `test_N12_rename_onto_stored` (subTests: web, tv-lost, tv-kept, bad currency, v2 control; AC 4) | `slice6_m4_test.py` | the QM4-1 A text (all subTests, also the v2 control) |
| `test_enum_output_field_rename_in_a_chain` flips to builds + v1 body decodes (R3, AC 3) | `slice6_m4_test.py` | `assert_rejected` text no longer wanted; HEAD rejects |
| `test_S1g_quarantine_value_does_not_lift_a_currency_rule` (AC 5) | `slice6_fates_test.py` | HEAD prints `fate: 1 stored ROW … (quarantine value)` and the a1 stop line, no ctor block |
| `test_S1h_two_quarantine_lines_count_apart` (AC 6) | `slice6_fates_test.py` | the PF-11 "has two" error |
| `test_S1i_first_matching_clause_decides` (AC 7) | `slice6_fates_test.py` | HEAD lifts the row under `quarantine currency` |
| F5 table: drop `two_quarantine_lines_one_type` | `slice6_fates_test.py` | (removal; covered by S1h) |

RED guards (must pass at HEAD and after GREEN): `two_fate_lines_one_field` stays in F5; S1, S1b `rows_currency`,
S1e, S1f unchanged; `test_N33_*`, `test_N34_*` unchanged.

**RED probe (scratch only, recorded in `red-output.md`):** build a scratch binary from HEAD with only `renamed_onto`
removed and run `test_N12_rename_onto_stored`. The `web`, `tv-kept` and `bad currency` subTests must still fail
("no variant" / "matches no signature"). This shows the `--stored` mapping is needed and that the stored tests do not
pass on the check deletion alone (false-pass guard).

Expected values come from the plan, the fixtures and the existing helpers (`ctor_block`, `help_q`, `fate`,
`literal_block`, `sds.row`, `sd.Slice6Db.runtime`), never from the new compiler.

## 4. Files touched

| File | Change |
|---|---|
| `experiments/0001-syntax-to-beam/src/main.rs` | delete `renamed_onto` + 2 calls; add `stored_key`; use it in `value_checks`; per-parameter `ctor_fate`; delete the PF-11 "has two" error; one clause mirror for help and lift |
| `experiments/0004-generated-replay/tests/slice6_m4_test.py` | R2 / R3 flip; delete `rename_text`, `RENAME_CASES`, `CHAIN_RENAME`; module docstring (QM4-1 A, QM4-4 A defaults gone) |
| `experiments/0004-generated-replay/tests/slice6_fates_test.py` | S1g, S1h, S1i; F5 row removed |
| `experiments/0004-generated-replay/slice6/db/bad_rename/*.beaml` | header comment only ("waits for M3" becomes "builds, DL-166"); path stays (PB-06) |
| `experiments/0005-prototype-fullstack/app/beaml/variants/rename_channel/orders.beaml` (new), `run.py` | DL-158 case (§6) |

Not touched: `wiki/`, the 0004 README (docs worker), `docs/`, review-site pages. The review-site page
`experiments/0005-prototype-fullstack/workflow/2026-11-08/review-site/explain/QM4-1.html` still shows the retired
text; the docs worker marks it retired (not this step).

## 5. Pin impact (six byte-pin sites + V18b)

| Site | Expected | Why |
|---|---|---|
| `slice6_pipe_test` `EFFECT_OUTPUTS`, `slice6_host_struct_test` `BYTE_GUARD`, `effect-reach/byte-guard.json` (digest) | no move | no emit change; the rename fixtures were errors, so no pinned output had them |
| `slice5_syntax_test` `PIN`, `slice6_entry_test` / `slice6_multi_test` `BASE`, `slice6_db_test` `P4_BASE` (hash) | no move | same; `value_checks` and the quarantine lift are `--stored` checks only |
| `record_v3_test` V18b help pins | no move | PF-21 help text unchanged |

**[Inference]** No pin moves. TEST must still run every site; a moved pin is a defect to explain, not to re-pin.

## 6. DL-158: landing in EXPERIMENT 0005

- **DL-166 lands (proposal).** New variant `variants/rename_channel/orders.beaml`: `type Order v2` with `source: Channel`
  in place of `channel`, `migrate Order v1 -> v2 { rename channel -> source }`, the `to_order` line writes
  `source: channel`. New `run.py run` step `gen-rename_channel` right after `n7_seed` (live v1 rows only): `--stored`
  build against the live table must exit 0. Use case `N14 a rename onto the enum field channel builds against the live
  v1 rows` in `EXPECTED`, pass. Gen only, no host compile: the host templates read `channel`, and a host rename is not
  part of the language case. The `finally: gen(None)` restores the checked-in module. This is the one real-data check
  of the `--stored` mapping (§1 A).
- **DL-172 does not land in a1b.** A hit quarantine line stops the build with the a1 stop line (DL-157, run time is
  fates-a2), so 0005 can show nothing new: N9 stays `blocked: fate slice (D036)`. a2 / a3 land N9 with the per-field
  rule.

## 7. Risks

- **R1 (high for a2, not a1b).** The run-time skip (DL-157, fates-a2) must use the same per-field rule. A failure TYPE
  (`BadAmount`) is the same for both clauses, so the Elixir side cannot tell which clause failed from the value alone.
  a2 needs a clause tag from `__beaml_from_T` or the Rust mirror. Record for the a2 plan; a1b changes no run time.
- **R2.** The Rust clause mirror (`failing_param`, `ponytail:` comment) now decides a build result, not only a help
  line. A new pattern kind (guards, Int compares) must change the mirror and the Elixir `cond` together. Keep the
  `ponytail:` comment, extend it: "decides the quarantine lift too (DL-172)".
- **R3.** `db.list` RESPONSE RECORD items are checked at the newest version (~6018), so an old list record of a renamed
  field still blocks with "no variant" / "matches no signature". Loud, not silent. Exclusion for a1b; DL-168 (nested
  and item versions, fates-a2) owns it.
- **R4.** Renames inside a constructor TYPE (`migrate Amount v1 -> v2 { rename v -> value }`) change the constructor
  input keys of the v1 row. **[Unknown]** whether `ctor_pick` sees the old key. Exclusion: a1b covers renames of the
  owner TYPE's fields only; RED adds no case; record as open.
- **R5.** A `quarantine f` whose field no clause tests with a literal never lifts a row (except the first-parameter
  fallback). It is not a compile error; the W3 "line no value hits" path gives exit 0. Accepted (PB-05).

## 8. Exclusions

R3, R4; the http live decode of a quarantined body (PF-22); any fmt change (a4); `redact` / `retire` (fates-b).

## 9. Open questions for the OWNER (language meaning, not decided here)

- **QB-1 (card QUAR-FIELD).** A clause that tests two parameters with literals (`fn Amount "0", ""`): does
  `quarantine value` **or** `quarantine currency` lift it (built default PB-03: either), or must the line name all
  tested parameters? No fixture has such a clause today.
- **QB-2 (card QUAR-FIELD).** A failing clause with no literal pattern (a catch-all that returns the failure TYPE): the
  built default lifts it by the first parameter (PF-21 fallback). Alternative: no quarantine line can lift it.

## Decisions

**Undo**
→ One RED and one GREEN for both parts (PB-01). By: Opus (PLAN fates-a1b)
→ Tests stay in `slice6_m4_test.py` and `slice6_fates_test.py`; no new test file, no new `run.py` step (PB-02). By: Opus (PLAN fates-a1b)
→ `bad_rename/` keeps its path; only header comments change (PB-06). By: Opus (PLAN fates-a1b)
→ Error texts name the newest field name after the rename. By: Opus (PLAN fates-a1b)

**Repair**
→ PB-03: lift when the quarantined parameter has a literal pattern in the first matching clause, over "the first literal parameter only", because the help suggests one parameter that works and a second tested parameter is no wrong answer. Commits us to: QB-1 open. By: Opus (PLAN fates-a1b)
→ PB-04: one clause mirror for help and lift, over a second mirror, because two mirrors can disagree (test-a1 objection 1 was exactly that). By: Opus (PLAN fates-a1b)
→ PB-05: an unhit `quarantine f` stays exit 0, over a new compile error, because W3 already pins that path. By: Opus (PLAN fates-a1b)
→ PB-07: `stored_key` undoes renames in `value_checks`, over applying all steps to the stored body in Rust, because only key moves matter for the checks and `add` / `drop` fields are String (checked by the stored-version field list). By: Opus (PLAN fates-a1b)
→ PB-08: DL-158 lands DL-166 as a gen-only 0005 step, over no 0005 case, because it is the one live-data check of the `--stored` mapping; DL-172 does not land (a1 stop line). Main agent accepts or rejects. By: Opus (PLAN fates-a1b)

**Migrate**
→ QB-1, QB-2 for the OWNER (card QUAR-FIELD); built defaults PB-03 and the PF-21 fallback.

## Repairs (after plan check, before RED)

**[Proposal]** RED fates-a1b, 2026-11-08. By: Opus (RED fates-a1b). Source: [plan-review.md](plan-review.md).

- **O1 (high, accepted by the main agent, By: Fable).** QB-2 default changes: a failing clause with **no literal
  pattern** (a catch-all that returns the failure TYPE) is lifted by **no** quarantine line. Lift only when the first
  matching clause has a literal pattern at the quarantined parameter. The help of such a block gives no quarantine
  suggestion: `  help: no fate line covers a failed rule that tests no parameter with a literal (QB-2 open); restore the
  rule of fn <T> that reads these records`. The PF-21 first-parameter fallback stays for nothing that decides a lift.
  New RED `test_S1j_a_rule_without_a_literal_is_not_lifted` (case `slice6/stored-elixir/nested.beaml` +
  `nested-fail.jsonl`, `fn Amount value, c` fails in `Code`; under `quarantine value` and under `quarantine currency`).
  §9 QB-2 built default now reads "not lifted"; QB-2 stays open for the OWNER (card QUAR-FIELD / QUAR-CLAUSE).
  **Text pins that move in GREEN** (not the six byte-pin sites; §5 extended): `record_v3_test.py` `HELP_REPIN`
  lines 173 to 175 (`stored-elixir/order.jsonl`, `nested-fail.jsonl`, `pipe-fail.jsonl`: all three fail a clause
  without a literal), `slice6_stored_elixir_test.py` line 41 `CTOR_FAILS`. `decode-ctor/stored-fail` (line 171,
  clause `_, ""`) stays. GREEN moves these pins in the same change and lists any other `help_quarantine` use it finds.
- **O2 (medium).** `stored_key(ty, version, field)` walk order: take the MIGRATE STEPS of `ty` with `step.from >= version`,
  **newest step first**; inside a step undo the changes **in reverse order**; each `Rename(old, new)` with `new == name`
  sets `name = old`. RED adds two subTests to `test_N12_rename_onto_stored`: (a) chain `v1 -> v2 { rename via -> ch }`,
  `v2 -> v3 { rename ch -> channel }`: a v1 row `via: "web"` builds, a v2 row `ch: "tv"` blocks with the lost-literal
  error for `channel` (`TYPE Order v2`); (b) `rename via -> channel, map channel "tv" -> Web` in one step: a v1 row
  `via: "tv"` gives the `fate: … mapped` line and the a1 stop line `NOT_BUILT_M`, not the lost-literal block.
- **Note AC 2.** The enum fixture has no `amount` field. The v1 enum row is `{order_id, via: "web"}` and decodes to
  `{order_id, channel: Web}`; the v1 constructor row is `{order_id, price: {value: "12.50", currency: "EUR"}}`.
- **Note S1h.** S1h asserts that its text replace changed the source (`assertNotEqual`, plus `swap` counts 1).
