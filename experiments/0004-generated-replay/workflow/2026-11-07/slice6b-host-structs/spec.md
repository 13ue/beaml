# Slice 6b step 11: constructor TYPES are structs at the host, `T.new/1`

Plan: [plan.md](plan.md), [decisions.md](decisions.md) (D6B-73 to D6B-83), [plan-review.md](plan-review.md). RED defaults: [notes.md](notes.md) (D6B-97 to D6B-101).
Decision log: DL-106, DL-117, DL-120 in [decision-log.md](../../../../../wiki/planning/decision-log.md).
By: Opus (RED, slice6b-host-structs).

## Contract

- A constructor TYPE `T` is a nested struct module `BeamlSpike.T` with atom keys (D6B-73). Its success values are structs (DL-106).
- `T.new/1` takes one map with atom keys, also for one parameter (DL-117). It always gives `{:ok, struct}` or `{:error, failure}` (D6B-74).
- The key set picks the signature. The first signature whose parameter names equal the key set runs (DL-117, D6B-99).
- No signature matches: `{:error, {:no_signature, "T.new/1: no signature takes these keys"}}` (D6B-97).
- A non-atom key adds the line `  help: keys must be atoms; decode outside data through the EFFECT` (D6B-98).
- A value that is not a map, or a wrong value TYPE for the picked signature, raises `ArgumentError, "invalid BEAML input"` (D6B-100, D6B-101).
- Every public wrapper requires the struct where a constructor TYPE stands, also in a nested field and in an enum payload. A map of the same shape raises `invalid BEAML input` (D6B-76, D6B-82).
- A plain record keeps the String-key map form (DL-106, D6B-79). A constructor TYPE failure through a pipe keeps its fields (D6B-77).
- Limit (DL-106, D6B-19): a deliberate struct literal at the host passes the check. H7 records this.
- Sources without a record constructor give byte-equal output (H8).
- Not in this step: the reject of a constructor that reaches an EFFECT (DL-120, step 12b).

## Tests

`tests/slice6_host_struct_test.py`, fixture `slice6/host-struct/nonzero.beaml`.

| Case | Assertion | Today |
|---|---|---|
| H1 | `keep(%{"value" => 4})` raises; `keep(struct)` gives the struct | FAIL |
| H1g | `keep(%{value: 4})` raises | PASS (guard) |
| H2 | `NonZeroInt.new(%{n: 3})` ok struct; `%{n: 0}` IsZero; `%{n: "3"}` and `3` raise; String keys, unknown key, extra key give D6B-97 | FAIL |
| H3 | `unbox(%{"n" => %{"value" => 4}})` raises; `unbox(%{"n" => s})` gives `s` | FAIL |
| H3e | `wrapped({"Wrap", "Has", [map]})` raises; with the struct it passes | FAIL |
| H4 | `wrap(5) == {:ok, %NonZeroInt{value: 5}}` | FAIL |
| H5 | `same(%{"value" => 0})` keeps the map | PASS (guard) |
| H6 | `twice(4) == {:error, %NonZeroInt{value: 4}}`; `twice(0)` IsZero | PASS (guard) |
| H7 | `keep(%NonZeroInt{value: 0})` gives the struct (limit) | FAIL |
| H8 | 45 sources and `payments.beaml` byte-equal | PASS (guard) |
| H9 | `Pair.new(%{x: "x", y: "y"})`; `Pair.new(%{x: "x"})` D6B-97; `Label.new` picks signature 1 or 2 by keys | FAIL |

## Acceptance

- `python3 -B experiments/0004-generated-replay/tests/slice6_host_struct_test.py`: 3 of 3 pass, every subtest passes.
- The changed assertions of the plan table pass in `slice6_constructor_test.py`, `slice6_pipe_test.py`, `slice6_enum_test.py`, `slice6_decode_ctor_test.py`.
- `cargo test --no-fail-fast`, `cargo fmt --check`, `cargo clippy --offline --all-targets -- -D warnings` pass in `experiments/0001-syntax-to-beam`, with the unit test `constructor_types_are_structs`.
- Every other `slice6_*_test.py` passes. `run.py` runs once in the TEST phase.
- Compiler events contain no source text and no path.
