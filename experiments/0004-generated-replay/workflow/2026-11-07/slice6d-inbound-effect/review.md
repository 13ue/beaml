# TEST and review: slice 6d, the ENTRY LINE

**Verdict: BLOCK** (one high objection, O1). By: Opus (TEST slice6d/red-team), 2026-11-07, HEAD 35c7e3bf. No commit. `main.rs` not edited.

## Checks (observed)

| Check | Result | Evidence |
|---|---|---|
| `python3 run.py` (0004, 34 steps) | pass, 34 of 34; wall time 1058 s (17 min 38 s) | `results/20261107T220212948306Z/result.json` |
| `slice6-entry` step | pass, 18 tests | same run, `slice6-entry.stderr` |
| `drift` step | pass, rows equal the DRIFT pin, `repaired_all` true | `results/20261107T220254343850Z/drift.json` |
| 0001 `run.py` | pass | `experiments/0001-syntax-to-beam/results/20261107T222001827189Z/result.json` |
| `cargo fmt --check` | clean | scratch log |
| `cargo clippy --all-targets -D warnings` | clean | scratch log |
| `cargo test` | 21 + 14 passed | scratch log |
| `scripts/lint_wiki.py` | 0 errors, 85 files | scratch log |
| tree-sitter `test` (scratch copy of `integrations/zed-beaml`) | 23 of 23 | scratch log; regenerated `parser.c` equals the tracked one |
| tree-sitter `parse`, 2091 tracked `.beaml` | 146 outside `results/`: 142 parse, 4 fail; all 17 `slice6/entry` sources parse | see below |

Parse failures outside `results/`: `slice6/redacted/bad/enum_payload.beaml`, `slice6/redacted/bad/signature.beaml` (`bad/`, by design); `examples/order-flow.beaml`, `syntax-options.beaml` (old `interface` sketches, pre-slice-6, not 6d). 945 failures sit in retained `results/` copies of older syntax (historical, not checked).

## Probes (scratch, compiler built from `git archive HEAD`)

- **[Observed]** Drift rule: a different input, output, failure TYPE and a missing failure TYPE each give exit 1 with the DL-130 text. Pass.
- **[Observed]** Stored entries (DL-134, DL-138): only rejected records (one `constructor`, one `null`) give exit 0 and the count line `2 entries, 0 checked, 2 rejected at capture`. An accepted record with `value: null` or a wrong shape blocks with the DL-102 text, no crash. Pass.
- **[Observed]** Stricter constructor: 3 records block (the reject and the `null` record are skipped). Lost literal: 1 record blocks; the record kept as `Unknown` (`unknown_fields`) does not. Stored Strings in stderr: 0 of all stored values (DL-124). Pass.
- **[Observed]** RETIRE: ENTRY LINE removed, no RETIRE LINE: the DL-040 parity block, count 5. Removed plus `retire ui.place keep 30 days`: exit 0. ENTRY LINE kept plus the RETIRE LINE: "still declares effect". G6D-10 and `test_s5b` do not contradict: G6D-10 is the kept-line case, `test_s5b` the removed-line case, as for an outbound EFFECT.
- **[Observed]** Host: the generated module compiles with `elixirc --warnings-as-errors`. `ui_place/1`: good map gives the flow result with an `accepted` ENTRY RECORD; bad constructor gives `Rejected{reason: "constructor"}`; missing key, atom keys, nested atom keys and a mixed-key map give `Rejected{reason: "decode"}`; each writes one `rejected` ENTRY RECORD. No raise reaches the host.
- **[Observed]** G6D-04: a source with `payments.authorize` and an ENTRY LINE to a pure fn builds; `ui_echo/1` writes no record and `Replay.entry/2` is not exported.

## Objections

### O1 · high · A nested enum or constructor field in the input TYPE builds green and rejects every UI event

- **Evidence [Observed].** Input TYPE `PlaceOrder { order_id: String line: Line }` with `Line { channel: Channel }` (or `Line { amount: Amount }`, constructor): exit 0, elixirc clean. A valid event gives `{:error, Rejected{reason: "decode"}}` every time. A nested plain record (`Line { note: String }`) is accepted, so only the nested enum or constructor case breaks. The same TYPE as an outbound EFFECT output is a compile error (`slice 1 decodes String fields only, not PlaceOrder.line`).
- **Consequence.** The green-output limit note says "same limit as the outbound decode". That is false: outbound blocks at build time, inbound fails silently at run time with a reject that looks like a bad form. The PROTOTYPE (EXPERIMENT 0005) forms inherit it.
- **Resolving test.** One `slice6_entry_test.py` case: the nested enum source and the nested constructor source give exit 1 with a compile error that names the field (as the outbound check does); or, if decoded, the valid event gives `{:ok, ...}`. The compile error is the smaller repair.

### O2 · medium · G6D-04 is classed Undo but is an open capture-scope default

- **Evidence [Observed].** G6D-04 stands under Undo with "(default, open)". It is not in the decision log nor in decisions to be made. D6B-136 justified "no record" by the missing `Replay` module; a source with an outbound EFFECT has that module, so the reason does not hold there.
- **Consequence.** UI events of a pure target are never captured; `--stored` and the REPLAY RUN never see them. DL-138 rejected "no reject records" for the same loss of evidence. Not a DL-139 record-format item and one repair step to change, so not a hidden Migrate. **[Inference]**
- **Action.** Raise to Repair; record it in the decision log as `By: Opus (default, open)` and present it to the OWNER (DL-139 sign-off rule).

### O3 · medium · R1 still open; ENTRY stream inherits C5

- **Evidence.** R1 (a captured reject that a looser rule accepts now) stays open (G6D-13). `check_entries` does not verify `value_sha256`; `Replay.entry` rejects a bad digest. Same root cause as C2/C5 (DL-136 not yet built for any stream). **[Observed]** in code.
- **Action.** Carry R1 and C5 into the DL-136 shared "replayable record" step; one test there covers RESPONSE and ENTRY RECORDS.

## Notes outside the cap

- R2 is closed by DL-141 and DL-142 (OWNER confirmed the two keys and both lists).
- The decision log holds two entries each for DL-140 and DL-141 (stable-ID rule, AGENTS.md). The slice 6d commit cites "DL-141" for the record-format entry. A documentation worker should renumber.

## Decisions

**Repair**
→ BLOCK statt PASS, weil O1 is a green build with a silent run-time reject on every event. By: Opus (TEST slice6d/red-team)
→ G6D-04 raised Undo to Repair, weil a capture-scope change needs one repair step. By: Opus (TEST slice6d/red-team)

**Undo**
→ G6D-10 and `test_s5b` consistent, no objection. By: Opus (TEST slice6d/red-team)
→ Four parse failures outside `results/` not counted against 6d (two `bad/`, two pre-slice-6 sketches). By: Opus (TEST slice6d/red-team)
→ O3 and duplicate IDs noted, not blocking. By: Opus (TEST slice6d/red-team)

## Re-check after TEST repair

**Verdict: PASS.** By: Opus (TEST re-check slice6d), 2026-11-07, HEAD f9b9083c. One round, new evidence only. No commit. `main.rs` not edited. Compiler built in scratch from `git archive HEAD`, run with `BEAML_SPIKE`.

### Checks

| Check | Result | Label |
|---|---|---|
| O1 nested enum (`bad/nested_enum.beaml`) | exit 1, names `Line.channel`, help line | [Observed] |
| O1 nested constructor (`bad/nested_constructor.beaml`) | exit 1, names `Line.amount`, help line | [Observed] |
| O1 two levels down (scratch: `PlaceOrder.line: Line`, `Line.deep: Deep`) | enum: exit 1, names `Deep.channel`; constructor: exit 1, names `Deep.amount` | [Observed] |
| Control: nested plain record two levels down, echo fixture | exit 0, `ui_echo` generated | [Observed] |
| Control: top-level enum and constructor plus nested plain record accept a good event | `test_o1_...` passes in all 5 runs below | [Observed] |
| Constructor TYPE with an enum parameter at the top level | exit 1 by the older S4 check; not a gap of the new loop | [Observed] |
| `--stored` over the ENTRY stream, orders fixture with `channel` moved into a nested `Line` | exit 1 with the DL-144 text, empty stdout, no count line: the stored check never runs | [Observed] |
| Stored values in that stderr | 0 of 9 stored String values | [Observed] |
| O2: G6D-04 in `0005 .../owner-review.md` | Repair, "(GREEN slice6d, default, open)", raised from Undo by TEST O2 (committed in 2207c856) | [Observed] |
| O3: D035 in `decisions-to-be-made.md` | two lines: R1 [Inference], entry `value_sha256` gap [Observed], both link this review | [Observed] |
| RED log | `test-repair-red.log`: 2 failures before the fix, both `n10` subtests | [Observed] |

### Entry test, five sequential runs

`BEAML_SPIKE=<scratch> python3 -B -m unittest tests/slice6_entry_test.py` from the EXPERIMENT directory, nothing else of mine running:

| Run | Result |
|---|---|
| 1 | OK, 19 tests, 9.4 s |
| 2 | OK, 19 tests, 9.5 s |
| 3 | OK, 19 tests, 8.9 s |
| 4 | OK, 19 tests, 11.9 s |
| 5 | OK, 19 tests, 9.6 s |

- **[Observed]** The payments stub listens on port 0 (ephemeral), so a fixed-port collision is not the cause.
- **[Unknown]** The cause of the 1 of 12 failure the worker saw. Not reproduced in 5 runs; no test name was captured. A product bug that fails 1 of 12 runs is unlikely in a deterministic compiler, so a harness or host race (shared `elixir` or `elixirc` load, other workers) is the more likely cause **[Inference]**. Next check: keep `-v` output of each `slice6-entry` step in `run.py` results, so a repeat names the test.

### Objections

None at critical or high. O1 is closed; O2 and O3 are recorded.

- Note (medium): the flake is unexplained; see the next check above. Not blocking.

### Decisions

**Repair**
→ PASS statt BLOCK, weil O1 builds red with the field name in all four probes and `--stored` never runs. By: Opus (TEST re-check slice6d)

**Undo**
→ O2 and O3 accepted as recorded. By: Opus (TEST re-check slice6d)
→ Flake noted, not blocking (0 of 5, no product evidence). By: Opus (TEST re-check slice6d)
→ Two-level help text ("move Deep.channel to the top level") not challenged: wording only. By: Opus (TEST re-check slice6d)
