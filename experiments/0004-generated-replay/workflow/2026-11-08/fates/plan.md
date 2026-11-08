# Plan: the FATE slice (DL-125, DL-155, DL-156)

**[Proposal]** PLAN phase, 2026-11-08, HEAD `5e05b5f3`. Task records only. No production file, no test, no commit, no run.
Decision basis (decision log): DL-102, DL-111, DL-116, DL-122, DL-124, DL-125, DL-134, DL-137, DL-140, DL-142, DL-150,
DL-151, DL-152, DL-153, DL-155, DL-156 (all By: 13ue, except DL-124 By: Fable). Concept: [migrate-fates](../../../../../wiki/concepts/migrate-fates.md).
Open register items: D041, D042, D035, D036 (M3, M5). Defaults PF-01 to PF-24 and OWNER questions QF-1 to QF-9: [decisions.md](decisions.md).
Machine form: [plan.json](plan.json). By: Opus (PLAN fates) for every proposal in this file.

## Scope in eight lines

1. Parser and checker: `quarantine f`, `retire f keep N days`, `redact f`, `map f "old" -> V`, bare `map "old" -> V`, `enum E vN`.
2. A MIGRATE STEP may hold fate lines only (no `rename`, `add` or `drop` needed); `migrate E v1 -> v2` works for an enum.
3. `--stored`: `quarantine` lifts the DL-102 constructor block, `map` lifts the DL-122 lost-literal block; counts are printed.
4. DL-155 gate: an affected stored value without the next TYPE VERSION and a fate line blocks; the help names the version form.
5. Generated Elixir: the decode applies `map`; a quarantined row is skipped and counted, never a decode error (QF-1 default).
6. REPLAY RUN: a record with a quarantined value returns the typed reason `quarantined` and does not run.
7. 0005: `stricter` gets `type Amount v2` and `migrate Amount v1 -> v2 { quarantine value }` (N9); a `channel_v2` variant maps `"app"`.
8. `beaml fmt` layout for MIGRATE STEP bodies, tree-sitter grammar, highlights, corpus, wasm; docs list.

**Test-first rule: applies.** Every item changes parse acceptance, compile errors, `--stored` exit codes or generated behavior.
Item 8 (`fmt`, tree-sitter) is behavior too: the `fmt` output and the corpus trees are tested before the change.

## Split proposal (PF-01)

**[Proposal]** The slice is too big for one RED / GREEN pair. Split by end-to-end behavior, not by layer:

| Part | Content | Why it stands alone |
|---|---|---|
| **fates-a** (this plan, built now) | syntax of all five forms and `enum E vN`; `quarantine` and `map` end to end: checker, `--stored`, DL-155 gate, generated decode, REPLAY RUN, 0005 N9 and N9b; `fmt`; tree-sitter | DL-156 asks for the loop "block → fate → green" in the demo app. `quarantine` and `map` close it for DL-102 and DL-122 |
| **fates-b** (later plan) | `redact f` (DL-111 exit, eager removal QF-9), `retire f keep N days` (M5, QF-4), DL-140 swap detection and the in-place rule change gap (QF-8), SQUASH note for dead fate lines, D042 | each needs an OWNER answer that is a record format or a stored-data meaning (DL-139 excludes those from built defaults) |

**[Proposal]** In fates-a, `redact f` and `retire f keep N days` parse and format, and the checker rejects them with a loud text
(PF-09). A source can never build with a fate line whose meaning is not built.

**[Proposal]** fates-a runs as four steps, each with its own RED, RED review and GREEN (implement-step "for each new meaningful
behavior step"). Only one code writer at a time.

| Step | Behavior | Files |
|---|---|---|
| a1 | parse, check, `--stored` lift, counts, DL-155 gate | `main.rs`, `tests/slice6_fates_test.py`, 0004 `run.py` step `slice6-fates` |
| a2 | generated decode (`map`, quarantine skip), REPLAY RUN | `main.rs`, `tests/slice6_fates_test.py` |
| a3 | 0005 N9, N9b, run.py acceptance | 0005 `variants/`, `fate_test.exs`, `run.py` |
| a4 | `fmt` body rule, tree-sitter | `main.rs` `fn bodies`, `tests/slice6_fmt_test.py`, `integrations/zed-beaml/` |

**[Inference]** a1 alone gives a green build whose `db.list` still fails at run time on the quarantined row (QDB-4). That is the
DL-150 hazard. So a1 and a2 must land before a3, and the slice is not reported done before a3 passes.

## Facts the slice builds on (observed at HEAD `5e05b5f3`)

- **[Verified]** `Parser::change` (main.rs line 343) accepts `rename`, `add`, `drop`; any other word gives
  `unsupported migrate step: <w>; a MIGRATE CHANGE is rename, add or drop`. Changes are comma-separated (line 750).
- **[Verified]** `derive_versions` (line 865) requires the migrate TYPE to be a record (`migrate E: unknown type: E` for an enum)
  and requires at least one change per step (line 909: `a MIGRATE STEP needs at least one rename, add or drop`).
- **[Verified]** `enum` parsing (line 550) takes no VERSION MARK. The grammar `enum_declaration` takes none either.
- **[Verified]** Probe (scratch, not retained): `stricter` with `type Amount v2` and no step builds against the M4 run ROW SNAPSHOT
  (`rows: 2 rows, 2 checked, 0 not decodable`); the generated Elixir equals plain `stricter` except the module name.
  A nested TYPE VERSION is source-only today: the `Order` fingerprint lists `["amount","Amount"]` without a version.
- **[Verified]** The stored row core has `unknown_fields` (DL-142) and no time key; the table column `inserted_at` exists
  (0005 host migration) but is not in the ROW SNAPSHOT. RESPONSE RECORDS carry no time key either. So `retire` has no age source.
- **[Verified]** DL-140 (known-to-known swap) is not built: no site in main.rs. The stored row holds only the ENUM LITERAL, not the
  variant name, so the compiler cannot see a swap without the previous literal table (QF-8).
- **[Verified]** DL-150 is not built: `rows: N rows, K checked, M not decodable` counts and passes (line 6052).
- **[Verified]** Block sites that get the DL-155 help: DL-102 rows and RESPONSE RECORDS (lines 5732, 5740, 5821), DL-122
  (line 5754), ENTRY RECORDS (lines 4692, 4752). DL-111 redact block (line 5619) stays for fates-b.
- **[Verified]** Tests that pin those help lines: `slice6_db_stored_test.py` (`HELP_PREFIX`, `LITERAL_HELP`), `slice6_entry_test.py`
  (95, 100), `slice6_stored_elixir_test.py` (53), `slice6_decode_test.py` (214), `slice6_db_test.py` (383),
  `slice6_decode_ctor_test.py` (`HELP_MIGRATE`), `slice6_redacted_test.py` (258, unchanged in fates-a). 0005 `stored_test.exs`
  pins only the first line (`@blocked`), not the help.
- **[Verified]** `fmt` (`fn bodies`, line 6877) touches only `type` and `enum` bodies. All tracked MIGRATE STEPS with two or more
  changes are on one line in slice 3 to 5 sources and in `integrations/zed-beaml/test/highlight/forms.beaml`; the `slice6/fmt`
  fixtures hold one change per step.
- **[Verified]** Hash guards compile every tracked source under `slice*/` etc. at an old commit: `slice6_db_test` N13 skips only
  sources with a db EFFECT or a LIST TYPE; the entry, multi and slice 5 guards skip db sources by a text filter.

## The forms (corpus syntax; new forms planned, not grammar yet)

```beaml
// planned (fates-a): N9, the stricter Amount gets its next TYPE VERSION and a fate
type Amount v2 {
  value: String
  currency: String
}
fn Amount value: String, currency: String -> Amount ! BadAmount
fn Amount "0",           _                -> Amount ! BadAmount = BadAmount {}
fn Amount _,             ""               -> Amount ! BadAmount = BadAmount {}
fn Amount value,         currency         -> Amount ! BadAmount = Amount { value: value, currency: currency }
migrate Amount v1 -> v2 { quarantine value }
```

```beaml
// planned (fates-a): N9b, the literal "app" leaves Channel; stored values map on purpose
enum Channel v2 {
  Web = "web"
  Mobile = "mobile"
  Unknown(String)
}
migrate Channel v1 -> v2 { map "app" -> Mobile }
```

```beaml
// planned (fates-a): the field-qualified form, when the TYPE owns the enum field
migrate Order v2 -> v3 { map channel "app" -> Mobile }
```

```beaml
// planned (fates-a parses, the checker rejects until fates-b)
migrate Payment v3 -> v4 { redact card_holder }
migrate Payment v4 -> v5 { retire amount keep 30 days }
```

## Step a1: parse, check, `--stored`, DL-155 gate

### Parser (`Parser::change`, top-level `enum`)

- New `Change` variants: `Quarantine(field)`, `Retire(field, days)`, `Redact(field)`, `Map(Option<field>, old, variant)`.
  `map` takes an optional field word, then a Text token, `->`, a constructor word. A payload (`V(...)`) is a parse error (QF-6 A).
- `enum E vN { … }`: the VERSION MARK as on `type` (DL-072, DL-074 texts reused).
- Comma rule unchanged (K9, K10).

### Checker (`derive_versions` and a new `fate_lines` check)

- A step with fate lines only is valid (PF-05). The "needs at least one" text names the fate forms too.
- `migrate E vN -> vM` for an enum: the chain rules (no gaps, start ≥ v1, mark agrees) apply; only bare `map` lines are allowed
  in it; a field-qualified line, `rename`, `add`, `drop` give an error (PF-06).
- Field-qualified lines need a field of the newest TYPE VERSION (PF-07). Errors, one each (texts in decisions.md PF-08):
  unknown field; `quarantine` on a field that has no rule (no constructor TYPE, no literal enum); `map` on a field that is no
  literal enum field; `map` target not a variant of the enum; target with a payload; enum with an ENUM CONSTRUCTOR (`fn E`, D041);
  `"old"` is a current literal of the enum (a swap, DL-140, fates-b, QF-8); bare `map` outside an enum step; two fate lines on one
  field in one step; a fate line in a step that is not the last step of its chain (PF-10); `redact`, `retire` (PF-09).
- `quarantine f` inside `migrate T vN -> vM` of a constructor TYPE `T` (the `Amount` form): `f` must be a parameter of the
  signature line of `fn T`; one `quarantine` line per constructor TYPE (QF-3 A, PF-11).

### `--stored` (`check_stored`, `value_checks`)

- DL-102 constructor failure of TYPE `T`: if the last step of `T`'s chain has `quarantine`, the value is quarantined, not a hit.
  This holds at any depth (`Order.amount`) and in every stream: rows, RESPONSE RECORDS, ENTRY RECORDS (DL-134, DL-137, PF-12).
- A failure of the owner form (`quarantine amount` in `migrate Order …`) is QF-3 C: not built.
- DL-122 lost literal of enum `E` with value `"old"` (not in `unknown_fields`, DL-142): a bare `map "old" -> V` in `E`'s last
  step, or a qualified `map f "old" -> V` in the owner's chain, makes it a mapped value, not a hit.
- New lines on stderr, printed only when the count is above 0, before the `rows:` line (PF-13). They name source text, never a
  stored value or row id (DL-124):

```
fate: 1 stored ROW of table records quarantined by migrate Amount v1 -> v2 (quarantine value)
fate: 2 stored RESPONSE RECORDS of operation orders.list quarantined by migrate Amount v1 -> v2 (quarantine value)
fate: 1 stored ROW of table records mapped by migrate Channel v1 -> v2 (map "app" -> Mobile)
```

- The `rows: N rows, K checked, M not decodable` line keeps its form; a quarantined row counts as checked (PF-14). With DL-150
  later, a quarantined row is never "not decodable" (they are told apart by the rule that failed and the declared line).

### DL-155 gate (help texts only; the block conditions exist)

- **[Verified]** Today a change without affected stored values does not block, and a change with affected values blocks. The gate
  adds the exit and the help, not a new condition.
- Help, DL-102 (QF-5 A default). `<param>` is the first parameter with a literal pattern in the failing clause, else the first:

```
  help: declare the next TYPE VERSION and a fate (DL-155): type Amount v2 and migrate Amount v1 -> v2 { quarantine value }
```

- Help, DL-122. The old String is a stored value and is never printed (DL-124), so it stays a placeholder:

```
  help: declare the next TYPE VERSION and a fate (DL-155): enum Channel v2 and migrate Channel v1 -> v2 { map "<old literal>" -> <Variant> }
```

- `vN` is the newest TYPE VERSION of the TYPE or enum, `vN+1` the next. A TYPE with no mark is v1 (DL-155).
- ENTRY RECORD help (D6B-130) names the same nested form, because the input TYPE itself still cannot migrate.
- The QM4-3 help that still names D6B-39 for an enum field is replaced by the DL-122 help above (PF-15).

## Step a2: generated Elixir

Only TYPES and enums with a fate line change their generated bytes (PF-16, the PM4-06 rule). Every other source keeps its bytes.

- **`map`, bare form (QF-2 A):** the literal function of `E` gets one more clause, `"old"` → `V`, for decode only. The encode of
  `V` writes V's own literal. Live input and stored values read the same (an alias), so no per-value version is needed.
- **`map`, qualified form:** runs in the chain step `vN -> vM` on the raw value, before the literal map (DL-152 order). Rows of
  vM and newer are not touched.
- **Quarantine, rows (QF-1 A):** the row decode returns `{:error, "quarantined"}` when the only failure is the constructor of a
  TYPE with a `quarantine` line. `rows_<t>` skips such a row and counts it; any other failure still fails the list (QDB-4).
  `db.get` of a quarantined row: `rejected` / `quarantined` (fifth reason value, QF-1 needs the OWNER before a2 GREEN, DL-139).
  The count goes to a span attribute `quarantined` on the db span, never into the value.
- **Quarantine, REPLAY RUN:** a RESPONSE RECORD or ENTRY RECORD whose decoded value hits a quarantined constructor returns
  `{:error, :quarantined}` from `Replay.run`; the flow does not run (DL-102, DL-125). A list record with one such item is
  quarantined whole (PF-17).
- The http EFFECT live decode: a live body that fails the constructor is still `rejected` / `constructor` (it is not stored data).

## Step a3: EXPERIMENT 0005

- `variants/stricter/orders.beaml` becomes the first form above (QF-3 A). N8 keeps its own copy of the old stricter source as
  `variants/stricter_v1/` (no mark, no step) so N8 and N8b still prove the block (PF-18).
- New `variants/channel_v2/orders.beaml`: the enum form above; `PlaceForm`, `Order` unchanged.
- `fate_test.exs` N9: place `order-zero` and one good order; `live_build("stricter", "n9")` exits 0, stderr has the quarantine
  `fate:` line and no stored value; a host copy built from that module lists only the good order through `Orders.ui_orders/1`;
  the row stays in `records` (no delete). N9b: a v1 row with `"app"` lists as `Mobile`; a form submit with `"tv"` stays
  `Unknown("tv")`. The header comment and the skip tag go; `run.py` `BLOCKED` becomes empty, EXPECTED gains N9b.
- The build report (`gen-stricter.stderr` in the run directory) holds the `fate:` line; `run.py` asserts it.

## Step a4: `fmt` and tree-sitter

- `fmt`: a MIGRATE STEP body follows the DL-148 body rule: zero or one line stays on one line; two or more go one per line, two
  spaces in, comma kept at the line end, `}` alone (PF-19, QF-7 covers the spelling, not the layout). A body with a comment stays.
  An `enum E vN` mark stays (DL-104).
- Grammar: `quarantine_operation`, `retire_operation`, `redact_operation`, `map_operation` in `_migrate_operation`;
  `optional(field("version", $.version))` on `enum_declaration`. Highlights: `quarantine`, `redact`, `map` as `@keyword`
  (`retire keep days` exist). Corpus file `test/corpus/fates.txt`. Rebuild `grammars/beaml.wasm` (README steps).
- **[Unknown]** Zed itself is not checked (README limit); `tree-sitter test --wasm --rebuild` and `parse -q` are.

## RED tests

`tests/slice6_fates_test.py` (new step `slice6-fates` in 0004 `run.py`, DL-147). Sources inline or under `slice6/db/fates/`
(db sources only, PF-20). Each test fails today for the stated reason.

| ID | Name | What it proves | Fails today because |
|---|---|---|---|
| F1 | `test_F1_quarantine_line_builds` | `type Amount v2` + `migrate Amount v1 -> v2 { quarantine value }` builds | `unsupported migrate step: quarantine` |
| F2 | `test_F2_enum_version_and_bare_map_build` | `enum Channel v2` + `migrate Channel v1 -> v2 { map "app" -> Mobile }` builds | enum takes no mark |
| F3 | `test_F3_qualified_map_builds` | `migrate Order v2 -> v3 { map channel "app" -> Mobile }` builds | unsupported step `map` |
| F4 | `test_F4_fate_only_step_is_valid` | a step without rename/add/drop is valid | "needs at least one" |
| F5 | `test_F5_rejects` (subTests, one per PF-08 text) | each wrong form gives its text, exit 1 | wrong text (parse error) |
| F6 | `test_F6_redact_and_retire_parse_and_wait` | both parse; the checker gives the PF-09 text | parse error |
| S1 | `test_S1_quarantine_lifts_the_constructor_block_over_rows` | the N18 row with `"0"`: exit 0, one `fate:` line, `rows: 2 rows, 2 checked, 0 not decodable` | parse error |
| S1b | `test_S1b_control_without_the_line_blocks_with_the_version_help` | DL-102 block, help names `type Amount v2` and `quarantine value` | old help |
| S1c | `test_S1c_quarantine_over_response_records` | a list RESPONSE RECORD with a failing item: exit 0, `fate:` line counts records | parse error |
| S1d | `test_S1d_quarantine_over_entry_records` | an ENTRY RECORD of `ui.place` with `"0"`: exit 0, counted | parse error |
| S1e | `test_S1e_line_lifts_only_its_type` | a row with two stricter constructor TYPES, only `Amount` has `quarantine value`: the other still blocks | parse error |
| S2 | `test_S2_map_lifts_the_lost_literal_block` | a row with `"app"`, App removed: exit 0, `mapped` line | parse error |
| S2b | `test_S2b_control_without_map_blocks_with_the_version_help` | DL-122 block, placeholder help, no stored String | old help |
| S2c | `test_S2c_kept_value_is_neither_mapped_nor_blocked` | `"app"` in `unknown_fields`: no block, no `mapped` count | parse error |
| S3 | `test_S3_gate_without_affected_values_is_free` | stricter rule, all rows pass, no mark: exit 0 (control, passes today) | (guard) |
| S3b | `test_S3b_gate_mark_without_fate_still_blocks` | `type Amount v2` and no step: the DL-102 block holds | (guard, passes today) |
| S4 | `test_S4_no_stored_value_in_any_text` | no `fate:` or help line holds a stored String or row id | parse error |
| R1 | `test_R1_db_list_skips_a_quarantined_row` | runtime: `list` gives the good row, span attribute `quarantined: 1` | step a2 |
| R2 | `test_R2_db_get_of_a_quarantined_row` | `rejected` / `quarantined` record (after QF-1) | step a2 |
| R3 | `test_R3_bare_map_decodes_old_literal` | `"app"` row → `Mobile`; encode writes `"mobile"`; `"tv"` → `Unknown` | step a2 |
| R4 | `test_R4_qualified_map_runs_in_the_chain_step` | v2 row `"app"` → `Mobile`; a v3 row is not mapped | step a2 |
| R5 | `test_R5_replay_skips_a_quarantined_record` | `Replay.run` gives `{:error, :quarantined}`; the flow does not run | step a2 |
| R6 | `test_R6_replay_applies_map` | a recorded list with `"app"` replays as `Mobile` | step a2 |
| R7 | `test_R7_sources_without_fate_lines_keep_their_bytes` | every tracked source compiles byte-equal to `5e05b5f3` (guard, passes before and after) | (guard) |
| N9 | 0005 `fate_test.exs` | live: stricter v2 builds, list omits `order-zero`, row stays | skip tag, blocked |
| N9b | 0005 `fate_test.exs` | live: v1 `"app"` row lists as `Mobile`; `"tv"` stays `Unknown` | no variant |
| T1 | `slice6_fmt_test.py` `test_T1_migrate_body_one_line_per_change` | two or more lines go one per line, commas kept | fmt leaves the body |
| T2 | `test_T2_one_fate_line_stays_on_one_line`, `test_T2b_enum_mark_kept` | single line and mark kept; idempotent | parse error |
| G1 | `tree-sitter test` corpus `fates.txt` | the five forms and `enum E v2` parse to named nodes, no `ERROR` | no rule |

**[Proposal]** RED depth probe (as in m4-lift): a scratch build where only the parser accepts the words and every check is a
no-op must fail S1b, S2b, S2c, F5 and R1. Otherwise the tests could pass on parsing alone.

## Byte-pin impact

**[Inference]** No pin site moves in fates-a, if PF-16 and PF-20 hold:

| Site | Kind | Moves? | Reason |
|---|---|---|---|
| `tests/slice6_pipe_test.py` `EFFECT_OUTPUTS` | digest | no | its sources have no fate line |
| `tests/slice6_host_struct_test.py` `BYTE_GUARD` | digest | no | same |
| `slice6/effect-reach/byte-guard.json` | digest | no | same |
| `tests/slice5_syntax_test.py` `PIN` | hash | no | new fixtures are db sources (filtered) or inline |
| `tests/slice6_entry_test.py` `BASE` | hash | no | same; help texts show only with stored hits, the guard compiles with an empty snapshot |
| `tests/slice6_multi_test.py` `BASE` | hash | no | same |
| also `tests/slice6_db_test.py` `P4_BASE` | hash | no | new http fate sources stay inline (a tracked one would fail to compile at `P4_BASE`) |

- If GREEN finds that a shared helper must change for every source (for example `rows_<t>` gets the skip branch for all
  TYPES), PF-16 is broken: the three digest pins move inside that GREEN with the hunk list, and the hash pins move in the
  commit right after (RV3-14). The GREEN worker reports this before it re-pins.
- Help text changes move no pin but change eight test constants (list above); a1 GREEN updates them.
- `fmt` (a4): the slice 3 to 5 sources with two changes on one line are unformatted on purpose (DL-148 P1) and never run
  through `fmt` in a test; `forms.beaml` is a highlight input, not a `fmt` input. No fixture moves.

## Acceptance criteria

- fates-a steps a1 to a4 each have genuine RED, the main agent RED review and a fresh RED review, then GREEN.
- Full 0004 `run.py` status `pass` with the new step; 0001 `cargo fmt --check`, `clippy -D warnings`, `cargo test` pass.
- 0005 `run.py run`: every N-TEST passes, N9 and N9b included; `BLOCKED` is empty; the run directory keeps `gen-stricter.stderr`.
- `tree-sitter test --wasm --rebuild` and `parse -q` over the new fixtures and the 0005 variants: no `ERROR`.
- No pin moved, or the moves follow the two-commit rule with a diff proof.
- No stored value, row id or secret in any compiler text, event or log (S4, 0005 N12).
- A PASS does not establish production readiness.

## Risks

- **[Inference]** QF-2 A (alias) changes the live decode of outside data: a provider that still sends `"app"` now gets `Mobile`.
  This is the point of the line, but it means a bare `map` line can never leave at SQUASH while senders send `"old"`.
- **[Inference]** In-place gap: once `quarantine value` exists, a further stricter rule on the newest version without a new
  version is covered by the old line silently. The build cannot see the old rule (same cause as DL-140 detection, QF-8).
  PF-10 only forces a fate line into the last step. Smallest test: fates-b, a third clause on `Amount v2` with no `v3`.
- **[Inference]** QF-1 adds a fifth reason value to the db call record. DL-139 keeps record formats out of built defaults, so
  a2 GREEN waits for the OWNER answer. a1 can run first.
- **[Verified]** The 0005 N9 test name and comment say `migrate Order v1 -> v2 { quarantine amount }` (QF-3 C); DL-155 and this
  task say `Amount v2` / `quarantine value` (QF-3 A). The plan builds A and renames the comment.
- **[Inference]** One quarantine line per constructor TYPE (PF-11) cannot tell two clauses apart. Enough for N9.
- **[Inference]** Help text churn touches eight test files; a missed one fails only in the full run (lesson of the PIN misses).

## Exclusions (fates-a)

- `redact f` semantics, DL-111 exit, eager removal, DL-116 stays as is (M3: `redact` makes a field absent and never skips a rule).
- `retire f keep N days` semantics (M5 parked; QF-4). The top-level RETIRE LINE is unchanged.
- DL-140 swap detection and the previous rule or literal table (QF-8). A `map` onto a current literal is an error in fates-a.
- Live `--stored` (DL-151): fates-a reads the ROW SNAPSHOT and `responses.jsonl`.
- DL-150 (block on a not-decodable row), D035 (digest half), DL-154 projection, D040.
- Lifting a quarantine by a later step, dead-line notes for fate lines, SQUASH text (DL-056, DL-155 "the build says when").
- Fate lines on nested paths (`quarantine amount.value`), a fate line on a top-level input TYPE (D6B-130 stays).
- D042 lazy recheck. It would need: a fate line such as `recheck f` (sketch), a typed outcome visible in signatures (D042 A,
  `Stale(T)` or `T v1 | T v2`), a list of every place the outcome can reach, the host handling each, and the redacted value
  present at the host. None of that is in fates-a.
- D041 (ENUM CONSTRUCTOR removal) is not decided. `map` works on literal enums only; an enum with `fn E` gets an error. Under
  D041 A or B nothing here changes; under C a later step adds `map` over constructor enums.

## Docs list (after TEST, fresh docs worker)

- 0004 README: new section "FATE slice (fates-a)", the help texts, the `fate:` lines, limits; the M4 section "What still waits".
- 0005 README: N9 and N9b results, Limits line, Prerequisites P6, Exclusions.
- [migrate-fates](../../../../../wiki/concepts/migrate-fates.md): built vs planned per operation, the answered open questions.
- GLOSSARY: QUARANTINED RECORD covers rows; the enum VERSION MARK.
- Decision log: PF entries that the OWNER signs or changes; QF answers. Register: M3, M5, D036, D041, D042 next checks; D043 done.
- `wiki/planning/research-and-development.md` register line, `wiki/log.md` entry, `integrations/zed-beaml/README.md` new nodes.

## Plan repair after plan check (2026-11-08)

**[Proposal]** Applies [plan-review.md](plan-review.md) repairs 1 to 9 and the main-agent rulings in [decisions.md](decisions.md)
("Rulings by the main agent after the plan check"). This section wins over the text above where they differ.
By: Opus (RED fates-a1), from the rulings By: Fable and DL-157 By: 13ue.

- **Line form A (QF-3 ruled).** A stricter constructor rule gets the next TYPE VERSION of the constructor TYPE and a
  quarantine line in its own step: `type Amount v2 { … }` + `migrate Amount v1 -> v2 { quarantine value }`. The owner
  form `migrate Order … { quarantine amount }` is an error whose text points to the constructor TYPE step (F5).
- **Enum form (QF-7 ruled).** `enum Channel v2 { … }` + `migrate Channel v1 -> v2 { map "app" -> Mobile }`. The
  field-qualified form `map channel "app" -> Mobile` stands in the last step of the owner TYPE chain.
- **a1 exits 1 when a fate line is hit (O2, repair 3 b).** a1 lifts the DL-102 and DL-122 block, prints the `fate:` line,
  and then stops with one error line per fate kind until a2 builds the run-time side:
  `error: a quarantine line is hit, but quarantine at run time is not built yet (fates-a2, DL-157)` and
  `error: a map line is hit, but map at run time is not built yet (fates-a2)`. A fate line that no stored value hits
  builds (exit 0). a2 removes both texts and its RED changes S1, S1c, S1d, S2 to exit 0.
- **DEAD LINE (O1, repair 2).** A fate-only MIGRATE STEP is never a DEAD LINE, and `--remove-dead
  --assume-complete` keeps it (RED F7, F7b). Other nested steps keep the W2 rule (setup control in F7).
- **Pins and help (O3, repair 4).** The pin list gains `tests/record_v3_test.py` V18b (`P2_BASE`): four of its five pairs
  change their help line in a1 GREEN (`decode-ctor/stored-fail`, `decode-ctor/stored-nomatch`,
  `stored-elixir/nested-fail`, `stored-elixir/pipe-fail`); `decode/stored-fail` (no variant, a shape fault) keeps its
  text. V18b is re-pinned in the a1 GREEN with the hunk list (two-commit rule). The help list gains
  `tests/slice6_m4_test.py` `rename_text`: it stays as is in a1, because `rename`, `add`, `drop` on an enum or constructor
  field still wait (QM4-4 open); only its imported `LITERAL_HELP` changes.
- **Help per DL-102 site (repair 5).** The DL-155 help stands only where a fates-a line lifts the block:
  - a failed constructor rule of a constructor TYPE `C` (rows, RESPONSE RECORDS, ENTRY RECORDS):
    `  help: declare the next TYPE VERSION and a fate (DL-155): type C vN+1 and migrate C vN -> vN+1 { quarantine p }`
    with `p` the first parameter with a literal pattern in the failing clause (PF-21), else the first parameter;
  - a lost ENUM LITERAL of `E`: `  help: declare the next TYPE VERSION and a fate (DL-155): enum E vN+1 and migrate E
    vN -> vN+1 { map "<old literal>" -> <Variant> }`;
  - a value that matches no signature of an ENUM CONSTRUCTOR `E` (D041 open, PF-06, PF-23 give no exit):
    `  help: no fate line covers an ENUM CONSTRUCTOR yet (D041 open); restore a signature of fn E that reads these records`;
  - a value that matches no signature of a constructor TYPE `C` (a decode fault, never quarantined):
    `  help: no fate line covers a value that matches no signature of C (a decode fault); restore a signature of fn C that reads these records`;
  - "no String value" and "no variant" (shape faults, DL-150 territory) keep today's DL-102 help (guard S5).
  `vN` is the newest TYPE VERSION; a TYPE or enum with a mark and no step into it is at the mark (S3: `type Amount v2`
  alone gives `type Amount v3 and migrate Amount v2 -> v3`).
- **PF-16 reworded (repair 6).** "Only sources with a fate line change their generated bytes." R7 excludes exactly those.
- **N9 evidence (repair 7).** a3 reads `<run>/n-tests/<n>-n9/build.stderr`, not `gen-stricter.stderr`; the `EXPECTED`
  name and the N9 test name change together.
- **Fixtures (repair 8, PF-20).** a1 fixtures stand under `slice6/db/fates/`, each holds a db EFFECT line (N13 filter
  `= *db\.\w+\(|: *\[`); wrong forms stay inline in the test (never under `bad/` or `slice6/db/bad/`).
- **Missing RED cases (repair 9)** are in the a1 RED: see [red-plan.md](red-plan.md). Cases for a2 stay there: R1b,
  R1c, R5b, R8.
- **DL-140 swap detection** stays out of a1 (a `map` onto a current literal is an error). The scope cut of DL-156 is an
  open OWNER question (decisions.md, "Open OWNER lines").

### What a3 (0005) needs from a1

- `variants/stricter/orders.beaml` becomes the form of `slice6/db/fates/amount_v2/orders.beaml` (`type Amount v2` +
  `migrate Amount v1 -> v2 { quarantine value }`), a new `variants/stricter_v1/` holds today's stricter source
  (the same text as `slice6/db/fates/stricter_v1/`) so N8 and N8b still prove the block.
- `variants/channel_v2/` takes the form of `slice6/db/fates/channel_v2/`.
- N9 needs a1 and a2 GREEN: with a1 alone the N9 build exits 1 with the quarantine "not built yet" line, on purpose.
