# Slice 6b step 10: REVIEW (fresh context)

Target: [spec.md](spec.md), [notes.md](notes.md) (F1 to F21, U1 to U11, GREEN G1 to G9), [red-review.md](red-review.md), plan step 10, D6B-41 to D6B-46, DL-083, DL-104, the diff `git diff bf5691a5..078bbf6f -- experiments/0001-syntax-to-beam/src/main.rs` (`fmt_file`, `fmt_mark`, `formatted`, `aligned`, `main()`).
Normal review, not a Devil's Advocate round. HEAD `8924cb3f`. TEST evidence: [test-output.log](test-output.log), [test-result.json](test-result.json). No code or test was changed.

**Verdict: PASS.** No critical or high defect. Two low notes.

## Step met

- **[Observed]** `slice6_fmt_test.py` 25 of 25 at HEAD (TEST). The cases cover D6B-41 to D6B-46: diff and atomic write, no write without a change, invalid source writes nothing, DL-104 marks, groups, comments, CRLF, idempotence, compile equivalence, the event.
- **[Verified]** `fmt_mark` is the DL-104 rule A: remove a mark only at the end of a chain from v1; write ` v<end>` for a chain above v1 without a mark; keep every other mark. Unit test `fmt_mark_follows_dl104`, 7 cases.
- **[Verified]** `formatted` runs `lex`, `Parser::program`, `Checker::new`, `validate` before any edit. An error returns before `write_atomic` (G1).
- **[Verified]** `aligned` changes only the gaps between cells. Cells come from tokens, so a string never gives a column (probe 2).
- **[Observed]** The diff adds no feature beyond plan step 10. No `--check`, no line breaking, no editor change.

## Adversarial probes (scratch, HEAD binary, exact output)

| # | Source | Result |
|---|---|---|
| 1 | Clauses with a tab indent and a tab gap (`\tfn f "a" -> ...`, `fn f "bbb"\t->  String`) | exit 0. Diff: `\tfn f "a"   -> String = "x"` and `fn f  "bbb" -> String = "y"`. Second run: no change. |
| 2 | `fn f "a\|>b" -> String = "x \|> y"`, `fn f "c"   -> String =   "p -> q = r"` | exit 0. Only the gaps before `->` change (`"c"    ->`, `other  ->`). String bytes and the gap after `=` stay. Second run: no change. |
| 3a | 2000 lines, 50 fns (71500 bytes) | exit 1, stderr `token limit exceeded`, file byte-equal. The existing lexer limit (8192 tokens) applies to the compile too. Not a `fmt` defect. |
| 3b | 1100 lines, 50 fns, 1000 changed lines (39440 bytes, under the token limit) | `fmt` real 0.64 s (debug build); compile of the same file 0.14 s. Second run: 0.53 s, no change. Compile output equal except the declaration offsets. |
| 4 | Syntax error at the last line (`fn g = = =`) | exit 1, empty stdout, stderr `expected expression or pattern at byte 86`, bytes equal, same inode, no temporary file. Event `fmt` `error` `changed: 0`. |
| 5 | Read-only file (mode 444) with a change | exit 1, empty stdout, stderr `error: cannot write ro.beaml: the file is not writable`, bytes equal, same inode, no temporary file. Read-only directory: `error: cannot write rodir/x.beaml: permission denied`, no file left. |

## Notes (low, no block)

- **N1 · low · Tab indent counts as one byte (U1).** Probe 1: `fmt` moves `"bbb"` to byte 6 to match the tab line, so the gap between `fn f` and the argument becomes two spaces. In an editor the lines do not align. Only mixed indent hits it. U1 records it as Undo.
- **N2 · low · `aligned` is quadratic (G9).** Probe 3b: about 0.5 s of the 0.64 s is `fmt` work. The token limit caps the input size, so no fix is needed in 6b.

## Consistency of RED, reviews and GREEN

- **[Observed]** RED 22 tests, RED repair 25 (24 FAIL, 1 guard pass), GREEN 25 of 25, TEST 25 of 25. The red-review R1, R2 and R3 are closed in the RED repair (F17 to F21).
- **[Observed]** GREEN cargo counts 18 unit + 14 CLI agree with TEST.
- **[Observed]** GREEN listed constructor 24 of 25 and decode_ctor 0 of 7 as RED by design. At HEAD (after step 8) they are 25 of 25 and 8 of 8.
- **[Observed]** Open OWNER points stay open: Q6B-9 (signature line as a header row), U3 (no width limit), U11. This review does not close them.

## Decisions

| # | Class | Decision | By |
|---|---|---|---|
| RV1 | Undo | The 2000-line probe exceeds the lexer token limit. A 1100-line file under the limit is the timing probe. | Opus (REVIEW, slice6b-fmt) |
| RV2 | Undo | N1 and N2 are low. They do not block. | Opus (REVIEW, slice6b-fmt) |
| RV3 | Undo | Verdict PASS. | Opus (REVIEW, slice6b-fmt) |

## Limits

- The probe files are in the scratch directory only. The commands are in the table above.
- Timing is from one run of a debug build.
