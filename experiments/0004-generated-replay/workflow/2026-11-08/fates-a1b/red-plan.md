# RED plan: fates-a1b

**[Proposal]** RED phase, 2026-11-08, HEAD `5cdd0975` (main.rs equal to `fafc9195`). By: Opus (RED fates-a1b).
Inputs: [plan.md](plan.md) (with "Repairs"), [plan-review.md](plan-review.md). Tests only; no production change, no commit.

## Tests written

**`tests/slice6_m4_test.py`** (R2 / R3 flip, AC 1 to 4, O2)

| Test | Checks | Expected source |
|---|---|---|
| `test_N12_rename_onto_builds` (4 subTests) | both `bad_rename/` fixtures exit 0 (module `BeamlSpike`, no ENTRY LINE); with `LIST_TAIL` (db.list + `ui.orders` ENTRY LINE) module `Orders` | AC 1 |
| `test_N12_rename_onto_runtime` | fake BeamlDb: v1 `{order_id, via: "web"}` lists as `channel` Web; v1 `{order_id, price: EUR}` lists as `amount` `%Orders.Amount{}` | AC 2 + note |
| `test_N12_rename_onto_stored` (8 subTests) | `web`, `tv kept` build (`rows: 1 rows, 1 checked, 0 not decodable`); `tv lost` DL-122 block for `channel` + `LITERAL_HELP`; `bad currency` ctor block for `amount` + `CTOR_HELP_PREFIX currency }`; `v2 control` exit 0, no error line; `chain v1` builds; `chain v2` block `TYPE Order v2`; `rename and map` gives `fate: … mapped … (map channel "tv" -> Web)` + `NOT_BUILT_M` | AC 4, O2 |
| `test_enum_output_field_rename_in_a_chain` | `sdec.CHAIN` builds; v1 body `{order_id, status: "ok"}` decodes to `state` Authorized, unknown keys `[]` | AC 3 |

Deleted: `rename_text`, `RENAME_CASES`, `CHAIN_RENAME`, `test_N12_rename_rejects`. Docstring: QM4-1 A and QM4-4 A retired.

**`tests/slice6_fates_test.py`** (AC 5 to 7, O1)

| Test | Checks |
|---|---|
| `test_S1g_quarantine_value_does_not_lift_a_currency_rule` | `AMOUNT_V2` + `row(NO_CURRENCY)`: exactly ctor block + `help_q("Amount", 2, "currency")`, no `fate:` line |
| `test_S1h_two_quarantine_lines_count_apart` | `quarantine value, quarantine currency` + rows `ZERO`, `NO_CURRENCY`: two `fate:` lines (set), `NOT_BUILT_Q` last, 3 lines; setup assert on the replace |
| `test_S1i_first_matching_clause_decides` | `quarantine currency` + `{"0", ""}`: ctor block + `help_q("Amount", 2, "value")`; guard subTest: `NO_CURRENCY` is lifted |
| `test_S1j_a_rule_without_a_literal_is_not_lifted` (2 subTests) | `nested.beaml` with `type Amount v2` + `quarantine value` / `quarantine currency` over `nested-fail.jsonl`: NoCurrency ctor block + `NO_LITERAL_HELP`, no `fate:` line |

F5 row `two_quarantine_lines_one_type` removed (covered by S1h); `two_fate_lines_one_field` stays.

**`tests/slice6_db_test.py`**: one stale comment (line 354) now says the rename cases build.

## Guards (pass at HEAD, must pass after GREEN)

F5 with `two_fate_lines_one_field`; S1, S1b (incl. `rows_currency`), S1e, S1f; S1i guard subTest; all `test_N33_*`,
`test_N34_*`; R3b, R8, R8b, R14 in `M4Decode`.

## Not in this RED

- 0005 variant `rename_channel` (plan §6): DL-158 puts the source, the variant and the `run.py run` use case in GREEN;
  plan §3 lists no 0005 RED. GREEN writes it.
- `bad_rename/*.beaml` header comments (plan §4): fixture text, GREEN changes it.
- Help pins of O1 (`record_v3_test.py` 173 to 175, `slice6_stored_elixir_test.py` 41): they move in GREEN with the
  help change; moving them now would make them fail at HEAD for no behavior reason.
