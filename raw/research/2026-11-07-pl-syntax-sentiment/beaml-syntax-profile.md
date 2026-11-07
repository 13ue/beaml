---
title: BEAML syntax profile (current surface and design intents)
status: temporary research, not ingested into wiki
date: 2026-11-07
---

# BEAML syntax profile

Purpose: give the synthesis worker an accurate, cited picture of what BEAML source looks like today and why. Every snippet names its file. [Verified] = quoted from a committed file. [Proposal] = from a sketch or concept page, not grammar. [Unknown] = not found in the KB.

Two syntax layers exist and do not agree fully:

- The compiler in [experiments/0001-syntax-to-beam/src/main.rs](../../../experiments/0001-syntax-to-beam/src/main.rs) (also used by EXPERIMENT 0004) parses `type`, `enum`, `fn`, `effect`, `migrate`, `retire`, `redacted`, `|>`, `!`, `with <field>` and literals. It does not parse `with ... do ... else ... end`.
- The Tree-sitter grammar in [integrations/zed-beaml/grammar.js](../../../integrations/zed-beaml/grammar.js) parses the same forms plus `with ... do ... else ... end` (keywords decided in DL-014; clause shapes "tolerant", see grammar comment).

The historical PDF specification ([wiki/sources/engineering-spec-v0.5.md](../../../wiki/sources/engineering-spec-v0.5.md), S02) sketched a different surface (`function`, `class`, `newtype`, `trait`, `impl`, `import`, `<T>` generics, `! {llm, network}` effect sets). None of that is built; the owner's 2026-11-05 syntax spike replaced it as the working surface ([syntax spike requirement](../../../wiki/sources/syntax-spike-requirement.md)).

## 1. What BEAML looks like today

### 1.1 Record TYPE, nested TYPES, no field separators required [Verified]

[experiments/0001-syntax-to-beam/example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml) lines 1-9. Fields are `name: Type`, newline-separated; commas are optional ([grammar.js](../../../integrations/zed-beaml/grammar.js) `_field_block`). Exact records: construction needs every field, rejects extras ([0001 README](../../../experiments/0001-syntax-to-beam/README.md), "Supported experimental contract").

```beaml
type Address {
  city: String
  country: String
}

type Customer {
  name: String
  address: Address
}
```

### 1.2 Variants with `enum`, payload in parentheses [Verified]

[example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml) lines 16-25. `enum` for variants, `type` for records (DL-061). Constructor names are globally unique in the 0001 subset. Note: in 0001 even zero-argument variants need `()`; later fixtures write bare `Pending` (see 1.3).

```beaml
enum OrderError {
  NotFound(String)
  Rejected(String)
}

enum OrderResult {
  Ok(Order)
  Error(OrderError)
}
```

### 1.3 ENUM LITERALS and the KEEP-VALUE VARIANT [Verified]

[experiments/0004-generated-replay/slice6/enum/literals.beaml](../../../experiments/0004-generated-replay/slice6/enum/literals.beaml) lines 2-10. `Authorized = "ok"` binds an outside String 1:1 to a variant (DL-082). `Unknown(String)` keeps a value the decode does not know (DL-062, DL-065). A bare variant is a pattern and an expression (DL-100).

```beaml
enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }

fn label Authorized -> String = "ok"
fn label Pending -> String = "pending"
fn label Unknown(s) -> String = s

fn pending -> PaymentState = Pending
```

### 1.4 Functions as top-level clauses with nested patterns [Verified]

[example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml) lines 34-43. No outer parameter parentheses; parameters separated by commas; `-> Type` on every clause; body after `=`. Record patterns select fields without `..`. First matching clause wins; unreachable clauses are compile errors ([0001 README](../../../experiments/0001-syntax-to-beam/README.md)). String concatenation is `+`.

```beaml
fn describe Ok(Order { id, customer: Customer { name } }) -> String =
  "Bestellung " + id + " von " + name

fn describe Error(NotFound(id)) -> String =
  "Bestellung " + id + " wurde nicht gefunden"

fn send target: String, message: String -> String = target + ": " + message
```

### 1.5 `effect` declaration and the pipe flow [Verified]

[experiments/0004-generated-replay/drift/R/orders.beaml](../../../experiments/0004-generated-replay/drift/R/orders.beaml) lines 6-16. `effect <namespace.operation> <Input> -> <Output> ! <Failure> = <transport>(...)` declares everything that leaves the module (DL-013). The pipe `|>` stops on a failure and passes it on; the failure must appear in the enclosing `!` list (DL-015).

```beaml
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize")

fn prepare Order { order_id } -> Order = Order { order_id: order_id + "" }

fn place order: Order -> Payment ! PaymentError =
  order
  |> prepare
  |> payments.authorize
  |> finish
```

### 1.6 Failure TYPES, record constructor, signature line [Verified]

[experiments/0004-generated-replay/slice6/constructor/nonzero.beaml](../../../experiments/0004-generated-replay/slice6/constructor/nonzero.beaml) lines 1-10. A `fn` named like a `type` is its constructor and the only way in (DL-092). A clause without `= body` is a signature line (DL-084). `! IsZero` is the failure position; success and failure TYPES never overlap (DL-093). Integer literal `0` is a pattern.

```beaml
type IsZero {}
type NonZeroInt { value: Int }

fn NonZeroInt n: Int -> NonZeroInt ! IsZero
fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}
fn NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }

fn wrap n: Int -> NonZeroInt ! IsZero = n |> NonZeroInt
```

### 1.7 Enum constructor with several signatures [Verified]

[experiments/0004-generated-replay/slice6/enum/constructor.beaml](../../../experiments/0004-generated-replay/slice6/enum/constructor.beaml) lines 8-11. Parameter names of the signature line are the wire keys (DL-084); clauses match by position; first match wins (DL-085); constructors and variants are pipe steps (DL-086). `_` is a wildcard.

```beaml
fn PaymentState status: String, decline_reason: String -> PaymentState
fn PaymentState "ok", _ -> PaymentState = Authorized
fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined
fn PaymentState other, _ -> PaymentState = Unknown(other)
```

### 1.8 MIGRATE CHAIN and VERSION MARK [Verified]

[experiments/0004-generated-replay/slice6/fmt/marks.beaml](../../../experiments/0004-generated-replay/slice6/fmt/marks.beaml) lines 3-5 and [slice3/SAR/orders.beaml](../../../experiments/0004-generated-replay/slice3/SAR/orders.beaml) lines 4-6. The `type` is always the newest version; history is `migrate T vA -> vB { rename | add | drop }` (DL-022, DL-023, DL-072). `v3` on the type line is the VERSION MARK (DL-070, DL-080).

```beaml
type Chained v3 { id: String state: String channel: String }
migrate Chained v1 -> v2 { rename status -> state }
migrate Chained v2 -> v3 { add channel: String = "web" }

migrate Payment v1 -> v2 { drop channel: String }
migrate Payment v2 -> v3 { add channel: String = "pre-v2" }
migrate Payment v3 -> v4 { rename channel -> reference }
```

### 1.9 RETIRE LINE [Verified]

[integrations/zed-beaml/test/highlight/forms.beaml](../../../integrations/zed-beaml/test/highlight/forms.beaml) line 39; compiler form in [0004 README, Syntax (slice 4)](../../../experiments/0004-generated-replay/README.md). Releases a deleted EFFECT whose records are still stored (DL-055, DL-057). Unit `days` only.

```beaml
retire payments.authorize keep 30 days
```

### 1.10 `redacted` field and `with` release on an EFFECT [Verified]

[experiments/0004-generated-replay/slice6/redacted/orders_with.beaml](../../../experiments/0004-generated-replay/slice6/redacted/orders_with.beaml) lines 3-7. `redacted` before the field TYPE marks PII (DL-059). An EFFECT loses redacted inputs unless it names them after `with` (DL-089). A `fn` cannot have `with`.

```beaml
type Order { order_id: String card_holder: redacted String }
type Payment { order_id: String status: String }
type PaymentError { reason: String }

effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder
```

### 1.11 `with ... do ... else ... end` [Verified in grammar only]

[integrations/zed-beaml/test/highlight/forms.beaml](../../../integrations/zed-beaml/test/highlight/forms.beaml) lines 45-61. Keywords decided (DL-014): `<-` binds the success value of a failing step, `else` arms are `Pattern -> expr`; the compiler must check `else` exhaustiveness (DL-015, [0004 README owner decisions](../../../experiments/0004-generated-replay/README.md)). Only the Tree-sitter grammar parses it; the compiler does not ([grammar.js](../../../integrations/zed-beaml/grammar.js) comment: "the clause shapes are tolerant"). No committed fixture compiles it.

```beaml
fn place order: Order -> Payment ! PaymentError | Timeout =
  with p <- order |> prepare |> payments.authorize do finish(p) else
    PaymentError { reason } -> fail(reason)
  end
```

### 1.12 Int literals in patterns and expressions [Verified]

[experiments/0004-generated-replay/slice6/int/int.beaml](../../../experiments/0004-generated-replay/slice6/int/int.beaml) lines 4-13. `Int` and `String` are the only primitive TYPES. No arithmetic operator is in the grammar (`+` is concatenation; division is a decided-but-unbuilt form, DL-030).

```beaml
fn f 0 -> String = "zero"
fn f n: Int -> String = "other"

fn size Box { n: 0 } -> String = "empty"
fn size Box { n: _ } -> String = "full"

fn seven -> Int = 7
```

### 1.13 Pipe in argument and field position, precedence [Verified]

[experiments/0004-generated-replay/slice6/pipe/pipe.beaml](../../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml) lines 16-25. `|>` binds weaker than `+`; a pipe in an argument ends at `,` or `)` (D6B-25).

```beaml
fn g p: P, x: String -> R = build(p |> prepare, x)
fn cat a: String, b: String, c: String -> String = join(a + b |> paren, c)
fn box r: String -> Box = Box { note: r, state: r |> paren |> Declined }
```

### 1.14 Comments, strings, escapes; interpolation stays data [Verified]

[example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml) lines 21 and 53; [syntax.beaml](../../../integrations/zed-beaml/test/highlight/syntax.beaml) line 15. `//` line comments only. Strings are `"..."` with `\n \r \t \" \\` escapes. There is no string interpolation: `#{...}` is literal text ([0001 README](../../../experiments/0001-syntax-to-beam/README.md), acceptance 6).

```beaml
// This experiment uses a concrete result type. Generics are a later experiment.
fn literal -> String = "#{raise(\"must stay data\")}: Grüße\n"
```

### 1.15 ENTRY LINE (inbound EFFECT) [Proposal]

Sketch from DL-128, recorded in [decision-log.md](../../../wiki/planning/decision-log.md) and [GLOSSARY.md](../../../GLOSSARY.md) (ENTRY LINE). Form open in [D021](../../../wiki/planning/decisions-to-be-made.md): options `on`, `effect` with body, `entry`, `effect in`.

```beaml
on ui "place" PlaceOrder -> place
```

### 1.16 FATE OPERATIONS in a MIGRATE STEP [Proposal]

[wiki/concepts/migrate-fates.md](../../../wiki/concepts/migrate-fates.md), section 2. Decided as concept (DL-125), "none of this is grammar yet".

```beaml
migrate Payment v2 -> v3 { redact card_holder }
migrate Payment v3 -> v4 { quarantine amount }
migrate Payment v4 -> v5 { retire amount keep 30 days }
migrate Payment v5 -> v6 { map state "pending" -> Declined }
```

### 1.17 Rejected or superseded spellings [Verified]

- `interface Order { ... }` was the record keyword until DL-061; now a hard error with a help line naming `type` (DL-074). Still in [order-flow.beaml](../../../experiments/0004-generated-replay/examples/order-flow.beaml) and 0003 fixtures as history.
- `migrate Payment 1 -> 2` (plain numbers) replaced by `v1 -> v2` (DL-072, DL-074).
- `type AuthorizeOutcome = Authorized(Payment) | Declined(String)` was a D001 option, not taken ([syntax-options.beaml](../../../experiments/0004-generated-replay/syntax-options.beaml) line 69).
- `@effect(...)` attribute and `extern fn` were EXPERIMENT 0004 options A/C, not taken ([syntax-options.beaml](../../../experiments/0004-generated-replay/syntax-options.beaml); owner chose option B, [0004 README](../../../experiments/0004-generated-replay/README.md) "Owner decisions").
- `pii` after the TYPE rejected in favour of `redacted` before it (DL-059).
- `enum E from String { ... }` and `enum E<String>` rejected (DL-062).
- A `fail` keyword rejected; the TYPE alone marks a failure (DL-093).
- `type NonZeroInt(Int)` wrapper form rejected for one `type X { ... }` form (DL-092).

## 2. Design intents stated in the KB

| Intent | Quote (under 15 words) | Page | Tag |
|---|---|---|---|
| Vertical integration, one compiler knows every stage | "BEAML owns the whole path from source to production" | [vertical-integration.md](../../../wiki/concepts/vertical-integration.md) | [Requirement] |
| Goal is fewer agent errors, not human ergonomics first | "so that agents make fewer errors" | [vertical-integration.md](../../../wiki/concepts/vertical-integration.md) | [Requirement] |
| No dynamic escape hatches | "Types persist at runtime. No `any`, no casts." | [vertical-integration.md](../../../wiki/concepts/vertical-integration.md) | [Requirement] |
| Rust-level diagnostics, fast compile | "Rust-level diagnostics, and compile times faster than Go" | [vertical-integration.md](../../../wiki/concepts/vertical-integration.md) | [Requirement] |
| Declarative for shape and policy, expressions for computation | "declarations carry shape and policy, expressions carry computation only" | [decision-log.md DL-126](../../../wiki/planning/decision-log.md) | [Requirement] |
| Every declaration has compiler semantics and an escape hatch | "keeps an expression escape hatch, so it is never magic" | [decision-log.md DL-126](../../../wiki/planning/decision-log.md) | [Requirement] |
| Totality, no crash | "no crash; every value is handled. Only effects carry `!`" | [decision-log.md DL-025](../../../wiki/planning/decision-log.md) | [Requirement] |
| No guessing fallbacks | "no fallback that invents a value" | [decision-log.md DL-028](../../../wiki/planning/decision-log.md) | [Requirement] |
| Loud compile error over silent gap | "a loud compile error over a silent gap" | [decision-log.md DL-116](../../../wiki/planning/decision-log.md) | [Requirement] |
| Left-to-right reading | "a value reads left to right instead of inside out" | [decision-log.md DL-086](../../../wiki/planning/decision-log.md) | [Requirement] |
| Clauses read as a table | "the clauses read as a table" | [decision-log.md DL-083](../../../wiki/planning/decision-log.md) | [Requirement] |
| One spelling per concept | "one spelling for a version everywhere" | [decision-log.md DL-072](../../../wiki/planning/decision-log.md) | [Requirement] |
| One way to build each TYPE | "exactly one way to build each enum from outside data" | [decision-log.md DL-088](../../../wiki/planning/decision-log.md) | [Requirement] |
| Source order is the rule, dead clauses are errors | "with 'first match wins' such a line is dead and misleading" | [decision-log.md DL-087](../../../wiki/planning/decision-log.md) | [Requirement] |
| Failure is a different TYPE, not a flag | "a real failure means something else and deserves its own TYPE" | [decision-log.md DL-093](../../../wiki/planning/decision-log.md) | [Requirement] |
| Privacy structural, declared at the field | "Privacy is structural, not a filter" | [decision-log.md DL-105](../../../wiki/planning/decision-log.md) | [Requirement] |
| Every release of PII visible at the effect | "every release of a redacted value is visible at the effect" | [decision-log.md DL-089](../../../wiki/planning/decision-log.md) | [Requirement] |
| Effects are the only impure thing; constructors pure | "the constructor itself never touches the world" | [decision-log.md DL-120](../../../wiki/planning/decision-log.md) | [Requirement] |
| Replay from source: every outbound call declared | "Everything that leaves this module. Recorded live, substituted in a REPLAY RUN." | [order-flow.beaml](../../../experiments/0004-generated-replay/examples/order-flow.beaml) | [Proposal] |
| Less to write while history is in the source | "less to write while the history is in the source" | [decision-log.md DL-071](../../../wiki/planning/decision-log.md) | [Requirement] |
| Exact records, no remainder marker in patterns | "Select record fields in patterns without a remainder marker" | [raw syntax spike capture](../../../raw/requirements/2026-11-05-syntax-spike.md) | [Requirement] |
| Agent-first tooling, CLI JSON is the agent interface | "The CLI and its JSON output are the agent interface" | [decision-log.md DL-096](../../../wiki/planning/decision-log.md) | [Requirement] |
| Accepts `!` despite Elixir's "raises" meaning | "`!` in a type stays, although Elixir uses `!` in names" | [0004 README, Owner decisions](../../../experiments/0004-generated-replay/README.md) | [Requirement] |
| Not a replacement for Elixir or Gleam; optional constructs not boilerplate | "optional modules, not mandatory boilerplate" | [engineering-spec-v0.5.md S01](../../../wiki/sources/engineering-spec-v0.5.md) | [Requirement] (historical spec) |
| TypeScript familiarity for discoverability (BAML heritage) | "Use TypeScript familiarity for discoverability, but publish an independent grammar" | [baml-language-and-tooling.md](../../../wiki/concepts/baml-language-and-tooling.md) | [Proposal] |
| Explicit effect sets, pure cannot call effectful | "pure functions unable to call effectful functions" | [engineering-spec-v0.5.md S03](../../../wiki/sources/engineering-spec-v0.5.md) | [Requirement] (historical spec) |

Anti-goals touching syntax: no guessing defaults in decode or `migrate` (DL-028); no raw body stored (DL-105); no `fail` keyword (DL-093); no `interface` for records (DL-061); no second constructor form (DL-092, DL-117); no SQL text in source (DL-129); no literal values in compiler output (DL-032, DL-124).

## 3. Syntax decisions already taken

All from [decision-log.md](../../../wiki/planning/decision-log.md) unless noted. Status: closed unless marked.

| ID | Choice (one line) | Status |
|---|---|---|
| Spike 2026-11-05 ([source note](../../../wiki/sources/syntax-spike-requirement.md)) | No outer parameter parentheses; calls and variants use `( , )`; exact records; patterns without `..`; nested top-level clauses | closed |
| DL-013 | One keyword `effect` for everything that leaves a function; `fmt` aligns consecutive effect lines | closed |
| DL-014 | `\|>` and `with ... do ... else ... end` are part of the language | closed (with-form: grammar only) |
| DL-015 | `!` failure TYPES on effects and fns, propagated; `else` exhaustive; Elixir `name`/`name!` pair | closed (`else` check not built) |
| DL-022 | History as `migrate T a -> b { rename, add, drop }`; the `type` is always newest | closed |
| DL-023 | `drop f: Type` names the TYPE | closed |
| DL-028 | No guessing fallback; `Unknown(other)` keeps the value; `add` with a constant allowed | closed |
| DL-030 | Division: `DivByZero` failure TYPE or a non-zero integer TYPE | closed, not built |
| DL-055, DL-057 | `retire <op> keep <n> days` | closed |
| DL-059 | `redacted` before the field TYPE | closed |
| DL-060 | `type` for both records and variants | superseded |
| DL-061 | `type` records, `enum` variants; `interface` reserved for behaviour contracts | closed (D001) |
| DL-062 | `Unknown(String)` is a declared variant; no `from String`, no `<String>` | closed (narrowed by DL-082) |
| DL-065 | Keep-value last branch required only in `migrate` and outside decode | closed |
| DL-070, DL-071, DL-072 | `type Payment v3 { }` VERSION MARK; `v` on every version number | closed |
| DL-074, DL-075 | `interface` and plain version numbers are hard errors with help lines; `v[1-9][0-9]*` | closed |
| DL-080, DL-081, DL-104 | Any agreeing mark is legal; `fmt` normalizes; `fmt` never changes the version | closed |
| DL-082 | ENUM LITERALS `A = "ok"` and an enum constructor `fn E ...` | closed |
| DL-083, DL-114 | `fmt` aligns clause columns; a signature line ends the group | closed |
| DL-084 | Constructor wire keys = parameter names of the signature line | closed |
| DL-085 | First matching signature or clause wins (source order) | closed |
| DL-086 | `\|>` in any expression; constructors and variants as steps | closed |
| DL-087 | Unreachable signature or clause is a compile error | closed |
| DL-088 | Enum with both literals and a constructor is an error | closed |
| DL-089 | `effect ... = transport(...) with field, field` releases redacted fields | closed |
| DL-090, DL-091 | `type NonZeroInt(Int)` wrapper form recorded then withdrawn | withdrawn |
| DL-092 | One `type X { }` form; a same-named `fn` is the constructor and only way in; `!` is a position | closed |
| DL-093 | Success and failure TYPES never overlap; no `fail` keyword | closed |
| DL-098 | Grammar details: signature = clause without body; uppercase names are constructors; `//` comments | closed |
| DL-099, DL-100, DL-101 | Enum constructor reads the field's own value; is decode-only; record constructor runs in decode | closed |
| DL-111 | `redact f` MIGRATE CHANGE | closed as concept, sketch |
| DL-117 | Host call `T.new/1` with one atom-key map | closed (host ABI) |
| DL-120 | A constructor that reaches an EFFECT is a compile error | closed |
| DL-125 | FATE OPERATIONS `redact`, `quarantine`, `retire ... keep`, `map` as declarative lines | closed as concept, not grammar |
| DL-126 | Declarative for shape and policy, expressions for computation | closed (principle) |
| DL-128 | Inbound EFFECT declared in source; sketch `on ui "place" Order -> place` | closed in principle; form open (D021) |
| DL-129 | Fixed transports `db.put`, `db.get`, `db.list` on ordinary `effect` lines; no SQL text | closed |
| 0004 owner decisions 2026-11-06 ([README](../../../experiments/0004-generated-replay/README.md)) | `<-` binds success only; `=` binds a pure step; generated errors are structs; tolerant decode with `unknown_keys` | closed |

## 4. Open syntax questions

From [decisions-to-be-made.md](../../../wiki/planning/decisions-to-be-made.md), [migrate-fates.md](../../../wiki/concepts/migrate-fates.md) and the [0004 README](../../../experiments/0004-generated-replay/README.md).

- D021 (Q6D-1): the form of the ENTRY LINE: `on`, `effect` with body, `entry`, or `effect in`. Open, Migrate.
- D022, D023: generated host function name and decode-reject shape for an entry. Open (host surface).
- D024 (Q6D-4): whether `--stored` reads ENTRY RECORDS. Open.
- D020: whether a MIGRATE STEP governs BEAML-owned persistence. Open.
- DL-125 follow-ups ([migrate-fates.md](../../../wiki/concepts/migrate-fates.md) section 5): final spelling of the four fate operations; nested field paths (`quarantine amount.cents`); duplicate fate lines; two fates on one record.
- DL-082 open note: the call form of a several-argument constructor inside a record constructor is "a sketch, not decided" (DL-099).
- DL-093 open note: generic functions `-> T ! E` need the overlap check at the call; "for later".
- DL-108 open note: a declared reachability form in the signature waits for modules (roadmap part 4).
- DL-126 candidates, concept only: policy on `effect` lines (retry, timeout, idempotent); `where` rules on a TYPE field; examples in source as tests; `keep N days` retention per TYPE.
- Roadmap parts 4 and 5 ([README.md](../../../README.md)): "Decide the module form", "Decide the test syntax". No options recorded.
- 0004 slice 1 Q6, Q7 ([README](../../../experiments/0004-generated-replay/README.md), "Owner questions"): shape of an EFFECT failure TYPE; HTTP target form (`http.post("...")` with config by namespace vs a `target` declaration). [Unknown] whether formally closed; slice 1 default is used throughout.
- Strict `exact interface` form "may come later" (owner decision on tolerant decode, [0004 README](../../../experiments/0004-generated-replay/README.md)).
- DL-104 option B (every `type T { }` means `v1`) deferred to "an own slice".
- RED TEAM 01 ([report](../../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/report.md)) C1, D1: an enum constructor with `!` breaks `--stored`; an enum remap is unchecked. Semantics, not spelling, but they touch the enum forms.

## 5. Feature checklist

| Feature | BEAML status | Evidence |
|---|---|---|
| Pattern matching | present [Verified]: nested constructor, record, String and Int literal patterns in top-level clauses; `_` wildcard; no `case`/`match` expression | [example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml), [int.beaml](../../../experiments/0004-generated-replay/slice6/int/int.beaml); DL-042 notes `Unknown` "needs `enum` and `case`" (not built) |
| Algebraic data types / sum types | present [Verified]: `enum` with payload variants; records via `type`; no generic ADTs | [example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml), DL-061 |
| Null / Option handling | not addressed [Unknown]: no `Option`, `nil` or optional field; `Unknown(String)` is the keep-value idiom; spec S06 required "missing vs explicit null" distinction | [engineering-spec-v0.5.md S06](../../../wiki/sources/engineering-spec-v0.5.md), DL-062 |
| Error handling model | present [Verified]: `-> T ! E1 \| E2` failure position on `fn` and `effect`; pipe stops on failure; generated `{:ok,_}`/`{:error, struct}` and `name!` | DL-015, DL-092, DL-093, [body.beaml](../../../experiments/0004-generated-replay/slice6/failure/body.beaml) |
| Exceptions | rejected [Requirement]: "no crash; every value is handled" (DL-025); host `name!` raises only at the Elixir boundary | DL-025, [0004 README owner decisions](../../../experiments/0004-generated-replay/README.md) |
| Pipe operator | present [Verified]: `\|>` in any expression, weaker than `+` | DL-014, DL-086, [pipe.beaml](../../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml) |
| Immutability / variables | present by omission [Verified]: no assignment, no `let`; bindings only via patterns and parameters; `with p <- ...` binds (grammar only) | [grammar.js](../../../integrations/zed-beaml/grammar.js) `_expression` |
| Type inference extent | minimal [Verified]: every clause declares its return TYPE; variable/wildcard heads need `: Type`; constructor and record patterns fix the input TYPE | [0001 README](../../../experiments/0001-syntax-to-beam/README.md) "Supported experimental contract" |
| Generics | planned [Proposal]: "Generics are deferred, not rejected"; spec S03 lists generics; `-> T ! E` "for later" | [syntax-spike-requirement.md](../../../wiki/sources/syntax-spike-requirement.md), DL-093 |
| Traits / protocols | planned [Proposal] in the historical spec only (`trait`, `impl`, coherent instances); `interface` reserved "for behaviour contracts later" | [engineering-spec-v0.5.md S02, S03](../../../wiki/sources/engineering-spec-v0.5.md), DL-061 |
| Modules / namespaces | planned [Proposal]: "The file system describes modules and namespaces"; roadmap part 4 "Concept"; today one file = one generated Elixir module; effect names are `namespace.operation` | [vertical-integration.md](../../../wiki/concepts/vertical-integration.md), [README.md](../../../README.md), [main.rs](../../../experiments/0001-syntax-to-beam/src/main.rs) `operation_name` |
| Imports | not addressed [Unknown]: spec S02 lists `import`; no form built; `import` only in the reserved-word list | [engineering-spec-v0.5.md S02](../../../wiki/sources/engineering-spec-v0.5.md) |
| String interpolation | rejected for now [Verified]: `#{...}` stays data; concatenation with `+` | [example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml) line 53, [0001 README](../../../experiments/0001-syntax-to-beam/README.md) acceptance 6 |
| Comments / doc comments | present [Verified]: `//` line comments only; no block or doc comment form | [grammar.js](../../../integrations/zed-beaml/grammar.js) `comment`, [config.toml](../../../integrations/zed-beaml/languages/beaml/config.toml) |
| Significant whitespace vs braces | braces for blocks, newline or comma separates fields and variants, whitespace not significant; `with` uses `do ... end` | [grammar.js](../../../integrations/zed-beaml/grammar.js) `_field_block`, `with_expression` |
| Semicolons | absent [Verified]: no statement terminator; one expression per body | [grammar.js](../../../integrations/zed-beaml/grammar.js) |
| Operator overloading | not addressed [Unknown]: only `+` (String concatenation), `\|>`, `->`, `!`, `\|`, `<-`, `=` exist | [grammar.js](../../../integrations/zed-beaml/grammar.js) |
| Macros / metaprogramming | rejected by principle [Requirement]: compiler derives decode, structs, spans, replay; "never asks for it in source"; spec S27 treats Elixir macros as an explicit trust boundary | DL-126, [engineering-spec-v0.5.md S27](../../../wiki/sources/engineering-spec-v0.5.md) |
| Async / concurrency syntax | not addressed [Unknown]: no process, spawn, receive or task form; BEAM processes mentioned only for termination (DL-025) | DL-025, [beam processes concept](../../../wiki/concepts/beam/processes-messages-and-otp.md) |
| Effects system | present [Verified]: `effect` declarations with transport body; reachability inferred, not declared (DL-108); constructors must be pure (DL-120); inbound EFFECT sketched (DL-128) | DL-013, DL-108, DL-120, DL-128 |
| Literals: records | present [Verified]: `Order { id: "1", customer: Customer { ... } }`; field punning `{ order_id }` in patterns and literals | [example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml), [grammar.js](../../../integrations/zed-beaml/grammar.js) `record_field` |
| Literals: lists | not addressed [Unknown]: no list TYPE or literal; DL-084 notes "lists as an external return TYPE (later)"; DL-129 needs "a `List` TYPE for `Orders`" | DL-084, DL-129 |
| Literals: maps | not addressed [Unknown]: no map TYPE; records lower to Elixir maps at the host | [0001 README](../../../experiments/0001-syntax-to-beam/README.md) "Experimental host representation" |
| Integer / float handling | partial [Verified]: `Int` TYPE and decimal literals since slice 6b step 1; no negative literal, no arithmetic, no `Float`; division form decided, not built (DL-030) | [int.beaml](../../../experiments/0004-generated-replay/slice6/int/int.beaml), [grammar.js](../../../integrations/zed-beaml/grammar.js) `integer`, DL-030 |
| Booleans | not addressed [Unknown]: `true`/`false` only in the reserved-word list; no `Bool` TYPE in grammar or fixtures (spec §22 sketch used `Bool`) | [main.rs](../../../experiments/0001-syntax-to-beam/src/main.rs) reserved list |
| Schema versioning in source | present [Verified]: `migrate`, `retire`, VERSION MARK; unusual among languages | section 1.8, 1.9 |
| PII marker in the type | present [Verified]: `redacted` modifier; `with` release on effects | section 1.10 |
| Formatter | planned/partly built [Verified]: `beaml fmt` aligns clause and effect columns (slice 6b step 10) | DL-083, [clauses.beaml](../../../experiments/0004-generated-replay/slice6/fmt/clauses.beaml) |
| Editor support | present [Verified]: Tree-sitter grammar and Zed extension; language server planned (DL-096) | [integrations/zed-beaml/README.md](../../../integrations/zed-beaml/README.md) |

## 6. Gaps noticed in the KB (for the synthesis worker)

- `with ... do ... else ... end` is decided (DL-014) and in the grammar, but no committed `.beaml` fixture compiles it and the compiler has no parser for it. Its real shape (where `=` pure bindings go, how `else` arms look) is a guess in the grammar.
- Zero-argument variants: 0001 requires `Waiting()`; slice 6 fixtures write bare `Pending` and `Approved()` side by side ([pipe.beaml](../../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml) line 7). No decision records the change.
- No page states the lexical rules as a whole (identifier charset, reserved words, Unicode in strings). The compiler's reserved-word list is Elixir-driven, not a BEAML keyword list.
- No `Bool`, `Float`, list, map, option or negative-number form exists, and no page lists them as open decisions except by side remarks.
- Module/import form and test syntax are roadmap rows without option tables.
- The historical spec's surface (`function`, `class`, generics `<T>`, `trait`) is never explicitly retired page by page; readers can mistake it for the current design.

## 7. Sources read

- [README.md](../../../README.md), [GLOSSARY.md](../../../GLOSSARY.md), [AGENTS.md](../../../AGENTS.md), [wiki/index.md](../../../wiki/index.md)
- [wiki/planning/decision-log.md](../../../wiki/planning/decision-log.md), [wiki/planning/decisions-to-be-made.md](../../../wiki/planning/decisions-to-be-made.md)
- [wiki/concepts/vertical-integration.md](../../../wiki/concepts/vertical-integration.md), [wiki/concepts/migrate-fates.md](../../../wiki/concepts/migrate-fates.md), [wiki/concepts/compiler-and-tooling.md](../../../wiki/concepts/compiler-and-tooling.md) (grep), [wiki/concepts/baml-language-and-tooling.md](../../../wiki/concepts/baml-language-and-tooling.md) (grep), [wiki/concepts/product-contract.md](../../../wiki/concepts/product-contract.md) (grep)
- [wiki/sources/syntax-spike-requirement.md](../../../wiki/sources/syntax-spike-requirement.md), [wiki/sources/engineering-spec-v0.5.md](../../../wiki/sources/engineering-spec-v0.5.md) (S01-S06, S22-S27), [wiki/planning/roasting-rounds.md](../../../wiki/planning/roasting-rounds.md) (grep)
- [raw/requirements/2026-11-05-syntax-spike.md](../../../raw/requirements/2026-11-05-syntax-spike.md), [raw/specification/engineering-spec-v0.5.pages.txt](../../../raw/specification/engineering-spec-v0.5.pages.txt) (pp. 1-2, §22-23)
- [integrations/zed-beaml/grammar.js](../../../integrations/zed-beaml/grammar.js), [integrations/zed-beaml/README.md](../../../integrations/zed-beaml/README.md), [integrations/zed-beaml/languages/beaml/config.toml](../../../integrations/zed-beaml/languages/beaml/config.toml), highlight tests `forms.beaml`, `constructors.beaml`, `syntax.beaml`, `lexer.beaml`
- [experiments/0001-syntax-to-beam/README.md](../../../experiments/0001-syntax-to-beam/README.md), [example.beaml](../../../experiments/0001-syntax-to-beam/example.beaml), [src/main.rs](../../../experiments/0001-syntax-to-beam/src/main.rs) (declaration dispatch, reserved words)
- [experiments/0004-generated-replay/README.md](../../../experiments/0004-generated-replay/README.md) (slice 1 source, owner decisions, owner questions, slice 6a forms), [examples/order-flow.beaml](../../../experiments/0004-generated-replay/examples/order-flow.beaml), [syntax-options.beaml](../../../experiments/0004-generated-replay/syntax-options.beaml), fixtures under `slice6/` (enum, constructor, host-struct, failure, redacted, pipe, int, fmt), `slice3/SAR`, `slice3/RR`, `drift/R`, `bad/undeclared_failure.beaml`
- [experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/](../../../experiments/0004-generated-replay/workflow/2026-11-07/slice6d-inbound-effect/decisions.md) (decisions, plan, plan-review; grep), [red-team-01](../../../experiments/0004-generated-replay/workflow/2026-11-07/red-team-01/report.md) (grep C1, D1)
