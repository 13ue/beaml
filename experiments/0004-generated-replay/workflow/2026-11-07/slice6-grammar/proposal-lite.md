# Proposal LITE: slice 6a grammar

**[Proposal]** PONYTAIL LITE, 2026-11-07. This file changes no production file.
LITE builds every required form and every boundary check. Each step names a smaller option in one line. The OWNER or the decision phase chooses.

## Evidence of this proposal

- **[Verified]** All steps ran in a scratch copy with CLI 0.26.5 (`/private/tmp/beaml-zed-highlighting/tools/tree-sitter`).
- **[Verified]** RED: the new tests on the current grammar give 18/23 corpus parses. 5 new examples fail.
- **[Verified]** GREEN: `generate` gives no conflict. `test` gives 23/23 corpus and 4/4 highlight files (15 new assertions). `test --wasm` gives 23/23.
- **[Verified]** `parse -q` exits 0 for the 3 `preview.py` `DEFAULT` sources and for the new highlight file.
- **[Unknown]** `preview.py --chat` and `build --wasm` did not run here. `preview.py` uses `npx`, which can download the CLI.

## Step 1: RED corpus test

Create `test/corpus/constructors.txt` with 6 examples. Write each expected tree by hand from `grammar.js`. Do not copy parser output without a review.

Inputs (one example per block):

```
enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }

enum PaymentState { Authorized  Declined(DeclineReason)  Unknown(String) }
fn PaymentState status: String, decline_reason: String -> PaymentState
fn PaymentState "ok", _ -> PaymentState = Authorized
fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined
fn PaymentState other, _ -> PaymentState = Unknown(other)

type NonZeroInt { value: Int }
fn NonZeroInt n: Int -> NonZeroInt ! IsZero
fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}
fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }

fn f x: String -> String ! String = x
fn h x: String -> String ! Int | Timeout

fn g p: P -> R = build(p |> prepare, x)

effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder
```

- The ENUM LITERALS and the constructor are in two enums. DL-088 forbids both on one enum. The corpus stays clean.
- The "Overlap" example also holds a signature line with `! E | F`. So it is RED today.
- Expected RED today: 5 of 6 fail. "Pipe inside an argument" passes; it is a guard.

The full file with the expected trees is in the appendix (250 lines).

→ Smaller option: one example per DL form, without the guard examples. Not proposed: the guards catch a regression.

## Step 2: RED highlight test

Create `test/highlight/constructors.beaml` (appendix, 22 lines, 15 assertions).

- `constructor`: enum literal name, `fn PaymentState`, bare `Authorized`, pipe steps `DeclineReason` and `Declined`, `Pending` as call argument, `Pending` in `add` (plan-review note 3).
- `function`: lowercase `fn g` and pipe step `prepare`. These make a broken predicate pair visible in the new file.
- `string`, `number`, `operator`, `keyword`, `property` (`card_holder` after `with`).

## Step 3: GREEN grammar.js

```diff
--- a/grammar.js
+++ b/grammar.js
@@ -35,7 +35,10 @@
       seq("enum", field("name", $.type), "{", repeat(seq($.variant_declaration, optional(","))), "}"),
 
     variant_declaration: ($) =>
-      seq($.constructor, optional(seq(token.immediate("("), optional(commaList($.type)), ")"))),
+      seq(
+        $.constructor,
+        optional(choice(seq(token.immediate("("), optional(commaList($.type)), ")"), seq("=", $.string))),
+      ),
 
     // `effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")` (DL-013, DL-015).
     effect_declaration: ($) =>
@@ -48,6 +51,8 @@
         optional($.failures),
         "=",
         field("body", $._expression),
+        // Redaction release (DL-089).
+        optional(seq("with", commaList($.property))),
       ),
 
     // MIGRATE CHAIN step: `migrate Payment v1 -> v2 { ... }` (DL-022, DL-072). A plain number is no VERSION (DL-074).
@@ -83,8 +88,8 @@
         "->",
         field("return_type", $.type),
         optional($.failures),
-        "=",
-        field("body", $._expression),
+        // A signature line has no body (DL-084).
+        optional(seq("=", field("body", $._expression))),
       ),
 
     // `! A | B` failure TYPES (DL-015).
@@ -97,7 +102,7 @@
     qualified_name: ($) => seq($.identifier, repeat1(seq(token.immediate("."), $.identifier))),
 
     _expression: ($) =>
-      choice($.identifier, $.qualified_name, $.string, $.call, $.record, $.concatenation, $.pipe, $.with_expression),
+      choice($.identifier, $.qualified_name, $.string, $.integer, $.call, $.record, $.concatenation, $.pipe, $.with_expression),
 
     call: ($) =>
       seq(field("name", $._name), token.immediate("("), optional(commaList($._expression)), ")"),
```

- The variant uses `choice`: a variant has a payload or a literal, not both.
- → Smaller option: `optional(seq("=", $.string))` after the payload. Then `Unknown(String) = "x"` parses; the compiler must reject it.
- The redaction release is an inline `seq` with no new node. `(property)` already gets `@property`.

## Step 4: GREEN highlights.scm

```diff
--- a/languages/beaml/highlights.scm
+++ b/languages/beaml/highlights.scm
@@ -17,13 +17,34 @@
 (type) @type
 (constructor) @constructor
 (property) @property
-(function_clause name: (identifier) @function)
+((function_clause name: (identifier) @constructor)
+ (#match? @constructor "^[A-Z]"))
+((function_clause name: (identifier) @function)
+ (#not-match? @function "^[A-Z]"))
 (effect_declaration name: (_) @function)
 (retire_declaration name: (_) @function)
-(pipe right: (identifier) @function)
+((pipe right: (identifier) @constructor)
+ (#match? @constructor "^[A-Z]"))
+((pipe right: (identifier) @function)
+ (#not-match? @function "^[A-Z]"))
 (pipe right: (qualified_name) @function)
 ((call name: (identifier) @constructor)
  (#match? @constructor "^[A-Z]"))
 ((call name: (identifier) @function)
  (#not-match? @function "^[A-Z]"))
 (call name: (qualified_name) @function)
+; Bare variants in expression positions (DL-082, DL-086). Not on (type (identifier)).
+([
+  (function_clause body: (identifier) @constructor)
+  (effect_declaration body: (identifier) @constructor)
+  (add_operation value: (identifier) @constructor)
+  (pipe left: (identifier) @constructor)
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

- Every pattern on `function_clause name:` and `pipe right: (identifier)` is in a `#match?` / `#not-match?` pair (plan-review note 2). The pairs exclude each other, so the capture order in Zed does not matter.
- The alternation shares one `#match?` predicate. `(type (identifier))` is not in the list.
- `(call (identifier))` also matches the call name. An uppercase name gets `@constructor` from both patterns. This is the same class, so there is no conflict.
- → Smaller option: no alternation, one line per parent with its own predicate (11 patterns). Same result, about 20 more lines.
- **[Unknown]** Zed was not run. If Zed rejects a predicate on an alternation, use the smaller option above.

## Step 5: README

Add one list item under "forms of the decision log":

```md
- ENUM LITERALS `Authorized = "ok"`, constructor clauses and signature lines without a body, record constructors, `! E` on a constructor, constructors as pipe steps, and `with field` after an `effect` (DL-082 to DL-093). The DL-085, DL-087, DL-088, DL-092 and DL-093 rules are compiler checks.
```

## Checks

Run from `integrations/zed-beaml`:

```sh
TS=/private/tmp/beaml-zed-highlighting/tools/tree-sitter
$TS generate --abi 15 --js-runtime native       # no conflict output
$TS test                                         # 23/23 corpus, 4/4 highlight files
$TS test --wasm                                  # 23/23
$TS parse --wasm -q ../../experiments/0001-syntax-to-beam/example.beaml
for f in ../../experiments/0002-http-correlation/apps/orders_api/priv/orders.beaml \
         ../../experiments/0002-http-correlation/apps/payments_api/priv/payments.beaml \
         ../../experiments/0001-syntax-to-beam/example.beaml; do $TS parse -q "$f" || echo "FAIL $f"; done
$TS build --wasm -o grammars/beaml.wasm
cd ../.. && python3 integrations/zed-beaml/preview.py --chat integrations/zed-beaml/test/highlight/constructors.beaml
```

Boundary checks (plan-review notes 1 and 2). Each command must print nothing:

```sh
# Note 1: no MISSING or ERROR node in the expected trees or in a fresh parse.
rg -n 'ERROR|MISSING' test/corpus/constructors.txt
$TS parse test/highlight/constructors.beaml 2>/dev/null | rg 'ERROR|MISSING'
# Note 2: no unpredicated pattern on function_clause name or pipe right.
rg -n '^\((function_clause name|pipe right): \(identifier\)' languages/beaml/highlights.scm
```

- `errors.txt` keeps its `:error` cases. `tree-sitter test` covers them.
- `preview.py --chat` must show class `c` on `PaymentState`, `Authorized`, `DeclineReason`, `Declined` and `Pending`.
- If `npx` must download the CLI, record a blocker. Do not download without OWNER approval.
- If the `/private/tmp` binary is gone, record a blocker.

## Size

| File | Lines |
|---|---|
| `grammar.js` | +8 / −3 |
| `highlights.scm` | +27 / −2 |
| `test/corpus/constructors.txt` | +250 (new, mostly trees) |
| `test/highlight/constructors.beaml` | +22 (new) |
| `README.md` | +1 |
| `src/*`, `grammars/beaml.wasm` | generated |

Hand-written total: about 310 lines, of which about 40 are grammar and query lines.

## Exclusions

As in `spec.md`: no `main.rs`, no `beaml fmt`, no semantic checks, no generics, no guards. `preview.py` does not change.

## Appendix A: test/corpus/constructors.txt

SHA-256 of the scratch version: `6d85ba79e6cc76b2bdcbadc0e046493a7d92136bf19c674af8c2a9fc4e11a22b`.

```
==================
Enum literals
==================

enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }

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
        (identifier)))))

==================
Enum constructor with signatures and clauses
==================

enum PaymentState { Authorized  Declined(DeclineReason)  Unknown(String) }
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
        (identifier)))
    (variant_declaration
      (constructor
        (identifier))
      (type
        (identifier)))
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

==================
Record constructor with a failure TYPE
==================

type NonZeroInt { value: Int }
fn NonZeroInt n: Int -> NonZeroInt ! IsZero
fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}
fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }

---

(source_file
  (type_declaration
    (type
      (identifier))
    (field_declaration
      (property
        (identifier))
      (type
        (identifier))))
  (function_clause
    (identifier)
    (parameter
      (identifier)
      (type
        (identifier)))
    (type
      (identifier))
    (failures
      (type
        (identifier))))
  (function_clause
    (identifier)
    (parameter
      (integer))
    (type
      (identifier))
    (failures
      (type
        (identifier)))
    (record
      (type
        (identifier))))
  (function_clause
    (identifier)
    (parameter
      (identifier)
      (type
        (identifier)))
    (type
      (identifier))
    (failures
      (type
        (identifier)))
    (record
      (type
        (identifier))
      (record_field
        (property
          (identifier))
        (identifier)))))

==================
Overlap is no grammar error
==================

fn f x: String -> String ! String = x
fn h x: String -> String ! Int | Timeout

---

(source_file
  (function_clause
    (identifier)
    (parameter
      (identifier)
      (type
        (identifier)))
    (type
      (identifier))
    (failures
      (type
        (identifier)))
    (identifier))
  (function_clause
    (identifier)
    (parameter
      (identifier)
      (type
        (identifier)))
    (type
      (identifier))
    (failures
      (type
        (identifier))
      (type
        (identifier)))))

==================
Pipe inside an argument
==================

fn g p: P -> R = build(p |> prepare, x)

---

(source_file
  (function_clause
    (identifier)
    (parameter
      (identifier)
      (type
        (identifier)))
    (type
      (identifier))
    (call
      (identifier)
      (pipe
        (identifier)
        (identifier))
      (identifier))))

==================
Effect releases a redacted field
==================

effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder

---

(source_file
  (effect_declaration
    (qualified_name
      (identifier)
      (identifier))
    (type
      (identifier))
    (type
      (identifier))
    (failures
      (type
        (identifier)))
    (call
      (qualified_name
        (identifier)
        (identifier))
      (string))
    (property
      (identifier))))
```

## Appendix B: test/highlight/constructors.beaml

SHA-256 of the scratch version: `5e1b4e385bc0cf8748528736f9b3288ff6616c6009098fc0c668408b32ebd4bb`.

```
enum PaymentState { Authorized = "ok"  Pending = "pending" }
//                  ^ constructor
//                               ^ string
fn PaymentState "ok", _ -> PaymentState = Authorized
// <- keyword
// ^ constructor
//                                        ^ constructor
fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined
//                                                             ^ constructor
//                                                                              ^ constructor
fn g p: P -> R = build(p |> prepare, Pending)
// ^ function
//                          ^ function
//                                   ^ constructor
fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}
//            ^ number
//                            ^ operator
migrate Payment v1 -> v2 { add state: PaymentState = Pending }
//                                                   ^ constructor
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder
//                                                                                          ^ keyword
//                                                                                               ^ property
```
