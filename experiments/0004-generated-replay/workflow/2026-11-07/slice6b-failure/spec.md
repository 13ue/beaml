# Slice 6b step 2: the failure position and the overlap check

Step: [plan.md, Step 2](../slice6b-plan/plan.md#step-2-failure-position-and-overlap-slice6b-failure), `plan.json` step `failure`.
Decisions: [D6B-04 to D6B-10](../slice6b-plan/decisions.md). Decision log: DL-092, DL-093 in [decision-log.md](../../../../../wiki/planning/decision-log.md).
Review note: [plan-review.md (5), Step 2](../slice6b-plan/plan-review.md). Assert the D6B-09 text, not "names String".

## Contract

- After `!` on a `fn`, any TYPE can stand: `String`, `Int`, a record or an enum (D6B-04).
- The TYPE of a clause body decides the result. A body of the output TYPE gives `{:ok, v}`. A body of a failure TYPE gives `{:error, v}` (D6B-05). A whole-body pipe can end in either.
- A record failure value is the failure struct `%__MODULE__.T{field: v}` with atom keys. A struct module is emitted for each record failure TYPE, also without an EFFECT (D6B-07). A non-record failure has no struct module.
- The success TYPE must not be a failure TYPE. `same_type` decides, so two records with equal fields overlap (D6B-06). The check runs on every `fn` and every EFFECT (D6B-08).
- Overlap text on a `fn` (D6B-09):
  `error: fn f: the success TYPE String is also a failure TYPE`
  `  help: give the failure a TYPE of its own (for example type FError { reason: String }), or remove String after !`
- A structural overlap adds `: S has the same fields` to the error line and names `S` in the help line.
- An EFFECT overlap has the same error line with `effect <name>`. Its help line has no "remove" part, because an EFFECT needs one failure TYPE.
- A body of neither TYPE: `type mismatch: expected String ! Int, got E`. A fn without `!` keeps the text of today.
- A variant after `!` stays `unknown type: Short` and gets `  help: Short is a variant of the enum Why, not a TYPE; write Why` (D6B-10).
- An `Int` at any depth of an EFFECT failure TYPE: `effect payments.authorize: slice 6b fails with String fields only, not O.code`.

## Pass rule

- `python3 -B experiments/0004-generated-replay/tests/slice6_failure_test.py`: 19 of 19 pass, 14 of 14 runtime subtests pass.
- Every reject gives exit 1, no stdout and the exact text in the test.
- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass.
- `slice6_int_test.py` and the slice 3 to 5 compile-level tests pass. The `payments.beaml` and orders outputs stay byte-identical (D6B-07).

## Exclusions

- No generic `-> T ! E` (DL-093 "for later").
- The EFFECT failure rule (one record with `reason: String`) stays.
- No constructor (step 3). No bare variant (step 4). No validity check on the `{:error, v}` value (notes.md, decision 9).
- Do not touch `integrations/zed-beaml/`.
