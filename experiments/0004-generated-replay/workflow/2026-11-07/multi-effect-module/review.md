# TEST and review: several EFFECTS and ENTRY LINES per source, module name (0005 P3, P5)

**[Observed]** TEST plus normal review, 2026-11-08, HEAD b3e75b6e (GREEN ce190054, pin commit b3e75b6e). Fresh-context reviewer, no worker context reused. No code changed, no commit.
By: Opus (TEST v3/multi).

## Verdict: PASS

No critical or high objection. Two medium notes (O1, O2).

## Checks

Same run as the [record-v3 review](../record-format-v3/review.md#checks-shared-with-the-multi-effect-review): full 0004 `run.py` 976.6 s, status `fail` only from `slice6-db` (40 failures) and `slice6-db-stored` (43 failures, 3 skipped), both equal to their RED records; `slice6-multi`, `slice6-entry`, `record-v3`, `redteam-c1`, `redteam-c3` and every other step pass. 0001 `run.py`, fmt, clippy, cargo test (22 + 14), wiki lint, tree-sitter over `slice6/multi/` and `two_entries.beaml`: pass. Result dir `results/20261107T230714580577Z` kept.

## Probes (own scratch source `shop_flow.beaml`)

Two http EFFECTS with one output TYPE (`Payment` holds `Amount`) and one failure TYPE, two ENTRY LINES.

| Probe | Result |
|---|---|
| build | exit 0, `defmodule ShopFlow do`; `Amount`, `PaymentError`, `BeamlFailure`, `Http`, `Rejected`, `Replay` each once |
| `elixirc --warnings-as-errors` with the N2 stubs | exit 0, no warning text |
| exports | `ShopFlow.ui_place/1`, `ui_hold/1`; `Replay`: `entry/2`, `entry_record/3`, `record/4`, `run/4` |
| live place and hold (two TCP stubs) | `{:ok, _}` each; RESPONSE operations `payments.authorize`, `stock.reserve`; ENTRY operations `ui.place`, `ui.hold` |
| `Replay.run(op, decoded, trace, records)` | equals the live value per operation; other flow on a trace and an unknown operation give `{:error, :operation_mismatch}` |
| `Replay.entry/2` per ENTRY RECORD | equals the live value |
| bad amount / bad keys | `%ShopFlow.Rejected{reason: "constructor"}` (ENTRY RECORD rejected, no RESPONSE RECORD) / `reason: "decode"` |
| one flow calling two EFFECTS (with and without ENTRY LINE) | exit 1, `error: fn place calls the effects payments.authorize and stock.reserve; slice 6e replays a flow with one effect` |
| two EFFECT lines with one operation | exit 1, `duplicate name: payments_authorize` |
| two ENTRY LINES with one operation | exit 1, `duplicate name: ui_place` |
| stems `enum`, `string`, `kernel`, `map`, `probe_support`, `open_telemetry`, `argument_error` | exit 1, the D6B-203 text |
| stem `system` | **exit 0**, `defmodule System do`; host `elixirc --warnings-as-errors`: `redefining module System`, exit 1 (O1) |
| stems `replay`, `http`, `rejected`, `amount`, `beaml_failure`, `process`, `atom`, `io` | build and elixirc exit 0 (`io` gives `Io`) |
| no ENTRY LINE, two EFFECTS | `defmodule BeamlSpike do` |
| `--stored` over one snapshot from the live run (3 entries, 3 responses, two operations each) | full source: `3 entries, 3 checked, 0 rejected at capture` (the DRIVER ran with `"name"` = `ShopFlow`); source without `stock.reserve`: the DL-040 orphan for `stock.reserve` only, count 2; with `retire stock.reserve`: the ENTRY orphan for `ui.hold`, count 2 |
| ca09d361 compiler vs HEAD over all 2092 tracked `.beaml` sources without an ENTRY LINE (G6D-01 filter), `--stored stored/empty.jsonl` | stdout, stderr and exit equal for all 2092; 33 ENTRY LINE sources skipped |

## Pin sites

- `slice5_syntax_test.py` `PIN` = ca09d361; `EFFECT_OUTPUTS`, `BYTE_GUARD`, `byte-guard.json` unchanged since ca09d361. **[Observed]**
- `slice6_entry_test.py` and `slice6_multi_test.py` `BASE` = ce190054; `slice6_db_test.py` `P4_BASE` = ce190054; the 11 db N13 failures of GREEN are gone (40 = the P4a RED count). **[Observed]**
- V18 skipped with a reason (record-v3 review). **[Inference]** With both N13 `BASE` at the GREEN commit, N13 proves nothing about this step; the 2092-source comparison above is the proof for it.

## Objections

### O1 · medium · D6B-203 misses `System`

- **Evidence.** The generated code calls `System.monotonic_time` (336 references over all tracked outputs; `Http` of every http EFFECT). `CALLED` in `main.rs` (13 names) has no `System`. `system.beaml` with an ENTRY LINE builds exit 0 and emits `defmodule System do`.
- **Consequence.** BEAML builds green; the host build redefines Elixir's `System`. With `--warnings-as-errors` the host build stops; without it the module replaces `System` in the host (wrong outcome outside BEAML). The list is hand-kept, so the next called module repeats the gap.
- **Resolving test.** Stem `system` with an ENTRY LINE gives the D6B-203 text. Stronger: every `X.` module that the emitted text calls is in the list (a test that greps the output of the multi fixture).

### O2 · medium · `run.py` cannot tell an expected RED from a regression

- **Evidence.** `run.py` sets `status` = `pass` only if every step passes; no expected-RED list. C4 (`redteam_c3_test.py`) demands every `slice6_*_test.py` in the full run, so a committed RED file turns the full status `fail`. Today the `fail` comes only from the two db RED files (counts equal to their RED records, checked by hand).
- **Consequence.** While a RED is open, `status: fail` is the normal state; a new regression in another step does not change the top status, and a regression inside a RED file is hidden by its own RED. A reader of the top line cannot see it.
- **C4 judgement.** C4 is right to force every file into the full run (DL-135, no silent files). It is missing the second half: a declared expected RED with its count.
- **Resolving test.** `run.py` gets an expected-RED table (file, failure count); a listed step with exactly that count is `red_expected`, any other count or any other failing step is `fail`; a test pins both cases.

## Dropped (low)

- `written_once` keys on text; a duplicate def with other text reaches elixirc (GREEN limit, N2 covers the fixture).
- No per-ENTRY-stream orphan in the same build as a RESPONSE orphan (first block only); DL-040 per stream, N8 pins it.

## Decisions

**Repair**
→ PASS statt BLOCK, weil O1 is caught by a host `--warnings-as-errors` build and O2 hides nothing today. → By: Opus (TEST v3/multi) · Repair
→ O1 medium statt high, weil it needs a stem that names a stdlib module. → By: Opus (TEST v3/multi) · Repair
→ O2 medium statt high, weil per-step status in `result.json` shows the cause. → By: Opus (TEST v3/multi) · Repair
→ Byte proof by own 2092-source comparison statt the N13 tests, weil N13 `BASE` equals the GREEN commit. → By: Opus (TEST v3/multi) · Repair

**Migrate (proposal, open)**
→ O2 expected-RED table in `run.py` vs. RED files out of `run.py` until GREEN (C4 change). OWNER or main agent chooses. → By: Opus (TEST v3/multi, proposal, open)

**Undo**
→ Scratch sources and outputs kept in scratch only. → By: Opus (TEST v3/multi) · Undo
