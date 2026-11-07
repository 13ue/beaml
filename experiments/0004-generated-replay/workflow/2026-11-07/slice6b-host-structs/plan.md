# Plan: slice 6b step 11, constructor TYPES are structs at the host

**[Proposal]** PLAN phase, 2026-11-07. Task records only. No production file, no commit, no `run.py` run.
Decision: DL-106 (Q6B-6, B) in [the decision log](../../../../../wiki/planning/decision-log.md). Also read: DL-092, DL-093, DL-099, DL-101, DL-105, DL-107, DL-108, DL-109; the [slice 6b plan](../slice6b-plan/plan.md), its [decisions](../slice6b-plan/decisions.md) and [plan review](../slice6b-plan/plan-review.md); the GREEN sections of the [step 2](../slice6b-failure/notes.md), [step 3](../slice6b-type-constructor/notes.md), [step 5](../slice6b-pipe/notes.md) and [step 8](../slice6b-decode-constructor/notes.md) ledgers; the [step 6 plan](../slice6b-redacted/plan.md); `experiments/0001-syntax-to-beam/src/main.rs`.
Design decisions that DL-106 does not settle: [decisions.md](decisions.md) (D6B-73 to D6B-83, OWNER question Q6B-16). Machine form: [plan.json](plan.json).
By: Opus (PLAN, slice6b-host-structs) for every proposal in this file (DL-107).

"Constructor TYPE" below means a record `type T` with a constructor `fn T` (DL-092). It is not a glossary term yet (D6B-83).

## Facts the step builds on (observed in `main.rs` at HEAD 8924cb3f)

- **[Verified]** A record value is a map with String keys. `emit_node` emits `Node::Record` as `%{<<...>> => v}` for a literal and for a pattern (one code point).
- **[Verified]** `__beaml_valid__(v, "T")` for a record is `is_map(v) and map_size(v) == N and __beaml_valid__(Map.get(v, <<"f">>), ...)`. Nested fields go through the same function, so a nested check follows from the outer one.
- **[Verified]** Every public `def` checks its inputs with `__beaml_valid__` and raises `ArgumentError, "invalid BEAML input"`. Its output check raises `"invalid BEAML output"`.
- **[Verified]** Record failure TYPES are nested struct modules with atom keys (`structs()`, `emit_structs`, step 2 G11, G12; step 8 G3 puts them at the top of `BeamlSpike` when a clause body builds them).
- **[Verified]** `result()` builds a failure struct from a non-literal body with `Map.get(value, <<"f">>)` (step 2 G10).
- **[Verified]** A constructor is the public `def new_T_k(...)` (step 3 G6). The decode through a constructor calls it (step 8 G4, `__beaml_from_T`).
- **[Verified]** D6B-19 still rejects a constructor TYPE in an EFFECT input, also in a nested field (step 8 G1, P2). So `ProbeSupport.json/1` never encodes a constructor value, and the span input `p0` of an EFFECT flow is never a struct.
- **[Observed]** Record constructors in fixtures: `NonZeroInt` (`slice6/constructor/nonzero.beaml`, `plain.beaml`, `slice6/pipe/pipe.beaml`), `Pair` (`pipe.beaml`), `DeclineReason` (`slice6/enum/constructor.beaml`, `slice6/decode-ctor/orders.beaml`), `Amount` (`decode-ctor/orders.beaml`), `F` (inline `CALL_SOURCE` in `slice6_constructor_test.py`). No arm, slice 2 to 5 or payments source has one.

## Change

1. **Struct module per constructor TYPE** (D6B-73). `defmodule T do defstruct [:f1, :f2] end` at the top of `BeamlSpike`, in the same place as the failure structs. A TYPE that is a constructor TYPE and a failure TYPE gets one module.
2. **`T.new/1`** in that module (D6B-74, Q6B-16). It calls the constructor and always returns `{:ok, struct}` or `{:error, failure}`.
3. **Literal and pattern** of a constructor TYPE emit `%__MODULE__.T{f: v}` (D6B-75). Plain records keep `%{<<"f">> => v}` (DL-106).
4. **Input and output check** (D6B-76). `__beaml_valid__(v, "T")` for a constructor TYPE is `is_struct(v, __MODULE__.T)` plus the field checks through `Map.get(v, :f)`. A map of the right shape fails, also in a nested field and in an enum payload.
5. **Failure through a pipe** (D6B-77). `result()` passes a constructor TYPE value through unchanged; it does not rebuild it with String-key `Map.get`.
6. **Decode** (D6B-78). The step 8 decode gets the struct from `new_T_k`. The shape check uses the new `__beaml_valid__`. The RESPONSE RECORD (today and in 6a) holds wire values, never a struct.

## First failing test: `tests/slice6_host_struct_test.py`

Harness: the step 3 runtime harness (generated module only, `elixirc --warnings-as-errors`, `elixir` asserts, no ProbeSupport). Fixture `slice6/host-structs/nonzero.beaml` = `slice6/constructor/nonzero.beaml` plus `type Plain { value: Int }`, `fn same p: Plain -> Plain = p`, `type Box { n: NonZeroInt }`, `fn unbox Box { n } -> NonZeroInt = n`, the D6B-77 fn `fn twice n: Int -> String ! NonZeroInt | IsZero = n |> NonZeroInt`, and (plan repair O2) `enum Wrap { Has(NonZeroInt) }`, `fn wrapped w: Wrap -> Wrap = w`.

- **H1 (first RED).** `BeamlSpike.keep(%{"value" => 4})` raises `ArgumentError` with `invalid BEAML input`. The value is valid, so a GREEN that runs the constructor on the map cannot pass. Today (observed in the step 3 test `keep_passes`): it returns the map. By: Opus (PLAN REPAIR, slice6b-host-structs) (O1)
- **H1g (guard, passes before and after).** `BeamlSpike.keep(%{value: 4})` (atom keys, no `__struct__`) raises `invalid BEAML input`. It fails on a GREEN that checks atom keys without `is_struct`. By: Opus (PLAN REPAIR, slice6b-host-structs) (O1)
- **H2.** `BeamlSpike.NonZeroInt.new(3) == {:ok, %BeamlSpike.NonZeroInt{value: 3}}`; `BeamlSpike.NonZeroInt.new(0) == {:error, %BeamlSpike.IsZero{}}`; `BeamlSpike.NonZeroInt.new("3")` raises `invalid BEAML input`. Today: `BeamlSpike.NonZeroInt` does not exist.
- **H3 (nested).** `BeamlSpike.unbox(%{"n" => %{"value" => 0}})` raises `invalid BEAML input`; `BeamlSpike.unbox(%{"n" => s})` with `{:ok, s} = BeamlSpike.NonZeroInt.new(4)` returns `s`.
- **H3e (enum payload depth, D6B-76).** `BeamlSpike.wrapped({"Wrap", "Has", [%{"value" => 4}]})` raises `invalid BEAML input` (tag in the binary form that the compiler writes); the same tuple with the struct from `NonZeroInt.new(4)` returns it. By: Opus (PLAN REPAIR, slice6b-host-structs) (O2)
- **H4 (success values).** `BeamlSpike.wrap(5) == {:ok, %BeamlSpike.NonZeroInt{value: 5}}`.
- **H5 (plain record keeps its form).** `BeamlSpike.same(%{"value" => 0}) == %{"value" => 0}`.
- **H6 (guard, passes before and after; not a RED; failure through a pipe, D6B-77).** `BeamlSpike.twice(4) == {:error, %BeamlSpike.NonZeroInt{value: 4}}`; `BeamlSpike.twice(0) == {:error, %BeamlSpike.IsZero{}}`. Today `result()` rebuilds the struct from a String-key map, so H6 passes; it fails on a GREEN that forgets D6B-77. By: Opus (PLAN REPAIR, slice6b-host-structs) (O3)
- **H7 (stated limit, DL-106).** `test_limit_deliberate_struct_literal_is_not_caught`: `BeamlSpike.keep(%BeamlSpike.NonZeroInt{value: 0})` returns the struct. The test name and its docstring say that it records the limit, not a wanted outcome.
- **H8 (byte guard).** Every source without a record constructor gives byte-equal output against the pre-step compiler (a `git archive` build of the base commit, as step 5 S12 and step 8). At least: `arms/gen/orders.beaml`, `slice2/reuse/orders.beaml`, all `slice2` to `slice5` sources, `slice6/int`, `slice6/failure`, `slice6/decode`, `slice6/enum/enum.beaml`, and `payments.beaml` against `tests/payments.generated.snapshot`.
- **H9 (Q6B-16, waits for the answer).** `BeamlSpike.Pair.new(...)` for the two-parameter constructor of `pipe.beaml`. The form follows Q6B-16. Before the answer, H9 is an open case, not a pass.

## Plan repair

- O1: H1 uses the valid value `4`; guard H1g adds the atom-key map. By: Opus (PLAN REPAIR, slice6b-host-structs)
- O2: H3e adds the enum payload depth `Wrap { Has(NonZeroInt) }`. By: Opus (PLAN REPAIR, slice6b-host-structs)
- O3: H6 is labelled a guard. The RED review does not count it as RED. By: Opus (PLAN REPAIR, slice6b-host-structs)
- Q6B-16 gets option C (keyword list), see [decisions.md](decisions.md). By: Opus (PLAN REPAIR, slice6b-host-structs)

## Existing assertions that change (each by name)

| File | Assertion | Today | After step 11 |
|---|---|---|---|
| `slice6_constructor_test.py` | `constructor_ok` | `new_NonZeroInt_1(3) == {:ok, %{"value" => 3}}` | `{:ok, %BeamlSpike.NonZeroInt{value: 3}}` |
| `slice6_constructor_test.py` | `wrap_ok` | `wrap(5) == {:ok, %{"value" => 5}}` | `{:ok, %BeamlSpike.NonZeroInt{value: 5}}` |
| `slice6_constructor_test.py` | `read_pattern` | `read(%{"value" => 4}) == 4` | `read(%BeamlSpike.NonZeroInt{value: 4}) == 4` |
| `slice6_constructor_test.py` | `keep_passes` | `keep(%{"value" => 4}) == %{"value" => 4}` | the struct in and out; the map case moves to H1 |
| `slice6_constructor_test.py` | `plain_ok` | `new_NonZeroInt_1(2) == {:ok, %{"value" => 2}}` | `{:ok, %BeamlSpike.NonZeroInt{value: 2}}` |
| `slice6_constructor_test.py` | `call_form` | `mk("x") == %{"reason" => "x"}` | `%BeamlSpike.F{reason: "x"}` |
| `slice6_constructor_test.py` | build lines 96 and 105 | `defp __beaml_new_NonZeroInt_1(v_n), do: {:ok, %{<<value>> => v_n}}` | `{:ok, %__MODULE__.NonZeroInt{value: v_n}}` |
| `slice6_pipe_test.py` | `record_field_in_constructor` | `new_Pair_1("x", "y") == %{"a" => "(x)", "b" => "y"}` | `%BeamlSpike.Pair{a: "(x)", b: "y"}` |
| `slice6_pipe_test.py` | `first_clause_ok`, `second_clause_ok` | `{:ok, %{"value" => 2}}`, `{:ok, %{"value" => 3}}` | `%BeamlSpike.NonZeroInt{value: ...}` |
| `slice6_enum_test.py` | line 38 (pipe clause), `call_pair` | payload `%{"text" => "card"}`, `%{"text" => "cvc"}` | payload `%BeamlSpike.DeclineReason{text: ...}` |
| `slice6_decode_ctor_test.py` | `EUR` (line 52), so every `ok(...)` result | `%{"value" => "12.50", "currency" => "EUR"}` | `%BeamlSpike.Amount{value: "12.50", currency: "EUR"}` |
| `slice6_decode_ctor_test.py` | `declined_via_pipe`, `replay_declined` | payload `%{"text" => "card"}` | `%BeamlSpike.DeclineReason{text: "card"}` |

- Not changed: the wire inputs `eur`, `st` and the stored records of `slice6_decode_ctor_test.py` (outside data stays JSON), every reject text, `slice6_fmt_test.py` (its case f compares two compiles of the same source), `slice6_failure_test.py`, `slice6_int_test.py`, `slice6_decode_test.py`, `cli.rs`.
- **[Inference]** The `slice6_struct_order_test.py` sources have no record constructor (grep). Their bytes stay.

## Byte changes

- **Change:** the outputs of `slice6/constructor/*.beaml`, `slice6/pipe/pipe.beaml`, `slice6/enum/constructor.beaml`, `slice6/decode-ctor/orders.beaml`, `slice6/fmt/clauses*.beaml` (compiled only inside `slice6_fmt_test.py`), and the inline test sources with a record constructor.
- **No change:** every arm, slice 2 to 5, payments and orders output (H8). So DL-110 does not touch step 11: no arm line reads a constructor value.

## Checks

- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` (0001). New unit test `constructor_types_are_structs` (emit of literal, pattern and `__beaml_valid__`).
- The six compile-level test files, every `slice6_*_test.py`, the new test file.
- `python3 -B experiments/0004-generated-replay/run.py` once at the TEST phase.
- Compiler events keep going to `.beaml/actions.jsonl`; the harness check "no source text, no path in events" runs on every compile.

## Order

- **[Proposal]** After 6a, before step 12, before 6b and 6c. Reasons:
  - 6a is unblocked (Q6B-10 is DL-110) and ends the LIB comparison. Step 11 changes no arm byte, so it does not depend on 6a for its logic. Both edit `slice6_decode_ctor_test.py`; one code-writing worker at a time, so one runs first.
  - Step 12 needs the struct form: its span input rule (D6B-88) treats a struct head as a non-plain record.
  - 6b plans `Map.from_struct/1` for a struct input (D6B-71) and Q6B-15 names "a TYPE without a constructor". With step 11 first, 6b builds on the real struct form.
- 6b then must check that the redaction helpers also handle a struct inside a plain record field (D6B-71 covers the input value only).

## Exclusions

- A deliberate struct literal at the host (DL-106 limit, H7). No opaque type, no `@enforce_keys`, no runtime token.
- Plain records without a constructor (DL-106 "for now").
- Enum values (D6B-79). Enum constructors stay the decode path (DL-100); variants stay tuples.
- Constructor TYPES in EFFECT inputs and failures (D6B-19 stays). JSON encode of a struct.
- Atom keys from outside data: the decode keeps String keys on the wire side; only `new_T_k` builds atoms from field names that the compiler knows.
- Struct module name collisions with `Http`, `Replay`, `Retired` (D6B-81).
- `integrations/zed-beaml/`.

## Limits

- **[Inference]** A host that holds a struct from an older build with another field set gets `invalid BEAML input`. No test.
- **[Unknown]** Whether `is_struct/2` inside the generated `import Kernel, only: [...]` list gives a warning under Elixir 1.18.1 `--warnings-as-errors`. The GREEN worker adds it to the list and checks.
- **[Inference]** The REPLAY RUN result of a flow whose output holds a constructor field is a struct inside a map. A host that compares it with a stored JSON value must convert it. No host does this today.
