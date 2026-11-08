# Plan check: M4 step 1, lift D6B-39, migrate first

**[Proposal]** Plan check (fresh agent, normal review, not a Devil's Advocate), 2026-11-08, HEAD `8433a3eb`.
Target: [plan.md](plan.md), [decisions.md](decisions.md), [plan.json](plan.json). Basis: DL-152, DL-153, `skills/implement-step/SKILL.md`.
No tracked file except this one was changed. Scratch builds only (`git archive HEAD` copies, release profile).
By: Opus (plan check m4-lift) for every finding, objection and repair in this file. Dispositions: pending.

## Evidence runs (scratch, not retained in the repo)

- HEAD binary: `git archive HEAD experiments/0001-syntax-to-beam`, `cargo build --release`.
- Probe binary: the same copy with only the two `if self.versioned(output)` D6B-39 branches of `output_fields` deleted.
- Both binaries over every tracked `*.beaml` (2136 files, 185 outside `results/`): stdout plus stderr hashed per file.
- Digest guards with `BEAML_SPIKE` set to each binary: `slice6_pipe_test` (all 13 tests, incl. EFFECT_OUTPUTS),
  `slice6_host_struct_test ... stay_byte_equal` (BYTE_GUARD), `slice6_effect_reach_test ... except_pure_step_spans`.
- Probe runtime over the fake `BeamlDb` (harness of `slice6_db_test.py`): `order_v2`, one v1 row, then one v2 row, `list_orders`.
- Probe `--stored` (harness of `slice6_db_stored_test.py`) over `order_v2`: the R4, R5, R5 control, R6 and R6b inputs.

## Findings

**(1) `--stored` needs no change in step 1.**
- **[Observed]** `type_versions` (main.rs 936-1000): `add` and `drop` reject every non-String TYPE; `rename` checks no TYPE.
- **[Observed]** `value_checks` (main.rs 5576): P4c reads the fields of the stored TYPE VERSION; literal and constructor
  checks read `literal_fields(ty)` and `ctor_fields(ty)` by the newest names.
- Trace, v1 row `{order_id, amount: {value, currency}, channel: "web"}`, TYPE `Order v1`, chain `add note: String = ""`:
  v1 fields are `order_id: String, amount: Amount, channel: Channel`. P4c checks `order_id` only; `note` is not a v1
  field, so it is not checked. `channel` holds the literal `"web"`: no lost literal, no fault. `amount` matches the
  two-parameter signature; the constructor call passes. Result: counted.
- **[Observed]** With the probe binary (no `--stored` change): R4 `rows: 2 rows, 2 checked, 0 not decodable`; R5 the
  exact N19 text for `TYPE Order v1` plus `LITERAL_HELP`; R5 control builds; R6 the DL-102 constructor text; R6b builds.
  A v2 row without `note` gives the P4c text (`no String value for field note`).
- **[Inference]** The central claim holds. R4 to R6b pin `--stored` only against today's code; they turn RED only
  because of the D6B-39 compile error, so they do not test the order "steps first, then checks".

**(2) The depth probe.**
- **[Observed]** Probe build of `order_v2` exits 0 (with a DEAD LINE warning on an empty store).
- **[Observed]** `elixirc --warnings-as-errors` exits 0 (Elixir 1.18.1, as the harness docstring says), with three
  warnings: `__beaml_literal_Channel/1` unused, `__beaml_from_Amount/1` unused, the `{:error, reason}` clause of
  `row_order/1` never matches. So `runtime` reaches the cases.
- **[Observed]** v1 row list: `{:error, %Orders.StoreError{reason: "decode"}}`. A v2 row list gives the same `decode`.
- **[Inference]** The probe separates "lift the compile check only" from "lift plus decode change". It does not separate
  the migrate-first form from a check-first form (the DL-101 tail per TYPE VERSION before the steps): in step 1 no step
  names an enum or constructor field, so both forms give equal values, keys and reasons on every planned case (O2).

**(3) The `unread` list (R8) against DL-109, DL-141 and QV3-6.**
- **[Observed]** The RESPONSE RECORD `unknown_keys` comes from `__beaml_project_<op>` over the raw body and the newest
  `declared` keys, not from the decode. `value_sha256` covers `redacted`, `unknown_keys`, `value` (QV3-6 A). So the
  `unread` join changes no record key and no digest.
- **[Observed]** The decode keys reach only the http span attribute `unknown_keys` (main.rs 3796: union with the
  record keys in a REPLAY RUN). The db path drops them: `row_<t>` matches `{:ok, value, _}`; `db_core` writes
  `unknown_keys: []`.
- **[Inference]** R8 is consistent: a v1 record captured under v1 holds `["extra"]`; the join gives `["extra"]`; the
  union stays `["extra"]`. But R8 must read the decode return (or the span), not the record key, and N33 cannot test
  the join at all. The nested part (`amount.extra`) has no test in the plan (O3).
- **[Observed]** `unknown_fields` (DL-109) is computed on the decoded value; for `orders.list` it is `items.<i>.channel`
  (PDB-18, `slice6_db_test.py` line 278), for `orders.load` it is `channel`. N33_v1_unknown_channel does not say which.
- DL-141 (ENTRY RECORD `outcome`, `reason`) is not touched: no ENTRY LINE decodes a versioned TYPE (see (5)).

**(4) Pin impact "none".**
- **[Observed]** HEAD versus probe over every tracked `*.beaml`: 3 files differ, exactly the 3 files that hit D6B-39
  today: `slice6/db/order_v2/orders.beaml`, `slice6/db/bad/row_enum_chain.beaml`, `slice6/db/bad/row_constructor_chain.beaml`.
  No other tracked source holds an output or ROW TYPE with an enum or constructor field and a chain or mark.
- **[Observed]** `byte-guard.json` holds no `slice6/db` row. All three digest guards pass with both binaries.
- **[Observed]** 39 tracked sources hold a chain or mark (many in BYTE_GUARD, for example `slice2/N-chain`); all are
  String-only outputs or fail earlier. So PM4-06 carries the whole "no pin moves" claim.
- **[Inference]** The rename check cannot change a source that builds today: such a source would already hit D6B-39.
- Not run: the hash pins (`slice5` PIN R-EQ, `slice6_entry` / `slice6_multi` BASE, `P4_BASE`) and `record_v3` V18;
  the full-corpus hash comparison above stands in for them for the lift. The GREEN bytes cannot be checked before GREEN.

**(5) Missing RED cases.**
- DL-122 plus `add`: covered (R5 on a chained `Order`, N33_v1_unknown_channel live). **[Observed]** with the probe.
- Constructor signature change between versions: the constructor has no version; a v1 amount that matches no current
  signature gives `decode` live and "matches no signature of Amount" in `--stored` (observed with the probe for a row
  without `amount`). The live no-signature branch (`__beaml_from_Amount` -> `:error`) has no N33 case. Low.
- `drop` of a String field beside an enum field: R8 (http) only. The db path and P4c over a v1 row with the dropped
  field have no case. Low: P4c code is unchanged.
- ENTRY RECORD path: **[Observed]** `emit_entry` always uses `plain_decode`; D6B-130 rejects a versioned input TYPE.
  `ui.place` decodes `PlaceForm` (unversioned) and builds `Order` in `to_order`. No ENTRY LINE reaches `versioned_decode`.

**(6) 0005 `order_v2` replacing `note_v2`.**
- **[Observed]** `note_v2` is named in: `run.py` (lines 8, 9, 202, 203, 272, 287, 293-300), `notes_test.exs` (lines 3,
  12, 24, 34, 93), `README.md` (lines 39, 53, 59, incl. the output hash `b0990620…`), and the variant source. No 0004 file.
- **[Observed]** `notes_test.exs` line 93: the Note N7b case calls `live_build("note_v2", "n7b")` and expects
  `counted(3, 3, 0)`. It cannot stay "unchanged in content".
- **[Observed]** `run.py phase/1` runs each phase with `--seed 0`: definition order, committed rows kept in `n7_read`.

## Objections (max three)

**O1 · medium · The `n7_read` row counts depend on the test order, and the plan fixes neither.**
Consequence: with rows Order v1 and Note v1 from `n7_seed`, the two N7b rebuilds see 3 and 4 rows in definition order.
R11 expects `counted(4, 4, 0)`; the Note N7b keeps `counted(3, 3, 0)`. Both hold only when the Note N7b runs before R11.
In any other order the RED or GREEN fails for a test reason, and a worker "fixes" a count without a rule. The Note N7b
also must change `live_build("note_v2", ...)` to `"order_v2"`. A copied `v2_module!` guard for Order
(`__beaml_encode_order(%{})`) raises, because the Amount encoder reads a nil map.
Resolving test: the R11 rebuild count and the Note N7b count, both stated with the definition order.

**O2 · medium · No RED case pins "steps first, then checks" (DL-152 effect (1)).**
Consequence: a GREEN that runs the DL-101 tail per TYPE VERSION before the steps passes R1 to R12 and the probe.
Step 1 gives equal results, so there is no wrong outcome now. But the decision intent is unverified, and the M3 step
that adds steps on such fields starts from an unpinned order (same gap as PM4-08 names for `--stored`).
Resolving test: a structural check on the generated `__beaml_decode_order/2`: the MIGRATE CHANGE line
(`Map.put(value, "note", "")`) stands before the first `__beaml_literal_Channel` and `__beaml_from_Amount` use, and the
per-version check names no `Channel` or `Amount` TYPE.

**O3 · medium · R8 and N33_v1_unknown_channel are ambiguous on which key list they read; the nested join is untested.**
Consequence: "unknown_keys is `["extra"]`" can be read as the RESPONSE RECORD key (projection, newest names) or the
decode return. The db path never surfaces decode keys, so N33 cannot check the join. Plan item 5 promises nested
constructor keys (`amount.extra`), but no case has a constructor field on the http path. A GREEN that drops `unread` or
the nested keys can pass. The `unknown_fields` name for a list is `items.0.channel`, not `channel`.
Resolving test: R8 asserts `__beaml_decode_payment(bytes, v1_type) == {:ok, value, ["extra"]}`; N33 names the list key.

## Repairs (text for the main agent)

1. plan.md, 0005 bullets: "Definition order in `NotesReadTest`: R10, Note N7, Note N7b, R11, N11 (`--seed 0`). Note N7b
   changes only `live_build("note_v2", "n7b")` to `live_build("order_v2", "n7b")`; its count stays `counted(3, 3, 0)`.
   R11 then sees Order v1, Note v1, Note v2, Order v2: `counted(4, 4, 0)`."
2. plan.md, R10/R11: "The Order v2 guard checks the module, not the encoder on an empty map: for example
   `Map.has_key?(Orders.__beaml_encode_order(o), "note")` with a full Order value, or `function_exported?`."
3. plan.md, RED tests: add "**R13 `test_N33_order_v2_steps_before_the_tail`**: in the generated `__beaml_decode_order/2`,
   the line `Map.put(value, "note", "")` stands before the first `__beaml_literal_Channel` and `__beaml_from_Amount`;
   the per-version field list holds no `Channel` and no `Amount` check. RED today: build fails (D6B-39). Pins DL-152
   effect (1), which no runtime case can observe in step 1."
4. plan.md, R8: "`unknown_keys` means the third element of `__beaml_decode_payment(bytes, v1_type)`, not the RESPONSE
   RECORD key (that one comes from the projection and stays unchanged, QV3-6)."
5. plan.md, item 5 of "Live decode": either add an http case with a chained constructor field and a stray `amount.extra`,
   or write "nested keys: computed from the raw constructor map as today; not tested in step 1 (db drops decode keys)".
6. plan.md, N33_v1_unknown_channel: "the `orders.list` record lists `items.0.channel` in `unknown_fields` (PDB-18)".
7. plan.md, "The `--stored` path": add "[Observed, plan check] with only the two branches deleted, R4, R5, R5 control,
   R6 and R6b already give the planned results; they turn RED only through D6B-39."
8. plan.md, depth probe: add "Observed in the plan check: the probe build compiles (elixirc 1.18.1 exits 0 with
   unused-function warnings for `__beaml_literal_Channel` and `__beaml_from_Amount`); v1 and v2 rows list with reason
   `decode`. The GREEN must leave no such warning: the 0005 `mix compile --warnings-as-errors` fails on it."
9. plan.md, "Callers, fixtures and tests that change": add the row "0005 `README.md` lines 39, 53, 59 (`note_v2`, output
   hash): docs phase" so the docs worker finds them.
10. plan.md, RED: optional low case "N33_v1_amount_no_signature: a v1 row with `amount: "12.50"` (a String, not a map;
    rehashed) fails with reason `decode`" (the `__beaml_from_Amount` no-match branch).

## Decisions of this check

→ Scope of evidence: scratch builds and probes only, no tracked test changed. By: Opus (plan check m4-lift)
→ O1 to O3 rated medium: none gives a wrong outcome in step 1; none blocks the RED. By: Opus (plan check m4-lift)
→ Repair 10 kept optional (low). By: Opus (plan check m4-lift)

Dispositions of O1 to O3 and repairs 1 to 10: pending (main agent).

## Limits

- The hash pins and V18 were not run; the per-file comparison of both binaries over the tracked corpus stands in.
- The comparison ran without `--stored` arguments. D6B-39 is a compile check before the stored pass, so this holds.
- The 0005 phases were not run (no database started).
