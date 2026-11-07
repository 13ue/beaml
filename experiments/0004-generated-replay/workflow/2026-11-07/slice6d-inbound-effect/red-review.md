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

## Re-check after RED repair

**[Observed]** 2026-11-07, git HEAD d5bb46b2. Fresh-context reviewer, one round, no worker context reused.
Inputs: [red-plan.md](red-plan.md) and [red-output.md](red-output.md) sections "RED repair", [red-repair-output.log](red-repair-output.log), `tests/slice6_entry_test.py`, `slice6/entry/`. Binding: DL-130, DL-131, DL-133, DL-134, DL-136, DL-138.
By: Opus (RED re-check slice6d).

### Verdict: PASS

O1, O2 and O3 are closed. Two medium notes (R1, R2). No critical or high objection.

### Evidence (reproduced)

- Compiler: `git archive HEAD experiments/0001-syntax-to-beam | tar -x -C <scratch>`, `cargo build --offline`. `main.rs` not edited.
- Test run against that build: 18 tests, 34 failing subtests, exit 1. `test_h2` and `test_n13` pass (guards). 32 failures stop at the ENTRY LINE parse error. `test_s5` fails with exit 0 and Elixir on stdout. `test_s5b` fails on `warning: DEAD LINE: retire ui.place ...`. Both are genuine.
- Own probe at HEAD (scratch copy of `orders.beaml` with no EFFECT, two `payments.authorize` records, status 200 and 503): exit 1, "has no effect in the source", count 2 (the 503 record counts), help names the RETIRE LINE. With `retire payments.authorize keep 30 days`: exit 0, empty stderr. This matches the worker's probe.
- Fixture facts, checked by key only (no value written here): all 5 lines have the same 14 keys. Lines 1 to 3 are `accepted`. Line 4 is `rejected`/`constructor` and fails the base `Amount` rule; it holds the enum value that `test_s3` removes. Line 5 is `rejected`/`decode` with `value: null`.

### Checklist

1. **O1 closed.** `test_s1` needs exit 0 and the count line as the only stderr line. A GREEN that checks line 4 blocks (base `Amount` rule); one that crashes or blocks on line 5 fails too. `test_s2` pins 3 records (4 if rejects are checked). `test_s3`, `test_s3b` pin 1 record at line 2 (2 if line 4 is checked). `test_s4` needs the block text and no stored word in stderr; `compile()` checks the events. `N8_entry_keys`, `N8_entry_fields`, `DL138_constructor_reject_outcome` and `N9_nested_nil_...` pin the keys at capture.
2. **O2 closed.** No expected help line names a TYPE VERSION. `CTOR_BLOCK` sends the user to restore the `Amount` rule. The `TYPE PlaceOrder v1:` header of `LITERAL_BLOCK` names the stored record's version, not a step.
3. **O3 closed.** `test_s5` pins the HEAD parity text with `ENTRY RECORD` and count 5. `test_s5b` pins that a RETIRE LINE frees the build with no DEAD LINE.
4. **R6D-15 consistent.** At HEAD the orphan count includes non-replayable records (probe above). DL-136 limits the *check*, not the orphan count. DL-138 asks for parity with today. Counting rejects is that parity; no hidden decision.
5. **Split as expected.** 2 guards green, the rest red on the parse error or on the two new s5/s5b cases.

### Notes

#### R1 · medium · A captured reject that passes now is not seen

- **Evidence.** DL-138 skips rejected entries. `N9_nested_nil_...` and `N9_constructor_reject_replays_as_reject` say the REPLAY RUN gives the live outcome.
- **Consequence.** A looser constructor turns a captured reject into `ok` at the REPLAY RUN. Neither `--stored` nor a test reports it. DL-121 ("check result equals REPLAY RUN result") holds for accepted entries only.
- **Resolving test.** Later slice: loosen `Amount`, replay line 4, pin the result (a note, or accepted as is).

#### R2 · medium · R6D-13 adds a record key; DL-139 holds record formats for the OWNER

- **Evidence.** DL-138 names one `outcome` key "with the reject reason". R6D-13 splits it into `outcome` and `reason`. DL-139: stored record keys and ENTRY RECORD layout wait for the OWNER; every built default is presented explicitly.
- **Consequence.** Bounded: no ENTRY RECORD exists outside fixtures. A different OWNER shape touches `ENTRY_KEYS`, two N-cases and `entries.jsonl`.
- **Action.** Present the R6D-13 key shape (and R6D-05 `unknown_fields`) to the OWNER as DL-139 built defaults before GREEN.

### Decisions

**Migrate**
→ R2: the R6D-13 key shape and R6D-05 go to the OWNER as DL-139 built defaults. Question only. → By: Opus (RED re-check slice6d)

**Repair**
→ PASS statt BLOCK, weil O1 to O3 have reproduced resolving tests and both notes are bounded. → By: Opus (RED re-check slice6d)
→ R6D-15 consistent statt hidden decision, weil the HEAD probe counts non-replayable records in the orphan count. → By: Opus (RED re-check slice6d)

**Undo**
→ R1 and R2 medium, not blocking. → By: Opus (RED re-check slice6d)
→ Dropped: no fixture line for a decode reject with a set value (low). → By: Opus (RED re-check slice6d)
