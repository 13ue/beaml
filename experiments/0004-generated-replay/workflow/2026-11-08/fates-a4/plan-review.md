# Plan review: fates-a4 (`fmt` and tree-sitter for VERSION MARKS, MIGRATE STEPS and fate lines)

**[Proposal]** PLAN CHECK phase, 2026-11-08, HEAD `3e52069e`. Fresh context, normal check (not Devil's Advocate).
Target: [plan.md](plan.md), [plan.json](plan.json). By: Opus (plan-check fates-a4) for every item in this file.

## Verdict

**GO for RED.** No critical or high objection. Three medium objections; the RED worker folds them into the tests.
GREEN of the `fmt` half follows the DL-139 calls below.

## Evidence (observed at `3e52069e`, scratch copies, release binary `beaml-spike` of 14:03)

- **[Verified]** `fmt_mark` (main.rs 7497) and `bodies` (7541) read as the plan says. `bodies` takes `type` and `enum`
  only. TYPE bodies have no commas, so the comma handling for MIGRATE bodies is new code.
- **[Verified]** Probe: `migrate Amount v1 -> v2 {quarantine value ,  quarantine currency}` (DL-172) and
  `{map channel "app" -> Mobile,` newline `quarantine channel "fax"}` both pass `validate`; `fmt` exit 0, body unchanged,
  mark removed. So these forms can be RED inputs.
- **[Verified]** `redact f` and `retire f keep N days` in a MIGRATE STEP parse, but `validate` rejects them (QF-9, QF-4).
  `fmt` cannot format them. Only the tree-sitter half sees them.
- **[Verified]** Every `fmt` input in a test (`slice6/fmt/*.beaml`, the N15 db fixtures, the seven fates fixtures, the 0005
  source and variants) has single-change bodies written `{ change }`. PF-19 changes none of them.
- **[Verified]** `git ls-files "…/slice*/*.beaml"` is recursive (167 files, the fates fixtures included). The plan's rule
  "no new tracked `.beaml` under `slice*/`" is right and needed. `integrations/zed-beaml/test/highlight/fates.beaml` is
  outside every guard glob. `byte-guard.json` rows are compile outputs, not `fmt` outputs. No pin moves.
- **[Verified]** `grammar.js` has `word: $.identifier`; `(version) @number` maps to class `c` in `preview.py`. G2 and the
  preview check agree.

## DL-139 classification (for the main agent; the main agent records its own call, By: Fable)

| Question | Syntax / line form / keyword? | Class of the default | Why |
|---|---|---|---|
| QA4-1 mark kept on a fate chain | no | default may be built; card must say "overrides DL-104 A as written" | parser accepts both forms; build output equal (plan, verified); B or C is one repair step (C = HEAD, B = one `fmt_mark` arm + one byte-guard row). Not inside DL-148: it amends an OWNER rule (DL-104), backed by the DL-155 effect line |
| QA4-2 MIGRATE body layout (PF-19) | no | default may be built | whitespace only; parser accepts every layout; no tested fixture changes; extends DL-148 (1) by analogy, not inside its letter |
| QA4-3 no table in MIGRATE bodies | no | default may be built | status quo, no code |

**[Inference]** The plan line "DL-139: syntax and layout are OWNER territory" misquotes DL-139. DL-139 names syntax,
record formats and host-called names. Layout is OWNER-decided by precedent (DL-104, DL-148), not by the DL-139 limit.
**[Inference]** The tree-sitter half adds no syntax. It mirrors forms the compiler parses and the OWNER chose (DL-155,
DL-156; DL-155 effect names "grammar, fmt, tree-sitter"). DL-171 (no grammar changes before D051) concerns the language
grammar. A D051 answer may later rename these forms; then G1 and G2 change with them.

**RED tests that depend on no QA4 answer (write now):** G1, G2, G3, T2b (existing guard), T5 (guard; a comment body
stays under every option). T1, T2, the `fmt_mark` unit case and N17 (once a3 lands) depend on QA4-1. T3, T4, T6 depend
on QA4-2 and QA4-3 (their expected texts hold no columns).

## Objections (max three)

**O1 · medium · Not every built fate form reaches the `fmt` tests or the corpus.**
T3 lists "owner TYPE step, enum step, `rename` beside a fate line, CRLF". It does not name DL-172 (two `quarantine`
lines for one constructor TYPE), `quarantine <field> "lit"`, or `map <field> "lit" -> C`. G1 says "the five fate forms";
the parser has seven shapes. Consequence: a member split that breaks on `<field> "lit"` or on a second `quarantine`
passes the slice. Resolving test: T3 subTests for `{quarantine value, quarantine currency}` and
`{map channel "app" -> Mobile, quarantine channel "fax"}` (both validate at HEAD, probed). G1 names all seven shapes:
`quarantine f`, `quarantine "l"`, `quarantine f "l"`, `map "l" -> C`, `map f "l" -> C`, `redact f`,
`retire f keep N days`, plus two `quarantine` lines in one body.

**O2 · medium · "A member keeps its comma" copies stray spaces; idempotence is checked on one input only.**
Members are source slices. The valid input `quarantine value ,  quarantine currency` (probed, exit 0) gives
`quarantine value ,` on its own line. A leading-comma layout (`a` newline `, b`) moves the comma to the wrong member.
Both outputs are fixed points, so T6 does not see them. Resolving test: a T3 subTest with ` ,` and with a leading comma;
expected `quarantine value,` (comma directly after the change). T6 runs the second `fmt` on every T3 and T4 output,
including the multi-line single change and a body with blank lines.

**O3 · medium · The keyword control in G1 is thinner than R2 says.**
R2 promises a field named `map:` as a control; the G1 row lists only `fn map x: String -> String = x`. A field named
`map`, `quarantine` or `redact` inside a MIGRATE body (`rename map -> route`, `quarantine map`, `drop redact: String`)
is the position where keyword extraction can go wrong. Consequence: a wrong `ERROR` or a keyword colour on a field name
passes G1 and G2. Resolving test: G1 controls for `type T { map: String }`, `rename map -> route`, `quarantine map`;
G2 asserts those names are `property`, not `keyword`.

Noted, not objections: the `redact` and `retire` corpus forms mirror parser forms that QF-4 and QF-9 may still change
(low). G3 and N17 skips count as missing checks (plan already says so).

## Decisions (By: Opus, plan-check fates-a4)

**Repair**
→ GO statt Stop, weil no objection is critical or high
⠀⠀↳ commits us to: O1 to O3 in RED
→ QA4-1/2/3 buildable defaults statt OWNER wait, weil no grammar change and each repair is one step
⠀⠀↳ commits us to: one explicit OWNER card each (DL-139 addition)

**Undo**
→ probes on scratch copies only
→ O3 as medium, not high: no current source uses these names
