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
| `integrations/zed-beaml/test/highlight/constructors.beaml` | 11 assertions | `940fadadae98aab6c3e1dee12820227b3c64bc17adc74990d143390ac19a9f58` (after RED repair; was `4e858a7d…21df1c8`) |

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

## RED repair

**[Verified]** RED REPAIR, 2026-11-07. Fresh worker. Input: [red-review.md](red-review.md) objection 1 (high), notes 2 and 3 (medium). Output: [red-output.log](red-output.log) Runs 3 to 5. No change to `grammar.js`, `highlights.scm` or `src/`.

### Change

- `test/highlight/constructors.beaml`: add ` // anchor` after `Authorized` (row 3), `Declined` (row 7) and `card_holder` (row 13). Carets do not move.
- **[Verified]** A trailing comment stops the borrowed class. Probe (Run 3): `= x` with `^ constructor` and `enum E { A }` on the next line passes. `= x // anchor` fails, `actual highlights: none`.
- Corpus file: no change.

### Mutation result (Run 4)

Each assertion alone, current grammar, `test --rebuild`, scratch copy:

| # | Target | Result |
|---|---|---|
| 1 | `Authorized` in the enum | pass (guard) |
| 2 | `"ok"` | FAIL, none |
| 3 | `fn` | pass (guard) |
| 4 | `PaymentState` clause name | FAIL, `function` |
| 5 | `Authorized` clause body | FAIL, none (row 1, column 42) |
| 6 | `DeclineReason` | FAIL, `function` |
| 7 | `Declined` pipe step | FAIL, `function` (row 2, column 80) |
| 8 | `g` | pass (guard) |
| 9 | `prepare` | pass (guard) |
| 10 | `card_holder` | FAIL, none |
| 11 | `Pending` | FAIL, none |

- **[Verified]** 7 FAIL, 4 guards pass. No hang: no failing assertion is the last token of the file.
- **[Verified]** Run 5 (repository, `--rebuild`, `-e`): old highlight files pass (19 + 48 + 2). `constructors.beaml` fails at row 0, column 33. Full `test --rebuild`: 17 old corpus examples and 2 guards pass, 4 new examples fail.
- **[Unknown]** The GREEN grammar without the bare-variant capture was not probed. The anchor removes the mechanism (probe), so the borrowed class can only be `comment`.

### Rules for GREEN, TEST and VERIFY

- Use `--rebuild` in every `tree-sitter test` command, also in the highlight run. A command without `--rebuild` is no evidence.
- Run `test --rebuild` directly before `preview.py`. Do not run probes in parallel with these phases.
- Every new highlight assertion on the last token of a line gets a trailing ` // anchor`.
- GREEN review check (red-review note 3). This command must print nothing:

```sh
rg -n '^\((function_clause|pipe right: \(identifier\))' languages/beaml/highlights.scm
```

- **[Verified]** Today it prints rows 20 and 23 (patterns without a predicate). A pattern with a predicate starts with `((`. The shared block lines start with a space.

### Decisions

| Class | Choice | Alternative | Reason |
|---|---|---|---|
| Undo | Trailing ` // anchor` comment | Move each target before another token | Smallest diff. Source forms stay as in the spec. Comment is in `extras`. |
| Undo | Mutation per assertion in a scratch copy | Edit the repository file per run | Repository file stays unchanged. Shared cache rebuilt from the repository after (Run 5). |
| Undo | Mutation on the current grammar only | Also probe a GREEN-like grammar | Task scope. Probe shows the mechanism is closed. |
| Undo | `rg` check on bare `function_clause` and `pipe right: (identifier)` patterns | `rg` on every capture pattern | Most patterns (keywords, `string`) need no predicate. The review asks only for these two. |
| Undo | Count fixed to 11, hash updated | Keep old row | The file has 11 assertions and changed. |

## GREEN

**[Verified]** GREEN phase, 2026-11-07. Fresh worker. Full output: [green-output.log](green-output.log). No change to the test files (hashes equal the Solve table).

### Change

- `grammar.js`: the 4 edits of PROPOSAL ULTRA Step 3, word for word. Comments added for DL-082 (variant literal), DL-084 (signature line) and DL-089 (`with` release).
- `languages/beaml/highlights.scm`: PROPOSAL ULTRA Step 4, word for word. The old `(call name: (identifier) @constructor)` pattern is deleted. The shared uppercase block is at the end of the file.
- `src/` regenerated. `grammars/beaml.wasm` rebuilt.

### Results

| Check | Result |
|---|---|
| `generate --abi 15 --js-runtime native` | exit 0, no conflict |
| `test --rebuild` | 23/23 corpus, 4/4 highlight files (19 + 48 + 2 + 11 assertions), exit 0 |
| `build --wasm -o grammars/beaml.wasm` | exit 0 |
| `test --wasm --rebuild` | 23/23, 4/4, exit 0 |
| Predicate `rg` check | prints nothing |
| `rg 'ERROR\|MISSING'` on `constructors.txt` and on `parse constructors.beaml` | prints nothing |
| `parse -q` and `parse --wasm -q`, 3 `preview.py` DEFAULT sources | exit 0 each |
| `parse -q`, 1375 `.beaml` files under `experiments/` | 277 clean, 1098 with ERROR, 0 MISSING |
| `test --rebuild`, then `preview.py --chat constructors.beaml` | `c` on `PaymentState` (name), `Authorized`, `Unknown`, `DeclineReason`, `Declined`, `Pending`. `p` on `card_holder`. `f` on `g`, `build`, `prepare` |

- **[Verified]** All 1098 failing files have a line that starts with `interface` (DL-074). They are old sketches and result copies in `0002`, `0003` and `0004` `results/`.
- **[Verified]** Swap check: with `interface ` replaced by `type ` in scratch copies, 1097 of 1098 parse with 0 ERROR. The last one is `experiments/0004-generated-replay/syntax-options.beaml`: an undecided `effect name { ... }` block sketch (OPTION A).
- **[Inference]** No failure comes from a GREEN form. A run of the old grammar on the same files was not done, to keep the shared parser cache clean.

### Event

- **[Verified]** Commit `4a691ec7` (slice 6b plan check, from another agent) holds the GREEN edits and a partial `green-output.log`. GREEN did not commit. The log diff is against `e70a95c3`.

### Decisions

| Class | Choice | Alternative | Reason |
|---|---|---|---|
| Undo | Apply PROPOSAL ULTRA Steps 3 and 4 with no deviation | Change the query or grammar | All checks pass. No deviation needed. |
| Undo | Skip the README items of Step 6 | Add them in GREEN | Task names `grammar.js` and `highlights.scm`. README belongs to the docs phase. |
| Undo | Parse `-type f` files only | Parse every path that ends in `.beaml` | Two `.beaml` paths are directories. The first run stopped at one of them. |
| Undo | Classify failures by `interface` lines and a swap check | Build the old grammar and compare | Old-grammar probe writes the shared cache (red-review note 2). |
| Undo | No mutation check on the bare-variant capture | Remove the capture and rerun | RED repair closed the borrowed class with ` // anchor`. Run 4 showed assertions 5 and 7 fail on the old query, which has no bare-variant capture. |
| Undo | Use the cached `npx` CLI for `preview.py` | Record a blocker | `npx --no-install` shows 0.26.5 is cached. No download. |

### Open points

- README items (Step 6) for the docs phase.
- **[Unknown]** Zed applies the shared `#match?` to each alternative (PROPOSAL ULTRA Step 4). Not checked in Zed.

## TEST

**[Verified]** TEST phase, 2026-11-07. Fresh worker. Full output: [test-output.log](test-output.log). Summary: [test-result.json](test-result.json). No change to code or tests.

### Results

| Check | Result |
|---|---|
| `generate --abi 15 --js-runtime native` | exit 0. No change to tracked files. |
| `test --rebuild` | 23/23 corpus, 4/4 highlight files, exit 0 |
| `test --wasm --rebuild` | 23/23, 4/4, exit 0. `grammars/beaml.wasm` unchanged. |
| Predicate `rg` check | prints nothing |
| `rg 'ERROR\|MISSING'` on `constructors.txt` and on `parse constructors.beaml` | prints nothing |
| `parse -q`, 3 `preview.py` DEFAULT sources | exit 0 each |
| `preview.py --chat` (repository root, after `test --rebuild`) | exit 0, 3 sections, classes `b c f k m o p s t` |
| `scripts/lint_wiki.py` | 81 files, 0 errors |
| `slice5_syntax_test.py` | 60 tests, OK |

- **[Verified]** Overall: pass. No check is `not_run`.
- **[Verified]** `src/` is ignored by git. The only tracked generated file is `grammars/beaml.wasm`. It did not change.
- **[Verified]** `parse` prints a warning on missing parser directories. The CLI uses the grammar in the work directory. The parse tree is present.

### Decisions

| Class | Choice | Alternative | Reason |
|---|---|---|---|
| Undo | No `build --wasm` in TEST | Rebuild `grammars/beaml.wasm` | Task names no build. A rebuild can change a tracked file. `test --wasm --rebuild` uses its own build. |
| Undo | `npx --no-install` cache check before `preview.py` | Run `preview.py` directly | `preview.py` calls `npx -y`. A check stops an unplanned download. |
| Undo | Log class counts of the preview, not the HTML | Keep the full fragment in the log | Short log. The fragment is repeatable from the command. |
| Undo | Old 1375-file parse sweep not repeated | Repeat the GREEN sweep | Task names the 3 DEFAULT sources only. GREEN recorded the sweep. |

### Process note

- **[Verified]** EVENT: the grammar edits reached `main` in commit `4a691ec7`, one commit before the GREEN commit `971385ec`. The main agent staged a plan-check commit while the GREEN worker still wrote files.
- Class Repair. The content is identical. The history is misleading: `4a691ec7` names the slice 6b plan check, but holds the slice 6a grammar.
- Rule reaffirmed: do not use `git add -A` while a worker runs. Stage named paths only.
