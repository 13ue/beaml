# RED review: slice 6a grammar

**[Verified]** Fresh-context RED REVIEW, 2026-11-07. This is no Devil's Advocate round. Scope: consequences only. No production file or test file changed.

## Verdict

BLOCK. One high objection (1). Two medium notes (2, 3). The corpus RED is genuine. The highlight RED has a false-pass hole for 3 of 11 assertions.

## Evidence

CLI: `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` (0.26.5). Probes ran in the scratchpad. The shared parser cache was rebuilt from the repository at the end.

- **[Verified]** `test --rebuild` in `integrations/zed-beaml/`: 4 new corpus examples fail, 2 guards pass, 17 old examples pass. Same result as `red-output.log` Run 1.
- **[Verified]** The stale cache fault is real. A scratch probe with a GREEN-like grammar writes `~/.cache/tree-sitter/lib/beaml.dylib`. After the probe, `test` without `--rebuild` in the repository passes "Record constructor with a failure TYPE". `test --rebuild` fails it again.
- **[Verified]** `src/` is git-ignored. `src/grammar.json` is the same as a new `generate` of `grammar.js`. So the RED ran against the current grammar.
- **[Verified]** `rg -n 'ERROR|MISSING' test/corpus/constructors.txt` prints nothing.
- **[Verified]** Each expected tree agrees with the DL text. DL-082 L and C2, DL-084 and DL-089 are word for word. DL-086 is left-associative. DL-092 and DL-093 parse as the spec says. `(parameter (integer))` is the same tree if GREEN adds `integer` to `parameter` or to `_expression`.
- **[Verified]** Each highlight assertion alone on the old grammar (11 assertions, not 10 as in `notes.md`):

| # | Target | Old grammar |
|---|---|---|
| 1 | `Authorized` in the enum | pass (guard) |
| 2 | `"ok"` ENUM LITERAL | fail, none |
| 3 | `fn` keyword | pass (guard) |
| 4 | `PaymentState` clause name | fail, `function` |
| 5 | `Authorized` clause body, end of line | fail, CLI hangs alone |
| 6 | `DeclineReason` pipe step | fail, `function` |
| 7 | `Declined` pipe step, end of line | fail, CLI hangs alone |
| 8 | `g` lowercase clause name | pass (guard) |
| 9 | `prepare` lowercase pipe step | pass (guard) |
| 10 | `card_holder`, end of line | fail, CLI hangs alone |
| 11 | `Pending` in `add` value | fail, none |

## Objections

1. **High. An assertion on the last token of a line borrows a class from a later line.**
   → Observed: `fn f x: String -> String = x` with `^ constructor` on `x`, then `enum E { A }`. The assertion passes. With `x + y` it fails ("actual highlights: none").
   → Observed: in `constructors.beaml` with assertions 1 to 4 removed, assertion 5 reports a list of classes from the next lines.
   → Wrong outcome: GREEN omits the bare-variant capture of spec item 7. `Authorized` (5) and `Declined` (7) get no class. The next line `fn PaymentState` gets `constructor` in GREEN, so both assertions pass. For 10, the next line has `state` as `property`. The corpus tree covers 10, but nothing else covers 5 and 7.
   → Smallest test: a mutation check in GREEN. Remove the bare-variant capture from `highlights.scm`, run `test --rebuild`, and record that `constructors.beaml` fails at row 3, column 42. Do the same for the pipe-step capture at row 7, column 80. Or move each target so that another token follows it on the same line.

2. **Medium. The shared parser cache can give a false pass after `--rebuild` also.**
   → Observed: every scratch probe of any worker writes the same `beaml.dylib`. `preview.py` calls `tree-sitter highlight` through `npx`, which uses this cache. The Run 2 command in `notes.md` has no `--rebuild`.
   → Wrong outcome: a probe runs between the GREEN test and the preview. The preview then shows `c` from a probe grammar, not from the committed grammar.
   → Smallest test: use `--rebuild` in every command of GREEN, TEST and VERIFY, including the highlight run. Run `test --rebuild` directly before `preview.py`. Do not run probes in parallel with these phases.

3. **Medium. The CLI result does not show the Zed result for two captures on one node.**
   → Inference: assertions 4 and 6 can pass in the CLI while an old `@function` pattern without a predicate stays in `highlights.scm`. Zed can then show `function`. **[Unknown]** Which capture Zed selects was not checked.
   → This is plan-check note 2. The RED has no test for it.
   → Smallest test: every pattern on `function_clause name:` and `pipe right: (identifier)` has `#match?` or `#not-match?`. Check it with `rg` in GREEN review.

## Guards

- Keep "Overlap is no grammar error". It stops GREEN from moving the DL-093 check into the grammar.
- Keep "Pipe inside an argument". It stops a precedence change from the new `=` or `integer` rules from breaking DL-086. It costs 1 example.
- Keep highlight guards 1, 3, 8 and 9. Guards 8 and 9 catch an uppercase rule that also hits lowercase names.

## Limits

- **[Verified]** The CLI hangs when a failing assertion targets the last token before the end of a file. It does not report a pass. A test run with a timeout can show this as no output.
- The Zed capture rule was not checked.
- The GREEN grammar was not probed for objection 1. The borrowed class comes from the observed mechanism.
