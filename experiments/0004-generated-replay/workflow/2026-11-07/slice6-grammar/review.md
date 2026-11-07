# REVIEW: slice 6a grammar

**[Verified]** Fresh-context final REVIEW, 2026-11-07. Devil's Advocate checkpoint, code mode (`advocatus-diaboli`, `implement-step` step 7). Target: `git diff 7858e728..e71f2aca -- integrations/zed-beaml/` and this ledger. No production file or test file changed. No commit.

## Verdict

PASS. No critical or high objection. Three medium notes.

## Own runs

CLI: `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` 0.26.5. Probes and mutations ran in scratch copies. The repository parser cache was rebuilt with `test --rebuild` after each probe set.

- **[Verified]** `test --rebuild` in `integrations/zed-beaml/`: 23/23 corpus, 4/4 highlight files (19 + 48 + 2 + 11 assertions). Same counts as `test-result.json` and `notes.md` GREEN and TEST.
- **[Verified]** SHA-256 of `test/corpus/constructors.txt` (`7f23972e…`) and `test/highlight/constructors.beaml` (`940fadad…`) equal the Solve table and `green-output.log`. GREEN did not change the tests.
- **[Verified]** `generate --abi 15` in a scratch copy: exit 0, no conflict. The new `src/grammar.json` equals the repository `src/grammar.json`.
- **[Verified]** `preview.py --chat test/highlight/constructors.beaml`: exit 0. Class `c` on `PaymentState` (name), `Authorized`, `Unknown`, `DeclineReason`, `Declined`, `Pending`. Class `f` on `g`, `build`, `prepare`. Class `p` on `card_holder`.
- **[Verified]** `tree-sitter query` with `highlights.scm` over the 4 highlight files and all adversarial inputs: no node range has two captures. The capture order of Zed cannot change a class in these files.

## Adversarial inputs

`parse -q`. OK = no ERROR and no MISSING node.

| Decision | Input | Result | Expected |
|---|---|---|---|
| DL-082 L | `enum E { A = 1 }` | ERROR | reject: a literal is a String |
| DL-082 L | `enum E { A(String) = "a" }` | MISSING | reject: payload or literal, not both |
| DL-082 L | `enum E { A = "a"  B("b") }` | ERROR | reject: a payload is a TYPE |
| DL-088 | `enum E { A = "a"  B }` and `fn E "x" -> E = A` | OK | accept: the compiler reports DL-088 |
| DL-093 | `fn f x: String -> String ! String` | OK | accept: compiler check |
| DL-093 | `fn f x: String -> String ! Int \| String = x` | OK | accept: compiler check |
| DL-093 | `fn f -> String ! = x` | ERROR | reject: empty failure list |
| DL-084 | signature line, then end of file | OK | accept |
| DL-084 | signature line, then `type X { a: Int }` | OK, 2 nodes | accept |
| DL-084 | `fn PaymentState status: String -> PaymentState =` | ERROR | reject: `=` without body |
| DL-084, DL-085 | 2 signatures, then 1 clause, one constructor | OK, 3 `function_clause` nodes | accept |
| DL-089 | `effect … = g() with` | ERROR | reject: zero fields |
| DL-089 | `effect … = g() with a, b` | OK | accept |
| DL-089 | `effect … = with x <- y do x end with card_holder` | OK, `property` on the effect | accept |
| DL-089 | `fn f x -> X = g() with card_holder` | ERROR | reject: release is for effects only |
| DL-086 | `x \|> g` | OK, `g` is `function` | accept |
| DL-086 | `x \|> Declined \|> g.h` | OK | accept |
| DL-086 | `x \|>` | MISSING | reject |
| DL-082 C2 | `fn f Authorized -> X = Authorized` | OK, both `constructor` | accept: pattern and expression |
| DL-082 C2 | `fn f x -> X = h(Authorized, Pending)` | OK | accept |
| DL-092 | `fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}` | OK | accept |
| DL-092 | `fn NonZeroInt 00 -> …` | OK | accept: no decision on leading zeros |
| DL-092 | `fn NonZeroInt 1.5 -> …`, `0x10` | ERROR | reject: no decided form |
| none | `fn f -1 -> Int = 0`, `= -1`, `+1` | ERROR | no decision for signed integers |
| DL-074 | `migrate T 1 -> 2 { … }` (`errors.txt`) | still `:error` | reject |
| none | `add a: Int = x`, `h(y) \|> k`, `else d -> e` | no `constructor` capture | lowercase stays out |

- **[Verified]** No input accepts a form that a decision forbids at grammar level. No input rejects a form that a decision requires.
- **[Inference]** DL-088 and DL-093 are compiler checks. The grammar must accept these inputs so that the compiler can report them with a help line.

## Mutation checks on the GREEN query

Scratch copy, `test --rebuild`.

| # | Mutation | Result |
|---|---|---|
| M1 | Delete `(function_clause (identifier) @constructor)` | FAIL row 3, column 3 |
| M5 | Limit it to `name:` (bare body loses its capture) | FAIL row 3, column 42 |
| M2 | Delete `(pipe (identifier) @constructor)` | FAIL row 7, column 63 |
| M6 | M2 and delete the `DeclineReason` assertion | FAIL row 7, column 80 |
| M4 | Delete `(add_operation value: …)` | FAIL row 15, column 53 |
| M3 | Delete the shared `#match?` | FAIL in `syntax.beaml`, `forms.beaml`: `function` became `constructor` |
| M7 | M5 and delete the 3 ` // anchor` comments | PASS (11 assertions) |

- **[Verified]** M5 and M6 close the RED review objection 1: each end-of-line assertion fails alone.
- **[Verified]** M7 shows that the anchors are load-bearing. Without them the old hole returns.
- **[Verified]** M3 and the lowercase query show that the shared `#match?` applies to the first and to later alternatives in the CLI.

## Objections

1. **Medium. No check tests the committed `grammars/beaml.wasm`.**
   → Observed: `test --wasm --rebuild` builds its own WASM. Two scratch builds of the same grammar give different SHA-256 values, so a hash cannot tie the file to `grammar.js`. The committed file is 28477 bytes; a fresh build is 28473 bytes; the old file was 26373 bytes.
   → Wrong outcome: Zed loads a stale or probe WASM, and all 12 checks still pass.
   → Smallest test: load `grammars/beaml.wasm` with `web-tree-sitter` (or in Zed) and parse the RED example with 0 ERROR nodes.
2. **Medium. The shared `#match?` over an alternation is not checked in Zed.**
   → Observed: the CLI applies the predicate to every alternative (M3, lowercase query).
   → Inference: Zed uses the same tree-sitter query engine, so the result is the same. **[Unknown]** Not observed in Zed.
   → Wrong outcome: in Zed, lowercase `g`, `prepare` or `x` show the constructor color.
   → Smallest test: open `test/highlight/constructors.beaml` in Zed with the dev extension. Check `g` and `prepare` against `Authorized`.
3. **Medium. The main-agent RED review has no record, and the RED repair had no second review.**
   → Observed: the ledger has `red-review.md` (fresh reviewer, BLOCK) and the RED repair in `notes.md`. No record of the main agent's own RED review exists in the ledger or in the commit messages.
   → Wrong outcome: none on the grammar. M5 and M6 above confirm the repair. The pipeline evidence for step 4 is incomplete.
   → Smallest test: the main agent adds one line to `notes.md` with its RED review result, or states that it did not do one.

## Task against `spec.md`

- **[Verified]** Forms 1 to 8 parse and highlight. Items 6 and 7 get class `c`.
- **[Verified]** Exclusions hold: no change to `main.rs`, no `fmt`, no generics, no guards.
- **[Verified]** Existing validation passes: 17 old corpus examples, 4 `:error` cases, 69 old assertions, wiki lint, slice 5 syntax test (TEST).
- **[Verified]** No added machinery. The grammar diff is 4 edits; the query diff is 2 predicates and 1 shared block. The old uppercase `call name:` pattern is deleted, not duplicated.
- **[Verified]** README items of the plan are open for the docs phase (GREEN decision). `spec.md` does not list them in its pass rule.
- **[Verified]** EVENT: the grammar edits reached `main` in `4a691ec7`, a commit for slice 6b. Recorded in `notes.md` TEST. The content is the same as the reviewed diff.

## Pipeline evidence

- **[Verified]** Genuine RED: `red-output.log` Run 1 (4 corpus examples fail on ERROR nodes), Run 2 and RED REPAIR Run 4 (7 of 11 assertions fail alone, 4 guards pass). Run 0 is a recorded setup fault, not RED.
- **[Verified]** Fresh RED review: `red-review.md`, BLOCK on objection 1, answered by the RED repair.
- **[Verified]** GREEN and TEST: counts, hashes and commands are the same in `notes.md`, `green-output.log`, `test-output.log`, `test-result.json` and my run.

## Deliberately not challenged

- Signed integer patterns: no decision names them. DL-092 uses only `0`.
- 6 old assertions on the last token of a line in `forms.beaml` and `lexer.beaml`: earlier slices, not this diff.
- `preview.py` maps `number` to class `c`: earlier code. The highlight tests, not the preview, decide the class.

## Not inspected

- Zed itself. The content of `proposal-lite.md` and `proposal-ultra.md` beyond the selection in `notes.md` Solve.

## Decisions

| Class | Choice | Alternative | Reason |
|---|---|---|---|
| Undo | Verdict PASS | BLOCK | No critical or high objection. |
| Undo | Accept DL-088 and DL-093 inputs in the grammar | Ask for grammar rejection | Both decisions name a compile error, and `spec.md` excludes these checks. |
| Undo | Mutations in a scratch copy, cache rebuilt from the repository after | Edit the repository files | No change to the target. RED review note 2. |
| Undo | WASM note as medium | High | Size and commit history point to a new build. No observed wrong outcome. |
| Undo | Zed note as medium | High | CLI evidence on the same engine. No double capture in the files. |
| Undo | Drop signed integers and old unanchored assertions | Raise them | No decision or no change in this slice. |
