# Plan: slice 6b, compiler for the decided forms

**[Proposal]** PLAN phase, 2026-11-07. Changes only task records. No production file, no commit.
Inputs: DL-013, DL-014, DL-015, DL-028, DL-029, DL-059, DL-062, DL-065, DL-081 to DL-097 in [the decision log](../../../../../wiki/planning/decision-log.md), [vertical integration](../../../../../wiki/concepts/vertical-integration.md), the 0004 README (slices 2 to 5), the [slice 6a ledger](../slice6-grammar/) and its corpus file `integrations/zed-beaml/test/corpus/constructors.txt` (read only), and `experiments/0001-syntax-to-beam/src/main.rs`.
Design decisions that the decision log does not settle: [decisions.md](decisions.md) (IDs `D6B-nn`, OWNER questions `Q6B-n`).

## Baseline (observed 2026-11-07, HEAD cd6c1211)

| Check | Result |
|---|---|
| `cargo test --no-fail-fast` (0001) | **[Verified]** pass: 11 unit tests, 14 CLI tests (25 total, 0 failed) |
| `cargo fmt --check` (0001) | **[Verified]** FAIL before any change: 4 hunks in `src/main.rs` (lines 209, 265, 3537, 3659) |
| `cargo clippy --offline --all-targets -- -D warnings` | **[Verified]** FAIL before any change: `needless_range_loop` at 3039, `type_complexity` at 3610 |
| `tests/slice3_types_test.py` | **[Verified]** 69 OK |
| `tests/slice5_syntax_test.py` | **[Verified]** 60 OK |
| `tests/slice5_squash_test.py` | **[Verified]** 24 OK |
| `tests/slice5_rewrite_test.py` | **[Verified]** 5 OK |
| `tests/stored_types_test.py` | **[Verified]** 33 OK |
| `tests/slice4_retire_test.py` | **[Verified]** 87 OK |
| `run.py` (full, releases), replay and arms tests | **[Unknown]** not run in PLAN (long, needs releases). Step 0 runs it once and records the baseline. |

Toolchain: cargo 1.94.0, rustc 1.94.0, Elixir 1.18.1 on OTP 27.

**[Inference]** The 0001 `run.py` runs `cargo fmt --check` and clippy, so it fails today. Step 0 repairs that first.

## What the compiler has today (facts the steps build on)

**[Verified]** in `main.rs`:

- `fn` names must start lowercase (`Checker::new`, "invalid function name"). `fn PaymentState` is rejected.
- Every clause needs `= body`. No signature line. A variable or `_` parameter needs `: TYPE`.
- Built-in TYPE: `String` only. The lexer has `Token::Number`, but `node()` does not accept it.
- Enum variants need parentheses (`Waiting()`); no literals. A bare `Authorized` is a variable name.
- Records are structural (`same_type`, unit test `interfaces_are_structural_and_exact`).
- Failure TYPES must be records (`failure_types` calls `record`). A failing fn body that is not a pipe always emits `{:ok, body}`.
- `Node::Pipe(head, steps)` is legal only as a whole body. Each body pipe is emitted by `emit_chain`, with one `ProbeSupport.span` per step. A fn with a pipe body has one clause.
- EFFECT output fields are `String` only. The RESPONSE RECORD stores the raw body (`body_base64`), `request` (the full EFFECT input), `unknown_keys` and the `type` key.
- No `redacted`, no `with`, no `fmt` command. The CLI is `beaml-spike SOURCE.beaml [--stored ...]`.
- Unreachable and non-exhaustive clauses are already compile errors (`validate`, `useful`). DL-087 holds for clauses today.
- All existing pipes in sources and tests hold an EFFECT step (checked with `rg`).

## Step order

Dependency order. One concern per step. One RED/GREEN round per step. Ledger root: `experiments/0004-generated-replay/workflow/2026-11-07/`.

| # | Step | Ledger | Depends on | Blocked by |
|---|---|---|---|---|
| 0 | Baseline hygiene (fmt, clippy, full run.py baseline) | `slice6b-hygiene/` | — | — |
| 1 | `Int` TYPE and integer literals | `slice6b-int/` | 0 | — |
| 2 | Failure position for any TYPE, E1 overlap check | `slice6b-failure/` | 1 | — |
| 3 | Record constructor `fn TypeName`, signature line, only way in | `slice6b-type-constructor/` | 2 | — |
| 4 | Enum literals, enum constructor, several signatures | `slice6b-enum/` | 3 | — |
| 5 | Pipe in any expression, constructors and variants as steps | `slice6b-pipe/` | 4 | — |
| 6 | `redacted` fields and `with` on EFFECTS | `slice6b-redacted/` | 0 | — |
| 7 | Decode of ENUM LITERALS from outside data, keep-value rule | `slice6b-decode-literals/` | 4, 6 | — |
| 8 | Decode through an enum constructor (K1, first match wins) | `slice6b-decode-constructor/` | 5, 7 | **Q6B-1** |
| 9 | An enum constructor is the only way to build its variants | `slice6b-enum-only-way-in/` | 4 | **Q6B-2** |
| 10 | `beaml fmt`: mark form (b), aligned clause and EFFECT columns | `slice6b-fmt/` | 1–6 | — |

Steps 6 and 10 do not need the enum steps for their logic. They run in this order because only one code-writing worker runs at a time and steps 7 and 6 both touch `emit_effect`.

Merges and splits against the candidate list:

- Candidate (1) needs `Int` first: DL-092 uses `type NonZeroInt { value: Int }`, DL-093 uses `-> String ! Int`. Split out as step 1.
- Candidate (2) comes before (1): the constructor example fails with `! IsZero`. So failure is step 2, the constructor step 3.
- Candidate (3) is split: compile forms (step 4), decode of literals (step 7), decode through a constructor (step 8, blocked).
- Candidate (5) merges into steps 7 and 8. `Unknown(String)` is already a legal declared variant; only the keep-value rule in decode is new.
- Candidate (4) stays one step (5). Step 3 already allows a constructor as a whole-body pipe step, because a failing constructor can only be called as a pipe step.
- Step 9 is new: DL-092 says every type gets the "same checked-constructor pattern"; whether that covers enum variants is open (Q6B-2).

## Steps in detail

Common rules for every step:

- Test-first applies to steps 1–10 (parser, type check and generated code are behavior). Step 0 is a no-behavior exception (formatting and two lint rewrites); its check is the unchanged test count and a byte-equal compiler output on the fixed sources.
- Checks, every step: `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` (from step 0 on), the six compile-level test files above, the step's own test file, and `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase.
- `payments.beaml` output stays byte-identical (`tests/payments.generated.snapshot`). Every existing reject keeps its message.
- Fixtures go to `experiments/0004-generated-replay/slice6/<step>/`. The step test file is `experiments/0004-generated-replay/tests/slice6_<step>_test.py`. Runtime checks compile the generated module with `elixirc --warnings-as-errors` and run asserts with `elixir`, like `0001/run.py`.
- Every decision of every class goes to the step `notes.md` (DL-097). A Repair that changes language behavior or a check also gets a decision-log entry at the end of the phase.
- Compiler events keep going to `.beaml/actions.jsonl`. No source text in events.
- Do not touch `integrations/zed-beaml/`.

### Step 0: baseline hygiene (`slice6b-hygiene/`)

- **Change.** `cargo fmt` on `main.rs`. Rewrite the loop at 3039 and add one `type` alias for the type at 3610. No behavior change.
- **Check instead of RED.** Test counts equal the baseline. Generated output of `example.beaml`, `payments.beaml` and the GEN `orders.beaml` is byte-equal before and after. Record the full `run.py` result as the slice 6b baseline.
- **Exclusion.** No other refactor.

### Step 1: `Int` (`slice6b-int/`)

- **Code.** `node()` accepts `Token::Number` as `Node::Int`. `check_type` knows `Int`. `pattern`, `expression`, `normalized`, `useful` (an `other-int` sentinel like `other-string`), `emit_node`, `__beaml_valid__` (`is_integer(v)`).
- **First RED.** Unit test `int_literals_and_patterns`: `fn f 0 -> String = "zero"  fn f n: Int -> String = "other"` compiles; `fn f 0 -> String = "zero"` alone is `non-exhaustive function: f`; `fn g -> Int = "x"` is a type mismatch. Today: the first source fails with "expected expression or pattern".
- **Fixture.** `slice6/int/int.beaml`.
- **Elixir shape.** `defp __beaml_valid__(v, <<73,110,116>>), do: is_integer(v)`; `defp __beaml_f(0), do: <<...>>`; `defp __beaml_f(_), do: <<...>>`.
- **Runtime check.** `f(0)` and `f(7)` give the two texts; `f("0")` raises `ArgumentError`.
- **Exclusions.** No arithmetic, no negative literals, no `+` on `Int`, no `Int` in EFFECT inputs or outputs (D6B-03).

### Step 2: failure position and overlap (`slice6b-failure/`)

- **Code.** `failure_types` accepts any declared TYPE and `String`, `Int`. New overlap check on every `fn` and EFFECT with `same_type`. `body`/`validate`: a body may have the output TYPE or one failure TYPE. `emit`: `{:ok, v}` or `{:error, v}` by the static TYPE. Record failure values are structs, as for EFFECT failures; struct modules are emitted whenever a record failure TYPE exists.
- **First RED.** Unit test `success_and_failure_types_never_overlap`: `-> String ! String` and `-> String ! Int | String` fail with an error that names `String` and a `help:` line; `fn f x: String -> String ! Int = 5` compiles. Today: `! Int` fails with `unknown type: Int`.
- **Second RED (same step).** Runtime: `fn check "" -> String ! Empty = Empty {}  fn check x: String -> String ! Empty = x` gives `{:error, %BeamlSpike.Empty{}}` and `{:ok, "a"}`. Today the first clause is a type mismatch.
- **Fixture.** `slice6/failure/overlap.beaml`, `slice6/failure/body.beaml`, reject sources inline in the test.
- **Elixir shape.** `defp __beaml_check(<<>>), do: {:error, %__MODULE__.Empty{}}`; `defp __beaml_check(v_x), do: {:ok, v_x}`; `defmodule Empty do ... defstruct [] end`.
- **Exclusions.** Generic `-> T ! E` (DL-093 "for later"). EFFECT failure rule (one record with `reason: String`) stays. Orders output must stay byte-identical (D6B-07).

### Step 3: record constructor (`slice6b-type-constructor/`)

- **Code.** Parser: `fn` without `=` is a signature line. Checker: an uppercase `fn` name must be a declared `type` (enums in step 4); output must be that TYPE; clause grouping under the nearest signature; nominal `same_type` for a TYPE with a constructor; record literal of such a TYPE only inside its own constructor clauses; a constructor as a whole-body pipe step and as a call; reject such a TYPE in EFFECT input, output, failure and in any field of them.
- **First RED.** Unit test `constructor_is_the_only_way_in`: the DL-092 fixture compiles; adding `fn make -> NonZeroInt = NonZeroInt { value: 1 }` fails with an error that names the constructor; `fn same p: Plain -> NonZeroInt = p` (equal fields) fails with a type mismatch. Today: `invalid function name: NonZeroInt`.
- **Fixture.** `slice6/type-constructor/nonzero.beaml`:
  `type IsZero {}`, `type NonZeroInt { value: Int }`, `fn NonZeroInt 0 -> NonZeroInt ! IsZero = IsZero {}`, `fn NonZeroInt n: Int -> NonZeroInt ! IsZero = NonZeroInt { value: n }`, `fn wrap n: Int -> NonZeroInt ! IsZero = n |> NonZeroInt`.
  A second fixture with a signature line and unannotated clauses: `fn Label text: String -> Label ! Empty`, `fn Label "" -> Label ! Empty = Empty {}`, `fn Label t -> Label ! Empty = Label { text: t }`.
- **Elixir shape.** `def new_NonZeroInt_1(a0)` (validity wrapper like every fn), `defp __beaml_new_NonZeroInt_1(0), do: {:error, %__MODULE__.IsZero{}}`, `defp __beaml_new_NonZeroInt_1(v_n), do: {:ok, %{<<118,97,108,117,101>> => v_n}}`. `wrap/1` calls it in a `with`.
- **Runtime check.** `wrap(0)` is `{:error, %IsZero{}}`; `wrap(5)` is `{:ok, %{"value" => 5}}`.
- **Exclusions.** Enum constructors, several signatures (step 4). Nested pipes (step 5). Decode through a constructor (Q6B-3).

### Step 4: enum literals and enum constructor (`slice6b-enum/`)

- **Code.** Parser: a variant without parentheses; `Variant = "text"`; a bare variant in expressions and patterns. Checker: literal rules (D6B-21), DL-088 one decode path, enum constructors (from step 3), several signatures, static call choice by TYPE (D6B-16), unreachable signature (D6B-23), unreachable literal.
- **First RED.** Unit test `enum_literals_and_constructor`: the fixture compiles; each reject compiles to an error: (a) an enum with a literal and a constructor (names DL-088 rule and both forms in `help:`), (b) a signature whose keys contain all keys of an earlier one with equal TYPES (`unreachable signature`), (c) two equal literals (`unreachable`). Today: `expected '('` at `Authorized =`.
- **Fixture.** `slice6/enum/enum.beaml`:
  `enum PaymentState { Authorized = "ok"  Pending = "pending"  Unknown(String) }`;
  `enum Outcome { Approved  Declined(String)  Other(String) }`;
  `fn Outcome status: String, reason: String -> Outcome`, clauses `"ok", _`, `"declined", reason`, `other, _`;
  `fn Outcome code: String -> Outcome`, clauses `"ok"`, `other`;
  `fn label Authorized -> String = "ok"` plus clauses for `Pending`, `Unknown(s)`.
- **Elixir shape.** Variants stay `{owner, variant, [args]}`. `def new_Outcome_1(a0, a1)`, `def new_Outcome_2(a0)`, each with its clauses in source order. ENUM LITERALS emit no new function in this step.
- **Runtime check.** `new_Outcome_1("declined", "card")` is `{"Outcome", "Declined", ["card"]}`; `new_Outcome_2("x")` is `{"Outcome", "Other", ["x"]}`.
- **Exclusions.** Decode (steps 7, 8). The variant restriction (step 9). Pipes in clause bodies (step 5).

### Step 5: pipe in any expression (`slice6b-pipe/`)

- **Code.** `Node::Pipe` moves from the body level into `node()`, weaker than `+`, ending at `,` and `)`. Step kinds: fn, EFFECT, constructor, variant with one payload. The one-clause rule and `emit_chain` with spans stay only for a pipe body with an EFFECT step. Other pipes compile to plain nested calls. A nested pipe with an EFFECT or failing step is a compile error (D6B-27).
- **First RED.** Unit test `pipe_in_any_expression`: the corpus clause `fn PaymentState "declined", reason -> PaymentState = reason |> DeclineReason |> Declined` (with a 1-input `DeclineReason` constructor) and `fn g p: P -> R = build(p |> prepare, x)` compile. Today: `a function with a pipe body has one clause in slice 1` and `expected ')'`.
- **Fixture.** `slice6/pipe/pipe.beaml` with the corpus constructor example of DL-082 (signature, clauses `"ok", _`, `"declined", reason`, `other, _`).
- **Elixir shape.** `defp __beaml_new_PaymentState_1(<<...declined...>>, v_reason), do: {"PaymentState", "Declined", [new_DeclineReason_1(v_reason)]}` (a failing `DeclineReason` in a whole-body pipe compiles to a `with`, without spans).
- **Runtime check.** Declined path gives the nested tuple. The orders and payments outputs stay byte-identical.
- **Exclusions.** Steps with arguments (`|> f(x)`). Nested failing steps.

### Step 6: `redacted` and `with` (`slice6b-redacted/`)

- **Code.** Parser: `field: redacted TYPE`; `with f1, f2` after the EFFECT target. Checker: D6B-29 to D6B-34. Emit: one helper per TYPE with redacted fields that drops them; the wire body keeps the `with` fields; spans, `ProbeSupport.event`, the RESPONSE RECORD `request` and the replay `request_mismatch` compare use the fully redacted value.
- **First RED.** Python test `slice6_redacted_test.py`, case R1: a GEN-like orders source with `card_holder: redacted String` in `Order` and an EFFECT without `with`: the generated `payments_authorize/1` sends a body without `card_holder`. Case R2: with `with card_holder` the wire body has it, but the RESPONSE RECORD `request`, the span input and the event have no `card_holder`. Case R3 rejects: `with` on a field that is not redacted, an unknown field, a duplicate, and a redacted field in the EFFECT output TYPE. Today: `type Order`: expected TYPE at `redacted`.
- **Fixture.** `slice6/redacted/orders.beaml`, `slice6/redacted/orders-with.beaml`, built with the empty RECORD SNAPSHOT.
- **Elixir shape.** `defp __beaml_redact__(v, <<"Order">>), do: Map.drop(v, [<<"card_holder">>])`; the post body is `Map.drop(a0, [...not named...])`; the span gets `__beaml_redact__(a0, "Order")`.
- **Runtime check.** Release-free: a loopback HTTP stub in the test captures the body; the capture file holds no redacted value (a unique marker string is not found anywhere in the run directory, spans included).
- **Exclusions.** Implicit flow (DL-029 target). Redacted fields in EFFECT outputs (Q6B-4). Dotted `with` paths. `redacted` in enum payloads and MIGRATE CHANGES.

### Step 7: decode of ENUM LITERALS (`slice6b-decode-literals/`)

- **Code.** `effects()` accepts an output field whose TYPE is an enum with literals. The decode maps the field's String: a literal gives its variant, any other String gives the keep-value variant, a non-String is a decode error. DL-065 check: an enum field in an EFFECT output needs a keep-value variant. Span attribute `unknown_fields`.
- **First RED.** Python test `slice6_decode_literals_test.py`: build with `type Payment { order_id: String state: PaymentState }`; replay of a record with `"state": "ok"` gives `Authorized`; `"state": "refunded"` gives `Unknown("refunded")`; `"state": 7` gives the typed reject `decode`. A literal enum without a keep-value variant in the output TYPE fails at compile time. Today: `slice 1 decodes String fields only`.
- **Fixture.** `slice6/decode-literals/orders.beaml`, records in `slice6/decode-literals/stored.jsonl` (hand-built, as the slice 2 RED fixtures).
- **Elixir shape.** `defp __beaml_literal_PaymentState(<<111,107>>), do: {"PaymentState", "Authorized", []}`, ..., `defp __beaml_literal_PaymentState(v) when is_binary(v), do: {"PaymentState", "Unknown", [v]}`, `defp __beaml_literal_PaymentState(_), do: :error`. The decode applies it to the field before `__beaml_valid__`.
- **Exclusions.** Enum fields in a versioned TYPE (D6B-39). Enum fields in EFFECT inputs (D6B-40). Constructor decode (step 8). The value run with Unknown counts (DL-031, not built).

### Step 8: decode through an enum constructor (`slice6b-decode-constructor/`) — blocked until Q6B-1 is answered

- **Code.** The decode of an output field whose enum has a constructor tries the signatures in source order (DL-085), with the keys from the parameter names (DL-084). DL-065 keep-value check on the last clause of each signature (D6B-50).
- **First RED.** Python test `slice6_decode_constructor_test.py`: the DL-082/DL-084 example; `{"status": "declined", "decline_reason": "card"}` gives `Declined(...)`; `{"status": "x", "decline_reason": ""}` gives `Unknown("x")`; a body with no signature's keys is a typed reject. A constructor whose last clause drops every open value (`fn PaymentState _, _ -> PaymentState = Pending`) fails at compile time.
- **Elixir shape.** `cond` over the signatures in source order: `Map.has_key?` and `__beaml_valid__` for each key, then `new_PaymentState_k`. Where the keys are read depends on Q6B-1.
- **Exclusions.** Lists as an external return TYPE (DL-084 "later").

### Step 9: enum variants only through the constructor (`slice6b-enum-only-way-in/`) — blocked until Q6B-2 is answered

- **Code.** Only if Q6B-2 answers yes: a variant expression of an enum with a constructor is legal only inside that constructor's clauses. Patterns stay free.
- **First RED.** `fn retry -> PaymentState = Pending` outside the constructor fails with an error that names the constructor.

### Step 10: `beaml fmt` (`slice6b-fmt/`)

- **Code.** `main()`: `beaml-spike fmt SOURCE.beaml`. Parse (and derive versions) first; an invalid source writes nothing and exits 1. Text edits from token ranges: VERSION MARK form (b) by D6B-43; aligned columns by D6B-44. `write_atomic` and `unified_diff` are reused. Event `fmt` with the count of changed lines.
- **First RED.** Python test `slice6_fmt_test.py`: (a) three single-line `fn PaymentState` clauses with different argument widths come out with `->` and `=` in one column, and the argument columns aligned; (b) two `effect` lines get aligned arrows and `=` (DL-013); (c) `type T v3 { ... }` with a chain `v1 -> v2 -> v3` loses the mark; a chain `v4 -> v5` without a mark gets `v5`; `type T v3` without a chain keeps its mark; (d) comments and blank lines stay byte-equal; (e) `fmt` twice is a no-op; (f) the compiled output before and after is equal except the `beaml-declaration-v1` byte offsets. Today: `fmt` is read as a source path (`cannot read source`).
- **Fixture.** `slice6/fmt/*.beaml` with expected `*.formatted.beaml` written by hand from DL-081 and DL-083.
- **Exclusions.** Whitespace other than the aligned columns and the mark, line breaking, `--check`, editor integration, `beaml check --json`.

## Exclusions for all of slice 6b

- Generics, guards, `with ... do ... else ... end` expressions (DL-014, not in the compiler yet), arithmetic.
- The live query of stored TYPE VERSIONS (DL-094).
- MIGRATE CHANGES that map values; so the DL-065 rule "in `migrate` steps" has no syntax to check yet. **[Inference]** It becomes testable when a value-mapping MIGRATE CHANGE is decided.
- Implicit PII flow (DL-029 target).
- `integrations/zed-beaml/` (another worker).

## Risks

- **[Inference]** Steps 3 and 4 change `same_type` (nominal for constructor TYPES). Every caller of `same_type` (`require_type`, the pipe step check, `--stored` compare) must be checked. The `--stored` TYPE VERSION compare uses field lists, not `same_type`.
- **[Inference]** Step 5 changes the AST of every pipe. Error message order of `bad/*.beaml` (unknown step, type mismatch, undeclared failure) must stay.
- **[Inference]** Step 6 changes the RESPONSE RECORD `request` for TYPES with redacted fields only. Sources without `redacted` must give byte-equal output.
