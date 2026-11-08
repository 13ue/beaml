---
id: planning-syntax-minimum-radical
kind: proposal
status: draft
date: 2026-11-08
author: Fable worker, radical brief
---

Corrected 2026-11-08 after the compare review (see [syntax-minimum.md](syntax-minimum.md#10-defects-found-in-the-two-proposals)).

# The radical syntax minimum

**[Proposal]** OWNER request of 2026-11-08: "only the minimum of syntax". This page asks of every form: can it go, merge, or become a library name? The OWNER decides. Nothing here is grammar. Evidence: the [syntax profile](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md), the [loved](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) and [hated](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) tables (`L n`, `H n`), the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md), the [decision log](decision-log.md) and 142 committed fixtures under `experiments/` (results directories excluded; `rg --files experiments -g '*.beaml' -g '!**/results/**'`).

## 1. Inventory today

**[Verified]** From the [profile, section 1 and 5](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#1-what-beaml-looks-like-today). Fixture counts are files out of 142.

| Group | Items | Count |
|---|---|---|
| Top-level forms | `type`, `enum`, `fn` clause, `effect` (outbound and ENTRY LINE, DL-130), `migrate`, `retire`. `with … do … else … end` is an expression (grammar only), not a top-level form | 6 |
| Keywords | `type` (136), `enum` (36), `fn` (142), `effect` (94), `migrate` (29), `retire` (5), `rename` (20), `add` (17), `drop` (17), `keep` (5), `days` (5), `redacted` (46), `with` (release 6, expression 0; one spelling, counted once), `do`, `else`, `end` (0) | 16 |
| Operators and punctuation | `\|>` (103), `->`, `!` (103), `\|` failure list (1), `=`, `<-` (0), `+` (66), `:`, `,`, `{ }`, `( )`, `.`, `_` | 13 |
| Marks and modifiers | VERSION MARK `vN` (32), field punning `{ order_id }` | 2 |
| Literal forms | String with escapes, Int, record literal `T { … }`, variant `Pending` / `Unknown(s)` / `Approved()`, `//` comment | 5 |
| Sketched, not grammar | `redact`, `quarantine`, `map`, `where`, policy words on `effect` lines (DL-125, DL-126) | 0 counted |

**Total today: 36 syntax items, 6 top-level forms.** Transport names (`http.post`, `ui.event`, `db.put`, `db.get`, `db.list`) are library names, not syntax, and stay out of the count.

## 2. The radical minimum

**[Proposal]** Four top-level forms. Every other item merges into one of them or goes.

| Form | Keeps | Absorbs | Cut |
|---|---|---|---|
| `type T [vN] { … }` | records, fields, `redacted`, VERSION MARK, ENUM LITERAL `A = "ok"` | `enum`: uppercase members are variants, lowercase members are fields; mixing is an error | `enum`; `Approved()` for a zero-argument variant |
| clause `name params -> T [! F] = body` | patterns, signature line, constructor by name, `\|>`, `+`, `!` with one failure TYPE | nothing new | `fn` keyword; `\|` failure list (several failures are one `type` with variants); `with … do … else … end`, `<-` |
| `effect ns.op In -> Out ! F = transport(…) [with f]` | outbound, inbound (DL-130), redacted release | nothing new | nothing |
| `migrate X [vN] { … }` | `add f: T = c`, `drop f: T`, `f -> g`, fates (DL-125) | `retire`: `migrate payments.authorize { retire 30 days }` | `retire` line, `keep`, `rename` word, `vA -> vB` (the target version alone, the chain has no gaps) |

Separators: one rule. Whitespace or newline separates items inside `{ }`; a comma separates items inside `( )` and parameter lists. No optional comma.

**Total proposed: 29 items** (keywords 9: `type`, `effect`, `migrate`, `add`, `drop`, `retire`, `days`, `redacted`, `with`; operators 11; marks 2; literals 5; new shapes 2: `migrate <operation> { retire N days }`, a `migrate` head without versions, and the `recover` clause). Cut: 9 items, 2 top-level forms. Added: 2 shapes.

Today and minimum, side by side, from the fixtures the profile cites. [Verified] for the "today" lines, [Proposal] for the "minimum" lines.

Variants ([literals.beaml](../../experiments/0004-generated-replay/slice6/enum/literals.beaml) line 2; [pipe.beaml](../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml) line 7):

```beaml
enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }
enum Outcome { Approved()  Declined(String) }
```
```beaml
type PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }
type Outcome { Approved  Declined(String) }
```

Clauses ([example.beaml](../../experiments/0001-syntax-to-beam/example.beaml) lines 34 to 38):

```beaml
fn describe Ok(Order { id, customer: Customer { name } }) -> String = "Bestellung " + id + " von " + name
fn describe Error(NotFound(id)) -> String = "Bestellung " + id + " wurde nicht gefunden"
```
```beaml
describe Ok(Order { id  customer: Customer { name } }) -> String = "Bestellung " + id + " von " + name
describe Error(NotFound(id)) -> String = "Bestellung " + id + " wurde nicht gefunden"
```

Constructor and signature line ([nonzero.beaml](../../experiments/0004-generated-replay/slice6/constructor/nonzero.beaml) lines 5 to 7):

```beaml
fn NonZeroInt n: Int -> NonZeroInt ! IsZero
fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}
fn NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }
```
```beaml
NonZeroInt n: Int -> NonZeroInt ! IsZero
NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}
NonZeroInt n -> NonZeroInt ! IsZero = NonZeroInt { value: n }
```

Failure list ([host-struct/nonzero.beaml](../../experiments/0004-generated-replay/slice6/host-struct/nonzero.beaml) line 24, the only fixture with `|`):

```beaml
fn twice n: Int -> String ! NonZeroInt | IsZero = n |> NonZeroInt
```
```beaml
type TwiceError { Wrapped(NonZeroInt)  Zero(IsZero) }
twice n: Int -> String ! TwiceError = n |> NonZeroInt
```

Effect, pipe and redacted release ([orders_with.beaml](../../experiments/0004-generated-replay/slice6/redacted/orders_with.beaml) lines 3, 7, 11 to 14): unchanged apart from `fn`.

```beaml
type Order { order_id: String card_holder: redacted String }
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder
fn place order: Order -> Payment ! PaymentError = order |> prepare |> payments.authorize
```
```beaml
type Order { order_id: String card_holder: redacted String }
effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder
place order: Order -> Payment ! PaymentError = order |> prepare |> payments.authorize
```

ENTRY LINE ([entry/orders.beaml](../../experiments/0004-generated-replay/slice6/entry/orders.beaml) line 19): unchanged. DL-130 already made it an `effect` line.

```beaml
effect ui.place PlaceOrder -> Payment ! PaymentError = ui.event("place") |> place
```

MIGRATE CHAIN and VERSION MARK ([marks.beaml](../../experiments/0004-generated-replay/slice6/fmt/marks.beaml) lines 3 to 5; [SAR/orders.beaml](../../experiments/0004-generated-replay/slice3/SAR/orders.beaml) lines 4 to 6):

```beaml
type Chained v3 { id: String state: String channel: String }
migrate Chained v1 -> v2 { rename status -> state }
migrate Chained v2 -> v3 { add channel: String = "web" }
migrate Payment v1 -> v2 { drop channel: String }
```
```beaml
type Chained v3 { id: String state: String channel: String }
migrate Chained v2 { status -> state }
migrate Chained v3 { add channel: String = "web" }
migrate Payment v2 { drop channel: String }
```

RETIRE LINE ([slice4/G+r/orders.beaml](../../experiments/0004-generated-replay/slice4/G+r/orders.beaml) line 7):

```beaml
retire payments.authorize keep 30 days
```
```beaml
migrate payments.authorize { retire 30 days }
```

`with … do … else … end` ([forms.beaml](../../integrations/zed-beaml/test/highlight/forms.beaml) lines 45 to 61, grammar only, no fixture compiles it):

```beaml
fn place order: Order -> Payment ! PaymentError | Timeout =
  with p <- order |> prepare |> payments.authorize do finish(p) else
    PaymentError { reason } -> fail(reason)
  end
```
```beaml
place order: Order -> Payment ! PlaceError = order |> prepare |> payments.authorize |> finish
recover PaymentError { reason } -> Payment = Payment { order_id: ""  status: reason }
recover p: Payment -> Payment = p
```

**[Inference]** The minimum has no local failure branch. A caller that must recover writes a clause over the failure TYPE, as 0001 does with `OrderResult { Ok(Order)  Error(OrderError) }` ([example.beaml](../../experiments/0001-syntax-to-beam/example.beaml) lines 22 to 25). How the pipe hands a failure to `recover` is not defined today; see the questions in section 7.

Record literal and pattern with commas ([example.beaml](../../experiments/0001-syntax-to-beam/example.beaml) lines 45 to 50): commas inside `{ }` go.

```beaml
describe(Ok(Order { id: "order-1", customer: Customer { name: "Kunde", address: Address { city: "Berlin", country: "DE" } } }))
```
```beaml
describe(Ok(Order { id: "order-1"  customer: Customer { name: "Kunde"  address: Address { city: "Berlin"  country: "DE" } } }))
```

## 3. Each cut in one line

Format: form → replacement → reopened decision → evidence.

- `enum` → `type` with uppercase members → reopens DL-061 (returns to the DL-060 reading, OWNER choice) → [L22](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) small language, [H4](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) complexity creep; 36 files.
- `fn` → keyword-less clause; `type`, `effect`, `migrate` are the only reserved line starts → reopens the [syntax spike](../sources/syntax-spike-requirement.md) surface and DL-098 (grammar) → [H10](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) text that carries no decision, [L7](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features); 142 files. [Inference] Haskell and Elm have no function keyword; the evidence does not score that directly.
- `|` failure list → one failure TYPE per signature; several failures are one `type` with variants → reopens DL-015 (list form), keeps DL-093 → [H11](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) versionability: a new failure changes one `type`, not every `!` list ([D027](decisions-to-be-made.md)); 1 file.
- `with … do … else … end`, `<-` → clauses over the failure TYPE → reopens DL-014 (the `with` half) and DL-015 (the `else` exhaustiveness check) → [L18](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) no hidden control flow, [L26](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) against (guard clauses are loved); 0 files, 1 highlight test.
- `retire … keep N days` → `migrate op { retire N days }` → reopens DL-055 and DL-057 (form only, the semantics stay) and the DL-125 spelling ([migrate fates](../concepts/migrate-fates.md)) → DL-125 made the fate a declarative operation in the MIGRATE STEP, and DL-137 applies one `migrate` block to RESPONSE RECORDS and database rows; [L22](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features); 5 files.
- `rename a -> b` → `a -> b` (the arrow is the rename; `map` uses the same arrow) → reopens DL-022 (change words) → [H10](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26); 20 files.
- `migrate T vA -> vB` → `migrate T vB`; the chain counts without gaps (0004 `derive_versions`) → reopens DL-022 and DL-072 (the `v` spelling stays) → [H10](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26); 29 files.
- `Approved()` → `Approved` → closes [D032](decisions-to-be-made.md) half → [H8](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) inconsistency; 3 files.
- optional comma inside `{ }` → whitespace only → closes [D032](decisions-to-be-made.md) other half, reopens the slice 3 rule "MIGRATE CHANGES separated by commas" ([0004 README](../../experiments/0004-generated-replay/README.md)) → [H25](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) silent adjacency; 79 files.
- Not cut, asked and kept: `effect` (DL-013; cutting it hides world contact, against [L18](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features)); `redacted` and `with` release (DL-059, DL-089, DL-105, DL-112: PII is structural; a wrapper TYPE needs generics, which do not exist); `!` (DL-092, DL-093; `fail` already rejected); `|>` (DL-086); `+` (the only operator; a `concat` call would be longer in 66 files); `//` (DL-132); `vN` (DL-070); punning (`{ id: id + "!" }` needs the long form, so both stay).

## 4. What the radical minimum costs

- Readability: without `fn` a reader finds a function only by shape. `beaml fmt` tables (DL-083) carry that load. [Inference] Agents grep `^fn `; they would grep `^[a-z]` instead. The claim "agents make fewer errors" (profile, design intents) is untested for keyword-less clauses.
- Two dialects: every cut rewrites fixtures. 142 of 142 files change for `fn`; 69 files change for the other cuts together; 79 for the comma rule. [BAML v0 to v1](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#5-baml-v0-to-v1-what-changed-in-the-syntax-and-how-it-was-received) shows the cost of a syntax break with users; BEAML has no users yet, so the cost is one mechanical rewrite plus hard errors with help lines (DL-074 pattern).
- Failure handling: the minimum has no local branch on a failure. Until the pipe can hand a failure to a clause, a flow either propagates or declares a result `type` with `Ok` and `Error` variants. [Unknown] whether the fixtures of EXPERIMENT 0005 need the local branch.
- Replay and `--stored`: `retire` inside `migrate` changes no record format; the RETIRE LINE semantics (DL-055, DL-057) stay. `migrate T vB` changes the parser, not the TYPE VERSION derivation. [Inference] Low risk, but RED tests of slices 2 to 4 and 6d must be rerun.
- PII policy: untouched. `redacted`, `with` release, DL-105 and DL-112 keep their forms.
- Tooling: the Tree-sitter grammar, the highlighter tests, the compiler parser in `main.rs`, `beaml fmt` and the help lines of DL-074 all change. One failure TYPE per signature also changes the generated Elixir `name!` pair (DL-015) for the one fixture.
- Agent-as-author: a smaller grammar is fewer choices per line, which [L22](../../raw/research/2026-11-07-pl-syntax-sentiment/loved.md#1-ranked-table-top-celebrated-features) and [H4](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) reward. The BAML team reports agents wrote v1 worse until a skill taught idioms ([reception](../../raw/research/2026-11-07-baml-syntax-sentiment/baml-reception.md#5-baml-v0-to-v1-what-changed-in-the-syntax-and-how-it-was-received)); fewer forms do not by themselves give better agent output. [Unknown]
- Expressiveness lost: nothing in the 142 fixtures. The historical spec surface (`trait`, generics, `import`) was never built; the minimum does not block it.

## 5. Smallest next test

**[Proposal]** Rewrite six fixtures by hand into the minimum: [example.beaml](../../experiments/0001-syntax-to-beam/example.beaml), [literals.beaml](../../experiments/0004-generated-replay/slice6/enum/literals.beaml), [constructor.beaml](../../experiments/0004-generated-replay/slice6/enum/constructor.beaml), [marks.beaml](../../experiments/0004-generated-replay/slice6/fmt/marks.beaml), [G+r/orders.beaml](../../experiments/0004-generated-replay/slice4/G+r/orders.beaml), [entry/orders.beaml](../../experiments/0004-generated-replay/slice6/entry/orders.beaml). Pass: a parser fork reads all six with no ambiguity (one parse tree each, the `type` with uppercase members and the keyword-less clause included), and the generated Elixir is byte-equal to today's output for each. Fail: any fixture needs a form outside the four, or two parses exist. One day of work; no decision needed before it, because it changes no committed file.

## 6. Decision class

**Migrate** (syntax, DL-139: syntax waits for the OWNER). This page gives no recommendation beyond the proposal. Questions the OWNER would need to answer:

1. Does `fn` go? It is the largest rewrite (142 files) and the one cut with no direct evidence row.
2. Does `enum` merge into `type` (back to the DL-060 reading), or does the record and variant split stay (DL-061)?
3. One failure TYPE per signature, with several failures as one `type`? This also answers [D027](decisions-to-be-made.md).
4. Does `with … do … else … end` go before it is ever built, and what hands a failure to a clause instead?
5. Does `retire` live inside `migrate`, and does `migrate` lose `rename`, `keep` and the `vA -> vB` arrow?
6. One separator rule (whitespace inside `{ }`, comma inside `( )`), with 79 files rewritten?

See also [syntax sentiment](../concepts/syntax-sentiment.md), [D033](decisions-to-be-made.md) (budget for top-level forms) and the [glossary](../../GLOSSARY.md).
