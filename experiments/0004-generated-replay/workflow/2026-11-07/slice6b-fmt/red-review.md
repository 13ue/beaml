# Slice 6b step 10: RED review (fresh context)

Target: [spec.md](spec.md), [notes.md](notes.md) F1 to F16 and U1 to U11, [red-output.log](red-output.log), `tests/slice6_fmt_test.py`, `slice6/fmt/`.
Not a Devil's Advocate round. Baseline: commit `cd379ff0`, `git archive` to a scratch directory, `cargo build --offline`. The live tree was not built. `run.py` was not run.

**Verdict: BLOCK on R1 (high).** R2 and R3 are medium. The rest of the RED is genuine.

## Rerun

- **[Observed]** Input hashes are the same as in notes.md.
- **[Observed]** 22 tests, 26 failures with subtests, 1 pass (guard F14). Each failure has the usage text as its cause. Same as red-output.log.
- **[Observed]** A scratch fake `fmt` (a Python wrapper over the baseline; it writes the expected file) passes 22 of 22. The tests are satisfiable.

## Partial GREEN probes (scratch fake, observed)

| Fake `fmt` | Tests that fail | Tests that pass falsely |
|---|---|---|
| No-op, exit 0 | 14 | 8, incl. idempotence, compile-equal, both invalid cases, blank and comment breaks, kept marks, comments |
| Marks only | 9 (all clause alignment, rewrite, CRLF, event of clauses) | none of the mark cases |
| Alignment only | 5 (mark removed, mark written, rewrite, CRLF, event of marks) | none |
| Comments lost (AST print) | 8 (comments, rewrite, compile-equal, idempotence, CRLF, event) | none |
| Writes LF | 2 (CRLF clauses, CRLF marks) | none |

## Encoding of the decisions

- **[Verified]** DL-104: `Chained v3` with a chain from v1 loses the mark. `Squashed v3` and `Payment v1` without a chain keep the mark. `Shortened` (chain from v4) gets ` v5`. `Kept v5` and `Plain` stay. Exact.
- **[Verified]** DL-083: argument columns and `->` align in group A, lines 16 and 17, lines 27 and 28. Changed lines: 7 in clauses, 2 in marks. The event counts agree.
- **[Inference]** The `=` column has no test power: in each group the return TYPE text is the same, so "align `=`" and "one space before `=`" give the same file. Two EFFECT lines would show it (F3, U6). Low; no objection.
- **[Verified]** CRLF: the copy keeps `\r\n`; a blank line with only `\r` must break the group, else line 19 pads and the whole-file compare fails.
- **[Verified]** Event: the test rejects the work path and the source tokens `fn `, `//`, `type `, `PaymentState`. The path is absolute, so a logged path fails.

## Objections

### R1 · high · The rule "of one `fn` name" has no test

- **Wrong outcome.** A `fmt` that groups any consecutive single-line clauses passes 22 of 22. Then two adjacent one-line functions with different names get padded to each other. Many files have one-line helpers in a row.
- **Evidence.** **[Verified]** No fixture has two adjacent single-line clauses with different names (clauses lines 4, 10 to 12, 16 to 17, 19, 21, 24, 27 to 28, 31, 38; marks line 26). Each group neighbour is a blank, a comment, a TYPE or a multi-line line.
- **Smallest test.** Add two adjacent lines with different names and different argument widths, one space each, e.g. `fn one a -> String = a` and `fn other_name bb -> String = bb`. Assert both lines stay. The CHANGED counts stay the same.

### R2 · medium · The invariant tests pass for a no-op

- **Wrong outcome.** `test_fmt_is_idempotent` and `test_compiled_output_equal_except_declaration_offsets` pass when `fmt` exits 0 and changes nothing (probe). F13 stops only a no-op that exits 1. The notes.md inference "F13 stops a no-op from passing" is true for the suite, not for each test.
- **Consequence.** Today the exact-file tests catch it. If a later change relaxes those tests, D6B-45 has no power. F16 shows the power only when the file changes.
- **Smallest test.** In both tests, assert that the first `fmt` result equals `expected(name)`.

### R3 · medium · F4 changes what the OWNER sees in a typical file

- **F4 (signature line ends a group): ask the OWNER.** **[Verified]** `slice6/enum/constructor.beaml` puts a signature line directly above each set of clauses. So F4 decides the look of every constructor table: header row aligned or not. One question; it does not block the RED. If the OWNER takes the header row, lines 9 and 15 of `clauses.formatted.beaml` and the test at line 130 change.
- **F5 (lone clause, one space): record.** It changes only lines with extra spaces. A typical hand-written file has one space and stays the same. Within DL-083 and DL-013.
- **U3 (no width limit): record.** DL-083 sets no limit. A limit is a new rule and a change of DL-083.

## Other notes

- U5 (two signatures of one name, no line between) and U9 (comment after a clause in a group of two) stay untested. Low.
- The spec is complete for the RED. No change of production files or tests in this review.

## Repeat

```
BEAML_SPIKE=<scratch>/experiments/0001-syntax-to-beam/target/debug/beaml-spike \
  python3 -B experiments/0004-generated-replay/tests/slice6_fmt_test.py
```
