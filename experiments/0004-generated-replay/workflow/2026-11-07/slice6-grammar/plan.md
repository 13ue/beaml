# Plan: slice 6a grammar

**[Proposal]** PLAN phase, 2026-11-07. Changes only task records.

## Toolchain

- **[Verified]** `tree-sitter` is not on PATH.
- **[Verified]** `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` is CLI 0.26.5, the version in the README.
- **[Verified]** Baseline in a scratch copy: 17/17 corpus parses pass, 3 highlight files pass (69 assertions).
- **[Unknown]** `preview.py` calls `npx -y tree-sitter-cli@0.26.5`. The PLAN phase did not run it (tool permission denied). A later phase must run it or record the blocker.
- **[Risk]** `/private/tmp` is temporary. If the binary is gone, record a blocker. Do not download a new CLI without OWNER approval.

## Probe of the current grammar

**[Verified]** One line per form, `tree-sitter parse` in a scratch copy:

| Form | Today |
|---|---|
| ENUM LITERALS `Authorized = "ok"` | ERROR |
| Signature line without `= body` | ERROR |
| Integer pattern `fn NonZeroInt 0 -> …` | ERROR |
| `effect … = http.post(…) with card_holder` | ERROR |
| Constructor clause `fn PaymentState "ok", _ -> … = Authorized` | parses |
| `fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }` | parses |
| `-> String ! Int \| Timeout` on `fn` | parses |
| Pipe inside an argument `build(p \|> prepare, x)` | parses |

**[Verified]** Highlight gaps today:

- `fn PaymentState` name shows `function`, not `constructor`.
- Pipe steps `DeclineReason`, `Declined` show `function`.
- Bare `Authorized` as a body has no class.

## Affected files

- `integrations/zed-beaml/grammar.js`: rules `variant_declaration`, `function_clause`, `effect_declaration`, `_expression`.
- `integrations/zed-beaml/src/` (`grammar.json`, `node-types.json`, `parser.c`): generated, do not edit by hand.
- `integrations/zed-beaml/languages/beaml/highlights.scm`.
- `integrations/zed-beaml/test/corpus/constructors.txt` (new).
- `integrations/zed-beaml/test/highlight/constructors.beaml` (new).
- `integrations/zed-beaml/grammars/beaml.wasm`: rebuilt.
- `integrations/zed-beaml/README.md`: one list item per new form.
- `preview.py`: no change expected. The `SHORT` map already maps `constructor` to `c`. Change it only if a new capture name appears.

Callers: Zed loads `grammars/beaml.wasm` and `highlights.scm`. `preview.py` uses the queries through `tree-sitter highlight`. No compiler code uses this grammar.

## First failing test (RED)

New file `test/corpus/constructors.txt`, first example "Enum constructor with signatures and clauses":

```
enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }
fn PaymentState status: String, decline_reason: String -> PaymentState
fn PaymentState "ok", _ -> PaymentState = Authorized
fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined
fn PaymentState other, _ -> PaymentState = Unknown(other)
```

Expected: a full tree with no ERROR node. RED today: ERROR on the literal `=` and on the signature line (observed in the probe).

**[Note]** Mixing ENUM LITERALS and a constructor for one enum is a compile error (DL-088). The grammar test may still hold both: the grammar does not check DL-088. A worker may split the example into two enums to keep the corpus clean.

Further corpus examples (same RED phase, same file):

- "Record constructor with a failure TYPE": `type NonZeroInt { value: Int }`, `fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}`, `fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }`. RED: integer pattern.
- "Overlap is no grammar error": `fn f x: String -> String ! String = x`. Passes today; it guards against a grammar-level overlap check.
- "Pipe inside an argument": `fn g p: P -> R = build(p |> prepare, x)`. Passes today; keeps DL-086 covered.
- "Effect releases a redacted field": the DL-089 line. RED: ERROR at `with`.

Highlight RED: `test/highlight/constructors.beaml` asserts `constructor` on `fn PaymentState`, on `Authorized` as a body, on `DeclineReason` and `Declined` as pipe steps, and `property` on `card_holder` after `with`. Lowercase pipe steps keep `function` (the existing `forms.beaml` assertions cover that).

## Minimal changes (direction for the proposals)

1. `variant_declaration`: add `optional(seq("=", $.string))`.
2. `function_clause`: make `seq("=", field("body", …))` optional. A signature line is a clause without a body.
3. `_expression`: add `$.integer`.
4. `effect_declaration`: add `optional(seq("with", commaList($.property)))` after the body.
5. `highlights.scm`:
   - `function_clause name:` uppercase gives `@constructor`, lowercase keeps `@function` (`#match?` / `#not-match?` pair).
   - `pipe right: (identifier)`: same pair.
   - Bare uppercase `identifier` in expression positions gives `@constructor`. List the parent fields: function body, pipe left, call argument, record field value, parameter, with clause, else arm, concatenation.
   - Do not use a pattern on every `identifier`: `(type (identifier))` would then also match.

**[Unknown]** Zed and the tree-sitter CLI may resolve two captures on one node in a different order. Use exclusive predicate pairs, so the order does not matter.

## Checks

```sh
cd integrations/zed-beaml
TS=/private/tmp/beaml-zed-highlighting/tools/tree-sitter
$TS generate --abi 15 --js-runtime native
$TS test
$TS test --wasm
$TS parse --wasm -q ../../experiments/0001-syntax-to-beam/example.beaml
$TS build --wasm -o grammars/beaml.wasm
cd ../.. && python3 integrations/zed-beaml/preview.py --chat integrations/zed-beaml/test/highlight/constructors.beaml
```

Also parse the experiment sources in `preview.py` `DEFAULT` with `-q`. They must stay free of ERROR nodes.

## Test-first

**[Proposal]** Test-first applies. Parsing and highlight captures are behavior. Corpus and highlight tests fail before the grammar change and pass after it.

## Exclusions

See `spec.md`. Also: no change to `main.rs`, no `beaml fmt`, no generics, no guards.

## Open questions for the OWNER

None. All forms are recorded in DL-082 to DL-093.
