# Notes: slice 6a grammar

## Solve

**[Proposal]** SOLVE phase, 2026-11-07. Fresh worker. Inputs: `spec.md`, `plan.md`, `plan-review.md`, `proposal-ultra.md`, `proposal-lite.md`.

### Choice

Use PROPOSAL ULTRA.

- The `grammar.js` diff is the same in both proposals (4 edits, `choice` in `variant_declaration`).
- ULTRA has the smaller `highlights.scm` diff: +19 / −4 against +27 / −2.
- ULTRA deletes the old `(call name: (identifier) @constructor)` pattern. One alternation block covers it.
- ULTRA keeps one uppercase rule in one place. LITE keeps three places: two predicate pairs and the block.
- Both proposals satisfy plan-check notes 1 and 2. ULTRA adds `add_operation value:` for note 3.

### Merge from LITE

- Merge the hand-written expected trees of LITE Appendix A for the same inputs. ULTRA names the extra examples but gives no trees. The trees were checked against `grammar.js` rule by rule.
- No other merge. No LITE change is a needed correction.

### Rejected complexity

- LITE split of the enum into two enums (DL-088). Reason: the grammar does not check DL-088. ULTRA keeps the DL-082 text word for word. The plan allows both.
- LITE body-less record signature `fn NonZeroInt n: Int -> NonZeroInt ! IsZero`. Reason: the example "Signature with several failure TYPES" covers a body-less signature with `!`.
- LITE `@constructor` / `@function` pairs on `function_clause name:` and `pipe right:`. Reason: the shared block with `#match?` and the `#not-match?` on `@function` give the same classes with fewer lines.
- LITE extra `number` and `operator` assertions. Reason: `forms.beaml` covers these classes.

### Test files of this phase

| File | Examples or assertions | SHA-256 |
|---|---|---|
| `integrations/zed-beaml/test/corpus/constructors.txt` | 6 examples | `7f23972e451961fc10699ddcac337f0650daade736102fd77f96527433d53001` |
| `integrations/zed-beaml/test/highlight/constructors.beaml` | 10 assertions | `4e858a7d3d6271ebc49c4c0a5f2e8b9f1e1e1b0cc50c468f33db6d18c21df1c8` |

- **[Verified]** Each caret column hits the intended token. A script compared each caret with the source line above it.
- **[Verified]** `rg -n 'ERROR|MISSING' test/corpus/constructors.txt` prints nothing (plan-check note 1).

## RED

**[Verified]** RED phase, 2026-11-07. Full output: [red-output.log](red-output.log). No change to `grammar.js`, `highlights.scm` or `src/`.

### Setup fault (fixed)

- **[Verified]** The first run `tree-sitter test` passed all 6 new corpus examples. This is no GREEN result.
- **[Verified]** `src/grammar.json` has no `=` literal in `variant_declaration` and needs `=` in `function_clause`.
- **[Inference]** The CLI used a cached parser library from a scratch probe of the GREEN grammar. It did not rebuild from `src/parser.c`.
- Fix: run with `--rebuild`. All later phases must use `--rebuild`, or a GREEN can be a false pass.

### Commands

Run in `integrations/zed-beaml/`:

```sh
TS=/private/tmp/beaml-zed-highlighting/tools/tree-sitter   # tree-sitter 0.26.5
$TS test --rebuild                                          # Run 1, corpus
$TS test -e 'Enum constructor|Record constructor|Signature with|Effect releases'   # Run 2, highlight
```

- **[Verified]** The CLI runs the highlight tests only when every corpus example passes. Run 2 excludes the 4 failing corpus examples to reach the highlight tests.

### Results

| Test | Result | Reason |
|---|---|---|
| Enum constructor with signatures and clauses | FAIL | `ERROR` at each `= "…"` literal. The signature line has no body and joins the next clause as `ERROR`. |
| Record constructor with a failure TYPE | FAIL | `ERROR` in place of `(parameter (integer))` for `0`. |
| Signature with several failure TYPES | FAIL | Root `ERROR` in place of `function_clause`: no body. |
| Effect releases a redacted field | FAIL | `ERROR` around the body and `with card_holder`. No `(property)`. |
| Overlap is no grammar error | pass | Guard. The form parses today. |
| Pipe inside an argument | pass | Guard. The form parses today. |
| `constructors.beaml` | FAIL | `row: 0, column: 33, expected highlight 'string', actual highlights: none`. The ENUM LITERAL is `ERROR` today. |
| 17 old corpus examples | pass | 17/17. |
| `syntax.beaml`, `forms.beaml`, `lexer.beaml` | pass | 19 + 48 + 2 = 69 assertions. |

- New failing: 4 corpus examples, 1 highlight file. New passing guards: 2.
- **[Verified]** The CLI reports only the first failed assertion per highlight file.
- **[Verified]** Run 0 with the cached parser showed the next highlight gap: `row: 3, column: 3, expected highlight 'constructor', actual highlights: 'function'` (`fn PaymentState`). This is the query gap that `highlights.scm` must close.

### Genuine RED

- **[Verified]** Each failure is an `ERROR` node or a wrong class for the form under test. No failure comes from a missing file, a broken CLI or an unrelated test.
- The expected trees and captures are the GREEN target. Do not change them in GREEN to fit the parser.
