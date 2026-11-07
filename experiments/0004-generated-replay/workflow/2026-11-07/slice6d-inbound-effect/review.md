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
