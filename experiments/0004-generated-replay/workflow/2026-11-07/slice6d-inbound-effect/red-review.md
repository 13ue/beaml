# RED review: slice 6d, the ENTRY LINE (inbound EFFECT)

**[Observed]** RED review, 2026-11-07, git HEAD d5d2a2ad. Fresh-context reviewer, no worker context reused.
Inputs: [plan.md](plan.md) (with Plan repair), [decisions.md](decisions.md), [red-plan.md](red-plan.md), [red-output.md](red-output.md), `tests/slice6_entry_test.py`, `slice6/entry/`. OWNER rules: DL-130 to DL-134 in [the decision log](../../../../../wiki/planning/decision-log.md).
By: Opus (RED review slice6d).

## Verdict: BLOCK

One high objection (O1). Two medium notes (O2, O3). Every RED is genuine.

## Evidence (reproduced)

- Compiler: `git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>`, `cargo build --offline`. `main.rs` not edited.
- `BEAML_SPIKE=<scratch>/.../beaml-spike python3 -B experiments/0004-generated-replay/tests/slice6_entry_test.py`: 16 tests, 32 failing subtests, exit 1. `test_h2` and `test_n13` pass (guards).
- Every failure text is `expected identifier at byte N` (the parse stop at the ENTRY LINE). No other failure reason in the log.
- All 14 `bad/` files and the 3 fixtures compile at HEAD (exit 0) with the `effect ui.` line removed. So no fixture typo; each `bad/` file fails on the ENTRY LINE only.
- `elixirc --warnings-as-errors` on a file with an undefined remote call: exit 0, warning on stderr (Elixir 1.18.1, OTP 27). Confirms R6D-11.

## Checklist

1. **RED genuine.** Yes. Parse error only; base sources compile; harness positive control in red-output.md.
2. **DL-130 drift rule.** Input (`drift_input`), output (`drift_output`), failure (`drift_failure`), plus head-none and fn-none. Covered, exact text.
3. **`Rejected` against the fn failure TYPE.** `N7_domain_failure_passes` expects `PaymentError` struct; every reject expects `Rejected`; struct equality includes `__struct__`. `DL133_rejected_shape` pins the keys, so a key-less `Rejected` cannot make `struct/2` hide the reason. Covered.
4. **DL-134.** `test_s2` (stricter constructor), `test_s3`, `test_s3b` (lost literal) block with exact DL-102 and DL-122 texts. `test_s4` needs the block text and finds no stored value in stderr; `compile()` checks the events. Covered, see O1 and O2 for the gaps.
5. **Host build (DL-131).** H2 judges the warning text. Sound: it is a guard of the Elixir behaviour, and H1 checks the absence of the same text. Limit: the host sees a warning, not an error, under `elixirc`. That meets DL-131 "warning or error".
6. **R6D-04 and R6D-05.** Not hidden Migrate decisions. R6D-04 follows the existing `<kind>.jsonl` side by side layout of `Capture`; R6D-05 copies the RESPONSE RECORD key of step 7. Both are cheap to undo in R&D (test, fixture). Repair is right. But see O1: the key set misses one fact.
7. **M1 and M2.** The worker stopped correctly at both. M1 leaves a pinned help text that conflicts with D6B-130 (O2). M2 leaves a path with no pinned outcome (O3).

## Objections

### O1 · high · A stored reject record blocks an unchanged build

- **Evidence.** D6B-135 writes an ENTRY RECORD also for a reject; D6B-145 writes `value: null` after a term check reject. The ENTRY RECORD has no outcome key (D6B-135: "no `status`"; `N8_entry_keys` pins the exact key set). DL-134 runs the input constructors and literals over each stored value. `stored/entries.jsonl` holds three records; none is a reject record (no null value, no empty currency).
- **Consequence.** The first live constructor reject is captured. The next `--stored` build on the unchanged source fails the `Amount` constructor and blocks with the DL-102 text. No MIGRATE STEP form exists (M1), so the build stays blocked. A `null` value record can crash the check. The reverse also goes unseen: a looser constructor turns a stored reject into `ok` at the REPLAY RUN. The tests pass a GREEN with all three faults.
- **Why GREEN cannot fix it alone.** Without a capture outcome in the record, the check cannot tell "failed at capture" from "fails now". The fix changes the stored record contract that every later stream copies (DL-134 reason). That is Migrate.
- **Resolving test.** Add two lines to a stored fixture: a constructor reject record and a `value: null` record. Pin the OWNER answer: for example `test_s1` still builds with empty stderr (reject records are skipped by a recorded outcome key), and `test_s2` still counts 3. Change `N8_entry_keys` if a key is added.
- **Question for the OWNER (Migrate).** A: the ENTRY RECORD records the capture outcome (for example `rejected: "decode" | "constructor" | null`); `--stored` skips records that were rejects at capture. B: `--stored` checks only records whose value decodes under the BASE source (needs the old source; heavier). C: reject records are not written to `entries.jsonl` (changes D6B-135, D6B-145 and N9 reject cases).

### O2 · medium · The `test_s2` help line advises a compile error

- **Evidence.** `CTOR_BLOCK` pins "declare the fate of these records in a MIGRATE STEP to a new TYPE VERSION of PlaceOrder (DL-102)". `bad/input_version_mark` pins that a VERSION MARK on the input TYPE is a compile error (D6B-130). red-plan M1 names the conflict and leaves it open.
- **Consequence.** GREEN implements a help line that sends the user into the `input_version_mark` reject. The test then changes after the M1 answer.
- **Resolving test.** Until M1 closes, pin the restore help of `LITERAL_BLOCK` style for `test_s2` ("restore the constructor rule of Amount"), or pin the first line only and leave the help line to the M1 answer.

### O3 · medium · A removed ENTRY LINE with stored ENTRY RECORDS has no pinned outcome

- **Evidence.** red-plan M2. A RESPONSE RECORD without its EFFECT blocks ("has no effect in the source"). No test runs `--stored` over `entries.jsonl` with the ENTRY LINE removed. H2 shows the host only gets a warning.
- **Consequence.** GREEN can skip these records silently, crash, or block. A silent skip plus a host warning gives a green build that lost the entry and its stored events.
- **Resolving test.** Orders without the ENTRY LINE, `--stored` over `stored/responses.jsonl`: pin the parity block text, or the OWNER answer to M2 (RETIRE LINE coverage). At minimum assert no crash and a non-empty stderr.

## Decisions

**Migrate**
→ O1: record the capture outcome (A), or check against the BASE source (B), or no reject records (C). OWNER chooses. By: Opus (RED review slice6d), question only.

**Repair**
→ BLOCK on O1 statt PASS with a note, weil the tests pass a GREEN that blocks an unchanged build after the first reject. → By: Opus (RED review slice6d)
→ R6D-04 and R6D-05 as Repair statt Migrate, weil both copy an existing record layout and are cheap to undo in R&D. → By: Opus (RED review slice6d)
→ H2 sound statt a mix-based probe, weil DL-131 accepts a warning and H1 checks its absence. → By: Opus (RED review slice6d)

**Undo**
→ O2 and O3 medium, not blocking. → By: Opus (RED review slice6d)
→ Out-of-scope finding (no warning gate in the 0004 runtime harnesses) left as recorded by the worker. → By: Opus (RED review slice6d)
