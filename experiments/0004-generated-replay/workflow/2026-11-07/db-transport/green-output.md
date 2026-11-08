# GREEN output: DB TRANSPORTS, P4a and P4b (EXPERIMENT 0005 prerequisite P4)

**[Observed]** GREEN phase, 2026-11-08. By: Opus (GREEN db-transport). Start: HEAD 0311306a. No commit.
Inputs: [plan.md](plan.md) with both repairs, [decisions.md](decisions.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), [red-review.md](red-review.md) (P4a M1 to M3, P4b M1, M2), TEST v3/multi O1.

## Diff summary

**`experiments/0001-syntax-to-beam/src/main.rs`**

- Lexer: `[` and `]` symbols. Parser: a record field TYPE `[T]` keeps the text `[T]` (also in the fingerprint).
- Checks: `list_inner`; LIST TYPE rules in `Checker::new` (record element, one field of a db.list output); `check_type` reads through `[T]`.
- `effects()`: four KINDS with the fourth-kind help; table `"records"` only; a db EFFECT takes `effect_failures` and `db_effect` (put head, get key QDB-1, list query and output, ROW TYPE constructor, redacted, enum without literals, the shared `output_fields` with D6B-39 and DL-065, constructor encode rule). The http body moved into `output_fields` and `effect_failures` unchanged.
- Emit: one `__beaml_valid__` clause per LIST TYPE; db EFFECTS through `emit_db_effect` (parent: input check, client span, `__beaml_fail_`, ROW TYPE decode, `__beaml_encode_<t>`, `__beaml_keys__`, structs, `ATTEMPT_FAILURE`); `Replay` gets `put_`/`get_`/`list_<op>`, `replay_<op>`, `DB_HELPERS` (`db_core`, `db_failed`, `db_call`) and per ROW TYPE `row_<t>` / `rows_<t>`. No `Http` module without `http.post`.
- Shared, byte-equal moves: `versioned_decode`, `emit_type_key`, `keys_fn`, `ATTEMPT_FAILURE`.
- REPLAY RUN db step: operation, attempt, request projection, digest, then the recorded `value`; a rejected record replays its reason; BeamlDb is never called.
- `--stored`: `check_stored` value checks moved into `value_checks` / `value_errors` (`ValueChecks`), with list items checked as the ROW TYPE (`items.<i>.<field>`); `no_path` takes the TYPE, noun and place. New `check_rows` over `rows.jsonl` with `snapshot-meta.json` `row_count` (both directions), `digest_holds` / `canonical` (Rust D6B-58 digest), orphan rows, count line `rows: N rows, K checked, M not decodable`; rows feed W1/W2 (`snapshot.operations`, `snapshot.oldest`). PDB-23 text when no `rows.jsonl` and a db.get or db.list exists.
- Reserved module names: `System` (TEST O1) and `BeamlDb`.

**Tests (tightening only)**

- `slice6_db_stored_test.py`: `test_N24_row_count_below_lines_blocks` (P4b review M2).
- `slice6_db_test.py`: docstring pin-site list and `P4_BASE` wording (P4a review M3). `P4_BASE` stays `ce190054` (passes); the main agent moves it to the GREEN commit.
- `slice6_pipe_test.py` S13: the table text, as the plan says.
- `slice5_syntax_test.py` A2: no PIN compare for a db EFFECT source (the S13 fixture).
- `slice6_multi_test.py`: `BAD_CASES["system"]` + fixture `slice6/multi/bad/system.beaml` (TEST O1).
- `slice6_entry_test.py`, `slice6_multi_test.py` N13: the filter also skips sources with a db EFFECT or a LIST TYPE (they change bytes on purpose; `slice6_db_test` N13 guards the rest). Without it both guards failed on the 16 db fixtures and S13.

**Grammar (`integrations/zed-beaml`)**: `list_type: ($) => seq("[", $.type, "]")` in `_field_type`; `"[" "]"` punctuation highlight; `test/corpus/list_type.txt`; `grammars/beaml.wasm` rebuilt (README step).

## Commands and results

```
cargo fmt --check                                     # ok
cargo clippy --offline --all-targets -- -D warnings   # ok
cargo test --offline --no-fail-fast                   # 22 + 14 passed
BEAML_SPIKE=<0001 target/debug/beaml-spike> python3 -B experiments/0004-generated-replay/tests/<file>
tree-sitter generate --abi 15 --js-runtime native; tree-sitter test --rebuild; tree-sitter test --wasm --rebuild
tree-sitter parse -q on all 23 slice6/db fixtures   # no ERROR
tree-sitter build --wasm -o grammars/beaml.wasm
```

| File | Result |
|---|---|
| slice6_db_test.py | 16 tests, OK, 1 skipped (N2c) |
| slice6_db_stored_test.py | 41 tests, OK, 3 skipped (N28b, N30, N30b) |
| tree-sitter test (both) | 24 of 24 parses, highlight 80 assertions |
| other Python files | see "Full run" below |

**Full run** (every file in `tests/` but `run.py`, `arms_test.py`, `slice6_db*` above):

- OK: slice2_replay 21, slice3_replay 31, slice3_types 69, slice4_replay 27, slice4_retire 87, slice5_replay 12, slice5_rewrite 5, slice5_squash 24, slice5_syntax 60 (after the A2 fix below), slice6_constructor 25, slice6_decode_ctor 8, slice6_decode 10, slice6_effect_reach 8, slice6_entry 20, slice6_enum 20, slice6_failure 22, slice6_fmt 25, slice6_host_struct 3, slice6_int 16, slice6_multi 14, slice6_pipe 12, slice6_record 5, slice6_redacted_failure 8, slice6_redacted 20, slice6_stored_elixir 15, slice6_struct_order 3, record_v3 26 (1 skipped), redteam_b3 1, redteam_c1 8, redteam_c3 5, drift 7, stored_types 33.
- **slice5_syntax A2** failed once on `bad/unsupported_effect_kind.beaml` (PIN compiler text vs the new S13 text). The plan listed only S13; A2 compares the same fixture. Fixed: A2 skips the PIN compare for a source with a db EFFECT. Rerun: 60 OK.
- **overlay_diff_test** fails `query.py: 211 lines, original 213` (0002). **[Observed]** It fails the same way with my changes stashed (HEAD 0311306a). Pre-existing, not this step; not changed.

- Not run: the full `run.py` (task rule).

## Decisions

**Big, Migrate-looking (default built, open; appended to the 0005 [owner review](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) "P4 GREEN defaults")**
→ Constructor field of a ROW TYPE needs a first signature with exactly its String fields (PDB-13 error) statt free constructors, weil encode and decode must round-trip. → By: Opus (GREEN db-transport, default, open) · Migrate
→ `BeamlDb` reserved as a module name (with `System`) statt free, weil the generated code calls it (D6B-203). → By: Opus (GREEN db-transport, default, open) · Migrate

**Repair**
→ ROW TYPE fields follow the http output rule (String, literal enum, constructor) statt also Int and nested records, weil the decode reads no others. → By: Opus (GREEN db-transport, default, open) · Repair
→ `--stored` over rows has no DL-101 shape check statt a field-by-field check, weil no test needs it; a row with a missing field fails `db.list` at run time. → By: Opus (GREEN db-transport, default, open) · Repair
→ Orphan rows print the DL-040 help and a RETIRE LINE frees them statt no help, weil the RED default A names the RETIRE LINE (M5 stays open). → By: Opus (GREEN db-transport, default, open) · Repair
→ Row digest checked in Rust (`canonical`, number text as read) statt skipped, weil N21 and N29 need it; float or exponent text of another encoder would not match. → By: Opus (GREEN db-transport) · Repair
→ slice5_syntax A2 skips the PIN compare for db sources statt a new pin, weil the plan's S13 change hits the same fixture. → By: Opus (GREEN db-transport) · Repair
→ Entry and multi N13 filters skip db sources statt keeping them, weil the db fixtures change bytes on purpose. → By: Opus (GREEN db-transport) · Repair

**Undo**
→ db call `Replay` functions are public (`put_/get_/list_<op>`), helpers private. → By: Opus (GREEN db-transport) · Undo
→ `__beaml_encode_<t>` public in the parent. → By: Opus (GREEN db-transport) · Undo
→ db call record `type`: the output TYPE (ROW TYPE for put/get, the LIST TYPE for list); fields in source order. → By: Opus (GREEN db-transport) · Undo
→ List `unknown_fields` in item order, then field order. → By: Opus (GREEN db-transport) · Undo
→ List-item DL-122 text uses the newest version of the ROW TYPE; a record with two bad items counts 2. → By: Opus (GREEN db-transport) · Undo
→ `with` on a db EFFECT: `error: effect <op>: with stands only after http.post (D6B-31)` (untested). → By: Opus (GREEN db-transport) · Undo
→ `snapshot-meta.json` without `row_count`: `error: snapshot-meta.json has no row_count (P5-19)` (untested). → By: Opus (GREEN db-transport) · Undo
→ A row with a malformed `type` is counted as not decodable. → By: Opus (GREEN db-transport) · Undo
→ The orphan check comes before the outcome check (DL-040: every row counts). → By: Opus (GREEN db-transport) · Undo
→ `rows.jsonl` is read whenever it exists, also beside a source without a db EFFECT. → By: Opus (GREEN db-transport) · Undo
→ LIST TYPE: the element check before the place check. → By: Opus (GREEN db-transport) · Undo
→ No new cargo unit tests (`db_transport_kinds`, `list_type_field`); the Python files cover them. → By: Opus (GREEN db-transport) · Undo
→ `grammars/beaml.wasm` rebuilt. → By: Opus (GREEN db-transport) · Undo

## Limits

- **[Inference]** Byte guards: `slice6_db_test` N13 (every non-db source vs `ce190054`), the four outbound pins and both other N13 guards pass; db sources are new bytes.
- **[Unknown]** Real Postgres `jsonb` and the real `BeamlDb`: 0005 (N2c and later).

## P4c GREEN

**[Observed]** 2026-11-08. By: Opus (GREEN P4c). Inputs: [red-plan.md](red-plan.md#p4c-row-shape-check), [red-output.md](red-output.md#p4c) (P4c and P4c RED repair), [red-review.md](red-review.md#p4c), 0005 [owner review](../../../../0005-prototype-fullstack/workflow/2026-11-07/owner-review.md) "Row shape check" default A.

### Diff summary

`experiments/0001-syntax-to-beam/src/main.rs` only (+29 / -3):

- `ValueChecks.strings`: per (TYPE, place, field) the failed count and the first failed line.
- `value_checks`: for a ROW TYPE (the row TYPE of any non-http EFFECT) at its newest TYPE VERSION, each declared `String` field that is not redacted must hold a String; else one count. Shared by the rows check and the RESPONSE RECORD check (also each `[T]` list item).
- `value_errors`: one text per key, before the enum and constructor texts: `error: TYPE <T>: <n> stored <ROW|RESPONSE RECORD>[S] of <place> has|have no String value for field <f>`, the record source line and the DL-102 help line. No stored value in the text (DL-124).
- RESPONSE RECORD gate: `value_checks` now runs for every record whose TYPE name is the EFFECT output, not only for TYPES with literal or constructor fields (a no-op for other TYPES).

### Commands and results

```
cargo fmt --check; cargo clippy --offline -- -D warnings; cargo test --offline      # experiments/0001-syntax-to-beam
python3 -B experiments/0004-generated-replay/tests/<name>_test.py                    # each file run.py lists, serially
```

- fmt: pass. clippy `-D warnings`: pass. cargo test: 22 + 14 pass.
- `slice6_db_stored_test.py`: **46 tests, OK, 3 skipped** (N28b, N30, N30b). N32, N32b, N32c [missing], N32c [wrong_type] now pass; `N32_control_complete_row_builds` and `N32c_control_complete_list_record_builds` stay green.
- Every other file `run.py` lists (arms, stored_types, slice2 to slice5, all slice6, record_v3, redteam c1/b3/c3, drift): exit 0, OK. Full `run.py` not run.
- EFFECT bytes: no change. The pin guards (slice5_syntax A2, N13 in slice6_entry, slice6_multi, slice6_db) pass; the diff touches only `--stored`.

### Decisions

**Repair**
→ String check on ROW TYPES only statt on every RESPONSE RECORD TYPE, weil the first try blocked 6 stored_types http cases (renamed fields read by the slice 1 decode). http records keep the old gap. → By: Opus (GREEN P4c, default, open) · Repair
→ Check only at the newest TYPE VERSION statt every version, weil an older version gets its fields by the MIGRATE CHAIN (N31 `add`). → By: Opus (GREEN P4c) · Repair

**Undo**
→ Redacted String fields skipped (absent from the projection; ROW TYPES forbid them, M3). → By: Opus (GREEN P4c) · Undo
→ The String text comes before the enum and constructor texts; the Elixir constructor run is skipped then (D6B-105). → By: Opus (GREEN P4c) · Undo
→ Gate removal for RESPONSE RECORDS (no-op for TYPES without checked fields). → By: Opus (GREEN P4c) · Undo
→ No new cargo unit test; the Python file covers it. → By: Opus (GREEN P4c) · Undo

### Limits

- **[Inference]** Plural text (`2 stored ROWS … have`) and a fault in list item 1 are not tested.
- **[Inference]** http RESPONSE RECORDS with a missing String field still pass `--stored`.
- **[Inference]** A `rejected` row or record stays counted, not shape-checked (QV3-8 B).

## P4c TEST repair

**[Observed]** 2026-11-08. By: Opus (TEST repair P4c). Inputs: [review.md](review.md#p4c-test) O1 (high), O2, O3 (medium); rulings by Fable under DL-144 (O1 Repair, O2 Repair, O3 Migrate, default A, open). HEAD `a6550a0f`.

### Diff summary

- `experiments/0001-syntax-to-beam/src/main.rs` (+13 / -7): `value_checks` takes the String fields from the stored TYPE VERSION of the row (`type_versions[version - chain_start]`), not only at the newest version. A version off the chain finds no fields and keeps the path text. `ValueChecks.strings` holds a last counted line: one list record with several bad items counts as 1 record.
- `experiments/0004-generated-replay/tests/slice6_db_stored_test.py` (+38 / -3): N32c subtest `item_1` (`[WIRE1, NO_ID]`), `N32c_two_bad_items_count_one_record`, `N32d_old_version_row_shape_blocks` (missing and Int `label`, PLAIN_V2), `N32e_http_record_shape_gap_builds` (documented gap guard: `arms/gen/orders.beaml`, line 1 of `stored/v1.jsonl` without `value.status`, own digest, exit 0).
- `experiments/0005-prototype-fullstack/workflow/2026-11-07/owner-review.md`: one O3 line under item 8 of "Big, first".

### RED (against HEAD, `git archive HEAD` build in the scratchpad, `BEAML_SPIKE`)

`python3 -B …/slice6_db_stored_test.py -k N32 -k N20_chain`: 9 tests, **3 failures**: N32d [missing] and [wrong_type] exit 0 with the module (the O1 fault); the count test got `2 stored RESPONSE RECORDS … have` (O2). Guards pass at HEAD: N32c `item_1` (GREEN checked every item, review Mutant B), N32e (the gap), `N20_chain_rows_build` (control).

### GREEN (working tree)

- `slice6_db_stored_test.py`: **49 tests, OK, 3 skipped** (N28b, N30, N30b).
- `cargo fmt --check`: pass. `cargo clippy --offline -- -D warnings`: pass. `cargo test --offline`: 22 + 14 pass.
- Every file `run.py` lists, serially (arms, stored_types, slice2 to slice5, all slice6, record_v3, redteam c1/b3/c3, drift): **35 of 35 exit 0, OK**. The first serial loop stopped at the 30 min shell limit after 9 files (all OK); the loop restarted at `slice5_replay`. Full `run.py` not run (task rule).
- EFFECT bytes: no change; the diff touches only `--stored`. The pin files (slice5_syntax, slice6_entry, slice6_multi, slice6_pipe, slice6_db, slice6_host_struct with `slice6/effect-reach/byte-guard.json`) pass unchanged.

### Decisions

**Migrate**
→ O3 http RESPONSE RECORD shape check: A keep the gap (built, pinned by N32e) · B check http after the version fix; default A. → By: Opus (GREEN P4c, default, open), raised to Migrate by the TEST review; OWNER chooses.

**Repair**
→ Fields of the stored TYPE VERSION statt a check after the MIGRATE CHAIN, weil the fields are already in `type_versions` and the chain run is not in `--stored`. → By: Opus (TEST repair P4c) · Repair
→ Count records by a last counted line statt count items, weil the text says RECORDS (O2 ruling). → By: Opus (TEST repair P4c) · Repair

**Undo**
→ N32e recomputes the record digest, so only the shape fault stays. → By: Opus (TEST repair P4c) · Undo
→ List items keep the newest TYPE VERSION of the ROW TYPE (items carry no own version). → By: Opus (TEST repair P4c) · Undo
→ Enum and constructor counts of list items stay per item (out of scope). → By: Opus (TEST repair P4c) · Undo

### Limits

- **[Inference]** A record with several bad items in the enum or constructor checks still counts items.
- **[Observed]** The run-time decode of a fixed v1 row was not run again; N32d covers the build side only.
