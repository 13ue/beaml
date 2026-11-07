# Slice 6a: grammar for the forms of DL-082 to DL-093

**[Requirement]** Task contract from the main agent, 2026-11-07. Grammar and highlighting only.

## Goal

Extend the tree-sitter grammar in `integrations/zed-beaml/`. The forms of DL-082 to DL-093 must parse with 0 ERROR nodes and highlight with the correct classes.

## Forms in scope

Source: `wiki/planning/decision-log.md`, `wiki/concepts/vertical-integration.md`.

1. ENUM LITERALS: `enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }` (DL-082 L).
2. Enum constructor clauses: `fn PaymentState "ok", _ -> PaymentState = Authorized` (DL-082 C2).
3. Signature lines without a body: `fn PaymentState status: String, decline_reason: String -> PaymentState` (DL-084). Several signatures and clauses of one constructor in a row (DL-084, DL-085).
4. Record constructor: `type NonZeroInt { value: Int }` and `fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }` (DL-092).
5. Failure position `-> T ! E1 | E2` on a `fn` (DL-092, DL-093). The overlap rule of DL-093 is a compiler check. The grammar parses `-> String ! String` without an ERROR node.
6. Pipe with constructors and variants as steps, also inside an argument: `reason |> DeclineReason |> Declined` (DL-086).
7. Bare variants in expressions (`Authorized`) get the constructor class `c`. Today they have no class.
8. Effect redaction release: `effect payments.authorize Order -> Payment ! PaymentError = http.post("payments/authorize") with card_holder` (DL-089). The concrete form is recorded in DL-089, so it is in scope.

## Exclusions

- `beaml fmt` and the column alignment (DL-081, DL-083).
- Compiler changes (`main.rs`), all semantic checks: DL-085 order, DL-087 unreachable clauses, DL-088 one decode path, DL-092 constructor-only access, DL-093 overlap.
- Generics (`-> T ! E` as type parameters).
- Guards and conditions in clauses (not decided).

## Pass rule

- Every new corpus example parses with 0 ERROR nodes and matches its expected tree.
- Every new highlight assertion passes (`tree-sitter test` runs `test/highlight/`).
- All existing corpus and highlight tests keep passing, including the `:error` cases in `errors.txt`.
- `tree-sitter generate` reports no new conflict.
- `python3 integrations/zed-beaml/preview.py --chat <new file>` renders the new forms. Variants and constructor names show class `c`.
- `grammars/beaml.wasm` is rebuilt from the new grammar.
