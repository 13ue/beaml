# Plan check: slice 6a grammar

**[Verified]** Fresh-context PLAN CHECK, 2026-11-07. This is no Devil's Advocate round. Scope: consequences only.

## Verdict

PASS. No critical or high objection. Two medium notes and one low note. The plan can go to RED.

## Evidence

Probe in a scratch copy with `/private/tmp/beaml-zed-highlighting/tools/tree-sitter` (0.26.5). No production file changed.

- **[Verified]** RED fails today for the stated reason. The ENUM LITERAL `=` gives 4 ERROR nodes. The signature line has no body, so it joins the next clause. The DL-089 effect gives ERROR at `with`.
- **[Verified]** The 4 minimal grammar changes of the plan give `generate` with no conflict. `tree-sitter test` keeps 17/17 corpus and 3/3 highlight files.
- **[Verified]** After the change, `parse -q` exits 0 for the RED example, the DL-089 effect, a body-less signature with `! E | F`, and `fn k 0 -> Int = 0`.
- **[Verified]** An effect body `with … do … end with card_holder` parses. The `with` keyword after the body does not conflict with `with_expression`.

## Decision text against the planned forms

- DL-082 L and C2: the RED example is the DL text word for word.
- DL-084, DL-085: several signatures and clauses in a row parse. The order rule stays a compiler check.
- DL-086: `reason |> DeclineReason |> Declined` parses left-associative.
- DL-089: the effect line is the DL text word for word.
- DL-092: `type NonZeroInt { value: Int }` and the record literal in the clause parse. `IsZero {}` is an example of the plan, not DL text. It is legal grammar.
- DL-093: `-> String ! String` parses. The overlap is a compiler check. This agrees with the DL.

No planned form contradicts a decision.

## Notes

1. **Medium. MISSING nodes can pass the pass rule.**
   → Wrong outcome: a worker writes the expected tree from the parser output. A `(MISSING …)` node is no ERROR node, so "0 ERROR nodes" passes.
   → Smallest test: `rg -n 'ERROR|MISSING' test/corpus/constructors.txt` is empty, and `parse -q` exits 0 for each new example.
2. **Medium. A capture without a predicate can pass in the CLI and fail in Zed.**
   → Wrong outcome: the worker adds an uppercase `@constructor` pattern and keeps the old `(pipe right: (identifier) @function)` or `(function_clause name: (identifier) @function)` without `#not-match?`. The CLI can show `constructor`, Zed can show `function`.
   → Smallest test: every pattern on `function_clause name:` and `pipe right: (identifier)` in `highlights.scm` has a `#match?` or `#not-match?` predicate.
3. **Low. The parent list for bare variants misses `add_operation value`.**
   → Wrong outcome: `add state: PaymentState = Pending` in a MIGRATE STEP shows `Pending` with no class. This form is likely for a field with an enum default.
   → Smallest test: one highlight assertion on `Pending` in an `add` line. Also `effect_declaration body` if it can be a bare variant.

## Missing forms

- **[Verified]** No compiler code uses this grammar (plan, Callers). A later compiler slice does not depend on it.
- **[Inference]** No further form of DL-082 to DL-093 is missing. Generics and guards stay excluded, as in the spec.

## Simpler change

- **[Inference]** None found. The 4 grammar edits are one `optional` or one choice item each. The parent-scoped captures are needed, because a capture on every uppercase `identifier` also hits `(type (identifier))`.

## Limits

- `preview.py` and `--wasm` were not run in this check.
- The probe used the plan's direction, not the worker's final grammar.
