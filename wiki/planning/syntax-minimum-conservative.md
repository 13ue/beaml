---
id: planning-syntax-minimum-conservative
kind: proposal
status: draft
date: 2026-11-08
author: Fable worker, conservative brief
---

Corrected 2026-11-08 after the compare review (see [syntax-minimum.md](syntax-minimum.md#10-defects-found-in-the-two-proposals)).

# The conservative syntax minimum

**[Proposal]** The OWNER asked on 2026-11-08: "I want to minimize. Really only the minimum of syntax." This page gives the minimum that keeps every closed decision in the [decision log](decision-log.md) intact. It removes redundancy, forbids growth and states a budget rule. It reopens nothing. The OWNER decides; see section 8.

Evidence base: the [BEAML syntax profile](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md), the [loved](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) and [hated](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) tables (`L n`, `H n`), the [BAML v0 to v1 churn](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#5-baml-v0-to-v1-what-changed-in-the-syntax-and-how-it-was-received), the [syntax sentiment concept](../concepts/syntax-sentiment.md) and the [grammar](../../integrations/zed-beaml/grammar.js).

## 1. Inventory today

**[Verified]** One row per distinct spelling, from the [profile](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#1-what-beaml-looks-like-today) and the grammar. "Decided by" names the closed entry that locks the row; "none" means no decision records the spelling. Count: **39**. The [compare page](syntax-minimum.md#1-one-inventory) counts 40 by another unit: it counts the two bracket pairs and the ENUM LITERAL shape, and not `String` and `Int` (library names).

| Group | Forms | Count | Decided by |
|---|---|---|---|
| Top-level keywords | `type`, `enum`, `fn`, `effect`, `migrate`, `retire` | 6 | DL-061, DL-061, spike 2026-11-05, DL-013, DL-022, DL-055 |
| Keyword words inside forms | `redacted`; `with` (EFFECT release); `with`, `do`, `else`, `end`; `rename`, `add`, `drop`; `keep`, `days` | 10 | DL-059; DL-089; DL-014; DL-022, DL-023; DL-055 |
| Marks | VERSION MARK `vN` on a `type` line | 1 | DL-070, DL-071, DL-072, DL-080 |
| Operators and punctuation | `\|>`, `->`, `!`, `\|`, `<-`, `=`, `+`, `,`, `:`, `.`, `_` | 11 | DL-014/DL-086, spike, DL-015/DL-092, DL-093, 0004 owner decisions, DL-082, spike, spike, spike, DL-013, none |
| Literal forms | `"..."` with 5 escapes, `Int` decimal, record literal `T { f: v }`, punning `{ f }`, `V(x)`, bare `V`, empty `V()` | 7 | 0001 README, slice 6b, spike, spike, DL-061, DL-100, none |
| Separator rule | newline or comma between fields and variants | 1 | none ([grammar](../../integrations/zed-beaml/grammar.js) `optional(",")`) |
| Primitive TYPES | `String`, `Int` | 2 | 0001, slice 6b |
| Comment | `//` | 1 | DL-132 |

**[Verified]** Two rows have no decision: `V()` next to bare `V` ([pipe.beaml](../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml) line 7 writes `Approved()`, [literals.beaml](../../experiments/0004-generated-replay/slice6/enum/literals.beaml) writes `Pending`) and the optional comma ([profile gaps](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#6-gaps-noticed-in-the-kb-for-the-synthesis-worker), D032).

## 2. The conservative minimum

**[Proposal]** Today 39 forms. Proposed **38**: one row goes (`V()`); the separator rule stays as one rule with a fixed direction; nothing is added. The ceiling for all planned forms is **39** (section 5).

| Form | Keep, merge or forbid | Reason | Rests on |
|---|---|---|---|
| 6 top-level keywords | keep | each is a closed decision | DL-013, DL-022, DL-055, DL-061 |
| `V()` empty payload | **forbid**; bare `V` is the one spelling | no decision made it; `V` is already a pattern and an expression; two spellings of one thing ([H25](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26), [L22](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features)) | DL-100, D032 open |
| newline-or-comma separator | **merge into one**: comma required between fields and variants | record literals, parameters and `with` fields already require the comma; between MIGRATE CHANGES the compiler requires it ([main.rs](../../experiments/0001-syntax-to-beam/src/main.rs) line 713) and the grammar makes it optional ([grammar.js](../../integrations/zed-beaml/grammar.js) line 68; see the [compare page](syntax-minimum.md#6-what-both-pages-miss)); one rule for every brace ([H8](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26), [L23](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features)) | grammar `commaList`, D032 open |
| `->` in four places (TYPE arrow, `v1 -> v2`, `rename a -> b`, `else` arm) | keep as one token, one meaning "to" | already minimal; forbid a second arrow (`=>`): BAML closed its `->` vs `=>` debate undecided ([churn](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#5-baml-v0-to-v1-what-changed-in-the-syntax-and-how-it-was-received)) | spike, DL-022, DL-014 |
| `=` in five places (body, ENUM LITERAL, `add` constant, transport, pure step in `with`) | keep as one token, one meaning "is defined as" | already minimal | spike, DL-082, DL-022, DL-013, 0004 owner decisions |
| `with` with two meanings | keep both, forbid a third | both closed; the cost is recorded in section 6 | DL-014, DL-089 |
| `\|` in the failure list | keep; forbid `\|` as a variant separator (D025 option A) | one token, one meaning; a second enum form is a second dialect ([H8](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26)) | DL-093, D025 open |
| VERSION MARK | keep; `fmt` already writes one canonical form | any agreeing mark is legal and `fmt` normalizes: gofmt pattern ([L23](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features)) | DL-080, DL-081, DL-104 |
| `redacted` modifier | keep; forbid further modifiers before a TYPE | the only modifier; new policy goes into a TYPE (rule 3) | DL-059 |
| `retire ... keep N days` | keep; `days` stays the only unit | one spelling; the FATE OPERATION reuses it | DL-055, DL-125 |
| `//` comment | keep; no second form | decided | DL-132 |
| `+`, `String`, `Int`, 5 escapes | keep; no interpolation form until D028 closes | `#{...}` stays data | 0001 acceptance 6, D028 open |

Snippets, today against proposed, only where something changes.

```beaml
// today (pipe.beaml): two spellings for a variant without payload
enum Outcome { Approved()  Declined(String) }
fn pending -> PaymentState = Pending
```
```beaml
// proposed: one spelling
enum Outcome { Approved, Declined(String) }
fn pending -> PaymentState = Pending
```

```beaml
// today: whitespace separates fields in a type, commas separate them in a literal
type R { id: String tag: String }
fn build P { id }, x: String -> R = R { id: id, tag: x }
```
```beaml
// proposed: the comma separates fields everywhere
type R { id: String, tag: String }
fn build P { id }, x: String -> R = R { id: id, tag: x }
```

```beaml
// today (literals.beaml): two spaces carry the separation
enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }
```
```beaml
// proposed
enum PaymentState { Authorized = "ok", Pending = "pending", Unknown(String) }
```

```beaml
// sketch that the budget forbids (D025): a second declaration dialect
enum Channel = Web | App
type PlaceForm = { amount: Amount, channel: Channel }
```
```beaml
// proposed: the one brace form stays
enum Channel { Web, App, Unknown(String) }
type PlaceForm { amount: Amount, channel: Channel }
```

```beaml
// DL-126 candidate, concept only: policy as keyword words on the EFFECT line
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") retry 3 timeout 2000
```
```beaml
// proposed under rule 3: policy is a TYPE value in a position that already takes values
type Policy { retry: Int, timeout_ms: Int }
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize", Policy { retry: 3, timeout_ms: 2000 })
```

```beaml
// DL-128 sketch, replaced by DL-130: the ENTRY LINE is an ordinary effect line, zero new forms
on ui "place" PlaceOrder -> place
```
```beaml
effect ui.place PlaceForm -> Order ! PlaceError = ui.event("place") |> place
```

```beaml
// D026 under the budget: absence as a declared enum, no `T?` suffix, no Option keyword
enum MaybeAddress { Some(Address), None }
type Customer { name: String, address: MaybeAddress }
```

## 3. Growth rules

**[Proposal]** Six rules, one sentence each, with the row that motivates it and the check.

1. **Ceiling.** The grammar has at most 39 spellings by the count of section 1; a syntax decision that would pass 39 is refused until one spelling is retired. Motivation: [H4](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) complexity creep, [L22](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) small language. Check: a grammar test counts the keyword strings and operator tokens of `grammar.js` against a pinned file.
2. **One in, one out.** A new keyword word retires one, and the retired spelling becomes a hard error with a help line, as DL-074 did for `interface`. Motivation: [H4](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26); BAML's removed `#"..."#`, `client<llm>` and `@@dynamic` ([churn](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#5-baml-v0-to-v1-what-changed-in-the-syntax-and-how-it-was-received)). Check: a `Budget: +1 / -1` field in every syntax entry of the decision log.
3. **Policy is a TYPE, not a keyword.** Retry, timeout, retention, field rules and other policy enter as TYPE values in a position that already takes a value, never as a new word. Motivation: [L15](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) a `type` line derives the rest, [L18](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) no hidden behaviour; DL-126 keeps policy declarative. Check: lint on a grammar diff: a new `seq("word"` needs a decision-log entry with the `Budget` field.
4. **One token, one meaning.** No existing token gets a further meaning: no `.` for field access, no `|` for variants, no `=>`, no third `with`. Motivation: [H8](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) inconsistency, [H20](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) Scala `implicit`, one keyword for several concepts. Check: a meaning table per token in the grammar README; the grammar test fails when a token appears in a new rule family.
5. **One spelling per concept.** The grammar accepts one spelling; `fmt` changes layout only, never a spelling, and every rejected spelling has a `bad/` fixture with a help line. Motivation: [L23](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) gofmt, [H25](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) optional separators; DL-072, DL-088. Check: fixture pairs, one accepted and one rejected, per decision.
6. **A fixture before a form.** A new form enters the grammar only with a `.beaml` fixture from an example application, never from a sketch. Motivation: DL-132 (`#` and `--` came from sketches), D025 (the `=` and `|` form came from a sketch), DL-145 (decide after the first example applications). Check: a `Fixture:` path field in the decision-log entry.

## 4. Planned forms under the budget

**[Inference]** Can the forms that exist today carry each planned form? Counts refer to the ceiling of 39.

| Planned form | Existing forms carry it? | One line |
|---|---|---|
| ENTRY LINE (DL-128, DL-130) | yes | DL-130 already chose the `effect` line with `ui.event("...")` as transport; zero new spellings. |
| FATE OPERATIONS (DL-125) | partly | `retire f keep N days` reuses three words; `redact f` could reuse `redacted`; `quarantine` and `map` are new words inside `migrate` only: +2, one over the ceiling of 39 after the count correction (38 + 2); rule 2 applies. |
| EFFECT policies (DL-126 candidates) | yes | a `Policy` TYPE value as a second transport argument (rule 3); no word added. |
| VERSION MARK | yes, built | DL-080 and DL-104 give one canonical form; nothing to add. |
| `with ... do ... else ... end` (DL-014) | no | the pipe carries the binding, nothing carries the `else` arms; it stays as decided and is already counted (4 words, `<-`). |
| Option (D026) | yes, with cost | a declared `enum` per TYPE (`Some(T)`, `None`) uses DL-061 forms; a generic `Option` or a `T?` suffix needs a new form and waits for generics. |
| Collections (D029) | list partly, map no | `List(Order)` as a TYPE and `List(a, b)` as a constructor call reuse the parenthesis shape of DL-092; a `[a, b]` literal is new; a map needs a pair form. |
| Lambdas (D030) | no | functions are not values today; any anonymous form is new and must trade under rule 2. |
| Concurrency (D031) | partly | `spawn` or a task as a fixed transport on an `effect` line follows DL-129 (`db.put` pattern), zero words; `receive` has no existing shape. |
| `where` rules on a TYPE field (DL-126 candidate) | yes | the constructor `fn` already carries any check (DL-092); no word added. |

## 5. What the conservative minimum costs

- **[Inference]** The comma rule changes 57 of 142 fixtures mechanically (those with a `type` or `enum` block; every `migrate` block already has commas), as DL-072 did; one character per field, and `fmt` must insert it.
- **[Verified]** `with` keeps two meanings (DL-014, DL-089); the minimum cannot remove this without reopening two closed decisions.
- **[Inference]** Absence as a hand-written `enum` per TYPE repeats two variants for every optional field until generics exist; the loved row L4 ergonomics are not reached.
- **[Inference]** Without lambdas, `map` and `filter` have no idiom; the ceiling forces a trade or a wait, which blocks L10 and L11.
- **[Inference]** A hard ceiling turns every good new form into a retirement fight; BEAML "wants the best syntax ever built" (DL-145), and a ceiling can block innovation as well as creep.
- **[Inference]** The count of 39 is one counting unit (one row per spelling); another unit gives another number, so the ceiling must name its unit.

## 6. Smallest next test

**[Proposal]** One EXPERIMENT run in `experiments/0004-generated-replay/`: rewrite three fixtures ([pipe.beaml](../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml), [literals.beaml](../../experiments/0004-generated-replay/slice6/enum/literals.beaml), [marks.beaml](../../experiments/0004-generated-replay/slice6/fmt/marks.beaml)) to the proposed spelling (bare variants, commas), run the existing slice 6 tests and `tree-sitter parse`, and add a count script over `grammar.js` that pins 39. Pass: every test stays green with no grammar change, the script prints 39, and `Approved()` fails with a help line. Fail: the compiler rejects a comma between fields; that result shows the compiler and the grammar disagree, which is evidence for D032 either way.

## 7. Decision class

**Migrate (syntax).** This page recommends nothing beyond the proposal. The OWNER answers:

1. Is today's count the ceiling, or a lower number, and in which counting unit?
2. Zero-argument variant: bare `Pending` only, or `Pending()` only? (D032)
3. Separator: comma required everywhere, or newline only and no comma? (D032)
4. Does `quarantine` or `map` take the one free slot, or must the FATE OPERATIONS reuse existing words?
5. Does rule 3 bind the DL-126 candidates, so that `where` and `keep N days` per TYPE never become keywords?
6. Does every syntax entry in the decision log get the `Budget` and `Fixture` fields from now on?
