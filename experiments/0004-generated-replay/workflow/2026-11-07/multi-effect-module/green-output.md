# GREEN output: slice 6e, several EFFECTS and ENTRY LINES per source, module named from the source

**[Observed]** GREEN phase, 2026-11-08. Base: HEAD b1879fa8 at start; HEAD 158ba4e1 at end (P4b RED commit by the main agent during this phase). No commit by this worker.
Specification: `tests/slice6_multi_test.py` (14 tests). Plan: [plan.md](plan.md), decisions [decisions.md](decisions.md), RED [red-output.md](red-output.md), review [red-review.md](red-review.md) (M1, M2).
By: Opus (GREEN multi-effect) for every finding and decision in this file.

## Diff summary

`experiments/0001-syntax-to-beam/src/main.rs` (+195 / -37 lines):

- **Checks (D6B-197).** The `slice 1 supports one effect` check and the D6B-147 `index > 0` check are gone. `validate` adds the Q6E-4 A check: two EFFECTS with one flow give `error: fn <f> calls the effects <a> and <b>; slice 6e replays a flow with one effect`. `entries` adds the D6B-201 check: two ENTRY LINES with one operation give `duplicate name: ui_<op>`.
- **Module name (Q6E-1 C, D6B-203).** New `Checker.module` (default `BeamlSpike`). `build_with_refusals` sets it from the stem for a source with an ENTRY LINE (`module_name_from_stem`, one capital per `_` segment), after the existing stem check. A reserved name gives `error: the source file name <stem> gives the module <M>, which the generated code calls; rename the file`. The `emit` header writes `defmodule <module> do`. `Rejected` stays nested, so it is `<Module>.Rejected` (Q6E-2 A, no extra code).
- **Shared parts once (D6B-198).** `written_once` runs over the `emit` text: a module-level item (def clause, nested module, comment) that stands two times is written once, at its first place. A one-EFFECT source repeats no item, so its bytes stay (four pin sites, N13).
- **Replay (D6B-199, Q6E-3 A).** `Replay` moves from `emit_effect` to `emit_replay`, after the EFFECT loop (the same place for one EFFECT). `emit_replay_clauses` gives `record` and `run` per EFFECT. With two or more EFFECTS: `record(operation, request, status, bytes)`, `run(operation, a0, trace_id, records)`, a last `run/4` clause `{:error, :operation_mismatch}`; the live call passes the operation (`replay_op`). With one EFFECT: the slice 6 form, byte-equal.
- **Entry REPLAY RUN (D6B-200).** `emit_replay_entry` covers every ENTRY LINE that reaches an EFFECT: `entry_record(operation, bytes, decoded)` per line, `entry(%{"operation" => op} = record, records)` per line, a last `entry/2` clause `{:error, :operation_mismatch}`. With two or more EFFECTS the clause calls `run(<effect operation>, value, ...)`.
- **DRIVER (D6B-204).** The stdin JSON has `"name"` beside `"module"`; the driver uses `Module.concat([name])` and matches `[^name, short]`. Both `check_stored` and `check_entries` send `self.module`.
- **Unit test.** `module_name_from_stem` (orders, order_flow, v2_orders).
- `tests/cli.rs`: no change needed (`arms/gen/orders.beaml` has no ENTRY LINE, so `defmodule BeamlSpike do` stays).

Other files:

| File | Change |
|---|---|
| `tests/slice6_entry_test.py` | `BeamlSpike.` → `Echo.` / `Count.` / `Orders.` by fixture, `Case.` for the O1 text source (stem `case`); `built` and `runtime` take `module`; HELPERS build `Rejected` and `Amount` from `mod`; `two_entries` leaves the reject table; new `test_n1c_two_entry_lines_to_one_flow_build`; H1/H2 `UNDEFINED` = the prefix `Orders.ui_place/1 is undefined` (without its ENTRY LINE the source is `BeamlSpike`, so Elixir says "module Orders is not available"); docstring |
| `slice6/entry/two_entries.beaml` | moved from `bad/` (the main agent's commit 158ba4e1 took the staged move); comment line 1 now says it compiles (D6B-207) |
| `tests/record_v3_test.py` | V8: `built(ORDERS, EMPTY, "BeamlSpike")` (`arms/gen` has no ENTRY LINE); V18 not edited (see below) |
| `tests/redteam_c1_test.py` | C1g driver stdin gets `"name": "BeamlSpike"` (D6B-204) |
| `run.py` | `SLICE_TESTS` adds `slice6_multi`, `slice6_db`, `slice6_db_stored`, `record_v3` (D6B-190 explicit list; `slice6_db_stored_test.py` appeared in 158ba4e1 during this phase) |

## Changed generated sources (against ca09d361)

**[Observed]** Every tracked source without an ENTRY LINE is byte-equal (multi N13, 6d N13, the four pin sites). The ENTRY LINE sources change:

| Source | Exit | Changed lines |
|---|---|---|
| `slice6/entry/echo.beaml`, `count.beaml` | 0 → 0 | the module line only (`Echo`, `Count`) |
| `slice6/entry/orders.beaml`, `slice6/multi/copy/orders.beaml`, `slice6/multi/no_hold/orders.beaml`, `slice6/multi/no_hold_retired/orders.beaml` | 0 → 0 | the module line (`Orders`), `entry_record/3` (operation first), the `entry/2` clause on the operation plus the last clause, and the `entry_record` call in `ui_place` (D6B-200) |
| `slice6/entry/two_entries.beaml` | 1 → 0 | was the D6B-147 reject; now builds `TwoEntries` |
| `slice6/multi/orders.beaml` | 1 → 0 | was `slice 1 supports one effect`; now builds `Orders` |
| `slice6/multi/bad/enum.beaml` | 0 → 1 | the D6B-203 text |
| `slice6/multi/bad/same_entry_operation.beaml` | 1 → 1 | D6B-147 text → `duplicate name: ui_place` |
| `slice6/multi/bad/two_effects_in_one_pipe.beaml` | 1 → 1 | `slice 1 supports one effect` → the Q6E-4 A text |

So the change is not "the module line only" for the `orders` ENTRY LINE sources: D6B-200 also moves the `entry` lines. This was planned (D6B-200: ENTRY LINE sources are not pinned).

## Test results (working tree at the end of GREEN)

| Check | Result |
|---|---|
| `cargo fmt --check` | ok |
| `cargo clippy --offline --all-targets -- -D warnings` | ok |
| `cargo test --offline --no-fail-fast` | 22 unit + 14 cli, all pass |
| `slice6_multi_test.py` | 14 tests OK (N13 against ca09d361 passes: it skips ENTRY LINE sources) |
| `slice6_entry_test.py` | 20 tests OK (N13 passes for the same reason) |
| `slice5_syntax_test.py` (PIN) | 60 OK |
| `slice6_pipe_test.py` (EFFECT_OUTPUTS) | 12 OK |
| `slice6_host_struct_test.py` (BYTE_GUARD) | 3 OK |
| `slice6_effect_reach_test.py` (byte-guard.json) | 8 OK |
| `slice6_constructor` 25, `decode_ctor` 8, `decode` 10, `enum` 20, `failure` 22, `fmt` 25, `int` 16, `record` 5, `redacted_failure` 8, `redacted` 20, `stored_elixir` 15, `struct_order` 3 | all OK |
| `redteam_b3` 1, `redteam_c1` 8, `redteam_c3` 5 | all OK |
| `drift_test.py` | 7 OK |
| `record_v3_test.py` | 26 tests, 11 failures, all V18 subtests (below) |
| `slice6_db_test.py` | 51 failures: the 40 P4a RED failures (same as at b1879fa8) plus 11 `test_N13_sources_without_a_db_effect_keep_their_bytes` subtests on the ENTRY LINE sources above (P4_BASE = ca09d361) |
| `slice6_db_stored_test.py` | 43 failures, 3 skipped: equal to the b1879fa8 compiler (P4b RED) |
| `elixirc --warnings-as-errors` on `two_entries.beaml` output | exit 0, no warning |

Not run: the full `run.py` (as told).

## Base pins for the main agent (M1)

- `slice6_db_test.py` `P4_BASE`: fails on the 11 ENTRY LINE sources until it points at the GREEN commit.
- `slice6_multi_test.py` and `slice6_entry_test.py` `BASE`: they pass at ca09d361 because both N13 filters skip ENTRY LINE sources. Moving them to the GREEN commit is optional; it must not move to a commit after GREEN.
- `record_v3_test.py` V18: fails on the same 11 sources. V18 compares against `P2_BASE` 545dded0 and allows hunks only in the two P2 writers. Hunks per source: the table above (module line; for the `orders` sources also `entry_record`, `entry`, `ui_place`; exit/stderr changes for the five reject or former-reject files). Options: filter ENTRY LINE sources in V18 (G6D-01 regex), or retire V18 after P2 TEST.

## Limits

- **[Inference]** `written_once` keys on text. Two defs with one name and other text still reach elixirc; N2 catches that for the multi fixture only.
- **[Inference]** `Replay` has two shapes (one EFFECT; two or more). `ponytail:` comment at `emit_replay`.
- **[Observed]** The staged `git mv` of `two_entries.beaml` went into the main agent's commit 158ba4e1 (P4b RED). The comment edit in that file is still uncommitted.
- **[Unknown]** Elixir behaviour when two generated sources with one stem meet in one host build (plan exclusion).

## Decisions

**Repair**
→ Text-keyed dedupe (`written_once`) statt one `once` call per shared def site, weil one pass covers every shared item (Http, BeamlFailure, failure structs, decode helpers, `__beaml_keys__`, entry reject trio) and cannot miss one site. Commits us to: emitted module-level items keep a stable 2-space layout. → By: Opus (GREEN multi-effect) · Repair
→ `Checker.module` field set in `build_with_refusals` statt a module argument to `emit`, `check_stored` and `check_entries`, weil one value serves the header and the DRIVER input. → By: Opus (GREEN multi-effect) · Repair
→ `two_entries.beaml` moved to `slice6/entry/` with a new compile test (n1c) statt deleted, weil it is the D6B-207 control (two ENTRY LINES to one flow). → By: Opus (GREEN multi-effect) · Repair
→ H1/H2 `UNDEFINED` = the common prefix statt two texts, weil Q6E-1 C renames the module when the last ENTRY LINE goes; H1 stays stricter. → By: Opus (GREEN multi-effect) · Repair

**Undo**
→ `slice6_db_stored` added to `run.py` beside the three told files, weil C4 globs every `slice6_*_test.py`. → By: Opus (GREEN multi-effect) · Undo
→ O1 text source keeps the stem `case`, so its module is `Case`. → By: Opus (GREEN multi-effect) · Undo
→ V18 not edited; hunks reported for the pin commit. → By: Opus (GREEN multi-effect) · Undo
→ `cli.rs` not edited (no ENTRY LINE in its fixture). → By: Opus (GREEN multi-effect) · Undo

**Migrate (defaults taken, open)**
→ Q6E-1 C, Q6E-2 A, Q6E-3 A (incl. `a0` = decoded input TYPE, M2), Q6E-4 A as built. → By: Opus (GREEN multi-effect, default, open)
