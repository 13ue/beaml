# Proposal ULTRA: slice 6a grammar

**[Proposal]** PONYTAIL ULTRA, 2026-11-07. This file changes no production file.

## Stance

- 4 grammar edits. Each edit is one `optional` or one `choice` item.
- 1 query block for all uppercase constructor positions. It replaces one old pattern.
- No new node, no new capture name, no change to `preview.py`.
- Delete before add: the old `(call name: (identifier) @constructor)` pattern goes. The new block covers it.

## Probe evidence

**[Verified]** Scratch copy of `integrations/zed-beaml/` with the diffs below. CLI `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` 0.26.5.

- `generate --abi 15 --js-runtime native` exits 0, no conflict.
- `test`: 17/17 corpus, 3/3 highlight files (69 assertions) still pass.
- `parse` of all 13 in-scope lines: 0 `ERROR`, 0 `MISSING`. `parse -q` exits 0.
- The 3 `preview.py` `DEFAULT` sources: `parse -q` exits 0.
- `query highlights.scm`: `constructor` on `fn PaymentState`, `fn NonZeroInt`, body `Authorized`, pipe steps `DeclineReason` and `Declined`, `add … = Pending`. `property` on `card_holder`. `function` stays on `g`, `f`, `h`, `build`, `prepare`, `http.post`, `payments.authorize`. No uppercase name has a `function` capture.
- **[Unknown]** `test --wasm`, `build --wasm` and `preview.py --chat` were not run in the probe.

## Step 1: RED corpus test

Create `integrations/zed-beaml/test/corpus/constructors.txt`. The first example is the RED test. Write the expected tree by hand from the grammar rules. Do not paste parser output.

```
==================
Enum constructor with signatures and clauses
==================

enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }
fn PaymentState status: String, decline_reason: String -> PaymentState
fn PaymentState "ok", _ -> PaymentState = Authorized
fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined
fn PaymentState other, _ -> PaymentState = Unknown(other)

---

(source_file
  (enum_declaration
    (type
      (identifier))
    (variant_declaration
      (constructor
        (identifier))
      (string))
    (variant_declaration
      (constructor
        (identifier))
      (string))
    (variant_declaration
      (constructor
        (identifier))
      (type
        (identifier))))
  (function_clause
    (identifier)
    (parameter
      (identifier)
      (type
        (identifier)))
    (parameter
      (identifier)
      (type
        (identifier)))
    (type
      (identifier)))
  (function_clause
    (identifier)
    (parameter
      (string))
    (parameter
      (identifier))
    (type
      (identifier))
    (identifier))
  (function_clause
    (identifier)
    (parameter
      (string))
    (parameter
      (identifier))
    (type
      (identifier))
    (pipe
      (pipe
        (identifier)
        (identifier))
      (identifier)))
  (function_clause
    (identifier)
    (parameter
      (identifier))
    (parameter
      (identifier))
    (type
      (identifier))
    (call
      (identifier)
      (identifier))))
```

Add these examples to the same file, same RED phase. Each example has its own expected tree.

1. "Record constructor with a failure TYPE": `type NonZeroInt { value: Int }`, `fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}`, `fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }`. RED: integer pattern.
2. "Signature with several failure TYPES": `fn h x: String -> String ! Int | Timeout`. RED: no body.
3. "Overlap is no grammar error": `fn f x: String -> String ! String = x`. Guard, passes today.
4. "Pipe inside an argument": `fn g p: P -> R = build(p |> prepare, x)`. Guard, passes today.
5. "Effect releases a redacted field": `effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder`. RED: `ERROR` at `with`.

**[Note]** DL-088 forbids ENUM LITERALS and a constructor on one enum. That is a compiler check. The RED example keeps the DL-082 text word for word.

## Step 2: RED highlight test

**[Verified]** With the GREEN diffs in a scratch copy, this file passes (11 assertions). The Step 1 example also passes there.

Create `integrations/zed-beaml/test/highlight/constructors.beaml`. Use the column-caret form of `forms.beaml`.

```
enum PaymentState { Authorized = "ok"  Unknown(String) }
//                  ^ constructor
//                               ^ string
fn PaymentState "ok", _ -> PaymentState = Authorized
// <- keyword
// ^ constructor
//                                        ^ constructor
fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined
//                                                             ^ constructor
//                                                                              ^ constructor
fn g p: P -> R = build(p |> prepare, x)
// ^ function
//                          ^ function
effect payments.authorize Order -> Payment = http.post("payments/authorize") with card_holder
//                                                                                ^ property
migrate Payment v3 -> v4 { add state: PaymentState = Pending }
//                                                   ^ constructor
```

The worker checks each caret column against its line before RED. RED: `function` on `fn PaymentState`, no class on `Authorized` and `Pending`, `function` on the pipe steps, no `property` (`ERROR`) on `card_holder`.

Run the RED check. Record the failing output in the gate ledger.

```sh
cd integrations/zed-beaml
TS=/private/tmp/beaml-zed-highlighting/tools/tree-sitter
$TS test
```

## Step 3: GREEN, `grammar.js`

```diff
     variant_declaration: ($) =>
-      seq($.constructor, optional(seq(token.immediate("("), optional(commaList($.type)), ")"))),
+      seq(
+        $.constructor,
+        optional(choice(seq(token.immediate("("), optional(commaList($.type)), ")"), seq("=", $.string))),
+      ),
@@ effect_declaration
         optional($.failures),
         "=",
         field("body", $._expression),
+        optional(seq("with", commaList($.property))),
       ),
@@ function_clause
         field("return_type", $.type),
         optional($.failures),
-        "=",
-        field("body", $._expression),
+        optional(seq("=", field("body", $._expression))),
       ),
@@ _expression
-      choice($.identifier, $.qualified_name, $.string, $.call, $.record, $.concatenation, $.pipe, $.with_expression),
+      choice($.identifier, $.qualified_name, $.string, $.integer, $.call, $.record, $.concatenation, $.pipe, $.with_expression),
```

- `choice` in `variant_declaration`: a variant has a payload or a literal, not both (DL-082).
- Update the comments on `effect_declaration` (DL-089) and `function_clause` (DL-084: a signature is a clause without a body).

## Step 4: GREEN, `highlights.scm`

```diff
-(function_clause name: (identifier) @function)
+((function_clause name: (identifier) @function)
+ (#not-match? @function "^[A-Z]"))
 (effect_declaration name: (_) @function)
 (retire_declaration name: (_) @function)
-(pipe right: (identifier) @function)
+((pipe right: (identifier) @function)
+ (#not-match? @function "^[A-Z]"))
 (pipe right: (qualified_name) @function)
-((call name: (identifier) @constructor)
- (#match? @constructor "^[A-Z]"))
 ((call name: (identifier) @function)
  (#not-match? @function "^[A-Z]"))
 (call name: (qualified_name) @function)
+; Uppercase identifiers in name and expression positions are constructors and variants (DL-082, DL-086).
+([
+  (function_clause (identifier) @constructor)
+  (effect_declaration body: (identifier) @constructor)
+  (add_operation value: (identifier) @constructor)
+  (pipe (identifier) @constructor)
+  (call (identifier) @constructor)
+  (record_field (identifier) @constructor)
+  (parameter (identifier) @constructor)
+  (concatenation (identifier) @constructor)
+  (with_expression body: (identifier) @constructor)
+  (with_clause (identifier) @constructor)
+  (else_arm (identifier) @constructor)
+ ]
+ (#match? @constructor "^[A-Z]"))
```

- Each item matches a direct child `identifier` only. `(type (identifier))` and `(property (identifier))` are grandchildren, so they never match.
- `function_clause` without a field covers the name and a bare body. `pipe` without a field covers both sides. `call` covers the name and the arguments.
- `effect_declaration` keeps the `body:` field. An uppercase effect name stays `function`.
- Plan-check low note: `add_operation value:` is in the list.
- **[Unknown]** Zed applies the shared predicate to every alternative, as the CLI does. Fallback: split the block into 11 patterns, each with its own `#match?`. Do this only if Zed shows a wrong class.

## Plan-check notes

**Medium 1, MISSING nodes.** The rule fails on `ERROR` and on `MISSING`:

```sh
rg -n 'ERROR|MISSING' test/corpus/constructors.txt                   # must print nothing
$TS parse test/highlight/constructors.beaml | rg 'ERROR|MISSING'     # must print nothing
```

- The highlight file holds the new forms. The `parse | rg` check covers them without per-example scratch files.
- `tree-sitter test` also fails if the hand-written tree differs from the parser tree. A hand-written tree has no `MISSING` node.
- Also run the `parse | rg` check on a scratch file with the 5 extra corpus inputs.

**Medium 2, predicates.** Every pattern on `function_clause name:` and `pipe right: (identifier)` has a predicate. Check:

```sh
rg -n 'function_clause|pipe' languages/beaml/highlights.scm
```

- Each hit has `#match?` or `#not-match?` on its own line or the next line. The block shares one `#match?`.
- `@function` and `@constructor` on one node are exclusive (`^[A-Z]` vs. not). The capture order in Zed has no effect.

## Step 5: checks

```sh
cd integrations/zed-beaml
TS=/private/tmp/beaml-zed-highlighting/tools/tree-sitter
$TS generate --abi 15 --js-runtime native        # exit 0, no conflict
$TS test                                         # all corpus and highlight tests, incl. errors.txt
$TS test --wasm
for f in ../../experiments/0001-syntax-to-beam/example.beaml \
         ../../experiments/0002-http-correlation/apps/orders_api/priv/orders.beaml \
         ../../experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml; do
  $TS parse --wasm -q "$f" || exit 1
done
$TS parse test/highlight/constructors.beaml | rg 'ERROR|MISSING' && exit 1
rg -n 'ERROR|MISSING' test/corpus/constructors.txt && exit 1
$TS build --wasm -o grammars/beaml.wasm
cd ../.. && python3 integrations/zed-beaml/preview.py --chat integrations/zed-beaml/test/highlight/constructors.beaml
```

- `preview.py` output: `class="c"` on `PaymentState`, `Authorized`, `DeclineReason`, `Declined`, `Pending`.
- `preview.py` calls `npx -y tree-sitter-cli@0.26.5`. If `npx` needs a download and that is blocked, record a blocker. Do not download a CLI without OWNER approval.
- If the binary in `/private/tmp` is gone, record a blocker.

## Step 6: README

Add one list item per new form to `integrations/zed-beaml/README.md`: ENUM LITERALS, signature lines, integer patterns, effect `with` release, uppercase constructor highlight.

## Size estimate

| File | Lines |
|---|---|
| `grammar.js` | +7 / −3 |
| `highlights.scm` | +19 / −4 |
| `test/corpus/constructors.txt` (new) | ~230 |
| `test/highlight/constructors.beaml` (new) | ~20 |
| `README.md` | +5 |
| `src/*`, `grammars/beaml.wasm` | generated |

Hand-written total: about 290 lines, of which about 30 lines are grammar and query.

## Skipped

- No new `variant_literal` node: `(variant_declaration (constructor) (string))` is enough. Add a node when the compiler needs a field name.
- No field on `call` arguments: `(call (identifier))` with `^[A-Z]` is enough.
- No lowercase-variable class: out of scope.
