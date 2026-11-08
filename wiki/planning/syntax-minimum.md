---
id: planning-syntax-minimum
kind: proposal
status: draft
date: 2026-11-08
author: Fable worker, compare brief
---

# The syntax minimum: two proposals compared

**[Requirement]** OWNER request of 2026-11-08: "I want to minimize. Really only the minimum of syntax."

**Status: two proposals, no decision; Class Migrate (syntax, [DL-139](decision-log.md)).** The [conservative minimum](syntax-minimum-conservative.md) reopens no closed decision. The [radical minimum](syntax-minimum-radical.md) reopens six. This page reconciles their counts, sets them side by side and lists the OWNER questions. It recommends nothing. Section 10 lists the defects found in both pages.

## 1. One inventory

**[Verified]** Counting unit: one distinct spelling that the parser reserves, or one literal shape that it recognises. A bracket pair counts once. `with` counts once (two meanings, one spelling). Primitive TYPE names (`String`, `Int`) and transport names (`http.post`, `ui.event`, `db.put`) are library names, not syntax. The separator rule counts as one rule. Sources: [grammar.js](../../integrations/zed-beaml/grammar.js), [main.rs](../../experiments/0001-syntax-to-beam/src/main.rs), the [syntax profile](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md#1-what-beaml-looks-like-today). Fixture counts are files out of 142 (`rg --files experiments -g '*.beaml' -g '!**/results/**'`).

| Group | Items | Count |
|---|---|---|
| Keywords | `type` 136, `enum` 36, `fn` 142, `effect` 94, `migrate` 29, `retire` 5, `redacted` 46, `with` (release 6, expression 0), `do`, `else`, `end` (0), `rename` 20, `add` 17, `drop` 17, `keep` 5, `days` 5 | 16 |
| Operators | `\|>` 103, `->`, `!` 103, `\|` failure list 1, `<-` 0, `=`, `+` 66, `,` 116, `:`, `.` | 10 |
| Bracket pairs | `{ }`, `( )` | 2 |
| Lexical forms | String with 5 escapes, Int literal, VERSION MARK `vN` 32, `//` comment 135, `_` wildcard | 5 |
| Literal shapes | record `T { f: v }`, punning `{ f }`, `V(x)`, bare `V`, empty `V()` 3, ENUM LITERAL `A = "s"` | 6 |
| Rules | comma optional inside `{ }` (grammar); required between MIGRATE CHANGES (compiler only, see section 7) | 1 |

**Total today: 40.** Top-level line forms: 6 (`type`, `enum`, `fn` clause, `effect`, `migrate`, `retire`); `with … do … else … end` is an expression.

**[Verified]** Where the two pages differ from 40, as first written. Radical 37: counts `with` twice (+1), the three variant shapes as one (−2), omits the ENUM LITERAL shape (−1) and the separator rule (−1). Conservative 39: counts `String` and `Int` (+2), omits both bracket pairs (−2) and the ENUM LITERAL shape (−1). Both arithmetic totals are internally consistent; the units differ. Corrected 2026-11-08 (section 10): the radical page now counts 36 today and 29 proposed (`with` once, two new shapes); the conservative page keeps 39 today and proposes 38.

## 2. The two proposals side by side

**[Proposal]** keep / merge / cut / forbid per cell. "Rests on" names the closed decision a change would reopen. "Row" is the loved (`L n`) or hated (`H n`) table row the pages cite, corrected where section 10 found an error.

| Item | Today | Conservative | Radical | Rests on | Row |
|---|---|---|---|---|---|
| `type` | keep | keep | keep; absorbs `enum` | DL-061 | L15 |
| `enum` | keep | keep | merge into `type` (36 files) | DL-061, back to DL-060 | L22, H4 |
| `fn` | keep | keep | cut (142 files) | syntax spike 2026-11-05 | H10, L7 |
| `effect` (outbound, ENTRY LINE) | keep | keep | keep | DL-013, DL-130 | L18 |
| `migrate` | keep | keep | keep; absorbs `retire`; `vB` only | DL-022, DL-072 | H23 |
| `retire` line | keep | keep | merge into `migrate` (5 files) | DL-055, DL-057 | L22 |
| `redacted` | keep | keep; forbid more modifiers | keep | DL-059, DL-105, DL-112 | silent |
| `with` release | keep | keep; forbid a third `with` | keep | DL-089 | L18 |
| `with do else end` | grammar only | keep | cut (0 files) | DL-014, DL-015 | L26 for, L18 for cut |
| `rename` | keep | keep | cut, `a -> b` (20 files) | DL-022 | H10 |
| `add`, `drop` | keep | keep | keep | DL-022, DL-023, DL-028 | silent |
| `keep` | keep | keep | cut (5 files) | DL-055 | H10 |
| `days` | keep | keep, only unit | keep | DL-057 | silent |
| `\|>` | keep | keep | keep | DL-014, DL-086 | L5 |
| `->` | keep | keep; forbid `=>` | keep; also the rename arrow | spike, DL-022 | H8 |
| `!` | keep | keep | keep, one failure TYPE | DL-015, DL-092, DL-093 | L3, H11 |
| `\|` failure list | keep | keep; forbid `\|` variants | cut (1 file) | DL-015; D025, D027 | H11 |
| `<-` | grammar only | keep | cut (0 files) | 0004 owner decisions | L26 |
| `=` | keep | keep, one meaning | keep | spike, DL-082 | H8 |
| `+` | keep | keep; no interpolation | keep | 0001 acceptance 6; D028 | L16 |
| `,` | optional in `{ }` | required in every brace (57 files) | cut inside `{ }`, keep in `( )` (79 files) | none; D032 | H25 |
| `:` | keep | keep | keep | spike | silent |
| `.` | keep | keep; forbid field access | keep | DL-013, DL-129 | H19 |
| `{ }`, `( )` | keep | keep | keep | spike | silent |
| String, 5 escapes | keep | keep | keep | 0001 | L16 |
| Int literal | keep | keep | keep | slice 6b | silent |
| VERSION MARK `vN` | keep | keep; `fmt` canonical | keep | DL-070, DL-072, DL-080 | H23 |
| `//` | keep | keep, one form | keep | DL-132 | silent |
| `_` | keep | keep | keep | none recorded | silent |
| record literal | keep | keep | keep | spike | L15 |
| punning `{ f }` | keep | keep | keep | spike | L12 |
| `V(x)` | keep | keep | keep | DL-061 | L2 |
| bare `V` | keep | keep | keep | DL-100 | L2 |
| `V()` | keep | forbid (3 files) | cut (3 files) | none; D032 | H25 |
| ENUM LITERAL `A = "s"` | keep | keep | keep | DL-082 | silent |
| separator rule | optional comma | merge: one rule, comma | merge: one rule, whitespace | none; D032 | H25 |
| Ceiling | none | 39 by its unit, one in one out | none stated | D033 | H4, L22 |

## 3. Where they agree

**[Verified]** The agreed set is the cheapest minimum. Both pages:

- forbid `V()`; bare `V` is the one spelling (3 files, no decision reopened, D032 half).
- replace the optional comma with one fixed rule (direction differs, see section 4; no decision reopened, D032 other half).
- keep `type`, `effect`, `migrate`, `redacted`, `with` release, `add`, `drop`, `days`, `|>`, `->`, `!`, `=`, `+`, `:`, `.`, both bracket pairs, String, Int, `vN`, `//`, `_`, the record literal, punning, `V(x)`, bare `V`, the ENUM LITERAL.
- keep the PII forms, the replay semantics and the failure-as-value model untouched.
- propose a test on committed fixtures before any grammar change.

**Agreed minimum: 39 items** (40 minus `V()`), 6 top-level forms. Every further cut is in section 4.

## 4. Where they differ

**[Verified]** Each line: the item, the decision that would reopen, the fixture count.

- `fn`: radical cuts, conservative keeps. Reopens the syntax spike surface and DL-098. 142 files, 560 clause lines. No direct evidence row.
- `enum`: radical merges into `type`, conservative keeps. Reopens DL-061 (returns to DL-060). 36 files.
- `with … do … else … end` and `<-`: radical cuts before it is built, conservative keeps. Reopens DL-014 and the `else` check of DL-015. 0 fixtures, 1 highlight test.
- `|` failure list: radical cuts (one failure TYPE per signature), conservative keeps and forbids `|` for variants. Reopens DL-015; touches D027. 1 file.
- `retire` line and `keep`: radical folds into `migrate`, conservative keeps. Reopens DL-055, DL-057 (form only). 5 files.
- `rename` and `vA ->`: radical cuts both, conservative keeps. Reopens DL-022 (DL-072 spelling stays). 20 and 29 files.
- Separator direction: conservative requires the comma in every brace (57 files gain commas); radical forbids it inside `{ }` (79 files lose commas). No decision reopened; the compiler and the grammar already disagree (section 7).
- Ceiling: conservative pins 39 by its unit with one-in-one-out and a `Budget` field; radical states no ceiling. D033.

## 5. Short recommendations as options

**[Proposal]** Options, not advice. Ordered from cheapest to most expensive. "Saves" is in items of section 1. Items 1 and 2 are inside the conservative set (no reopen); items 3 to 8 need a reopen.

1. Forbid `V()` → saves 1, reopens none (D032), affects 3 files, row H25. Inside the conservative set.
2. One separator rule (direction open) → saves 0 (the rule stays, fixed), reopens none (D032), affects 57 or 79 files, row H25. Inside the conservative set.
3. Cut `|`; several failures become one `type` with variants → saves 1, reopens DL-015, closes D027 one way, affects 1 file, row H11. Needs a reopen.
4. Cut `with … do … else … end` and `<-` before build → saves 5, reopens DL-014 and DL-015 (`else`), affects 0 files, rows L26 against and L18 for. Needs a reopen; leaves no local failure branch.
5. Fold `retire` into `migrate`; cut `keep` → saves 1 item and 1 top-level form, reopens DL-055 and DL-057 (form only), affects 5 files, row L22. Needs a reopen.
6. Cut `rename` and `vA ->` → saves 1, reopens DL-022, affects 29 files (20 with `rename`), row H10. Needs a reopen.
7. Merge `enum` into `type` → saves 1, reopens DL-061 (back to DL-060), affects 36 files, rows L22 and H4. Needs a reopen.
8. Cut `fn` → saves 1, reopens the syntax spike surface, affects 142 files and 560 lines, no evidence row. Needs a reopen; the only cut with no row behind it.

## 6. What both pages miss

- **[Verified]** Counting unit. The pages count 37 and 39 for the same grammar and neither names which parser is the source. Section 1 fixes one unit; a ceiling without a unit cannot be checked.
- **[Verified]** The compiler and the grammar disagree today. [main.rs](../../experiments/0001-syntax-to-beam/src/main.rs) line 713 requires a comma between MIGRATE CHANGES; [grammar.js](../../integrations/zed-beaml/grammar.js) line 68 makes it optional. Both pages treat "today" as one surface. A separator decision must name the authority.
- **[Inference]** Agent-authored token cost. The design intent is "so that agents make fewer errors"; neither page measures tokens or error rates. `fn` is one token on 560 lines; a required comma is one token per field in 57 files. The smallest measurement (tokens per fixture before and after, errors per 100 generated lines) is not proposed by either page.
- **[Inference]** The `with … else` gap. Both pages leave failure branching undefined: the radical page cuts the form and sketches a `recover` clause with no hand-over rule; the conservative page keeps a form that no fixture compiles. Neither names the fixture of EXPERIMENT 0005 that would need the branch.
- **[Verified]** Generics and precedents. `List(T)` ([conservative](syntax-minimum-conservative.md), D029) is the first generic TYPE; the radical page says generics do not exist. [Syntax sentiment section 10](../concepts/syntax-sentiment.md#10-terraform-hcl-as-the-declarative-precedent): HCL added one block kind per request for twelve years with no budget (D033) and regretted interpolation as its only expression form (D028); [section 9](../concepts/syntax-sentiment.md#9-baml-as-the-nearest-precedent): BAML's complaints were structural (a separate language, churn), not about punctuation. Neither page uses section 10.

## 7. Smallest next test

**[Proposal]** One scratch run in `experiments/0004-generated-replay/`, no committed file changed. Copy [pipe.beaml](../../experiments/0004-generated-replay/slice6/pipe/pipe.beaml), [literals.beaml](../../experiments/0004-generated-replay/slice6/enum/literals.beaml) and [marks.beaml](../../experiments/0004-generated-replay/slice6/fmt/marks.beaml). Write each copy twice: bare `V` with a required comma, and bare `V` with whitespace only inside `{ }`. Run the existing slice 6 tests and `tree-sitter parse` on all six copies. Add one script that counts the spellings of `grammar.js` and the token table of `main.rs` under the unit of section 1 and prints both numbers. Pass: the generated Elixir is byte-equal to today's output for every copy that the compiler accepts; the script prints 40 for the grammar; `Approved()` fails with a help line. Fail: the compiler rejects one separator variant, or the two parsers give different counts; either result is evidence for D032 and for the ceiling unit. Both pages accept this: it is the conservative page's test plus the radical page's separator variant, and it reopens nothing. Half a day.

## 8. Questions for the OWNER

Ordered so that the first answer narrows the most. No recommendation.

1. Does the minimum reopen closed syntax decisions (DL-014, DL-015, DL-022, DL-055, DL-061, the spike), or only the undecided rows (D032)?
2. Which counting unit is the ceiling, and which number: 40 (section 1), 39 (conservative), 36 (radical, corrected), or lower?
3. D032: bare `V` only, and which one separator rule, comma in every brace or whitespace inside `{ }`?
4. Does `fn` go (142 files, 560 lines, no evidence row)?
5. Does `enum` merge into `type` (DL-061 back to DL-060, 36 files)?
6. One failure TYPE per signature, several failures as one `type` (DL-015, D027, 1 file)?
7. Does `with … do … else … end` go before it is built, and what hands a failure to a clause instead?
8. Do `retire`, `keep`, `rename` and `vA ->` fold into `migrate` (DL-022, DL-055, DL-057, 29 files)?

## 9. Decision class

**Migrate** (syntax, DL-139). Both pages say so. Nothing here is grammar until the OWNER answers section 8.

## 10. Defects found in the two proposals

**[Verified]** Corrected 2026-11-08: the High and Medium defects below, the DL-098 line and the H20 line are repaired in both proposal pages (each carries a correction line under its front matter). The Low items on `Policy` and `Approved()` stay as written. The line numbers below refer to the pages before the correction.

**[Verified]** Spot checks: 12 fixture counts of the radical page agree with `rg` (`fn` 142, `enum` 36, `|` 1, `retire` 5, `rename` 20, `migrate` 29, `redacted` 46, `+` 66, `with` release 6, commas in braces 79, union of the other cuts 69, `V()` 3 files). Links: 0 missing files, 0 bad anchors in either page (python check over every relative link). Neither page reopens a non-negotiable without saying so: exceptions, failures as values, hidden effects, replay and PII stay untouched or are named at each reopen.

**High**

- Both pages cite `H6` as "inconsistency" ([radical](syntax-minimum-radical.md) line 169; [conservative](syntax-minimum-conservative.md) lines 40, 44, 126). Row 6 of the [hated table](../../raw/research/2026-11-07-pl-syntax-sentiment/hated.md#ranked-table-the-top-26) is the borrow checker. The inconsistency row is `H8`; the theme is hated theme 6.
- [Conservative](syntax-minimum-conservative.md) line 40: "MIGRATE CHANGES … already require the comma" holds for the compiler only; the grammar makes it optional (section 6). The page's own test (line 158) would hit this disagreement.

**Medium**

- [Radical](syntax-minimum-radical.md) line 166: "DL-137 made `migrate` the one fate form". DL-137 closes D020, "One `migrate` block governs RESPONSE RECORDS and … database rows"; DL-125 made the fate declarative.
- [Conservative](syntax-minimum-conservative.md) line 34: 39 to 37 counts the separator rule as removed; a required comma is still one rule, so the proposed count is 38 by its own unit.
- [Radical](syntax-minimum-radical.md) line 20: `with` counted twice in 17 keywords; by spelling it is one. Line 19: `with … do … else … end` listed as a top-level form; it is an expression.
- [Conservative](syntax-minimum-conservative.md) line 27: `String` and `Int` counted as syntax; they are prelude names like `http.post`. Both pages omit the ENUM LITERAL shape from the inventory.
- [Radical](syntax-minimum-radical.md) lines 130 and 142 to 144: `migrate payments.authorize { retire 30 days }` gives `migrate` an operation head without versions, and `recover` needs a hand-over rule; both are new shapes counted as 0 items (line 147 admits the second).
- [Conservative](syntax-minimum-conservative.md) line 149: "changes every fixture"; 57 of 142 files have a `type` or `enum` block that needs commas, and every `migrate` block already has them.

**Low**

- [Conservative](syntax-minimum-conservative.md) line 24: `_` "decided by DL-098"; DL-098 does not mention the wildcard. No decision records it.
- [Conservative](syntax-minimum-conservative.md) line 126: `H20` cited as "one keyword for several concepts"; H20 is Scala implicits.
- [Conservative](syntax-minimum-conservative.md) line 102: a `Policy` value as a transport argument puts policy in an expression position; DL-126 keeps policy in declarations. The page should state that it reads the transport call as part of the declaration.
- [Radical](syntax-minimum-radical.md) line 169: "`Approved()` … 3 files"; `Approved()` is in 1 file, 3 files have a zero-argument `V()`.
- Neither page is listed in [wiki/index.md](../index.md) yet; this page is not either. Another worker edits the index today.

See also [syntax sentiment](../concepts/syntax-sentiment.md), [D026 to D034](decisions-to-be-made.md), the [syntax profile](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-syntax-profile.md), the [BEAML lens](../../raw/research/2026-11-07-pl-syntax-sentiment/beaml-lens.md) and the [glossary](../../GLOSSARY.md).
