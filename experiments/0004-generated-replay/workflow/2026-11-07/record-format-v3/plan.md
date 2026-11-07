# Plan: RECORD FORMAT v3, one record core for every EFFECT stream (EXPERIMENT 0005 prerequisite P2)

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no test, no commit, no `run.py` run.
Decision: DL-143 (option A) in [the decision log](../../../../../wiki/planning/decision-log.md). Also binding: DL-105, DL-136, DL-138, DL-141, DL-142, DL-124, DL-144 (free run), D026 with P5-18 in [the 0005 plan](../../../../0005-prototype-fullstack/workflow/2026-11-07/plan.md#o1--p2-changes-record-keys-only-m8-m9-avoided).
Read: `experiments/0001-syntax-to-beam/src/main.rs` at HEAD 35c7e3bf (`git show HEAD:`; the slice 6d GREEN worker edits the working copy), the 6d working copy only for `entry_record/2` and `check_entries`, `tests/slice6_entry_test.py` (expected 6d behaviour), `tests/slice6_record_test.py`, `tests/drift_test.py`, `run.py`, the record contract of [slice6b-records-v2/spec.md](../slice6b-records-v2/spec.md) and its [repin.md](../slice6b-records-v2/repin.md).
Design decisions: [decisions.md](decisions.md) (RV3-01 to RV3-13, Migrate questions QV3-1 to QV3-8, all `(default, open)` under DL-144). OWNER list: [owner-review.md](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md#record-format-v3-p2). Machine form: [plan.json](plan.json).
By: Opus (PLAN record-v3) for every proposal in this file.

## Facts the step builds on

- **[Verified]** Two writers exist. `Replay.record/3` writes the RESPONSE RECORD (`version: 2`) at HEAD. `Replay.entry_record/2` writes the ENTRY RECORD (`version: 2`) in the 6d working copy.
- **[Verified]** RESPONSE RECORD v2 keys: `version`, `trace_id`, `client_span_id`, `artifact_id`, `operation`, `attempt`, `request`, `status`, `value`, `redacted`, `unknown_keys`, `value_sha256`, `type`; `unknown_fields` only when the output TYPE has a keep-value variant.
- **[Verified]** ENTRY RECORD v2 keys: `version`, `trace_id`, `server_span_id`, `artifact_id`, `operation`, `attempt`, `value`, `redacted`, `unknown_keys`, `unknown_fields`, `value_sha256`, `type`, `outcome`, `reason`.
- **[Verified]** `body_base64`, `body_sha256`, `body_length` exist only in version 1 (`slice6/record/stored-v1.jsonl`, the fixture of the D6B-59 reject). Version 2 replaced them with `value` + `value_sha256` (DL-105, D6B-53 to D6B-60). So the HTTP mapping is settled: `value` is the typed projection of the decoded JSON body, never the raw body (RV3-02).
- **[Verified]** `--stored` at HEAD accepts RESPONSE RECORD version 2 only (D6B-59 text). It does not read `status` (DL-136 is decided, not built for RESPONSE RECORDS). The 6d `check_entries` checks no `version`; it skips `outcome: "rejected"` for constructors and literals and prints `N entries, K checked, M rejected at capture`.
- **[Verified]** The REPLAY RUN (`Replay.run/3`) reads `trace_id`, `operation`, `attempt`, `request`, `status`, `value`, `redacted`, `unknown_keys`, `value_sha256`, `type`. `Replay.entry/2` reads `operation` and the digest keys. Neither reads `version` or a span id.
- **[Verified]** The `--stored` DRIVER (`elixir -e`) gets constructor calls from Rust and reads no record key.
- **[Verified]** `record/3` already calls `@parent.__beaml_decode_E(bytes)` when the output has a keep-value field; the decode exists in every output form and returns `{:ok, v, keys}`, `{:error, "constructor"}` or `:error`.
- **[Verified]** Every tracked RESPONSE RECORD fixture has `status: 200` (15 files, survey in this plan phase).
- **[Verified]** `run.py` reads `value` (`body_json`), `request` and `status`; no `version`. `drift_test.py` asserts `version == 2` and `status == 200` on the repair record (line 198, 223).

## The v3 shape (QV3-1 to QV3-3, QV3-6, defaults)

| Part | Keys | Notes |
|---|---|---|
| Core, every stream | `version: 3`, `trace_id`, `span_id`, `artifact_id`, `operation`, `attempt`, `type`, `value`, `value_sha256`, `redacted`, `unknown_keys`, `unknown_fields`, `outcome`, `reason` | 14 keys |
| HTTP extras (RESPONSE RECORD) | `request`, `status` | flat, top level |
| UI extras (ENTRY RECORD) | none | |
| db extras (P4) | decided in P4; the core is fixed here | |

- **Format marker (QV3-1 default A).** The key `version` with the value `3`. It is the record format version, not a TYPE VERSION (that stays `type.version`).
- **Span id (QV3-2 default A).** One key `span_id`: the client span for HTTP, the root server span for UI. `client_span_id` and `server_span_id` go.
- **Extras (QV3-3 default A).** Flat top-level keys, as today. The REPLAY RUN keeps `record["status"]`.
- **`unknown_fields` (RV3-03).** Always written; `[]` when the TYPE has no keep-value variant.
- **Digest (QV3-6 default A).** `value_sha256` keeps the D6B-58 rule over `redacted`, `unknown_keys`, `value`. So no stored digest changes and `stored_types_test.value_sha256` stays.

## `outcome` and `reason` of a RESPONSE RECORD (QV3-4 default A)

Written in `record/3` at capture, from facts the live call has:

| Capture fact | `outcome` | `reason` |
|---|---|---|
| `status != 200` | `"rejected"` | `"status"` |
| 200, decode `:error` | `"rejected"` | `"decode"` |
| 200, decode `{:error, "constructor"}` | `"rejected"` | `"constructor"` |
| 200, decode `{:ok, _, _}` | `"accepted"` | `null` |

- Rule: the record `reason` equals the `reason` of the failure that the live call returns (V8). A transport failure writes no record, as today.
- The digest is not a capture fact: the writer always writes a correct digest. DL-136 "bad digest" is a read-time fact (RV3-07).
- `unknown_fields` is read from the `{:ok, decoded, _}` decode result as today, else `[]`.

## Readers

| Reader | Reads after P2 | Change |
|---|---|---|
| `--stored`, RESPONSE RECORDS | `version` must be 3; `outcome`; the v2 value keys | version text (V12); `rejected` records skip the DL-102 constructor and DL-122 literal checks (QV3-8 A); count line `N records, K checked, M not replayable`, printed only when M > 0 (QV3-7 A) |
| `--stored`, ENTRY RECORDS | `version` must be 3 (new, RV3-06); the 6d keys | version text (V13); the 6d count line unchanged |
| REPLAY RUN `Replay.run/3`, `body/1`, `digest/3`, `Replay.entry/2` | unchanged | none (RV3-04); bytes equal (V18) |
| DRIVER | no record key | none (RV3-05) |
| `run.py` | `value`, `request`, `status` | none |
| `drift_test.py` | `version` | `2` becomes `3` (line 198); nothing else |
| DRIFT pin (`run.py` `DRIFT_PIN`, `drift_test.PIN`) | row classes | unchanged; V20 proves it at TEST |

- TYPE path check, redacted-held check (D6B-72) and the orphan count still read every record, also a rejected one (QV3-8 A, parity with 6d and the 6d RED review note R6D-15).
- Bad-digest records: not skipped in P2 (RV3-07). The DL-136 digest half is a follow-up step P2b over both streams.

## Old files (QV3-5 default A: one-time rewrite)

- `convert_v3.py` in this ledger (RV3-08), run once from the repository root. Input must be `version: 2` (assert). Per record: `version` 3; `client_span_id` or `server_span_id` becomes `span_id`; `unknown_fields` `[]` when absent; RESPONSE RECORD `outcome`/`reason` by `status` only (RV3-12): 200 gives `accepted`/`null`, other gives `rejected`/`"status"`; ENTRY RECORD keeps its `outcome`/`reason`. `value` and `value_sha256` stay; the script recomputes the digest with `stored_types_test.value_sha256` and asserts equality.
- Files: `stored/v1.jsonl`, `stored/v1-v2.jsonl`, `slice6/decode/stored.jsonl`, `stored-fail.jsonl`, `stored-resolved.jsonl`, `slice6/decode-ctor/stored.jsonl`, `stored-fail.jsonl`, `stored-nomatch.jsonl`, `slice6/redacted/stored-unredacted.jsonl`, `stored-request-unredacted.jsonl`, `slice6/stored-elixir/order.jsonl`, `nested-fail.jsonl`, `pipe-fail.jsonl`, `rec-loop.jsonl`, `slice6/entry/stored/entries.jsonl`. `slice6/entry/stored/responses.jsonl` is empty and stays.
- Not converted: `slice6/record/stored-v1.jsonl` (the version 1 reject fixture), every `results/*` run (retained evidence, immutable).
- The fixture file names keep their names (`stored/v1.jsonl` names TYPE VERSION 1, not the record version).

## Change (defaults, each in decisions.md)

1. **RESPONSE writer** (`Replay.record/3`, emit in `emit_effect`). `version: 3`; `span_id:` instead of `client_span_id:`; `unknown_fields:` always; one `case` gives `{outcome, reason, unknown_fields}` from `status` and `@parent.__beaml_decode_E(bytes)`; `outcome:`, `reason:` keys. No change to the live EFFECT function, `__beaml_result_E`, `run/3`, `body/1`, `digest/3`.
2. **ENTRY writer** (`Replay.entry_record/2`). `version: 3`; `span_id:` instead of `server_span_id:`. No other change.
3. **`check_stored`.** Version text `3` and `DL-143`; read `outcome` (`accepted`, `rejected`, else the error `stored RESPONSE RECORD has no capture outcome accepted or rejected (DL-138)`, the 6d text with RESPONSE); skip rejected records in the `literal_fields` and `ctor_fields` loop; count; return the count line when M > 0.
4. **`check_entries`.** Version check before the `outcome` read, same text form with ENTRY.
5. **Output order.** The RESPONSE count line (when printed) comes before the ENTRY count line on stderr.
6. **Fixtures.** `convert_v3.py` over the files above. New fixture `slice6/record-v3/` (V14).
7. **Tests.** New `tests/record_v3_test.py`; listed assertions move (table below); five pin sites move with the diff proof.

## First failing test: `tests/record_v3_test.py`

Harness: the `slice6_record_test.py` runtime harness (`stored.(status, body)`, `replay.(record)`, `text.(...)`, `sd.Slice6Decode.run_runtime`) for the RESPONSE writer; the `slice6_entry_test.py` runtime harness for the ENTRY writer; `sf.Slice6Failure.compile` for `--stored`. Expected values come from this plan, DL-143 and `stored_types_test.value_sha256`, never from the new compiler.

- **V1 (first RED).** `stored.(200, U)["version"] == 3`. Today `2`.
- **V2 (key set).** `Enum.sort(Map.keys(stored.(200, U)))` equals the 14 core keys plus `request`, `status`, sorted. Replaces P1 `RECORD_KEYS`.
- **V3 (span id).** The record has `span_id`; it has no `client_span_id`, no `server_span_id`.
- **V4 (accepted).** `stored.(200, VALID)`: `outcome == "accepted"`, `reason == :null`.
- **V5 (status).** `stored.(503, VALID)`: `outcome == "rejected"`, `reason == "status"`; `value` and `value_sha256` as P4 today (D6B-57).
- **V6 (decode).** `stored.(200, MISSING_KEY)`: `"rejected"`, `"decode"`.
- **V7 (constructor).** On a `slice6/decode-ctor` source: a 200 body whose field fails the constructor gives `"rejected"`, `"constructor"`.
- **V8 (reason parity).** For V5, V6, V7 the live call returns `{:error, %PaymentError{reason: r}}` with `r` equal to the record `reason`.
- **V9 (`unknown_fields` always).** `arms/gen/orders.beaml` (no enum): `unknown_fields == []`. A `slice6/decode` source with a kept `Unknown`: the field names, as today.
- **V10 (digest unchanged).** `value_sha256 == st.value_sha256(value, unknown_keys, redacted)` for V4 to V7; `replay.(stored.(200, VALID)) == {:ok, PAYMENT}`.
- **V11 (ENTRY RECORD).** `ui_place(good)` in the 6d harness: one `"entries"` record with `version: 3`, key set exactly the 14 core keys, `span_id` present, `outcome`/`reason` as 6d N8.
- **V12 (RESPONSE version reject).** `--stored` over a version 2 file: exit 1, empty stdout, stderr exactly
  `error: stored RESPONSE RECORD has record version 2; this build reads record version 3 only (DL-143)` and `  record source: S:1 (line 1)`. `slice6/record/stored-v1.jsonl` gives the same with `1`; a record without `version` gives `none`.
- **V13 (ENTRY version reject).** An `entries.jsonl` with one version 2 line beside an empty responses file: exit 1, stderr exactly
  `error: stored ENTRY RECORD has record version 2; this build reads record version 3 only (DL-143)` and `  record source: E:1 (line 1)`.
- **V14 (count line).** New fixture `slice6/record-v3/stored-mixed.jsonl`, three records of one `slice6/decode-ctor` source: line 1 `accepted` (value passes a stricter `Amount`), line 2 `rejected`/`status` (503), line 3 `rejected`/`constructor`; lines 2 and 3 hold values that fail the stricter `Amount`. Build the stricter source with `--stored`: exit 0, stderr exactly `3 records, 1 checked, 2 not replayable`.
- **V14b (control, no false pass).** The same file with line 1 failing the stricter `Amount`: exit 1 with the DL-102 block text of step 8 (count line filtered, as `blocked()` in 6d). Line 1 is named, lines 2 and 3 are not.
- **V15 (no line at M = 0).** Build `arms/gen/orders.beaml` with the converted `stored/v1.jsonl`: stderr equals the pre-P2 compiler stderr over the v2 file.
- **V16 (DL-124).** V14 and V14b stderr hold no stored value word (list as `STORED_WORDS` in 6d).
- **V17 (converter).** Every converted file: all lines `version: 3`; key sets as V2 or V11; recomputed digest equals `value_sha256`; `git diff --stat` touches only the 15 listed files.
- **V18 (diff proof, guard).** See [Pin sites](#pin-sites-and-diff-proof).
- **V19 (events).** Every compile keeps the harness check: no source text, no path, no stored value in `.beaml/actions.jsonl`.
- **V20 (DRIFT, TEST phase).** `run.py drift` rows equal `DRIFT_PIN`; `drift_test.py` passes with the version 3 line.
- **V21 (M8, M9 guard).** Every existing block text test passes with its text unchanged (6d `CTOR_BLOCK`, `LITERAL_BLOCK`, `NO_ENTRY_BLOCK`; step 8 and 13 texts). No generated function gets a new parameter.

## Existing assertions that change (each by name)

| File | Assertion | Today | After P2 |
|---|---|---|---|
| `tests/slice6_record_test.py` | `P1_version_is_2`, `P4_not_json_value_is_null` (`version == 2`) | 2 | 3 |
| `tests/slice6_record_test.py` | `RECORD_KEYS` (`P1_key_set_is_D6B_53`) | v2 keys | V2 key set |
| `tests/slice6_record_test.py` | `version_error()`, `test_P6_*`, `test_runtime_record_version_2` | "version 2 only (DL-105)" | "version 3 only (DL-143)"; the version 2 build case uses a v3 file |
| `tests/slice6_entry_test.py` | `ENTRY_KEYS`, N8 `ex({"version": 2, ...})` (line 232) | `server_span_id`, 2 | `span_id`, 3 |
| `tests/slice6_entry_test.py` | `BASE` (N13) | `857fb310` | the P2 base commit (fifth pin site, RV3-09) |
| `tests/arms_test.py` | line 373 `"version": 2` | 2 | 3 |
| `tests/redteam_c1_test.py` | `TEMPLATE` | `version: 2`, `client_span_id` | `version: 3`, `span_id`, `outcome: "accepted"`, `reason: null`, `unknown_fields: []` |
| `tests/drift_test.py` | line 198 | `!= 2` | `!= 3` |
| `tests/stored_types_test.py` | `with_value` docstring and callers | version 2 | version 3 (base records come converted) |

- **[Inference]** No other test asserts the v2 key names (grep for `client_span_id`, `server_span_id`, `"version"` over `tests/` and `cli.rs` in this phase). The RED worker greps again at the P2 base.

## Pin sites and diff proof

Five sites move together (the four of the byte-pin note plus the 6d N13 base, RV3-09):

1. `tests/slice5_syntax_test.py` `PIN` (F01, A2).
2. `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS` (also read by `slice6_struct_order_test.py`).
3. `tests/slice6_host_struct_test.py` `BYTE_GUARD`.
4. `slice6/effect-reach/byte-guard.json` (keep its `(71, 40)` setup invariant, as the step 6b re-pin did).
5. `tests/slice6_entry_test.py` `BASE` of N13.

- **Diff proof.** Compile every pinned source and every A2 and N13 source with the pre-P2 compiler and the P2 compiler (`--stored stored/empty.jsonl` where needed). Group each changed line by the nearest `def`, `defp` or `defmodule` above it (method of [repin.md](../slice6b-records-v2/repin.md)).
- **Allowed hunks.** `Replay.record/3` in every EFFECT source; `Replay.entry_record/2` in ENTRY LINE sources. Nothing else.
- **Must be equal.** `Replay.run/3`, `body/1`, `digest/3`, `Replay.entry/2`, the live EFFECT function, every non-EFFECT output, `payments.generated.snapshot`, every exit code, every stderr over a converted fixture.
- A hunk outside the allowed set stops the re-pin and is reported (repin.md precedent).
- `payments.generated.snapshot` stays byte-equal (no EFFECT in `payments.beaml`).

## Checks

- 0001: `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings`.
- 0004: `tests/record_v3_test.py`, every `slice6_*_test.py`, `slice5_syntax_test.py` first (byte-pin note), `stored_types_test.py`, `redteam_c1_test.py`, `arms_test.py`; `python3 -B experiments/0004-generated-replay/run.py` once at TEST (V20).

## Order

- After the slice 6d TEST commit (6d GREEN writes `main.rs` now). The P2 base is that commit. One code-writing worker at a time. Before P3 and P4 of EXPERIMENT 0005.

## Exclusions

- The DL-136 digest half: `--stored` does not yet skip bad-digest records (P2b, RV3-07).
- The db stream extras and writer (P4). P2 fixes the core only.
- M8 and M9 (D026, P5-18): no failure struct as an input value; no new per-record line in a block text. A worker that must change either one stops and reports a blocker.
- A version check in the REPLAY RUN (RV3-04).
- Retention, RETIRE LINE semantics, fate forms (DL-125, D026 M3 to M5).
- Wiki and README contract text: the docs phase.

## Limits

- **[Inference]** The digest does not cover `outcome`, `reason`, `status`, `span_id` or `unknown_fields` (QV3-6 A). A hand-edited `outcome` is not detected; `--stored` trusts it.
- **[Inference]** A converted v2 RESPONSE RECORD with status 200 is `accepted` even if its body failed the decode at capture (RV3-12). The converted fixtures keep their `--stored` result.
- **[Inference]** A rejected record still counts in the TYPE path check (QV3-8 A): an old 503 record of a TYPE VERSION without a path still blocks.
- **[Inference]** The REPLAY RUN reads no `version`: a v2 record still replays under the v3 code. Only `--stored` enforces v3.
- **[Inference]** `record/3` decodes the body once more on every 200 call (already true for outputs with a keep-value field).
- **[Unknown]** Whether the 6d GREEN changes `entry_record/2` again before the P2 base. The RED worker reads it at the base.
- **[Inference]** The count line prints only when M > 0 (QV3-7 A); a clean file gives no line, unlike the ENTRY line.

## Smallest next test

- P2b: a `--stored` record with a wrong `value_sha256` is counted in `M not replayable` and not checked, for both streams (DL-136 second half).

## Plan repair (after plan check), 2026-11-07

**[Proposal]** PLAN repair after the [plan check](plan-review.md) BLOCK (O1 high, O2 high, O3 medium). Main-agent rulings under DL-144 applied as given. This section overrides the sections above where they differ.
By: Fable (main agent, rulings under DL-144) for the O1, O2 and O3 changes; Opus (PLAN repair record-v3) for the details marked so in [decisions.md](decisions.md#plan-repair-after-plan-check-2026-11-07).

### O1: GREEN sub-step "pin sites follow GREEN" (RV3-14)

The table row "`BASE` (N13) → the P2 base commit" is wrong and is replaced. N13 keeps its full source set; no EFFECT source is excluded.

1. **GREEN.** Write the P2 change. Run the diff proof (V18) against the **P2 base compiler** (the 6d TEST commit). Move the three byte pins to the P2 bytes in the GREEN commit:
   - site 2: `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS` (also read by `slice6_struct_order_test.py`);
   - site 3: `tests/slice6_host_struct_test.py` `BYTE_GUARD`;
   - site 4: `slice6/effect-reach/byte-guard.json` (keep the `(71, 40)` setup invariant).
2. **Commit right after GREEN** (the `acf12d75` pattern). Set the two commit pins to the P2 GREEN commit hash:
   - site 1: `tests/slice5_syntax_test.py` `PIN`;
   - site 5: `tests/slice6_entry_test.py` `BASE` (N13).
   The commit message names the GREEN hash. The ledger keeps the diff proof hunk list (allowed hunks only: `Replay.record/3`, `Replay.entry_record/2`).
3. Run `slice5_syntax_test.py` first, then `slice6_entry_test.py` N13, at the pinned GREEN hash. Both pass with the full source set.

### O2: QV3-8 default B (rejected RESPONSE RECORD skips the value and path checks)

Replaces the reader row and the bullet "TYPE path check, redacted-held check (D6B-72) and the orphan count still read every record (QV3-8 A, parity ...)". The parity claim is withdrawn: 6d `check_entries` has no TYPE path check.

| Check | `accepted` record | `rejected` record (non-200, or 200 with decode/constructor reject at capture) |
|---|---|---|
| DL-102 constructors, DL-122 literals | run | skip |
| TYPE path check, W2 version count | run | skip |
| Orphan count (DL-040) | run | run |
| Redacted-held check (D6B-72) | run | run |

- Because: DL-136 (OWNER) "a recorded outage is not a TYPE change and asks for no MIGRATE STEP". DL-137 carries it to database rows (P4).
- Change step 3 of "Change": the skip covers the path check and the W2 count too.
- Limit "a rejected record still counts in the TYPE path check" is withdrawn. New limit: a rejected record of a TYPE VERSION without a path is not seen by the path check; only its orphan and held checks run.

### O3: count line text and the P2b marker (QV3-7 big)

- Count line (stderr, when printed): `N records, K checked, M rejected at capture`. The word "not replayable" goes; it would state a false fact for a bad-digest record that P2 still checks.
- Second line directly below it: `digest not verified (P2b)`. It stays until P2b lands; P2b removes it.
- When it prints: QV3-7 default A unchanged (only when M > 0). Both lines print together or not at all.
- P2b is open item [D035](../../../../../wiki/planning/decisions-to-be-made.md#d035--p2b-the-dl-136-digest-half-for-stored-records) (trigger: before 0005 TEST). The docs phase marks DL-136 "half built (P2), digest half open (P2b, D035)".

### Changed and new tests

- **V14 (changed).** stderr exactly `3 records, 1 checked, 2 rejected at capture` and `digest not verified (P2b)`, in this order.
- **V14b (changed).** `blocked()` filters both lines. Otherwise unchanged.
- **V15 (unchanged).** M = 0 gives no line, so neither line prints.
- **V16 (changed).** Also covers V22 and V23 stderr.
- **V22 (new, QV3-8 B, 503).** A one-record file: `rejected`/`status` (503) of a TYPE VERSION that has no path in the built source. `--stored` exit 0, stdout as the pre-P2 build over an empty file, stderr exactly the two count lines `1 records, 0 checked, 1 rejected at capture` and `digest not verified (P2b)`.
- **V23 (new, QV3-8 B, 200 rejected at capture).** The same with `status: 200`, `rejected`/`constructor`. Same exit and stderr.
- **V24 (new, control for V22 and V23).** The same file with the record `accepted`: exit 1 with the existing TYPE path block text (V21 text unchanged). Proves the skip, not a missing check.
- **V25 (new, held still runs).** A `rejected`/`status` record with an unredacted secret field: exit 1 with the D6B-72 text. Proves the held check reads rejected records.
- **Text of V22 count.** `1 records` follows the one format `N records`; no singular form (RV3-16).

### Exclusions and limits (changed)

- The DL-136 digest half stays out of P2 and is now tracked as D035 (not only in this ledger).
- The REPLAY RUN still reads no `version` (unchanged).
